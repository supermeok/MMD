from fastapi import UploadFile

from app.config import get_settings
from app.services.detection import DetectionService


async def MAC_Judge(news_caption: str, image: UploadFile):
    service = DetectionService(get_settings())
    response = await service.analyze(news_caption=news_caption, image=image)
    return response.model_dump()
