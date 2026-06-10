"""OCR 层:把一张结算/对位截图变成文本。

默认用 RapidOCR(onnxruntime,pip 一句话装好、自带模型、离线、中文好),
装不上时自动回退到 PaddleOCR。只在真正用到时才 import,这样纯解析逻辑
(parse.py)可以在没装任何 OCR 引擎的环境里照样测试。

提供两种输出:
  ocr_image(path) -> list[str]            按阅读顺序的文本行(简单页面)
  ocr_items(path) -> list[dict]           带坐标的文本块(对位对比页需要)
"""
from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def _rapid():
    from rapidocr_onnxruntime import RapidOCR

    return RapidOCR()


@lru_cache(maxsize=1)
def _paddle():
    from paddleocr import PaddleOCR

    return PaddleOCR(use_angle_cls=True, lang="ch", show_log=False)


def _raw(path: str) -> list[tuple]:
    """统一两种后端的输出为 [(box, text), ...],box 是 4 个 [x, y] 顶点。"""
    try:
        import rapidocr_onnxruntime  # noqa: F401

        result, _ = _rapid()(path)
        return [(box, text) for box, text, score in (result or [])]
    except ImportError:
        pass

    result = _paddle().ocr(path, cls=True)
    rows = result[0] if result and result[0] else []
    return [(box, text) for box, (text, conf) in rows]


def ocr_items(path: str) -> list[dict]:
    """识别图片,返回每个文本块的 {text, cx, cy}(中心坐标)。

    对位对比页需要 x 坐标来区分「左列=你 / 右列=对手」。
    """
    items = []
    for box, text in _raw(path):
        xs = [p[0] for p in box]
        ys = [p[1] for p in box]
        items.append(
            {"text": text, "cx": sum(xs) / len(xs), "cy": sum(ys) / len(ys)}
        )
    return items


def ocr_image(path: str) -> list[str]:
    """识别图片,返回按「先上后下、先左后右」排序的文本行列表。"""
    items = ocr_items(path)
    items.sort(key=lambda it: (round(it["cy"] / 12), it["cx"]))
    return [it["text"] for it in items]
