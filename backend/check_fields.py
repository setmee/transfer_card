#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查fields表数据
"""

import pymysql
import json

def load_config():
    """加载配置文件"""
    with open('config/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
        return config['database']

def check_fields():
    """检查fields表数据"""
    try:
        db_config = load_config()
        db_config['cursorclass'] = pymysql.cursors.DictCursor
        conn = pymysql.connect(**db_config)

        with conn.cursor() as cursor:
            cursor.execute('SELECT id, name, display_name FROM fields ORDER BY id')
            fields = cursor.fetchall()
            print('Fields表中的数据:')
            for field in fields:
                print(f'ID: {field["id"]}, Name: {field["name"]}, Display: {field["display_name"]}')
            
            print(f'\n总共 {len(fields)} 个字段')

        conn.close()
    except Exception as e:
        print(f'检查失败: {e}')

if __name__ == "__main__":
    check_fields()
