"""把阶段一的汇总/趋势数据,变成「弱点 + 搜索计划」。

纯逻辑、无网络,可单元测试。输入是 batch.py 产出的 summary dict
(含 champion / avg_kp / avg_cs_diff / avg_gold_diff / winrate 等)。
"""
from __future__ import annotations

# 每条规则:命中条件 + 严重度 + 对应搜索主题(用 {champ} 占位英雄名)+ 建议
_RULES = [
    {
        "key": "参团率低",
        "metric": "avg_kp",
        "hit": lambda v: v is not None and v < 45,
        "severity": lambda v: 45 - v,
        "topics": ["{champ} 团战 切入 时机", "{champ} 游走 gank 教学", "如何提高参团率"],
        "advice": "团战参与太低,重点练游走时机和团战切入。",
    },
    {
        "key": "补刀落后",
        "metric": "avg_cs_diff",
        "hit": lambda v: v is not None and v < -8,
        "severity": lambda v: -v,
        "topics": ["{champ} 对线 补刀 教学", "{champ} 对线期 细节", "补刀 提升 训练"],
        "advice": "对线补刀落后,练补刀基本功和对线节奏。",
    },
    {
        "key": "经济落后",
        "metric": "avg_gold_diff",
        "hit": lambda v: v is not None and v < -250,
        "severity": lambda v: -v / 100,
        "topics": ["{champ} 出装 思路", "对线 压制 滚雪球 教学", "{champ} 运营 教学"],
        "advice": "经济落后,优化出装与对线压制/滚雪球思路。",
    },
]

# 没有明显弱点时的兜底:就看进阶/高端局
_FALLBACK = {
    "key": "进阶提升",
    "advice": "没有明显短板,看高端局学进阶细节。",
    "topics": ["{champ} 进阶 教学 高端局", "{champ} 天梯 上分 教学"],
}


def derive_weaknesses(summary: dict) -> list[dict]:
    """返回按严重度从高到低排序的弱点列表。"""
    found = []
    for rule in _RULES:
        v = summary.get(rule["metric"])
        if rule["hit"](v):
            found.append({
                "key": rule["key"],
                "metric": rule["metric"],
                "value": v,
                "severity": round(rule["severity"](v), 2),
                "topics": rule["topics"],
                "advice": rule["advice"],
            })
    found.sort(key=lambda w: w["severity"], reverse=True)
    return found


def build_search_plan(summary: dict, max_weaknesses: int = 3) -> list[dict]:
    """弱点 -> 搜索计划:[{weakness, advice, queries:[...]}]。"""
    champ = (summary.get("champion") or "").strip()
    weaknesses = derive_weaknesses(summary)[:max_weaknesses]
    if not weaknesses:
        weaknesses = [{"key": _FALLBACK["key"], "advice": _FALLBACK["advice"],
                       "topics": _FALLBACK["topics"]}]

    plan = []
    for w in weaknesses:
        queries = []
        for t in w["topics"]:
            q = t.replace("{champ}", champ).strip()
            q = " ".join(q.split())          # 去掉英雄名为空时的多余空格
            if q and q not in queries:
                queries.append(q)
        plan.append({"weakness": w["key"], "advice": w["advice"], "queries": queries})
    return plan
