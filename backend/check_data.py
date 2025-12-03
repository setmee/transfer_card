#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql
import json
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def load_config():
    try:
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            db_config = config['database']
            # 确保添加DictCursor
            db_config['cursorclass'] = pymysql.cursors.DictCursor
            return db_config
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        # 回退到环境变量
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'database': os.getenv('DB_NAME', 'transfer_card_system'),
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor
        }

def check_card_data():
    """检查流转卡数据"""
    try:
        # 连接数据库
        config = load_config()
        connection = pymysql.connect(**config)

        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            # 查询card_data表中card_id=9的数据
            cursor.execute('SELECT * FROM card_data WHERE card_id = 9')
            card_data = cursor.fetchone()
            
            if card_data:
                print('=== card_data表中的所有数据 ===')
                for key, value in card_data.items():
                    print(f'{key}: {value}')
                
                print('\n=== 有值的字段 ===')
                for key, value in card_data.items():
                    if key.startswith('field_') and value is not None and str(value).strip() != '':
                        print(f'{key}: {value}')
            else:
                print('没有找到card_id=9的数据')
                
            # 查询transfer_cards表确认流转卡存在
            cursor.execute('SELECT id, card_number, template_id FROM transfer_cards WHERE id = 9')
            card_info = cursor.fetchone()
            
            if card_info:
                print(f'\n=== 流转卡信息 ===')
                print(f'ID: {card_info["id"]}')
                print(f'卡号: {card_info["card_number"]}')
                print(f'模板ID: {card_info["template_id"]}')
            else:
                print('没有找到ID=9的流转卡')

    except Exception as e:
        print(f'错误: {e}')
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == '__main__':
    check_card_data()
