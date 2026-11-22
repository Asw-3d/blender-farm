#!/usr/bin/env python3
"""Tekstur papan warung + ikon gelembung no-signal (digambar PIL, tajam kayak overlay grafis)."""
from PIL import Image, ImageDraw, ImageFont
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BOLD = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

# --- papan warung: kuning, teks merah + hitam ---
img = Image.new('RGB', (1024, 384), (255, 205, 40))
d = ImageDraw.Draw(img)
d.rectangle([14, 14, 1010, 370], outline=(30, 30, 30), width=10)
d.text((512, 118), 'WARUNG KOPI', font=ImageFont.truetype(BOLD, 128),
       fill=(216, 44, 32), anchor='mm')
d.text((512, 268), 'PAK RT', font=ImageFont.truetype(BOLD, 104),
       fill=(24, 24, 28), anchor='mm')
img.save(os.path.join(HERE, 'sign_warung.png'))  # orientasi diatur lewat UV di scene.py

# --- ikon no-signal: cakram putih, busur wifi abu, coret merah ---
S = 512
img = Image.new('RGBA', (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.ellipse([26, 26, S - 26, S - 26], fill=(255, 255, 255, 255), outline=(16, 18, 24, 255), width=14)
cx, cy = S / 2, S / 2 + 60
for r in (150, 105, 60):
    d.arc([cx - r, cy - r, cx + r, cy + r], start=215, end=325, fill=(90, 96, 108, 255), width=26)
d.ellipse([cx - 17, cy - 17, cx + 17, cy + 17], fill=(90, 96, 108, 255))
d.line([120, 392, 392, 120], fill=(226, 42, 42, 255), width=34)
img.save(os.path.join(HERE, 'icon_nosignal.png'))
print('textures ok')
