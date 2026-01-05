#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化示例数据脚本
- 创建部门
- 创建字段定义
- 创建模板
- 关联字段到模板
"""

import pymysql
import json
from pathlib import Path

def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent / 'backend' / 'config' / 'config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config

def init_departments(cursor):
    """初始化部门"""
    print("\n初始化部门...")
    
    departments = [
        ('工程部', '负责工程设计和规划'),
        ('采购部', '负责物料采购'),
        ('生产部', '负责生产制造'),
        ('质量部', '负责质量控制'),
        ('仓库部', '负责库存管理')
    ]
    
    for name, desc in departments:
        try:
            cursor.execute(
                "INSERT INTO departments (name, description) VALUES (%s, %s)",
                (name, desc)
            )
            print(f"  ✅ 创建部门: {name}")
        except Exception as e:
            print(f"  ⚠️  部门 {name} 已存在或创建失败: {e}")

def init_fields(cursor):
    """初始化字段定义"""
    print("\n初始化字段定义...")
    
    # 字段定义列表
    fields = [
        ('field_01_pcs_project', 'PCS项目', 'text', '工程部', '基本信息', 1),
        ('field_02_spec_model', '规格型号', 'text', '工程部', '基本信息', 2),
        ('field_03_manufacturer', '制造商', 'text', '采购部', '供应商信息', 3),
        ('field_04_manufacturer_desc', '制造商说明', 'text', '采购部', '供应商信息', 4),
        ('field_05_origin_country', '原产国', 'text', '采购部', '供应商信息', 5),
        ('field_06_origin_country_cn', '原产国中文名称', 'text', '采购部', '供应商信息', 6),
        ('field_07_material_desc', '物料说明', 'text', '工程部', '物料信息', 7),
        ('field_08_stock_unit', '库存单位', 'text', '仓库部', '库存信息', 8),
        ('field_09_material_group', '物料组', 'text', '工程部', '分类信息', 9),
        ('field_10_material_group_desc', '物料组说明', 'text', '工程部', '分类信息', 10),
        ('field_11_material_group2', '物料组二', 'text', '工程部', '分类信息', 11),
        ('field_12_material_group2_desc', '物料组二说明', 'text', '工程部', '分类信息', 12),
        ('field_13_product_type', '产品类型', 'text', '工程部', '分类信息', 13),
        ('field_14_product_type_desc', '产品类型说明', 'text', '工程部', '分类信息', 14),
        ('field_15_product_category', '产品大类', 'text', '工程部', '分类信息', 15),
        ('field_16_product_category_desc', '产品大类说明', 'text', '工程部', '分类信息', 16),
        ('field_17_product_classification', '产品分类', 'text', '工程部', '分类信息', 17),
        ('field_18_product_classification_desc', '产品分类说明', 'text', '工程部', '分类信息', 18),
        ('field_19_weight', '重量', 'number', '工程部', '规格信息', 19),
        ('field_20_special_part', '专用件', 'text', '工程部', '规格信息', 20),
        ('field_21_batch_control', '批次控制', 'text', '生产部', '生产信息', 21),
        ('field_22_material_signal', '物料信号', 'text', '工程部', '规格信息', 22),
        ('field_23_effective_date', '生效日期', 'date', '采购部', '时间信息', 23),
        ('field_24_expiry_date', '失效日期', 'date', '采购部', '时间信息', 24),
        # 预留字段
        ('field_25', '预留字段25', 'text', '工程部', '预留字段', 25),
        ('field_26', '预留字段26', 'text', '工程部', '预留字段', 26),
        ('field_27', '预留字段27', 'text', '工程部', '预留字段', 27),
        ('field_28', '预留字段28', 'text', '工程部', '预留字段', 28),
        ('field_29', '预留字段29', 'text', '工程部', '预留字段', 29),
        ('field_30', '预留字段30', 'text', '工程部', '预留字段', 30),
        ('field_31', '预留字段31', 'text', '工程部', '预留字段', 31),
        ('field_32', '预留字段32', 'text', '工程部', '预留字段', 32),
        ('field_33', '预留字段33', 'text', '工程部', '预留字段', 33),
        ('field_34', '预留字段34', 'text', '工程部', '预留字段', 34),
        ('field_35', '预留字段35', 'text', '工程部', '预留字段', 35),
        ('field_36', '预留字段36', 'text', '工程部', '预留字段', 36),
        ('field_37', '预留字段37', 'text', '工程部', '预留字段', 37),
        ('field_38', '预留字段38', 'text', '工程部', '预留字段', 38),
        ('field_39', '预留字段39', 'text', '工程部', '预留字段', 39),
        ('field_40', '预留字段40', 'text', '工程部', '预留字段', 40),
        ('field_41', '预留字段41', 'text', '工程部', '预留字段', 41),
        ('field_42', '预留字段42', 'text', '工程部', '预留字段', 42),
        ('field_43', '预留字段43', 'text', '工程部', '预留字段', 43),
        ('field_44', '预留字段44', 'text', '工程部', '预留字段', 44),
        ('field_45', '预留字段45', 'text', '工程部', '预留字段', 45),
        ('field_46', '预留字段46', 'text', '工程部', '预留字段', 46),
        ('field_47', '预留字段47', 'text', '工程部', '预留字段', 47),
        ('field_48', '预留字段48', 'text', '工程部', '预留字段', 48),
        ('field_49', '预留字段49', 'text', '工程部', '预留字段', 49),
        ('field_50', '预留字段50', 'text', '工程部', '预留字段', 50),
    ]
    
    # 获取部门ID
    dept_ids = {}
    cursor.execute("SELECT id, name FROM departments")
    for dept in cursor.fetchall():
        dept_ids[dept['name']] = dept['id']
    
    # 插入字段
    for name, display_name, field_type, dept_name, category, position in fields:
        try:
            dept_id = dept_ids.get(dept_name)
            cursor.execute(
                """INSERT INTO fields 
                (name, display_name, field_type, department_id, department_name, category, field_position, is_required)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (name, display_name, field_type, dept_id, dept_name, category, position, False)
            )
            print(f"  ✅ 创建字段: {display_name}")
        except Exception as e:
            print(f"  ⚠️  字段 {display_name} 已存在或创建失败: {e}")

