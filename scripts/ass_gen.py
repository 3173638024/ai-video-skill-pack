# -*- coding: utf-8 -*-
"""cues.json -> ASS 字幕（金黄字+深描边样式，>20字自动断行，支持产品名条第二层）。

用法:
  python ass_gen.py cues.json subs.ass [--labels labels.json]
labels.json: [[start, end, "量子密钥分发终端（QKD）"], ...]   # 可选
覆盖某段延迟（改时间轴不动 cue）: 在 cues.json 里直接改 delay_ms 即可。
"""
import json, sys


def ass_time(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def wrap(text, limit=20):
    if len(text) <= limit:
        return text
    mid = len(text) / 2
    best, bestd = None, 1e9
    for i, ch in enumerate(text):
        if ch in ",，、——：":
            d = abs(i - mid)
            if d < bestd:
                best, bestd = i, d
    if best is None or best < 4 or best > len(text) - 4:
        best = len(text) // 2
        return text[:best] + r"\N" + text[best:]
    return text[:best + 1] + r"\N" + text[best + 1:]


STYLE = """[Script Info]
ScriptType: v4.00+
PlayResX: 1280
PlayResY: 720
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Narr,Microsoft YaHei,38,&H00CAF6FE,&H00FFFFFF,&H0018242D,&H00000000,1,0,0,0,100,100,0,0,1,2.5,1,2,40,40,26,1
Style: Label,Microsoft YaHei,34,&H00FFFFFF,&H00FFFFFF,&H00A05A1E,&H00000000,1,0,0,0,100,100,0,0,3,6,0,2,40,40,96,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
# Narr  = 金黄字 RGB(254,246,202) + 深棕描边 RGB(45,36,24)（ASS 颜色为 &H00BBGGRR）
# Label = 白字 + 金色底框（BorderStyle=3），MarginV=96 抬高到中下部


def main():
    cues_file, out_file = sys.argv[1], sys.argv[2]
    labels = []
    if "--labels" in sys.argv:
        labels = json.load(open(sys.argv[sys.argv.index("--labels") + 1], encoding="utf-8"))
    data = json.load(open(cues_file, encoding="utf-8"))
    lines = []
    for seg, s in data.items():
        delay = s["delay_ms"] / 1000.0
        for c in s["cues"]:
            text = c["text"].replace(" ", "")
            lines.append((delay + c["start"], delay + c["end"], wrap(text)))
    lines.sort()
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(STYLE)
        for t0, t1, text in lines:
            f.write(f"Dialogue: 0,{ass_time(t0)},{ass_time(t1)},Narr,,0,0,0,,{text}\n")
        for t0, t1, text in labels:
            f.write(f"Dialogue: 1,{ass_time(t0)},{ass_time(t1)},Label,,0,0,0,,{text}\n")
    print(f"{out_file} written, {len(lines)} narr cues, {len(labels)} labels")


if __name__ == "__main__":
    main()
