#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流转卡系统 - Python Flask后端
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
# from conflict_resolution import get_conflict_resolver  # 已删除
# from realtime_sync import get_sync_manager  # 已删除
# 锁定机制已移除，将重新设计
# from card_lock_manager import card_lock_manager
# from lock_api import lock_bp
# from simple_lock_api import simple_lock_bp  # 已删除

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
        "origins": "*",  # 允许所有来源
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": False
    }
}, supports_credentials=False)
jwt = JWTManager(app)

# 数据库配置 - 从配置文件读取
def load_config():
    try:
        # 尝试多个可能的配置文件路径
        config_paths = [
            'backend/config/config.json',
            'config/config.json',
            os.path.join(os.path.dirname(__file__), 'config', 'config.json')
        ]
        
        config = None
        for path in config_paths:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    print(f" 成功加载配置文件: {path}")
                    break
            except FileNotFoundError:
                continue
        
        if config:
            db_config = config['database']
            # 确保添加DictCursor
            db_config['cursorclass'] = pymysql.cursors.DictCursor
            return db_config
        else:
            raise FileNotFoundError("未找到配置文件")
            
    except Exception as e:
        print(f" 加载配置文件失败: {e}")
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

@app.route('/api/auth/refresh', methods=['POST'])
@jwt_required()
def refresh():
    """刷新访问令牌"""
    try:
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return jsonify({'success': False, 'message': '无效的令牌'}), 401
        
        # 获取用户信息
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            sql = """
            SELECT u.*, d.name as department_name 
            FROM users u 
            LEFT JOIN departments d ON u.department_id = d.id 
            WHERE u.id = %s AND u.is_active = 1
            """
            cursor.execute(sql, (current_user_id,))
            user = cursor.fetchone()
            
            if not user:
                return jsonify({'success': False, 'message': '用户不存在或已被禁用'}), 401
            
            # 生成新的访问令牌
            new_token = create_access_token(identity=str(user['id']))
            
            return jsonify({
                'success': True,
                'token': new_token,
                'data': {
                    'id': user['id'],
                    'username': user['username'],
                    'role': user['role'],
                    'department_id': user['department_id'],
                    'department_name': user['department_name']
                }
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'刷新令牌失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

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

def map_data_type_to_field_type(data_type):
    """将数据库数据类型映射为前端字段类型"""
    mapping = {
        'VARCHAR': 'text',
        'INT': 'number',
        'DECIMAL': 'number',
        'DATE': 'date',
        'BOOLEAN': 'boolean',
        'TEXT': 'text'
    }
    return mapping.get(data_type, 'text')

# 获取可用预留字段
@app.route('/api/fields/available-placeholders', methods=['GET'])
@jwt_required()
def get_available_placeholders():
    """获取可用的预留字段列表"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        if current_user['role'] != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            sql = """
            SELECT id, name, display_name, field_position
            FROM fields 
            WHERE is_placeholder = 1
            ORDER BY field_position
            """
            cursor.execute(sql)
            placeholders = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'data': placeholders
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取可用预留字段失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 创建字段（修改为将预留字段转换为业务字段）
@app.route('/api/fields', methods=['POST'])
@jwt_required()
def create_field():
    """创建新字段（将预留字段转换为业务字段）"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        if current_user['role'] != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        data = request.get_json()
        field_id = data.get('field_id')  # 要转换的预留字段ID
        name = data.get('name')
        display_name = data.get('display_name')
        field_type = data.get('field_type')
        department_name = data.get('department_name')
        category = data.get('category', '')
        validation_rules = data.get('validation_rules', '')
        options = data.get('options', '')
        is_required = data.get('is_required', False)
        is_hidden = data.get('is_hidden', False)
        
        if not field_id:
            return jsonify({'success': False, 'message': '请选择要转换的预留字段'}), 400
        if not all([name, display_name, field_type, department_name]):
            return jsonify({'success': False, 'message': '字段名称、显示名称、类型和负责部门不能为空'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 开始事务
            connection.begin()
            
            try:
                # 检查是否为预留字段
                cursor.execute("SELECT * FROM fields WHERE id = %s AND is_placeholder = 1", (field_id,))
                placeholder_field = cursor.fetchone()
                
                if not placeholder_field:
                    return jsonify({'success': False, 'message': '指定的字段不是预留字段或不存在'}), 400
                
                # 检查字段名是否已存在
                cursor.execute("SELECT id FROM fields WHERE name = %s AND id != %s", (name, field_id))
                if cursor.fetchone():
                    return jsonify({'success': False, 'message': '字段名已存在'}), 400
                
                # 获取部门ID
                dept_sql = "SELECT id FROM departments WHERE name = %s"
                cursor.execute(dept_sql, (department_name,))
                dept_result = cursor.fetchone()
                
                if not dept_result:
                    raise Exception(f"部门 '{department_name}' 不存在")
                
                # 更新预留字段为业务字段
                update_sql = """
                UPDATE fields 
                SET name = %s, display_name = %s, field_type = %s, 
                    department_id = %s, department_name = %s, category = %s,
                    validation_rules = %s, options = %s, is_required = %s, 
                    is_hidden = %s, is_placeholder = 0, updated_at = NOW()
                WHERE id = %s
                """
                cursor.execute(update_sql, (name, display_name, field_type, dept_result['id'], 
                                           department_name, category, validation_rules, options,
                                           1 if is_required else 0, 1 if is_hidden else 0, field_id))
                
                # 提交事务
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': '预留字段转换成功'
                })
            
            except Exception as e:
                connection.rollback()
                raise e
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'转换预留字段失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 更新字段
@app.route('/api/fields/<int:field_id>', methods=['PUT'])
@jwt_required()
def update_field(field_id):
    """更新字段信息"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        if current_user['role'] != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        data = request.get_json()
        display_name = data.get('display_name')
        field_type = data.get('field_type')
        department_name = data.get('department_name')
        category = data.get('category')
        validation_rules = data.get('validation_rules')
        options = data.get('options')
        is_required = data.get('is_required')
        is_hidden = data.get('is_hidden')
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 开始事务
            connection.begin()
            
            try:
                # 先检查字段是否存在
                cursor.execute("SELECT name, department_id FROM fields WHERE id = %s", (field_id,))
                field_result = cursor.fetchone()
                if not field_result:
                    return jsonify({'success': False, 'message': '字段不存在'}), 404
                
                # 构建更新SQL
                update_fields = []
                update_params = []
                
                if display_name is not None:
                    update_fields.append("display_name = %s")
                    update_params.append(display_name)
                
                if field_type is not None:
                    update_fields.append("field_type = %s")
                    update_params.append(field_type)
                
                if category is not None:
                    update_fields.append("category = %s")
                    update_params.append(category)
                
                if validation_rules is not None:
                    update_fields.append("validation_rules = %s")
                    update_params.append(validation_rules)
                
                if options is not None:
                    update_fields.append("options = %s")
                    update_params.append(json.dumps(options) if isinstance(options, (list, dict)) else options)
                
                if is_required is not None:
                    update_fields.append("is_required = %s")
                    update_params.append(1 if is_required else 0)
                
                if is_hidden is not None:
                    update_fields.append("is_hidden = %s")
                    update_params.append(1 if is_hidden else 0)
                
                # 如果部门名称有变化，更新部门ID
                if department_name is not None:
                    dept_sql = "SELECT id FROM departments WHERE name = %s"
                    cursor.execute(dept_sql, (department_name,))
                    dept_result = cursor.fetchone()
                    
                    if dept_result:
                        update_fields.append("department_id = %s")
                        update_params.append(dept_result['id'])
                        update_fields.append("department_name = %s")
                        update_params.append(department_name)
                
                if update_fields:
                    update_fields.append("updated_at = NOW()")
                    update_params.append(field_id)
                    
                    update_sql = f"UPDATE fields SET {', '.join(update_fields)} WHERE id = %s"
                    print(f" 执行SQL: {update_sql}")
                    print(f" 参数: {update_params}")
                    cursor.execute(update_sql, update_params)
                
                # 提交事务
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': '字段信息更新成功'
                })
            
            except Exception as e:
                connection.rollback()
                raise e
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新字段失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 删除字段（修改为还原为预留字段）
@app.route('/api/fields/<int:field_id>', methods=['DELETE'])
@jwt_required()
def delete_field(field_id):
    """删除字段（还原为预留字段）"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        if current_user['role'] != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 开始事务
            connection.begin()
            
            try:
                # 先检查字段是否存在且不是预留字段
                cursor.execute("SELECT * FROM fields WHERE id = %s AND is_placeholder = 0", (field_id,))
                field_result = cursor.fetchone()
                if not field_result:
                    return jsonify({'success': False, 'message': '字段不存在或已经是预留字段'}), 404
                
                # 还原为预留字段
                update_sql = """
                UPDATE fields 
                SET name = %s, display_name = %s, field_type = 'text',
                    department_id = NULL, department_name = NULL, category = '预留字段',
                    validation_rules = NULL, options = NULL, is_required = 0, 
                    is_hidden = 0, is_placeholder = 1, updated_at = NOW()
                WHERE id = %s
                """
                
                # 生成预留字段名
                placeholder_name = f"field_{field_result['field_position']:02d}"
                placeholder_display_name = f"预留字段{field_result['field_position']}"
                
                cursor.execute(update_sql, (placeholder_name, placeholder_display_name, field_id))
                
                # 提交事务
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': '字段已还原为预留字段'
                })
            
            except Exception as e:
                connection.rollback()
                raise e
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'还原预留字段失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 公共部门接口（不需要认证）
@app.route('/api/public/departments', methods=['GET'])
def get_public_departments():
    """获取公共部门列表（用于登录页面）"""
    try:
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            sql = "SELECT id, name FROM departments ORDER BY name"
            cursor.execute(sql)
            departments = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'data': departments
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取部门列表失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals() and connection is not None:
            connection.close()

