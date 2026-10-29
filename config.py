# -*- coding: utf-8 -*-
"""全局配置常量"""

import os
import sys

# 基础目录（兼容 PyInstaller 打包后的路径）
# BASE_DIR: 用户数据目录（数据库文件放在 exe 同级目录）
# RESOURCE_DIR: 打包资源目录（图标等 --add-data 打包的文件在 _MEIPASS 临时目录）
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
    RESOURCE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = BASE_DIR

# 数据库文件路径（放在项目根目录 / exe 同级目录）
DB_PATH = os.path.join(BASE_DIR, 'mailsendhelper.db')

# 图标路径（打包资源）
ICON_PATH = os.path.join(RESOURCE_DIR, 'assets', 'icon.png')

# 勾选框对钩图标路径（打包资源）
CHECKMARK_PATH = os.path.join(RESOURCE_DIR, 'assets', 'checkmark.png')

# 默认 SMTP 服务器（腾讯企业邮箱）
DEFAULT_SMTP_SERVER = 'smtp.exmail.qq.com'
DEFAULT_SMTP_PORT = 465
DEFAULT_USE_SSL = True

# 应用信息
APP_NAME = '邮件发送助手'
APP_VERSION = 'V2026.08.06'
