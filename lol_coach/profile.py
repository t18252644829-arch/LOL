"""个人档案:教练的"记忆"。存你的分路/段位/目标/英雄池/定制计划。

我(对话里的教练)没有跨会话的长期记忆,这个文件就是记忆载体。每次开始训练,
用 `digest` 把(档案 + 当前任务 + 最近一次对局汇总)导出来贴给我,我就能"接上"。

存到 data/profile.json。命令:
    set   --lane top --rank 未定级 --goal 白银 --pool 诺手,盖伦
    plan  "我的定制成长计划文本"
    show
    digest                       # 导出给教练的状态包(贴给对话)
"""
from __future__ import annotations

import json
from pathlib import Path

PROFILE_FILE = Path("data/profile.json")
MATCHES_DIR = Path("data/matches")

_FIELDS = ("lane", "current_rank", "goal_rank", "champion_pool", "plan", "notes")


def _load(path: Path = PROFILE_FILE) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _save(profile: dict, path: Path = PROFILE_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding="utf-8")


def update(path: Path = PROFILE_FILE, **kw) -> dict:
    profile = _load(path)
    for k, v in kw.items():
        if v is not None:
            profile[k] = v
    _save(profile, path)
    return profile


def latest_summary(matches_dir: Path = MATCHES_DIR) -> dict | None:
    """取最近一次 batch 汇总(按修改时间);没有则 None。"""
    files = list(matches_dir.glob("*_汇总.json")) if matches_dir.exists() else []
    if not files:
        return None
    newest = max(files, key=lambda p: p.stat().st_mtime)
    try:
        doc = json.loads(newest.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return doc.get("summary", doc)


def digest(profile_path: Path = PROFILE_FILE,
           matches_dir: Path = MATCHES_DIR,
           tasks_path: Path | None = None) -> dict:
    """导出给教练的状态包:档案 + 当前任务 + 最近对局 + 已有任务进度。"""
    from . import tasks as T

    tp = tasks_path or T.TASKS_FILE
    profile = _load(profile_path)
    summary = latest_summary(matches_dir)
    active = T.list_tasks(path=tp)
    out: dict = {
        "个人档案": profile,
        "当前任务": active,
        "最近一次对局": summary,
    }
    if summary:
        out["最近任务进度"] = T.evaluate(summary, tasks=active)
    out["_提示给教练"] = "请先确认当前游戏版本(联网查),再结合本状态包更新建议、计划与任务。"
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="个人档案(教练记忆)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("set", help="设置档案字段")
    s.add_argument("--lane", help="分路 top/jungle/mid/adc/support")
    s.add_argument("--rank", dest="current_rank", help="当前段位(未定级就写 未定级)")
    s.add_argument("--goal", dest="goal_rank", help="目标段位")
    s.add_argument("--pool", dest="champion_pool", help="英雄池,逗号分隔")

    p = sub.add_parser("plan", help="设置定制计划文本")
    p.add_argument("text")

    sub.add_parser("show", help="查看档案")
    sub.add_parser("digest", help="导出状态包给教练")

    args = ap.parse_args(argv)

    if args.cmd == "set":
        pool = (args.champion_pool.split(",") if args.champion_pool else None)
        prof = update(lane=args.lane, current_rank=args.current_rank,
                      goal_rank=args.goal_rank,
                      champion_pool=[c.strip() for c in pool] if pool else None)
        print(json.dumps(prof, ensure_ascii=False, indent=2))
    elif args.cmd == "plan":
        prof = update(plan=args.text)
        print("计划已保存。")
    elif args.cmd == "show":
        print(json.dumps(_load(), ensure_ascii=False, indent=2))
    elif args.cmd == "digest":
        print(json.dumps(digest(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
