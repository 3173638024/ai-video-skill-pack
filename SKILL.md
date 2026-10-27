# 企业介绍视频制作技能（SKILL）

一句话需求 → 3 分钟成片：模仿参考视频风格，融合客户素材 + 网络素材 + PPT 图，自动配音、精确对时字幕、背景音乐，交付验收级企业介绍视频。

## 适用场景

- 公司/产品介绍视频、验收会演示、项目汇报片
- 输入：参考视频（可选）、客户素材（视频/图片/PPT）、公司背景资料
- 输出：1280x720 / 25fps / H.264 成片 + 可独立修改的字幕、配音、混音工程

## 环境依赖

```
ffmpeg >= 7（含 libass；建议 9.x，注意参数变更见 PITFALLS.md）
pip install edge-tts pillow
可选：Python venv 隔离安装
```

## 六步工作流

### 第 1 步：解说词分段 + TTS 配音（带句级精确时间戳）

写 `segments.json`（每段 = 一个画面章节 + 全局起始延迟）：

```json
{
  "seg1": {"text": "当信息成为这个时代最重要的资产……", "delay_ms": 2500},
  "seg2": {"text": "光，是当前传输信息最理想的载体……", "delay_ms": 20000}
}
```

```bash
python scripts/tts_cues.py segments.json out/
# 产出 out/<seg>.mp3 + out/cues.json（含每句 start/end 秒，来自服务端 SentenceBoundary 事件）
```

**关键**：不要按字数估算字幕时间！edge-tts 的 `SentenceBoundary` 事件提供句级精确时间戳（单位 100ns），字幕/画面切换全部以此为准。

### 第 2 步：素材镜头定位（逐秒抽帧 + 条带拼图）

宣传素材里镜头切换远比想象的密。**必须逐秒抽帧拼图确认每个镜头的边界和内容**：

```bash
ffmpeg -ss <start> -i 素材.mp4 -t 12 -vf "fps=1,scale=300:-1,tile=5x3" -frames:v 1 probe.jpg
```

### 第 3 步：检查并裁掉素材自带的内嵌字幕

**几乎所有的宣传素材底部都有原字幕，且不同镜头字幕高度不同！** 先跑检测：

```bash
python scripts/check_bottom.py clips/   # 输出底部条带拼图，人工确认字幕带位置
```

再对有字幕的片段用等比 crop 裁掉（保持 16:9 需同时收窄宽度）：

```
crop=1454:818:233:107   # 示例：保留源 y 107-925，左右各裁 12%
```

**同时检查画面里的第三方品牌/机构名是否与解说词冲突**（例：解说"与 A 大学合作"，画面却是 B 大学横幅 = 穿帮）。

### 第 4 步：生成画面片段（Ken Burns 缓推 + 实拍裁剪）

```bash
bash scripts/ffmpeg_cheatsheet.sh   # 内含 seg/prod/cert 三个函数模板
```

- 产品图/照片：contain 缩放 + 黑底 pad + zoompan 1.03~1.05 缓推
- 实拍片段：`-ss <t> -i 素材 -t <dur>` + crop + 统一 1280x720/25fps/h264/yuv420p/无音轨
- 所有片段编码参数必须一致，否则 concat demuxer 会花屏

### 第 5 步：字幕生成（ASS，样式可定制）

```bash
python scripts/ass_gen.py cues.json subs.ass --labels labels.json
```

- 内置"金黄字 + 深描边"样式（BorderStyle=1, Outline=2.5），无底色框不挡画面
- >20 字自动在标点处断行；产品名条（Label 样式）可叠加第二层
- 字幕时间 = 段延迟 + cue 相对时间，改时间轴只需改 delay，cue 不动

### 第 6 步：拼接 + 混音 + 烧字幕 + 验证

```bash
# 拼接（各片段参数一致时 -c copy 秒完成）
ffmpeg -f concat -safe 0 -i list.txt -c copy full.mp4

# 混音：N 段配音按延迟铺 + BGM 循环低音量 + 淡出（模板见 cheatsheet）
# 烧字幕
ffmpeg -i full.mp4 -vf "ass=subs.ass" -c:v libx264 -crf 18 -c:a copy final.mp4
```

**交付前验证**：按关键点抽帧拼图检查（字幕对位、无穿帮、无残留原字幕）+ `volumedetect` 查各段电平（旁白 mean ≈ -25dB，纯 BGM ≈ -38dB）。

## 时间轴设计原则

- 任意两句解说间隔 ≤ 2 秒（用户对"中途停顿"极其敏感）
- **中段提前某句解说，会把它的后一个空档拉大**——提前量必须向后传递，用压缩前段槽位时长来吸收
- 重大信息（获奖、证书）前可留 1.5~2 秒戏剧性停顿
- 结尾保留 6~8 秒 LOGO/口号 + BGM 淡出，不算"停顿"

## 迭代心态

第一版一定不完美。真实项目迭代了 6 版：双字幕遮挡 → 画面深裁 → 字幕样式推翻重做 → 品牌穿帮 → 静态图换动画 → 节奏压缩。每轮改动用"等长替换"优先，避免牵一发动全身。
