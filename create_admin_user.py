#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建管理员用户脚本
"""

import pymysql
import bcrypt
import json
from pathlib import Path

def load_config():
    """加载配置文件"""
    config_path = Path(__file__).parent / 'backend' / 'config' / 'config.json'
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return config

def create_admin_user():
    """创建管理员用户"""
    try:
        # 加载配置
        config = load_config()
        db_config = config['database']
        
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
        
        # 管理员信息
        username = 'admin'
        password = '123456'
        real_name = '系统管理员'
        email = 'admin@example.com'
        role = 'admin'
        
        # 检查用户是否已存在
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                print(f"⚠️  用户 '{username}' 已存在！")
                choice = input("是否要更新密码？(y/N): ").strip().lower()
                if choice != 'y':
                    print("操作已取消")
                    return
                else:
                    # 更新密码
                    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    cursor.execute(
                        "UPDATE users SET password = %s, real_name = %s, email = %s WHERE username = %s",
                        (hashed_password, real_name, email, username)
                    )
                    print(f"✅ 用户 '{username}' 密码已更新")
            else:
                # 创建新用户
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                cursor.execute(
                    """INSERT INTO users (username, password, real_name, email, role, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                    (username, hashed_password, real_name, email, role, True)
                )
                print(f"✅ 管理员用户 '{username}' 创建成功")
        
        # 提交更改
        connection.commit()
        
        # 显示用户信息
        print("\n" + "="*50)
        print("管理员账户信息")
        print("="*50)
        print(f"用户名: {username}")
        print(f"密码: {password}")
        print(f"真实姓名: {real_name}")
        print(f"邮箱: {email}")
        print(f"角色: {role}")
        print("="*50)
        print("\n请使用以上信息登录系统")
        
    except pymysql.Error as e:
        print(f"❌ 数据库错误: {e}")
    except FileNotFoundError:
        print("❌ 配置文件不存在: backend/config/config.json")
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        if 'connection' in locals() and connection:
            connection.close()
            print("\n数据库连接已关闭")

if __name__ == '__main__':
    print("="*50)
    print("创建管理员用户")
    print("="*50)
    create_admin_user()
