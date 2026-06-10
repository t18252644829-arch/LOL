"""抓官方补丁说明文本,供 AI 解读「这版改了什么、对你英雄有啥影响」。

官方补丁说明 URL 有稳定规律:patch-<major>-<minor>-notes。
拿到 HTML 后去标签转成纯文本(结构会变,但正文文字能取到)。

注意:这是网络爬取,需在你电脑上跑;第一次可能要校准。所有取文本走可注入
getter,纯函数(URL 构造 / HTML 转文本)可离线测试。
"""
from __future__ import annotations

import re
import urllib.request


def _get_text(url: str, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 lol-coach"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def patch_url(version: str, locale: str = "en-us") -> str:
    """'14.10.1' / '14.10' -> .../patch-14-10-notes/"""
    parts = version.split(".")
    mm = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else version
    return f"https://www.leagueoflegends.com/{locale}/news/game-updates/patch-{mm}-notes/"


def html_to_text(html: str) -> str:
    """去掉 script/style/标签,折叠空白,得到可读正文。"""
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html,
                  flags=re.I | re.S)
    html = re.sub(r"<[^>]+>", " ", html)
    html = re.sub(r"&[a-z]+;", " ", html)
    return re.sub(r"\s+", " ", html).strip()


def fetch_patch_notes(version: str, locale: str = "en-us",
                      getter=_get_text, max_chars: int = 12000) -> dict:
    """抓某版本补丁说明纯文本(截断到 max_chars,避免过长)。"""
    url = patch_url(version, locale)
    try:
        text = html_to_text(getter(url))
    except Exception as e:                      # noqa: BLE001 网络/解析失败统一兜底
        return {"version": version, "url": url, "error": str(e)[:120]}
    return {"version": version, "url": url, "text": text[:max_chars],
            "truncated": len(text) > max_chars}


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json

    ap = argparse.ArgumentParser(description="抓官方补丁说明文本")
    ap.add_argument("version", help="版本号,如 14.10")
    ap.add_argument("--locale", default="en-us", help="如 en-us")
    args = ap.parse_args(argv)
    print(json.dumps(fetch_patch_notes(args.version, args.locale),
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
