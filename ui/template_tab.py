# -*- coding: utf-8 -*-
"""模板设置 Tab - 模板CRUD + 富文本编辑 + 附件管理"""

import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QTextEdit, QCheckBox, QListWidget, QAbstractItemView,
    QMessageBox, QGroupBox, QFontComboBox, QSpinBox,
    QToolBar, QAction, QColorDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QTextCharFormat, QColor, QBrush

from db_manager import DatabaseManager
from qt_utils import translate_menu_actions
from ui.widgets import CheckableComboBox


class RichTextEditor(QTextEdit):
    """支持字体大小等格式的富文本编辑器"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptRichText(True)
        self.setMinimumHeight(120)

    def contextMenuEvent(self, event):
        """右键菜单中文化"""
        menu = self.createStandardContextMenu()
        translate_menu_actions(menu)
        menu.exec_(event.globalPos())

    def insertFromMimeData(self, source):
        """粘贴时保留富文本格式"""
        if source.hasHtml():
            self.insertHtml(source.html())
        elif source.hasText():
            self.insertPlainText(source.text())


class PathInputDialog(QDialog):
    """附件路径输入弹窗"""

    def __init__(self, parent=None, title='添加附件', initial_path=''):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(710)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 16)
        layout.setSpacing(14)

        label = QLabel('请输入附件文件完整路径：')
        layout.addWidget(label)

        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText('例：W:\\估值表导出\\YYYYMMDD\\证券投资基金估值表_博远增强回报债券型证券投资基金_YYYY-MM-DD.xls')
        self.path_edit.setMinimumHeight(34)
        self.path_edit.setText(initial_path)
        self.path_edit.returnPressed.connect(self.accept)
        layout.addWidget(self.path_edit)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton('确定')
        ok_btn.setObjectName('primary_btn')
        ok_btn.setMinimumWidth(90)
        ok_btn.setMinimumHeight(34)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        cancel_btn = QPushButton('取消')
        cancel_btn.setMinimumWidth(90)
        cancel_btn.setMinimumHeight(34)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        self.path_edit.setFocus()

    def get_path(self):
        return self.path_edit.text()


class TemplateEditDialog(QDialog):
    """模板新增/编辑对话框"""

    def __init__(self, db_manager: DatabaseManager,
                 mode='add', template_data=None, parent=None, readonly=False):
        super().__init__(parent)
        self.db_manager = db_manager
        self.mode = mode
        self.template_data = template_data or {}
        self.readonly = readonly
        self._original_name = self.template_data.get('template_name', '')
        self._init_ui()
        if mode in ('edit', 'copy') or readonly:
            self._fill_form()
        if readonly:
            self._apply_readonly()

    def _init_ui(self):
        if self.readonly:
            tname = self.template_data.get('template_name', '')
            title = f'查看 - {tname}' if tname else '查看'
        elif self.mode == 'edit':
            title = '编辑模板'
        elif self.mode == 'copy':
            title = '复制模板'
        else:
            title = '新增模板'
        self.setWindowTitle(f'{title}')
        self.setMinimumWidth(780)
        self.setMinimumHeight(900)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # --- 基本信息区 ---
        info_group = QGroupBox('基本信息')
        info_form = QFormLayout(info_group)
        info_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        info_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        info_form.setHorizontalSpacing(16)
        info_form.setVerticalSpacing(18)
        info_form.setContentsMargins(16, 24, 16, 16)

        input_min_height = 24

        # 模板名称 + 模板分类（同一行）
        name_class_layout = QHBoxLayout()
        name_class_layout.setSpacing(8)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText('模板名称（唯一，不可重复）')
        self.name_edit.setMinimumHeight(input_min_height)
        name_class_layout.addWidget(self.name_edit, stretch=3)

        name_class_layout.addWidget(QLabel('分类：'))

        self.class_edit = QLineEdit()
        self.class_edit.setPlaceholderText('模板分类')
        self.class_edit.setMinimumHeight(input_min_height)
        if self.mode == 'add':
            self.class_edit.setText('未分类')
        name_class_layout.addWidget(self.class_edit, stretch=2)

        info_form.addRow('模板名称 *：', name_class_layout)

        self.recipients_edit = QLineEdit()
        self.recipients_edit.setPlaceholderText('多个地址用逗号或分号分隔')
        self.recipients_edit.setMinimumHeight(input_min_height)
        info_form.addRow('收件人 *：', self.recipients_edit)

        self.cc_edit = QLineEdit()
        self.cc_edit.setPlaceholderText('多个地址用逗号或分号分隔')
        self.cc_edit.setMinimumHeight(input_min_height)
        info_form.addRow('抄送人：', self.cc_edit)

        self.bcc_edit = QLineEdit()
        self.bcc_edit.setPlaceholderText('多个地址用逗号或分号分隔')
        self.bcc_edit.setMinimumHeight(input_min_height)
        info_form.addRow('暗送人：', self.bcc_edit)

        self.subject_edit = QLineEdit()
        self.subject_edit.setPlaceholderText('支持日期宏：YYYYMMDD, YYYY-MM-DD 等')
        self.subject_edit.setMinimumHeight(input_min_height)
        info_form.addRow('主题 *：', self.subject_edit)

        self.status_check = QCheckBox('启用此模板')
        self.status_check.setChecked(True)
        info_form.addRow('状态：', self.status_check)

        layout.addWidget(info_group)

        # --- 正文区（含富文本工具栏）---
        body_group = QGroupBox('正文（富文本，支持日期宏）')
        body_layout = QVBoxLayout(body_group)
        body_layout.setContentsMargins(16, 24, 16, 16)
        body_layout.setSpacing(6)

        toolbar = self._build_rich_text_toolbar()
        if self.readonly:
            toolbar.setVisible(False)
        body_layout.addWidget(toolbar)

        self.body_edit = RichTextEditor()
        self.body_edit.setMinimumHeight(120)
        body_layout.addWidget(self.body_edit)

        layout.addWidget(body_group, stretch=1)

        # --- 附件区 ---
        attach_group = QGroupBox('附件设置')
        attach_layout = QVBoxLayout(attach_group)
        attach_layout.setContentsMargins(16, 24, 16, 16)
        attach_layout.setSpacing(10)

        # 第一行：包含附件复选框 + 添加/删除/清空按钮（全部在同一行）
        attach_top_layout = QHBoxLayout()
        attach_top_layout.setSpacing(8)

        self.has_attachment_check = QCheckBox('包含附件')
        if self.mode == 'add':
            self.has_attachment_check.setChecked(True)
        self.has_attachment_check.toggled.connect(self._on_attachment_toggled)
        attach_top_layout.addWidget(self.has_attachment_check)

        attach_top_layout.addStretch()

        if not self.readonly:
            self.add_path_btn = QPushButton('添加')
            self.add_path_btn.setMinimumWidth(70)
            self.add_path_btn.clicked.connect(self._add_attachment)
            attach_top_layout.addWidget(self.add_path_btn)

            self.modify_attach_btn = QPushButton('修改')
            self.modify_attach_btn.setMinimumWidth(70)
            self.modify_attach_btn.clicked.connect(self._modify_attachment)
            attach_top_layout.addWidget(self.modify_attach_btn)

            self.del_attach_btn = QPushButton('删除选中')
            self.del_attach_btn.setMinimumWidth(90)
            self.del_attach_btn.clicked.connect(self._del_attachment)
            attach_top_layout.addWidget(self.del_attach_btn)

            self.clear_attach_btn = QPushButton('清空附件')
            self.clear_attach_btn.setMinimumWidth(90)
            self.clear_attach_btn.clicked.connect(self._clear_attachments)
            attach_top_layout.addWidget(self.clear_attach_btn)

        attach_layout.addLayout(attach_top_layout)

        # 附件路径列表
        self.attachment_list = QListWidget()
        self.attachment_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.attachment_list.setMinimumHeight(70)
        self.attachment_list.setEnabled(self.has_attachment_check.isChecked())
        self.attachment_list.itemDoubleClicked.connect(
            lambda item: self._modify_attachment()
        )
        attach_layout.addWidget(self.attachment_list)

        # 初始化按钮启用状态
        if not self.readonly:
            self._on_attachment_toggled(self.has_attachment_check.isChecked())

        layout.addWidget(attach_group)

        # --- 按钮区 ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_layout.addStretch()
        if self.readonly:
            close_btn = QPushButton('关闭')
            close_btn.setObjectName('primary_btn')
            close_btn.setMinimumWidth(100)
            close_btn.setMinimumHeight(34)
            close_btn.clicked.connect(self.accept)
            btn_layout.addWidget(close_btn)
        else:
            save_btn = QPushButton('保存')
            save_btn.setObjectName('primary_btn')
            save_btn.setMinimumWidth(100)
            save_btn.setMinimumHeight(34)
            save_btn.clicked.connect(self._on_save)
            btn_layout.addWidget(save_btn)
            cancel_btn = QPushButton('取消')
            cancel_btn.setMinimumWidth(100)
            cancel_btn.setMinimumHeight(34)
            cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _build_rich_text_toolbar(self):
        """构建富文本格式工具栏"""
        toolbar = QToolBar()
        toolbar.setMovable(False)

        # 字体
        font_combo = QFontComboBox()
        font_combo.setMaxVisibleItems(30)
        font_combo.currentFontChanged.connect(
            lambda f: self.body_edit.setCurrentFont(f)
        )
        # 确保下拉弹窗有足够高度显示全部字体
        font_combo.view().setMinimumHeight(300)
        # 点击整个框体（非仅箭头）也能弹出下拉
        font_combo.lineEdit().installEventFilter(self)
        toolbar.addWidget(font_combo)
        toolbar.addWidget(QLabel('  '))

        # 字号
        size_combo = QSpinBox()
        size_combo.setRange(6, 72)
        size_combo.setValue(10)
        size_combo.setSuffix(' pt')
        size_combo.valueChanged.connect(
            lambda s: self.body_edit.setFontPointSize(s)
        )
        toolbar.addWidget(size_combo)
        toolbar.addWidget(QLabel('  '))

        # 加粗
        bold_action = QAction('B', self)
        bold_action.setCheckable(True)
        bold_action.setFont(QFont('Arial', 10, QFont.Bold))
        bold_action.triggered.connect(
            lambda: self.body_edit.setFontWeight(
                QFont.Bold if bold_action.isChecked() else QFont.Normal
            )
        )
        toolbar.addAction(bold_action)

        # 斜体
        italic_action = QAction('I', self)
        italic_action.setCheckable(True)
        italic_font = QFont('Arial', 10)
        italic_font.setItalic(True)
        italic_action.setFont(italic_font)
        italic_action.triggered.connect(
            lambda: self.body_edit.setFontItalic(italic_action.isChecked())
        )
        toolbar.addAction(italic_action)

        # 下划线
        underline_action = QAction('U', self)
        underline_action.setCheckable(True)
        underline_font = QFont('Arial', 10)
        underline_font.setUnderline(True)
        underline_action.setFont(underline_font)
        underline_action.triggered.connect(
            lambda: self.body_edit.setFontUnderline(underline_action.isChecked())
        )
        toolbar.addAction(underline_action)

        toolbar.addSeparator()

        # 颜色
        color_action = QAction('颜色', self)
        color_action.triggered.connect(self._set_text_color)
        toolbar.addAction(color_action)

        toolbar.addSeparator()

        # 对齐
        left_align = QAction('左对齐', self)
        left_align.triggered.connect(
            lambda: self.body_edit.setAlignment(Qt.AlignLeft)
        )
        toolbar.addAction(left_align)

        center_align = QAction('居中', self)
        center_align.triggered.connect(
            lambda: self.body_edit.setAlignment(Qt.AlignCenter)
        )
        toolbar.addAction(center_align)

        right_align = QAction('右对齐', self)
        right_align.triggered.connect(
            lambda: self.body_edit.setAlignment(Qt.AlignRight)
        )
        toolbar.addAction(right_align)

        return toolbar

    def _set_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.body_edit.setTextColor(color)

    def eventFilter(self, obj, event):
        """事件过滤器：QFontComboBox 的 lineEdit 点击时弹出下拉"""
        if event.type() == event.MouseButtonPress:
            from PyQt5.QtWidgets import QFontComboBox
            parent = obj.parent()
            if isinstance(parent, QFontComboBox):
                parent.showPopup()
                return True
        return super().eventFilter(obj, event)

    def _on_attachment_toggled(self, checked):
        """附件复选框状态变化"""
        self.attachment_list.setEnabled(checked)
        if self.readonly:
            return
        self.add_path_btn.setEnabled(checked)
        self.modify_attach_btn.setEnabled(checked)
        self.del_attach_btn.setEnabled(checked)
        self.clear_attach_btn.setEnabled(checked)

    def _add_attachment(self):
        """添加附件路径（自定义弹窗输入）"""
        dialog = PathInputDialog(self, title='添加附件')
        if dialog.exec_() != QDialog.Accepted:
            return
        path = dialog.get_path().strip()
        if not path:
            QMessageBox.warning(self, '提示', '附件路径不能为空')
            return
        # 检查是否重复
        for i in range(self.attachment_list.count()):
            if self.attachment_list.item(i).text() == path:
                QMessageBox.warning(self, '提示', '该附件路径已存在')
                return
        self.attachment_list.addItem(path)

    def _modify_attachment(self):
        """修改选中的附件路径"""
        current_item = self.attachment_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, '提示', '请先选择要修改的附件')
            return
        old_path = current_item.text()
        dialog = PathInputDialog(self, title='修改附件', initial_path=old_path)
        if dialog.exec_() != QDialog.Accepted:
            return
        new_path = dialog.get_path().strip()
        if not new_path:
            QMessageBox.warning(self, '提示', '附件路径不能为空')
            return
        if new_path == old_path:
            return
        # 检查是否与其他项重复
        for i in range(self.attachment_list.count()):
            if i == self.attachment_list.row(current_item):
                continue
            if self.attachment_list.item(i).text() == new_path:
                QMessageBox.warning(self, '提示', '该附件路径已存在')
                return
        current_item.setText(new_path)

    def _del_attachment(self):
        """删除选中的附件"""
        for item in self.attachment_list.selectedItems():
            self.attachment_list.takeItem(self.attachment_list.row(item))

    def _clear_attachments(self):
        """清空附件列表"""
        self.attachment_list.clear()

    def _fill_form(self):
        """编辑/复制模式下填充表单"""
        d = self.template_data
        # 复制模式：模板名称留空可编辑
        if self.mode == 'copy':
            self.name_edit.setText('')
        else:
            self.name_edit.setText(d.get('template_name', ''))
            #self.name_edit.setReadOnly(True)  # 编辑模式主键不可修改
        tc = d.get('template_class', '')
        self.class_edit.setText(tc if tc.strip() else '未分类')
        self.recipients_edit.setText(d.get('recipients', ''))
        self.cc_edit.setText(d.get('cc', ''))
        self.bcc_edit.setText(d.get('bcc', ''))
        self.subject_edit.setText(d.get('subject', ''))
        self.body_edit.setHtml(d.get('body', ''))
        has_att = bool(d.get('has_attachment', 0))
        self.has_attachment_check.setChecked(has_att)

        paths = d.get('attachment_paths', '[]')
        if isinstance(paths, str):
            try:
                paths = json.loads(paths)
            except json.JSONDecodeError:
                paths = []
        for p in paths:
            self.attachment_list.addItem(p)

        self.status_check.setChecked(bool(d.get('status', 1)))

    def _apply_readonly(self):
        """只读模式：禁用所有输入控件"""
        for w in (self.name_edit, self.class_edit, self.recipients_edit,
                  self.cc_edit, self.bcc_edit, self.subject_edit):
            w.setReadOnly(True)
        self.body_edit.setReadOnly(True)
        self.status_check.setEnabled(False)
        self.has_attachment_check.setEnabled(False)
        self.attachment_list.setEnabled(False)

    def _get_form_data(self):
        """收集表单数据"""
        attachment_paths = []
        for i in range(self.attachment_list.count()):
            attachment_paths.append(self.attachment_list.item(i).text())

        return {
            'template_name': self.name_edit.text().strip(),
            'template_class': self.class_edit.text().strip(),
            'recipients': self.recipients_edit.text().strip(),
            'cc': self.cc_edit.text().strip(),
            'bcc': self.bcc_edit.text().strip(),
            'subject': self.subject_edit.text().strip(),
            'body': self.body_edit.toHtml(),
            'has_attachment': self.has_attachment_check.isChecked(),
            'attachment_paths': attachment_paths,
            'status': 1 if self.status_check.isChecked() else 0,
        }

    def _on_save(self):
        """保存模板"""
        data = self._get_form_data()

        # 校验必填项
        if not data['template_name']:
            QMessageBox.warning(self, '提示', '请输入模板名称')
            self.name_edit.setFocus()
            return
        if not data['template_class']:
            QMessageBox.warning(self, '提示', '请选择模板分类')
            self.class_edit.setFocus()
            return
        if not data['recipients']:
            QMessageBox.warning(self, '提示', '请输入收件人')
            self.recipients_edit.setFocus()
            return
        if not data['subject']:
            QMessageBox.warning(self, '提示', '请输入主题')
            self.subject_edit.setFocus()
            return

        # 勾选了包含附件但没有设置附件路径
        if data['has_attachment'] and not data['attachment_paths']:
            QMessageBox.warning(
                self, '提示',
                '已勾选"包含附件"但未设置附件路径，\n请添加附件路径或取消勾选。'
            )
            return

        if self.mode in ('add', 'copy'):
            success, message = self.db_manager.add_template(data)
        else:
            success, message = self.db_manager.update_template(
                self._original_name, data
            )

        if success:
            QMessageBox.information(self, '成功', message)
            self.accept()
        else:
            QMessageBox.warning(self, '提示', message)


class TemplateTab(QWidget):
    """模板设置 Tab 页面"""

    template_changed = pyqtSignal()  # 模板变更信号（通知发送Tab刷新）

    # 停用行的背景色和文字色
    DISABLED_BG = QColor('#f0f0f0')
    DISABLED_FG = QColor('#999999')
    ENABLED_FG = QColor('#333333')

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self._init_ui()
        self._refresh_class_options()
        self.refresh_table()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # --- 查询区 ---
        query_group = QGroupBox('查询')
        query_layout = QHBoxLayout(query_group)
        query_layout.setContentsMargins(14, 18, 14, 14)
        query_layout.setSpacing(8)

        query_layout.addWidget(QLabel('模板分类：'))
        self.class_filter = CheckableComboBox()
        self.class_filter.setMinimumWidth(140)
        self.class_filter.selectionChanged.connect(self.refresh_table)
        query_layout.addWidget(self.class_filter)

        query_layout.addWidget(QLabel('模板名称：'))
        self.name_filter = QLineEdit()
        self.name_filter.textChanged.connect(self.refresh_table)
        query_layout.addWidget(self.name_filter)

        query_layout.addWidget(QLabel('收件人：'))
        self.recipient_filter = QLineEdit()
        self.recipient_filter.textChanged.connect(self.refresh_table)
        query_layout.addWidget(self.recipient_filter)

        query_layout.addWidget(QLabel('主题：'))
        self.subject_filter = QLineEdit()
        self.subject_filter.textChanged.connect(self.refresh_table)
        query_layout.addWidget(self.subject_filter)

        query_layout.addWidget(QLabel('状态：'))
        self.status_filter = QComboBox()
        self.status_filter.addItems(['全部', '启用', '停用'])
        self.status_filter.currentIndexChanged.connect(self.refresh_table)
        query_layout.addWidget(self.status_filter)

        reset_btn = QPushButton('重置')
        reset_btn.clicked.connect(self._reset_query)
        query_layout.addWidget(reset_btn)

        layout.addWidget(query_group)

        # --- 操作按钮区（查询条件下方，列表上方） ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        add_btn = QPushButton('新增模板')
        add_btn.setMinimumWidth(90)
        add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton('编辑模板')
        edit_btn.setMinimumWidth(90)
        edit_btn.clicked.connect(self._on_edit_button)
        btn_layout.addWidget(edit_btn)

        copy_btn = QPushButton('复制模板')
        copy_btn.setMinimumWidth(90)
        copy_btn.clicked.connect(self._on_copy)
        btn_layout.addWidget(copy_btn)

        delete_btn = QPushButton('删除模板')
        delete_btn.setMinimumWidth(90)
        delete_btn.clicked.connect(self._on_delete)
        btn_layout.addWidget(delete_btn)

        toggle_btn = QPushButton('启用/停用')
        toggle_btn.setMinimumWidth(90)
        toggle_btn.clicked.connect(self._on_toggle_status)
        btn_layout.addWidget(toggle_btn)

        btn_layout.addStretch()

        refresh_btn = QPushButton('刷新')
        refresh_btn.setMinimumWidth(80)
        refresh_btn.clicked.connect(self.refresh_table)
        btn_layout.addWidget(refresh_btn)

        layout.addLayout(btn_layout)

        # --- 表格 ---
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels([
            '模板分类', '模板名称', '收件人', '抄送人', '主题',
            '附件', '状态', '创建时间'
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.doubleClicked.connect(self._on_edit)
        layout.addWidget(self.table, stretch=1)

        # --- 统计栏 ---
        self.stats_label = QLabel('')
        self.stats_label.setStyleSheet(
            'color: #666; font-size: 9pt; padding: 2px 4px;'
        )
        layout.addWidget(self.stats_label)

    def _refresh_class_options(self):
        """从数据库刷新模板分类下拉选项（保留当前选中状态）"""
        current_selected = set(self.class_filter.get_selected_items())
        classes = self.db_manager.get_template_classes()
        self.class_filter.blockSignals(True)
        self.class_filter.set_items(classes)
        # 恢复之前的选中状态
        if current_selected:
            model = self.class_filter.model()
            for i in range(1, model.rowCount()):
                item = model.item(i)
                if item:
                    if item.text() in current_selected:
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)
            # 更新"全选"状态
            if model.rowCount() > 1:
                all_checked = all(
                    model.item(i).checkState() == Qt.Checked
                    for i in range(1, model.rowCount())
                )
                model.item(0).setCheckState(
                    Qt.Checked if all_checked else Qt.Unchecked
                )
        # 更新显示文本
        self.class_filter._update_text()
        self.class_filter.blockSignals(False)

    def _reset_query(self):
        self.name_filter.blockSignals(True)
        self.recipient_filter.blockSignals(True)
        self.subject_filter.blockSignals(True)
        self.status_filter.blockSignals(True)
        self.name_filter.clear()
        self.recipient_filter.clear()
        self.subject_filter.clear()
        self.status_filter.setCurrentIndex(0)
        # 重置分类为全选
        model = self.class_filter.model()
        for i in range(model.rowCount()):
            model.item(i).setCheckState(Qt.Checked)
        self.class_filter._update_text()
        self.name_filter.blockSignals(False)
        self.recipient_filter.blockSignals(False)
        self.subject_filter.blockSignals(False)
        self.status_filter.blockSignals(False)
        self.refresh_table()

    def refresh_table(self):
        """刷新表格数据"""
        name = self.name_filter.text().strip()
        recipient = self.recipient_filter.text().strip()
        subject = self.subject_filter.text().strip()
        status_idx = self.status_filter.currentIndex()
        status_filter = None
        if status_idx == 1:
            status_filter = 1
        elif status_idx == 2:
            status_filter = 0

        class_filter = self.class_filter.get_selected_items()

        templates = self.db_manager.get_templates(
            name, recipient, subject, status_filter,
            class_filter if class_filter else None
        )

        self.table.setRowCount(0)
        enabled_count = 0
        disabled_count = 0

        for t in templates:
            row = self.table.rowCount()
            self.table.insertRow(row)

            is_enabled = bool(t.get('status', 1))
            if is_enabled:
                enabled_count += 1
            else:
                disabled_count += 1

            # 根据状态设置整行颜色
            row_bg = self.DISABLED_BG if not is_enabled else None
            row_fg = self.DISABLED_FG if not is_enabled else self.ENABLED_FG

            def _make_item(text, fg=None, bg=None):
                item = QTableWidgetItem(text)
                if fg is not None:
                    item.setForeground(fg)
                if bg is not None:
                    item.setBackground(bg)
                return item

            self.table.setItem(row, 0, _make_item(t.get('template_class', ''), row_fg, row_bg))
            self.table.setItem(row, 1, _make_item(t.get('template_name', ''), row_fg, row_bg))
            self.table.setItem(row, 2, _make_item(t.get('recipients', ''), row_fg, row_bg))
            self.table.setItem(row, 3, _make_item(t.get('cc', ''), row_fg, row_bg))
            self.table.setItem(row, 4, _make_item(t.get('subject', ''), row_fg, row_bg))

            # 附件信息
            has_att = bool(t.get('has_attachment', 0))
            att_paths = t.get('attachment_paths', '[]')
            if isinstance(att_paths, str):
                try:
                    att_list = json.loads(att_paths)
                except json.JSONDecodeError:
                    att_list = []
            else:
                att_list = att_paths or []
            att_text = f'{len(att_list)} 个' if has_att and att_list else ('包含(无路径)' if has_att else '无')
            self.table.setItem(row, 5, _make_item(att_text, row_fg, row_bg))

            # 状态
            status_text = '启用' if is_enabled else '停用'
            status_item = QTableWidgetItem(status_text)
            if is_enabled:
                status_item.setForeground(QColor('#2e7d32'))
            else:
                status_item.setForeground(QColor('#d32f2f'))
            if row_bg is not None:
                status_item.setBackground(row_bg)
            self.table.setItem(row, 6, status_item)

            self.table.setItem(row, 7, _make_item(t.get('created_at', ''), row_fg, row_bg))

        # 存储完整数据用于编辑
        self._templates_data = templates

        # 更新统计
        total = len(templates)
        self.stats_label.setText(
            f'共 {total} 条  |  启用 {enabled_count} 条  |  停用 {disabled_count} 条'
        )

    def _get_selected_template_name(self):
        """获取当前选中行的模板名称"""
        row = self.table.currentRow()
        if row < 0:
            return None
        return self.table.item(row, 1).text()

    def _get_selected_template_data(self):
        """获取当前选中行的完整模板数据"""
        name = self._get_selected_template_name()
        if not name:
            return None
        for t in self._templates_data:
            if t['template_name'] == name:
                return t
        return None

    def _on_add(self):
        """新增模板"""
        dialog = TemplateEditDialog(self.db_manager, mode='add', parent=self)
        if dialog.exec_() == QDialog.Accepted:
            self._refresh_class_options()
            self.refresh_table()
            self.template_changed.emit()

    def _on_edit_button(self):
        """编辑按钮"""
        self._on_edit()

    def _on_edit(self):
        """编辑模板（双击或按钮触发）"""
        data = self._get_selected_template_data()
        if not data:
            QMessageBox.warning(self, '提示', '请先选择要编辑的模板')
            return
        dialog = TemplateEditDialog(
            self.db_manager, mode='edit', template_data=data, parent=self
        )
        if dialog.exec_() == QDialog.Accepted:
            self._refresh_class_options()
            self.refresh_table()
            self.template_changed.emit()

    def _on_copy(self):
        """复制模板（带出全部内容，模板名称留空）"""
        data = self._get_selected_template_data()
        if not data:
            QMessageBox.warning(self, '提示', '请先选择要复制的模板')
            return
        dialog = TemplateEditDialog(
            self.db_manager, mode='copy', template_data=data, parent=self
        )
        if dialog.exec_() == QDialog.Accepted:
            self._refresh_class_options()
            self.refresh_table()
            self.template_changed.emit()

    def _on_delete(self):
        """删除模板"""
        name = self._get_selected_template_name()
        if not name:
            QMessageBox.warning(self, '提示', '请先选择要删除的模板')
            return
        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除模板 "{name}" 吗？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db_manager.delete_template(name)
            self._refresh_class_options()
            self.refresh_table()
            self.template_changed.emit()
            QMessageBox.information(self, '成功', '模板已删除')

    def _on_toggle_status(self):
        """切换启用/停用状态"""
        data = self._get_selected_template_data()
        if not data:
            QMessageBox.warning(self, '提示', '请先选择模板')
            return
        name = data['template_name']
        current_status = bool(data.get('status', 1))
        new_status = not current_status
        self.db_manager.toggle_template_status(name, new_status)
        self.refresh_table()
        self.template_changed.emit()
        status_text = '启用' if new_status else '停用'
        QMessageBox.information(self, '成功', f'模板已{status_text}')
