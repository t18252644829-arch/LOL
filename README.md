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

## 按「英雄 + 日期段」文件夹归档(推荐日常这样用)

不想每次敲命令、也不想手动标英雄?**用文件夹名当英雄名 + 周期**:

1. 建文件夹,名字 = 英雄名 + 日期段,如 `武器大师6.10-6.20`
2. 把这个周期里该英雄的对位截图都丢进去
3. 把整个文件夹**拖到 `批量识别.bat`** 上

工具会:
- 自动拆出 英雄=武器大师、周期=6.10-6.20
- 识别每一局并打上英雄标签
- 汇总该周期的胜率/平均补刀差/参团率等,存到 `data/matches/武器大师_6.10-6.20_汇总.json`
- **缓存**:识别过的图(路径+大小不变)不再重复 OCR,重跑很快、不重复分析

下个周期就新建 `武器大师6.20-6.30`,以此类推,各周期互不覆盖。

```bash
python -m lol_coach.batch "武器大师6.10-6.20"
```

## 长期成长趋势

攒了多个周期后,**双击 `长期分析.bat`**(或 `python -m lol_coach.trend`):
把同一英雄各周期串起来,按时间排序,显示补刀差/参团率/经济差是 **↑变好** 还是
**↓变差**,以及总胜率。把输出发我即可得到长期成长诊断。

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

## 阶段二:根据弱点推荐学习视频

把阶段一某个周期的弱点,自动变成搜索词,去 **B站 + YouTube** 抓高质量视频、
按播放量排序、按弱点分组推荐。

**用法:把某个 `_汇总.json` 拖到 `推荐学习.bat`**(或命令行):

```bash
python -m lol_coach.learn.recommend data/matches/武器大师_6.10-6.20_汇总.json
# --source bili,youtube   选择视频源
# --per 4                 每个弱点推荐几个
```

输出按「弱点 → 搜索词 → 推荐视频(标题/UP/播放量/链接)」分组。把清单发我做取舍。

**想总结某个视频**(YouTube 多有自动字幕,B站看有没有 CC):

```bash
python -m lol_coach.learn.subtitles "视频URL"
```

抓到的字幕文本贴给对话,我把它提炼成「针对你弱点的要点」。没字幕的视频会提示抓不到。

> 依赖 `yt-dlp`(已在 requirements 里)。需要能访问 B站/YouTube。

## 阶段二(进阶):版本情报 + 个性化分析简报

分工:**工具采集客观情报,AI 做分析。**

- `learn/scout.py`:抓 Riot 官方 Data Dragon —— 英雄当前版本的技能/CD/消耗/被动/
  基础数值/定位标签(中文)。国服版本慢,用 `--version` 锁国服客户端显示的版本号。
- `learn/brief.py`:把「你的数据 + 当前版本事实 + 段位」打包成一份简报。

**用法:把 `_汇总.json` 拖到 `分析简报.bat`**(会问你段位和版本号),或命令行:

```bash
python -m lol_coach.learn.scout 武器大师 --version 14.10
python -m lol_coach.learn.brief data/matches/武器大师_6.10-6.20_汇总.json --rank 黄金 --version 14.10
```

把生成的简报整段发给对话,我据此产出:**生态位、装备天赋优先级、打法思路、
对线要点、结合你段位与短板的实操成长路径**。
```