# 获取当前用户信息
@app.route('/api/auth/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前用户信息"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        # 返回用户信息，不包含密码
        user_info = {
            'id': current_user['id'],
            'username': current_user['username'],
            'real_name': current_user.get('real_name', ''),
            'email': current_user.get('email', ''),
            'role': current_user['role'],
            'department_id': current_user['department_id'],
            'department_name': current_user['department_name'],
            'is_active': current_user['is_active'],
            'created_at': current_user['created_at'].isoformat() if current_user.get('created_at') else None
        }
        
        return jsonify({
            'success': True,
            'data': user_info
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取用户信息失败: {str(e)}'}), 500

# 退出登录
@app.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """退出登录"""
    try:
        # JWT是无状态的，客户端删除token即可
        return jsonify({
            'success': True,
            'message': '退出登录成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'退出登录失败: {str(e)}'}), 500

# ========== 用户管理接口 ==========

# 获取用户列表
@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    """获取用户列表"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        if current_user['role'] != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            sql = """
            SELECT u.*, d.name as department_name 
            FROM users u 
            LEFT JOIN departments d ON u.department_id = d.id 
            ORDER BY u.created_at DESC
            """
            cursor.execute(sql)
            users = cursor.fetchall()
            
            # 移除密码字段
            for user in users:
                user.pop('password', None)
            
            return jsonify({
                'success': True,
                'data': users
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取用户列表失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 创建用户
@app.route('/api/users', methods=['POST'])
@jwt_required()
def create_user():
    """创建新用户"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        if current_user['role'] != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        real_name = data.get('real_name', '')
        email = data.get('email', '')
        department_id = data.get('department_id')
        role = data.get('role', 'user')
        
        if not all([username, password, department_id]):
            return jsonify({'success': False, 'message': '用户名、密码和部门不能为空'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': '用户名已存在'}), 400
            
            # 加密密码
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            
            # 创建用户
            sql = """
            INSERT INTO users (username, password, real_name, email, department_id, role, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, 1, NOW())
            """
            cursor.execute(sql, (username, hashed_password.decode('utf-8'), real_name, email, department_id, role))
            connection.commit()
            
            return jsonify({
                'success': True,
                'message': '用户创建成功'
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'创建用户失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 更新用户
@app.route('/api/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """更新用户信息"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        if current_user['role'] != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        data = request.get_json()
        real_name = data.get('real_name')
        email = data.get('email')
        department_id = data.get('department_id')
        role = data.get('role')
        password = data.get('password')
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 构建更新SQL
            update_fields = []
            update_params = []
            
            if real_name is not None:
                update_fields.append("real_name = %s")
                update_params.append(real_name)
            
            if email is not None:
                update_fields.append("email = %s")
                update_params.append(email)
            
            if department_id is not None:
                update_fields.append("department_id = %s")
                update_params.append(department_id)
            
            if role is not None:
                update_fields.append("role = %s")
                update_params.append(role)
            
            if password:
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
                update_fields.append("password = %s")
                update_params.append(hashed_password.decode('utf-8'))
            
            if update_fields:
                update_fields.append("updated_at = NOW()")
                update_params.append(user_id)
                
                update_sql = f"UPDATE users SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(update_sql, update_params)
                connection.commit()
            
            return jsonify({
                'success': True,
                'message': '用户信息更新成功'
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新用户失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 删除用户
@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """删除用户"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        if current_user['role'] != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            connection.commit()
            
            return jsonify({
                'success': True,
                'message': '用户删除成功'
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除用户失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# ========== 部门管理接口 ==========

# 获取部门列表
@app.route('/api/departments', methods=['GET'])
@jwt_required()
def get_departments():
    """获取部门列表"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            sql = "SELECT * FROM departments ORDER BY name"
            cursor.execute(sql)
            departments = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'data': departments
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取部门列表失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 创建部门
@app.route('/api/departments', methods=['POST'])
@jwt_required()
def create_department():
    """创建新部门"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        if current_user['role'] != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        
        if not name:
            return jsonify({'success': False, 'message': '部门名称不能为空'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 检查部门名称是否已存在
            cursor.execute("SELECT id FROM departments WHERE name = %s", (name,))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': '部门名称已存在'}), 400
            
            # 创建部门
            sql = """
            INSERT INTO departments (name, description, created_at)
            VALUES (%s, %s, NOW())
            """
            cursor.execute(sql, (name, description))
            connection.commit()
            
            return jsonify({
                'success': True,
                'message': '部门创建成功'
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'创建部门失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 更新部门
@app.route('/api/departments/<int:dept_id>', methods=['PUT'])
@jwt_required()
def update_department(dept_id):
    """更新部门信息"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        if current_user['role'] != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        data = request.get_json()
        name = data.get('name')
        description = data.get('description')
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 构建更新SQL
            update_fields = []
            update_params = []
            
            if name is not None:
                update_fields.append("name = %s")
                update_params.append(name)
            
            if description is not None:
                update_fields.append("description = %s")
                update_params.append(description)
            
            if update_fields:
                update_fields.append("updated_at = NOW()")
                update_params.append(dept_id)
                
                update_sql = f"UPDATE departments SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(update_sql, update_params)
                connection.commit()
            
            return jsonify({
                'success': True,
                'message': '部门信息更新成功'
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新部门失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 删除部门
@app.route('/api/departments/<int:dept_id>', methods=['DELETE'])
@jwt_required()
def delete_department(dept_id):
    """删除部门"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        if current_user['role'] != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM departments WHERE id = %s", (dept_id,))
            connection.commit()
            
            return jsonify({
                'success': True,
                'message': '部门删除成功'
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除部门失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# ========== 流转卡接口 ==========

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
                # 普通用户只能看到有权限访问的流转卡，且不能看到草稿和取消状态
                sql = """
                SELECT DISTINCT tc.*, t.template_name, u.username as creator_name,
                       (SELECT COUNT(*) FROM card_data cdr WHERE cdr.card_id = tc.id) as row_count
                FROM transfer_cards tc
                LEFT JOIN templates t ON tc.template_id = t.id
                LEFT JOIN users u ON tc.created_by = u.id
                LEFT JOIN template_field_permissions tfp ON t.id = tfp.template_id
                WHERE (tfp.department_id = %s OR tc.created_by = %s)
                AND tc.status NOT IN ('draft', 'cancelled')
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
                
                # 不再创建card_data_rows记录，新的设计中只有card_data表
                # 每条记录代表一行有数据的数据，不需要预先创建空行
                
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
            
            # 获取模板配置的字段
            if current_user['role'] == 'admin':
                # 管理员可以看到模板配置的所有字段
                field_sql = """
                SELECT tf.*, f.department_name, f.department_id as field_dept_id,
                       GROUP_CONCAT(DISTINCT tfp.can_read) as can_read,
                       GROUP_CONCAT(DISTINCT tfp.can_write) as can_write,
                       GROUP_CONCAT(DISTINCT tfp.department_id) as perm_dept_id
                FROM template_fields tf
                LEFT JOIN fields f ON tf.field_id = f.id
                LEFT JOIN template_field_permissions tfp ON tf.field_name = tfp.field_name 
                                                          AND tfp.template_id = %s
                WHERE tf.template_id = %s
                GROUP BY tf.id
                ORDER BY tf.field_order
                """
                cursor.execute(field_sql, (card_info['template_id'], card_info['template_id']))
            else:
                # 普通用户只能看到模板配置且有权限的字段
                field_sql = """
                SELECT tf.*, f.department_name, f.department_id as field_dept_id,
                       GROUP_CONCAT(DISTINCT tfp.can_read) as can_read,
                       GROUP_CONCAT(DISTINCT tfp.can_write) as can_write,
                       GROUP_CONCAT(DISTINCT tfp.department_id) as perm_dept_id
                FROM template_fields tf
                LEFT JOIN fields f ON tf.field_id = f.id
                LEFT JOIN template_field_permissions tfp ON tf.field_name = tfp.field_name 
                                                          AND tfp.template_id = %s
                                                          AND tfp.department_id = %s
                WHERE tf.template_id = %s
                GROUP BY tf.id
                ORDER BY tf.field_order
                """
                cursor.execute(field_sql, (card_info['template_id'], current_user['department_id'], card_info['template_id']))
            
            fields = cursor.fetchall()
            
            # 处理GROUP_CONCAT结果，转换为布尔值，并重命名字段以匹配前端期望
            for field in fields:
                # 重命名字段以匹配前端期望的格式
                if 'field_name' in field and 'name' not in field:
                    field['name'] = field['field_name']
                if 'field_display_name' in field and 'display_name' not in field:
                    field['display_name'] = field['field_display_name']
                
                if field.get('can_read'):
                    # 将逗号分隔的值转换为布尔值
                    can_read_values = str(field['can_read']).split(',')
                    field['can_read'] = any(value.strip() == '1' for value in can_read_values)
                else:
                    field['can_read'] = False
                    
                if field.get('can_write'):
                    # 将逗号分隔的值转换为布尔值
                    can_write_values = str(field['can_write']).split(',')
                    field['can_write'] = any(value.strip() == '1' for value in can_write_values)
                else:
                    field['can_write'] = False
                    
                # 处理部门ID
                if field.get('perm_dept_id'):
                    dept_ids = str(field['perm_dept_id']).split(',')
                    field['perm_dept_id'] = [int(id.strip()) for id in dept_ids if id.strip().isdigit()]
                else:
                    field['perm_dept_id'] = None
            
            # 获取数据行（新的card_data表）
            cursor.execute("""
                SELECT cd.*, d.name as department_name
                FROM card_data cd
                LEFT JOIN departments d ON cd.department_id = d.id
                WHERE cd.card_id = %s
                ORDER BY cd.row_number
            """, (card_id,))
            rows = cursor.fetchall()
            
            # 不再有单独的card_data记录，数据直接在rows中
            card_data = None
            
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
                    field_name = field['field_name']
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

# 批量保存流转卡数据（带冲突检测和解决）
@app.route('/api/cards/<int:card_id>/data', methods=['POST'])
@jwt_required()
def save_card_data(card_id):
    """批量保存流转卡数据（支持冲突检测和解决）"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        # 锁定机制已移除，改为部门流转模式
        
        data = request.get_json()
        row_data_list = data.get('row_data', [])  # 行数据列表
        conflict_resolution = data.get('conflict_resolution', {})  # 冲突解决策略
        
        if not row_data_list:
            return jsonify({'success': False, 'message': '请提供要保存的数据'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 开始事务，使用SERIALIZABLE隔离级别防止并发问题
            connection.begin()
            
            try:
                # 设置事务隔离级别为SERIALIZABLE，防止并发修改
                cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                
                # 检查流转卡是否存在并锁定
                cursor.execute("SELECT id, template_id, updated_at, status FROM transfer_cards WHERE id = %s FOR UPDATE", (card_id,))
                card_result = cursor.fetchone()
                if not card_result:
                    return jsonify({'success': False, 'message': '流转卡不存在'}), 404
                
                # 检查流转卡是否已完成（管理员除外）
                if card_result['status'] == 'completed' and current_user['role'] != 'admin':
                    return jsonify({'success': False, 'message': '该流转卡已完成整个流转流程，无法再修改数据'}), 403
                
                template_id = card_result['template_id']
                card_updated_at = card_result['updated_at']
                
                # 处理每行数据 - 新的数据库结构（每条记录代表一行有数据的数据）
                for row_data in row_data_list:
                    row_number = row_data.get('row_number')
                    values = row_data.get('values', {})
                    client_updated_at = data.get('client_updated_at')  # 客户端数据最后更新时间
                    
                    if not row_number:
                        continue
                    
                    # 检查用户是否有权限修改这些字段
                    for field_name, field_value in values.items():
                        if current_user['role'] != 'admin':
                            # 检查字段权限
                            cursor.execute("""
                                SELECT can_write FROM template_field_permissions 
                                WHERE template_id = %s AND field_name = %s AND department_id = %s
                            """, (template_id, field_name, current_user['department_id']))
                            perm_result = cursor.fetchone()
                            
                            if not perm_result or not perm_result['can_write']:
                                return jsonify({
                                    'success': False, 
                                    'message': f'您没有权限修改字段 {field_name}'
                                }), 403
                    
                    # 锁定目标行防止并发修改
                    cursor.execute("""
                        SELECT id, updated_at, submitted_by, submitted_at 
                        FROM card_data 
                        WHERE card_id = %s AND `row_number` = %s 
                        FOR UPDATE
                    """, (card_id, row_number))
                    existing_row = cursor.fetchone()
                    
                    # 检查数据冲突：如果该行已被其他用户提交
                    if existing_row and existing_row['submitted_at']:
                        submitted_by_other = existing_row['submitted_by']
                        if submitted_by_other and str(submitted_by_other) != str(current_user['id']):
                            # 该行已被其他用户提交，禁止修改
                            cursor.execute("SELECT username FROM users WHERE id = %s", (submitted_by_other,))
                            submitter_result = cursor.fetchone()
                            submitter_name = submitter_result['username'] if submitter_result else '未知用户'
                            
                            return jsonify({
                                'success': False,
                                'message': f'第{row_number}行已被用户 {submitter_name} 提交，无法修改',
                                'error_type': 'DATA_CONFLICT',
                                'conflict_info': {
                                    'row_number': row_number,
                                    'submitted_by': submitter_name,
                                    'submitted_at': existing_row['submitted_at'].isoformat() if existing_row['submitted_at'] else None
                                }
                            }), 409
                    
                    # 检查版本冲突（基于更新时间）
                    if existing_row and client_updated_at:
                        server_updated_at = existing_row['updated_at']
                        if server_updated_at and client_updated_at:
                            try:
                                from datetime import datetime
                                client_time = datetime.fromisoformat(client_updated_at.replace('Z', '+00:00'))
                                server_time = server_updated_at.replace(tzinfo=None)
                                
                                # 如果服务器时间比客户端时间新，说明有冲突
                                if server_time > client_time:
                                    return jsonify({
                                        'success': False,
                                        'message': f'第{row_number}行数据已被其他用户修改，请刷新后重试',
                                        'error_type': 'VERSION_CONFLICT',
                                        'conflict_info': {
                                            'row_number': row_number,
                                            'server_updated_at': server_time.isoformat(),
                                            'client_updated_at': client_updated_at
                                        }
                                    }), 409
                            except Exception as version_error:
                                print(f"版本检查错误: {version_error}")
                                # 版本检查失败时继续执行，但记录警告
                    
                    if existing_row:
                        # 更新现有行
                        update_fields = []
                        update_params = []
                        
                        for field_name, field_value in values.items():
                            update_fields.append(f"{field_name} = %s")
                            update_params.append(field_value)
                        
                        if update_fields:
                            update_fields.append("updated_at = NOW()")
                            update_params.append(card_id)
                            update_params.append(row_number)
                            
                            update_sql = f"""
                            UPDATE card_data 
                            SET {', '.join(update_fields)} 
                            WHERE card_id = %s AND `row_number` = %s
                            """
                            cursor.execute(update_sql, update_params)
                            print(f" 更新行 {row_number}: {update_sql}")
                    else:
                        # 插入新行（只有有数据时才插入）
                        if any(values.values()):  # 只有当至少有一个字段有值时才插入
                            insert_fields = ['card_id', 'row_number'] + list(values.keys())
                            insert_values = [card_id, row_number] + list(values.values())
                            placeholders = ', '.join(['%s'] * len(insert_fields))
                            
                            insert_sql = f"""
                            INSERT INTO card_data ({', '.join([f'`{f}`' if f == 'row_number' else f for f in insert_fields])}, created_at, updated_at)
                            VALUES ({placeholders}, NOW(), NOW())
                            """
                            cursor.execute(insert_sql, insert_values)
                            print(f" 插入新行 {row_number}: {insert_sql}")
                    
                    # 更新行状态（如果用户提交）
                    if row_data.get('submit', False):
                        if existing_row and existing_row['submitted_at']:
                            # 检查是否已经提交
                            if existing_row['submitted_by'] == current_user['id']:
                                # 已经是同一用户提交，允许更新
                                pass
                            else:
                                # 其他用户已提交，禁止重复提交
                                return jsonify({
                                    'success': False,
                                    'message': f'第{row_number}行已被其他用户提交，无法重复提交',
                                    'error_type': 'ALREADY_SUBMITTED'
                                }), 409
                        
                        cursor.execute("""
                            UPDATE card_data 
                            SET status = 'submitted', submitted_by = %s, submitted_at = NOW()
                            WHERE card_id = %s AND `row_number` = %s
                        """, (current_user['id'], card_id, row_number))
                
                # 提交事务
                connection.commit()
                
                # 实时同步通知功能已移除
                print(f" 数据保存完成，流转卡ID: {card_id}")
                
                return jsonify({
                    'success': True,
                    'message': '数据保存成功'
                })
            
            except Exception as e:
                connection.rollback()
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
        print(f" PUT请求数据: {data}")
        
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
            # 直接使用数据作为字段数据，但排除系统字段
            filtered_data = {}
            for key, value in data.items():
                if key not in ['table_data', 'fieldData', 'status', 'card_id', 'template_id']:
                    filtered_data[key] = value
            if filtered_data:
                table_data = [filtered_data]
        
        print(f" 处理后的table_data: {table_data}")
        print(f" 处理后的status: {status}")
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 开始事务
            connection.begin()
            
            try:
                # 检查流转卡是否存在（必须包含status字段以支持自动流转）
                cursor.execute("SELECT id, template_id, status, current_department_id FROM transfer_cards WHERE id = %s FOR UPDATE", (card_id,))
                card_result = cursor.fetchone()
                if not card_result:
                    return jsonify({'success': False, 'message': '流转卡不存在'}), 404
                
                # 检查流转卡是否已完成（管理员除外）
                if card_result['status'] == 'completed' and current_user['role'] != 'admin':
                    return jsonify({'success': False, 'message': '该流转卡已完成整个流转流程，无法再修改数据'}), 403
                
                template_id = card_result['template_id']
                old_status = card_result.get('status')
                
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
                                
                            # 检查用户是否有权限修改这个字段
                            if current_user['role'] != 'admin':
                                cursor.execute("""
                                    SELECT can_write FROM template_field_permissions 
                                    WHERE template_id = %s AND field_name = %s AND department_id = %s
                                """, (template_id, field_name, current_user['department_id']))
                                perm_result = cursor.fetchone()
                                
                                if not perm_result or not perm_result['can_write']:
                                    print(f" 跳过无权限字段: {field_name}")
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
                            print(f" 收集字段更新: {field_name} = {processed_value} (原始值: {field_value})")
                        
                        # 检查该行是否已存在
                        cursor.execute("SELECT id FROM card_data WHERE card_id = %s AND `row_number` = %s", (card_id, row_number))
                        existing_row = cursor.fetchone()
                        
                        if existing_row and field_updates:
                            # 更新现有行
                            update_fields = []
                            update_params = []
                            
                            for field_name, field_value in field_updates.items():
                                update_fields.append(f"{field_name} = %s")
                                update_params.append(field_value)
                            
                            if update_fields:
                                update_fields.append("updated_at = NOW()")
                                update_params.append(card_id)
                                update_params.append(row_number)
                                
                                update_sql = f"""
                                UPDATE card_data 
                                SET {', '.join(update_fields)} 
                                WHERE card_id = %s AND `row_number` = %s
                                """
                                cursor.execute(update_sql, update_params)
                                print(f" 更新行 {row_number}: {update_sql}")
                        
                        elif not existing_row and field_updates:
                            # 插入新行（只有有数据时才插入）
                            insert_fields = ['card_id', 'row_number'] + list(field_updates.keys())
                            insert_values = [card_id, row_number] + list(field_updates.values())
                            placeholders = ', '.join(['%s'] * len(insert_fields))
                            
                            insert_sql = f"""
                            INSERT INTO card_data ({', '.join([f'`{f}`' if f == 'row_number' else f for f in insert_fields])}, created_at, updated_at)
                            VALUES ({placeholders}, NOW(), NOW())
                            """
                            cursor.execute(insert_sql, insert_values)
                            print(f" 插入新行 {row_number}: {insert_sql}")
                
                # 更新流转卡状态
                if status:
                    old_status = card_result.get('status')
                    cursor.execute("""
                        UPDATE transfer_cards 
                        SET status = %s, updated_at = NOW()
                        WHERE id = %s
                    """, (status, card_id))
                    
                    # 如果状态从draft变为in_progress，自动启动流转
                    if old_status == 'draft' and status == 'in_progress':
                        # 检查是否已启动流转
                        cursor.execute("""
                            SELECT current_department_id, template_id 
                            FROM transfer_cards 
                            WHERE id = %s
                        """, (card_id,))
                        card_status = cursor.fetchone()
                        
                        if card_status and card_status['current_department_id'] is None:
                            # 获取模板的部门流转顺序
                            cursor.execute("""
                                SELECT tdf.*, d.name as department_name
                                FROM template_department_flow tdf
                                LEFT JOIN departments d ON tdf.department_id = d.id
                                WHERE tdf.template_id = %s
                                ORDER BY tdf.flow_order
                            """, (card_status['template_id'],))
                            flow_steps = cursor.fetchall()
                            
                            if flow_steps:
                                # 删除触发器以避免循环触发
                                cursor.execute("DROP TRIGGER IF EXISTS update_card_flow_stats")
                                
                                # 更新流转卡当前部门
                                cursor.execute("""
                                    UPDATE transfer_cards 
                                    SET current_department_id = %s, flow_started_at = NOW()
                                    WHERE id = %s
                                """, (flow_steps[0]['department_id'], card_id))
                                
                                # 创建流转状态记录
                                for step in flow_steps:
                                    step_status = 'processing' if step['flow_order'] == 1 else 'pending'
                                    if step['flow_order'] == 1:
                                        # 第一步：processing状态，记录started_at
                                        cursor.execute("""
                                            INSERT INTO card_flow_status 
                                            (card_id, department_id, flow_order, status, started_at, created_at)
                                            VALUES (%s, %s, %s, %s, NOW(), NOW())
                                        """, (card_id, step['department_id'], step['flow_order'], step_status))
                                    else:
                                        # 其他步骤：pending状态，started_at为NULL
                                        cursor.execute("""
                                            INSERT INTO card_flow_status 
                                            (card_id, department_id, flow_order, status, created_at)
                                            VALUES (%s, %s, %s, %s, NOW())
                                        """, (card_id, step['department_id'], step['flow_order'], step_status))
                                
                                # 记录操作日志
                                cursor.execute("""
                                    INSERT INTO flow_operation_logs 
                                    (card_id, operation_type, operator_id, notes, created_at)
                                    VALUES (%s, 'start_flow', %s, %s, NOW())
                                """, (card_id, current_user['id'], f"自动启动流转，流转至{flow_steps[0]['department_name']}"))
                                
                                # 重新创建触发器
                                cursor.execute("""
                                CREATE TRIGGER IF NOT EXISTS update_card_flow_stats 
                                AFTER UPDATE ON transfer_cards
                                FOR EACH ROW
                                BEGIN
                                    IF NEW.status IN ('completed', 'cancelled') AND OLD.status NOT IN ('completed', 'cancelled') THEN
                                        UPDATE transfer_cards 
                                        SET flow_completed_at = NOW(),
                                            completed_flow_steps = (
                                                SELECT COUNT(*) 
                                                FROM card_flow_status 
                                                WHERE card_id = NEW.id AND status = 'completed'
                                            )
                                        WHERE id = NEW.id;
                                    END IF;
                                    
                                    IF NEW.status = 'flowing' AND OLD.status != 'flowing' THEN
                                        UPDATE transfer_cards 
                                        SET flow_started_at = NOW(),
                                            total_flow_steps = (
                                                SELECT COUNT(*) 
                                                FROM template_department_flow 
                                                WHERE template_id = NEW.template_id
                                            )
                                        WHERE id = NEW.id;
                                    END IF;
                                END
                                """)
                                
                                print(f" 自动启动流转卡 {card_id} 的流转，当前流转至: {flow_steps[0]['department_name']}")
                
                # 提交事务
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': '数据更新成功'
                })
            
            except Exception as e:
                connection.rollback()
                print(f" PUT请求错误: {str(e)}")
                import traceback
                print(f" 错误堆栈: {traceback.format_exc()}")
                raise e
    
    except Exception as e:
        print(f" PUT请求外部错误: {str(e)}")
        return jsonify({'success': False, 'message': f'更新数据失败: {str(e)}'}), 500
    
    finally:
        if 'connection' in locals():
            connection.close()

# ========== 模板接口 ==========

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

# 更新模板
@app.route('/api/templates/<int:template_id>', methods=['PUT'])
@jwt_required()
def update_template(template_id):
    """更新模板信息"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        data = request.get_json()
        template_name = data.get('template_name')
        template_description = data.get('template_description')
        is_active = data.get('is_active')
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 构建更新SQL
            update_fields = []
            update_params = []
            
            if template_name is not None:
                update_fields.append("template_name = %s")
                update_params.append(template_name)
            
            if template_description is not None:
                update_fields.append("template_description = %s")
                update_params.append(template_description)
            
            if is_active is not None:
                update_fields.append("is_active = %s")
                update_params.append(1 if is_active else 0)
            
            if update_fields:
                update_fields.append("updated_at = NOW()")
                update_params.append(template_id)
                
                update_sql = f"UPDATE templates SET {', '.join(update_fields)} WHERE id = %s"
                cursor.execute(update_sql, update_params)
                connection.commit()
            
            return jsonify({
                'success': True,
                'message': '模板信息更新成功'
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新模板失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 删除模板
@app.route('/api/templates/<int:template_id>', methods=['DELETE'])
@jwt_required()
def delete_template(template_id):
    """删除模板"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM templates WHERE id = %s", (template_id,))
            connection.commit()
            
            return jsonify({
                'success': True,
                'message': '模板删除成功'
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除模板失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# ========== 模板流转卡接口 ==========

# 获取模板流转卡列表（使用现有的transfer_cards表）
@app.route('/api/template-cards', methods=['GET'])
@jwt_required()
def get_template_cards():
    """获取基于模板的流转卡列表（包含流转顺序）"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            if current_user['role'] == 'admin':
                # 管理员可以看到所有基于模板的流转卡
                sql = """
                SELECT tc.*, t.template_name, u.username as creator_name,
                       (SELECT COUNT(*) FROM card_data cdr WHERE cdr.card_id = tc.id) as row_count,
                       d.name as current_department_name,
                       cfs.flow_order as current_step,
                       tdf.total_steps,
                       CASE 
                           WHEN cfs.flow_order = tdf.total_steps THEN 1 
                           ELSE 0 
                       END as is_last_department
                FROM transfer_cards tc
                LEFT JOIN templates t ON tc.template_id = t.id
                LEFT JOIN users u ON tc.created_by = u.id
                LEFT JOIN departments d ON tc.current_department_id = d.id
                LEFT JOIN card_flow_status cfs ON tc.id = cfs.card_id AND cfs.status = 'processing'
                LEFT JOIN (
                    SELECT 
                        template_id,
                        COUNT(*) as total_steps
                    FROM template_department_flow
                    GROUP BY template_id
                ) tdf ON tc.template_id = tdf.template_id
                WHERE tc.template_id IS NOT NULL
                ORDER BY tc.created_at DESC
                """
                cursor.execute(sql)
            else:
                # 普通用户可以看到：
                # 1. 当前流转到他们部门的流转卡（processing状态）
                # 2. 已经流转到过他们部门的流转卡（completed状态）
                # 3. 自己创建的流转卡
                sql = """
                SELECT DISTINCT tc.*, t.template_name, u.username as creator_name,
                       (SELECT COUNT(*) FROM card_data cdr WHERE cdr.card_id = tc.id) as row_count,
                       d.name as current_department_name,
                       cfs.flow_order as current_step,
                       tdf.total_steps,
                       CASE 
                           WHEN cfs.flow_order = tdf.total_steps THEN 1 
                           ELSE 0 
                       END as is_last_department,
                       CASE 
                           WHEN tc.current_department_id = %s THEN 'can_submit'
                           WHEN EXISTS (
                               SELECT 1 FROM card_flow_status cfs2 
                               WHERE cfs2.card_id = tc.id 
                               AND cfs2.department_id = %s 
                               AND cfs2.status = 'completed'
                           ) THEN 'view_only'
                           WHEN tc.created_by = %s THEN 'owner'
                           ELSE 'none'
                       END as permission_level
                FROM transfer_cards tc
                LEFT JOIN templates t ON tc.template_id = t.id
                LEFT JOIN users u ON tc.created_by = u.id
                LEFT JOIN departments d ON tc.current_department_id = d.id
                LEFT JOIN card_flow_status cfs ON tc.id = cfs.card_id AND cfs.status = 'processing'
                LEFT JOIN (
                    SELECT 
                        template_id,
                        COUNT(*) as total_steps
                    FROM template_department_flow
                    GROUP BY template_id
                ) tdf ON tc.template_id = tdf.template_id
                WHERE tc.template_id IS NOT NULL
                AND (
                    tc.current_department_id = %s 
                    OR EXISTS (
                        SELECT 1 FROM card_flow_status cfs3 
                        WHERE cfs3.card_id = tc.id 
                        AND cfs3.department_id = %s 
                        AND cfs3.status = 'completed'
                    )
                    OR tc.created_by = %s
                )
                AND tc.status NOT IN ('draft', 'cancelled')
                ORDER BY tc.created_at DESC
                """
                cursor.execute(sql, (current_user['department_id'], current_user['department_id'], current_user['id'], 
                                  current_user['department_id'], current_user['department_id'], current_user['id']))
            
            template_cards = cursor.fetchall()
            
            # 为每个流转卡获取完整的流转顺序
            for card in template_cards:
                # 格式化时间
                if card.get('created_at'):
                    card['created_at'] = card['created_at'].isoformat()
                if card.get('updated_at'):
                    card['updated_at'] = card['updated_at'].isoformat()
                
                # 获取模板的流转部门顺序
                if card.get('template_id'):
                    cursor.execute("""
                        SELECT tdf.*, d.name as department_name
                        FROM template_department_flow tdf
                        LEFT JOIN departments d ON tdf.department_id = d.id
                        WHERE tdf.template_id = %s
                        ORDER BY tdf.flow_order
                    """, (card['template_id'],))
                    flow_departments = cursor.fetchall()
                    
                    # 标记当前流转部门
                    for dept in flow_departments:
                        dept['is_current'] = (dept['department_id'] == card.get('current_department_id'))
                    
                    card['flow_departments'] = flow_departments
                else:
                    card['flow_departments'] = []
            
            return jsonify({
                'success': True,
                'data': template_cards
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取模板流转卡列表失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 删除模板流转卡
@app.route('/api/template-cards/<int:card_id>', methods=['DELETE'])
@jwt_required()
def delete_template_card(card_id):
    """删除模板流转卡"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 开始事务
            connection.begin()
            
            try:
                # 检查流转卡是否存在
                cursor.execute("SELECT id FROM transfer_cards WHERE id = %s", (card_id,))
                card_result = cursor.fetchone()
                if not card_result:
                    return jsonify({'success': False, 'message': '流转卡不存在'}), 404
                
                # 删除相关的card_data记录
                cursor.execute("DELETE FROM card_data WHERE card_id = %s", (card_id,))
                
                # 删除流转卡主记录
                cursor.execute("DELETE FROM transfer_cards WHERE id = %s", (card_id,))
                
                # 提交事务
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': '流转卡删除成功'
                })
            
            except Exception as e:
                connection.rollback()
                raise e
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除流转卡失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 基于模板创建流转卡（表格格式，使用现有的transfer_cards表）
@app.route('/api/template-cards/table-format', methods=['POST'])
@jwt_required()
def create_template_card_with_table_data():
    """基于模板创建流转卡（表格格式）"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        data = request.get_json()
        template_id = data.get('template_id')
        card_number = data.get('card_number')
        title = data.get('title', '')
        description = data.get('description', '')
        row_count = data.get('row_count', 10)
        responsible_person = data.get('responsible_person', '')
        create_date = data.get('create_date')
        status = data.get('status', 'draft')
        selected_fields = data.get('selected_fields', [])  # 选中的字段列表
        
        if not all([template_id, card_number]):
            return jsonify({'success': False, 'message': '模板ID和流转卡号不能为空'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 开始事务
            connection.begin()
            
            try:
                # 检查模板是否存在
                cursor.execute("SELECT id, template_name FROM templates WHERE id = %s", (template_id,))
                template_result = cursor.fetchone()
                if not template_result:
                    return jsonify({'success': False, 'message': '模板不存在'}), 404
                
                # 获取模板关联的字段配置
                cursor.execute("""
                    SELECT tf.*, f.name as field_name, f.field_position
                    FROM template_fields tf
                    LEFT JOIN fields f ON tf.field_id = f.id
                    WHERE tf.template_id = %s
                    ORDER BY tf.field_order
                """, (template_id,))
                template_fields = cursor.fetchall()
                
                # 如果模板没有配置字段，使用selected_fields作为备选
                if not template_fields and selected_fields:
                    # 从selected_fields创建临时字段配置
                    template_fields = []
                    for i, field_data in enumerate(selected_fields, 1):
                        template_fields.append({
                            'field_name': field_data.get('field_name'),
                            'field_order': i,
                            'is_required': field_data.get('is_required', False),
                            'default_value': field_data.get('default_value', ''),
                            'field_position': field_data.get('field_position', i)
                        })
                elif not template_fields and not selected_fields:
                    # 如果模板和selected_fields都没有，使用所有非预留字段
                    cursor.execute("""
                        SELECT name as field_name, field_position 
                        FROM fields 
                        WHERE is_placeholder = 0 
                        ORDER BY field_position
                    """)
                    all_fields = cursor.fetchall()
                    template_fields = [{'field_name': f['field_name'], 'field_order': i+1, 'field_position': f['field_position']} 
                                     for i, f in enumerate(all_fields)]
                
                # 检查流转卡号是否已存在
                cursor.execute("SELECT id FROM transfer_cards WHERE card_number = %s", (card_number,))
                if cursor.fetchone():
                    return jsonify({'success': False, 'message': '流转卡号已存在'}), 400
                
                # 创建流转卡主记录，使用现有的transfer_cards表
                sql = """
                INSERT INTO transfer_cards (card_number, template_id, title, description, 
                                          status, created_by, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """
                cursor.execute(sql, (card_number, template_id, title, description, 
                                     status, current_user['id']))
                card_id = cursor.lastrowid
                
                # 创建数据记录，使用现有的card_data表
                for i in range(1, row_count + 1):
                    cursor.execute("""
                        INSERT INTO card_data (card_id, `row_number`, created_at, updated_at)
                        VALUES (%s, %s, NOW(), NOW())
                    """, (card_id, i))
                
                # 根据模板字段设置默认值
                if template_fields:
                    update_fields = []
                    update_params = []
                    
                    for field in template_fields:
                        field_name = field.get('field_name')
                        default_value = field.get('default_value', '')
                        
                        # 优先使用模板配置的默认值，其次使用selected_fields的默认值
                        if not default_value and selected_fields:
                            for selected_field in selected_fields:
                                if selected_field.get('field_name') == field_name:
                                    default_value = selected_field.get('default_value', '')
                                    break
                        
                        if field_name and default_value:
                            update_fields.append(f"{field_name} = %s")
                            update_params.append(default_value)
                    
                    if update_fields:
                        update_fields.append("updated_at = NOW()")
                        update_params.append(card_id)
                        
                        update_sql = f"""
                        UPDATE card_data 
                        SET {', '.join(update_fields)} 
                        WHERE card_id = %s
                        """
                        cursor.execute(update_sql, update_params)
                
                # 提交事务
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': '基于模板的流转卡创建成功',
                    'data': {
                        'card_id': card_id,
                        'card_number': card_number,
                        'template_name': template_result['template_name'],
                        'row_count': row_count,
                        'template_fields_count': len(template_fields),
                        'selected_fields_count': len(selected_fields) if selected_fields else 0
                    }
                })
            
            except Exception as e:
                connection.rollback()
                raise e
    
    except Exception as e:
        print(f" 创建基于模板的流转卡失败详细错误: {str(e)}")
        print(f" 错误类型: {type(e).__name__}")
        import traceback
        print(f" 错误堆栈: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'创建基于模板的流转卡失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 获取模板关联字段列表
@app.route('/api/templates/<int:template_id>/fields', methods=['GET'])
@jwt_required()
def get_template_fields(template_id):
    """获取模板关联字段列表"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 检查模板是否存在
            cursor.execute("SELECT id FROM templates WHERE id = %s", (template_id,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'message': '模板不存在'}), 404
            
            # 获取与模板关联的字段
            sql = """
            SELECT tf.*, f.*, d.name as department_name
            FROM template_fields tf
            LEFT JOIN fields f ON tf.field_id = f.id
            LEFT JOIN departments d ON f.department_id = d.id
            WHERE tf.template_id = %s
            ORDER BY tf.field_order
            """
            cursor.execute(sql, (template_id,))
            template_fields = cursor.fetchall()
            
            # 如果模板没有关联字段，返回空数组
            if not template_fields:
                return jsonify({
                    'success': True,
                    'data': []
                })
            
            # 处理字段数据
            for field in template_fields:
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
                'data': template_fields
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取模板字段失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 添加模板字段关联
@app.route('/api/templates/<int:template_id>/fields', methods=['POST'])
@jwt_required()
def add_template_field(template_id):
    """为模板添加字段关联"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        data = request.get_json()
        field_id = data.get('field_id')
        
        if not field_id:
            return jsonify({'success': False, 'message': '字段ID不能为空'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 开始事务
            connection.begin()
            
            try:
                # 检查模板是否存在
                cursor.execute("SELECT id FROM templates WHERE id = %s", (template_id,))
                if not cursor.fetchone():
                    return jsonify({'success': False, 'message': '模板不存在'}), 404
                
                # 获取字段详细信息
                cursor.execute("SELECT id, name, display_name, field_type, options FROM fields WHERE id = %s", (field_id,))
                field_result = cursor.fetchone()
                if not field_result:
                    return jsonify({'success': False, 'message': '字段不存在'}), 404
                
                # 检查是否已存在关联
                cursor.execute(
                    "SELECT id FROM template_fields WHERE template_id = %s AND field_id = %s", 
                    (template_id, field_id)
                )
                if cursor.fetchone():
                    return jsonify({'success': False, 'message': '字段已关联到此模板'}), 400
                
                # 获取当前最大排序值
                cursor.execute(
                    "SELECT COALESCE(MAX(field_order), 0) as max_order FROM template_fields WHERE template_id = %s", 
                    (template_id,)
                )
                max_order_result = cursor.fetchone()
                next_order = (max_order_result['max_order'] or 0) + 1
                
                # 添加关联，包含冗余字段
                sql = """
                INSERT INTO template_fields (template_id, field_id, field_name, field_display_name, 
                                          field_type, field_order, options, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                """
                cursor.execute(sql, (template_id, field_id, field_result['name'], field_result['display_name'],
                                   field_result['field_type'], next_order, field_result['options']))
                
                # 提交事务
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': '字段关联成功'
                })
            
            except Exception as e:
                connection.rollback()
                raise e
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'添加模板字段失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 批量更新模板字段关联
@app.route('/api/templates/<int:template_id>/fields', methods=['PUT'])
@jwt_required()
def update_template_fields(template_id):
    """批量更新模板字段关联"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        data = request.get_json()
        if not data or not isinstance(data, list):
            return jsonify({'success': False, 'message': '请提供字段数据数组'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 开始事务
            connection.begin()
            
            try:
                # 检查模板是否存在
                cursor.execute("SELECT id FROM templates WHERE id = %s", (template_id,))
                if not cursor.fetchone():
                    return jsonify({'success': False, 'message': '模板不存在'}), 404
                
                # 删除现有关联
                cursor.execute("DELETE FROM template_fields WHERE template_id = %s", (template_id,))
                
                # 重新添加关联
                for field_data in data:
                    field_name = field_data.get('field_name')
                    field_order = field_data.get('field_order', 1)
                    is_required = field_data.get('is_required', False)
                    default_value = field_data.get('default_value', '')
                    
                    if not field_name:
                        continue
                    
                    # 获取字段信息
                    cursor.execute("SELECT id, display_name, field_type, options FROM fields WHERE name = %s", (field_name,))
                    field_result = cursor.fetchone()
                    if not field_result:
                        continue
                    
                    # 插入新的关联
                    sql = """
                    INSERT INTO template_fields (template_id, field_id, field_name, field_display_name, 
                                              field_type, field_order, is_required, default_value, 
                                              options, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    """
                    cursor.execute(sql, (template_id, field_result['id'], field_name, field_result['display_name'],
                                       field_result['field_type'], field_order, 1 if is_required else 0, 
                                       default_value, field_result['options']))
                
                # 提交事务
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': '模板字段更新成功'
                })
            
            except Exception as e:
                connection.rollback()
                raise e
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'更新模板字段失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 删除模板字段关联
@app.route('/api/templates/<int:template_id>/fields/<int:field_id>', methods=['DELETE'])
@jwt_required()
def remove_template_field(template_id, field_id):
    """删除模板字段关联"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 删除关联
            cursor.execute(
                "DELETE FROM template_fields WHERE template_id = %s AND field_id = %s", 
                (template_id, field_id)
            )
            connection.commit()
            
            return jsonify({
                'success': True,
                'message': '字段关联删除成功'
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除模板字段失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 快速创建流转卡
@app.route('/api/cards/quick-create', methods=['POST'])
@jwt_required()
def quick_create_card():
    """快速创建流转卡"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        data = request.get_json()
        card_number = data.get('card_number')
        batch_number = data.get('batch_number', '')
        product_name = data.get('product_name', '')
        template_id = data.get('template_id', 24)  # 默认使用测试模板
        card_data = data.get('card_data', {})
        
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
                title = f"{product_name} - {batch_number}" if product_name and batch_number else product_name or batch_number
                sql = """
                INSERT INTO transfer_cards (card_number, template_id, title, description, status, created_by, created_at)
                VALUES (%s, %s, %s, %s, 'draft', %s, NOW())
                """
                cursor.execute(sql, (card_number, template_id, title, f"快速创建: {batch_number}", current_user['id']))
                card_id = cursor.lastrowid
                
                # 创建第一行数据并设置字段值
                if card_data:
                    # 构建插入字段
                    insert_fields = ['card_id', 'row_number'] + list(card_data.keys())
                    insert_values = [card_id, 1] + list(card_data.values())
                    placeholders = ', '.join(['%s'] * len(insert_fields))
                    
                    insert_sql = f"""
                    INSERT INTO card_data ({', '.join([f'`{f}`' if f == 'row_number' else f for f in insert_fields])}, created_at, updated_at)
                    VALUES ({placeholders}, NOW(), NOW())
                    """
                    cursor.execute(insert_sql, insert_values)
                    print(f" 快速创建数据行: {insert_sql}")
                
                # 提交事务
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': '快速创建流转卡成功',
                    'data': {
                        'card_id': card_id,
                        'card_number': card_number,
                        'title': title,
                        'template_id': template_id
                    }
                })
            
            except Exception as e:
                connection.rollback()
                raise e
    
    except Exception as e:
        print(f" 快速创建失败详细错误: {str(e)}")
        print(f" 错误类型: {type(e).__name__}")
        import traceback
        print(f" 错误堆栈: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'快速创建流转卡失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# ========== 工作台相关接口 ==========

# 记录操作日志的装饰器
def log_operation(action, target_type="未知", target_id=None, description=""):
    """记录操作日志的装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                # 获取当前用户信息
                current_user = get_current_user_info()
                if not current_user:
                    return func(*args, **kwargs)
                
                # 获取客户端IP
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', 
                                         request.environ.get('REMOTE_ADDR', '127.0.0.1'))
                
                # 记录操作日志
                connection = get_db_connection()
                if connection:
                    try:
                        with connection.cursor() as cursor:
                            sql = """
                            INSERT INTO operation_logs 
                            (user_id, user_name, action, target_type, target_id, description, 
                             ip_address, user_agent, created_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
                            """
                            cursor.execute(sql, (
                                current_user['id'],
                                current_user['username'],
                                action,
                                target_type,
                                target_id,
                                description,
                                client_ip,
                                request.environ.get('HTTP_USER_AGENT', ''),
                            ))
                            connection.commit()
                    except Exception as e:
                        print(f"记录操作日志失败: {e}")
                        connection.rollback()
                    finally:
                        connection.close()
                
                # 执行原函数
                return func(*args, **kwargs)
            except Exception as e:
                print(f"操作日志装饰器错误: {e}")
                return func(*args, **kwargs)
        return wrapper
    return decorator

# 获取工作台统计数据
@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """获取工作台统计数据"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 第一个统计：状态为进行中的流转卡个数
            if current_user['role'] == 'admin':
                # 管理员可以看到所有进行中的流转卡
                cursor.execute("""
                    SELECT COUNT(*) as in_progress_count 
                    FROM transfer_cards 
                    WHERE status = 'in_progress'
                """)
            else:
                # 普通用户只能看到有权限访问的进行中流转卡
                cursor.execute("""
                    SELECT COUNT(DISTINCT tc.id) as in_progress_count
                    FROM transfer_cards tc
                    LEFT JOIN template_field_permissions tfp ON tc.template_id = tfp.template_id
                    WHERE tc.status = 'in_progress'
                    AND (tfp.department_id = %s OR tc.created_by = %s)
                """, (current_user['department_id'], current_user['id']))
            
            in_progress_result = cursor.fetchone()
            in_progress_cards = in_progress_result['in_progress_count'] if in_progress_result else 0
            
            # 第二个统计：今日创建的流转卡数量（改为从transfer_cards表统计）
            if current_user['role'] == 'admin':
                cursor.execute("""
                    SELECT COUNT(*) as today_create_count
                    FROM transfer_cards
                    WHERE DATE(created_at) = CURDATE()
                """)
            else:
                cursor.execute("""
                    SELECT COUNT(DISTINCT tc.id) as today_create_count
                    FROM transfer_cards tc
                    LEFT JOIN template_field_permissions tfp ON tc.template_id = tfp.template_id
                    WHERE DATE(tc.created_at) = CURDATE()
                    AND (tfp.department_id = %s OR tc.created_by = %s)
                """, (current_user['department_id'], current_user['id']))
            
            today_create_result = cursor.fetchone()
            today_create_count = today_create_result['today_create_count'] if today_create_result else 0
            
            # 第三个统计：本周创建的流转卡数量（改为从transfer_cards表统计）
            if current_user['role'] == 'admin':
                cursor.execute("""
                    SELECT COUNT(*) as weekly_create_count
                    FROM transfer_cards
                    WHERE YEARWEEK(created_at, 1) = YEARWEEK(CURDATE(), 1)
                """)
            else:
                cursor.execute("""
                    SELECT COUNT(DISTINCT tc.id) as weekly_create_count
                    FROM transfer_cards tc
                    LEFT JOIN template_field_permissions tfp ON tc.template_id = tfp.template_id
                    WHERE YEARWEEK(tc.created_at, 1) = YEARWEEK(CURDATE(), 1)
                    AND (tfp.department_id = %s OR tc.created_by = %s)
                """, (current_user['department_id'], current_user['id']))
            
            weekly_create_result = cursor.fetchone()
            weekly_create_count = weekly_create_result['weekly_create_count'] if weekly_create_result else 0
            
            # 第四个统计：流转卡总数（包括所有状态，除了cancelled）
            if current_user['role'] == 'admin':
                # 管理员可以看到所有非取消状态的流转卡
                cursor.execute("""
                    SELECT COUNT(*) as total_count 
                    FROM transfer_cards 
                    WHERE status != 'cancelled'
                """)
            else:
                # 普通用户只能看到有权限访问的非取消状态流转卡
                cursor.execute("""
                    SELECT COUNT(DISTINCT tc.id) as total_count
                    FROM transfer_cards tc
                    LEFT JOIN template_field_permissions tfp ON tc.template_id = tfp.template_id
                    WHERE tc.status != 'cancelled'
                    AND (tfp.department_id = %s OR tc.created_by = %s)
                """, (current_user['department_id'], current_user['id']))
            
            total_result = cursor.fetchone()
            total_cards = total_result['total_count'] if total_result else 0
            
            # 计算趋势（简化版本，实际应该与历史数据比较）
            stats = {
                'pendingCards': in_progress_cards,  # 改为进行中的流转卡个数
                'completedToday': today_create_count,  # 改为今日创建数量
                'weeklyTotal': weekly_create_count,   # 改为本周创建数量
                'totalCards': total_cards,            # 改为非取消状态的流转卡总数
                'pendingTrend': 'up' if in_progress_cards > 0 else 'down',
                'pendingChange': 15,  # 模拟数据
                'completedTrend': 'up' if today_create_count > 0 else 'down',
                'completedChange': 8,   # 模拟数据
                'weeklyTrend': 'up' if weekly_create_count > 0 else 'down',
                'weeklyChange': 12,     # 模拟数据
                'totalTrend': 'up',
                'totalChange': 5        # 模拟数据
            }
            
            return jsonify({
                'success': True,
                'data': stats
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取统计数据失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 获取最近操作记录
@app.route('/api/dashboard/operations', methods=['GET'])
@jwt_required()
def get_recent_operations():
    """获取最近操作记录"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        action_filter = request.args.get('action', '')
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 构建WHERE条件
            where_conditions = []
            params = []
            
            if action_filter:
                where_conditions.append("ol.action = %s")
                params.append(action_filter)
            
            where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
            
            # 获取总记录数
            count_sql = f"""
                SELECT COUNT(*) as total_count 
                FROM operation_logs ol
                LEFT JOIN users u ON ol.user_id = u.id
                LEFT JOIN departments d ON u.department_id = d.id
                {where_clause}
            """
            cursor.execute(count_sql, params)
            total_result = cursor.fetchone()
            total_count = total_result['total_count'] if total_result else 0
            
            # 获取分页数据
            offset = (page - 1) * page_size
            sql = f"""
                SELECT ol.*, u.real_name, u.username, d.name as department_name
                FROM operation_logs ol
                LEFT JOIN users u ON ol.user_id = u.id
                LEFT JOIN departments d ON u.department_id = d.id
                {where_clause}
                ORDER BY ol.created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql, params + [page_size, offset])
            operations = cursor.fetchall()
            
            # 格式化数据
            for op in operations:
                # 格式化时间
                if op['created_at']:
                    op['created_at'] = op['created_at'].isoformat()
                
                # 处理空值
                op['user_name'] = op['real_name'] or op['username'] or '未知用户'
                op['department_name'] = op['department_name'] or '未分配部门'
            
            # 计算分页信息
            total_pages = (total_count + page_size - 1) // page_size
            has_more = page < total_pages
            
            return jsonify({
                'success': True,
                'data': {
                    'operations': operations,
                    'pagination': {
                        'current_page': page,
                        'page_size': page_size,
                        'total_count': total_count,
                        'total_pages': total_pages,
                        'has_more': has_more
                    }
                }
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取操作记录失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()


# ========== 版本控制接口 ==========

# 获取带版本信息的流转卡数据
@app.route('/api/cards/<int:card_id>/data-with-versions', methods=['GET'])
@jwt_required()
def get_card_data_with_versions(card_id):
    """获取带版本信息的流转卡数据"""
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
                field_sql = """
                SELECT DISTINCT f.*, tfp.can_read, tfp.can_write, tfp.department_id as perm_dept_id
                FROM fields f
                LEFT JOIN template_field_permissions tfp ON f.name = tfp.field_name 
                                                          AND tfp.template_id = %s
                WHERE f.is_placeholder = 0
                ORDER BY f.field_position
                """
                cursor.execute(field_sql, (card_info['template_id'],))
            else:
                field_sql = """
                SELECT DISTINCT f.*, tfp.can_read, tfp.can_write, tfp.department_id as perm_dept_id
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
            
            # 额外去重处理
            unique_fields = {}
            for field in fields:
                field_name = field['name']
                if field_name not in unique_fields:
                    unique_fields[field_name] = field
            
            fields = list(unique_fields.values())
            
            # 获取带版本信息的数据行
            cursor.execute("""
                SELECT cd.*, d.name as department_name,
                       u1.username as submitted_by_name,
                       u2.username as updated_by_name
                FROM card_data cd
                LEFT JOIN departments d ON cd.department_id = d.id
                LEFT JOIN users u1 ON cd.submitted_by = u1.id
                LEFT JOIN users u2 ON cd.last_updated_by = u2.id
                WHERE cd.card_id = %s
                ORDER BY cd.row_number
            """, (card_id,))
            rows = cursor.fetchall()
            
            # 构建带版本信息的表格数据
            table_data = []
            
            for row in rows:
                row_data = {
                    'row_number': row['row_number'],
                    'department_id': row['department_id'],
                    'department_name': row['department_name'],
                    'status': row['status'],
                    'submitted_by': row['submitted_by'],
                    'submitted_by_name': row['submitted_by_name'],
                    'submitted_at': row['submitted_at'].isoformat() if row['submitted_at'] else None,
                    'version': row.get('version', 1),
                    'last_updated_by': row.get('last_updated_by'),
                    'last_updated_by_name': row.get('updated_by_name'),
                    'last_updated_at': row.get('last_updated_at').isoformat() if row.get('last_updated_at') else None,
                    'values': {}
                }
                
                # 为每个字段添加值
                for field in fields:
                    field_name = field['name']
                    field_value = row.get(field_name, '')
                    
                    # 处理日期格式
                    if field_value and hasattr(field_value, 'isoformat'):
                        field_value = field_value.isoformat()
                    elif field_value is None:
                        field_value = ''
                    
                    row_data['values'][field_name] = field_value
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
        return jsonify({'success': False, 'message': f'获取带版本信息的数据失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 冲突检测和解决API
@app.route('/api/cards/<int:card_id>/detect-conflicts', methods=['POST'])
@jwt_required()
def detect_conflicts(card_id):
    """检测数据冲突"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        data = request.get_json()
        row_data_list = data.get('row_data', [])
        
        if not row_data_list:
            return jsonify({'success': False, 'message': '请提供要检测的数据'}), 400
        
        # 冲突检测功能已移除
        conflicts = []
        suggestions = {}
        
        return jsonify({
            'success': True,
            'data': {
                'has_conflicts': len(conflicts) > 0,
                'conflicts': conflicts,
                'suggestions': suggestions
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'冲突检测失败: {str(e)}'}), 500

@app.route('/api/cards/<int:card_id>/resolve-conflicts', methods=['POST'])
@jwt_required()
def resolve_conflicts(card_id):
    """解决数据冲突"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        data = request.get_json()
        row_data_list = data.get('row_data', [])
        conflict_resolution = data.get('conflict_resolution', {})
        
        if not row_data_list:
            return jsonify({'success': False, 'message': '请提供要解决的数据'}), 400
        
        # 冲突解决功能已移除
        result = {'success': True, 'message': '冲突解决功能已移除', 'resolved_rows': len(row_data_list), 'failed_rows': 0}
        
        return jsonify({
            'success': result['success'],
            'message': result['message'],
            'data': {
                'resolved_rows': result['resolved_rows'],
                'failed_rows': result['failed_rows']
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'冲突解决失败: {str(e)}'}), 500

# 带版本检查的保存数据
@app.route('/api/cards/<int:card_id>/save-with-version', methods=['POST'])
@jwt_required()
def save_card_data_with_version(card_id):
    """带版本检查的保存流转卡数据"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        data = request.get_json()
        row_data_list = data.get('row_data', [])
        
        if not row_data_list:
            return jsonify({'success': False, 'message': '请提供要保存的数据'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 开始事务，使用SERIALIZABLE隔离级别
            connection.begin()
            
            try:
                # 设置事务隔离级别
                cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")
                
                # 检查流转卡是否存在并锁定
                cursor.execute("SELECT id, template_id, status FROM transfer_cards WHERE id = %s FOR UPDATE", (card_id,))
                card_result = cursor.fetchone()
                if not card_result:
                    return jsonify({'success': False, 'message': '流转卡不存在'}), 404
                
                # 检查流转卡是否已完成（管理员除外）
                if card_result['status'] == 'completed' and current_user['role'] != 'admin':
                    return jsonify({'success': False, 'message': '该流转卡已完成整个流转流程，无法再修改数据'}), 403
                
                template_id = card_result['template_id']
                
                # 处理每行数据
                for row_data in row_data_list:
                    row_number = row_data.get('row_number')
                    values = row_data.get('values', {})
                    expected_version = row_data.get('version')  # 客户端期望的版本号
                    
                    if not row_number:
                        continue
                    
                    # 检查用户权限
                    for field_name, field_value in values.items():
                        if current_user['role'] != 'admin':
                            cursor.execute("""
                                SELECT can_write FROM template_field_permissions 
                                WHERE template_id = %s AND field_name = %s AND department_id = %s
                            """, (template_id, field_name, current_user['department_id']))
                            perm_result = cursor.fetchone()
                            
                            if not perm_result or not perm_result['can_write']:
                                return jsonify({
                                    'success': False, 
                                    'message': f'您没有权限修改字段 {field_name}'
                                }), 403
                    
                    # 锁定目标行
                    cursor.execute("""
                        SELECT id, version, submitted_by, submitted_at 
                        FROM card_data 
                        WHERE card_id = %s AND `row_number` = %s 
                        FOR UPDATE
                    """, (card_id, row_number))
                    existing_row = cursor.fetchone()
                    
                    # 检查数据冲突
                    if existing_row and existing_row['submitted_at']:
                        submitted_by_other = existing_row['submitted_by']
                        if submitted_by_other and str(submitted_by_other) != str(current_user['id']):
                            cursor.execute("SELECT username FROM users WHERE id = %s", (submitted_by_other,))
                            submitter_result = cursor.fetchone()
                            submitter_name = submitter_result['username'] if submitter_result else '未知用户'
                            
                            return jsonify({
                                'success': False,
                                'message': f'第{row_number}行已被用户 {submitter_name} 提交，无法修改',
                                'error_type': 'DATA_CONFLICT',
                                'conflict_info': {
                                    'row_number': row_number,
                                    'submitted_by': submitter_name,
                                    'submitted_at': existing_row['submitted_at'].isoformat() if existing_row['submitted_at'] else None
                                }
                            }), 409
                    
                    # 版本检查（乐观锁）
                    if existing_row and expected_version is not None:
                        current_version = existing_row.get('version', 1)
                        if current_version != expected_version:
                            return jsonify({
                                'success': False,
                                'message': f'第{row_number}行数据已被其他用户修改，请刷新后重试',
                                'error_type': 'VERSION_CONFLICT',
                                'conflict_info': {
                                    'row_number': row_number,
                                    'expected_version': expected_version,
                                    'current_version': current_version
                                }
                            }), 409
                    
                    if existing_row:
                        # 更新现有行，版本号递增
                        update_fields = []
                        update_params = []
                        
                        for field_name, field_value in values.items():
                            update_fields.append(f"{field_name} = %s")
                            update_params.append(field_value)
                        
                        if update_fields:
                            update_fields.extend([
                                "version = version + 1",
                                "last_updated_by = %s",
                                "updated_at = NOW()"
                            ])
                            update_params.extend([current_user['id'], card_id, row_number])
                            
                            update_sql = f"""
                            UPDATE card_data 
                            SET {', '.join(update_fields)} 
                            WHERE card_id = %s AND `row_number` = %s
                            """
                            cursor.execute(update_sql, update_params)
                    else:
                        # 插入新行，版本号为1
                        if any(values.values()):
                            insert_fields = ['card_id', 'row_number', 'version', 'last_updated_by'] + list(values.keys())
                            insert_values = [card_id, row_number, 1, current_user['id']] + list(values.values())
                            placeholders = ', '.join(['%s'] * len(insert_fields))
                            
                            insert_sql = f"""
                            INSERT INTO card_data ({', '.join([f'`{f}`' if f == 'row_number' else f for f in insert_fields])}, created_at, updated_at)
                            VALUES ({placeholders}, NOW(), NOW())
                            """
                            cursor.execute(insert_sql, insert_values)
                    
                    # 更新行状态（如果用户提交）
                    if row_data.get('submit', False):
                        if existing_row and existing_row['submitted_at']:
                            if existing_row['submitted_by'] == current_user['id']:
                                pass
                            else:
                                return jsonify({
                                    'success': False,
                                    'message': f'第{row_number}行已被其他用户提交，无法重复提交',
                                    'error_type': 'ALREADY_SUBMITTED'
                                }), 409
                        
                        cursor.execute("""
                            UPDATE card_data 
                            SET status = 'submitted', submitted_by = %s, submitted_at = NOW()
                            WHERE card_id = %s AND `row_number` = %s
                        """, (current_user['id'], card_id, row_number))
                
                # 提交事务
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': '数据保存成功（带版本控制）'
                })
            
            except Exception as e:
                connection.rollback()
                raise e
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'保存数据失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 注册部门流转API
from flow_api import register_flow_blueprint
register_flow_blueprint(app)

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
