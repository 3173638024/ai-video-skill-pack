# -*- coding: utf-8 -*-
"""检测片段底部是否残留素材自带内嵌字幕。

用法: python check_bottom.py <clip.mp4> [more.mp4 ...]
对每个片段抽 3 帧，输出 y=590-720 的底部条带拼图 bottom_strips.jpg，
人工确认字幕带位置后再决定 crop 参数。
"""
import os, subprocess, sys
from PIL import Image

TMP = ".check_bottom_tmp"


def main():
    os.makedirs(TMP, exist_ok=True)
    strips = []
    for clip in sys.argv[1:]:
        name = os.path.splitext(os.path.basename(clip))[0]
        for t in (0.5, 2.5, 4.5):
            frame = os.path.join(TMP, f"{name}_{t}.png")
            subprocess.run(["ffmpeg", "-y", "-ss", str(t), "-i", clip, "-frames:v", "1",
                            frame, "-loglevel", "error"], check=True)
            im = Image.open(frame).convert("RGB")
            w, h = im.size
            strips.append((f"{name}@{t}s", im.crop((0, int(h * 0.82), w, h)).resize((640, 65))))
    sheet = Image.new("RGB", (660, (65 + 16) * len(strips) + 5), "white")
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    for i, (label, s) in enumerate(strips):
        y = i * (65 + 16)
        d.text((4, y + 2), label, fill="black")
        sheet.paste(s, (5, y + 15))
    sheet.save("bottom_strips.jpg", quality=88)
    print("bottom_strips.jpg written — 检查每条底部是否有残留字幕")


if __name__ == "__main__":
    main()
