from pydantic import BaseModel, Field


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserRegisterRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str
    created_at: str = ""


class UserProfileResponse(BaseModel):
    id: str
    username: str
    email: str = ""
    avatar: str = ""
    created_at: str = ""


class UserProfileUpdateRequest(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str | None = None


class AvatarUploadResponse(BaseModel):
    avatar_url: str


class LoginResponse(BaseModel):
    token: str
    username: str
    user_id: str


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
    history_id: str = ""


class PaginatedResponse(BaseModel):
    total: int = 0
    page: int = 1
    page_size: int = 10
    total_pages: int = 0


class KnowledgeItem(BaseModel):
    id: str
    title: str = ""
    image_url: str = ""
    fake_type: str = ""
    binary_fake_type: str = ""
    reasoning: str = ""
    dataset: str = ""
    source: str = ""


class KnowledgeListResponse(PaginatedResponse):
    items: list[KnowledgeItem] = Field(default_factory=list)


class KnowledgeStatsResponse(BaseModel):
    total: int = 0
    fake_type_stats: dict[str, int] = Field(default_factory=dict)
    binary_stats: dict[str, int] = Field(default_factory=dict)


class HistoryRecordSummary(BaseModel):
    id: str
    title: str = ""
    image_url: str = ""
    created_at: str = ""
    updated_at: str = ""
    response_language: str = ""
    auto_verdict: str = ""
    auto_category: str = ""
    auto_confidence: int = 0
    auto_reasoning: str = ""
    review_status: str = "pending"
    manual_verdict: str = ""
    reviewer: str = ""
    reviewed_at: str = ""
    review_notes: str = ""


class HistoryListResponse(PaginatedResponse):
    items: list[HistoryRecordSummary] = Field(default_factory=list)


class HistorySummaryResponse(BaseModel):
    total: int = 0
    pending_review: int = 0
    approved_count: int = 0
    corrected_count: int = 0
    flagged_count: int = 0


class HistoryDetailResponse(BaseModel):
    item: HistoryRecordSummary
    agents: AgentBundle
    judge: JudgeResult
    meta: DetectionMeta


class ReviewUpdateRequest(BaseModel):
    review_status: str = "pending"
    manual_verdict: str = ""
    notes: str = ""
    reviewer: str = ""


class ReviewUpdateResponse(BaseModel):
    item: HistoryRecordSummary


class HistoryDeleteResponse(BaseModel):
    id: str = ""
    deleted: bool = True


class ManualSection(BaseModel):
    id: str
    title: str
    summary: str = ""
    bullets: list[str] = Field(default_factory=list)
    highlights: list[str] = Field(default_factory=list)


class ManualResponse(BaseModel):
    updated_at: str = ""
    sections: list[ManualSection] = Field(default_factory=list)
