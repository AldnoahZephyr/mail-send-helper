# -*- coding: utf-8 -*-
"""日期宏替换工具

支持以下日期宏（按长度从长到短依次替换，避免部分匹配）:
  yyyyMMddHHmmss -> 20260730090800
  yyyyMMdd        -> 20260730
  yyyy-MM-dd      -> 2026-07-30
  yyyy/MM/dd      -> 2026/07/30
  yyyy.MM.dd      -> 2026.07.30
  yyyyMM          -> 202607
"""

from datetime import date, datetime

# (宏模式, strftime格式)  
_PATTERNS = [
    ('yyyyMMddHHmmss', '%Y%m%d%H%M%S'),
    ('yyyy年MM月dd日', '%Y年%m月%d日'),
    ('YYYY年MM月DD日', '%Y年%m月%d日'),
    ('yyyy-MM-dd', '%Y-%m-%d'),
    ('YYYY-MM-DD', '%Y-%m-%d'),
    ('yyyyMMdd', '%Y%m%d'),
    ('YYYYMMDD', '%Y%m%d'),
    ('yyyy年MM月', '%Y年%m月'),
    ('YYYY年MM月', '%Y年%m月'),
    ('yyyyMM', '%Y%m'),
    ('YYYYMM', '%Y%m'),
    ('MMdd', '%m%d'),
    ('MMDD', '%m%d'),
    ('yyyy.MM.dd', '%Y.%m.%d'),
]


def replace_date_macros(text, target_date):
    """将文本中的日期宏替换为实际日期值

    Args:
        text: 原始文本
        target_date: datetime.date 或 datetime.datetime 对象

    Returns:
        替换后的文本；如果 text 为 None 则返回空字符串
    """
    if not text:
        return ''

    if isinstance(target_date, datetime):
        d = target_date
    elif isinstance(target_date, date):
        d = target_date
    else:
        return text

    result = text
    for macro, fmt in _PATTERNS:
        result = result.replace(macro, d.strftime(fmt))
    return result