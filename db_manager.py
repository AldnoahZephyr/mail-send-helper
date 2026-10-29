# -*- coding: utf-8 -*-
"""数据库管理模块

三张表:
  1. sender_config   - 发件人参数信息表
  2. mail_template   - 邮件模板信息表 (template_name 为主键)
  3. mail_send_record- 邮件发送记录表
"""

import sqlite3
import json
from datetime import datetime

from config import DB_PATH


class DatabaseManager:
    """SQLite 数据库管理器"""

    def __init__(self, db_path=None):
        self.db_path = db_path or DB_PATH
        self._init_db()

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        return conn

    def _init_db(self):
        """创建所有表（如果不存在）+ 迁移新字段（兼容旧库）"""
        with self._get_conn() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS sender_config (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    email_address   TEXT NOT NULL,
                    smtp_server     TEXT NOT NULL,
                    smtp_port       INTEGER DEFAULT 465,
                    password        TEXT,
                    use_ssl         INTEGER DEFAULT 1,
                    signature_enabled  INTEGER DEFAULT 1,
                    signature_content  TEXT,
                    updated_at      TEXT
                );

                CREATE TABLE IF NOT EXISTS mail_template (
                    template_name   TEXT PRIMARY KEY,
                    recipients      TEXT,
                    cc              TEXT,
                    bcc             TEXT,
                    subject         TEXT,
                    body            TEXT,
                    has_attachment  INTEGER DEFAULT 0,
                    attachment_paths TEXT,
                    template_class  TEXT,
                    status          INTEGER DEFAULT 1,
                    created_at      TEXT,
                    updated_at      TEXT
                );

                CREATE TABLE IF NOT EXISTS mail_send_record (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_name   TEXT,
                    send_date       TEXT,
                    recipients      TEXT,
                    cc              TEXT,
                    bcc             TEXT,
                    subject         TEXT,
                    body            TEXT,
                    attachments     TEXT,
                    template_class  TEXT,
                    send_status     TEXT,
                    send_time       TEXT
                );
            ''')
            # --- 迁移：为旧库追加新列（如果不存在）---
            self._migrate_columns(conn)

    @staticmethod
    def _migrate_columns(conn):
        """安全地添加可能缺失的列（兼容旧版本数据库）"""
        migrations = [
            ('sender_config', 'signature_enabled', 'INTEGER DEFAULT 1'),
            ('sender_config', 'signature_content', 'TEXT'),
            ('mail_template', 'template_class', 'TEXT'),
            ('mail_send_record', 'template_class', 'TEXT'),
        ]
        for table, column, coldef in migrations:
            try:
                conn.execute(f'ALTER TABLE {table} ADD COLUMN {column} {coldef}')
            except sqlite3.OperationalError:
                pass  # 列已存在，跳过

        # 将历史数据中空的 template_class 统一设置为"未分类"
        conn.execute(
            "UPDATE mail_template SET template_class='未分类' "
            "WHERE template_class IS NULL OR template_class=''"
        )
        conn.execute(
            "UPDATE mail_send_record SET template_class='未分类' "
            "WHERE template_class IS NULL OR template_class=''"
        )

    # ==================================================================
    # sender_config 表操作
    # ==================================================================
    def get_sender_config(self):
        """获取发件人配置（单条记录）"""
        with self._get_conn() as conn:
            row = conn.execute(
                'SELECT * FROM sender_config ORDER BY id LIMIT 1'
            ).fetchone()
            if row:
                return dict(row)
            return None

    def save_sender_config(self, email_address, smtp_server, smtp_port,
                           password, use_ssl, signature_enabled=True,
                           signature_content=''):
        """保存或更新发件人配置"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with self._get_conn() as conn:
            existing = conn.execute(
                'SELECT id FROM sender_config ORDER BY id LIMIT 1'
            ).fetchone()
            if existing:
                conn.execute('''
                    UPDATE sender_config
                    SET email_address=?, smtp_server=?, smtp_port=?,
                        password=?, use_ssl=?, updated_at=?,
                        signature_enabled=?, signature_content=?
                    WHERE id=?
                ''', (email_address, smtp_server, smtp_port,
                      password, 1 if use_ssl else 0, now,
                      1 if signature_enabled else 0, signature_content,
                      existing['id']))
            else:
                conn.execute('''
                    INSERT INTO sender_config
                        (email_address, smtp_server, smtp_port, password,
                         use_ssl, signature_enabled, signature_content, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (email_address, smtp_server, smtp_port, password,
                      1 if use_ssl else 0,
                      1 if signature_enabled else 0, signature_content, now))
            conn.commit()

    # ==================================================================
    # mail_template 表操作
    # ==================================================================
    def get_templates(self, name_filter='', recipient_filter='',
                      subject_filter='', status_filter=None,
                      class_filter=None):
        """查询模板列表（支持模糊查询 + 模板分类筛选）"""
        sql = 'SELECT * FROM mail_template WHERE 1=1'
        params = []
        if name_filter:
            sql += ' AND template_name LIKE ?'
            params.append(f'%{name_filter}%')
        if recipient_filter:
            sql += ' AND recipients LIKE ?'
            params.append(f'%{recipient_filter}%')
        if subject_filter:
            sql += ' AND subject LIKE ?'
            params.append(f'%{subject_filter}%')
        if status_filter is not None and status_filter != '':
            sql += ' AND status = ?'
            params.append(int(status_filter))
        if class_filter:
            placeholders = ','.join(['?'] * len(class_filter))
            sql += f' AND template_class IN ({placeholders})'
            params.extend(class_filter)
        sql += ' ORDER BY status DESC, template_name'
        with self._get_conn() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

    def get_template(self, template_name):
        """获取单个模板"""
        with self._get_conn() as conn:
            row = conn.execute(
                'SELECT * FROM mail_template WHERE template_name=?',
                (template_name,)
            ).fetchone()
            return dict(row) if row else None

    def add_template(self, template):
        """新增模板

        Args:
            template: dict with keys:
                template_name, recipients, cc, bcc, subject, body,
                has_attachment, attachment_paths (list), status
        Returns:
            (success: bool, message: str)
        """
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        attachment_json = json.dumps(
            template.get('attachment_paths', []),
            ensure_ascii=False
        ) if template.get('attachment_paths') else '[]'

        with self._get_conn() as conn:
            try:
                conn.execute('''
                    INSERT INTO mail_template
                        (template_name, recipients, cc, bcc, subject, body,
                         has_attachment, attachment_paths, template_class,
                         status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    template['template_name'],
                    template.get('recipients', ''),
                    template.get('cc', ''),
                    template.get('bcc', ''),
                    template.get('subject', ''),
                    template.get('body', ''),
                    1 if template.get('has_attachment') else 0,
                    attachment_json,
                    template.get('template_class', '') or '未分类',
                    1 if template.get('status', 1) else 0,
                    now, now
                ))
                conn.commit()
                return True, '模板添加成功'
            except sqlite3.IntegrityError:
                return False, '模板名称已存在，请使用不同的名称'

    def update_template(self, original_name, template):
        """更新模板"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        attachment_json = json.dumps(
            template.get('attachment_paths', []),
            ensure_ascii=False
        ) if template.get('attachment_paths') else '[]'

        with self._get_conn() as conn:
            try:
                conn.execute('''
                    UPDATE mail_template
                    SET template_name=?, recipients=?, cc=?, bcc=?,
                        subject=?, body=?, has_attachment=?,
                        attachment_paths=?, template_class=?, status=?, updated_at=?
                    WHERE template_name=?
                ''', (
                    template['template_name'],
                    template.get('recipients', ''),
                    template.get('cc', ''),
                    template.get('bcc', ''),
                    template.get('subject', ''),
                    template.get('body', ''),
                    1 if template.get('has_attachment') else 0,
                    attachment_json,
                    template.get('template_class', '') or '未分类',
                    1 if template.get('status', 1) else 0,
                    now,
                    original_name
                ))
                conn.commit()
                return True, '模板更新成功'
            except sqlite3.IntegrityError:
                return False, '模板名称已存在，请使用不同的名称'

    def delete_template(self, template_name):
        """删除模板"""
        with self._get_conn() as conn:
            conn.execute(
                'DELETE FROM mail_template WHERE template_name=?',
                (template_name,)
            )
            conn.commit()

    def toggle_template_status(self, template_name, status):
        """切换模板启用/停用状态"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with self._get_conn() as conn:
            conn.execute(
                'UPDATE mail_template SET status=?, updated_at=? WHERE template_name=?',
                (1 if status else 0, now, template_name)
            )
            conn.commit()

    def get_enabled_templates(self):
        """获取所有启用的模板"""
        with self._get_conn() as conn:
            rows = conn.execute(
                'SELECT * FROM mail_template WHERE status=1 ORDER BY template_name'
            ).fetchall()
            return [dict(r) for r in rows]

    def get_template_classes(self):
        """获取所有不重复的模板分类（启用模板的分类靠前，停用的靠后）"""
        with self._get_conn() as conn:
            rows = conn.execute(
                'SELECT template_class, MAX(status) AS has_enabled '
                'FROM mail_template '
                'WHERE template_class IS NOT NULL AND template_class != "" '
                'GROUP BY template_class '
                'ORDER BY '
                '  CASE WHEN template_class="未分类" THEN 0 ELSE 1 END, '
                '  CASE WHEN MAX(status)=1 THEN 0 ELSE 1 END, '
                '  template_class'
            ).fetchall()
            return [r['template_class'] for r in rows]

    def get_enabled_template_classes(self):
        """获取启用模板的不重复分类（仅 show_tab 使用）"""
        with self._get_conn() as conn:
            rows = conn.execute(
                'SELECT DISTINCT template_class FROM mail_template '
                'WHERE status=1 AND template_class IS NOT NULL AND template_class != "" '
                'ORDER BY CASE WHEN template_class="未分类" THEN 0 ELSE 1 END, template_class'
            ).fetchall()
            return [r['template_class'] for r in rows]

    # ==================================================================
    # mail_send_record 表操作
    # ==================================================================
    def get_send_record(self, template_name, send_date):
        """获取指定模板和日期的发送记录"""
        with self._get_conn() as conn:
            row = conn.execute(
                '''SELECT * FROM mail_send_record
                   WHERE template_name=? AND send_date=?
                   ORDER BY id DESC LIMIT 1''',
                (template_name, send_date)
            ).fetchone()
            return dict(row) if row else None

    def get_send_records_by_date(self, send_date):
        """获取指定日期的所有发送记录"""
        with self._get_conn() as conn:
            rows = conn.execute(
                '''SELECT * FROM mail_send_record
                   WHERE send_date=? ORDER BY id''',
                (send_date,)
            ).fetchall()
            return [dict(r) for r in rows]

    def save_send_record(self, record):
        """保存发送记录（新增或更新）"""
        attachments_json = json.dumps(
            record.get('attachments', []),
            ensure_ascii=False
        ) if record.get('attachments') else '[]'

        existing = self.get_send_record(
            record['template_name'], record['send_date']
        )

        with self._get_conn() as conn:
            if existing:
                conn.execute('''
                    UPDATE mail_send_record
                    SET recipients=?, cc=?, bcc=?, subject=?, body=?,
                        attachments=?, template_class=?, send_status=?, send_time=?
                    WHERE id=?
                ''', (
                    record.get('recipients', ''),
                    record.get('cc', ''),
                    record.get('bcc', ''),
                    record.get('subject', ''),
                    record.get('body', ''),
                    attachments_json,
                    record.get('template_class', '') or '未分类',
                    record.get('send_status', ''),
                    record.get('send_time', ''),
                    existing['id']
                ))
            else:
                conn.execute('''
                    INSERT INTO mail_send_record
                        (template_name, send_date, recipients, cc, bcc,
                         subject, body, attachments, template_class,
                         send_status, send_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    record['template_name'],
                    record['send_date'],
                    record.get('recipients', ''),
                    record.get('cc', ''),
                    record.get('bcc', ''),
                    record.get('subject', ''),
                    record.get('body', ''),
                    attachments_json,
                    record.get('template_class', '') or '未分类',
                    record.get('send_status', ''),
                    record.get('send_time', '')
                ))
            conn.commit()

    def delete_send_record(self, template_name, send_date):
        """删除指定模板和日期的发送记录"""
        with self._get_conn() as conn:
            conn.execute(
                'DELETE FROM mail_send_record '
                'WHERE template_name=? AND send_date=?',
                (template_name, send_date)
            )
            conn.commit()
