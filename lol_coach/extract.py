"""命令行入口:截图 -> 紧凑 JSON。

支持两种页面:
  - 对位详情页(掌盟「战绩详情页」,左右两个玩家对比)—— 自动识别
  - 普通结算/数据页(单人标签+数值)

用法:
    # 截图识别 + 解析,打印紧凑 JSON 并存档(自动判断页面类型)
    python -m lol_coach.extract shot.png

    # 强制对位模式 / 指定你在哪一侧(默认左)
    python -m lol_coach.extract shot.png --mode versus --side left

    # 校准用:把 OCR 出来的带坐标文本块(ocr_items 的输出)存成 json 再喂进来
    python -m lol_coach.extract --from-items items.json

    # 无 paddle 时调试普通页:每行一条 OCR 文本
    python -m lol_coach.extract --from-text ocr_lines.txt --mode simple

输出的 JSON 才是要贴进对话给教练分析的东西;截图本身不进对话。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .parse import parse_scoreboard, parse_versus

_SAVE_DIR = Path("data/matches")
_VS_HINTS = ("对位", "参团率", "承受伤害", "给英雄造成")


def _looks_like_versus(texts: list[str]) -> bool:
    joined = " ".join(texts)
    return any(h in joined for h in _VS_HINTS)


def _run(items: list[dict] | None, texts: list[str] | None,
         mode: str, side: str, overrides: dict) -> dict:
    if items is not None:
        all_text = [it["text"] for it in items]
    else:
        all_text = texts or []

    if mode == "auto":
        mode = "versus" if _looks_like_versus(all_text) else "simple"

    if mode == "versus":
        if items is None:
            raise SystemExit("对位模式需要带坐标的输入(截图或 --from-items)")
        data = parse_versus(items, side=side)
    else:
        data = parse_scoreboard(all_text)

    for k, v in overrides.items():
        if v is not None:
            data[k] = v
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="LOL 结算/对位截图 -> 紧凑对局 JSON")
    ap.add_argument("image", nargs="?", help="截图路径")
    ap.add_argument("--from-items", help="读取 ocr_items 的 JSON(带坐标),用于校准")
    ap.add_argument("--from-text", help="读取每行一条的 OCR 文本(仅 simple 模式)")
    ap.add_argument("--mode", choices=["auto", "versus", "simple"], default="auto")
    ap.add_argument("--side", choices=["left", "right"], default="left",
                    help="对位页里哪一侧是你(默认左)")
    ap.add_argument("--champion", help="手动指定英雄")
    ap.add_argument("--result", choices=["胜利", "失败"], help="手动指定胜负")
    ap.add_argument("--no-save", action="store_true")
    ap.add_argument("--save-dir", default=str(_SAVE_DIR))
    args = ap.parse_args(argv)

    items: list[dict] | None = None
    texts: list[str] | None = None

    if args.from_items:
        items = json.loads(Path(args.from_items).read_text(encoding="utf-8"))
    elif args.from_text:
        texts = [ln.strip() for ln in
                 Path(args.from_text).read_text(encoding="utf-8").splitlines()
                 if ln.strip()]
    elif args.image:
        from .ocr import ocr_items  # 延迟导入

        items = ocr_items(args.image)
    else:
        ap.error("需要提供 image / --from-items / --from-text")
        return 2

    overrides = {"champion": args.champion, "result": args.result}
    data = _run(items, texts, args.mode, args.side, overrides)

    text = json.dumps(data, ensure_ascii=False, indent=2)
    print(text)

    if not args.no_save:
        save_dir = Path(args.save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        champ = data.get("champion", "match")
        fp = save_dir / f"match_{stamp}_{champ}.json"
        fp.write_text(text, encoding="utf-8")
        print(f"\n已存档: {fp}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
