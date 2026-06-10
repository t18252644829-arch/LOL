"""把 OCR 出来的零散文本行,解析成结构化的对局数据。

这一层是纯 Python、不依赖任何 OCR 引擎,所以可以单独跑单元测试。
输入:一串按阅读顺序排好的 OCR 文本(list[str])。
输出:紧凑的 dict —— 这个 dict 才是要喂进对话/教练分析的东西。

国服结算界面里,要么是一行行 "标签 + 数字"(数据详情页),
要么是 KDA / 时长 这种有固定格式的串。解析逻辑就围绕这两类。
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

_DATA = Path(__file__).parent / "data" / "champions_zh.json"


def load_champions() -> list[str]:
    """读取国服英雄中文名清单(可在 data/champions_zh.json 里自行增删)。"""
    if _DATA.exists():
        return json.loads(_DATA.read_text(encoding="utf-8"))
    return []


def _to_number(s: str) -> int | None:
    """把 '28,500' / '28.5k' / '14200' 这类字符串转成 int。"""
    s = s.strip().lower().replace(",", "").replace("，", "")
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([km]?)", s)
    if not m:
        return None
    val = float(m.group(1))
    if m.group(2) == "k":
        val *= 1_000
    elif m.group(2) == "m":
        val *= 1_000_000
    return int(round(val))


def _first_number_in(text: str) -> int | None:
    """从一段文本里取第一个数字(支持 1,234 / 12.3k 形式)。"""
    m = re.search(r"\d[\d,，]*(?:\.\d+)?\s*[km]?", text, re.IGNORECASE)
    return _to_number(m.group(0)) if m else None


def _find_value_near(tokens: list[str], keywords: Iterable[str]) -> int | None:
    """找到含某标签关键词的 token,取它(或紧随其后)的数字。

    兼容 '补刀245'(同一 token)和 '补刀' '245'(相邻 token)两种排版。
    """
    kws = list(keywords)
    for i, tok in enumerate(tokens):
        if any(kw in tok for kw in kws):
            here = _first_number_in(tok)
            if here is not None:
                return here
            for j in range(i + 1, min(i + 3, len(tokens))):
                nxt = _first_number_in(tokens[j])
                if nxt is not None:
                    return nxt
    return None


def parse_scoreboard(tokens: list[str], champions: list[str] | None = None) -> dict:
    """主解析函数:OCR 文本行 -> 紧凑对局 dict。"""
    champions = champions if champions is not None else load_champions()
    joined = " ".join(tokens)
    out: dict = {}

    # 胜负
    if "胜利" in joined or "胜　利" in joined:
        out["result"] = "胜利"
    elif "失败" in joined or "失　败" in joined:
        out["result"] = "失败"

    # 英雄(在文本里做子串匹配,取最长命中以避免短名误中)
    hits = [c for c in champions if c and c in joined]
    if hits:
        out["champion"] = max(hits, key=len)

    # 时长 mm:ss
    m = re.search(r"(\d{1,2})\s*[:：]\s*(\d{2})", joined)
    if m:
        minutes, seconds = int(m.group(1)), int(m.group(2))
        out["duration"] = f"{minutes}:{seconds:02d}"
        out["duration_min"] = round(minutes + seconds / 60, 2)

    # KDA  k/d/a
    m = re.search(r"(\d{1,2})\s*[/／]\s*(\d{1,2})\s*[/／]\s*(\d{1,2})", joined)
    if m:
        k, d, a = int(m.group(1)), int(m.group(2)), int(m.group(3))
        out["kda"] = [k, d, a]
        out["kda_ratio"] = round((k + a) / d, 2) if d else float(k + a)

    # 标签 -> 数值
    cs = _find_value_near(tokens, ["补刀", "小兵", "正补"])
    if cs is not None:
        out["cs"] = cs
        if out.get("duration_min"):
            out["cs_per_min"] = round(cs / out["duration_min"], 1)

    gold = _find_value_near(tokens, ["金币", "经济", "获得金币"])
    if gold is not None:
        out["gold"] = gold

    dmg = _find_value_near(tokens, ["对英雄伤害", "造成伤害", "输出"])
    if dmg is not None:
        out["damage_dealt"] = dmg

    taken = _find_value_near(tokens, ["承受伤害", "承受的伤害", "承伤"])
    if taken is not None:
        out["damage_taken"] = taken

    vision = _find_value_near(tokens, ["视野得分", "视野"])
    if vision is not None:
        out["vision_score"] = vision

    wards = _find_value_near(tokens, ["插眼", "放置守卫", "守卫"])
    if wards is not None:
        out["wards_placed"] = wards

    return out
