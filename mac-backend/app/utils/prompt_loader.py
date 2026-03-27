from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=16)
def _load_template(template_path: str) -> str:
    return Path(template_path).read_text(encoding="utf-8")


def render_prompt(prompt_dir: Path, template_name: str, news_caption: str) -> str:
    template_path = prompt_dir / template_name
    template = _load_template(str(template_path))
    return template.replace("[News caption]", news_caption)
