import asyncio
import time
from dataclasses import dataclass

from fastapi import HTTPException, UploadFile
from openai import APIConnectionError, AuthenticationError, BadRequestError, RateLimitError

from app.config import Settings
from app.schemas import AgentBundle, AgentResult, DetectionMeta, DetectionResponse, JudgeResult, VerdictResult
from app.utils.prompt_loader import render_prompt
from app.utils.qwen_client import QwenAPIClient
from app.utils.wiki_search import search_wiki_knowledge


def clean_data(answer: str) -> str:
    answer = answer.replace("\n", " ")
    answer = answer.replace("\t", " ")
    return answer.strip()


def summarize_text(value: str, limit: int = 96) -> str:
    cleaned = clean_data(value)
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit].rstrip()}..."


def parse_debate_verdict(judge_output: str) -> VerdictResult:
    result = {
        "verdict": "True",
        "category": "original",
        "confidence": 0,
        "reasoning": "",
    }

    for raw_line in judge_output.strip().splitlines():
        line = raw_line.strip()
        lower_line = line.lower()
        if lower_line.startswith("verdict:"):
            verdict_str = line.split(":", 1)[1].strip().lower()
            result["verdict"] = "Fake" if "fake" in verdict_str else "True"
        elif lower_line.startswith("category:"):
            category_str = line.split(":", 1)[1].strip().lower()
            if "textual" in category_str:
                result["category"] = "textual_veracity_distortion"
            elif "visual" in category_str:
                result["category"] = "visual_veracity_distortion"
            elif "mismatch" in category_str:
                result["category"] = "mismatch"
            else:
                result["category"] = "original"
        elif lower_line.startswith("confidence:"):
            try:
                result["confidence"] = int(line.split(":", 1)[1].strip().replace("%", ""))
            except ValueError:
                result["confidence"] = 0
        elif lower_line.startswith("reasoning:"):
            result["reasoning"] = line.split(":", 1)[1].strip()

    return VerdictResult(**result)


@dataclass(frozen=True)
class PromptSet:
    text_prompt: str
    visual_prompt: str
    consistency_prompt: str
    judge_prompt: str


