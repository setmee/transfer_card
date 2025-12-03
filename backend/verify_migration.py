#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证数据库迁移结果
"""

import pymysql
import json

def load_config():
    try:
        import os
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

def verify_migration():
    """验证迁移结果"""
    db_config = load_config()
    if not db_config:
        return
    
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()
    
    try:
        print("🔍 验证数据库迁移结果...")
        
        # 检查card_data_rows表结构
        cursor.execute('DESCRIBE card_data_rows')
        columns = cursor.fetchall()
        print('🔍 card_data_rows表结构:')
        for col in columns:
            print(f'  {col["Field"]}: {col["Type"]} ({col["Null"]}, {col["Key"]})')
        
        print()
        
        # 检查card_data表是否已删除
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'card_data'
        """)
        card_data_exists = cursor.fetchone()['count']
        
        if card_data_exists == 0:
            print('✅ card_data表已成功删除')
        else:
            print('❌ card_data表仍然存在')
        
        print()
        
        # 查看card_id=9的数据
        cursor.execute("""
            SELECT id, card_id, `row_number`, field_01_pcs_project, field_02_spec_model, status
            FROM card_data_rows 
            WHERE card_id = 9 
            ORDER BY `row_number`
        """)
        
        rows = cursor.fetchall()
        print(f'🔍 card_id=9的记录数: {len(rows)}')
        for row in rows:
            print(f'  行号{row["row_number"]}: field_01={row["field_01_pcs_project"]}, field_02={row["field_02_spec_model"]}, 状态={row["status"]}')
        
        print()
        
        # 统计总记录数
        cursor.execute('SELECT COUNT(*) as total FROM card_data_rows')
        total_rows = cursor.fetchone()['total']
        print(f'✅ card_data_rows表总记录数: {total_rows}')
        
        # 统计流转卡数量
        cursor.execute('SELECT COUNT(*) as total FROM transfer_cards')
        total_cards = cursor.fetchone()['total']
        print(f'✅ transfer_cards表总记录数: {total_cards}')
        
        print('✅ 数据库迁移验证完成！')
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        print(f"❌ 错误堆栈: {traceback.format_exc()}")
    
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    verify_migration()