def init_template(cursor):
    """初始化模板"""
    print("\n初始化模板...")
    
    try:
        # 获取第一个用户（管理员）作为创建者
        cursor.execute("SELECT id FROM users WHERE role='admin' LIMIT 1")
        admin = cursor.fetchone()
        if not admin:
            print("  ❌ 未找到管理员用户")
            return None
        
        # 获取第一个部门
        cursor.execute("SELECT id FROM departments LIMIT 1")
        dept = cursor.fetchone()
        
        cursor.execute(
            """INSERT INTO templates 
            (template_name, template_description, department_id, created_by, is_active)
            VALUES (%s, %s, %s, %s, %s)""",
            ('标准流转卡模板', '标准物料流转卡模板，包含50个字段', dept['id'], admin['id'], True)
        )
        template_id = cursor.lastrowid
        print(f"  ✅ 创建模板: 标准流转卡模板 (ID: {template_id})")
        return template_id
    except Exception as e:
        print(f"  ❌ 创建模板失败: {e}")
        return None

def init_template_fields(cursor, template_id):
    """初始化模板字段关联"""
    print(f"\n初始化模板字段关联（模板ID: {template_id})...")
    
    # 获取所有字段
    cursor.execute("SELECT id, name, display_name, field_type FROM fields ORDER BY field_position")
    fields = cursor.fetchall()
    
    for idx, field in enumerate(fields, 1):
        try:
            cursor.execute(
                """INSERT INTO template_fields
                (template_id, field_id, field_name, field_display_name, field_type, field_order, is_required)
                VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (template_id, field['id'], field['name'], field['display_name'], 
                 field['field_type'], idx, idx <= 10)  # 前10个字段必填
            )
            print(f"  ✅ 关联字段 {idx}: {field['display_name']}")
        except Exception as e:
            print(f"  ⚠️  关联字段 {field['display_name']} 失败: {e}")

def init_department_flow(cursor, template_id):
    """初始化模板部门流转顺序"""
    print(f"\n初始化模板部门流转顺序...")
    
    # 获取所有部门
    cursor.execute("SELECT id, name FROM departments ORDER BY id")
    departments = cursor.fetchall()
    
    for idx, dept in enumerate(departments, 1):
        try:
            cursor.execute(
                """INSERT INTO template_department_flow
                (template_id, department_id, flow_order, is_required, auto_skip, timeout_hours)
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (template_id, dept['id'], idx, idx > 1, False, 24)
            )
            print(f"  ✅ 设置流转顺序 {idx}: {dept['name']}")
        except Exception as e:
            print(f"  ⚠️  设置流转顺序 {dept['name']} 失败: {e}")

def init_sample_data():
    """初始化示例数据"""
    try:
        # 加载配置
        config = load_config()
        db_config = config['database']
        
        print("="*50)
        print("初始化示例数据")
        print("="*50)
        print(f"连接数据库: {db_config['database']}")
        
        # 连接数据库
        connection = pymysql.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['database'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        
        print("✅ 数据库连接成功")
        
        with connection.cursor() as cursor:
            # 1. 初始化部门
            init_departments(cursor)
            
            # 2. 初始化字段定义
            init_fields(cursor)
            
            # 3. 初始化模板
            template_id = init_template(cursor)
            
            if template_id:
                # 4. 初始化模板字段关联
                init_template_fields(cursor, template_id)
                
                # 5. 初始化模板部门流转顺序
                init_department_flow(cursor, template_id)
        
        # 提交更改
        connection.commit()
        
        # 显示统计信息
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM departments")
            dept_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM fields")
            field_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM templates")
            template_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM template_fields")
            template_field_count = cursor.fetchone()['count']
        
        print("\n" + "="*50)
        print("初始化完成！")
        print("="*50)
        print(f"部门数: {dept_count}")
        print(f"字段数: {field_count}")
        print(f"模板数: {template_count}")
        print(f"模板字段关联数: {template_field_count}")
        print("="*50)
        print("\n现在可以登录系统并创建流转卡了！")
        
    except pymysql.Error as e:
        print(f"❌ 数据库错误: {e}")
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        if 'connection' in locals() and connection:
            connection.close()
            print("\n数据库连接已关闭")

if __name__ == '__main__':
    init_sample_data()
