"""OCR 层:把一张结算/对位截图变成文本。

依赖 PaddleOCR(中文+数字识别好,本地离线运行)。只在真正用到时才
import,这样纯解析逻辑(parse.py)可以在没装 paddle 的环境里照样测试。

提供两种输出:
  ocr_image(path) -> list[str]            按阅读顺序的文本行(简单页面)
  ocr_items(path) -> list[dict]           带坐标的文本块(对位对比页需要)
"""
from __future__ import annotations

from functools import lru_cache

_LANG = "ch"  # 中英文混合


@lru_cache(maxsize=1)
def _get_engine():
    from paddleocr import PaddleOCR  # 延迟导入

    return PaddleOCR(use_angle_cls=True, lang=_LANG, show_log=False)


def _raw(path: str):
    result = _get_engine().ocr(path, cls=True)
    return result[0] if result and result[0] else []


def ocr_items(path: str) -> list[dict]:
    """识别图片,返回每个文本块的 {text, cx, cy}(中心坐标)。

    对位对比页需要 x 坐标来区分「左列=你 / 右列=对手」。
    """
    items = []
    for box, (text, conf) in _raw(path):
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        items.append(
            {
                "text": text,
                "cx": sum(xs) / len(xs),
                "cy": sum(ys) / len(ys),
            }
        )
    return items


def ocr_image(path: str) -> list[str]:
    """识别图片,返回按「先上后下、先左后右」排序的文本行列表。"""
    items = ocr_items(path)
    items.sort(key=lambda it: (round(it["cy"] / 12), it["cx"]))
    return [it["text"] for it in items]
