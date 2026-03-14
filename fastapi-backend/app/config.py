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
        app_version="0.2.1",
        cors_origins=cors_origins,
        qwen_api_key=_read_env("DASHSCOPE_API_KEY"),
        qwen_base_url=_read_env(
            "QWEN_BASE_URL",
            "https://dashscope.aliyuncs.com/compatible-mode/v1",
        ),
        qwen_vl_model=_read_env("QWEN_VL_MODEL", default_model),
        qwen_text_model=_read_env("QWEN_TEXT_MODEL", default_model),
        prompt_dir=BASE_DIR / "prompt_template",
    )
