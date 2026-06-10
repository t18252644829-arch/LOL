"""成长任务系统:存储我布置的任务,并在下一回合用你的汇总数据自动核对进度。

任务有两种:
  - 可量化任务:绑定一个汇总指标(如 avg_cs_diff)和目标值,下一回合自动判定达成。
  - 主观任务(如「5层再交R」):不绑指标,靠你自评打勾。

存到 data/tasks.json。命令:
    add  --desc "前10分钟补刀不落后" --champion 诺手 --metric avg_cs_diff --target 0
    list [--champion 诺手]
    done <id> / drop <id>
    review <某汇总.json>      # 用这回合数据核对任务进度
"""
from __future__ import annotations

import json
from pathlib import Path

TASKS_FILE = Path("data/tasks.json")

# 可自动评估的指标(对应 batch 汇总里的字段)
METRICS = {"avg_cs_diff", "avg_kp", "avg_gold_diff", "avg_cs", "avg_deaths"}


def _load(path: Path = TASKS_FILE) -> list[dict]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def _save(tasks: list[dict], path: Path = TASKS_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


def add_task(desc: str, champion: str | None = None, metric: str | None = None,
             target: float | None = None, cmp: str = ">=",
             path: Path = TASKS_FILE) -> dict:
    tasks = _load(path)
    tid = (max((t["id"] for t in tasks), default=0) + 1)
    task = {"id": tid, "desc": desc, "champion": champion,
            "metric": metric, "target": target, "cmp": cmp, "status": "active"}
    tasks.append(task)
    _save(tasks, path)
    return task


def set_status(tid: int, status: str, path: Path = TASKS_FILE) -> bool:
    tasks = _load(path)
    for t in tasks:
        if t["id"] == tid:
            t["status"] = status
            _save(tasks, path)
            return True
    return False


def list_tasks(champion: str | None = None, status: str = "active",
               path: Path = TASKS_FILE) -> list[dict]:
    tasks = _load(path)
    return [t for t in tasks
            if (status is None or t["status"] == status)
            and (champion is None or t.get("champion") in (None, champion))]


def _met(current, target, cmp: str):
    if current is None or target is None:
        return None
    return {">=": current >= target, "<=": current <= target,
            ">": current > target, "<": current < target}.get(cmp)


def evaluate(summary: dict, tasks: list[dict] | None = None) -> list[dict]:
    """用一回合的汇总数据,核对当前激活任务的进度。"""
    champ = summary.get("champion")
    active = tasks if tasks is not None else list_tasks(champion=champ)
    out = []
    for t in active:
        if t.get("champion") not in (None, champ):
            continue
        row = {"id": t["id"], "desc": t["desc"]}
        metric = t.get("metric")
        if metric and metric in summary:
            current = summary.get(metric)
            row.update({"metric": metric, "target": t.get("target"),
                        "current": current,
                        "met": _met(current, t.get("target"), t.get("cmp", ">="))})
        else:
            row["met"] = None        # 主观任务,需自评
        out.append(row)
    return out


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="成长任务管理")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="布置任务")
    a.add_argument("--desc", required=True)
    a.add_argument("--champion")
    a.add_argument("--metric", choices=sorted(METRICS))
    a.add_argument("--target", type=float)
    a.add_argument("--cmp", default=">=", choices=[">=", "<=", ">", "<"])

    lp = sub.add_parser("list", help="查看任务")
    lp.add_argument("--champion")
    lp.add_argument("--all", action="store_true", help="含已完成/放弃")

    dn = sub.add_parser("done", help="标记完成"); dn.add_argument("id", type=int)
    dr = sub.add_parser("drop", help="放弃任务"); dr.add_argument("id", type=int)

    rv = sub.add_parser("review", help="用汇总核对进度")
    rv.add_argument("summary")

    args = ap.parse_args(argv)

    if args.cmd == "add":
        t = add_task(args.desc, args.champion, args.metric, args.target, args.cmp)
        print(f"已布置任务 #{t['id']}: {t['desc']}")
    elif args.cmd == "list":
        rows = list_tasks(args.champion, status=None if args.all else "active")
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    elif args.cmd == "done":
        print("已标记完成" if set_status(args.id, "done") else "未找到该任务")
    elif args.cmd == "drop":
        print("已放弃" if set_status(args.id, "dropped") else "未找到该任务")
    elif args.cmd == "review":
        doc = json.loads(Path(args.summary).read_text(encoding="utf-8"))
        summary = doc.get("summary", doc)
        print(json.dumps(evaluate(summary), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
