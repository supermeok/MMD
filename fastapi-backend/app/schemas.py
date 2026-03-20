from pydantic import BaseModel, Field


class VerdictResult(BaseModel):
    verdict: str = "True"
    category: str = "original"
    confidence: int = 0
    reasoning: str = ""


class ReportSection(BaseModel):
    title: str = ""
    content: str = ""


class AgentResult(BaseModel):
    status: str = "done"
    logs: list[str] = Field(default_factory=list)
    summary: str = ""
    raw_output: str = ""
    duration_ms: int = 0
    verdict: str = ""
    confidence: int = 0
    excerpt: str = ""
    report_sections: list[ReportSection] = Field(default_factory=list)
    details: dict[str, str] = Field(default_factory=dict)


class AgentBundle(BaseModel):
    text_analysis: AgentResult
    visual_investigate: AgentResult
    consistency_check: AgentResult


class JudgeResult(BaseModel):
    status: str = "done"
    logs: list[str] = Field(default_factory=list)
    raw_output: str = ""
    duration_ms: int = 0
    verdict: VerdictResult


class DetectionMeta(BaseModel):
    elapsed_ms: int = 0
    model: str = ""
    filename: str = ""
    response_language: str = ""


class DetectionResponse(BaseModel):
    verdict: VerdictResult
    agents: AgentBundle
    judge: JudgeResult
    meta: DetectionMeta
