"""社区站 meta 数据(tier / 胜率 / 出装优先级 / 对线胜负)。

以 lolalytics 数据接口为主。社区站属非官方接口、结构会变,是最易碎、最需校准的
一块。为便于在连不上外网的开发端校准,这里把 HTTP 抓取做成「诊断式」:不直接
对响应做 json.loads(那样非 JSON 会崩),而是先拿到 状态码/内容类型/原文,
抓不到 JSON 时返回诊断信息,方便把真实返回发回来定位。

纯函数(URL/参数构造、lane 映射、parse_meta)可离线测试。
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

# 我们的位置名 -> lolalytics 的 lane 名
LANES = {"top": "top", "jungle": "jungle", "mid": "middle",
         "adc": "bottom", "support": "support"}

DEFAULT_BASE = "https://ax.lolalytics.com/mega/"


def http_get(url: str, timeout: int = 25) -> dict:
    """抓取并返回 {status, content_type, body, url};失败也返回结构而非抛异常。"""
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://lolalytics.com/",
        "Origin": "https://lolalytics.com",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode("utf-8", errors="ignore")
            return {"status": getattr(r, "status", 200),
                    "content_type": r.headers.get("Content-Type"),
                    "body": body, "url": url}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore") if e.fp else ""
        return {"status": e.code, "content_type": e.headers.get("Content-Type") if e.headers else None,
                "body": body, "url": url, "error": f"HTTP {e.code}"}
    except Exception as e:  # noqa: BLE001  URLError/超时/DNS 等
        return {"status": None, "content_type": None, "body": "",
                "url": url, "error": str(e)[:160]}


def norm_patch(version: str) -> str:
    """'14.10.1' -> '14.10'(社区站按大版本)。"""
    parts = version.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else version


def meta_url(champ_key: str, lane: str, patch: str,
             tier: str = "all", region: str = "all", base: str = DEFAULT_BASE) -> str:
    lane_name = LANES.get(lane, lane)
    return (
        f"{base}?ep=champion&p=d&v=1"
        f"&patch={patch}&cid={champ_key}&lane={lane_name}"
        f"&tier={tier}&queue=420&region={region}"
    )


def parse_meta(raw: dict) -> dict:
    """从 lolalytics 返回里尽力抽取关键字段;抽不到则给校准提示。"""
    out: dict = {}
    header = raw.get("header") or {}
    if isinstance(header, dict):
        for field, src in (("winrate", "wr"), ("pickrate", "pr"),
                           ("banrate", "br"), ("games", "n")):
            if header.get(src) is not None:
                out[field] = header[src]
    for k in ("tier", "rank"):
        if raw.get(k) is not None:
            out[k] = raw[k]
    if not out:
        out["_note"] = ("未识别到字段,请把原始返回发我校准(顶层键: "
                        + ",".join(list(raw.keys())[:15]) + ")")
    return out


def fetch_meta(champ_key: str, lane: str, version: str, tier: str = "all",
               base: str = DEFAULT_BASE, http=http_get) -> dict:
    url = meta_url(champ_key, lane, norm_patch(version), tier=tier, base=base)
    resp = http(url)
    if resp.get("error") or not resp.get("body"):
        return {"url": url, "status": resp.get("status"),
                "error": resp.get("error") or "空响应",
                "body_preview": resp.get("body", "")[:300],
                "_note": "抓取失败/空,把这段发我校准接口"}
    try:
        raw = json.loads(resp["body"])
    except json.JSONDecodeError:
        return {"url": url, "status": resp.get("status"),
                "content_type": resp.get("content_type"),
                "body_preview": resp["body"][:300],
                "_note": "返回不是JSON,把这段发我校准接口"}
    result = parse_meta(raw)
    result["url"] = url
    return result


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(description="抓社区站 meta(lolalytics)")
    ap.add_argument("champ_key", help="英雄数字id(scout 输出里的 key)")
    ap.add_argument("lane", choices=list(LANES), help="位置")
    ap.add_argument("version", help="版本号,如 14.10")
    ap.add_argument("--tier", default="all")
    ap.add_argument("--base", default=DEFAULT_BASE, help="接口基址(校准时可换)")
    ap.add_argument("--raw", action="store_true",
                    help="诊断:打印 状态码/内容类型/原文前段")
    args = ap.parse_args(argv)

    if args.raw:
        url = meta_url(args.champ_key, args.lane, norm_patch(args.version),
                       tier=args.tier, base=args.base)
        resp = http_get(url)
        print("URL:", url)
        print("STATUS:", resp.get("status"), "| TYPE:", resp.get("content_type"),
              "| ERR:", resp.get("error"))
        print("BODY(前1500字):")
        print(resp.get("body", "")[:1500])
        return 0
    print(json.dumps(fetch_meta(args.champ_key, args.lane, args.version,
                                tier=args.tier, base=args.base),
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
