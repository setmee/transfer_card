#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移：将card_data表的所有字段合并到card_data_rows表中
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

def migrate_to_single_table():
    """将card_data表迁移到card_data_rows表"""
    db_config = load_config()
    if not db_config:
        return
    
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()
    
    try:
        print("🔍 开始数据库迁移...")
        
        # 步骤1：为card_data_rows表添加所有字段
        print("🔧 为card_data_rows表添加字段...")
        
        field_definitions = [
            "field_01_pcs_project TEXT COMMENT 'PCS项目'",
            "field_02_spec_model TEXT COMMENT '规格型号'",
            "field_03_manufacturer TEXT COMMENT '制造商'",
            "field_04_manufacturer_desc TEXT COMMENT '制造商说明'",
            "field_05_origin_country TEXT COMMENT '原产国'",
            "field_06_origin_country_cn TEXT COMMENT '原产国中文名称'",
            "field_07_material_desc TEXT COMMENT '物料说明'",
            "field_08_stock_unit TEXT COMMENT '库存单位'",
            "field_09_material_group TEXT COMMENT '物料组'",
            "field_10_material_group_desc TEXT COMMENT '物料组说明'",
            "field_11_material_group2 TEXT COMMENT '物料组二'",
            "field_12_material_group2_desc TEXT COMMENT '物料组二说明'",
            "field_13_product_type TEXT COMMENT '产品类型'",
            "field_14_product_type_desc TEXT COMMENT '产品类型说明'",
            "field_15_product_category TEXT COMMENT '产品大类'",
            "field_16_product_category_desc TEXT COMMENT '产品大类说明'",
            "field_17_product_classification TEXT COMMENT '产品分类'",
            "field_18_product_classification_desc TEXT COMMENT '产品分类说明'",
            "field_19_weight DECIMAL(10,4) COMMENT '重量'",
            "field_20_special_part TEXT COMMENT '专用件'",
            "field_21_batch_control TEXT COMMENT '批次控制'",
            "field_22_material_signal TEXT COMMENT '物料信号'",
            "field_23_effective_date DATE COMMENT '生效日期'",
            "field_24_expiry_date DATE COMMENT '失效日期'",
            "field_25 TEXT COMMENT '预留字段25'",
            "field_26 TEXT COMMENT '预留字段26'",
            "field_27 TEXT COMMENT '预留字段27'",
            "field_28 TEXT COMMENT '预留字段28'",
            "field_29 TEXT COMMENT '预留字段29'",
            "field_30 TEXT COMMENT '预留字段30'",
            "field_31 TEXT COMMENT '预留字段31'",
            "field_32 TEXT COMMENT '预留字段32'",
            "field_33 TEXT COMMENT '预留字段33'",
            "field_34 TEXT COMMENT '预留字段34'",
            "field_35 TEXT COMMENT '预留字段35'",
            "field_36 TEXT COMMENT '预留字段36'",
            "field_37 TEXT COMMENT '预留字段37'",
            "field_38 TEXT COMMENT '预留字段38'",
            "field_39 TEXT COMMENT '预留字段39'",
            "field_40 TEXT COMMENT '预留字段40'",
            "field_41 TEXT COMMENT '预留字段41'",
            "field_42 TEXT COMMENT '预留字段42'",
            "field_43 TEXT COMMENT '预留字段43'",
            "field_44 TEXT COMMENT '预留字段44'",
            "field_45 TEXT COMMENT '预留字段45'",
            "field_46 TEXT COMMENT '预留字段46'",
            "field_47 TEXT COMMENT '预留字段47'",
            "field_48 TEXT COMMENT '预留字段48'",
            "field_49 TEXT COMMENT '预留字段49'",
            "field_50 TEXT COMMENT '预留字段50'"
        ]
        
        # 检查字段是否已存在，如果不存在则添加
        for field_def in field_definitions:
            field_name = field_def.split()[0]
            
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'card_data_rows' 
                AND COLUMN_NAME = %s
            """, (field_name,))
            
            if not cursor.fetchone():
                alter_sql = f"ALTER TABLE card_data_rows ADD COLUMN {field_def}"
                cursor.execute(alter_sql)
                print(f"  ✅ 添加字段: {field_name}")
        
        # 步骤2：将card_data表的数据迁移到card_data_rows表
        print("🔧 迁移数据...")
        
        # 获取所有流转卡
        cursor.execute("SELECT id FROM transfer_cards")
        cards = cursor.fetchall()
        
        for card in cards:
            card_id = card['id']
            print(f"  🔍 处理流转卡 {card_id}...")
            
            # 获取card_data表的数据
            cursor.execute("""
                SELECT * FROM card_data 
                WHERE card_id = %s
            """, (card_id,))
            
            card_data_records = cursor.fetchall()
            
            # 获取card_data_rows表的行
            cursor.execute("""
                SELECT id, `row_number` 
                FROM card_data_rows 
                WHERE card_id = %s
                ORDER BY `row_number`
            """, (card_id,))
            
            card_rows = cursor.fetchall()
            
            if card_data_records and card_rows:
                # 将数据迁移到每一行
                for row in card_rows:
                    row_id = row['id']
                    row_number = row['row_number']
                    
                    # 如果有多条card_data记录，选择对应行号的记录
                    # 如果只有一条记录，所有行都使用相同的数据
                    if len(card_data_records) == 1:
                        source_record = card_data_records[0]
                    else:
                        # 查找对应行号的记录
                        source_record = None
                        for record in card_data_records:
                            if hasattr(record, 'row_num') and record.get('row_num') == row_number:
                                source_record = record
                                break
                        if not source_record:
                            source_record = card_data_records[0]  # 默认使用第一条
                    
                    # 构建更新语句
                    update_fields = []
                    update_params = []
                    
                    for i in range(1, 51):
                        field_name = f'field_{i:02d}'
                        if field_name in source_record:
                            update_fields.append(f"{field_name} = %s")
                            update_params.append(source_record[field_name])
                    
                    if update_fields:
                        update_fields.append("updated_at = NOW()")
                        update_params.append(row_id)
                        
                        update_sql = f"""
                            UPDATE card_data_rows 
                            SET {', '.join(update_fields)} 
                            WHERE id = %s
                        """
                        cursor.execute(update_sql, update_params)
                
                print(f"  ✅ 流转卡 {card_id}: 迁移了 {len(card_rows)} 行数据")
        
        # 步骤3：删除card_data表
        print("🔧 删除card_data表...")
        cursor.execute("DROP TABLE IF EXISTS card_data")
        print("✅ card_data表已删除")
        
        # 提交所有更改
        connection.commit()
        print("✅ 数据库迁移完成！")
        
        # 验证迁移结果
        print("🔍 验证迁移结果...")
        cursor.execute("SELECT COUNT(*) as total FROM card_data_rows")
        total_rows = cursor.fetchone()['total']
        print(f"✅ card_data_rows表现在有 {total_rows} 条记录")
        
    except Exception as e:
        connection.rollback()
        print(f"❌ 迁移失败: {e}")
        import traceback
        print(f"❌ 错误堆栈: {traceback.format_exc()}")
    
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    migrate_to_single_table()
