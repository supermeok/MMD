from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.schemas import (
    DetectionResponse,
    HistoryDeleteResponse,
    HistoryDetailResponse,
    HistoryListResponse,
    HistorySummaryResponse,
    KnowledgeListResponse,
    KnowledgeStatsResponse,
    ManualResponse,
    ReviewUpdateRequest,
    ReviewUpdateResponse,
)
from app.services.content import MongoContentService
from app.services.detection import DetectionService


settings = get_settings()
settings.storage_dir.mkdir(parents=True, exist_ok=True)
app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory=settings.storage_dir, check_dir=False), name="media")
app.mount(
    "/knowledge-media",
    StaticFiles(directory=settings.knowledge_media_dir, check_dir=False),
    name="knowledge-media",
)


@app.get("/api/health")
async def health():
    return {"ok": True, "version": settings.app_version}


@app.post("/api/detection/analyze", response_model=DetectionResponse)
@app.post("/api/detection/verdict", response_model=DetectionResponse)
async def detection_analyze(
    title: str = Form(...),
    image: UploadFile = File(...),
):
    service = DetectionService(settings)
    return await service.analyze(news_caption=title, image=image)


@app.get("/api/knowledge/articles", response_model=KnowledgeListResponse)
async def knowledge_articles(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=48),
    fake_type: str | None = None,
    binary_fake_type: str | None = None,
    search: str | None = None,
    lang: str = Query("zh", pattern="^(zh|en)$"),
):
    repository = MongoContentService(settings)
    try:
        return repository.list_knowledge(
            base_url=str(request.base_url).rstrip("/"),
            lang=lang,
            page=page,
            page_size=page_size,
            fake_type=fake_type,
            binary_fake_type=binary_fake_type,
            search=search,
        )
    finally:
        repository.close()


@app.get("/api/knowledge/stats", response_model=KnowledgeStatsResponse)
async def knowledge_stats(lang: str = Query("zh", pattern="^(zh|en)$")):
    repository = MongoContentService(settings)
    try:
        return repository.get_knowledge_stats(lang=lang)
    finally:
        repository.close()


@app.get("/api/history", response_model=HistoryListResponse)
async def history_records(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(8, ge=1, le=40),
    review_status: str | None = Query(default=None, pattern="^(pending|approved|corrected|flagged)?$"),
    search: str | None = None,
):
    repository = MongoContentService(settings)
    try:
        return repository.list_history(
            base_url=str(request.base_url).rstrip("/"),
            page=page,
            page_size=page_size,
            review_status=review_status,
            search=search,
        )
    finally:
        repository.close()


@app.get("/api/history/summary", response_model=HistorySummaryResponse)
async def history_summary():
    repository = MongoContentService(settings)
    try:
        return repository.get_history_summary()
    finally:
        repository.close()


@app.get("/api/history/{record_id}", response_model=HistoryDetailResponse)
async def history_record_detail(request: Request, record_id: str):
    repository = MongoContentService(settings)
    try:
        return repository.get_history_detail(
            record_id=record_id,
            base_url=str(request.base_url).rstrip("/"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    finally:
        repository.close()


@app.patch("/api/history/{record_id}/review", response_model=ReviewUpdateResponse)
async def history_record_review(request: Request, record_id: str, payload: ReviewUpdateRequest):
    repository = MongoContentService(settings)
    try:
        item = repository.update_history_review(
            record_id=record_id,
            payload=payload,
            base_url=str(request.base_url).rstrip("/"),
        )
        return ReviewUpdateResponse(item=item)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    finally:
        repository.close()


@app.delete("/api/history/{record_id}", response_model=HistoryDeleteResponse)
async def history_record_delete(record_id: str):
    repository = MongoContentService(settings)
    try:
        deleted_id = repository.delete_history_record(record_id=record_id)
        return HistoryDeleteResponse(id=deleted_id, deleted=True)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    finally:
        repository.close()


@app.get("/api/manual", response_model=ManualResponse)
async def system_manual():
    repository = MongoContentService(settings)
    try:
        return repository.get_manual()
    finally:
        repository.close()
