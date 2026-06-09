from __future__ import annotations

import re

IMAGEM_RE = re.compile(r"\.(jpe?g|png|gif|webp|svg|bmp)(\?|$)", re.IGNORECASE)
YOUTUBE_RE = re.compile(r"(?:youtube\.com/watch\?v=|youtu\.be/)([A-Za-z0-9_-]{11})")


def id_video_youtube(url: str | None) -> str | None:
    if not url:
        return None
    match = YOUTUBE_RE.search(url)
    return match.group(1) if match else None


def eh_imagem(url: str | None) -> bool:
    return bool(url and IMAGEM_RE.search(url))


def url_embed_youtube(video_id: str) -> str:
    return f"https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0"


def url_thumb_youtube(video_id: str) -> str:
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
