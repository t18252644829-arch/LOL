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
| OCR | `lol_coach/ocr.py` | RapidOCR(本地、离线、免费;PaddleOCR 为备选) | 截图 → 文本行 |
| 解析 | `lol_coach/parse.py` | 纯 Python | 文本行 → 紧凑 JSON,有单元测试 |
| 入口 | `lol_coach/extract.py` | 串联上面两层 | 命令行 |

这样解析逻辑可以不装 OCR 引擎就跑测试。

## 安装

```bash
pip install -r requirements.txt   # 装 RapidOCR(自带中文模型,离线运行)
```

第一次运行会用到内置模型,无需联网下载大文件。

## 支持的页面

- **对位详情页**(掌盟「战绩详情页 / 战局」,左右两个玩家对比)—— 数据最丰富,
  自动识别。会抽出你 vs 对手的参团率、补刀、视野、伤害构成、经济差等,并算好差值。
  **掌盟里查自己战绩时你在左列,工具默认锁左列为「你」**(`--side` 可改)。
- **普通结算/数据页**(单人标签+数值)。

## 用法

```bash
# 截图 → JSON(自动判断对位页 / 普通页,并存到 data/matches/)
python -m lol_coach.extract 截图.png

# 强制对位模式 / 指定你在哪一侧
python -m lol_coach.extract 截图.png --mode versus --side left

# OCR 漏识别英雄时兜底
python -m lol_coach.extract 截图.png --champion 亚索
```

对位页输出示例(你=左,自带 `_opp` 对手值与 `_diff` 差值):

```json
{
  "result": "胜利", "kp": 22.2, "kp_opp": 50.0,
  "wards": "6/0", "wards_opp": "3/0",
  "cs": 117, "cs_opp": 139, "cs_diff": -22,
  "dmg_to_champ": 8326, "dmg_to_champ_opp": 9100,
  "gold": 6100, "gold_opp": 6700, "gold_diff": -600
}
```

## 按英雄文件夹批量(推荐日常这样用)

不想每次敲命令、也不想手动标英雄?**用文件夹名当英雄名**:

1. 建一个文件夹,名字就叫英雄名,如 `武器大师`
2. 把这个英雄的多张对位截图都丢进去
3. 把整个文件夹**拖到 `批量识别.bat`** 上

工具会识别每一局、自动打上英雄=文件夹名,并汇总这个英雄的胜率、平均补刀差、
平均参团率等趋势,存到 `data/matches/<英雄>_汇总.json`。把输出发我即可出诊断。

```bash
# 命令行等价写法
python -m lol_coach.batch "武器大师"
```

## 校准(重要)

OCR 字段映射依赖掌盟页面的实际排版。第一次用时,在你电脑上把识别到的
**带坐标文本块**导出发我,我按真实坐标把 `parse.py` 调准:

```python
from lol_coach.ocr import ocr_items
import json
json.dump(ocr_items("截图.png"), open("items.json", "w"), ensure_ascii=False, indent=2)
```

然后 `python -m lol_coach.extract --from-items items.json` 可离线复跑解析。

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
