# -*- coding: utf-8 -*-
"""邮件发送服务模块"""

import smtplib
import ssl
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.header import Header


def _parse_addresses(raw):
    """将逗号/分号分隔的地址字符串解析为列表"""
    if not raw:
        return []
    parts = raw.replace(';', ',').split(',')
    result = []
    for p in parts:
        p = p.strip()
        if p:
            result.append(p)
    return result


def test_smtp_connection(email_address, smtp_server, smtp_port,
                         password, use_ssl, timeout=15):
    """测试 SMTP 连接是否正常

    Returns:
        (success: bool, message: str)
    """
    if not email_address:
        return False, '发件人邮箱地址不能为空'
    if not smtp_server:
        return False, 'SMTP服务器地址不能为空'
    if not password:
        return False, '邮箱密码不能为空'

    try:
        if use_ssl:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(smtp_server, smtp_port,
                                     timeout=timeout, context=context)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=timeout)
            server.starttls()
        try:
            server.login(email_address, password)
            return True, '连接成功，账户验证通过'
        finally:
            server.quit()
    except smtplib.SMTPAuthenticationError:
        return False, '认证失败：邮箱地址或密码错误'
    except smtplib.SMTPConnectError:
        return False, f'连接失败：无法连接到 {smtp_server}:{smtp_port}'
    except smtplib.SMTPServerDisconnected:
        return False, f'连接断开：服务器 {smtp_server} 拒绝连接'
    except TimeoutError:
        return False, f'连接超时：请检查网络或服务器地址 {smtp_server}'
    except Exception as e:
        return False, f'连接异常：{e}'


def send_email(sender_config, email_data):
    """发送邮件

    Args:
        sender_config: dict with email_address, smtp_server, smtp_port,
                       password, use_ssl
        email_data: dict with recipients, cc, bcc, subject, body,
                    attachment_paths (list of file paths)

    Returns:
        (success: bool, message: str)
    """
    email_addr = sender_config['email_address']
    smtp_server = sender_config['smtp_server']
    smtp_port = sender_config.get('smtp_port', 465)
    password = sender_config.get('password', '')
    use_ssl = sender_config.get('use_ssl', 1)

    recipients = _parse_addresses(email_data.get('recipients', ''))
    cc_list = _parse_addresses(email_data.get('cc', ''))
    bcc_list = _parse_addresses(email_data.get('bcc', ''))

    if not recipients:
        return False, '收件人不能为空'

    # 构建 MIME 邮件
    msg = MIMEMultipart()
    msg['From'] = email_addr
    msg['To'] = ', '.join(recipients)
    if cc_list:
        msg['Cc'] = ', '.join(cc_list)
    msg['Subject'] = email_data.get('subject', '(无主题)')

    # HTML 正文
    body = email_data.get('body', '')
    if body:
        msg.attach(MIMEText(body, 'html', 'utf-8'))
    else:
        msg.attach(MIMEText('', 'html', 'utf-8'))

    # 附件
    attachment_paths = email_data.get('attachment_paths', [])
    for filepath in attachment_paths:
        if not filepath or not os.path.isfile(filepath):
            return False, f'附件文件不存在: {filepath}'
        try:
            with open(filepath, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                filename = os.path.basename(filepath)
                #part.add_header('Content-Disposition','attachment',filename=('utf-8', '', filename))
                part.add_header('Content-Disposition','attachment',filename=Header(filename, 'utf-8').encode())
                msg.attach(part)
        except Exception as e:
            return False, f'读取附件失败 [{filepath}]: {e}'

    # 发送
    try:
        all_recipients = recipients + cc_list + bcc_list
        if use_ssl:
            context = ssl.create_default_context()
            server = smtplib.SMTP_SSL(smtp_server, smtp_port,
                                      timeout=30, context=context)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
            server.starttls()
        try:
            server.login(email_addr, password)
            server.sendmail(email_addr, all_recipients, msg.as_string())
            return True, '发送成功'
        finally:
            server.quit()
    except smtplib.SMTPAuthenticationError:
        return False, '认证失败：邮箱地址或密码错误'
    except smtplib.SMTPRecipientsRefused as e:
        refused = ', '.join(e.recipients.keys())
        return False, f'收件人被拒绝: {refused}'
    except smtplib.SMTPException as e:
        return False, f'SMTP错误: {e}'
    except Exception as e:
        return False, f'发送异常: {e}'
