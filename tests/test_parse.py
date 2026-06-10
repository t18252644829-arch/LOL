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


def test_weakness_and_search_plan():
    from lol_coach.learn.weakness import derive_weaknesses, build_search_plan
    summary = {"champion": "武器大师", "avg_kp": 22.2,
               "avg_cs_diff": -22, "avg_gold_diff": -600}
    ws = derive_weaknesses(summary)
    keys = [w["key"] for w in ws]
    assert "参团率低" in keys and "补刀落后" in keys and "经济落后" in keys
    # 补刀落后(severity 22)应排在参团率低(severity 22.8?)附近且都在前
    plan = build_search_plan(summary)
    assert plan[0]["queries"], "应生成具体搜索词"
    assert any("武器大师" in q for q in plan[0]["queries"])  # 英雄名已填入


def test_search_plan_fallback_when_no_weakness():
    from lol_coach.learn.weakness import build_search_plan
    plan = build_search_plan({"champion": "亚索", "avg_kp": 60,
                              "avg_cs_diff": 10, "avg_gold_diff": 500})
    assert len(plan) == 1 and plan[0]["weakness"] == "进阶提升"


def test_recommend_orchestration_with_fake_search():
    from lol_coach.learn.recommend import recommend
    calls = []

    def fake(query, source="bili", limit=5):
        calls.append((query, source))
        return [{"title": f"{query}-{source}", "url": f"u/{query}/{source}",
                 "uploader": "up", "duration": 600, "views": 1000, "source": source}]

    summary = {"champion": "武器大师", "avg_cs_diff": -22}
    result = recommend(summary, ["bili", "youtube"], per=3, searcher=fake)
    assert result["sections"], "应有推荐分区"
    assert all("videos" in s for s in result["sections"])
    assert calls, "应调用了搜索"


def _fake_ddragon(champ_zh="武器大师", cid="Jax"):
    """构造一个可注入的 Data Dragon getter,模拟官方 JSON 结构。"""
    def getter(url, timeout=20):
        if url.endswith("/api/versions.json"):
            return ["14.10.1", "14.9.1"]
        if "/champion.json" in url:
            return {"data": {cid: {"name": champ_zh}, "Garen": {"name": "盖伦"}}}
        if f"/champion/{cid}.json" in url:
            return {"data": {cid: {
                "title": "武器大师", "tags": ["Fighter"], "partype": "法力",
                "passive": {"name": "致命打击"},
                "spells": [
                    {"name": "勇往直前", "cooldownBurn": "3.5", "costBurn": "65"},
                    {"name": "气定神闲", "cooldownBurn": "9", "costBurn": "30"},
                    {"name": "武器闪击", "cooldownBurn": "7", "costBurn": "30"},
                    {"name": "无双剑姬", "cooldownBurn": "100", "costBurn": "100"},
                ],
                "stats": {"hp": 685, "armor": 36, "spellblock": 32,
                          "attackdamage": 68, "movespeed": 350, "attackrange": 125},
            }}}
        raise AssertionError(f"未预期的 url: {url}")
    return getter


def test_scout_champion_facts():
    from lol_coach.learn.scout import champion_facts
    facts = champion_facts("武器大师", getter=_fake_ddragon())
    assert facts["version"] == "14.10.1"
    assert facts["id"] == "Jax"
    assert [s["key"] for s in facts["spells"]] == ["Q", "W", "E", "R"]
    assert facts["spells"][3]["name"] == "无双剑姬"
    assert facts["base_stats"]["armor"] == 36


def test_scout_unknown_champion():
    from lol_coach.learn.scout import champion_facts
    facts = champion_facts("不存在的英雄", getter=_fake_ddragon())
    assert "error" in facts


def test_build_brief_bundles_data_and_facts():
    from lol_coach.learn.brief import build_brief
    from lol_coach.learn.scout import champion_facts
    summary = {"champion": "武器大师", "period": "6.10-6.20", "winrate": "100%",
               "avg_cs_diff": -22, "avg_kp": 22.2}
    getter = _fake_ddragon()
    brief = build_brief(summary, rank="黄金",
                        facts_getter=lambda c, version=None: champion_facts(c, getter=getter))
    assert brief["我的段位"] == "黄金"
    assert brief["我的数据"]["avg_cs_diff"] == -22
    assert brief["当前版本事实"]["id"] == "Jax"
    assert len(brief["请你分析"]) == 5


def test_patch_url_and_html_to_text():
    from lol_coach.learn.patchnotes import patch_url, html_to_text, fetch_patch_notes
    assert patch_url("14.10.1") == \
        "https://www.leagueoflegends.com/en-us/news/game-updates/patch-14-10-notes/"
    assert patch_url("14.10") == \
        "https://www.leagueoflegends.com/en-us/news/game-updates/patch-14-10-notes/"
    html = "<html><style>x{}</style><body><h1>Patch 14.10</h1><p>武器大师 Q 调整</p></body></html>"
    assert html_to_text(html) == "Patch 14.10 武器大师 Q 调整"
    # 注入 getter,验证抓取+截断逻辑
    res = fetch_patch_notes("14.10", getter=lambda url, timeout=20: html, max_chars=5)
    assert res["version"] == "14.10" and res["truncated"] is True


def test_meta_url_and_parse():
    from lol_coach.learn.meta import meta_url, norm_patch, parse_meta, fetch_meta
    assert norm_patch("14.10.1") == "14.10"
    url = meta_url("24", "top", "14.10")
    assert "cid=24" in url and "lane=top" in url and "patch=14.10" in url
    parsed = parse_meta({"header": {"wr": 51.2, "pr": 8.3, "br": 2.1, "n": 12000}})
    assert parsed["winrate"] == 51.2 and parsed["games"] == 12000
    # 未知结构应给出校准提示
    assert "_note" in parse_meta({"weird": 1})
    # 注入 getter
    got = fetch_meta("24", "top", "14.10",
                     getter=lambda url, timeout=25: {"header": {"wr": 50}})
    assert got["winrate"] == 50 and "url" in got


def test_vtt_to_text():
    from lol_coach.learn.subtitles import _vtt_to_text
    vtt = (
        "WEBVTT\n\n1\n00:00:01.000 --> 00:00:03.000\n大家好今天讲补刀\n"
        "2\n00:00:03.000 --> 00:00:05.000\n大家好今天讲补刀\n"   # 重复行
        "3\n00:00:05.000 --> 00:00:07.000\n第一点是补兵节奏\n"
    )
    text = _vtt_to_text(vtt)
    assert text == "大家好今天讲补刀 第一点是补兵节奏"


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
