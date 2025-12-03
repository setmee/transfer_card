#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的测试数据创建脚本
"""

import sqlite3
import json
from datetime import datetime

def create_simple_test_data():
    """创建简化的测试数据"""
    conn = sqlite3.connect('transfer_card.db')
    cursor = conn.cursor()
    
    print("🚀 开始创建简化测试数据...")
    
    try:
        # 1. 创建测试部门
        cursor.execute("""
        INSERT OR IGNORE INTO departments (id, name, description) 
        VALUES (1, '研发部', '负责产品研发'),
               (2, '采购部', '负责物料采购'),
               (3, '生产部', '负责生产制造')
        """)
        
        # 2. 创建测试字段
        cursor.execute("""
        INSERT OR IGNORE INTO fields (name, display_name, field_type, department_name, is_required, is_placeholder) 
        VALUES 
            ('field_001', '物料名称', 'text', '采购部', 1, 0),
            ('field_002', '物料编码', 'text', '采购部', 1, 0),
            ('field_003', '数量', 'number', '生产部', 1, 0),
            ('field_004', '生产日期', 'date', '生产部', 0, 0),
            ('field_005', '质检结果', 'select', '生产部', 0, 0)
        """)
        
        # 3. 创建测试模板
        cursor.execute("""
        INSERT OR IGNORE INTO templates (id, template_name, template_description, is_active, created_by, created_at) 
        VALUES (1, '生产流转卡', '用于生产过程管理的流转卡', 1, 1, ?)
        """, (datetime.now(),))
        
        # 4. 创建模板字段关联
        cursor.execute("""
        INSERT OR IGNORE INTO template_fields (template_id, field_name, field_order, is_required) 
        VALUES 
            (1, 'field_001', 1, 1),
            (1, 'field_002', 2, 1),
            (1, 'field_003', 3, 1),
            (1, 'field_004', 4, 0),
            (1, 'field_005', 5, 0)
        """)
        
        # 5. 创建测试流转卡
        cursor.execute("""
        INSERT OR IGNORE INTO template_cards (id, template_id, card_number, title, description, row_count, responsible_person, create_date, status, created_by, created_at) 
        VALUES (1, 1, 'TC20251201001', '测试生产流转卡', '这是一个用于测试的流转卡', 3, '测试用户', ?, 'draft', 1, ?)
        """, (datetime.now().date(), datetime.now()))
        
        # 6. 创建流转卡数据
        card_data = [
            # 第1行数据
            (1, 1, 'field_001', '原材料A'),
            (1, 1, 'field_002', 'MAT001'),
            (1, 1, 'field_003', 100),
            (1, 1, 'field_004', datetime.now().date()),
            (1, 1, 'field_005', '合格'),
            
            # 第2行数据
            (1, 2, 'field_001', '原材料B'),
            (1, 2, 'field_002', 'MAT002'),
            (1, 2, 'field_003', 200),
            (1, 2, 'field_004', datetime.now().date()),
            (1, 2, 'field_005', '合格'),
            
            # 第3行数据
            (1, 3, 'field_001', '原材料C'),
            (1, 3, 'field_002', 'MAT003'),
            (1, 3, 'field_003', 150),
            (1, 3, 'field_004', datetime.now().date()),
            (1, 3, 'field_005', '待检')
        ]
        
        cursor.executemany("""
        INSERT OR IGNORE INTO card_data (card_id, row_number, field_name, field_value) 
        VALUES (?, ?, ?, ?)
        """, card_data)
        
        conn.commit()
        print("✅ 测试数据创建完成！")
        print("\n📋 测试信息:")
        print("流转卡号: TC20251201001")
        print("包含字段: 物料名称、物料编码、数量、生产日期、质检结果")
        print("数据行数: 3行")
        print("\n🔧 测试步骤:")
        print("1. 启动后端服务")
        print("2. 启动前端服务")
        print("3. 登录系统")
        print("4. 进入 '流转卡管理' 页面")
        print("5. 找到流转卡 'TC20251201001'")
        print("6. 点击 '填写数据' 按钮")
        print("7. 应该可以看到可编辑的输入框")
        
    except Exception as e:
        print(f"❌ 创建测试数据失败: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    create_simple_test_data()
