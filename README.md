# MailSendHelper - 邮件发送助手

基于 Python3 + PyQt5 + SQLite 开发的邮件发送管理工具，支持邮件模板管理、模板分类筛选、日期宏替换、富文本编辑、附件检查、批量发送、发送记录清除、邮件签名等功能。

## 功能概览

### 模板管理
- **CRUD 操作**：新增 / 编辑 / 复制 / 删除模板，启用 / 停用切换
- **富文本编辑器**：字体、字号、加粗、斜体、下划线、颜色、对齐方式
- **模板分类**：必填项（默认"未分类"），支持按分类多选筛选
- **日期宏**：主题、正文、附件路径均支持日期宏自动替换
- **附件管理**：手动输入附件路径（支持日期宏），添加 / 修改 / 删除 / 清空
- **只读浏览**：双击列表行查看模板内容（未发送展示替换日期宏后的模板内容，已发送展示发送记录内容）
- **停用标灰**：停用模板整行标灰并排序靠后

### 邮件发送
- **发送列表**：按日期查看发送列表，支持按模板分类（多选）/ 模板名称 / 收件人 / 主题模糊查询
- **检查附件**：扫描所有待发送邮件的附件就绪状态，缺少附件时标红提示
- **批量发送**：勾选邮件后批量发送，实时进度显示，发送前自动校验 SMTP 连接
- **发送状态着色**：未发送（浅灰）/ 发送失败（浅红）/ 发送成功（浅绿）整行区分
- **智能排序**：发送状态优先 → 发送时间倒序 → 模板更新时间倒序
- **发送成功不可重发**：发送成功的记录可勾选但发送时自动跳过
- **发送失败重发查询最新模板**：发送失败的邮件重新发送时，自动从数据库查询最新模板数据（收件人/正文/附件等）
- **清除记录**：勾选已发送（成功/失败）的记录后可批量清除程序中的发送记录（不会撤回实际邮件）
- **列头全选**：点击勾选列列头实现全选 / 取消全选
- **双击浏览**：双击列表行以只读方式查看邮件内容

### 参数设置
- **SMTP 配置**：发件人邮箱、SMTP 服务器 / 端口 / SSL，内置连接测试
- **邮件签名**：富文本签名编辑器，启用签名后每封邮件正文末尾自动附加签名
- **标题联动**：保存参数后主窗口标题实时显示发件人邮箱地址

### 其他
- **全局中文化**：所有按钮、弹窗、右键菜单均为中文
- **全局样式**：统一 QSS 样式表管理，蓝色主题
- **窗口标题**：格式为"邮件发送助手 - 发件人邮箱"，邮箱为空时不追加
- **关于弹窗**：显示应用图标、名称、版本号
- **代码签名**：打包后自动使用自签名证书签名，减少杀毒软件误报

## 项目结构

```
MailSendHelper/
├── main.py                  # 应用入口（全局字体、中文化、样式加载）
├── config.py                # 全局配置常量（APP_NAME/APP_VERSION/路径）
├── styles.py                # 全局 QSS 样式表
├── qt_utils.py              # Qt UI 中文化工具（事件过滤器翻译按钮/右键菜单）
├── db_manager.py            # 数据库管理（SQLite，三张表 CRUD + 迁移）
├── email_sender.py          # SMTP 邮件发送服务（含连接测试）
├── date_macro.py            # 日期宏替换工具
├── build.bat                # PyInstaller 打包 + 数字签名脚本
├── requirements.txt         # 依赖列表
├── mailsendhelper.db        # SQLite 数据库文件（运行后自动生成）
├── assets/
│   ├── icon.png             # 应用图标
│   ├── icon.ico             # 打包用图标
│   └── checkmark.png        # 复选框对钩图标
├── certs/
│   ├── gen_cert.py          # 自签名证书生成脚本（Python）
│   ├── gen_cert.ps1         # 证书安装脚本（PowerShell，需管理员）
│   ├── MailSendHelper.pfx   # 自签名 PFX 证书（密码 mail123）
│   └── MailSendHelper.cer   # 公钥证书（安装到受信任根）
├── ui/
│   ├── __init__.py
│   ├── main_window.py       # 主窗口（Tab管理、菜单栏、状态栏、窗口标题）
│   ├── settings_dialog.py   # 参数设置弹窗（SMTP配置 + 签名设置）
│   ├── template_tab.py      # 模板设置页面（CRUD + 富文本编辑器 + 附件管理）
│   ├── send_tab.py          # 邮件发送页面（发送列表 + 检查 + 发送 + 清除记录）
│   └── widgets.py           # 自定义控件（CheckableComboBox 多选下拉框）
├── generate_icon.py         # 图标生成脚本
├── gen_checkmark.py         # 对钩图标生成脚本
└── README.md
```

