#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查用户密码格式
"""

import pymysql
import json
from dotenv import load_dotenv

load_dotenv()

def check_password_format():
    """检查密码格式"""
    try:
        # 加载配置
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            db_config = config['database']
            db_config['cursorclass'] = pymysql.cursors.DictCursor

        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        print('🔍 检查用户密码格式...')
        
        # 检查用户密码
        cursor.execute('SELECT username, password FROM users LIMIT 3')
        users = cursor.fetchall()
        
        for user in users:
            password = user['password']
            print(f'用户: {user["username"]}')
            print(f'密码长度: {len(password)}')
            print(f'密码开头: {password[:20]}...')
            print(f'是否包含$符号: {"$" in password}')
            print('---')
        
        conn.close()
        
    except Exception as e:
        print(f'❌ 检查失败: {e}')

if __name__ == '__main__':
    check_password_format()
