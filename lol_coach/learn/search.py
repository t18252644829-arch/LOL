"""用 yt-dlp 搜索 B站 / YouTube,返回统一格式的视频列表。

yt-dlp 自动处理 B站签名、YouTube 接口,比手写爬虫稳。在你电脑上运行
(需 `pip install yt-dlp`,且能访问 B站/YouTube)。
"""
from __future__ import annotations

import json
import subprocess

# source -> yt-dlp 搜索前缀
_PREFIX = {"bili": "bilisearch", "youtube": "ytsearch"}


def _run_ytdlp(args: list[str], timeout: int = 90) -> str:
    proc = subprocess.run(
        ["yt-dlp", *args],
        capture_output=True, text=True, timeout=timeout,
    )
    return proc.stdout


def search_videos(query: str, source: str = "bili", limit: int = 5) -> list[dict]:
    """搜索单个关键词,返回 [{title, uploader, url, duration, views, source}]。

    出错(网络/未装 yt-dlp)时返回空列表,不抛异常,便于批量容错。
    """
    prefix = _PREFIX.get(source)
    if not prefix:
        raise ValueError(f"未知视频源: {source}")

    spec = f"{prefix}{limit}:{query}"
    try:
        out = _run_ytdlp([spec, "--flat-playlist", "--dump-json", "--no-warnings"])
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []

    results = []
    for line in out.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        results.append({
            "title": d.get("title"),
            "uploader": d.get("uploader") or d.get("channel"),
            "url": d.get("url") or d.get("webpage_url") or d.get("id"),
            "duration": d.get("duration"),
            "views": d.get("view_count"),
            "source": source,
        })
    return results


def rank(videos: list[dict], limit: int = 5) -> list[dict]:
    """按播放量排序,过滤掉过短(<2分钟)的视频;时长未知的保留。"""
    def ok_duration(v):
        dur = v.get("duration")
        return dur is None or dur >= 120

    def view_key(v):
        return v.get("views") or 0

    filtered = [v for v in videos if ok_duration(v)]
    filtered.sort(key=view_key, reverse=True)
    return filtered[:limit]
