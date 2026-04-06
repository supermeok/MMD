import logging
import mimetypes
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import asyncio
import re
import time
from dataclasses import dataclass

from fastapi import HTTPException, UploadFile
from openai import APIConnectionError, AuthenticationError, BadRequestError, RateLimitError

from app.config import Settings
from app.schemas import (
    AgentBundle,
    AgentResult,
    DetectionMeta,
    DetectionResponse,
    JudgeResult,
    ReportSection,
    VerdictResult,
)
from app.services.content import MongoContentService
from app.utils.prompt_loader import render_prompt
from app.utils.qwen_client import QwenAPIClient
from app.utils.wiki_search import search_wiki_knowledge


logger = logging.getLogger(__name__)
ZH_CHAR_PATTERN = re.compile(r"[\u3400-\u9fff]")
FINISH_PATTERN = re.compile(r"finish\[(.*?)\]", re.IGNORECASE | re.DOTALL)
CONFIDENCE_PATTERN = re.compile(r"confidence\s*=\s*(\d{1,3})", re.IGNORECASE)


def clean_data(answer: str) -> str:
    answer = answer.replace("\n", " ")
    answer = answer.replace("\t", " ")
    return answer.strip()


def summarize_text(value: str, limit: int = 96) -> str:
    cleaned = clean_data(value)
    if len(cleaned) <= limit:
        return cleaned
    return f"{cleaned[:limit].rstrip()}..."


@dataclass(frozen=True)
class ResponseLanguage:
    code: str
    name: str
    is_chinese: bool


def detect_response_language(text: str) -> ResponseLanguage:
    if ZH_CHAR_PATTERN.search(text or ""):
        return ResponseLanguage(code="zh-CN", name="Simplified Chinese", is_chinese=True)
    return ResponseLanguage(code="en-US", name="English", is_chinese=False)


def append_language_instruction(
    prompt: str,
    response_language: ResponseLanguage,
    *,
    keep_finish_tag: bool = False,
    keep_judge_format: bool = False,
) -> str:
    if not response_language.is_chinese:
        return prompt

    instructions = [
        "Additional instruction:",
        "- Write all explanatory text in Simplified Chinese.",
    ]

    if keep_finish_tag:
        instructions.append("- Keep any required Finish[...] control tag in English exactly as specified.")

    if keep_judge_format:
        instructions.extend(
            [
                "- Keep the field names Verdict, Category, Confidence, and Reasoning in English exactly as specified.",
                "- Keep the Verdict values and Category values in English exactly as specified.",
                "- Write the content after Reasoning in Simplified Chinese.",
            ]
        )

    return f"{prompt.rstrip()}\n\n" + "\n".join(instructions)


def build_entity_extraction_prompt(prompt: str) -> str:
    return (
        f"{prompt.rstrip()}\n\n"
        "Additional instruction:\n"
        "- Return one concise key entity name for Wikipedia lookup.\n"
        "- Prefer an English canonical name when possible.\n"
        "- Use exactly this format: Finish: [key entity noun].\n"
        "- Do not add any extra explanation."
    )


def build_consistency_analysis_prompt(prompt: str, response_language: ResponseLanguage) -> str:
    base_prompt = prompt.split("Provide your judgment with confidence score", 1)[0].strip()
    analysis_prompt = (
        f"{base_prompt}\n\n"
        "Briefly explain whether the caption matches the image in 2-3 sentences.\n"
        "Do not output any Finish[...] tag."
    )
    return append_language_instruction(analysis_prompt, response_language)


def extract_finish_result(output: str) -> tuple[str | None, int | None]:
    match = FINISH_PATTERN.search(output or "")
    if not match:
        return None, None

    payload = match.group(1).strip()
    if not payload:
        return None, None

    label = payload.split(",", 1)[0].strip().upper()
    confidence_match = CONFIDENCE_PATTERN.search(payload)
    confidence = int(confidence_match.group(1)) if confidence_match else None
    return label, confidence


