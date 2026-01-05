#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键初始化流转卡系统数据库
自动创建数据库并导入schema.sql
"""

import pymysql
import json
import os
import sys

def print_success(msg):
    print(f"✅ {msg}")

def print_error(msg):
    print(f"❌ {msg}")

def print_info(msg):
    print(f"ℹ️  {msg}")

def main():
    print("=" * 60)
    print("流转卡系统 - 数据库初始化")
    print("=" * 60)
    
    # 读取配置
    config_path = 'backend/config/config.json'
    if not os.path.exists(config_path):
        print_error(f"配置文件不存在: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    db_config = config['database']
    db_name = db_config['database']
    
    print_info(f"目标数据库: {db_name}")
    print()
    
    # 不连接到特定数据库，只连接到MySQL服务器
    server_config = {
        'host': db_config['host'],
        'port': db_config['port'],
        'user': db_config['user'],
        'password': db_config['password'],
        'charset': db_config['charset']
    }
    
    try:
        # 连接MySQL服务器
        print_info("正在连接MySQL服务器...")
        connection = pymysql.connect(**server_config)
        print_success("MySQL服务器连接成功")
        
        with connection.cursor() as cursor:
            # 检查数据库是否存在
            cursor.execute(f"SHOW DATABASES LIKE '{db_name}'")
            result = cursor.fetchone()
            
            if result:
                print(f"\n⚠️  数据库 '{db_name}' 已存在")
                choice = input("是否删除并重新创建？(y/N): ").strip().lower()
                
                if choice == 'y':
                    print_info(f"正在删除数据库 '{db_name}'...")
                    cursor.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
                    print_success("数据库已删除")
                else:
                    print_info("保留现有数据库，跳过创建步骤")
                    
                    # 检查是否有表
                    cursor.execute(f"USE `{db_name}`")
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()
                    
                    if tables:
                        print(f"\n⚠️  数据库中已有 {len(tables)} 个表")
                        choice = input("是否清空所有表并重新导入？(y/N): ").strip().lower()
                        
                        if choice != 'y':
                            print_info("取消初始化")
                            connection.close()
                            sys.exit(0)
            
            # 创建数据库
            print_info(f"正在创建数据库 '{db_name}'...")
            cursor.execute(f"""
                CREATE DATABASE IF NOT EXISTS `{db_name}`
                CHARACTER SET utf8mb4 
                COLLATE utf8mb4_unicode_ci
            """)
            print_success(f"数据库 '{db_name}' 创建成功")
            
            # 使用数据库
            cursor.execute(f"USE `{db_name}`")
            
        connection.close()
        
        # 导入schema.sql
        schema_path = 'database/schema.sql'
        if not os.path.exists(schema_path):
            print_error(f"数据库结构文件不存在: {schema_path}")
            sys.exit(1)
        
        print_info(f"正在导入数据库结构: {schema_path}")
        
        # 读取并执行SQL文件
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 重新连接到新创建的数据库
        server_config['database'] = db_name
        connection = pymysql.connect(**server_config)
        
        with connection.cursor() as cursor:
            # 分割SQL语句
            statements = []
            current_statement = []
            
            for line in sql_content.split('\n'):
                line = line.strip()
                
                # 跳过注释和空行
                if not line or line.startswith('--'):
                    continue
                
                current_statement.append(line)
                
                # 检查语句是否结束
                if line.endswith(';'):
                    full_statement = '\n'.join(current_statement)
                    statements.append(full_statement)
                    current_statement = []
            
            # 执行每个语句
            for i, statement in enumerate(statements, 1):
                try:
                    # 跳过CREATE DATABASE和USE语句（我们已经创建了）
                    if 'CREATE DATABASE' in statement or 'USE' in statement:
                        continue
                    
                    cursor.execute(statement)
                    print(f"  执行语句 {i}/{len(statements)}: 成功")
                except Exception as e:
                    if 'Duplicate' in str(e) or 'already exists' in str(e):
                        print(f"  执行语句 {i}/{len(statements)}: 跳过（已存在）")
                    else:
                        print(f"  执行语句 {i}/{len(statements)}: 错误 - {e}")
            
            connection.commit()
        
        # 检查创建的表
        with connection.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            table_count = len(tables)
        
        connection.close()
        
        print()
        print("=" * 60)
        print_success("数据库初始化完成！")
        print("=" * 60)
        print(f"数据库名称: {db_name}")
        print(f"表数量: {table_count}")
        print()
        print("下一步:")
        print("1. 启动后端: cd backend && python app.py")
        print("2. 启动前端: cd frontend && npm start")
        print("3. 或使用: ./start.bat (Windows) 或 ./start.sh (Linux/Mac)")
        print("=" * 60)
        
    except pymysql.Error as e:
        print_error(f"MySQL错误: {e}")
        print()
        print("请检查:")
        print("1. MySQL服务是否已启动")
        print("2. 配置文件 backend/config/config.json 中的数据库连接信息是否正确")
        print("3. 数据库用户权限是否足够")
        sys.exit(1)
    except Exception as e:
        print_error(f"未知错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
