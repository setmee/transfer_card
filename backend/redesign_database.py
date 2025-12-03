#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新设计数据库：支持动态行存储（只存储有数据的行）
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

def redesign_database():
    """重新设计数据库结构"""
    db_config = load_config()
    if not db_config:
        return
    
    connection = pymysql.connect(**db_config)
    cursor = connection.cursor()
    
    try:
        print("🔍 开始重新设计数据库...")
        
        # 步骤1：删除现有的card_data_rows表（因为它是固定行数的）
        print("🔧 删除现有的card_data_rows表...")
        cursor.execute("DROP TABLE IF EXISTS card_data_rows")
        print("✅ card_data_rows表已删除")
        
        # 步骤2：创建新的card_data表（每条记录代表一行有数据的数据）
        print("🔧 创建新的card_data表...")
        cursor.execute("""
            CREATE TABLE card_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                card_id INT NOT NULL COMMENT '流转卡ID',
                `row_number` INT NOT NULL COMMENT '行号（从1开始）',
                department_id INT NULL COMMENT '负责部门ID',
                status ENUM('draft', 'submitted', 'approved') DEFAULT 'draft' COMMENT '状态',
                submitted_by INT NULL COMMENT '提交人ID',
                submitted_at TIMESTAMP NULL COMMENT '提交时间',
                approved_by INT NULL COMMENT '审批人ID',
                approved_at TIMESTAMP NULL COMMENT '审批时间',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                
                -- 业务字段
                field_01_pcs_project TEXT COMMENT 'PCS项目',
                field_02_spec_model TEXT COMMENT '规格型号',
                field_03_manufacturer TEXT COMMENT '制造商',
                field_04_manufacturer_desc TEXT COMMENT '制造商说明',
                field_05_origin_country TEXT COMMENT '原产国',
                field_06_origin_country_cn TEXT COMMENT '原产国中文名称',
                field_07_material_desc TEXT COMMENT '物料说明',
                field_08_stock_unit TEXT COMMENT '库存单位',
                field_09_material_group TEXT COMMENT '物料组',
                field_10_material_group_desc TEXT COMMENT '物料组说明',
                field_11_material_group2 TEXT COMMENT '物料组二',
                field_12_material_group2_desc TEXT COMMENT '物料组二说明',
                field_13_product_type TEXT COMMENT '产品类型',
                field_14_product_type_desc TEXT COMMENT '产品类型说明',
                field_15_product_category TEXT COMMENT '产品大类',
                field_16_product_category_desc TEXT COMMENT '产品大类说明',
                field_17_product_classification TEXT COMMENT '产品分类',
                field_18_product_classification_desc TEXT COMMENT '产品分类说明',
                field_19_weight DECIMAL(10,4) COMMENT '重量',
                field_20_special_part TEXT COMMENT '专用件',
                field_21_batch_control TEXT COMMENT '批次控制',
                field_22_material_signal TEXT COMMENT '物料信号',
                field_23_effective_date DATE COMMENT '生效日期',
                field_24_expiry_date DATE COMMENT '失效日期',
                field_25 TEXT COMMENT '预留字段25',
                field_26 TEXT COMMENT '预留字段26',
                field_27 TEXT COMMENT '预留字段27',
                field_28 TEXT COMMENT '预留字段28',
                field_29 TEXT COMMENT '预留字段29',
                field_30 TEXT COMMENT '预留字段30',
                field_31 TEXT COMMENT '预留字段31',
                field_32 TEXT COMMENT '预留字段32',
                field_33 TEXT COMMENT '预留字段33',
                field_34 TEXT COMMENT '预留字段34',
                field_35 TEXT COMMENT '预留字段35',
                field_36 TEXT COMMENT '预留字段36',
                field_37 TEXT COMMENT '预留字段37',
                field_38 TEXT COMMENT '预留字段38',
                field_39 TEXT COMMENT '预留字段39',
                field_40 TEXT COMMENT '预留字段40',
                field_41 TEXT COMMENT '预留字段41',
                field_42 TEXT COMMENT '预留字段42',
                field_43 TEXT COMMENT '预留字段43',
                field_44 TEXT COMMENT '预留字段44',
                field_45 TEXT COMMENT '预留字段45',
                field_46 TEXT COMMENT '预留字段46',
                field_47 TEXT COMMENT '预留字段47',
                field_48 TEXT COMMENT '预留字段48',
                field_49 TEXT COMMENT '预留字段49',
                field_50 TEXT COMMENT '预留字段50',
                
                -- 索引
                INDEX idx_card_id (card_id),
                INDEX idx_status (status),
                INDEX idx_department (department_id),
                UNIQUE KEY uk_card_row (card_id, `row_number`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流转卡数据表（每条记录一行数据）'
        """)
        print("✅ 新的card_data表创建成功")
        
        # 步骤3：创建transfer_cards表（如果不存在）
        print("🔧 确保transfer_cards表存在...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transfer_cards (
                id INT AUTO_INCREMENT PRIMARY KEY,
                card_number VARCHAR(50) NOT NULL UNIQUE COMMENT '流转卡号',
                template_id INT NULL COMMENT '模板ID',
                title VARCHAR(200) COMMENT '标题',
                description TEXT COMMENT '描述',
                status ENUM('draft', 'active', 'completed', 'cancelled') DEFAULT 'draft' COMMENT '状态',
                created_by INT NOT NULL COMMENT '创建人ID',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
                
                INDEX idx_status (status),
                INDEX idx_created_by (created_by),
                INDEX idx_template (template_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流转卡主表'
        """)
        print("✅ transfer_cards表确保存在")
        
        # 提交更改
        connection.commit()
        print("✅ 数据库重新设计完成！")
        
        # 验证结果
        print("🔍 验证数据库结构...")
        cursor.execute("DESCRIBE card_data")
        columns = cursor.fetchall()
        print(f"✅ card_data表有 {len(columns)} 个字段")
        
        cursor.execute("SELECT COUNT(*) as count FROM transfer_cards")
        card_count = cursor.fetchone()['count']
        print(f"✅ transfer_cards表有 {card_count} 条记录")
        
        cursor.execute("SELECT COUNT(*) as count FROM card_data")
        data_count = cursor.fetchone()['count']
        print(f"✅ card_data表当前有 {data_count} 条记录")
        
        print("\n🎉 新的数据库设计特点：")
        print("  1. 每条记录代表一行有数据的数据")
        print("  2. 只有真正有数据的行才会存储")
        print("  3. 每个流转卡可以有不同数量的数据行")
        print("  4. 更高效的数据存储，避免存储空行")
        print("  5. 支持动态行号管理")
        
    except Exception as e:
        connection.rollback()
        print(f"❌ 重新设计失败: {e}")
        import traceback
        print(f"❌ 错误堆栈: {traceback.format_exc()}")
    
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    redesign_database()
