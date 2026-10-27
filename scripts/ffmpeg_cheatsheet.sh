#!/bin/bash
# ffmpeg 模板速查：Ken Burns / 实拍裁剪 / 拼接 / 混音 / 验证
# 用法：把本文件当函数库 source 进自己的构建脚本，或照抄单条命令
set -e
cd "$(dirname "$0")"
mkdir -p clips

# ---------- 1) 实拍素材裁剪段（裁掉底部原字幕 + 统一参数） ----------
# CROP 四元组按素材实测调整：宽:高:x偏移:y偏移，宽/高 必须 = 16/9 保持不变形
CROP="crop=1454:818:233:107,scale=1280:720,format=yuv420p"
seg() { # $1=起点秒 $2=时长秒 $3=输出名
  ffmpeg -y -ss "$1" -i "素材.mp4" -t "$2" -vf "$CROP" -r 25 \
    -c:v libx264 -preset medium -crf 18 -an "clips/$3" -loglevel error
}

# ---------- 2) 图片 Ken Burns 缓推段（产品图/证书/照片） ----------
kb() { # $1=图片 $2=输出名 $3=时长秒 $4=pad色(black/white)
  ffmpeg -y -loop 1 -t "$3" -i "$1" -vf "\
scale=iw*min(1280/iw\,720/ih):ih*min(1280/iw\,720/ih),\
pad=1280:720:(ow-iw)/2:(oh-ih)/2:color=$4,\
scale=2560:1440,\
zoompan=z='min(1.0+0.05*on/($3*25),1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1280x720:fps=25,\
format=yuv420p" \
    -c:v libx264 -preset medium -crf 18 -an "clips/$2" -loglevel error
}
# 架构图/文字较多的图用更轻的推近(1.03)防止边缘被裁：把 0.05/1.05 改成 0.03/1.03

# ---------- 3) 拼接（片段参数必须一致：1280x720/25fps/h264/yuv420p/无音轨） ----------
# list.txt 每行: file 'clips/xxx.mp4'
ffmpeg -y -f concat -safe 0 -i list.txt -c copy full_video.mp4 -loglevel error

# ---------- 4) 混音：N 段配音按延迟铺 + BGM 循环 + 淡出 ----------
# 假设 3 段配音 a1/a2/a3，延迟 2500/20000/95900 ms；BGM 91.5s 循环 3 遍铺满 196s
ffmpeg -y -i full_video.mp4 \
  -i seg1.mp3 -i seg2.mp3 -i seg3.mp3 -i bgm.mp3 \
  -filter_complex "\
[1:a]aresample=48000,aformat=channel_layouts=stereo,adelay=2500:all=1[a1];\
[2:a]aresample=48000,aformat=channel_layouts=stereo,adelay=20000:all=1[a2];\
[3:a]aresample=48000,aformat=channel_layouts=stereo,adelay=95900:all=1[a3];\
[4:a]aresample=48000,aformat=channel_layouts=stereo,aloop=loop=2:size=4400000,\
volume=0.22,atrim=0:196.9,afade=t=in:d=2,afade=t=out:st=193.4:d=3.5[bgm];\
[a1][a2][a3][bgm]amix=inputs=4:normalize=0,alimiter=limit=0.95[mix]" \
  -map 0:v -map "[mix]" -c:v copy -c:a aac -b:a 192k -t 196.9 full_music.mp4 -loglevel error
# 音量参考：BGM volume=0.22(约-13dB) 不压旁白；旁白段 mean≈-25dB、纯BGM段≈-38dB 为佳

# ---------- 5) 烧字幕 ----------
ffmpeg -y -i full_music.mp4 -vf "ass=subs.ass" -c:v libx264 -preset medium -crf 18 \
  -c:a copy final.mp4 -loglevel error

# ---------- 6) 验证 ----------
# 电平检查（旁白段 / 纯BGM段 / 淡出段）
ffmpeg -ss 30 -t 10 -i final.mp4 -af volumedetect -f null - 2>&1 | grep -E "mean_volume|max_volume"
# 关键帧抽帧拼图（人工检查字幕对位/穿帮/残留）
ffmpeg -ss 128.5 -i final.mp4 -frames:v 1 check_128.jpg
# 只改画面不动音频时，直接复用旧音轨（免重混音）：
# ffmpeg -y -i new_video.mp4 -i old_music.mp4 -map 0:v -map 1:a -c copy full.mp4
