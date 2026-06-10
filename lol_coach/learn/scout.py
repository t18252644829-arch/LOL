"""情报采集(官方源):Riot Data Dragon。

拿当前(或指定)版本的英雄客观数据:技能名/CD/消耗、被动、基础数值、定位标签,
全中文(locale=zh_CN)。这是「锚定真实版本」用的,避免我凭记忆给过时数值。

国服版本通常比国际服慢,但 Data Dragon 保留历史版本——用 --version 锁国服
客户端显示的版本号,就能拿到与国服一致的数据。

所有取数走可注入的 getter,便于离线单元测试。
"""
from __future__ import annotations

import json
import urllib.request

DDRAGON = "https://ddragon.leagueoflegends.com"


def _get_json(url: str, timeout: int = 20):
    req = urllib.request.Request(url, headers={"User-Agent": "lol-coach"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def latest_version(getter=_get_json) -> str:
    return getter(f"{DDRAGON}/api/versions.json")[0]


def champion_index(version: str, locale: str = "zh_CN", getter=_get_json) -> dict:
    """返回 {中文名: 英雄id}。"""
    data = getter(f"{DDRAGON}/cdn/{version}/data/{locale}/champion.json")["data"]
    return {info["name"]: cid for cid, info in data.items()}


def _compact_champion(version: str, name: str, cid: str, d: dict) -> dict:
    keys = ["Q", "W", "E", "R"]
    spells = [
        {"key": k, "name": s.get("name"),
         "cd": s.get("cooldownBurn"), "cost": s.get("costBurn")}
        for k, s in zip(keys, d.get("spells", []))
    ]
    stats = d.get("stats", {})
    want = ("hp", "armor", "spellblock", "attackdamage", "attackspeed",
            "movespeed", "attackrange")
    return {
        "version": version,
        "champion": name,
        "id": cid,
        "key": d.get("key"),                   # 数字id,社区站(lolalytics等)用
        "title": d.get("title"),
        "tags": d.get("tags"),                 # Fighter / Tank / Mage ...
        "partype": d.get("partype"),           # 法力 / 能量 ...
        "passive": (d.get("passive") or {}).get("name"),
        "spells": spells,
        "base_stats": {k: stats[k] for k in want if k in stats},
    }


def champion_facts(name_zh: str, version: str | None = None,
                   locale: str = "zh_CN", getter=_get_json) -> dict:
    """拿某英雄在指定/最新版本的客观数据。"""
    version = version or latest_version(getter)
    idx = champion_index(version, locale, getter)
    cid = idx.get(name_zh)
    if not cid:
        return {"version": version, "champion": name_zh,
                "error": f"在版本 {version} 未找到英雄「{name_zh}」,检查名字或换版本号"}
    detail = getter(
        f"{DDRAGON}/cdn/{version}/data/{locale}/champion/{cid}.json"
    )["data"][cid]
    return _compact_champion(version, name_zh, cid, detail)


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="抓取英雄当前版本客观数据(Data Dragon)")
    ap.add_argument("champion", help="英雄中文名,如 武器大师")
    ap.add_argument("--version", help="锁定版本号(填国服客户端显示的版本)")
    args = ap.parse_args(argv)

    facts = champion_facts(args.champion, version=args.version)
    print(json.dumps(facts, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
