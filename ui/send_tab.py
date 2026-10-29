# -*- coding: utf-8 -*-
"""邮件发送 Tab - 发送列表 + 检查附件 + 发送逻辑"""

import json
import os
from datetime import datetime, date
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDateEdit, QCheckBox, QMessageBox, QProgressDialog, QGroupBox,
    QApplication
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal, QThread
from PyQt5.QtGui import QColor, QBrush

from db_manager import DatabaseManager
from date_macro import replace_date_macros
from email_sender import send_email, test_smtp_connection
from ui.template_tab import TemplateEditDialog
from ui.widgets import CheckableComboBox

# 发送状态排序优先级（值越小越靠前）
_STATUS_ORDER = {'未发送': 0, '发送失败': 1, '发送成功': 2}

# 发送状态对应的整行背景色
_STATUS_BG_COLOR = {
    '未发送':   QColor('#fafafa'),   # 浅灰，待处理
    '发送失败': QColor('#fff0f0'),   # 浅红，异常
    '发送成功': QColor('#f0faf0'),   # 浅绿，完成
}


def _parse_time_to_stamp(time_str):
    """将时间字符串解析为时间戳，用于排序比较"""
    if not time_str:
        return 0.0
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
        try:
            return datetime.strptime(time_str.strip(), fmt).timestamp()
        except ValueError:
            continue
    return 0.0


class SendEmailThread(QThread):
    """后台线程发送单封邮件"""
    finished_signal = pyqtSignal(bool, str, str)  # success, message, template_name

    def __init__(self, sender_config, email_data, template_name):
        super().__init__()
        self.sender_config = sender_config
        self.email_data = email_data
        self.template_name = template_name

    def run(self):
        success, message = send_email(self.sender_config, self.email_data)
        self.finished_signal.emit(success, message, self.template_name)


