#!/usr/bin/env python3
"""Overlay gaya referensi di atas frame render: pill label atas + caption kata
di bawah + watermark. Lalu encode mp4 (upscale 1080x1920)."""
import os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FRAMES = os.path.join(HERE, 'frames')
COMP = os.path.join(HERE, 'comp')
os.makedirs(COMP, exist_ok=True)
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

PILL_TEXT = '1 ROUTER · 30 HP'
CAPTIONS = []  # PR #6: caption baris dimatikan — diganti caption kata karaoke + narasi di pasca-produksi
WATERMARK = 'BUKTI MESIN BLENDER · 01'
# Jadwal pill versi 60 detik (aktif hanya bila jumlah frame > 300)
PILL_SCHEDULE = [(1, 240, '1 ROUTER · 30 HP'), (241, 480, 'JAM 7 MALAM'),
                 (481, 720, '50 Mbps DIBAGI 30'), (721, 960, 'SEMUANYA JADI LEMOT'),
                 (961, 1200, 'SOLUSINYA ADA 3'), (1201, 1440, 'NGGAK KERJA SENDIRIAN')]
WATERMARK_60 = 'MESIN BLENDER · VERSI 60 DETIK'


def pill_for(f, n):
    if n > 300:
        for a, b, t in PILL_SCHEDULE:
            if a <= f <= b:
                return t
    return PILL_TEXT

def caption_for(f):
    for a, b, t in CAPTIONS:
        if a <= f <= b:
            return t
    return ''

files = sorted(f for f in os.listdir(FRAMES) if f.endswith('.png'))
print('frames:', len(files))
for i, fn in enumerate(files, start=1):
    im = Image.open(os.path.join(FRAMES, fn)).convert('RGB')
    W, H = im.size
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    # pill atas (muncul frame 20+, pop-in halus)
    if i >= 20:
        f_pill = ImageFont.truetype(BOLD, 34)
        ptxt = pill_for(i, len(files))
        tw = d.textlength(ptxt, font=f_pill)
        pw, ph = tw + 56, 62
        x0, y0 = (W - pw) / 2, 54
        d.rounded_rectangle([x0, y0, x0 + pw, y0 + ph], radius=31,
                            fill=(178, 224, 32, 255), outline=(10, 12, 16, 255), width=4)
        d.text((W / 2, y0 + ph / 2), ptxt, font=f_pill, fill=(10, 12, 16, 255), anchor='mm')
    # caption bawah
    cap = caption_for(i)
    if cap:
        f_cap = ImageFont.truetype(BOLD, 40)
        d.text((W / 2 + 2, H - 118 + 2), cap, font=f_cap, fill=(0, 0, 0, 160), anchor='mm')
        d.text((W / 2, H - 118), cap, font=f_cap, fill=(255, 255, 255, 255), anchor='mm')
    # watermark
    f_wm = ImageFont.truetype(BOLD, 19)
    d.text((W - 16, 18), WATERMARK_60 if len(files) > 300 else WATERMARK,
           font=f_wm, fill=(255, 255, 255, 170), anchor='ra')
    out = Image.alpha_composite(im.convert('RGBA'), ov).convert('RGB')
    out.save(os.path.join(COMP, fn))
    if i % 60 == 0:
        print('comp', i)

_yf = os.path.expanduser('~/workspace/your_files')
out_mp4 = (os.path.join(_yf, 'blender-proof-01.mp4') if os.path.isdir(_yf)
           else os.path.join(HERE, 'blender-proof-01.mp4'))
cmd = ['ffmpeg', '-y', '-v', 'error', '-framerate', '24', '-i', os.path.join(COMP, 'f%04d.png'),
       '-vf', 'scale=1080:1920:flags=lanczos,eq=contrast=1.04:saturation=1.07,unsharp=5:5:0.4',
       '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p',
       '-color_primaries', 'bt709', '-color_trc', 'bt709', '-colorspace', 'bt709',
       '-movflags', '+faststart', out_mp4]
subprocess.run(cmd, check=True)
print('DONE', out_mp4, os.path.getsize(out_mp4) // 1024, 'KB')