def format_stage_summary(stage: str, output: str, response_language: ResponseLanguage) -> str:
    label, confidence = extract_finish_result(output)
    if not label:
        return summarize_text(output)

    zh_map = {
        "text": {
            "TEXT REFUTES": "文本证据倾向反驳新闻标题",
            "TEXT SUPPORTS": "文本证据倾向支持新闻标题",
        },
        "visual": {
            "IMAGE REFUTES": "图像中存在与客观事实冲突的迹象",
            "IMAGE SUPPORTS": "图像中未发现明显的客观事实冲突",
        },
        "consistency": {
            "MATCH": "图文内容整体一致",
            "MISMATCH": "图文内容存在明显不一致",
        },
    }
    en_map = {
        "text": {
            "TEXT REFUTES": "Text evidence tends to refute the news caption",
            "TEXT SUPPORTS": "Text evidence tends to support the news caption",
        },
        "visual": {
            "IMAGE REFUTES": "The image shows signs of conflicting with objective facts",
            "IMAGE SUPPORTS": "No obvious factual conflict was found in the image",
        },
        "consistency": {
            "MATCH": "The caption and image are broadly consistent",
            "MISMATCH": "The caption and image show a clear mismatch",
        },
    }

    summary = (zh_map if response_language.is_chinese else en_map).get(stage, {}).get(label)
    if not summary:
        return summarize_text(output)

    if confidence is None:
        return summary
    if response_language.is_chinese:
        return f"{summary}，置信度 {confidence}%。"
    return f"{summary}, confidence {confidence}%."


def localize_verdict_display(verdict: VerdictResult, response_language: ResponseLanguage) -> tuple[str, str]:
    if not response_language.is_chinese:
        return verdict.verdict, verdict.category

    verdict_map = {
        "True": "真实",
        "Fake": "虚假",
    }
    category_map = {
        "original": "原始新闻",
        "textual_veracity_distortion": "文本事实失真",
        "visual_veracity_distortion": "视觉事实失真",
        "mismatch": "图文不匹配",
    }
    return verdict_map.get(verdict.verdict, verdict.verdict), category_map.get(verdict.category, verdict.category)


def localize_agent_decision(stage: str, label: str | None, response_language: ResponseLanguage) -> str:
    if not label:
        return "待判定" if response_language.is_chinese else "Pending"

    zh_map = {
        "text": {
            "TEXT SUPPORTS": "支持标题",
            "TEXT REFUTES": "反驳标题",
        },
        "visual": {
            "IMAGE SUPPORTS": "图像可信",
            "IMAGE REFUTES": "图像存疑",
        },
        "consistency": {
            "MATCH": "图文一致",
            "MISMATCH": "图文不一致",
        },
    }
    en_map = {
        "text": {
            "TEXT SUPPORTS": "Supports caption",
            "TEXT REFUTES": "Refutes caption",
        },
        "visual": {
            "IMAGE SUPPORTS": "Image appears credible",
            "IMAGE REFUTES": "Image appears suspicious",
        },
        "consistency": {
            "MATCH": "Caption matches image",
            "MISMATCH": "Caption mismatches image",
        },
    }
    return (zh_map if response_language.is_chinese else en_map).get(stage, {}).get(label, label)


def build_search_report_line(key_entity: str, response_language: ResponseLanguage) -> str:
    if response_language.is_chinese:
        return f"已执行外部搜索，检索实体：{key_entity or '未识别'}。"
    return f"External search executed for entity: {key_entity or 'N/A'}."


