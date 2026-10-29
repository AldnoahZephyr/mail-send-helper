# -*- coding: utf-8 -*-
"""全局 QSS 样式表 - 统一管理应用视觉风格"""

import os
import sys

# 资源目录（打包后图标等资源在 _MEIPASS 临时目录）
if getattr(sys, 'frozen', False):
    RESOURCE_DIR = sys._MEIPASS
else:
    RESOURCE_DIR = os.path.dirname(os.path.abspath(__file__))

# 对钩图片绝对路径（用于 QSS url()）
_CHECKMARK_URL = os.path.join(RESOURCE_DIR, 'assets', 'checkmark.png').replace('\\', '/')

GLOBAL_QSS = """
/* ==================== 基础控件 ==================== */
QWidget {
    font-family: 'Microsoft YaHei', '微软雅黑', sans-serif;
    font-size: 10pt;
    color: #333333;
}

QMainWindow {
    background-color: #f0f2f5;
}

/* ==================== 顶部导航栏 ==================== */
#top_bar {
    background-color: #ffffff;
    border-bottom: 1px solid #e8eaed;
}

#menu_btn {
    background-color: transparent;
    border: none;
    padding: 10px 28px;
    font-size: 11pt;
    font-weight: bold;
    color: #1a73e8;
}
#menu_btn::menu-indicator {
    image: none;
}
#menu_btn:hover {
    background-color: #f0f4ff;
}

#about_btn {
    background-color: transparent;
    border: none;
    padding: 10px 18px;
    font-size: 10pt;
    color: #5f6368;
}
#about_btn:hover {
    background-color: #f0f4ff;
    color: #1a73e8;
}

#settings_btn {
    background-color: transparent;
    border: none;
    padding: 10px 18px;
    font-size: 10pt;
    color: #5f6368;
}
#settings_btn:hover {
    background-color: #f0f4ff;
    color: #1a73e8;
}

/* ==================== 菜单下拉 ==================== */
QMenu {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    padding: 6px;
}
QMenu::item {
    padding: 8px 36px 8px 20px;
    font-size: 10pt;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #e8f0fe;
    color: #1a73e8;
}
QMenu::separator {
    height: 1px;
    background: #e8eaed;
    margin: 4px 8px;
}

/* ==================== Tab 控件 ==================== */
QTabWidget::pane {
    border: none;
    background-color: #ffffff;
}

QTabBar::tab {
    background-color: #eef1f6;
    padding: 8px 24px;
    margin-right: 2px;
    border: 1px solid #ddd;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    font-size: 10pt;
    color: #666;
}
QTabBar::tab:selected {
    background-color: #ffffff;
    color: #1a73e8;
    border-color: #1a73e8;
    border-bottom: 2px solid #1a73e8;
}
QTabBar::tab:hover:!selected {
    background-color: #e0e7f1;
}

/* ==================== 分组框 ==================== */
QGroupBox {
    font-size: 10pt;
    font-weight: bold;
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 14px;
    background-color: #ffffff;
}
QGroupBox::title {
    left: 14px;
    padding: 0 6px;
    color: #1a73e8;
}

/* ==================== 表格 ==================== */
QTableWidget {
    gridline-color: #eaecef;
    alternate-background-color: #f7f9fc;
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    border-radius: 6px;
    font-size: 10pt;
    selection-background-color: #d0e0ff;
    selection-color: #333333;
}
QTableWidget::item {
    padding: 6px 4px;
}
QTableWidget::item:disabled {
    color: #999;
}

QHeaderView::section {
    background-color: #1a73e8;
    color: #ffffff;
    border: none;
    padding: 8px 6px;
    font-weight: bold;
    font-size: 10pt;
}
QHeaderView::section:first {
    border-top-left-radius: 6px;
}
QHeaderView::section:last {
    border-top-right-radius: 6px;
}

/* ==================== 按钮 ==================== */
QPushButton {
    padding: 6px 18px;
    border: 1px solid #d0d4dc;
    border-radius: 5px;
    background-color: #ffffff;
    font-size: 10pt;
    color: #333;
    min-height: 24px;
}
QPushButton:hover {
    background-color: #e8f0fe;
    border-color: #1a73e8;
    color: #1a73e8;
}
QPushButton:pressed {
    background-color: #d2e3fc;
}
QPushButton:disabled {
    color: #bbb;
    border-color: #e0e0e0;
    background-color: #f5f5f5;
}

/* 主按钮 */
QPushButton#primary_btn {
    background-color: #1a73e8;
    color: #ffffff;
    border: none;
    font-weight: bold;
}
QPushButton#primary_btn:hover {
    background-color: #1557b0;
}
QPushButton#primary_btn:pressed {
    background-color: #1446a0;
}

/* ==================== 输入控件 ==================== */
QLineEdit {
    padding: 6px 10px;
    border: 1px solid #d0d4dc;
    border-radius: 5px;
    background-color: #ffffff;
    font-size: 10pt;
    min-height: 20px;
    selection-background-color: #1a73e8;
    selection-color: #ffffff;
}
QLineEdit:focus {
    border: 2px solid #1a73e8;
    padding: 5px 9px;
}

QComboBox {
    padding: 5px 10px 5px 8px;
    border: 1px solid #d0d4dc;
    border-radius: 5px;
    background-color: #ffffff;
    font-size: 10pt;
    min-height: 24px;
}
QComboBox:focus {
    border: 2px solid #1a73e8;
    padding: 4px 9px 4px 7px;
}
QComboBox::drop-down {
    border: none;
    width: 22px;
}
QComboBox QAbstractItemView {
    border: 1px solid #d0d4dc;
    border-radius: 4px;
    background-color: #ffffff;
    selection-background-color: #e8f0fe;
    selection-color: #1a73e8;
    outline: none;
    padding: 4px;
}

QDateEdit, QDateTimeEdit {
    padding: 5px 8px;
    border: 1px solid #d0d4dc;
    border-radius: 5px;
    background-color: #ffffff;
    font-size: 10pt;
    min-height: 24px;
}
QDateEdit:focus, QDateTimeEdit:focus {
    border: 2px solid #1a73e8;
    padding: 4px 7px;
}

QSpinBox {
    padding: 5px 8px;
    border: 1px solid #d0d4dc;
    border-radius: 5px;
    background-color: #ffffff;
    font-size: 10pt;
}

/* ==================== 复选框 ==================== */
QCheckBox {
    font-size: 10pt;
    spacing: 6px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #c0c4cc;
    border-radius: 3px;
    background-color: #ffffff;
}
QCheckBox::indicator:checked {
    background-color: #1a73e8;
    border-color: #1a73e8;
    image: url(__CHECKMARK_URL__);
}
QCheckBox::indicator:hover {
    border-color: #1a73e8;
}
QCheckBox::indicator:disabled {
    background-color: #f5f5f5;
    border-color: #e0e0e0;
}

/* ==================== 列表 ==================== */
QListWidget {
    border: 1px solid #e0e0e0;
    border-radius: 5px;
    background-color: #ffffff;
    font-size: 10pt;
    padding: 3px;
}
QListWidget::item {
    padding: 4px 6px;
    border-radius: 3px;
}
QListWidget::item:selected {
    background-color: #e8f0fe;
    color: #1a73e8;
}
QListWidget::item:disabled {
    color: #999;
    background-color: #f5f5f5;
}

/* ==================== 文本编辑 ==================== */
QTextEdit {
    border: 1px solid #e0e0e0;
    border-radius: 5px;
    background-color: #ffffff;
    font-size: 10pt;
    padding: 4px;
}
QTextEdit:focus {
    border: 1px solid #1a73e8;
}

/* ==================== 工具栏 ==================== */
QToolBar {
    background-color: #f5f7fa;
    border: 1px solid #e0e0e0;
    border-radius: 5px;
    padding: 3px;
    spacing: 4px;
}
QToolBar QToolButton {
    padding: 4px 10px;
    border: 1px solid transparent;
    border-radius: 4px;
    font-size: 10pt;
}
QToolBar QToolButton:hover {
    background-color: #e8f0fe;
    border: 1px solid #d0d4dc;
}

/* ==================== 进度条 ==================== */
QProgressBar {
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    text-align: center;
    font-size: 10pt;
    background-color: #f5f5f5;
}
QProgressBar::chunk {
    background-color: #1a73e8;
    border-radius: 3px;
}

/* ==================== 状态栏 ==================== */
QStatusBar {
    background-color: #ffffff;
    border-top: 1px solid #e8eaed;
    color: #999;
    font-size: 9pt;
}
QStatusBar::item {
    border: none;
}

/* ==================== 对话框 ==================== */
QDialog {
    background-color: #ffffff;
}

/* ==================== 滚动条 ==================== */
QScrollBar:vertical {
    border: none;
    background: #f0f2f5;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background: #c4c8d0;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background: #a0a4ac;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    border: none;
    background: #f0f2f5;
    height: 10px;
    border-radius: 5px;
}
QScrollBar::handle:horizontal {
    background: #c4c8d0;
    border-radius: 5px;
    min-width: 30px;
}
QScrollBar::handle:horizontal:hover {
    background: #a0a4ac;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* ==================== 提示框 ==================== */
QToolTip {
    background-color: #333333;
    color: #ffffff;
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 5px 8px;
    font-size: 9pt;
}

/* ==================== 消息框 ==================== */
QMessageBox {
    font-size: 10pt;
}
QMessageBox QLabel {
    font-size: 10pt;
    /*min-width: 180px;*/
}

/* ==================== 字体下拉框 ==================== */
QFontComboBox {
    padding: 3px 6px;
    border: 1px solid #d0d4dc;
    border-radius: 4px;
    font-size: 10pt;
    min-height: 24px;
}
QFontComboBox QAbstractItemView {
    min-height: 300px;
    border: 1px solid #d0d4dc;
    border-radius: 4px;
    background-color: #ffffff;
    selection-background-color: #e8f0fe;
    selection-color: #1a73e8;
    outline: none;
    padding: 4px;
}
QFontComboBox QAbstractItemView::item {
    padding: 4px 8px;
    min-height: 22px;
}

/* ==================== 分割线 ==================== */
QFrame[frameShape="4"], QFrame[frameShape="5"] {
    color: #e0e0e0;
}
"""

# 注入对钩图片绝对路径（避免 QSS 中使用相对路径在打包后失效）
GLOBAL_QSS = GLOBAL_QSS.replace('__CHECKMARK_URL__', _CHECKMARK_URL)
