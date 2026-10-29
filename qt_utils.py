# -*- coding: utf-8 -*-
"""Qt UI 中文化工具

通过全局事件过滤器自动翻译：
  1. QMessageBox 标准按钮 (OK / Cancel / Yes / No / Ignore ...)
  2. QLineEdit 右键菜单 (Undo / Redo / Cut / Copy / Paste / Select All)
  3. QTextEdit 右键菜单 (同上，供 RichTextEditor 调用)
"""

from PyQt5.QtCore import QObject, QEvent
from PyQt5.QtWidgets import QMessageBox, QLineEdit

# 按钮英文 -> 中文（去除 & 助记符后的规范化 key）
BTN_CN = {
    'OK': '确定',
    'Cancel': '取消',
    'Yes': '是',
    'No': '否',
    'Ignore': '忽略',
    'Close': '关闭',
    'Save': '保存',
    'Discard': '丢弃',
    'Abort': '中止',
    'Retry': '重试',
    'Apply': '应用',
    'Reset': '重置',
    'Restore Defaults': '恢复默认',
    'Help': '帮助',
}

# 右键菜单项英文 -> 中文（去除 & 助记符后的规范化 key）
MENU_CN = {
    'Undo': '撤销',
    'Redo': '重做',
    'Cut': '剪切',
    'Copy': '复制',
    'Paste': '粘贴',
    'Delete': '删除',
    'Select All': '全选',
}


def _split_shortcut(text):
    """将 action 文本拆为 (去除&的base, \\t快捷键后缀)"""
    parts = text.split('\t', 1)
    base = parts[0].replace('&', '')
    shortcut = '\t' + parts[1] if len(parts) > 1 else ''
    return base, shortcut


def translate_menu_actions(menu):
    """翻译 QMenu 中所有 action 文字为中文"""
    for action in menu.actions():
        if not action.text():
            continue
        base, shortcut = _split_shortcut(action.text())
        cn = MENU_CN.get(base)
        if cn:
            action.setText(cn + shortcut)


class ChineseUiFilter(QObject):
    """全局事件过滤器：将标准 UI 元素翻译为中文"""

    def eventFilter(self, obj, event):
        # QMessageBox 显示时翻译按钮文字
        if event.type() == QEvent.Show and isinstance(obj, QMessageBox):
            for btn in obj.buttons():
                base, _ = _split_shortcut(btn.text())
                cn = BTN_CN.get(base)
                if cn:
                    btn.setText(cn)

        # QLineEdit 右键菜单翻译
        elif event.type() == QEvent.ContextMenu and isinstance(obj, QLineEdit):
            menu = obj.createStandardContextMenu()
            translate_menu_actions(menu)
            menu.exec_(event.globalPos())
            return True  # 事件已处理

        return False
