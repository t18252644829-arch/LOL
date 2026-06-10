"""按「英雄 + 日期段」文件夹批量识别 + 汇总。

约定:文件夹名 = 英雄名 + 日期段,例如 `武器大师6.10-6.20`。
工具会拆成 英雄=武器大师、周期=6.10-6.20,每个周期单独存一份汇总,
不同周期互不覆盖,方便后续做长期趋势对比(见 trend.py)。

用法:
    python -m lol_coach.batch "武器大师6.10-6.20"

特性:
  - 文件夹名自动拆「英雄 / 周期」
  - 缓存:同一张图(路径+大小不变)识别过就跳过,不重复 OCR
  - 汇总:胜率、平均补刀差、平均参团率等
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from .parse import parse_versus

_IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
_SAVE_DIR = Path("data/matches")
_CACHE = Path("data/cache.json")


def split_champion_period(folder_name: str) -> tuple[str, str | None]:
    """把文件夹名拆成 (英雄名, 周期)。周期从第一个数字开始。

    '武器大师6.10-6.20' -> ('武器大师', '6.10-6.20')
    '亚索 6.10-6.20'    -> ('亚索', '6.10-6.20')
    '武器大师'          -> ('武器大师', None)
    """
    m = re.search(r"\d", folder_name)
    if not m:
        return folder_name.strip(), None
    champ = folder_name[:m.start()].strip(" -_")
    period = folder_name[m.start():].strip(" -_")
    return (champ or folder_name.strip()), (period or None)


def _avg(matches: list[dict], key: str):
    vals = [m[key] for m in matches if isinstance(m.get(key), (int, float))]
    return round(sum(vals) / len(vals), 1) if vals else None


def _avg_deaths(matches: list[dict]):
    deaths = [m["kda"][1] for m in matches
              if isinstance(m.get("kda"), list) and len(m["kda"]) == 3]
    return round(sum(deaths) / len(deaths), 1) if deaths else None


def summarize(champion: str, period: str | None, matches: list[dict]) -> dict:
    n = len(matches)
    wins = sum(1 for m in matches if m.get("result") == "胜利")
    return {
        "champion": champion,
        "period": period,
        "games": n,
        "wins": wins,
        "winrate": f"{round(wins / n * 100)}%" if n else None,
        "avg_kp": _avg(matches, "kp"),
        "avg_cs": _avg(matches, "cs"),
        "avg_cs_diff": _avg(matches, "cs_diff"),
        "avg_deaths": _avg_deaths(matches),
        "avg_dmg": _avg(matches, "dmg_to_champ"),
        "avg_gold_diff": _avg(matches, "gold_diff"),
    }


def _load_cache() -> dict:
    if _CACHE.exists():
        try:
            return json.loads(_CACHE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def process_folder(folder: str, side: str = "left") -> dict:
    from .ocr import ocr_items  # 延迟导入

    folder_p = Path(folder)
    champion, period = split_champion_period(folder_p.name)
    images = sorted(p for p in folder_p.iterdir() if p.suffix.lower() in _IMG_EXT)

    cache = _load_cache()
    cache_dirty = False
    matches = []
    for img in images:
        key = f"{img.resolve()}|{img.stat().st_size}"
        if key in cache:
            data = dict(cache[key])
            print(f"  · {img.name}(缓存)", file=sys.stderr)
        else:
            data = parse_versus(ocr_items(str(img)), side=side)
            cache[key] = data
            cache_dirty = True
            print(f"  ✓ {img.name}", file=sys.stderr)
        data["champion"] = champion
        data["_file"] = img.name
        matches.append(data)

    if cache_dirty:
        _CACHE.parent.mkdir(parents=True, exist_ok=True)
        _CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")

    return {"summary": summarize(champion, period, matches), "matches": matches}


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="按英雄+日期段文件夹批量识别 + 汇总")
    ap.add_argument("folder", help="文件夹路径(名字=英雄名+日期段)")
    ap.add_argument("--side", choices=["left", "right"], default="left")
    ap.add_argument("--save-dir", default=str(_SAVE_DIR))
    args = ap.parse_args(argv)

    if not Path(args.folder).is_dir():
        print(f"不是文件夹: {args.folder}", file=sys.stderr)
        return 2

    result = process_folder(args.folder, side=args.side)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)

    s = result["summary"]
    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    tag = f"{s['champion']}_{s['period']}" if s["period"] else s["champion"]
    fp = save_dir / f"{tag}_汇总.json"
    fp.write_text(text, encoding="utf-8")
    print(f"\n已存档: {fp}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
