"""把「你的数据 + 当前版本事实 + 段位」打包成一份给 AI 教练分析的简报。

工具只负责采集与打包(客观);真正的分析(生态位、装备天赋优先级、打法思路、
对线要点、结合段位的实操成长路径)由对话里的我来做。

用法:
    python -m lol_coach.learn.brief data/matches/武器大师_6.10-6.20_汇总.json \
        --rank 黄金 --version 14.10
"""
from __future__ import annotations

import json
from pathlib import Path

from ..tasks import evaluate as evaluate_tasks
from .meta import fetch_meta
from .patchnotes import fetch_patch_notes
from .scout import champion_facts

# 我要回答的分析维度(贴给对话后,我据此产出报告)
_QUESTIONS = [
    "这个英雄在当前版本该位置的生态位(强/弱、定位、为什么)",
    "装备与天赋优先级(核心出装顺序、关键符文,及取舍理由)",
    "核心打法思路与连招",
    "对线要点(常见对位的优劣势与应对)",
    "结合我当前段位与数据短板,最有效的实操成长方式(具体练什么、怎么练)",
]


def _personal(summary: dict) -> dict:
    keys = ["champion", "period", "games", "winrate",
            "avg_kp", "avg_cs", "avg_cs_diff", "avg_gold_diff"]
    return {k: summary[k] for k in keys if k in summary}


def build_brief(summary: dict, rank: str | None = None, version: str | None = None,
                lane: str | None = None, with_meta: bool = False,
                with_patch: bool = False, facts_getter=champion_facts) -> dict:
    champ = (summary.get("champion") or "").strip()
    facts = facts_getter(champ, version=version) if champ else {}
    brief = {
        "我的段位": rank,
        "我的位置": lane,
        "我的数据": _personal(summary),
        "上次任务进度": evaluate_tasks(summary),
        "当前版本事实": facts,
    }
    use_version = facts.get("version") or version
    if with_meta and lane and facts.get("key") and use_version:
        brief["社区meta"] = fetch_meta(facts["key"], lane, use_version)
    if with_patch and use_version:
        brief["补丁说明"] = fetch_patch_notes(use_version)
    brief["请你分析"] = _QUESTIONS
    return brief


def _load_summary(path: str) -> dict:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    return doc.get("summary", doc)


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="打包个人数据+版本事实,生成分析简报")
    ap.add_argument("summary", help="阶段一汇总 json")
    ap.add_argument("--rank", help="你的段位,如 黄金/铂金")
    ap.add_argument("--version", help="锁定版本号(国服客户端显示的)")
    ap.add_argument("--lane", help="位置 top/jungle/mid/adc/support(抓社区meta需要)")
    ap.add_argument("--meta", action="store_true", help="附带社区meta(易碎,需校准)")
    ap.add_argument("--patch", action="store_true", help="附带官方补丁说明文本")
    args = ap.parse_args(argv)

    summary = _load_summary(args.summary)
    brief = build_brief(summary, rank=args.rank, version=args.version,
                        lane=args.lane, with_meta=args.meta, with_patch=args.patch)
    print(json.dumps(brief, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
