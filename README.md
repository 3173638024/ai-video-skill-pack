# ai-video-skill-pack · 企业介绍视频制作技能包

一句话需求 → 3 分钟成片：客户素材混剪、网络素材补充、TTS 配音、**句级精确对时字幕**、背景音乐，交付验收级企业介绍视频。

> 来源于真实项目：一句话生成初版，之后 6 轮人工迭代（双字幕、画面深裁、字幕样式推翻重做、品牌穿帮、节奏压缩），每一条踩坑都沉淀在本技能包里。

## 目录结构

```
├── SKILL.md                  # 六步工作流 + 时间轴设计原则（从这里开始）
├── PITFALLS.md               # 19 条踩坑实录（每条都真金白银翻过车）
├── requirements.txt
└── scripts/
    ├── tts_cues.py           # TTS 配音 + SentenceBoundary 句级精确时间戳
    ├── ass_gen.py            # cues.json → 金黄字描边 ASS 字幕（支持双层级）
    ├── check_bottom.py       # 素材内嵌字幕检测（底部条带拼图）
    └── ffmpeg_cheatsheet.sh  # Ken Burns / 裁剪 / 拼接 / 混音 / 验证模板
```

## 快速开始

```bash
# 依赖
ffmpeg >= 7（含 libass，建议 9.x）
pip install -r requirements.txt

# 1. 写解说词 segments.json（每段一个章节 + 全局起始延迟），跑配音
python scripts/tts_cues.py segments.json out/

# 2. 检查素材自带字幕 → 决定裁剪参数
python scripts/check_bottom.py clips/*.mp4

# 3. 照 SKILL.md 六步工作流组装：片段 → 拼接 → 混音 → 烧字幕 → 验证
```

## 核心设计

- **字幕时间不估算**：edge-tts 的 `SentenceBoundary` 事件提供句级精确时间戳（单位 100ns），字幕、画面切换全部以此为准；改时间轴只改每段 `delay_ms`，cue 一行不动。
- **先检测再裁剪**：宣传素材底部几乎都有自带字幕，且不同镜头高度不同——先跑条带检测，再等比 crop。
- **时间轴向后传递**：中段提前一句解说会把后一个空档拉大，提前量必须向后传递。

## License

MIT — 欢迎改造到你自己的工作流。
