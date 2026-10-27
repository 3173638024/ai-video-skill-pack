# -*- coding: utf-8 -*-
"""TTS 配音 + 句级精确时间戳采集。

输入 segments.json:
{
  "seg1": {"text": "解说词……", "delay_ms": 2500},
  "seg2": {"text": "……", "delay_ms": 20000}
}
输出 out/<name>.mp3 + out/cues.json:
{ "seg1": {"delay_ms":2500, "dur":15.3, "cues":[{"start":0.1,"end":5.2,"text":"……"}, ...]} }

依赖: pip install edge-tts;  系统需有 ffprobe
代理: 自动读取环境变量 https_proxy（edge-tts 的 aiohttp 不会自动读）
"""
import asyncio, json, os, re, sys
import edge_tts

VOICE = "zh-CN-YunjianNeural"   # 男声；女声可用 zh-CN-XiaoxiaoNeural
RATE = "-6%"                    # 稍慢，汇报片更稳重

# SentenceBoundary 句合并策略：
#  - 短句贪心合并到 >=10 字或遇到句末标点
#  - 单句 >32 字按逗号贪心分组（每组 >=12 字），组间按时长比例切分时间轴
MIN_MERGE = 10
LONG_SPLIT = 32
GROUP_MIN = 12


async def collect(name, text, out_dir, proxy):
    mp3 = os.path.join(out_dir, f"{name}.mp3")
    tts = edge_tts.Communicate(text, VOICE, rate=RATE, proxy=proxy)
    sentences = []
    with open(mp3, "wb") as f:
        async for chunk in tts.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                sentences.append({"t0": chunk["offset"] / 1e7,
                                  "t1": (chunk["offset"] + chunk["duration"]) / 1e7,
                                  "text": chunk["text"]})
    cues, buf = [], []
    for w in sentences:
        buf.append(w)
        txt = "".join(x["text"] for x in buf)
        ended = w["text"].rstrip().endswith(("。", "！", "？", "；"))
        if len(txt.strip().rstrip("。！？；,，")) >= MIN_MERGE or ended:
            s = txt.strip().rstrip("。！？；")
            start, end = buf[0]["t0"], buf[-1]["t1"]
            if len(s) > LONG_SPLIT:
                parts = [p for p in re.split(r"[,，、]", s) if p]
                total = sum(len(p) for p in parts)
                groups, cur, cur_len = [], [], 0
                for p in parts:
                    cur.append(p); cur_len += len(p)
                    if cur_len >= GROUP_MIN:
                        groups.append(cur); cur, cur_len = [], 0
                if cur:
                    if groups and cur_len < 6:
                        groups[-1].extend(cur)
                    else:
                        groups.append(cur)
                t = start
                for g in groups:
                    glen = sum(len(p) for p in g)
                    d = (end - start) * glen / total
                    cues.append({"start": round(t, 3), "end": round(t + d, 3), "text": ",".join(g)})
                    t += d
            else:
                cues.append({"start": round(start, 3), "end": round(end, 3), "text": s})
            buf = []
    if buf:
        s = "".join(x["text"] for x in buf).strip().rstrip("。！？；,，")
        cues.append({"start": round(buf[0]["t0"], 3), "end": round(buf[-1]["t1"], 3), "text": s})
    proc = await asyncio.create_subprocess_exec(
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp3,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
    out, _ = await proc.communicate()
    return {"cues": cues, "dur": float(out.decode().strip())}


async def main():
    seg_file, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    proxy = os.environ.get("https_proxy") or os.environ.get("HTTPS_PROXY")
    segments = json.load(open(seg_file, encoding="utf-8"))
    result = {}
    for name, seg in segments.items():
        data = await collect(name, seg["text"], out_dir, proxy)
        result[name] = {"delay_ms": seg["delay_ms"], **data}
        print(f"{name}: dur={data['dur']:.2f}s cues={len(data['cues'])}")
    with open(os.path.join(out_dir, "cues.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)
    print("cues.json written")

if __name__ == "__main__":
    asyncio.run(main())
