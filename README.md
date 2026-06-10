# LOL 国服教练工具(阶段一:截图诊断)

国服由腾讯运营,**没有 Riot 官方 API,也不被 op.gg 等战绩站收录**。
所以这个工具走「截图 OCR」路线:打完一局截结算图,本地工具把图里的关键
数据识别成一份**紧凑 JSON**,只有这份 JSON 进对话给 AI 教练分析 —— 截图本身
不进对话,省 80%+ token,数字也更准。

```
打完一局 → 截结算图 → python -m lol_coach.extract shot.png
        → 紧凑 match_*.json → 贴进对话 → 教练诊断
```

## 设计:两层解耦

| 层 | 文件 | 依赖 | 说明 |
|----|------|------|------|
| OCR | `lol_coach/ocr.py` | PaddleOCR(本地、离线、免费) | 截图 → 文本行 |
| 解析 | `lol_coach/parse.py` | 纯 Python | 文本行 → 紧凑 JSON,有单元测试 |
| 入口 | `lol_coach/extract.py` | 串联上面两层 | 命令行 |

这样解析逻辑可以不装 OCR 引擎就跑测试。

## 安装

```bash
pip install -r requirements.txt   # 仅 OCR 层需要
```

## 用法

```bash
# 截图 → JSON(并自动存到 data/matches/)
python -m lol_coach.extract 结算截图.png

# OCR 漏识别时手动兜底
python -m lol_coach.extract 结算截图.png --champion 亚索 --result 胜利

# 无 paddle 环境 / 调试:直接喂 OCR 文本(每行一条)
python -m lol_coach.extract --from-text ocr_lines.txt --no-save
```

输出示例:

```json
{
  "result": "胜利", "champion": "亚索", "duration": "32:15", "duration_min": 32.25,
  "kda": [8, 5, 7], "kda_ratio": 3.0, "cs": 245, "cs_per_min": 7.6,
  "gold": 14200, "damage_dealt": 28500, "vision_score": 18, "wards_placed": 9
}
```

## 测试

```bash
python tests/test_parse.py
```

## 已知限制(诚实说明)

- 结算面板只有**整局汇总**,没有时间线/补刀曲线/死亡热力图 —— 那些需要官方
  API,国服拿不到。所以诊断维度比 Riot 区服浅。
- OCR 字段映射(补刀/伤害/视野等)依赖国服结算「数据详情页」的标签排版。
  **拿一张你真实的结算截图来,我再按实际排版校准 `parse.py` 的关键词和裁剪。**
- 英雄名清单在 `lol_coach/data/champions_zh.json`,可自行增删。

## 后续(阶段二)

根据多局 JSON 累积出弱点趋势(如「视野长期偏低」),再去 B站/YouTube
抓对应主题攻略做推荐。先把阶段一用顺。
```
