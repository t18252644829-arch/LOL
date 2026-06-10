"""lol_coach —— 国服 LOL 截图诊断小工具。

分层:
  ocr.py     截图 -> OCR 文本行(依赖 PaddleOCR,本地运行)
  parse.py   OCR 文本行 -> 紧凑对局 dict(纯 Python,可测试)
  extract.py 命令行入口,把上面两层串起来
"""

from .parse import parse_scoreboard

__all__ = ["parse_scoreboard"]
