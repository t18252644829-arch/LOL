"""按英雄文件夹批量识别 + 汇总。

用法:
    python -m lol_coach.batch "某个文件夹"

约定:**文件夹名 = 英雄名**。把同一个英雄的多张对位截图丢进
「武器大师」这种文件夹,工具会:
  1. 识别文件夹里每一张图 -> 每局一条记录(自动打上英雄=文件夹名)
  2. 汇总这个英雄的胜率、平均补刀差、平均参团率等趋势
  3. 把结果存到 data/matches/<英雄>_汇总.json,并打印出来

这样你不用每次敲命令、也不用手动标英雄,把文件夹拖到「批量识别.bat」即可。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from .parse import parse_versus

_IMG_EXT = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
_SAVE_DIR = Path("data/matches")


def _avg(matches: list[dict], key: str):
    vals = [m[key] for m in matches if isinstance(m.get(key), (int, float))]
    return round(sum(vals) / len(vals), 1) if vals else None


def summarize(champion: str, matches: list[dict]) -> dict:
    n = len(matches)
    wins = sum(1 for m in matches if m.get("result") == "胜利")
    return {
        "champion": champion,
        "games": n,
        "wins": wins,
        "winrate": f"{round(wins / n * 100)}%" if n else None,
        "avg_kp": _avg(matches, "kp"),
        "avg_cs": _avg(matches, "cs"),
        "avg_cs_diff": _avg(matches, "cs_diff"),
        "avg_dmg": _avg(matches, "dmg_to_champ"),
        "avg_gold_diff": _avg(matches, "gold_diff"),
    }


def process_folder(folder: str, side: str = "left") -> dict:
    from .ocr import ocr_items  # 延迟导入

    folder_p = Path(folder)
    champion = folder_p.name  # 文件夹名 = 英雄名
    images = sorted(p for p in folder_p.iterdir() if p.suffix.lower() in _IMG_EXT)

    matches = []
    for img in images:
        data = parse_versus(ocr_items(str(img)), side=side)
        data["champion"] = champion
        data["_file"] = img.name
        matches.append(data)
        print(f"  ✓ {img.name}", file=sys.stderr)

    return {"summary": summarize(champion, matches), "matches": matches}


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="按英雄文件夹批量识别 + 汇总")
    ap.add_argument("folder", help="英雄文件夹路径(文件夹名即英雄名)")
    ap.add_argument("--side", choices=["left", "right"], default="left",
                    help="对位页里哪一侧是你(默认左)")
    ap.add_argument("--save-dir", default=str(_SAVE_DIR))
    args = ap.parse_args(argv)

    if not Path(args.folder).is_dir():
        print(f"不是文件夹: {args.folder}", file=sys.stderr)
        return 2

    result = process_folder(args.folder, side=args.side)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    print(text)

    save_dir = Path(args.save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    fp = save_dir / f"{result['summary']['champion']}_汇总.json"
    fp.write_text(text, encoding="utf-8")
    print(f"\n已存档: {fp}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
