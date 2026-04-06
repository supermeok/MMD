import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _split_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _read_env(name: str, default: str = "") -> str:
    value = os.getenv(name)
    if value is None:
        value = os.getenv(f"\ufeff{name}")
    if value is None:
        value = default
    return value.strip()


@dataclass(frozen=True)
class Settings:
    app_name: str
    app_version: str
    cors_origins: tuple[str, ...]
    qwen_api_key: str
    qwen_base_url: str
    qwen_vl_model: str
    qwen_text_model: str
    prompt_dir: Path
    mongo_uri: str
    mongo_db: str
    knowledge_collection_zh: str
    knowledge_collection_en: str
    history_collection: str
    manual_collection: str
    storage_dir: Path
    knowledge_media_dir: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    cors_origins = _split_csv(
        _read_env(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        )
    )

    default_model = _read_env("QWEN_MODEL", "qwen3.5-plus")

    return Settings(
        app_name="Rumor Detection API",
        app_version="0.3.0",
        cors_origins=cors_origins,
        qwen_api_key=_read_env("DASHSCOPE_API_KEY"),
        qwen_base_url=_read_env(
            "QWEN_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ),
        qwen_vl_model=_read_env("QWEN_VL_MODEL", default_model),
        qwen_text_model=_read_env("QWEN_TEXT_MODEL", default_model),
        prompt_dir=BASE_DIR / "prompt_template",
        mongo_uri=_read_env("MONGO_URI", "mongodb://localhost:27017/"),
        mongo_db=_read_env("MONGO_DB", "mmfakebench"),
        knowledge_collection_zh=_read_env("MONGO_KNOWLEDGE_COLLECTION_ZH", "multiple_count_zh"),
        knowledge_collection_en=_read_env("MONGO_KNOWLEDGE_COLLECTION_EN", "multiple_count"),
        history_collection=_read_env("MONGO_HISTORY_COLLECTION", "detection_history"),
        manual_collection=_read_env("MONGO_MANUAL_COLLECTION", "system_manual"),
        storage_dir=Path(_read_env("STORAGE_DIR", str(BASE_DIR / "storage"))),
        knowledge_media_dir=Path(
            _read_env(
                "KNOWLEDGE_MEDIA_DIR",
                str(BASE_DIR / "data"),
            )
        ),
    )
