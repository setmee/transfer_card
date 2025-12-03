#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
"""

import pymysql
import bcrypt
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'charset': 'utf8mb4'
}

def create_database():
    """创建数据库"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS transfer_card_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        connection.commit()
        print("✓ 数据库创建成功")
    except Exception as e:
        print(f"✗ 数据库创建失败: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()
    return True

def init_tables():
    """初始化表结构"""
    try:
        # 连接到指定数据库
        config = DB_CONFIG.copy()
        config['database'] = 'transfer_card_system'
        connection = pymysql.connect(**config)
        
        with connection.cursor() as cursor:
            # 读取SQL文件
            schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'schema.sql')
            with open(schema_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 修改SQL内容，添加DROP TABLE IF EXISTS
            modified_sql = sql_content.replace(
                'CREATE TABLE departments (',
                'DROP TABLE IF EXISTS departments; CREATE TABLE departments ('
            ).replace(
                'CREATE TABLE users (',
                'DROP TABLE IF EXISTS users; CREATE TABLE users ('
            ).replace(
                'CREATE TABLE fields (',
                'DROP TABLE IF EXISTS fields; CREATE TABLE fields ('
            ).replace(
                'CREATE TABLE templates (',
                'DROP TABLE IF EXISTS templates; CREATE TABLE templates ('
            ).replace(
                'CREATE TABLE template_fields (',
                'DROP TABLE IF EXISTS template_fields; CREATE TABLE template_fields ('
            ).replace(
                'CREATE TABLE transfer_cards (',
                'DROP TABLE IF EXISTS transfer_cards; CREATE TABLE transfer_cards ('
            ).replace(
                'CREATE TABLE card_data (',
                'DROP TABLE IF EXISTS card_data; CREATE TABLE card_data ('
            ).replace(
                'CREATE TABLE card_data_rows (',
                'DROP TABLE IF EXISTS card_data_rows; CREATE TABLE card_data_rows ('
            ).replace(
                'CREATE TABLE template_field_permissions (',
                'DROP TABLE IF EXISTS template_field_permissions; CREATE TABLE template_field_permissions ('
            ).replace(
                'CREATE TABLE operation_logs (',
                'DROP TABLE IF EXISTS operation_logs; CREATE TABLE operation_logs ('
            )
            
            # 分割SQL语句
            sql_statements = [stmt.strip() for stmt in modified_sql.split(';') if stmt.strip()]
            
            # 执行SQL语句
            for statement in sql_statements:
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                    except Exception as e:
                        if "already exists" not in str(e) and "Duplicate entry" not in str(e):
                            print(f"SQL执行警告: {e}")
                            print(f"SQL语句: {statement[:100]}...")
            
        connection.commit()
        print("✓ 表结构创建成功")
    except Exception as e:
        print(f"✗ 表结构创建失败: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()
    return True

def init_departments():
    """初始化部门数据"""
    try:
        config = DB_CONFIG.copy()
        config['database'] = 'transfer_card_system'
        connection = pymysql.connect(**config)
        
        # SQL文件中已经有部门数据，这里可以跳过或添加额外数据
        print("✓ 部门数据已在SQL文件中初始化")
        
        connection.commit()
        print("✓ 部门数据初始化成功")
    except Exception as e:
        print(f"✗ 部门数据初始化失败: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()
    return True

def init_fields():
    """初始化字段数据"""
    try:
        config = DB_CONFIG.copy()
        config['database'] = 'transfer_card_system'
        connection = pymysql.connect(**config)
        
        # SQL文件中已经有字段数据，这里可以跳过或添加额外数据
        print("✓ 字段数据已在SQL文件中初始化")
        
        connection.commit()
        print("✓ 字段数据初始化成功")
    except Exception as e:
        print(f"✗ 字段数据初始化失败: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()
    return True

def init_users():
    """初始化用户数据"""
    try:
        config = DB_CONFIG.copy()
        config['database'] = 'transfer_card_system'
        connection = pymysql.connect(**config)
        
        # 创建测试用户密码都是 admin123
        password_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        users_data = [
            (1, 'admin', 'admin', None, password_hash),
            (2, 'dev_user', 'user', 1, password_hash),
            (3, 'purchase_user', 'user', 2, password_hash),
            (4, 'sales_user', 'user', 3, password_hash),
            (5, 'production_user', 'user', 4, password_hash),
            (6, 'quality_user', 'user', 5, password_hash)
        ]
        
        with connection.cursor() as cursor:
            for user in users_data:
                cursor.execute("""
                    INSERT IGNORE INTO users (
                        id, username, role, department_id, password
                    ) VALUES (%s, %s, %s, %s, %s)
                """, user)
        
        connection.commit()
        print("✓ 用户数据初始化成功")
    except Exception as e:
        print(f"✗ 用户数据初始化失败: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()
    return True

def main():
    """主函数"""
    print("开始初始化数据库...")
    
    steps = [
        ("创建数据库", create_database),
        ("创建表结构", init_tables),
        ("初始化部门数据", init_departments),
        ("初始化字段数据", init_fields),
        ("初始化用户数据", init_users)
    ]
    
    success_count = 0
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if step_func():
            success_count += 1
        else:
            print(f"初始化失败，停止后续步骤")
            break
    
    if success_count == len(steps):
        print("\n🎉 数据库初始化完成！")
        print("\n默认账户信息：")
        print("- 管理员: admin / admin123 (无部门限制)")
        print("- 研发用户: dev_user / admin123")
        print("- 采购用户: purchase_user / admin123")
        print("- 销售用户: sales_user / admin123")
        print("- 生产用户: production_user / admin123")
        print("- 质检用户: quality_user / admin123")
    else:
        print(f"\n❌ 数据库初始化失败！成功步骤: {success_count}/{len(steps)}")

if __name__ == '__main__':
    main()
