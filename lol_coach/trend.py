"""长期趋势分析:把同一英雄各周期的汇总串起来,看你是变强还是退步。

读取 data/matches/ 下所有 *_汇总.json,按英雄分组、按周期排序,
输出每个英雄的「周期 -> 胜率 / 补刀差 / 参团率 / 经济差」走势,
并对关键指标给出变好/变差的方向判断。

用法:
    python -m lol_coach.trend                 # 分析全部英雄
    python -m lol_coach.trend 武器大师         # 只看某个英雄
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_SAVE_DIR = Path("data/matches")


def _period_key(period: str | None):
    """把 '6.10-6.20' 的起始日期解析成可排序的 (月, 日);无日期排最后。"""
    if not period:
        return (99, 99)
    m = re.match(r"(\d+)[.\-/](\d+)", period)
    return (int(m.group(1)), int(m.group(2))) if m else (99, 99)


def load_summaries(save_dir: Path = _SAVE_DIR) -> list[dict]:
    out = []
    for fp in save_dir.glob("*_汇总.json"):
        try:
            doc = json.loads(fp.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        s = doc.get("summary")
        if s:
            out.append(s)
    return out


def _direction(values: list, higher_is_better: bool) -> str | None:
    """比较首尾两个周期,给出方向。"""
    nums = [v for v in values if isinstance(v, (int, float))]
    if len(nums) < 2:
        return None
    delta = nums[-1] - nums[0]
    if abs(delta) < 1e-9:
        return "持平"
    good = (delta > 0) == higher_is_better
    return f"{'↑' if delta > 0 else '↓'} {'变好' if good else '变差'}({nums[0]}→{nums[-1]})"


def build_trends(summaries: list[dict], champion: str | None = None) -> dict:
    champs: dict[str, list[dict]] = {}
    for s in summaries:
        if champion and s.get("champion") != champion:
            continue
        champs.setdefault(s.get("champion", "未知"), []).append(s)

    result = {}
    for champ, periods in champs.items():
        periods.sort(key=lambda s: _period_key(s.get("period")))
        total_games = sum(p.get("games", 0) for p in periods)
        total_wins = sum(p.get("wins", 0) for p in periods)
        result[champ] = {
            "total_games": total_games,
            "total_wins": total_wins,
            "overall_winrate": f"{round(total_wins / total_games * 100)}%"
            if total_games else None,
            "periods": [
                {
                    "period": p.get("period"),
                    "games": p.get("games"),
                    "winrate": p.get("winrate"),
                    "avg_cs_diff": p.get("avg_cs_diff"),
                    "avg_kp": p.get("avg_kp"),
                    "avg_gold_diff": p.get("avg_gold_diff"),
                }
                for p in periods
            ],
            "trend": {
                "补刀差": _direction([p.get("avg_cs_diff") for p in periods], True),
                "参团率": _direction([p.get("avg_kp") for p in periods], True),
                "经济差": _direction([p.get("avg_gold_diff") for p in periods], True),
            },
        }
    return result


def main(argv: list[str] | None = None) -> int:
    champion = (argv or sys.argv[1:])
    champ = champion[0] if champion else None
    summaries = load_summaries()
    if not summaries:
        print("还没有任何周期汇总,先用 批量识别.bat 处理几个英雄文件夹。",
              file=sys.stderr)
        return 1
    trends = build_trends(summaries, champ)
    print(json.dumps(trends, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
