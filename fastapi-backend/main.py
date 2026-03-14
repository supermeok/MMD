from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.schemas import DetectionResponse
from app.services.detection import DetectionService


settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
