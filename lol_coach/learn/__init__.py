"""第二阶段:学习推荐。

根据阶段一诊断出的弱点,自动生成搜索词,去 B站 / YouTube 抓高质量视频
并排序推荐;有字幕的视频可抓字幕供 AI 总结。

  weakness.py   汇总/趋势 -> 弱点 -> 搜索计划(纯逻辑,可测试)
  search.py     yt-dlp 封装:bilisearch / ytsearch -> 统一结果
  subtitles.py  yt-dlp 抓字幕 -> 纯文本(YouTube 自动字幕为主)
  recommend.py  串联:弱点 -> 搜索 -> 排序 -> 推荐(命令行)
"""
