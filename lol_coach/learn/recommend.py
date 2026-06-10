"""串联:阶段一汇总 -> 弱点 -> 搜索 B站/YouTube -> 排序 -> 推荐清单。

用法:
    # 用某英雄某周期的汇总,生成针对性学习推荐
    python -m lol_coach.learn.recommend data/matches/武器大师_6.10-6.20_汇总.json

    # 指定源与每个弱点的推荐数
    python -m lol_coach.learn.recommend 汇总.json --source bili,youtube --per 4
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .search import rank, search_videos
from .weakness import build_search_plan


def recommend(summary: dict, sources: list[str], per: int = 4, searcher=search_videos) -> dict:
    """对每个弱点跨源搜索、去重、排序,产出推荐清单。"""
    plan = build_search_plan(summary)
    out = {"champion": summary.get("champion"), "period": summary.get("period"),
           "sections": []}

    for item in plan:
        videos, seen = [], set()
        for query in item["queries"]:
            for src in sources:
                for v in searcher(query, source=src, limit=per):
                    key = v.get("url")
                    if key and key not in seen:
                        seen.add(key)
                        videos.append(v)
        out["sections"].append({
            "weakness": item["weakness"],
            "advice": item["advice"],
            "queries": item["queries"],
            "videos": rank(videos, limit=per),
        })
    return out


def _load_summary(path: str) -> dict:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    return doc.get("summary", doc)  # 兼容 {summary,matches} 或直接 summary


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="根据弱点推荐 B站/YouTube 学习视频")
    ap.add_argument("summary", help="阶段一汇总 json(data/matches/xxx_汇总.json)")
    ap.add_argument("--source", default="bili,youtube", help="逗号分隔: bili,youtube")
    ap.add_argument("--per", type=int, default=4, help="每个弱点推荐几个视频")
    args = ap.parse_args(argv)

    summary = _load_summary(args.summary)
    sources = [s.strip() for s in args.source.split(",") if s.strip()]
    result = recommend(summary, sources, per=args.per)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    total = sum(len(s["videos"]) for s in result["sections"])
    if total == 0:
        print("\n没搜到视频。请确认已 pip install yt-dlp、且能访问 B站/YouTube。",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
