#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库表结构
"""

import pymysql
import json

# 加载配置
with open('backend/config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)
    db_config = config['database']
    db_config['cursorclass'] = pymysql.cursors.DictCursor

# 连接数据库
conn = pymysql.connect(**db_config)
cursor = conn.cursor()

# 获取所有表
cursor.execute('SHOW TABLES')
tables = cursor.fetchall()

print("=== 数据库中的所有表 ===")
for table in tables:
    table_name = table[f"Tables_in_{db_config['database']}"]
    print(f"\n表名: {table_name}")
    
    # 获取表结构
    cursor.execute(f'DESCRIBE {table_name}')
    columns = cursor.fetchall()
    print(f"  字段数: {len(columns)}")
    
    print("  字段列表:")
    for col in columns:
        print(f"    - {col['Field']}: {col['Type']} {'NULL' if col['Null'] == 'YES' else 'NOT NULL'}")

cursor.close()
conn.close()
