# -*- coding: utf-8 -*-
"""主窗口 - Tab 管理 + 菜单栏 + 状态栏"""

import os
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QTabWidget, QMessageBox, QLabel, QMenu, QDialog, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QIcon

from config import APP_NAME, APP_VERSION, ICON_PATH, DEFAULT_SMTP_SERVER
from db_manager import DatabaseManager
from ui.settings_dialog import SettingsDialog
from ui.template_tab import TemplateTab
from ui.send_tab import SendTab


class AboutDialog(QDialog):
    """关于对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('关于')
        self.setFixedSize(380, 340)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(30, 30, 30, 30)

        # 图标
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        if os.path.isfile(ICON_PATH):
            pix = QPixmap(ICON_PATH)
            icon_label.setPixmap(
                pix.scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        layout.addWidget(icon_label)

        # 应用名称
        name_label = QLabel(APP_NAME)
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setStyleSheet(
            'font-size: 16pt; font-weight: bold; color: #1a73e8;'
        )
        layout.addWidget(name_label)

        # 版本号
        ver_label = QLabel(f'版本：{APP_VERSION}')
        ver_label.setAlignment(Qt.AlignCenter)
        ver_label.setStyleSheet('font-size: 11pt; color: #5f6368;')
        layout.addWidget(ver_label)

        # 分割线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet('color: #e0e0e0;')
        layout.addWidget(line)

        # 描述
        desc = QLabel(
            '一款简单实用的邮件发送助手\n'
            '支持模板管理、日期宏、富文本和附件'
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet('font-size: 10pt; color: #80868b;')
        layout.addWidget(desc)

        layout.addStretch()

        # 确定按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton('确定')
        ok_btn.setMinimumWidth(80)
        ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(ok_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self._open_tabs = {}  # tab_key -> widget
        self._init_ui()
        # self._init_tray()  # 系统托盘功能已注释
        # 默认打开邮件发送Tab
        self._open_tab('send')

    def _init_ui(self):
        self._update_window_title()
        self.setMinimumSize(1280, 791)

        # 设置窗口图标
        try:
            if os.path.isfile(ICON_PATH):
                self.setWindowIcon(QIcon(ICON_PATH))
        except Exception:
            pass

        central = QWidget()
        central.setObjectName('central')
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- 顶部导航栏 ---
        top_bar = QWidget()
        top_bar.setObjectName('top_bar')
        top_bar.setFixedHeight(46)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(12, 0, 12, 0)
        top_layout.setSpacing(4)

        # 菜单按钮（下拉选择子菜单）
        menu_btn = QPushButton('  菜单  ')
        menu_btn.setObjectName('menu_btn')
        menu_menu = QMenu(menu_btn)
        menu_menu.addAction('邮件发送', lambda: self._open_tab('send'))
        menu_menu.addAction('模板设置', lambda: self._open_tab('template'))
        menu_btn.setMenu(menu_menu)
        top_layout.addWidget(menu_btn)

        # 关于按钮（直接放在菜单右侧）
        about_btn = QPushButton('关于')
        about_btn.setObjectName('about_btn')
        about_btn.clicked.connect(self._on_about)
        top_layout.addWidget(about_btn)

        top_layout.addStretch()

        # 参数设置按钮
        settings_btn = QPushButton('⚙  参数设置')
        settings_btn.setObjectName('settings_btn')
        settings_btn.clicked.connect(self._on_settings)
        top_layout.addWidget(settings_btn)

        main_layout.addWidget(top_bar)

        # --- Tab 区域 ---
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self._on_close_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        main_layout.addWidget(self.tab_widget, stretch=1)

        self.setCentralWidget(central)

        # --- 状态栏 ---
        self.statusBar().setStyleSheet(
            'QStatusBar { background-color: #ffffff; '
            'border-top: 1px solid #e8eaed; color: #999; font-size: 9pt; }'
        )
        version_label = QLabel(f'  {APP_VERSION}  ')
        version_label.setStyleSheet('color: #999; font-size: 9pt;')
        self.statusBar().addPermanentWidget(version_label)

    def _update_window_title(self):
        """根据发件人配置更新窗口标题：APP_NAME 或 APP_NAME - 邮箱地址"""
        config = self.db_manager.get_sender_config()
        email = config.get('email_address', '') if config else ''
        if email:
            self.setWindowTitle(f'{APP_NAME} - {email}')
        else:
            self.setWindowTitle(f'{APP_NAME}')

    # ==================== 系统托盘功能（已注释） ====================
    # def _init_tray(self):
    #     """初始化系统托盘"""
    #     self.tray_icon = QSystemTrayIcon(self)
    #     if os.path.isfile(ICON_PATH):
    #         self.tray_icon.setIcon(QIcon(ICON_PATH))
    #     self.tray_icon.setToolTip(APP_NAME)
    #
    #     # 托盘右键菜单
    #     tray_menu = QMenu()
    #     show_action = QAction('显示主窗口', self)
    #     show_action.triggered.connect(self._show_from_tray)
    #     tray_menu.addAction(show_action)
    #
    #     tray_menu.addSeparator()
    #
    #     quit_action = QAction('退出程序', self)
    #     quit_action.triggered.connect(self._quit_from_tray)
    #     tray_menu.addAction(quit_action)
    #
    #     self.tray_icon.setContextMenu(tray_menu)
    #
    #     # 双击托盘图标显示窗口
    #     self.tray_icon.activated.connect(
    #         lambda reason: self._show_from_tray()
    #         if reason == QSystemTrayIcon.DoubleClick
    #         else None
    #     )
    #
    #     self.tray_icon.show()
    #
    # def _show_from_tray(self):
    #     """从托盘恢复显示"""
    #     self.show()
    #     self.setWindowState(
    #         self.windowState() & ~Qt.WindowMinimized
    #     )
    #     self.raise_()
    #     self.activateWindow()
    #
    # def _quit_from_tray(self):
    #     """从托盘菜单退出"""
    #     self._force_quit = True
    #     self.tray_icon.hide()
    #     self.close()
    # ==================== 系统托盘功能结束 ====================

    def _open_tab(self, tab_key):
        """打开或切换到指定Tab"""
        if tab_key in self._open_tabs:
            widget = self._open_tabs[tab_key]
            idx = self.tab_widget.indexOf(widget)
            if idx >= 0:
                self.tab_widget.setCurrentIndex(idx)
            return

        if tab_key == 'template':
            widget = TemplateTab(self.db_manager)
            widget.template_changed.connect(self._on_template_changed)
            title = '模板设置'
        elif tab_key == 'send':
            widget = SendTab(self.db_manager)
            title = '邮件发送'
        else:
            return

        self._open_tabs[tab_key] = widget
        idx = self.tab_widget.addTab(widget, title)
        self.tab_widget.setCurrentIndex(idx)

    def _on_close_tab(self, index):
        """关闭Tab"""
        widget = self.tab_widget.widget(index)
        self.tab_widget.removeTab(index)
        for key, w in list(self._open_tabs.items()):
            if w == widget:
                del self._open_tabs[key]
                break

    def _on_tab_changed(self, index):
        """Tab切换时刷新发送Tab数据"""
        widget = self.tab_widget.widget(index)
        if widget and isinstance(widget, SendTab):
            widget.refresh_table()

    def _on_settings(self):
        """打开参数设置对话框"""
        dialog = SettingsDialog(self.db_manager, parent=self)
        dialog.exec_()
        # 参数设置保存后更新窗口标题（发件人邮箱可能变更）
        self._update_window_title()

    def _on_about(self):
        """打开关于对话框"""
        dialog = AboutDialog(parent=self)
        dialog.exec_()

    def _on_template_changed(self):
        """模板变更时刷新发送Tab"""
        send_tab = self._open_tabs.get('send')
        if send_tab:
            send_tab._refresh_class_options()
            send_tab.refresh_table()

    def closeEvent(self, event):
        """关闭窗口事件 - 确认是否退出"""
        reply = QMessageBox.question(
            self, '退出确认',
            f'确定要退出 {APP_NAME} 吗？',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

    # ==================== 窗口状态变化（已注释） ====================
    # def changeEvent(self, event):
    #     """窗口状态变化 - 最小化时隐藏到托盘"""
    #     if event.type() == QEvent.WindowStateChange:
    #         if self.windowState() & Qt.WindowMinimized:
    #             # 不自动隐藏，让用户通过关闭按钮选择
    #             pass
    #     super().changeEvent(event)
