#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库结构
"""

import pymysql
import json

def load_config():
    try:
        import os
        # 获取脚本所在目录
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(script_dir, 'config', 'config.json')
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            db_config = config['database']
            db_config['cursorclass'] = pymysql.cursors.DictCursor
            return db_config
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return None

def check_database():
    """检查数据库结构"""
    db_config = load_config()
    if not db_config:
        return
    
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()
    
    try:
        # 查看card_data表结构
        cursor.execute('DESCRIBE card_data')
        columns = cursor.fetchall()
        print('🔍 card_data表结构:')
        for col in columns:
            print(f'  {col["Field"]}: {col["Type"]} ({col["Null"]}, {col["Key"]})')
        
        print()
        
        # 查看card_data_rows表结构  
        cursor.execute('DESCRIBE card_data_rows')
        columns = cursor.fetchall()
        print('🔍 card_data_rows表结构:')
        for col in columns:
            print(f'  {col["Field"]}: {col["Type"]} ({col["Null"]}, {col["Key"]})')
        
        print()
        
        # 查看当前card_id=9的数据
        cursor.execute('SELECT * FROM card_data WHERE card_id = 9')
        card_data = cursor.fetchall()
        print(f'🔍 card_id=9的card_data记录数: {len(card_data)}')
        if card_data:
            print('第一条记录:')
            for key, value in card_data[0].items():
                if key not in ['created_at', 'updated_at'] and value:
                    print(f'  {key}: {value}')
        
        print()
        
        cursor.execute('SELECT * FROM card_data_rows WHERE card_id = 9 ORDER BY `row_number`')
        row_data = cursor.fetchall()
        print(f'🔍 card_id=9的card_data_rows记录数: {len(row_data)}')
        for row in row_data:
            print(f'  行号{row["row_number"]}: 状态={row["status"]}, 部门={row["department_id"]}')
    
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    check_database()
