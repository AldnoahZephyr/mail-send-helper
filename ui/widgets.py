# -*- coding: utf-8 -*-
"""自定义可复用控件"""

from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QStandardItem, QStandardItemModel


class CheckableComboBox(QComboBox):
    """多选下拉框 - 支持全选/多选/不选

    第一项固定为"全选"，勾选/取消"全选"会联动所有子项。
    不选任何项 = 不过滤（显示全部）。
    点击整个框体均可弹出下拉（通过事件过滤器实现）。
    """

    selectionChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setEditable(True)
        self.lineEdit().setReadOnly(True)
        self.lineEdit().setPlaceholderText('全选')
        # 点击 lineEdit（框体中间区域）也能弹出下拉
        self.lineEdit().installEventFilter(self)
        self._model = QStandardItemModel()
        self.setModel(self._model)
        self._model.itemChanged.connect(self._on_item_changed)
        self._updating = False
        # 关键：阻止下拉点击后自动关闭（实现真正的多选）
        self.view().viewport().installEventFilter(self)

    def eventFilter(self, obj, event):
        """事件过滤器：
        - lineEdit 点击 → 弹出下拉
        - viewport 点击 → 手动切换复选框状态，阻止下拉关闭
        """
        if obj == self.lineEdit() and event.type() == event.MouseButtonPress:
            self.showPopup()
            return True
        if obj == self.view().viewport():
            if event.type() == event.MouseButtonPress:
                # 在 popup 内点击 → 手动切换对应项的复选框
                idx = self.view().indexAt(event.pos())
                if idx.isValid():
                    item = self._model.item(idx.row())
                    if item and item.isCheckable():
                        new_state = (
                            Qt.Unchecked
                            if item.checkState() == Qt.Checked
                            else Qt.Checked
                        )
                        item.setCheckState(new_state)
                # 吃掉事件，阻止 QComboBox 默认的"选中→关闭 popup"行为
                return True
            elif event.type() == event.MouseButtonRelease:
                return True  # 同样吃掉 release，防止触发关闭
        return super().eventFilter(obj, event)

    def mousePressEvent(self, event):
        """点击整个框体都能弹出下拉（覆盖默认行为）"""
        super().mousePressEvent(event)
        if not self.view().isVisible():
            self.showPopup()

    def set_items(self, items):
        """设置可选项列表（替换现有项），默认全部勾选"""
        self._updating = True
        self._model.clear()
        # "全选" 项
        all_item = QStandardItem('全选')
        all_item.setCheckable(True)
        all_item.setCheckState(Qt.Checked)
        self._model.appendRow(all_item)
        # 各分类项
        for text in items:
            item = QStandardItem(text)
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            self._model.appendRow(item)
        self._updating = False
        self._update_text()

    def get_selected_items(self):
        """返回已勾选的项文本列表（不含"全选"）。
        空列表表示不过滤（全选或全不选）。"""
        items = []
        for i in range(1, self._model.rowCount()):
            item = self._model.item(i)
            if item and item.checkState() == Qt.Checked:
                items.append(item.text())
        return items

    def _on_item_changed(self, item):
        if self._updating:
            return
        self._updating = True
        if item.row() == 0:
            # "全选" 被切换 - 联动所有子项
            state = item.checkState()
            for i in range(1, self._model.rowCount()):
                self._model.item(i).setCheckState(state)
        else:
            # 子项被切换 - 更新"全选"状态
            if self._model.rowCount() > 1:
                all_checked = all(
                    self._model.item(i).checkState() == Qt.Checked
                    for i in range(1, self._model.rowCount())
                )
                self._model.item(0).setCheckState(
                    Qt.Checked if all_checked else Qt.Unchecked
                )
        self._updating = False
        self._update_text()
        self.selectionChanged.emit()

    def _update_text(self):
        selected = self.get_selected_items()
        total = self._model.rowCount() - 1  # 排除"全选"
        if total <= 0:
            self.lineEdit().setText('')
        elif not selected:
            self.lineEdit().setText('未选')
        elif len(selected) == total:
            self.lineEdit().setText('全选')
        else:
            display = ', '.join(selected)
            if len(display) > 30:
                display = display[:28] + '...'
            self.lineEdit().setText(display)
