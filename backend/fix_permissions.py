#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复流转卡系统权限配置脚本
为所有模板、字段、部门组合创建默认权限
"""

import pymysql
import json
import os
from dotenv import load_dotenv

load_dotenv()

def load_config():
    """加载数据库配置"""
    try:
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            db_config = config['database']
            db_config['cursorclass'] = pymysql.cursors.DictCursor
            return db_config
    except Exception as e:
        print(f'加载配置文件失败: {e}')
        return None

def create_permissions():
    """创建模板字段权限"""
    DB_CONFIG = load_config()
    if not DB_CONFIG:
        return False
    
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            print("🔍 开始创建权限配置...")
            
            # 获取所有模板
            cursor.execute('SELECT id, template_name FROM templates WHERE is_active = 1')
            templates = cursor.fetchall()
            print(f"找到 {len(templates)} 个活跃模板")
            
            # 获取所有非预留字段
            cursor.execute('SELECT name, department_id, display_name FROM fields WHERE is_placeholder = 0')
            fields = cursor.fetchall()
            print(f"找到 {len(fields)} 个业务字段")
            
            # 获取所有部门
            cursor.execute('SELECT id, name FROM departments')
            departments = cursor.fetchall()
            print(f"找到 {len(departments)} 个部门")
            
            total_created = 0
            
            # 为每个模板创建权限
            for template in templates:
                template_id = template['id']
                template_name = template['template_name']
                print(f"\n📋 处理模板: {template_name} (ID: {template_id})")
                
                template_created = 0
                
                # 为每个字段创建权限
                for field in fields:
                    field_name = field['name']
                    field_dept_id = field['department_id']
                    field_display_name = field['display_name']
                    
                    # 为每个部门创建权限
                    for dept in departments:
                        dept_id = dept['id']
                        dept_name = dept['name']
                        
                        # 检查权限是否已存在
                        cursor.execute('''
                            SELECT id FROM template_field_permissions 
                            WHERE template_id = %s AND field_name = %s AND department_id = %s
                        ''', (template_id, field_name, dept_id))
                        existing = cursor.fetchone()
                        
                        if not existing:
                            # 根据字段所属部门决定权限
                            if field_dept_id == dept_id:
                                # 字段所属部门有读写权限
                                can_read = True
                                can_write = True
                                permission_desc = "读写"
                            else:
                                # 其他部门只有读权限
                                can_read = True
                                can_write = False
                                permission_desc = "只读"
                            
                            # 创建权限记录
                            cursor.execute('''
                                INSERT INTO template_field_permissions 
                                (template_id, field_name, department_id, can_read, can_write) 
                                VALUES (%s, %s, %s, %s, %s)
                            ''', (template_id, field_name, dept_id, can_read, can_write))
                            
                            total_created += 1
                            template_created += 1
                            
                            if template_created <= 5:  # 只显示前5个
                                print(f"  ✓ {field_display_name} -> {dept_name} ({permission_desc})")
            
            # 提交事务
            connection.commit()
            print(f"\n✅ 权限配置创建完成！")
            print(f"📊 总共创建了 {total_created} 条权限记录")
            
            # 验证结果
            cursor.execute('SELECT COUNT(*) as total FROM template_field_permissions')
            total_perms = cursor.fetchone()['total']
            print(f"📈 权限表现有 {total_perms} 条记录")
            
            # 显示具体权限示例
            print(f"\n🔍 权限示例（模板24）:")
            
            # 研发部权限
            cursor.execute('''
                SELECT f.display_name, tfp.can_write, d.name as dept_name
                FROM template_field_permissions tfp
                JOIN fields f ON tfp.field_name = f.name
                JOIN departments d ON tfp.department_id = d.id
                WHERE tfp.template_id = 24 AND tfp.department_id = 1
                ORDER BY f.field_position
                LIMIT 5
            ''')
            dev_perms = cursor.fetchall()
            print(f"  研发部权限:")
            for perm in dev_perms:
                status = "可写" if perm['can_write'] else "只读"
                print(f"    • {perm['display_name']} - {status}")
            
            return True
            
    except Exception as e:
        print(f"❌ 创建权限失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if 'connection' in locals():
            connection.close()

def test_user_permissions():
    """测试用户权限"""
    DB_CONFIG = load_config()
    if not DB_CONFIG:
        return
    
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            print(f"\n🧪 测试用户权限...")
            
            # 测试研发部用户（testuser）
            cursor.execute('''
                SELECT f.display_name, tfp.can_write
                FROM template_field_permissions tfp
                JOIN fields f ON tfp.field_name = f.name
                WHERE tfp.template_id = 24 
                AND tfp.department_id = 1 
                AND tfp.can_write = 1
                ORDER BY f.field_position
                LIMIT 10
            ''')
            dev_write_perms = cursor.fetchall()
            
            print(f"  研发部用户可写的字段（前10个）:")
            for perm in dev_write_perms:
                print(f"    ✓ {perm['display_name']}")
            
            # 测试采购部用户（purchase_user）
            cursor.execute('''
                SELECT f.display_name, tfp.can_write
                FROM template_field_permissions tfp
                JOIN fields f ON tfp.field_name = f.name
                WHERE tfp.template_id = 24 
                AND tfp.department_id = 2 
                AND tfp.can_write = 1
                ORDER BY f.field_position
                LIMIT 10
            ''')
            purchase_write_perms = cursor.fetchall()
            
            print(f"  采购部用户可写的字段（前10个）:")
            for perm in purchase_write_perms:
                print(f"    ✓ {perm['display_name']}")
                
    except Exception as e:
        print(f"❌ 测试权限失败: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == '__main__':
    print("🔧 流转卡系统权限修复工具")
    print("=" * 50)
    
    if create_permissions():
        test_user_permissions()
        print(f"\n🎉 权限修复完成！现在普通用户应该可以保存流转卡数据了。")
        print(f"\n📝 说明:")
        print(f"  • 每个字段对其所属部门有读写权限")
        print(f"  • 每个字段对其他部门只有读权限")
        print(f"  • 管理员用户对所有字段都有完整权限")
    else:
        print(f"\n❌ 权限修复失败，请检查错误信息")