def extract_labeled_value(line: str, *labels: str) -> str | None:
    for label in labels:
        pattern = rf"^\s*{re.escape(label)}\s*[:：]\s*(.+)$"
        match = re.match(pattern, line, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def parse_debate_verdict(judge_output: str) -> VerdictResult:
    result = {
        "verdict": "True",
        "category": "original",
        "confidence": 0,
        "reasoning": "",
    }

    for raw_line in judge_output.strip().splitlines():
        line = raw_line.strip()

        verdict_value = extract_labeled_value(line, "Verdict", "裁决", "结论")
        if verdict_value is not None:
            verdict_str = verdict_value.lower()
            result["verdict"] = "Fake" if any(token in verdict_str for token in ("fake", "false", "虚假", "造假")) else "True"
            continue

        category_value = extract_labeled_value(line, "Category", "类别", "类型")
        if category_value is not None:
            category_str = category_value.lower()
            if any(token in category_str for token in ("textual", "文本")):
                result["category"] = "textual_veracity_distortion"
            elif any(token in category_str for token in ("visual", "图像", "视觉")):
                result["category"] = "visual_veracity_distortion"
            elif any(token in category_str for token in ("mismatch", "不匹配", "不一致")):
                result["category"] = "mismatch"
            else:
                result["category"] = "original"
            continue

        confidence_value = extract_labeled_value(line, "Confidence", "置信度")
        if confidence_value is not None:
            try:
                result["confidence"] = int(confidence_value.replace("%", ""))
            except ValueError:
                result["confidence"] = 0
            continue

        reasoning_value = extract_labeled_value(line, "Reasoning", "理由", "依据", "分析")
        if reasoning_value is not None:
            result["reasoning"] = reasoning_value

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
            stored_image_path = self._store_uploaded_image(image.filename, image_bytes, image.content_type)
            response_language = detect_response_language(news_caption)
            prompts = self._load_prompts(news_caption, response_language)

            text_task = asyncio.to_thread(
                self._run_text_analysis,
                prompts.text_prompt,
                image_data_url,
                response_language,
            )
            visual_task = asyncio.to_thread(
                self._run_visual_investigation,
                prompts.visual_prompt,
                image_data_url,
                response_language,
            )
            consistency_task = asyncio.to_thread(
                self._run_consistency_check,
                prompts.consistency_prompt,
                image_data_url,
                response_language,
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
                response_language,
            )

            elapsed_ms = int((time.perf_counter() - total_started) * 1000)
            response = DetectionResponse(
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
                    response_language=response_language.code,
                ),
            )
            response.history_id = self._persist_history_record(
                news_caption=news_caption,
                image_path=stored_image_path,
                response=response,
            )
            return response
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

    def _persist_history_record(
        self,
        *,
        news_caption: str,
        image_path: str,
        response: DetectionResponse,
    ) -> str:
        now = datetime.now(timezone.utc)
        document = {
            "title": news_caption,
            "image_path": image_path,
            "verdict": response.verdict.model_dump(),
            "agents": response.agents.model_dump(),
            "judge": response.judge.model_dump(),
            "meta": response.meta.model_dump(),
            "review_status": "pending",
            "review": {
                "manual_verdict": "",
                "notes": "",
                "reviewer": "",
                "reviewed_at": None,
            },
            "created_at": now,
            "updated_at": now,
        }

        repository = MongoContentService(self.settings)
        try:
            return repository.create_history_record(document)
        except Exception as exc:  # pragma: no cover
            logger.warning("Failed to persist detection history: %s", exc)
            return ""
        finally:
            repository.close()

    def _store_uploaded_image(
        self,
        filename: str | None,
        image_bytes: bytes,
        content_type: str | None,
    ) -> str:
        timestamp = datetime.now(timezone.utc)
        target_dir = self.settings.storage_dir / "detections" / timestamp.strftime("%Y%m")
        target_dir.mkdir(parents=True, exist_ok=True)

        suffix = Path(filename or "").suffix.lower()
        if not suffix:
            suffix = mimetypes.guess_extension(content_type or "image/jpeg") or ".jpg"

        target_name = f"{timestamp.strftime('%Y%m%dT%H%M%S')}_{uuid4().hex[:10]}{suffix}"
        target_path = target_dir / target_name
        target_path.write_bytes(image_bytes)
        return target_path.relative_to(self.settings.storage_dir).as_posix()

    def _load_prompts(self, news_caption: str, response_language: ResponseLanguage) -> PromptSet:
        return PromptSet(
            text_prompt=append_language_instruction(
                render_prompt(self.settings.prompt_dir, "textual_veracity_check.txt", news_caption),
                response_language,
                keep_finish_tag=True,
            ),
            visual_prompt=append_language_instruction(
                render_prompt(self.settings.prompt_dir, "visual_veracity_check.txt", news_caption),
                response_language,
                keep_finish_tag=True,
            ),
            consistency_prompt=append_language_instruction(
                render_prompt(self.settings.prompt_dir, "cross_modal_consistency.txt", news_caption),
                response_language,
                keep_finish_tag=True,
            ),
            judge_prompt=append_language_instruction(
                render_prompt(self.settings.prompt_dir, "comprehensive_judge.txt", news_caption),
                response_language,
                keep_judge_format=True,
            ),
        )

    def _create_client(self) -> QwenAPIClient:
        return QwenAPIClient(
            vision_model=self.settings.qwen_vl_model,
            text_model=self.settings.qwen_text_model,
            api_key=self.settings.qwen_api_key,
            base_url=self.settings.qwen_base_url,
        )

    def _run_text_analysis(
        self,
        prompt: str,
        image_data_url: str,
        response_language: ResponseLanguage,
    ) -> AgentResult:
        started = time.perf_counter()
        api_client = self._create_client()

        action_1 = prompt.split("Action 1:")[0].strip()
        action_1 = build_entity_extraction_prompt(action_1)
        entity_output = api_client.call_vision(action_1, image_data_url)

        key_entity, wiki_knowledge = search_wiki_knowledge(entity_output)

        action_2 = prompt.split("[Analysis]")[0].strip()
        action_2 = action_2.replace("[key entity noun]", key_entity)
        action_2 = action_2.replace("[External Knowledge]", wiki_knowledge)
        action_2 = append_language_instruction(action_2, response_language)
        analysis_output = api_client.call_vision(action_2, image_data_url)
        if "Analysis:" in analysis_output:
            analysis_output = analysis_output.split("Analysis:", 1)[1]
        analysis = clean_data(analysis_output)

        action_3 = prompt.replace("[key entity noun]", key_entity)
        action_3 = action_3.replace("[External Knowledge]", wiki_knowledge)
        action_3 = action_3.replace("[Analysis]", analysis)
        final_output = api_client.call_vision(action_3, image_data_url)

        verdict_code, confidence = extract_finish_result(final_output)
        stage_summary = format_stage_summary("text", final_output, response_language)
        verdict_display = localize_agent_decision("text", verdict_code, response_language)
        excerpt = summarize_text(analysis_output or final_output, 160)
        duration_ms = int((time.perf_counter() - started) * 1000)

        return AgentResult(
            logs=[
                f"判定结果: {verdict_display}",
                f"置信度: {confidence or 0}%",
                f"模型摘录: {excerpt}",
            ],
            summary=stage_summary,
            raw_output=final_output,
            duration_ms=duration_ms,
            verdict=verdict_display,
            confidence=confidence or 0,
            excerpt=excerpt,
            report_sections=[
                ReportSection(title="关键实体抽取", content=entity_output or "无返回内容"),
                ReportSection(title="外部搜索", content=build_search_report_line(key_entity, response_language)),
                ReportSection(title="事实分析", content=analysis_output or "无返回内容"),
                ReportSection(title="最终判定", content=final_output or "无返回内容"),
            ],
            details={
                "key_entity": key_entity,
                "analysis": analysis,
                "decision_code": verdict_code or "",
            },
        )

    def _run_visual_investigation(
        self,
        prompt: str,
        image_data_url: str,
        response_language: ResponseLanguage,
    ) -> AgentResult:
        started = time.perf_counter()
        api_client = self._create_client()

        action_1 = prompt.split("Observation:")[0].strip()
        action_1 = append_language_instruction(action_1, response_language)
        observation_output = api_client.call_vision(action_1, image_data_url)
        if "Thought 2" in observation_output:
            observation_output = observation_output.split("Thought 2", 1)[0]
        image_description = clean_data(observation_output)

        action_2 = prompt.replace("[Fact-conflicting Description]", image_description)
        final_output = api_client.call_vision(action_2, image_data_url)

        verdict_code, confidence = extract_finish_result(final_output)
        stage_summary = format_stage_summary("visual", final_output, response_language)
        verdict_display = localize_agent_decision("visual", verdict_code, response_language)
        excerpt = summarize_text(observation_output or final_output, 160)
        duration_ms = int((time.perf_counter() - started) * 1000)
        return AgentResult(
            logs=[
                f"判定结果: {verdict_display}",
                f"置信度: {confidence or 0}%",
                f"模型摘录: {excerpt}",
            ],
            summary=stage_summary,
            raw_output=final_output,
            duration_ms=duration_ms,
            verdict=verdict_display,
            confidence=confidence or 0,
            excerpt=excerpt,
            report_sections=[
                ReportSection(title="图像观察", content=observation_output or "无返回内容"),
                ReportSection(title="最终判定", content=final_output or "无返回内容"),
            ],
            details={
                "image_description": image_description,
                "decision_code": verdict_code or "",
            },
        )

    def _run_consistency_check(
        self,
        prompt: str,
        image_data_url: str,
        response_language: ResponseLanguage,
    ) -> AgentResult:
        started = time.perf_counter()
        api_client = self._create_client()

        analysis_prompt = build_consistency_analysis_prompt(prompt, response_language)
        analysis_output = api_client.call_vision(analysis_prompt, image_data_url)
        final_output = api_client.call_vision(prompt, image_data_url)

        verdict_code, confidence = extract_finish_result(final_output)
        stage_summary = format_stage_summary("consistency", final_output, response_language)
        verdict_display = localize_agent_decision("consistency", verdict_code, response_language)
        excerpt = summarize_text(analysis_output or final_output, 160)
        duration_ms = int((time.perf_counter() - started) * 1000)

        return AgentResult(
            logs=[
                f"判定结果: {verdict_display}",
                f"置信度: {confidence or 0}%",
                f"模型摘录: {excerpt}",
            ],
            summary=stage_summary,
            raw_output=final_output,
            duration_ms=duration_ms,
            verdict=verdict_display,
            confidence=confidence or 0,
            excerpt=excerpt,
            report_sections=[
                ReportSection(title="一致性分析", content=analysis_output or "无返回内容"),
                ReportSection(title="最终判定", content=final_output or "无返回内容"),
            ],
            details={
                "analysis": clean_data(analysis_output),
                "decision_code": verdict_code or "",
            },
        )

    def _run_comprehensive_judge(
        self,
        text_result: str,
        visual_result: str,
        consistency_result: str,
        prompt: str,
        response_language: ResponseLanguage,
    ) -> JudgeResult:
        started = time.perf_counter()
        api_client = self._create_client()

        judge_prompt = prompt.replace("[text_result]", text_result)
        judge_prompt = judge_prompt.replace("[visual_result]", visual_result)
        judge_prompt = judge_prompt.replace("[consistency_result]", consistency_result)

        raw_output = api_client.call_text(judge_prompt)
        verdict = parse_debate_verdict(raw_output)
        verdict_label, category_label = localize_verdict_display(verdict, response_language)
        duration_ms = int((time.perf_counter() - started) * 1000)

        return JudgeResult(
            logs=[
                "接收文本、视觉、一致性三路证据",
                "执行冲突对齐与可信度融合",
                f"生成最终裁决: {verdict_label} / {category_label}",
            ],
            raw_output=raw_output,
            duration_ms=duration_ms,
            verdict=verdict,
        )
