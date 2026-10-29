# -*- coding: utf-8 -*-
"""生成勾选框对钩图标"""
from PIL import Image, ImageDraw
import os

def generate_checkmark():
    size = 16
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # White checkmark
    points = [(3, 8), (6, 11), (13, 4)]
    width = 3
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=(255, 255, 255, 255), width=width)
    for pt in points:
        r = 1
        draw.ellipse([pt[0]-r, pt[1]-r, pt[0]+r, pt[1]+r], fill=(255, 255, 255, 255))

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'checkmark.png')
    img.save(out)
    print(f'checkmark.png saved: {os.path.getsize(out)} bytes')

if __name__ == '__main__':
    generate_checkmark()
