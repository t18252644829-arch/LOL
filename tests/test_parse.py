"""解析层的单元测试 —— 用模拟的 OCR 文本验证逻辑,无需安装 OCR 引擎。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lol_coach.parse import _to_number, parse_scoreboard, parse_versus  # noqa: E402


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


def _it(text, cx, cy):
    return {"text": text, "cx": cx, "cy": cy}


def test_parse_versus_real_layout():
    """模拟掌盟对位页(真实截图排版):上半=数字在标签上方且左右各一标签,
    下半=居中单标签两侧夹值。左列=你。"""
    items = [
        _it("我方胜利", 150, 445), _it("18/8/17", 330, 445),  # 队伍总和(最上,排除)
        _it("3/2/1", 110, 620), _it("2/3/2", 800, 620),       # 两名玩家 KDA
        # —— 上半块:value 在上(cy=1000/1090),label 在下(cy=1035/1125)
        _it("22.2%", 95, 1000), _it("参团率", 95, 1035),
        _it("6/0", 230, 1000), _it("插/反眼", 230, 1035),
        _it("1", 365, 1000), _it("最大多杀", 365, 1035),
        _it("50.0%", 560, 1000), _it("参团率", 560, 1035),
        _it("3/0", 695, 1000), _it("插/反眼", 695, 1035),
        _it("1", 825, 1000), _it("最大多杀", 825, 1035),
        _it("117", 95, 1090), _it("补刀", 95, 1125),
        _it("2", 230, 1090), _it("最大连杀", 230, 1125),
        _it("0", 365, 1090), _it("推塔数", 365, 1125),
        _it("139", 560, 1090), _it("补刀", 560, 1125),
        _it("0", 695, 1090), _it("最大连杀", 695, 1125),
        _it("0", 825, 1090), _it("推塔数", 825, 1125),
        # —— 下半块:居中标签,左右夹值(含百分比干扰)
        _it("47.7%", 80, 1250), _it("8326", 250, 1250),
        _it("给英雄造成的总伤害", 460, 1250), _it("9100", 680, 1250), _it("52.3%", 850, 1250),
        _it("15%", 80, 1360), _it("1199", 250, 1360),
        _it("给英雄造成的物理伤害", 460, 1360), _it("6779", 680, 1360), _it("85%", 850, 1360),
        _it("83%", 80, 1470), _it("6622", 250, 1470),
        _it("给英雄造成的魔法伤害", 460, 1470), _it("1356", 680, 1470), _it("17%", 850, 1470),
        _it("50.2%", 80, 1580), _it("10012", 250, 1580),
        _it("承受伤害", 460, 1580), _it("9909", 680, 1580), _it("49.8%", 850, 1580),
        _it("63.1%", 80, 1690), _it("3719", 250, 1690),
        _it("回复生命", 460, 1690), _it("2170", 680, 1690), _it("36.9%", 850, 1690),
        _it("6.1k", 250, 1800), _it("47.3%", 380, 1800),
        _it("对位经济差", 460, 1800), _it("52.7%", 540, 1800), _it("6.7k", 680, 1800),
    ]
    d = parse_versus(items, side="left")
    assert d["result"] == "胜利"
    assert d["kp"] == 22.2 and d["kp_opp"] == 50.0
    assert d["wards"] == "6/0" and d["wards_opp"] == "3/0"
    assert d["cs"] == 117 and d["cs_opp"] == 139 and d["cs_diff"] == -22
    assert d["max_spree"] == 2 and d["max_spree_opp"] == 0
    assert d["towers"] == 0 and d["towers_opp"] == 0
    assert d["dmg_to_champ"] == 8326 and d["dmg_to_champ_opp"] == 9100
    assert d["physical_dmg"] == 1199 and d["magic_dmg"] == 6622
    assert d["dmg_taken"] == 10012 and d["dmg_taken_opp"] == 9909
    assert d["healing"] == 3719 and d["healing_opp"] == 2170
    assert d["gold"] == 6100 and d["gold_opp"] == 6700 and d["gold_diff"] == -600
    assert d["kda"] == [3, 2, 1] and d["kda_ratio"] == 2.0  # 左=你,排除队伍总和


def test_missing_fields_are_omitted():
    d = parse_scoreboard(["随便一些不相关的文字"])
    assert "kda" not in d
    assert "champion" not in d


def test_split_champion_period():
    from lol_coach.batch import split_champion_period
    assert split_champion_period("武器大师6.10-6.20") == ("武器大师", "6.10-6.20")
    assert split_champion_period("亚索 6.10-6.20") == ("亚索", "6.10-6.20")
    assert split_champion_period("武器大师") == ("武器大师", None)


def test_trend_direction_and_sort():
    from lol_coach.trend import build_trends
    summaries = [
        {"champion": "武器大师", "period": "6.20-6.30", "games": 5, "wins": 4,
         "winrate": "80%", "avg_cs_diff": 5, "avg_kp": 45, "avg_gold_diff": 300},
        {"champion": "武器大师", "period": "6.10-6.20", "games": 3, "wins": 1,
         "winrate": "33%", "avg_cs_diff": -22, "avg_kp": 22, "avg_gold_diff": -600},
    ]
    t = build_trends(summaries)["武器大师"]
    assert t["total_games"] == 8 and t["total_wins"] == 5
    # 按周期升序:6.10 在前、6.20 在后
    assert [p["period"] for p in t["periods"]] == ["6.10-6.20", "6.20-6.30"]
    # 补刀差 -22 -> 5,越高越好 => 变好
    assert "变好" in t["trend"]["补刀差"]


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
