"""社区站 meta 数据(tier / 胜率 / 出装优先级 / 对线胜负)。

以 lolalytics 的数据接口为主(用英雄数字id查)。社区站属非官方接口、结构会变,
**这是最易碎、最需要校准的一块**:第一次在你电脑上跑后,把输出或报错发我,
我据实际返回结构修 parse_meta。

纯函数(URL/参数构造、lane 映射)可离线测试;实际抓取走可注入 getter。
"""
from __future__ import annotations

import json
import urllib.request

# 我们的位置名 -> lolalytics 的 lane 名
LANES = {"top": "top", "jungle": "jungle", "mid": "middle",
         "adc": "bottom", "support": "support"}


def _get_json(url: str, timeout: int = 25):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 lol-coach"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="ignore"))


def norm_patch(version: str) -> str:
    """'14.10.1' -> '14.10'(社区站按大版本)。"""
    parts = version.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else version


def meta_url(champ_key: str, lane: str, patch: str,
             tier: str = "all", region: str = "all") -> str:
    lane_name = LANES.get(lane, lane)
    return (
        "https://a1.lolalytics.com/mega/?ep=champion&p=d&v=1"
        f"&patch={patch}&cid={champ_key}&lane={lane_name}"
        f"&tier={tier}&queue=420&region={region}"
    )


def parse_meta(raw: dict) -> dict:
    """从 lolalytics 返回里尽力抽取关键字段。

    结构可能变;抽不到的字段留空,并在 _note 提示发原始数据来校准。
    """
    out: dict = {}
    header = raw.get("header") or {}
    if isinstance(header, dict):
        for field, src in (("winrate", "wr"), ("pickrate", "pr"),
                           ("banrate", "br"), ("games", "n")):
            if header.get(src) is not None:
                out[field] = header[src]
    # 出装/符文/对线:不同版本字段名不一,保留候选键供校准
    for k in ("tier", "rank"):
        if raw.get(k) is not None:
            out[k] = raw[k]
    if not out:
        out["_note"] = "未识别到字段,请把原始返回发我校准(键: " \
                       + ",".join(list(raw.keys())[:12]) + ")"
    return out


def fetch_meta(champ_key: str, lane: str, version: str,
               tier: str = "all", getter=_get_json) -> dict:
    patch = norm_patch(version)
    url = meta_url(champ_key, lane, patch, tier=tier)
    try:
        raw = getter(url)
    except Exception as e:                      # noqa: BLE001
        return {"url": url, "error": str(e)[:120]}
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
    ap.add_argument("--raw", action="store_true", help="打印原始返回(校准用)")
    args = ap.parse_args(argv)

    if args.raw:
        url = meta_url(args.champ_key, args.lane, norm_patch(args.version), tier=args.tier)
        print(json.dumps(_get_json(url), ensure_ascii=False, indent=2)[:8000])
        return 0
    print(json.dumps(fetch_meta(args.champ_key, args.lane, args.version, tier=args.tier),
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