class DetectionService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def analyze(self, news_caption: str, image: UploadFile) -> DetectionResponse:
        try:
            if not self.settings.qwen_api_key:
                raise HTTPException(status_code=500, detail="Missing DASHSCOPE_API_KEY in .env")

            total_started = time.perf_counter()
            image_bytes = await image.read()
            if not image_bytes:
                raise HTTPException(status_code=400, detail="Uploaded image is empty")

            image_data_url = QwenAPIClient.encode_image_bytes(
                image_bytes,
                image.content_type or "image/jpeg",
            )
            prompts = self._load_prompts(news_caption)

            text_task = asyncio.to_thread(
                self._run_text_analysis,
                prompts.text_prompt,
                image_data_url,
            )
            visual_task = asyncio.to_thread(
                self._run_visual_investigation,
                prompts.visual_prompt,
                image_data_url,
            )
            consistency_task = asyncio.to_thread(
                self._run_consistency_check,
                prompts.consistency_prompt,
                image_data_url,
            )

            text_result, visual_result, consistency_result = await asyncio.gather(
                text_task,
                visual_task,
                consistency_task,
            )

            judge_result = await asyncio.to_thread(
                self._run_comprehensive_judge,
                text_result.raw_output,
                visual_result.raw_output,
                consistency_result.raw_output,
                prompts.judge_prompt,
            )

            elapsed_ms = int((time.perf_counter() - total_started) * 1000)
            return DetectionResponse(
                verdict=judge_result.verdict,
                agents=AgentBundle(
                    text_analysis=text_result,
                    visual_investigate=visual_result,
                    consistency_check=consistency_result,
                ),
                judge=judge_result,
                meta=DetectionMeta(
                    elapsed_ms=elapsed_ms,
                    model=self.settings.qwen_vl_model,
                    filename=image.filename or "",
                ),
            )
        except HTTPException:
            raise
        except AuthenticationError as exc:
            raise HTTPException(status_code=401, detail=f"DashScope authentication failed: {exc}") from exc
        except RateLimitError as exc:
            raise HTTPException(status_code=429, detail=f"DashScope rate limit exceeded: {exc}") from exc
        except BadRequestError as exc:
            raise HTTPException(status_code=400, detail=f"DashScope rejected the request: {exc}") from exc
        except APIConnectionError as exc:
            raise HTTPException(status_code=502, detail=f"DashScope connection failed: {exc}") from exc
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Detection pipeline failed: {exc}") from exc

    def _load_prompts(self, news_caption: str) -> PromptSet:
        return PromptSet(
            text_prompt=render_prompt(self.settings.prompt_dir, "textual_veracity_check.txt", news_caption),
            visual_prompt=render_prompt(self.settings.prompt_dir, "visual_veracity_check.txt", news_caption),
            consistency_prompt=render_prompt(self.settings.prompt_dir, "cross_modal_consistency.txt", news_caption),
            judge_prompt=render_prompt(self.settings.prompt_dir, "comprehensive_judge.txt", news_caption),
        )

    def _create_client(self) -> QwenAPIClient:
        return QwenAPIClient(
            vision_model=self.settings.qwen_vl_model,
            text_model=self.settings.qwen_text_model,
            api_key=self.settings.qwen_api_key,
            base_url=self.settings.qwen_base_url,
        )

    def _run_text_analysis(self, prompt: str, image_data_url: str) -> AgentResult:
        started = time.perf_counter()
        api_client = self._create_client()

        action_1 = prompt.split("Action 1:")[0].strip()
        action_1 += " Please answer in the form: 'Finish: [key entity noun].'"
        entity_output = api_client.call_vision(action_1, image_data_url)

        key_entity, wiki_knowledge = search_wiki_knowledge(entity_output)

        action_2 = prompt.split("[Analysis]")[0].strip()
        action_2 = action_2.replace("[key entity noun]", key_entity)
        action_2 = action_2.replace("[External Knowledge]", wiki_knowledge)
        analysis_output = api_client.call_vision(action_2, image_data_url)
        if "Analysis:" in analysis_output:
            analysis_output = analysis_output.split("Analysis:", 1)[1]
        analysis = clean_data(analysis_output)

        action_3 = prompt.replace("[key entity noun]", key_entity)
        action_3 = action_3.replace("[External Knowledge]", wiki_knowledge)
        action_3 = action_3.replace("[Analysis]", analysis)
        final_output = api_client.call_vision(action_3, image_data_url)

        duration_ms = int((time.perf_counter() - started) * 1000)
        knowledge_status = "已命中" if wiki_knowledge else "未命中外部知识"

        return AgentResult(
            logs=[
                f"抽取关键实体: {key_entity or '未识别'}",
                f"外部知识检索: {knowledge_status}",
                f"文本分析摘要: {summarize_text(final_output)}",
            ],
            summary=summarize_text(final_output),
            raw_output=final_output,
            duration_ms=duration_ms,
            details={
                "key_entity": key_entity,
                "external_knowledge": wiki_knowledge,
                "analysis": analysis,
            },
        )

    def _run_visual_investigation(self, prompt: str, image_data_url: str) -> AgentResult:
        started = time.perf_counter()
        api_client = self._create_client()

        action_1 = prompt.split("Observation:")[0].strip()
        observation_output = api_client.call_vision(action_1, image_data_url)
        if "Thought 2" in observation_output:
            observation_output = observation_output.split("Thought 2", 1)[0]
        image_description = clean_data(observation_output)

        action_2 = prompt.replace("[Fact-conflicting Description]", image_description)
        final_output = api_client.call_vision(action_2, image_data_url)

        duration_ms = int((time.perf_counter() - started) * 1000)
        return AgentResult(
            logs=[
                f"图像描述提取: {summarize_text(image_description)}",
                f"视觉分析摘要: {summarize_text(final_output)}",
            ],
            summary=summarize_text(final_output),
            raw_output=final_output,
            duration_ms=duration_ms,
            details={
                "image_description": image_description,
            },
        )

    def _run_consistency_check(self, prompt: str, image_data_url: str) -> AgentResult:
        started = time.perf_counter()
        api_client = self._create_client()
        final_output = api_client.call_vision(prompt, image_data_url)
        duration_ms = int((time.perf_counter() - started) * 1000)

        return AgentResult(
            logs=[
                "已完成图文跨模态一致性推理",
                f"一致性判断摘要: {summarize_text(final_output)}",
            ],
            summary=summarize_text(final_output),
            raw_output=final_output,
            duration_ms=duration_ms,
            details={},
        )

    def _run_comprehensive_judge(
        self,
        text_result: str,
        visual_result: str,
        consistency_result: str,
        prompt: str,
    ) -> JudgeResult:
        started = time.perf_counter()
        api_client = self._create_client()

        judge_prompt = prompt.replace("[text_result]", text_result)
        judge_prompt = judge_prompt.replace("[visual_result]", visual_result)
        judge_prompt = judge_prompt.replace("[consistency_result]", consistency_result)

        raw_output = api_client.call_text(judge_prompt)
        verdict = parse_debate_verdict(raw_output)
        duration_ms = int((time.perf_counter() - started) * 1000)

        return JudgeResult(
            logs=[
                "接收文本、视觉、一致性三路证据",
                "执行冲突对齐与可信度融合",
                f"生成最终裁决: {verdict.verdict} / {verdict.category}",
            ],
            raw_output=raw_output,
            duration_ms=duration_ms,
            verdict=verdict,
        )
