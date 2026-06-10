"""OCR 层:把一张结算截图变成「按阅读顺序排好的文本行」。

这一层依赖 PaddleOCR(中文+数字识别效果好,本地离线运行)。
只在真正用到时才 import paddleocr,这样纯解析逻辑(parse.py)可以
在没装 paddle 的环境里照样测试。
"""
from __future__ import annotations

from functools import lru_cache

_LANG = "ch"  # 中英文混合


@lru_cache(maxsize=1)
def _get_engine():
    # 延迟导入:没装 paddleocr 时不影响 parse.py 的使用与测试
    from paddleocr import PaddleOCR

    return PaddleOCR(use_angle_cls=True, lang=_LANG, show_log=False)


def ocr_image(path: str) -> list[str]:
    """识别图片,返回按「先上后下、先左后右」排序的文本行列表。"""
    engine = _get_engine()
    result = engine.ocr(path, cls=True)
    if not result or not result[0]:
        return []

    items = []  # (y_center, x_left, text)
    for line in result[0]:
        box, (text, conf) = line
        ys = [p[1] for p in box]
        xs = [p[0] for p in box]
        items.append((sum(ys) / len(ys), min(xs), text))

    # 同一行的按 y 容差归并后再按 x 排;简单起见直接 (y, x) 排序
    items.sort(key=lambda t: (round(t[0] / 12), t[1]))
    return [text for _, _, text in items]