## 数据库表结构

### sender_config（发件人参数信息表）

| 字段                | 类型    | 说明                         |
|---------------------|---------|------------------------------|
| id                  | INTEGER | 主键，自增                   |
| email_address       | TEXT    | 发件人邮箱地址               |
| smtp_server         | TEXT    | SMTP 服务器地址              |
| smtp_port           | INTEGER | SMTP 端口（默认 465）        |
| password            | TEXT    | 邮箱密码/授权码              |
| use_ssl             | INTEGER | 是否使用 SSL（1/0）          |
| signature_enabled   | INTEGER | 是否启用签名（1/0，默认 1）  |
| signature_content   | TEXT    | 签名内容（HTML 富文本）      |
| updated_at          | TEXT    | 更新时间                     |

### mail_template（邮件模板信息表）

| 字段              | 类型 | 说明                                      |
|-------------------|------|-------------------------------------------|
| template_name     | TEXT | 模板名称（主键）                          |
| recipients        | TEXT | 收件人（逗号/分号分隔）                   |
| cc                | TEXT | 抄送人                                    |
| bcc               | TEXT | 暗送人                                    |
| subject           | TEXT | 主题（支持日期宏）                        |
| body              | TEXT | 正文 HTML（支持日期宏，富文本格式）       |
| has_attachment    | INTEGER | 是否包含附件（1/0）                    |
| attachment_paths  | TEXT | 附件路径 JSON 数组（支持日期宏）          |
| template_class    | TEXT | 模板分类（必填，默认"未分类"）            |
| status            | INTEGER | 启用/停用（1/0），新增默认 1           |
| created_at        | TEXT | 创建时间                                  |
| updated_at        | TEXT | 更新时间                                  |

### mail_send_record（邮件发送记录表）

| 字段            | 类型 | 说明                                          |
|-----------------|------|-----------------------------------------------|
| id              | INTEGER | 主键，自增                                 |
| template_name   | TEXT | 模板名称                                      |
| send_date       | TEXT | 发送日期（yyyy-MM-dd）                        |
| recipients      | TEXT | 收件人                                        |
| cc              | TEXT | 抄送人                                        |
| bcc             | TEXT | 暗送人                                        |
| subject         | TEXT | 主题                                          |
| body            | TEXT | 正文 HTML（含签名）                           |
| attachments     | TEXT | 附件路径 JSON 数组                            |
| template_class  | TEXT | 模板分类                                      |
| send_status     | TEXT | 发送状态（发送成功/发送失败/未发送）          |
| send_time       | TEXT | 发送时间（yyyy-MM-dd HH:mm）                  |

> **数据库迁移**：启动时自动检测并追加缺失的列（signature_enabled、signature_content、template_class），兼容旧版本数据库。历史空分类自动更新为"未分类"。

## 快速开始

### 1. 环境要求

- Python 3.x（推荐 3.8+）
- pip

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 生成图标

```bash
python generate_icon.py
python gen_checkmark.py
```

### 4. 运行程序

```bash
python main.py
```

> 数据库文件 `mailsendhelper.db` 会在首次运行时自动创建在项目根目录。

## 使用说明

### 参数设置
1. 点击右上角"参数设置"按钮
2. 填写发件人邮箱地址、SMTP 服务器（留空默认 `smtp.exmail.qq.com`）、端口、密码
3. 在"签名设置"区编辑签名内容（富文本），勾选"启用签名"
4. 点击"测试连接"验证账户是否可用
5. 点击"保存"，主窗口标题将自动显示发件人邮箱地址

### 模板设置
1. 通过顶部"菜单 → 模板设置"打开模板管理页
2. 点击"新增模板"填写模板信息：
   - 模板名称（必填，唯一）、模板分类（必填，默认"未分类"）
   - 收件人、抄送人、暗送人、主题（必填）
   - 正文支持富文本编辑（字体/字号/加粗/斜体/下划线/颜色/对齐）
   - 勾选"包含附件"后可添加/修改/删除附件路径（支持日期宏）
