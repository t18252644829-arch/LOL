"""用 yt-dlp 抓视频字幕,转成纯文本,供 AI 总结。

YouTube 大多有自动字幕(zh/en),B站有 CC 时也能抓。抓到的纯文本贴给对话,
我就能把它提炼成「针对你弱点的要点」。无字幕的视频会返回空。
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from pathlib import Path

_LANGS = "zh-Hans,zh-CN,zh,en,en-US"


def _vtt_to_text(vtt: str) -> str:
    """把 .vtt 字幕去掉时间轴/标签/重复行,拼成连续文本。"""
    lines, prev = [], None
    for raw in vtt.splitlines():
        s = raw.strip()
        if (not s or s == "WEBVTT" or "-->" in s
                or s.isdigit() or s.startswith(("Kind:", "Language:"))):
            continue
        s = re.sub(r"<[^>]+>", "", s)        # 去掉 <00:00:00.000> 之类内联标签
        if s and s != prev:                  # 去掉自动字幕常见的逐行重复
            lines.append(s)
            prev = s
    return " ".join(lines)


def fetch_subtitle(url: str, timeout: int = 120) -> str:
    """抓字幕并返回纯文本;无字幕或出错返回空字符串。"""
    with tempfile.TemporaryDirectory() as tmp:
        out_tpl = str(Path(tmp) / "sub")
        try:
            subprocess.run(
                ["yt-dlp", url, "--skip-download",
                 "--write-subs", "--write-auto-subs",
                 "--sub-langs", _LANGS, "--sub-format", "vtt",
                 "-o", out_tpl, "--no-warnings"],
                capture_output=True, text=True, timeout=timeout,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return ""
        vtts = list(Path(tmp).glob("*.vtt"))
        if not vtts:
            return ""
        # 优先中文字幕
        vtts.sort(key=lambda p: 0 if ("zh" in p.name) else 1)
        return _vtt_to_text(vtts[0].read_text(encoding="utf-8", errors="ignore"))


def main(argv: list[str] | None = None) -> int:
    import sys
    args = argv or sys.argv[1:]
    if not args:
        print("用法: python -m lol_coach.learn.subtitles <视频URL>", file=sys.stderr)
        return 2
    text = fetch_subtitle(args[0])
    if not text:
        print("(没抓到字幕,这个视频可能没有字幕)", file=sys.stderr)
        return 1
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
