#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
激活预留字段的示例脚本
"""

import pymysql
from app_fixed import load_config

def activate_placeholder_field(field_number, new_display_name):
    """
    激活预留字段
    
    Args:
        field_number: 字段编号（如 25）
        new_display_name: 新的显示名称
    """
    config = load_config()
    connection = pymysql.connect(**config)
    cursor = connection.cursor()
    
    field_name = f"field_{field_number:02d}"
    
    try:
        # 更新字段信息
        update_query = """
        UPDATE fields 
        SET display_name = %s, is_placeholder = 0 
        WHERE name = %s
        """
        cursor.execute(update_query, (new_display_name, field_name))
        connection.commit()
        
        print(f"✅ 成功激活字段 {field_name} -> {new_display_name}")
        
        # 验证更新
        cursor.execute("SELECT name, display_name, is_placeholder FROM fields WHERE name = %s", (field_name,))
        result = cursor.fetchone()
        if result:
            status = "业务字段" if result[2] == 0 else "预留字段"
            print(f"   验证: {result[0]} -> {result[1]} ({status})")
        
    except Exception as e:
        print(f"❌ 激活字段失败: {str(e)}")
        connection.rollback()
    finally:
        connection.close()

def show_available_placeholders():
    """显示可用的预留字段"""
    config = load_config()
    connection = pymysql.connect(**config)
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute('SELECT name, display_name, field_position FROM fields WHERE is_placeholder = 1 ORDER BY field_position')
    placeholders = cursor.fetchall()
    
    print(f"📋 可用的预留字段 ({len(placeholders)} 个):")
    for field in placeholders:
        print(f"  - {field['name']} -> {field['display_name']} (position: {field['field_position']})")
    
    connection.close()
    return placeholders

if __name__ == "__main__":
    print("=== 预留字段管理工具 ===\n")
    
    # 显示可用预留字段
    show_available_placeholders()
    
    print("\n=== 使用示例 ===")
    print("要将 field_25 激活为'新字段名称'，可以使用:")
    print("activate_placeholder_field(25, '新字段名称')")
