#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流转卡系统 - Python Flask后端 - 修复版本
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import pymysql
import bcrypt
import os
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建Flask应用
app = Flask(__name__)

# 配置
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# 初始化扩展 - 配置CORS支持前后端分离
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:8080", "http://127.0.0.1:8080", "http://192.168.216.1:8080", "http://192.168.202.1:8080", "http://192.168.8.28:8080", "http://172.25.16.1:8080"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
jwt = JWTManager(app)

# 数据库配置 - 从配置文件读取
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

DB_CONFIG = load_config()

# 数据库连接函数
def get_db_connection():
    try:
        connection = pymysql.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

# 获取当前用户完整信息
def get_current_user_info():
    """获取当前用户的完整信息"""
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return None
            
        connection = get_db_connection()
        if not connection:
            return None
        
        with connection.cursor() as cursor:
            sql = """
            SELECT u.*, d.name as department_name 
            FROM users u 
            LEFT JOIN departments d ON u.department_id = d.id 
            WHERE u.id = %s AND u.is_active = 1
            """
            cursor.execute(sql, (user_id,))
            return cursor.fetchone()
    except Exception as e:
        print(f"获取用户信息失败: {e}")
        return None
    finally:
        if 'connection' in locals():
            connection.close()

# 用户认证路由
@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        login_type = data.get('login_type', 'user')  # 'user' 或 'admin'
        department_id = data.get('department_id')  # 用户登录时的部门选择
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        # 用户登录时必须选择部门
        if login_type == 'user' and not department_id:
            return jsonify({'success': False, 'message': '请选择部门'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 查询用户
            sql = """
            SELECT u.*, d.name as department_name 
            FROM users u 
            LEFT JOIN departments d ON u.department_id = d.id 
            WHERE u.username = %s AND u.is_active = 1
            """
            cursor.execute(sql, (username,))
            user = cursor.fetchone()
            
            if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
            
            # 验证用户角色与登录类型是否匹配
            if login_type == 'admin' and user['role'] != 'admin':
                return jsonify({'success': False, 'message': '您不是管理员，无法通过管理员登录界面登录'}), 403
            
            if login_type == 'user' and user['role'] == 'admin':
                return jsonify({'success': False, 'message': '您是管理员，请通过管理员登录界面登录'}), 403
            
            # 验证用户登录时选择的部门是否与用户归属部门匹配
            if login_type == 'user' and str(user['department_id']) != str(department_id):
                return jsonify({'success': False, 'message': '选择的部门与用户归属部门不匹配'}), 403
            
            # 生成访问令牌
            access_token = create_access_token(identity=str(user['id']))
            
            return jsonify({
                'success': True,
                'token': access_token,
                'data': {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'department_id': user['department_id'],
                    'department_name': user['department_name']
                }
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'登录失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 验证字段名是否有效
def validate_field_name(field_name):
    """验证字段名是否有效"""
    if not field_name or not isinstance(field_name, str):
        return False
    
    # 字段名应该是字母、数字、下划线的组合
    import re
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
    return re.match(pattern, field_name) is not None

# 获取字段列表（根据部门权限过滤）
@app.route('/api/fields', methods=['GET'])
@jwt_required()
def get_fields():
    """获取字段列表"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            if current_user['role'] == 'admin':
                # 管理员可以看到所有字段，包括隐藏字段
                sql = """
                SELECT f.*, 
                       d.name as department_name,
                       CASE WHEN f.is_hidden = 1 THEN '价格敏感字段' ELSE '普通字段' END as field_type_desc
                FROM fields f 
                LEFT JOIN departments d ON f.department_id = d.id
                ORDER BY f.category, f.display_name
                """
                cursor.execute(sql)
            else:
                # 普通用户只能看到本部门的非隐藏字段
                sql = """
                SELECT f.*, 
                       d.name as department_name,
                       CASE WHEN f.is_hidden = 1 THEN '价格敏感字段' ELSE '普通字段' END as field_type_desc
                FROM fields f 
                LEFT JOIN departments d ON f.department_id = d.id
                WHERE (f.department_id = %s AND f.is_hidden = 0) OR f.department_id IS NULL
                ORDER BY f.category, f.display_name
                """
                cursor.execute(sql, (current_user['department_id'],))
            
            fields = cursor.fetchall()
            
            # 转换字段类型为前端友好的格式
            for field in fields:
                # 处理选项
                if field.get('options'):
                    try:
                        if isinstance(field['options'], str):
                            field['options'] = json.loads(field['options'])
                        elif not isinstance(field['options'], list):
                            field['options'] = []
                    except:
                        field['options'] = []
                else:
                    field['options'] = []
                
                # 确保布尔值正确转换
                field['is_required'] = bool(field.get('is_required', 0))
                field['is_hidden'] = bool(field.get('is_hidden', 0))
            
            return jsonify({
                'success': True,
                'data': fields
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取字段列表失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 获取流转卡列表
@app.route('/api/cards', methods=['GET'])
@jwt_required()
def get_cards():
    """获取流转卡列表"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            if current_user['role'] == 'admin':
                # 管理员可以看到所有流转卡
                sql = """
                SELECT tc.*, t.template_name, u.username as creator_name,
                       (SELECT COUNT(*) FROM card_data cdr WHERE cdr.card_id = tc.id) as row_count
                FROM transfer_cards tc
                LEFT JOIN templates t ON tc.template_id = t.id
                LEFT JOIN users u ON tc.created_by = u.id
                ORDER BY tc.created_at DESC
                """
                cursor.execute(sql)
            else:
                # 普通用户只能看到有权限访问的流转卡
                sql = """
                SELECT DISTINCT tc.*, t.template_name, u.username as creator_name,
                       (SELECT COUNT(*) FROM card_data cdr WHERE cdr.card_id = tc.id) as row_count
                FROM transfer_cards tc
                LEFT JOIN templates t ON tc.template_id = t.id
                LEFT JOIN users u ON tc.created_by = u.id
                LEFT JOIN template_field_permissions tfp ON t.id = tfp.template_id
                WHERE tfp.department_id = %s OR tc.created_by = %s
                ORDER BY tc.created_at DESC
                """
                cursor.execute(sql, (current_user['department_id'], current_user['id']))
            
            cards = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'data': cards
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取流转卡列表失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 创建流转卡（仅管理员）
@app.route('/api/cards', methods=['POST'])
@jwt_required()
def create_card():
    """创建流转卡（仅管理员）"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        if current_user['role'] != 'admin':
            return jsonify({'success': False, 'message': '只有管理员可以创建流转卡'}), 403
        
        data = request.get_json()
        card_number = data.get('card_number')
        template_id = data.get('template_id')
        title = data.get('title', '')
        description = data.get('description', '')
        row_count = data.get('row_count', 10)  # 默认创建10行
        
        if not card_number:
            return jsonify({'success': False, 'message': '流转卡号不能为空'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 开始事务
            connection.begin()
            
            try:
                # 检查流转卡号是否已存在
                cursor.execute("SELECT id FROM transfer_cards WHERE card_number = %s", (card_number,))
                if cursor.fetchone():
                    return jsonify({'success': False, 'message': '流转卡号已存在'}), 400
                
                # 创建流转卡主记录
                sql = """
                INSERT INTO transfer_cards (card_number, template_id, title, description, status, created_by, created_at)
                VALUES (%s, %s, %s, %s, 'draft', %s, NOW())
                """
                cursor.execute(sql, (card_number, template_id, title, description, current_user['id']))
                card_id = cursor.lastrowid
                
                # 提交事务
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': '流转卡创建成功',
                    'data': {
                        'card_id': card_id,
                        'card_number': card_number,
                        'row_count': row_count
                    }
                })
            
            except Exception as e:
                connection.rollback()
                raise e
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'创建流转卡失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 获取流转卡数据（表格格式）
@app.route('/api/cards/<int:card_id>/data', methods=['GET'])
@jwt_required()
def get_card_data(card_id):
    """获取流转卡数据（表格格式）"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 获取流转卡基本信息
            cursor.execute("""
                SELECT tc.*, t.template_name, u.username as creator_name
                FROM transfer_cards tc
                LEFT JOIN templates t ON tc.template_id = t.id
                LEFT JOIN users u ON tc.created_by = u.id
                WHERE tc.id = %s
            """, (card_id,))
            card_info = cursor.fetchone()
            
            if not card_info:
                return jsonify({'success': False, 'message': '流转卡不存在'}), 404
            
            # 获取用户有权限的字段
            if current_user['role'] == 'admin':
                # 管理员可以看到所有字段
                field_sql = """
                SELECT f.*, tfp.can_read, tfp.can_write, tfp.department_id as perm_dept_id
                FROM fields f
                LEFT JOIN template_field_permissions tfp ON f.name = tfp.field_name 
                                                          AND tfp.template_id = %s
                WHERE f.is_placeholder = 0
                ORDER BY f.field_position
                """
                cursor.execute(field_sql, (card_info['template_id'],))
            else:
                # 普通用户只能看到有权限的字段
                field_sql = """
                SELECT f.*, tfp.can_read, tfp.can_write, tfp.department_id as perm_dept_id
                FROM fields f
                LEFT JOIN template_field_permissions tfp ON f.name = tfp.field_name 
                                                          AND tfp.template_id = %s
                                                          AND tfp.department_id = %s
                WHERE f.is_placeholder = 0 
                AND (tfp.department_id = %s OR tfp.department_id IS NULL)
                ORDER BY f.field_position
                """
                cursor.execute(field_sql, (card_info['template_id'], current_user['department_id'], current_user['department_id']))
            
            fields = cursor.fetchall()
            
            # 获取数据行（新的card_data表）
            cursor.execute("""
                SELECT cd.*, d.name as department_name
                FROM card_data cd
                LEFT JOIN departments d ON cd.department_id = d.id
                WHERE cd.card_id = %s
                ORDER BY cd.row_number
            """, (card_id,))
            rows = cursor.fetchall()
            
            # 构建表格数据 - 新的数据结构（每条记录代表一行有数据的数据）
            table_data = []
            
            # 处理每一行数据
            for row in rows:
                row_data = {
                    'row_number': row['row_number'],
                    'department_id': row['department_id'],
                    'department_name': row['department_name'],
                    'status': row['status'],
                    'submitted_by': row['submitted_by'],
                    'submitted_at': row['submitted_at'].isoformat() if row['submitted_at'] else None,
                    'values': {}
                }
                
                # 为每个字段添加值（从当前行记录中获取）
                for field in fields:
                    field_name = field['name']
                    field_value = row.get(field_name, '')
                    
                    # 处理日期格式
                    if field_value and hasattr(field_value, 'isoformat'):
                        field_value = field_value.isoformat()
                    elif field_value is None:
                        field_value = ''
                    
                    row_data['values'][field_name] = field_value
                    # 同时将字段值直接添加到行数据中（兼容前端处理）
                    row_data[field_name] = field_value
                
                table_data.append(row_data)
            
            return jsonify({
                'success': True,
                'data': {
                    'card_info': card_info,
                    'fields': fields,
                    'table_data': table_data
                }
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取流转卡数据失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 批量保存流转卡数据 - 修复版本
@app.route('/api/cards/<int:card_id>/data', methods=['POST'])
@jwt_required()
def save_card_data(card_id):
    """批量保存流转卡数据"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        data = request.get_json()
        row_data_list = data.get('row_data', [])  # 行数据列表
        
        if not row_data_list:
            return jsonify({'success': False, 'message': '请提供要保存的数据'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 开始事务
            connection.begin()
            
            try:
                # 检查流转卡是否存在
                cursor.execute("SELECT id, template_id FROM transfer_cards WHERE id = %s", (card_id,))
                card_result = cursor.fetchone()
                if not card_result:
                    return jsonify({'success': False, 'message': '流转卡不存在'}), 404
                
                template_id = card_result['template_id']
                
                # 获取所有有效的字段名
                cursor.execute("SELECT name FROM fields WHERE is_placeholder = 0")
                valid_fields_result = cursor.fetchall()
                valid_fields = {field['name'] for field in valid_fields_result}
                
                # 处理每行数据 - 新的数据库结构（每条记录代表一行有数据的数据）
                for row_data in row_data_list:
                    row_number = row_data.get('row_number')
                    values = row_data.get('values', {})
                    
                    if not row_number:
                        continue
                    
                    # 验证和过滤字段名
                    valid_values = {}
                    for field_name, field_value in values.items():
                        # 验证字段名格式
                        if not validate_field_name(field_name):
                            print(f"🔍 跳过无效字段名: {field_name}")
                            continue
                        
                        # 检查字段是否在数据库中存在
                        if field_name not in valid_fields:
                            print(f"🔍 跳过不存在的字段: {field_name}")
                            continue
                        
                        # 检查用户是否有权限修改这些字段
                        if current_user['role'] != 'admin':
                            # 检查字段权限
                            cursor.execute("""
                                SELECT can_write FROM template_field_permissions 
                                WHERE template_id = %s AND field_name = %s AND department_id = %s
                            """, (template_id, field_name, current_user['department_id']))
                            perm_result = cursor.fetchone()
                            
                            if not perm_result or not perm_result['can_write']:
                                print(f"🔍 跳过无权限字段: {field_name}")
                                continue
                        
                        valid_values[field_name] = field_value
                    
                    if not valid_values:
                        print(f"🔍 行 {row_number} 没有有效字段，跳过")
                        continue
                    
                    # 检查该行是否已存在
                    cursor.execute("SELECT id FROM card_data WHERE card_id = %s AND row_number = %s", (card_id, row_number))
                    existing_row = cursor.fetchone()
                    
                    if existing_row:
                        # 更新现有行
                        update_fields = []
                        update_params = []
                        
                        for field_name, field_value in valid_values.items():
                            update_fields.append(f"`{field_name}` = %s")  # 使用反引号包围字段名
                            update_params.append(field_value)
                        
                        if update_fields:
                            update_fields.append("updated_at = NOW()")
                            update_params.append(card_id)
                            update_params.append(row_number)
                            
                            update_sql = f"""
                            UPDATE card_data 
                            SET {', '.join(update_fields)} 
                            WHERE card_id = %s AND row_number = %s
                            """
                            cursor.execute(update_sql, update_params)
                            print(f"🔍 更新行 {row_number}: {update_sql}")
                    else:
                        # 插入新行（只有有数据时才插入）
                        if any(valid_values.values()):  # 只有当至少有一个字段有值时才插入
                            insert_fields = ['card_id', 'row_number'] + [f"`{field}`" for field in valid_values.keys()]
                            insert_values = [card_id, row_number] + list(valid_values.values())
                            placeholders = ', '.join(['%s'] * len(insert_fields))
                            
                            insert_sql = f"""
                            INSERT INTO card_data ({', '.join(insert_fields)}, created_at, updated_at)
                            VALUES ({placeholders}, NOW(), NOW())
                            """
                            cursor.execute(insert_sql, insert_values)
                            print(f"🔍 插入新行 {row_number}: {insert_sql}")
                    
                    # 更新行状态（如果用户提交）
                    if row_data.get('submit', False):
                        cursor.execute("""
                            UPDATE card_data 
                            SET status = 'submitted', submitted_by = %s, submitted_at = NOW()
                            WHERE card_id = %s AND row_number = %s
                        """, (current_user['id'], card_id, row_number))
                
                # 提交事务
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': '数据保存成功'
                })
            
            except Exception as e:
                connection.rollback()
                print(f"🔥 保存数据错误: {str(e)}")
                import traceback
                print(f"🔥 错误堆栈: {traceback.format_exc()}")
                raise e
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'保存数据失败: {str(e)}'}), 500
    
    finally:
        if 'connection' in locals():
            connection.close()

# 更新流转卡数据
@app.route('/api/cards/<int:card_id>/data', methods=['PUT'])
@jwt_required()
def update_card_data(card_id):
    """更新流转卡数据"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        data = request.get_json()
        print(f"🔍 PUT请求数据: {data}")
        
        # 兼容多种数据格式
        table_data = []
        status = None
        
        if 'table_data' in data:
            # 标准格式：{ table_data: [...], status: "..." }
            table_data = data.get('table_data', [])
            status = data.get('status')
        elif 'fieldData' in data:
            # 前端可能发送的格式：{ fieldData: {...} }
            field_data = data.get('fieldData', {})
            if isinstance(field_data, dict):
                table_data = [field_data]
        elif isinstance(data, dict):
            # 直接使用数据作为字段数据
            table_data = [data]
        
        print(f"🔍 处理后的table_data: {table_data}")
        print(f"🔍 处理后的status: {status}")
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 开始事务
            connection.begin()
            
            try:
                # 检查流转卡是否存在
                cursor.execute("SELECT id, template_id FROM transfer_cards WHERE id = %s", (card_id,))
                card_result = cursor.fetchone()
                if not card_result:
                    return jsonify({'success': False, 'message': '流转卡不存在'}), 404
                
                template_id = card_result['template_id']
                
                # 获取所有有效的字段名
                cursor.execute("SELECT name FROM fields WHERE is_placeholder = 0")
                valid_fields_result = cursor.fetchall()
                valid_fields = {field['name'] for field in valid_fields_result}
                
                # 处理数据更新 - 新的数据库结构（每条记录代表一行有数据的数据）
                if table_data:
                    for row_data in table_data:
                        if not isinstance(row_data, dict):
                            continue
                        
                        row_number = row_data.get('row_number')
                        if not row_number:
                            continue
                        
                        # 收集字段更新
                        field_updates = {}
                        
                        for field_name, field_value in row_data.items():
                            # 跳过系统字段
                            if field_name in ['row_number', 'department_id', 'department_name', 'status', 'submitted_by', 'submitted_at', 'values']:
                                continue
                            
                            # 验证字段名格式
                            if not validate_field_name(field_name):
                                print(f"🔍 跳过无效字段名: {field_name}")
                                continue
                            
                            # 检查字段是否在数据库中存在
                            if field_name not in valid_fields:
                                print(f"🔍 跳过不存在的字段: {field_name}")
                                continue
                                
                            # 检查用户是否有权限修改这个字段
                            if current_user['role'] != 'admin':
                                cursor.execute("""
                                    SELECT can_write FROM template_field_permissions 
                                    WHERE template_id = %s AND field_name = %s AND department_id = %s
                                """, (template_id, field_name, current_user['department_id']))
                                perm_result = cursor.fetchone()
                                
                                if not perm_result or not perm_result['can_write']:
                                    print(f"🔍 跳过无权限字段: {field_name}")
                                    continue  # 跳过无权限的字段
                            
                            # 处理特殊字段类型的值
                            processed_value = field_value
                            if field_value == '' or field_value is None:
                                # 获取字段类型信息
                                cursor.execute("""
                                    SELECT field_type FROM fields 
                                    WHERE name = %s
                                """, (field_name,))
                                field_type_result = cursor.fetchone()
                                
                                if field_type_result:
                                    field_type = field_type_result['field_type']
                                    # 对于日期类型，将空字符串转换为NULL
                                    if field_type == 'date':
                                        processed_value = None
                                    # 对于数字类型，将空字符串转换为NULL
                                    elif field_type in ['number', 'int', 'decimal']:
                                        processed_value = None
                                    # 对于文本类型，保持空字符串或转换为NULL
                                    else:
                                        processed_value = None if field_value is None else ''
                                else:
                                    # 如果找不到字段类型信息，默认转换为None
                                    processed_value = None if field_value == '' else field_value
                            
                            # 收集字段更新
                            field_updates[field_name] = processed_value
                            print(f"🔍 收集字段更新: {field_name} = {processed_value} (原始值: {field_value})")
                        
                        if not field_updates:
                            print(f"🔍 行 {row_number} 没有有效字段更新，跳过")
                            continue
                        
                        # 检查该行是否已存在
                        cursor.execute("SELECT id FROM card_data WHERE card_id = %s AND row_number = %s", (card_id, row_number))
                        existing_row = cursor.fetchone()
                        
                        if existing_row and field_updates:
                            # 更新现有行
                            update_fields = []
                            update_params = []
                            
                            for field_name, field_value in field_updates.items():
                                update_fields.append(f"`{field_name}` = %s")  # 使用反引号包围字段名
                                update_params.append(field_value)
                            
                            if update_fields:
                                update_fields.append("updated_at = NOW()")
                                update_params.append(card_id)
                                update_params.append(row_number)
                                
                                update_sql = f"""
                                UPDATE card_data 
                                SET {', '.join(update_fields)} 
                                WHERE card_id = %s AND row_number = %s
                                """
                                cursor.execute(update_sql, update_params)
                                print(f"🔍 更新行 {row_number}: {update_sql}")
                        
                        elif not existing_row and field_updates:
                            # 插入新行（只有有数据时才插入）
                            insert_fields = ['card_id', 'row_number'] + [f"`{field}`" for field in field_updates.keys()]
                            insert_values = [card_id, row_number] + list(field_updates.values())
                            placeholders = ', '.join(['%s'] * len(insert_fields))
                            
                            insert_sql = f"""
                            INSERT INTO card_data ({', '.join(insert_fields)}, created_at, updated_at)
                            VALUES ({placeholders}, NOW(), NOW())
                            """
                            cursor.execute(insert_sql, insert_values)
                            print(f"🔍 插入新行 {row_number}: {insert_sql}")
                
                # 更新流转卡状态
                if status:
                    cursor.execute("""
                        UPDATE transfer_cards 
                        SET status = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (status, card_id))
                
                # 提交事务
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': '数据更新成功'
                })
            
            except Exception as e:
                connection.rollback()
                print(f"🔥 PUT请求错误: {str(e)}")
                import traceback
                print(f"🔥 错误堆栈: {traceback.format_exc()}")
                raise e
    
    except Exception as e:
        print(f"🔥 PUT请求外部错误: {str(e)}")
        return jsonify({'success': False, 'message': f'更新数据失败: {str(e)}'}), 500
    
    finally:
        if 'connection' in locals():
            connection.close()

# 获取模板列表
@app.route('/api/templates', methods=['GET'])
@jwt_required()
def get_templates():
    """获取模板列表"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            sql = "SELECT * FROM templates ORDER BY template_name"
            cursor.execute(sql)
            templates = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'data': templates
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取模板列表失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 创建模板
@app.route('/api/templates', methods=['POST'])
@jwt_required()
def create_template():
    """创建新模板"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        data = request.get_json()
        template_name = data.get('template_name')
        template_description = data.get('template_description', '')
        is_active = data.get('is_active', True)
        
        if not template_name:
            return jsonify({'success': False, 'message': '模板名称不能为空'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            sql = """
            INSERT INTO templates (template_name, template_description, is_active, created_by, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            """
            cursor.execute(sql, (template_name, template_description, 1 if is_active else 0, current_user['id']))
            connection.commit()
            
            return jsonify({
                'success': True,
                'message': '模板创建成功'
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'创建模板失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 健康检查
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    print("流转卡系统后端启动中...")
    print("健康检查: http://localhost:5000/health")
    print("API文档: http://localhost:5000/api")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )
