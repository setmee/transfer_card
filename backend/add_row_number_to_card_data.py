#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为card_data表添加row_number字段
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

def add_row_number_field():
    """为card_data表添加row_number字段"""
    db_config = load_config()
    if not db_config:
        return
    
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()
    
    try:
        print("🔍 检查card_data表是否已有row_number字段...")
        
        # 检查字段是否已存在
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE() 
            AND TABLE_NAME = 'card_data' 
            AND COLUMN_NAME = 'row_num'
        """)
        
        if cursor.fetchone():
            print("✅ row_number字段已存在，跳过添加")
            return
        
        print("🔧 添加row_number字段到card_data表...")
        
        # 添加row_num字段（避免使用保留关键字row_number）
        cursor.execute("""
            ALTER TABLE card_data 
            ADD COLUMN row_num INT NOT NULL DEFAULT 1 COMMENT '行号' AFTER card_id
        """)
        
        # 添加唯一索引
        cursor.execute("""
            ALTER TABLE card_data 
            ADD UNIQUE KEY uk_card_row (card_id, row_num)
        """)
        
        print("✅ row_num字段添加成功")
        
        # 为现有数据创建多行记录
        print("🔧 为现有流转卡创建多行数据...")
        
        # 获取所有流转卡
        cursor.execute("SELECT id FROM transfer_cards")
        cards = cursor.fetchall()
        
        for card in cards:
            card_id = card['id']
            
            # 检查该流转卡有多少行
            cursor.execute("""
                SELECT COUNT(*) as row_count 
                FROM card_data_rows 
                WHERE card_id = %s
            """, (card_id,))
            
            result = cursor.fetchone()
            row_count = result['row_count'] if result else 1
            
            # 获取现有的card_data记录
            cursor.execute("""
                SELECT * FROM card_data 
                WHERE card_id = %s
            """, (card_id,))
            
            existing_records = cursor.fetchall()
            
            if existing_records and len(existing_records) == 1:
                # 如果只有一条记录，需要复制到多行
                original_record = existing_records[0]
                
                # 删除原有记录
                cursor.execute("""
                    DELETE FROM card_data 
                    WHERE card_id = %s
                """, (card_id,))
                
                # 为每一行创建记录
                for row_num in range(1, row_count + 1):
                    # 构建插入语句
                    field_names = ['card_id', 'row_number']
                    field_values = [card_id, row_num]
                    placeholders = ['%s', '%s']
                    
                    # 添加所有字段（除了id和时间戳）
                    for i in range(1, 51):
                        field_name = f'field_{i:02d}'
                        if field_name in original_record:
                            field_names.append(field_name)
                            field_values.append(original_record[field_name])
                            placeholders.append('%s')
                    
                    # 添加时间戳
                    field_names.extend(['created_at', 'updated_at'])
                    field_values.extend(['NOW()', 'NOW()'])
                    placeholders.extend(['NOW()', 'NOW()'])
                    
                    insert_sql = f"""
                        INSERT INTO card_data ({', '.join(field_names)})
                        VALUES ({', '.join(placeholders)})
                    """
                    
                    cursor.execute(insert_sql, field_values)
                
                print(f"  ✅ 流转卡 {card_id}: 创建了 {row_count} 行数据")
        
        # 提交所有更改
        connection.commit()
        print("✅ 数据库结构更新完成！")
        
    except Exception as e:
        connection.rollback()
        print(f"❌ 更新失败: {e}")
        import traceback
        print(f"❌ 错误堆栈: {traceback.format_exc()}")
    
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    add_row_number_field()
