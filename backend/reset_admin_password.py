#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重置管理员密码
"""

import pymysql
import bcrypt
import json
from dotenv import load_dotenv

load_dotenv()

def reset_admin_password():
    """重置管理员密码为123456"""
    try:
        # 加载配置
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            db_config = config['database']
            db_config['cursorclass'] = pymysql.cursors.DictCursor

        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        
        print('🔧 重置管理员密码...')
        
        # 新密码
        new_password = '123456'
        username = 'admin'
        
        # 生成新的密码哈希
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        hashed_password_str = hashed_password.decode('utf-8')
        
        print(f'🔍 新密码哈希: {hashed_password_str}')
        
        # 更新密码
        cursor.execute('UPDATE users SET password = %s WHERE username = %s', 
                      (hashed_password_str, username))
        
        if cursor.rowcount > 0:
            print(f'✅ 用户 {username} 密码重置成功')
            conn.commit()
        else:
            print(f'❌ 用户 {username} 不存在')
        
        # 验证新密码
        cursor.execute('SELECT password FROM users WHERE username = %s', (username,))
        result = cursor.fetchone()
        
        if result:
            stored_password = result['password'].encode('utf-8')
            test_password = new_password.encode('utf-8')
            is_valid = bcrypt.checkpw(test_password, stored_password)
            print(f'🔍 密码验证测试: {is_valid}')
        
        conn.close()
        
    except Exception as e:
        print(f'❌ 重置密码失败: {e}')

if __name__ == '__main__':
    reset_admin_password()
