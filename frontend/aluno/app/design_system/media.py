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


def js_remover_player_youtube() -> str:
    return "var el=document.getElementById('yt-bar'); if(el) el.remove();"


def js_player_youtube(video_id: str) -> str:
    return f"""
        (function() {{
            var old = document.getElementById('yt-bar');
            if (old) return;
            var bar = document.createElement('div');
            bar.id = 'yt-bar';
            bar.style.cssText = 'position:fixed;top:0;left:0;width:100%;z-index:9999;background:#000;display:flex;flex-direction:column;align-items:center;';
            var fr = document.createElement('iframe');
            fr.src = 'https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0';
            fr.style.cssText = 'width:100%;max-height:42vh;aspect-ratio:16/9;border:none;';
            fr.allow = 'autoplay; encrypted-media; fullscreen';
            var btn = document.createElement('button');
            btn.textContent = 'Fechar video';
            btn.style.cssText = 'width:100%;padding:6px;background:#111;color:#888;border:none;border-top:1px solid #222;cursor:pointer;font-size:13px;';
            btn.onclick = function(){{ bar.remove(); }};
            bar.appendChild(fr);
            bar.appendChild(btn);
            document.body.appendChild(bar);
        }})();
    """
