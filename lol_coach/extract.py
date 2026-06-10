"""命令行入口:截图 -> 紧凑 JSON。

用法:
    # 从截图识别并解析,打印紧凑 JSON,同时存档
    python -m lol_coach.extract shot.png

    # OCR 漏识别时手动兜底某些字段
    python -m lol_coach.extract shot.png --champion 亚索 --result 胜利

    # 已经有 OCR 文本(每行一条),只跑解析(调试/无 paddle 环境)
    python -m lol_coach.extract --from-text ocr_lines.txt

输出的 JSON 才是要贴进对话给教练分析的东西;截图本身不进对话。
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from .parse import parse_scoreboard

_SAVE_DIR = Path("data/matches")


def _build(tokens: list[str], overrides: dict) -> dict:
    data = parse_scoreboard(tokens)
    for k, v in overrides.items():
        if v is not None:
            data[k] = v
    return data


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="LOL 结算截图 -> 紧凑对局 JSON")
    ap.add_argument("image", nargs="?", help="结算截图路径")
    ap.add_argument("--from-text", help="改为读取已有 OCR 文本文件(每行一条)")
    ap.add_argument("--champion", help="手动指定英雄(OCR 漏识别时兜底)")
    ap.add_argument("--result", choices=["胜利", "失败"], help="手动指定胜负")
    ap.add_argument("--no-save", action="store_true", help="只打印,不存档")
    ap.add_argument("--save-dir", default=str(_SAVE_DIR), help="存档目录")
    args = ap.parse_args(argv)

    if args.from_text:
        tokens = [
            ln.strip()
            for ln in Path(args.from_text).read_text(encoding="utf-8").splitlines()
            if ln.strip()
        ]
    elif args.image:
        from .ocr import ocr_image  # 延迟导入,避免无 paddle 时报错

        tokens = ocr_image(args.image)
    else:
        ap.error("需要提供 image 或 --from-text")
        return 2

    overrides = {"champion": args.champion, "result": args.result}
    data = _build(tokens, overrides)

    text = json.dumps(data, ensure_ascii=False, indent=2)
    print(text)

    if not args.no_save:
        save_dir = Path(args.save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        champ = data.get("champion", "unknown")
        fp = save_dir / f"match_{stamp}_{champ}.json"
        fp.write_text(text, encoding="utf-8")
        print(f"\n已存档: {fp}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
