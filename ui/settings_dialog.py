# -*- coding: utf-8 -*-
"""发件人参数设置对话框"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QSpinBox,
    QCheckBox, QPushButton, QHBoxLayout, QMessageBox, QLabel,
    QGroupBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from config import DEFAULT_SMTP_SERVER, DEFAULT_SMTP_PORT, DEFAULT_USE_SSL
from db_manager import DatabaseManager
from email_sender import test_smtp_connection
from ui.template_tab import RichTextEditor


class TestConnectionThread(QThread):
    """后台线程测试 SMTP 连接"""
    finished_signal = pyqtSignal(bool, str)

    def __init__(self, email_address, smtp_server, smtp_port,
                 password, use_ssl):
        super().__init__()
        self.email_address = email_address
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.password = password
        self.use_ssl = use_ssl

    def run(self):
        success, message = test_smtp_connection(
            self.email_address, self.smtp_server, self.smtp_port,
            self.password, self.use_ssl
        )
        self.finished_signal.emit(success, message)


class SettingsDialog(QDialog):
    """发件人参数设置弹窗"""

    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.test_thread = None
        self._init_ui()
        self._load_config()

    def _init_ui(self):
        self.setWindowTitle('参数设置 - 发件人配置')
        self.setMinimumWidth(620)
        self.setMinimumHeight(720)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # --- SMTP 配置区 ---
        smtp_group = QGroupBox('SMTP 服务器配置')
        smtp_form = QFormLayout(smtp_group)
        smtp_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        smtp_form.setSpacing(10)
        smtp_form.setContentsMargins(16, 24, 16, 16)

        self.email_edit = QLineEdit()
        self.email_edit.setPlaceholderText('例如：sender@company.com')
        smtp_form.addRow('邮箱地址 *：', self.email_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText('输入邮箱密码')
        smtp_form.addRow('密码 *：', self.password_edit)

        self.server_edit = QLineEdit()
        self.server_edit.setPlaceholderText(
            f'默认：{DEFAULT_SMTP_SERVER}（留空则使用默认值）'
        )
        smtp_form.addRow('SMTP服务器：', self.server_edit)

        self.port_spin = QSpinBox()
        self.port_spin.setRange(1, 65535)
        self.port_spin.setValue(DEFAULT_SMTP_PORT)
        smtp_form.addRow('SMTP端口：', self.port_spin)

        self.ssl_check = QCheckBox('使用SSL加密连接')
        self.ssl_check.setChecked(DEFAULT_USE_SSL)
        smtp_form.addRow('', self.ssl_check)

        layout.addWidget(smtp_group)

        # --- 签名设置区 ---
        sig_group = QGroupBox('签名设置')
        sig_layout = QVBoxLayout(sig_group)
        sig_layout.setContentsMargins(16, 24, 16, 16)
        sig_layout.setSpacing(10)

        # 启用签名勾选框
        self.signature_check = QCheckBox('启用签名（发送邮件时将签名附加在正文之后）')
        self.signature_check.setChecked(True)
        sig_layout.addWidget(self.signature_check)

        # 签名内容提示
        sig_hint = QLabel('请输入签名内容（支持富文本格式）：')
        sig_hint.setStyleSheet('color: #666; font-size: 9pt;')
        sig_layout.addWidget(sig_hint)

        # 富文本签名编辑器
        self.signature_edit = RichTextEditor()
        self.signature_edit.setMinimumHeight(180)
        self.signature_edit.setPlaceholderText(
            '例如：\n张三 | 财务部\n电话：xxx-xxxxxxx\n邮箱：xxx@company.com'
        )
        sig_layout.addWidget(self.signature_edit)

        layout.addWidget(sig_group, stretch=1)

        # --- 校验提示 ---
        self.hint_label = QLabel('')
        self.hint_label.setStyleSheet('color: #d32f2f; font-size: 9pt;')
        layout.addWidget(self.hint_label)

        # --- 按钮区 ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        test_btn = QPushButton('测试连接')
        test_btn.setMinimumWidth(90)
        test_btn.clicked.connect(self._on_test_connection)
        btn_layout.addWidget(test_btn)

        btn_layout.addStretch()

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

        # 实时校验邮箱格式
        self.email_edit.textChanged.connect(self._validate_email)

    def _validate_email(self, text):
        """简单的邮箱格式校验"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not text:
            self.hint_label.setText('')
            return False
        if re.match(pattern, text.strip()):
            self.hint_label.setText('')
            return True
        else:
            self.hint_label.setText('邮箱地址格式不正确')
            return False

    def _load_config(self):
        """从数据库加载已有配置"""
        config = self.db_manager.get_sender_config()
        if config:
            self.email_edit.setText(config.get('email_address', ''))
            self.server_edit.setText(config.get('smtp_server', ''))
            self.port_spin.setValue(config.get('smtp_port', DEFAULT_SMTP_PORT))
            self.ssl_check.setChecked(bool(config.get('use_ssl', 1)))
            self.password_edit.setText(config.get('password', ''))
            self.signature_check.setChecked(
                bool(config.get('signature_enabled', 1))
            )
            self.signature_edit.setHtml(
                config.get('signature_content', '') or ''
            )

    def _get_config_data(self):
        """获取界面填写的配置数据"""
        email = self.email_edit.text().strip()
        server = self.server_edit.text().strip()
        if not server:
            server = DEFAULT_SMTP_SERVER
        port = self.port_spin.value()
        password = self.password_edit.text()
        use_ssl = self.ssl_check.isChecked()
        sig_enabled = self.signature_check.isChecked()
        sig_content = self.signature_edit.toHtml()
        return email, server, port, password, use_ssl, sig_enabled, sig_content

    def _on_test_connection(self):
        """测试连接按钮"""
        email, server, port, password, use_ssl, _, _ = self._get_config_data()

        if not email:
            QMessageBox.warning(self, '提示', '请输入邮箱地址')
            return
        if not self._validate_email(email):
            QMessageBox.warning(self, '提示', '邮箱地址格式不正确')
            return
        if not password:
            QMessageBox.warning(self, '提示', '请输入密码')
            return

        # 禁用按钮，显示等待
        self._set_buttons_enabled(False)
        self.hint_label.setText('正在测试连接，请稍候...')
        self.hint_label.setStyleSheet('color: #666; font-size: 9pt;')

        # 后台线程测试
        self.test_thread = TestConnectionThread(
            email, server, port, password, use_ssl
        )
        self.test_thread.finished_signal.connect(self._on_test_finished)
        self.test_thread.start()

    def _on_test_finished(self, success, message):
        """测试完成回调"""
        self._set_buttons_enabled(True)
        if success:
            self.hint_label.setText('✓ ' + message)
            self.hint_label.setStyleSheet('color: #2e7d32; font-size: 9pt;')
            QMessageBox.information(self, '测试结果', message)
        else:
            self.hint_label.setText('✗ ' + message)
            self.hint_label.setStyleSheet('color: #d32f2f; font-size: 9pt;')
            QMessageBox.warning(self, '测试结果', message)

    def _set_buttons_enabled(self, enabled):
        """禁用/启用所有按钮"""
        for btn in self.findChildren(QPushButton):
            btn.setEnabled(enabled)

    def _on_save(self):
        """保存配置"""
        email, server, port, password, use_ssl, sig_enabled, sig_content = \
            self._get_config_data()

        if not email:
            QMessageBox.warning(self, '提示', '请输入邮箱地址')
            return
        if not self._validate_email(email):
            QMessageBox.warning(self, '提示', '邮箱地址格式不正确')
            return
        if not password:
            QMessageBox.warning(self, '提示', '请输入密码')
            return

        # 校验签名：启用时内容不能为空（纯空格也算空）
        if sig_enabled:
            # 提取纯文本检查是否为空白
            sig_plain = self.signature_edit.toPlainText().strip()
            if not sig_plain:
                QMessageBox.warning(
                    self, '提示',
                    '已勾选"启用签名"但签名内容为空，\n'
                    '请输入签名内容或取消勾选。'
                )
                self.signature_edit.setFocus()
                return

        self.db_manager.save_sender_config(
            email, server, port, password, use_ssl,
            sig_enabled, sig_content
        )
        QMessageBox.information(self, '成功', '发件人配置已保存')
        self.accept()
