#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def load_config():
    try:
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            db_config = config['database']
            db_config['cursorclass'] = pymysql.cursors.DictCursor
            return db_config
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'transfer_card_system'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }

def check_template_fields():
    """检查模板字段配置"""
    try:
        config = load_config()
        connection = pymysql.connect(**config)

        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 查询模板ID=17的信息
            cursor.execute('SELECT * FROM templates WHERE id = 17')
            template = cursor.fetchone()
            
            if template:
                print('=== 模板信息 ===')
                print(f'ID: {template["id"]}')
                print(f'名称: {template["template_name"]}')
                print(f'描述: {template["template_description"]}')
                
                # 查询模板关联的字段
                cursor.execute('''
                    SELECT tf.*, f.name, f.display_name, f.field_type, f.field_position
                    FROM template_fields tf
                    LEFT JOIN fields f ON tf.field_id = f.id
                    WHERE tf.template_id = 17
                    ORDER BY tf.field_order
                ''')
                template_fields = cursor.fetchall()
                
                print(f'\n=== 模板关联字段 ({len(template_fields)}个) ===')
                for field in template_fields:
                    print(f'排序: {field["field_order"]}, 字段名: {field["field_name"]}, 显示名: {field["field_display_name"]}, 类型: {field["field_type"]}')
                
                # 如果没有关联字段，查看所有可用字段
                if not template_fields:
                    cursor.execute('''
                        SELECT name, display_name, field_type, field_position
                        FROM fields 
                        WHERE is_placeholder = 0
                        ORDER BY field_position
                        LIMIT 10
                    ''')
                    available_fields = cursor.fetchall()
                    
                    print(f'\n=== 可用字段 (前10个) ===')
                    for field in available_fields:
                        print(f'位置: {field["field_position"]}, 字段名: {field["name"]}, 显示名: {field["display_name"]}, 类型: {field["field_type"]}')
            else:
                print('没有找到模板ID=17')

    except Exception as e:
        print(f'错误: {e}')
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == '__main__':
    check_template_fields()
