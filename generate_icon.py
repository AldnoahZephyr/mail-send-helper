# -*- coding: utf-8 -*-
"""生成软件图标 - 信封主题，无版权风险

运行此脚本会在 assets/ 目录下生成 icon.png 和 icon.ico
"""

import os
import sys

# 确保能导入 config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import (
    QPainter, QPixmap, QColor, QPen, QBrush, QPainterPath,
    QLinearGradient
)
from PyQt5.QtCore import Qt, QRectF, QPoint


def _draw_icon(pixmap, size):
    """在给定的 QPixmap 上绘制信封图标"""
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.SmoothPixmapTransform)

    # 背景圆角矩形 - 渐变蓝色
    margin = size * 0.1
    bg_rect = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)
    radius = size * 0.12

    gradient = QLinearGradient(bg_rect.topLeft(), bg_rect.bottomRight())
    gradient.setColorAt(0, QColor('#1a73e8'))
    gradient.setColorAt(1, QColor('#0d47a1'))
    painter.setBrush(QBrush(gradient))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(bg_rect, radius, radius)

    # 绘制信封
    env_margin = size * 0.2
    env_rect = QRectF(env_margin, env_margin * 1.5, size - 2 * env_margin,
                      (size - 2 * env_margin) * 0.65)

    # 信封背景（白色）
    painter.setBrush(QColor('#ffffff'))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(env_rect, size * 0.02, size * 0.02)

    # 信封顶部三角形（信封盖）
    path = QPainterPath()
    path.moveTo(env_rect.topLeft())
    path.lineTo(QPoint(
        int(env_rect.center().x()),
        int(env_rect.top() + env_rect.height() * 0.45)
    ))
    path.lineTo(env_rect.topRight())
    path.lineTo(env_rect.topRight().x(), env_rect.top())
    path.closeSubpath()

    # 信封盖颜色
    painter.setBrush(QColor('#e8f0fe'))
    painter.drawPath(path)

    # 信封盖的边线
    pen = QPen(QColor('#1a73e8'), max(1, size * 0.012))
    painter.setPen(pen)
    painter.drawLine(
        env_rect.topLeft(),
        QPoint(int(env_rect.center().x()),
               int(env_rect.top() + env_rect.height() * 0.45))
    )
    painter.drawLine(
        env_rect.topRight(),
        QPoint(int(env_rect.center().x()),
               int(env_rect.top() + env_rect.height() * 0.45))
    )

    # 底部 V 形线
    painter.drawLine(
        env_rect.bottomLeft(),
        QPoint(int(env_rect.center().x()),
               int(env_rect.top() + env_rect.height() * 0.45))
    )
    painter.drawLine(
        env_rect.bottomRight(),
        QPoint(int(env_rect.center().x()),
               int(env_rect.top() + env_rect.height() * 0.45))
    )

    # 信封边框
    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(QColor('#1a73e8'), max(1, size * 0.01)))
    painter.drawRoundedRect(env_rect, size * 0.02, size * 0.02)

    painter.end()


def generate_icons(assets_dir):
    """生成 PNG 和 ICO 图标文件"""
    os.makedirs(assets_dir, exist_ok=True)

    # 生成 256x256 PNG
    pixmap = QPixmap(256, 256)
    _draw_icon(pixmap, 256)
    png_path = os.path.join(assets_dir, 'icon.png')
    pixmap.save(png_path, 'PNG')
    print(f'PNG 已生成: {png_path}')

    # 生成 ICO
    ico_path = os.path.join(assets_dir, 'icon.ico')
    pixmap.save(ico_path, 'ICO')
    if os.path.isfile(ico_path) and os.path.getsize(ico_path) > 0:
        print(f'ICO 已生成: {ico_path}')
    else:
        print('ICO 格式不受支持，仅生成 PNG')


if __name__ == '__main__':
    from config import BASE_DIR

    app = QApplication(sys.argv)
    assets_dir = os.path.join(BASE_DIR, 'assets')
    generate_icons(assets_dir)
    app.quit()
