"""解析层的单元测试 —— 用模拟的 OCR 文本验证逻辑,无需安装 OCR 引擎。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lol_coach.parse import _to_number, parse_scoreboard  # noqa: E402


def test_to_number():
    assert _to_number("28,500") == 28500
    assert _to_number("14200") == 14200
    assert _to_number("28.5k") == 28500
    assert _to_number("12,3") == 123
    assert _to_number("abc") is None


def test_parse_detail_page():
    # 模拟「数据详情页」那种 标签+数值 的 OCR 文本行
    tokens = [
        "胜利", "亚索", "32:15",
        "8 / 5 / 7",
        "补刀", "245",
        "金币", "14200",
        "对英雄伤害", "28,500",
        "承受伤害", "19000",
        "视野得分", "18",
        "插眼", "9",
    ]
    d = parse_scoreboard(tokens)
    assert d["result"] == "胜利"
    assert d["champion"] == "亚索"
    assert d["duration"] == "32:15"
    assert d["duration_min"] == 32.25
    assert d["kda"] == [8, 5, 7]
    assert d["kda_ratio"] == 3.0
    assert d["cs"] == 245
    assert d["cs_per_min"] == 7.6
    assert d["gold"] == 14200
    assert d["damage_dealt"] == 28500
    assert d["damage_taken"] == 19000
    assert d["vision_score"] == 18
    assert d["wards_placed"] == 9


def test_parse_inline_label_value():
    # 标签和数字粘在同一个 token 里(补刀245)的情况
    tokens = ["失败", "盖伦", "25:48", "3/8/4", "补刀178", "视野得分12"]
    d = parse_scoreboard(tokens)
    assert d["result"] == "失败"
    assert d["champion"] == "盖伦"
    assert d["kda"] == [3, 8, 4]
    assert d["cs"] == 178
    assert d["vision_score"] == 12


def test_missing_fields_are_omitted():
    d = parse_scoreboard(["随便一些不相关的文字"])
    assert "kda" not in d
    assert "champion" not in d


if __name__ == "__main__":
    import traceback

    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"\n{len(fns) - failed}/{len(fns)} passed")
    raise SystemExit(1 if failed else 0)
