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


# ---------------------------------------------------------------------------
# 对位对比页(掌盟「战绩详情页 / 战局」):左右两个玩家并排,中间是标签。
# 用 x 坐标把每行的值分到「你(左) / 对手(右)」,默认左=你。
# ---------------------------------------------------------------------------

# (标签子串, 输出字段名, 取值类型) —— 类型: int / percent / wards
_VS_FIELDS = [
    ("参团率", "kp", "percent"),
    ("反眼", "wards", "wards"),          # "插/反眼" 列,值形如 6/0
    ("最大多杀", "max_multikill", "int"),
    ("补刀", "cs", "int"),
    ("最大连杀", "max_spree", "int"),
    ("推塔数", "towers", "int"),
    ("总伤害", "dmg_to_champ", "int"),
    ("物理伤害", "physical_dmg", "int"),
    ("魔法伤害", "magic_dmg", "int"),
    ("承受伤害", "dmg_taken", "int"),
    ("回复生命", "healing", "int"),
    ("经济", "gold", "int"),             # "对位经济差",值形如 6.1k
]


def _pick_value(items: list[dict], vtype: str):
    """从同一行、某一侧的若干文本块里,按类型取出目标值。

    伤害/经济这类行里同时有百分比和绝对值(如 "47.7%" 和 "8326"),
    int 类型会跳过带 % 的块,只取绝对值。
    """
    for it in items:
        t = it["text"]
        if vtype == "percent":
            m = re.search(r"(\d+(?:\.\d+)?)\s*%", t)
            if m:
                return float(m.group(1))
        elif vtype == "wards":
            m = re.search(r"\d+\s*/\s*\d+", t)
            if m:
                return m.group(0).replace(" ", "")
        else:  # int —— 先抹掉百分比(如 47.7%),再取绝对数(支持 6.1k)
            cleaned = re.sub(r"\d+(?:\.\d+)?\s*%", " ", t)
            n = _first_number_in(cleaned)
            if n is not None:
                return n
    return None


def parse_versus(items: list[dict], side: str = "left",
                 champions: list[str] | None = None, band: float = 28.0) -> dict:
    """对位对比页解析:OCR 文本块(带坐标) -> 紧凑 dict(含你 vs 对手 + 差值)。

    side: "left" 或 "right" —— 哪一列是「你」。掌盟里查自己战绩时你在左列。
    band: 判定「同一行」的 y 像素容差。
    """
    champions = champions if champions is not None else load_champions()
    out: dict = {}
    if not items:
        return out

    # 胜负:结果条左侧标「我方胜利/失败」,右侧标「敌方…」
    for it in items:
        if "我方" in it["text"]:
            out["result"] = "胜利" if "胜利" in it["text"] else (
                "失败" if "失败" in it["text"] else None)
            break

    def beside(label: dict, vtype: str, want: str):
        """居中标签:取同一行、左/右那一侧的值(下半部分伤害块)。"""
        row = [it for it in items
               if it is not label and abs(it["cy"] - label["cy"]) <= band]
        left = sorted([it for it in row if it["cx"] < label["cx"]],
                      key=lambda it: -it["cx"])   # 靠近标签的优先
        right = sorted([it for it in row if it["cx"] > label["cx"]],
                       key=lambda it: it["cx"])
        mine_side, opp_side = (left, right) if side == "left" else (right, left)
        return _pick_value(mine_side if want == "mine" else opp_side, vtype)

    def above(label: dict, vtype: str, xtol: float = 60.0, ymax: float = 70.0):
        """数字在标签正上方:取同列、紧挨在上的值(上半部分小格子)。"""
        cand = [it for it in items
                if it is not label and abs(it["cx"] - label["cx"]) < xtol
                and 0 < (label["cy"] - it["cy"]) <= ymax]
        cand.sort(key=lambda it: label["cy"] - it["cy"])  # 最近的在上面
        return _pick_value(cand, vtype)

    for substr, key, vtype in _VS_FIELDS:
        labels = [it for it in items if substr in it["text"]]
        if not labels:
            continue
        if len(labels) >= 2:
            # 每侧各一个标签、数字在上方
            labels.sort(key=lambda it: it["cx"])
            mine_lbl = labels[0] if side == "left" else labels[-1]
            opp_lbl = labels[-1] if side == "left" else labels[0]
            mine, opp = above(mine_lbl, vtype), above(opp_lbl, vtype)
        else:
            # 居中单标签、数字在两侧
            mine = beside(labels[0], vtype, "mine")
            opp = beside(labels[0], vtype, "opp")
        if mine is None:
            continue
        out[key] = mine
        if opp is not None:
            out[f"{key}_opp"] = opp
            if vtype == "int":
                out[f"{key}_diff"] = mine - opp

    return out
