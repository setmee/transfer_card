#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查用户表数据
"""

import pymysql
import json
from dotenv import load_dotenv

load_dotenv()

def check_users():
    """检查用户数据"""
    try:
        # 加载配置
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            db_config = config['database']
            db_config['cursorclass'] = pymysql.cursors.DictCursor

        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        print('🔍 检查用户表数据...')
        
        # 检查管理员用户
        cursor.execute('SELECT id, username, role, is_active FROM users WHERE role = "admin"')
        admins = cursor.fetchall()
        print(f'管理员用户: {len(admins)} 个')
        for admin in admins:
            print(f'  ID: {admin["id"]}, 用户名: {admin["username"]}, 激活: {admin["is_active"]}')
        
        # 检查普通用户
        cursor.execute('SELECT id, username, department_id, role, is_active FROM users WHERE role = "user"')
        users = cursor.fetchall()
        print(f'普通用户: {len(users)} 个')
        for user in users:
            print(f'  ID: {user["id"]}, 用户名: {user["username"]}, 部门ID: {user["department_id"]}, 激活: {user["is_active"]}')
        
        conn.close()
        
    except Exception as e:
        print(f'❌ 检查失败: {e}')

if __name__ == '__main__':
    check_users()
