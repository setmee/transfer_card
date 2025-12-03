#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试模板数据
"""

import pymysql
import json
from datetime import datetime
import os

def load_config():
    """加载配置文件"""
    try:
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config['database']
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        return None

def create_test_template():
    """创建测试模板数据"""
    try:
        # 加载配置
        db_config = load_config()
        if not db_config:
            print("❌ 无法加载数据库配置")
            return None
        
        # 添加DictCursor
        db_config['cursorclass'] = pymysql.cursors.DictCursor
        
        # 连接数据库
        connection = pymysql.connect(**db_config)
        
        with connection.cursor() as cursor:
            # 检查是否已存在测试模板
            cursor.execute("SELECT id FROM templates WHERE template_name = '生产流转卡模板'")
            existing = cursor.fetchone()
            if existing:
                print(f"✅ 测试模板已存在，ID: {existing['id']}")
                return existing['id']
            
            # 创建测试模板
            cursor.execute("""
                INSERT INTO templates (template_name, template_description, created_by, created_at)
                VALUES (%s, %s, %s, NOW())
            """, ('生产流转卡模板', '用于生产过程管理的流转卡模板', 1))
            template_id = cursor.lastrowid
            
            # 为模板添加字段关联（使用实际的字段ID）
            template_fields = [
                (template_id, 52, 'field_01_pcs_project', 'PCS项目', 'text', 1),
                (template_id, 53, 'field_02_spec_model', '规格型号', 'text', 2),
                (template_id, 54, 'field_03_manufacturer', '制造商', 'text', 3),
                (template_id, 70, 'field_19_weight', '重量', 'number', 4),
                (template_id, 74, 'field_23_effective_date', '生效日期', 'date', 5)
            ]
            
            cursor.executemany("""
                INSERT INTO template_fields (template_id, field_id, field_name, field_display_name, field_type, field_order, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, template_fields)
            
            connection.commit()
            print(f"✅ 成功创建测试模板，ID: {template_id}")
            return template_id
            
    except Exception as e:
        print(f"❌ 创建测试数据失败: {e}")
        return None
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    create_test_template()
