# -*- coding: utf-8 -*-
"""MailSendHelper - 邮件发送助手

应用入口文件
"""

import sys
import os

# 确保项目根目录在 sys.path 中
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QTranslator, QLibraryInfo

from config import APP_NAME, APP_VERSION, ICON_PATH
from styles import GLOBAL_QSS
from ui.main_window import MainWindow


def main():
    # 高DPI支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    # 全局字体：Microsoft YaHei 10号
    app.setFont(QFont('Microsoft YaHei', 10))

    # 安装 Qt 中文翻译（尝试加载，若不可用则靠事件过滤器兜底）
    translator = QTranslator()
    trans_path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    translator.load('qt_zh_CN', trans_path)
    app.installTranslator(translator)

    # 安装中文 UI 事件过滤器（翻译 QMessageBox 按钮文字、QLineEdit 右键菜单）
    from qt_utils import ChineseUiFilter
    _chinese_filter = ChineseUiFilter()
    app.installEventFilter(_chinese_filter)

    # 设置应用图标
    if os.path.isfile(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))

    # 全局样式
    app.setStyleSheet(GLOBAL_QSS)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
