#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置文件管理模块
"""

import json
import os

def get_db_config():
    """获取数据库配置"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config['database']
    except Exception as e:
        # 默认配置
        return {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '',
            'database': 'transfer_card_system',
            'charset': 'utf8mb4'
        }

def get_server_config():
    """获取服务器配置"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config['server']
    except Exception as e:
        # 默认配置
        return {
            'host': '0.0.0.0',
            'port': 5000,
            'debug': True
        }

def get_jwt_config():
    """获取JWT配置"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config['jwt']
    except Exception as e:
        # 默认配置
        return {
            'secret': 'transfer_card_secret_key_2023',
            'expire_hours': 24
        }