class SendTab(QWidget):
    """邮件发送 Tab 页面"""

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self._row_data = []  # 存储每行数据
        self._init_ui()
        self._refresh_class_options()
        self.refresh_table()  # 进入界面自动刷新

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # --- 查询区 ---
        query_group = QGroupBox('查询')
        query_layout = QHBoxLayout(query_group)
        query_layout.setContentsMargins(14, 18, 14, 14)
        query_layout.setSpacing(8)

        query_layout.addWidget(QLabel('日期：'))
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        self.date_edit.dateChanged.connect(self.refresh_table)
        query_layout.addWidget(self.date_edit)

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

        query_layout.addStretch()

        layout.addWidget(query_group)

        # --- 按钮区 ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        refresh_btn = QPushButton('刷新')
        refresh_btn.setMinimumWidth(80)
        refresh_btn.clicked.connect(self.refresh_table)
        btn_layout.addWidget(refresh_btn)

        check_btn = QPushButton('检查附件')
        check_btn.setMinimumWidth(90)
        check_btn.clicked.connect(self._on_check_attachments)
        btn_layout.addWidget(check_btn)

        send_btn = QPushButton('发送')
        send_btn.setObjectName('primary_btn')
        send_btn.setMinimumWidth(90)
        send_btn.clicked.connect(self._on_send)
        btn_layout.addWidget(send_btn)

        btn_layout.addStretch()

        # 清除记录按钮（在全选左侧）
        clear_btn = QPushButton('清除记录')
        clear_btn.setMinimumWidth(90)
        clear_btn.clicked.connect(self._on_clear_records)
        btn_layout.addWidget(clear_btn)

        # 全选/取消全选
        self.select_all_check = QCheckBox('全选/取消全选')
        self.select_all_check.stateChanged.connect(self._on_select_all)
        btn_layout.addWidget(self.select_all_check)

        layout.addLayout(btn_layout)

        # --- 数据表格 ---
        self.table = QTableWidget(0, 12)
        self.table.setHorizontalHeaderLabels([
            ' 选择 ', '模板分类', '模板名称', '日期', '收件人', '抄送人',
            '暗送人', '主题', '模板附件数', '附件数量',
            '发送状态', '发送时间'
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)  # 收件人
        header.setSectionResizeMode(7, QHeaderView.Stretch)  # 主题
        header.sectionClicked.connect(self._on_header_section_clicked)  # 列头点击
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(False)  # 使用按状态的整行着色替代交替行
        self.table.doubleClicked.connect(self._on_view)
        layout.addWidget(self.table, stretch=1)

        # --- 统计栏 ---
        self.stats_label = QLabel('')
        self.stats_label.setStyleSheet(
            'color: #666; font-size: 9pt; padding: 2px 4px;'
        )
        layout.addWidget(self.stats_label)

    def _get_selected_date_str(self):
        """获取当前选择的日期字符串 yyyy-MM-dd"""
        return self.date_edit.date().toString('yyyy-MM-dd')

    def _get_selected_date_obj(self):
        """获取当前选择的日期 date 对象"""
        d = self.date_edit.date()
        return date(d.year(), d.month(), d.day())

    def _refresh_class_options(self):
        """从数据库刷新模板分类下拉选项（只展示启用模板的分类，保留当前选中状态）"""
        current_selected = set(self.class_filter.get_selected_items())
        classes = self.db_manager.get_enabled_template_classes()
        self.class_filter.blockSignals(True)
        self.class_filter.set_items(classes)
        if current_selected:
            model = self.class_filter.model()
            for i in range(1, model.rowCount()):
                item = model.item(i)
                if item:
                    if item.text() in current_selected:
                        item.setCheckState(Qt.Checked)
                    else:
                        item.setCheckState(Qt.Unchecked)
            if model.rowCount() > 1:
                all_checked = all(
                    model.item(i).checkState() == Qt.Checked
                    for i in range(1, model.rowCount())
                )
                model.item(0).setCheckState(
                    Qt.Checked if all_checked else Qt.Unchecked
                )
        self.class_filter._update_text()
        self.class_filter.blockSignals(False)

    def refresh_table(self):
        """刷新表格数据 - 查询模板与发送记录的关联结果"""
        selected_date_str = self._get_selected_date_str()
        selected_date_obj = self._get_selected_date_obj()

        # 获取所有启用模板
        templates = self.db_manager.get_enabled_templates()

        # 获取当天所有发送记录
        records = self.db_manager.get_send_records_by_date(selected_date_str)
        record_map = {}
        for r in records:
            record_map[r['template_name']] = r

        # 查询过滤条件
        name_filter = self.name_filter.text().strip().lower()
        recipient_filter = self.recipient_filter.text().strip().lower()
        subject_filter = self.subject_filter.text().strip().lower()
        class_filter = self.class_filter.get_selected_items()

        self._row_data = []
        self.table.setRowCount(0)

        for tmpl in templates:
            tname = tmpl['template_name']
            record = record_map.get(tname)

            # 模板时间戳（用于无发送记录时的排序）
            tmpl_created = tmpl.get('created_at', '')
            tmpl_updated = tmpl.get('updated_at', '')

            if record:
                # 有发送记录 - 使用记录数据
                row_data = {
                    'template_name': tname,
                    'date': selected_date_str,
                    'recipients': record.get('recipients', ''),
                    'cc': record.get('cc', ''),
                    'bcc': record.get('bcc', ''),
                    'subject': record.get('subject', ''),
                    'body': record.get('body', ''),
                    'send_status': record.get('send_status', '未发送'),
                    'send_time': record.get('send_time', ''),
                    'has_record': True,
                    'has_attachment': bool(tmpl.get('has_attachment', 0)),
                    'template_attachment_paths_raw': tmpl.get('attachment_paths', '[]'),
                    'attachment_paths': self._parse_attachments(
                        record.get('attachments', '[]'), selected_date_obj
                    ),
                    'template_class': record.get('template_class', '') or tmpl.get('template_class', '') or '未分类',
                    'template_created_at': tmpl_created,
                    'template_updated_at': tmpl_updated,
                }
            else:
                # 无发送记录 - 使用模板数据（替换日期宏）
                subject = replace_date_macros(
                    tmpl.get('subject', ''), selected_date_obj
                )
                body = replace_date_macros(
                    tmpl.get('body', ''), selected_date_obj
                )
                row_data = {
                    'template_name': tname,
                    'date': selected_date_str,
                    'recipients': tmpl.get('recipients', ''),
                    'cc': tmpl.get('cc', ''),
                    'bcc': tmpl.get('bcc', ''),
                    'subject': subject,
                    'body': body,
                    'send_status': '未发送',
                    'send_time': '',
                    'has_record': False,
                    'has_attachment': bool(tmpl.get('has_attachment', 0)),
                    'template_attachment_paths_raw': tmpl.get('attachment_paths', '[]'),
                    'attachment_paths': self._parse_attachments(
                        tmpl.get('attachment_paths', '[]'), selected_date_obj
                    ),
                    'template_class': tmpl.get('template_class', '') or '未分类',
                    'template_created_at': tmpl_created,
                    'template_updated_at': tmpl_updated,
                }

            # 计算模板附件数和实际附件数量
            raw_paths = row_data.get('template_attachment_paths_raw', '[]')
            if isinstance(raw_paths, str):
                try:
                    raw_paths_list = json.loads(raw_paths)
                except json.JSONDecodeError:
                    raw_paths_list = []
            else:
                raw_paths_list = raw_paths or []

            if row_data['has_attachment']:
                row_data['template_attachment_count'] = len(raw_paths_list)
                # 实际存在的附件文件数
                actual_count = 0
                for p in row_data['attachment_paths']:
                    if p and os.path.isfile(p):
                        actual_count += 1
                row_data['actual_attachment_count'] = actual_count
            else:
                row_data['template_attachment_count'] = 0
                row_data['actual_attachment_count'] = 0

            # 应用过滤
            if name_filter and name_filter not in tname.lower():
                continue
            if recipient_filter and recipient_filter not in row_data['recipients'].lower():
                continue
            if subject_filter and subject_filter not in row_data['subject'].lower():
                continue
            if class_filter:
                tmpl_class = row_data.get('template_class', '')
                if tmpl_class not in class_filter:
                    continue

            self._row_data.append(row_data)

        # 排序：发送状态优先级 → 发送时间倒序 → 模板更新时间倒序 → 模板创建时间倒序
        self._row_data.sort(key=lambda r: (
            _STATUS_ORDER.get(r['send_status'], 99),
            -_parse_time_to_stamp(
                r.get('send_time', '')
                or r.get('template_updated_at', '')
                or r.get('template_created_at', '')
            ),
        ))

        # 填充表格
        for row_data in self._row_data:
            self._add_table_row(row_data)

        # 更新统计
        total = len(self._row_data)
        cnt_unsent = sum(1 for r in self._row_data if r['send_status'] == '未发送')
        cnt_success = sum(1 for r in self._row_data if r['send_status'] == '发送成功')
        cnt_fail = sum(1 for r in self._row_data if r['send_status'] == '发送失败')
        self.stats_label.setText(
            f'共 {total} 条  |  未发送 {cnt_unsent} 条  '
            f'|  发送成功 {cnt_success} 条  |  发送失败 {cnt_fail} 条'
        )

    def _parse_attachments(self, raw, target_date):
        """解析附件路径列表并替换日期宏"""
        if isinstance(raw, str):
            try:
                paths = json.loads(raw)
            except json.JSONDecodeError:
                paths = []
        elif isinstance(raw, list):
            paths = raw
        else:
            paths = []

        result = []
        for p in paths:
            replaced = replace_date_macros(p, target_date)
            result.append(replaced)
        return result

    def _add_table_row(self, row_data):
        """添加一行数据到表格"""
        row = self.table.rowCount()
        self.table.insertRow(row)

        # 整行背景色（按发送状态区分）
        bg_color = _STATUS_BG_COLOR.get(
            row_data['send_status'], QColor('#ffffff')
        )
        bg_brush = QBrush(bg_color)

        # 勾选框
        checkbox = QCheckBox()
        checkbox_widget = QWidget()
        cb_layout = QHBoxLayout(checkbox_widget)
        cb_layout.addWidget(checkbox)
        cb_layout.setAlignment(Qt.AlignCenter)
        cb_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_widget.setLayout(cb_layout)
        checkbox_widget.setStyleSheet(
            f'background-color: {bg_color.name()};'
        )
        # 所有记录均可勾选：发送成功/失败的可通过"清除记录"删除，
        # 发送成功的在"发送"时自动跳过（_on_send 已过滤）
        self.table.setCellWidget(row, 0, checkbox_widget)

        # 模板分类（col 1）
        class_item = QTableWidgetItem(row_data.get('template_class', ''))
        class_item.setBackground(bg_brush)
        self.table.setItem(row, 1, class_item)

        # 其他列（col 2-7）
        items = [
            QTableWidgetItem(row_data['template_name']),
            QTableWidgetItem(row_data['date']),
            QTableWidgetItem(row_data['recipients']),
            QTableWidgetItem(row_data['cc']),
            QTableWidgetItem(row_data['bcc']),
            QTableWidgetItem(row_data['subject']),
        ]
        for col, item in enumerate(items, start=2):
            item.setBackground(bg_brush)
            self.table.setItem(row, col, item)

        # 附件数
        tmpl_count = row_data['template_attachment_count']
        actual_count = row_data['actual_attachment_count']
        att_text = f'{actual_count}/{tmpl_count}'
        att_item = QTableWidgetItem(att_text)
        att_item.setBackground(bg_brush)
        if row_data['has_attachment'] and actual_count < tmpl_count:
            att_item.setForeground(QColor('#d32f2f'))
        elif row_data['has_attachment'] and actual_count == tmpl_count and tmpl_count > 0:
            att_item.setForeground(QColor('#2e7d32'))
        tmpl_item = QTableWidgetItem(str(tmpl_count))
        tmpl_item.setBackground(bg_brush)
        self.table.setItem(row, 8, tmpl_item)
        self.table.setItem(row, 9, att_item)

        # 发送状态
        status_item = QTableWidgetItem(row_data['send_status'])
        status_item.setBackground(bg_brush)
        if row_data['send_status'] == '发送成功':
            status_item.setForeground(QColor('#2e7d32'))
        elif row_data['send_status'] == '发送失败':
            status_item.setForeground(QColor('#d32f2f'))
        elif row_data['send_status'] == '未发送':
            status_item.setForeground(QColor('#666666'))
        self.table.setItem(row, 10, status_item)

        # 发送时间
        time_item = QTableWidgetItem(row_data['send_time'])
        time_item.setBackground(bg_brush)
        self.table.setItem(row, 11, time_item)

    def _on_view(self, index):
        """双击查看行数据（只读）"""
        row = index.row()
        if row < 0 or row >= len(self._row_data):
            return
        rd = self._row_data[row]

        # 构造 template_data，兼容 TemplateEditDialog._fill_form
        template_data = {
            'template_name': rd.get('template_name', ''),
            'recipients': rd.get('recipients', ''),
            'cc': rd.get('cc', ''),
            'bcc': rd.get('bcc', ''),
            'subject': rd.get('subject', ''),
            'body': rd.get('body', ''),
            'has_attachment': 1 if rd.get('has_attachment') else 0,
            'attachment_paths': rd.get('attachment_paths', []),
            'template_class': rd.get('template_class', ''),
            'status': 1,
        }

        dialog = TemplateEditDialog(
            self.db_manager, mode='edit',
            template_data=template_data, parent=self, readonly=True
        )
        dialog.exec_()

    def _on_header_section_clicked(self, section):
        """列头点击 — 第0列（勾选框列）实现全选/取消全选"""
        if section != 0:
            return
        # 判断当前状态：所有可用的勾选框是否已全部选中
        all_checked = True
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox and checkbox.isEnabled():
                    if not checkbox.isChecked():
                        all_checked = False
                        break
        # 如果全选则取消，否则全选
        new_state = not all_checked
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox and checkbox.isEnabled():
                    checkbox.setChecked(new_state)

    def _on_select_all(self, state):
        """全选/取消全选"""
        checked = state == Qt.Checked
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox and checkbox.isEnabled():
                    checkbox.setChecked(checked)

    def _on_clear_records(self):
        """清除勾选的发送记录"""
        selected_rows = self._get_selected_rows()
        if not selected_rows:
            QMessageBox.warning(self, '提示', '请先勾选要清除的记录')
            return

        # 检查是否有未发送的记录
        unsent_rows = [
            row for row in selected_rows
            if self._row_data[row]['send_status'] == '未发送'
        ]
        if unsent_rows:
            unsent_names = [
                self._row_data[row]['template_name'] for row in unsent_rows
            ]
            QMessageBox.warning(
                self, '提示',
                '以下记录尚未发送，无法清除：\n\n'
                + '\n'.join(f'  • {name}' for name in unsent_names)
                + '\n\n只能清除"发送成功"或"发送失败"的记录。'
            )
            return

        # 收集可清除的记录（发送成功 + 发送失败）
        clearable_rows = [
            row for row in selected_rows
            if self._row_data[row]['send_status'] in ('发送成功', '发送失败')
        ]
        if not clearable_rows:
            QMessageBox.warning(self, '提示', '没有可清除的记录')
            return

        # 构建确认提示
        detail = '\n'.join(
            f'  • {self._row_data[row]["template_name"]} '
            f'({self._row_data[row]["send_status"]})'
            for row in clearable_rows
        )
        reply = QMessageBox.question(
            self, '确认清除记录',
            f'即将清除 {len(clearable_rows)} 条发送记录：\n\n{detail}\n\n'
            f'注意：此操作仅删除程序中的发送记录，\n'
            f'不会实际删除或撤回已发送的邮件。\n\n'
            f'确定要继续吗？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # 批量删除
        selected_date_str = self._get_selected_date_str()
        deleted_count = 0
        for row in clearable_rows:
            rd = self._row_data[row]
            self.db_manager.delete_send_record(
                rd['template_name'], selected_date_str
            )
            deleted_count += 1

        # 取消全选状态
        self.select_all_check.setChecked(False)

        # 刷新表格
        self.refresh_table()
        QMessageBox.information(
            self, '成功', f'已清除 {deleted_count} 条发送记录'
        )

    def _get_selected_rows(self):
        """获取所有勾选行的索引列表（含所有发送状态）"""
        selected = []
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if widget:
                checkbox = widget.findChild(QCheckBox)
                if checkbox and checkbox.isChecked():
                    selected.append(row)
        return selected

    def _on_check_attachments(self):
        """检查附件按钮"""
        # 检查未发送和发送失败的（都可能是待发送的）
        checkable_rows = [
            i for i, rd in enumerate(self._row_data)
            if rd['send_status'] != '发送成功'
        ]

        if not checkable_rows:
            QMessageBox.information(
                self, '检查结果',
                '当前没有待发送的邮件，无需检查附件。'
            )
            return

        not_ready = []
        has_attachment_count = 0

        for idx in checkable_rows:
            row_data = self._row_data[idx]
            if not row_data['has_attachment']:
                continue
            has_attachment_count += 1

            tmpl_count = row_data['template_attachment_count']
            actual_count = row_data['actual_attachment_count']

            if tmpl_count == 0:
                continue
            if actual_count < tmpl_count:
                missing = tmpl_count - actual_count
                not_ready.append((row_data['template_name'], missing))

        if has_attachment_count == 0:
            QMessageBox.information(
                self, '检查结果',
                '所有待发送的邮件均不包含附件，无需检查。'
            )
        elif not_ready:
            detail = '\n'.join(
                f'  • {name}: 缺少 {count} 个附件文件'
                for name, count in not_ready
            )
            QMessageBox.warning(
                self, '检查结果',
                f'还有 {len(not_ready)} 个模板的附件未就绪：\n\n{detail}'
            )
        else:
            QMessageBox.information(
                self, '检查结果',
                f'所有待发送的邮件附件均已就绪（共 {has_attachment_count} 个含附件模板）。'
            )

    def _on_send(self):
        """发送按钮"""
        # 1. 检查勾选项
        selected_rows = self._get_selected_rows()

        if not selected_rows:
            QMessageBox.warning(self, '提示', '请先勾选要发送的邮件')
            return

        # 检查是否都已发送成功
        all_sent = True
        for row in selected_rows:
            if self._row_data[row]['send_status'] != '发送成功':
                all_sent = False
                break

        if all_sent:
            QMessageBox.information(self, '提示', '所选邮件均已发送成功，无需重复发送')
            return

        # 过滤出非发送成功的（失败和未发送的都可以重新发送）
        to_send_rows = [
            row for row in selected_rows
            if self._row_data[row]['send_status'] != '发送成功'
        ]
        skipped_sent = len(selected_rows) - len(to_send_rows)

        # 2. 检查发件人账户配置
        config = self.db_manager.get_sender_config()
        if not config:
            QMessageBox.warning(
                self, '提示',
                '尚未配置发件人信息，请先点击"参数设置"进行配置。'
            )
            return

        # 重新校验账户连接
        QApplication.setOverrideCursor(Qt.WaitCursor)
        ok, msg = test_smtp_connection(
            config['email_address'],
            config['smtp_server'],
            config['smtp_port'],
            config.get('password', ''),
            bool(config.get('use_ssl', 1))
        )
        QApplication.restoreOverrideCursor()

        if not ok:
            QMessageBox.warning(
                self, '账户校验失败',
                f'发件人账户连接校验未通过：\n{msg}\n\n请检查参数设置。'
            )
            return

        # 3. 确认发送
        send_msg = f'即将发送 {len(to_send_rows)} 封邮件，确定继续吗？'
        if skipped_sent > 0:
            send_msg += f'\n\n（已自动跳过 {skipped_sent} 条发送成功的记录）'
        reply = QMessageBox.question(
            self, '确认发送', send_msg,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        # 4. 逐一发送
        self._do_send(to_send_rows)

    def _do_send(self, row_indices):
        """逐一发送邮件"""
        total = len(row_indices)
        progress = QProgressDialog(
            '正在准备发送...', '取消', 0, total, self
        )
        progress.setWindowTitle('发送进度')
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)

        sent_count = 0
        fail_count = 0
        skip_count = 0
        config = self.db_manager.get_sender_config()

        # 预处理签名：若启用则替换日期宏后缓存
        sig_html = ''
        if config and config.get('signature_enabled', 1):
            sig_raw = config.get('signature_content', '') or ''
            if sig_raw.strip():
                selected_date_obj = self._get_selected_date_obj()
                sig_html = replace_date_macros(sig_raw, selected_date_obj)

        for i, row_idx in enumerate(row_indices):
            if progress.wasCanceled():
                break

            row_data = self._row_data[row_idx]
            tname = row_data['template_name']

            # 发送失败的邮件：重新查询最新模板数据（可能发送失败后修改了模板）
            if row_data['send_status'] == '发送失败':
                latest_tmpl = self.db_manager.get_template(tname)
                if latest_tmpl:
                    selected_date_obj = self._get_selected_date_obj()
                    row_data['recipients'] = latest_tmpl.get('recipients', '')
                    row_data['cc'] = latest_tmpl.get('cc', '')
                    row_data['bcc'] = latest_tmpl.get('bcc', '')
                    row_data['subject'] = replace_date_macros(
                        latest_tmpl.get('subject', ''), selected_date_obj
                    )
                    row_data['body'] = replace_date_macros(
                        latest_tmpl.get('body', ''), selected_date_obj
                    )
                    row_data['template_class'] = (
                        latest_tmpl.get('template_class', '') or '未分类'
                    )
                    # 重新解析附件路径
                    raw_paths = latest_tmpl.get('attachment_paths', '[]')
                    if isinstance(raw_paths, str):
                        try:
                            raw_paths_list = json.loads(raw_paths)
                        except json.JSONDecodeError:
                            raw_paths_list = []
                    else:
                        raw_paths_list = raw_paths or []
                    row_data['template_attachment_paths_raw'] = raw_paths
                    if row_data['has_attachment']:
                        row_data['template_attachment_count'] = len(raw_paths_list)
                        new_paths = [
                            replace_date_macros(p, selected_date_obj)
                            for p in raw_paths_list
                        ]
                        row_data['attachment_paths'] = new_paths
                        actual_count = sum(
                            1 for p in new_paths if p and os.path.isfile(p)
                        )
                        row_data['actual_attachment_count'] = actual_count
                    else:
                        row_data['template_attachment_count'] = 0
                        row_data['actual_attachment_count'] = 0

            progress.setLabelText(f'正在发送: {tname} ({i + 1}/{total})')
            progress.setValue(i)
            QApplication.processEvents()

            # 检查附件
            if row_data['has_attachment']:
                tmpl_count = row_data['template_attachment_count']
                actual_count = row_data['actual_attachment_count']

                if tmpl_count > 0 and actual_count < tmpl_count:
                    # 弹窗提示附件未就绪
                    reply = QMessageBox.question(
                        self, '附件未就绪',
                        f'模板 "{tname}" 的附件不存在或未完全就绪'
                        f'（{actual_count}/{tmpl_count}）。\n\n'
                        f'选择"忽略"跳过此模板继续发送其他，'
                        f'选择"取消"停止发送。',
                        QMessageBox.Ignore | QMessageBox.Cancel,
                        QMessageBox.Ignore
                    )
                    if reply == QMessageBox.Ignore:
                        skip_count += 1
                        continue
                    else:
                        break

            # 准备邮件数据（附加签名）
            send_body = row_data['body']
            if sig_html:
                send_body = send_body + '<br><br><hr/>' + sig_html

            email_data = {
                'recipients': row_data['recipients'],
                'cc': row_data['cc'],
                'bcc': row_data['bcc'],
                'subject': row_data['subject'],
                'body': send_body,
                'attachment_paths': row_data['attachment_paths']
                    if row_data['has_attachment'] else [],
            }

            # 发送
            success, message = send_email(config, email_data)

            # 记录发送结果
            now = datetime.now()
            send_time = now.strftime('%Y-%m-%d %H:%M')
            send_date_str = row_data['date']

            record = {
                'template_name': tname,
                'send_date': send_date_str,
                'recipients': row_data['recipients'],
                'cc': row_data['cc'],
                'bcc': row_data['bcc'],
                'subject': row_data['subject'],
                'body': send_body,
                'attachments': row_data['attachment_paths']
                    if row_data['has_attachment'] else [],
                'template_class': row_data.get('template_class', ''),
                'send_status': '发送成功' if success else '发送失败',
                'send_time': send_time,
            }
            self.db_manager.save_send_record(record)

            if success:
                sent_count += 1
            else:
                fail_count += 1

            progress.setValue(i + 1)
            QApplication.processEvents()

        progress.close()

        # 刷新表格
        self.refresh_table()

        # 汇总结果
        summary = f'发送完成：成功 {sent_count} 封'
        if fail_count:
            summary += f'，失败 {fail_count} 封'
        if skip_count:
            summary += f'，跳过 {skip_count} 封'
        QMessageBox.information(self, '发送结果', summary)