3. 主题、正文、附件路径均可使用日期宏（如 `报告_yyyyMMdd.pdf`）
4. 支持"复制模板"（带出全部内容，模板名称留空）
5. 双击列表行可直接编辑模板
6. 查询区支持模板分类多选筛选、模板名称/收件人/主题模糊查询、状态筛选
7. 停用模板整行标灰并排序靠后

### 邮件发送
1. 启动时默认进入"邮件发送"页面
2. 选择日期，可按模板分类（多选）/ 模板名称 / 收件人 / 主题模糊查询
3. 点击"检查附件"扫描所有待发送邮件的附件就绪状态
4. 勾选要发送的邮件（点击勾选列列头可全选/取消全选）
5. 点击"发送"，系统自动校验发件人账户，确认后逐一发送并显示进度
6. 发送成功的记录会自动跳过（不可重发），发送失败的可重新发送
7. 发送失败重发时自动查询最新模板数据
8. 勾选已发送（成功/失败）的记录后点击"清除记录"可删除程序中的发送记录
9. 双击列表行可只读浏览邮件内容
10. 列表按发送状态着色：未发送（浅灰）/ 发送失败（浅红）/ 发送成功（浅绿）

## 打包为 EXE（含数字签名）

### 1. 生成自签名证书

```bash
cd certs
python gen_cert.py
```

生成 `MailSendHelper.pfx`（密码 `mail123`）和 `MailSendHelper.cer`。

### 2. 安装证书到受信任根（需管理员权限）

以管理员身份运行 PowerShell：

```powershell
cd certs
.\gen_cert.ps1
```

或手动操作：双击 `MailSendHelper.cer` → 安装证书 → 存储位置选"本地计算机" → 浏览 → 选择"受信任的根证书颁发机构" → 完成。

### 3. 打包并签名

```bash
build.bat
```

`build.bat` 会自动执行：
1. PyInstaller 打包（`--windowed` 无控制台窗口，含图标和资源）
2. 检测 PFX 证书，使用 PowerShell `Set-AuthenticodeSignature` 对 exe 进行数字签名
3. 添加 DigiCert 时间戳

> **注意**：打包后 `mailsendhelper.db` 数据库文件会生成在 exe 同级目录。

### 手动打包命令

如果不使用 `build.bat`，可手动执行：

```bash
# 安装 PyInstaller
pip install pyinstaller

# 打包
pyinstaller --noconfirm --noupx --windowed ^
  --name "MailSendHelper" ^
  --add-data "assets;assets" ^
  --icon "assets\icon.ico" ^
  main.py

# 签名（需先生成证书）
powershell -Command "$cert = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2('certs\MailSendHelper.pfx', 'mail123'); Set-AuthenticodeSignature -FilePath 'dist\MailSendHelper.exe' -Certificate $cert -TimestampServer 'http://timestamp.digicert.com'"
```

> Linux/macOS 请将 `^` 换行符替换为 `\`，`--add-data` 分隔符改为 `:`。

## 日期宏说明

| 宏                  | 示例输出         |
|---------------------|-----------------|
| `yyyyMMddHHmmss`   | 20260730090800  |
| `yyyyMMdd`          | 20260730        |
| `yyyy-MM-dd`        | 2026-07-30      |
| `yyyy.MM.dd`        | 2026.07.30      |
| `yyyy年MM月dd日`    | 2026年07月30日   |
| `yyyy年MM月`        | 2026年07月       |
| `yyyyMM`            | 202607          |
| `MMdd`              | 0730            |

> 同时支持大写宏变体（如 `YYYYMMDD`、`YYYY-MM-DD`、`YYYY年MM月DD日` 等），效果相同。

在主题、正文、附件路径、签名内容中使用这些宏，发送时会根据所选日期自动替换。

## 技术说明

- **路径分离设计**：`BASE_DIR`（exe 目录，存放数据库）与 `RESOURCE_DIR`（`sys._MEIPASS`，存放打包资源）分离，确保打包后数据库可读写、图标可加载
- **多选下拉框**：自定义 `CheckableComboBox` 控件，点击整个框体弹出下拉，支持多选不关闭 popup
- **字体下拉框**：`QFontComboBox` 通过事件过滤器实现点击整个框体弹出下拉
- **中文化**：通过 `ChineseUiFilter` 全局事件过滤器翻译 QMessageBox 按钮和 QLineEdit 右键菜单
- **全局样式**：`styles.py` 统一管理 QSS，使用 `__CHECKMARK_URL__` 占位符避免 f-string 花括号冲突
