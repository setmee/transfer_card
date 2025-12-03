#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库中的所有字段（包括预留字段）
"""

import pymysql
from app_fixed import load_config

def check_all_fields():
    config = load_config()
    connection = pymysql.connect(**config)
    cursor = connection.cursor(pymysql.cursors.DictCursor)

    cursor.execute('SELECT name, display_name, is_placeholder, field_position FROM fields ORDER BY field_position')
    fields = cursor.fetchall()
    print('📋 所有字段:')
    for field in fields:
        placeholder = '预留' if field['is_placeholder'] else '业务'
        print(f'  - {field["name"]} -> {field["display_name"]} ({placeholder}, position: {field["field_position"]})')

    # 统计预留字段数量
    placeholder_count = sum(1 for f in fields if f['is_placeholder'])
    active_count = sum(1 for f in fields if not f['is_placeholder'])
    print(f'\n📊 统计: 业务字段 {active_count} 个，预留字段 {placeholder_count} 个，总计 {len(fields)} 个')

    connection.close()

if __name__ == "__main__":
    check_all_fields()
