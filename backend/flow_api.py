#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
部门流转API
实现流转卡按部门顺序流转的功能
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
import sys
import os
from datetime import datetime, timedelta
import pymysql

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import get_db_config
from refactor_flow_logic import FlowManager

# 获取数据库配置
db_config = get_db_config()
db_config['cursorclass'] = pymysql.cursors.DictCursor

# 创建蓝图
flow_bp = Blueprint('flow', __name__, url_prefix='/api/flow')

def get_db_connection():
    """获取数据库连接"""
    try:
        import pymysql
        return pymysql.connect(**db_config)
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return None

def get_current_user_info():
    """获取当前用户完整信息"""
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

@flow_bp.route('/templates/<int:template_id>/departments', methods=['GET'])
@jwt_required()
def get_template_departments(template_id):
    """获取模板的部门流转顺序"""
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
            # 获取模板的部门流转顺序
            cursor.execute("""
                SELECT tdf.*, d.name as department_name
                FROM template_department_flow tdf
                LEFT JOIN departments d ON tdf.department_id = d.id
                WHERE tdf.template_id = %s
                ORDER BY tdf.flow_order
            """, (template_id,))
            departments = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'data': departments
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取模板部门流转顺序失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

@flow_bp.route('/templates/<int:template_id>/departments', methods=['POST'])
@jwt_required()
def set_template_departments(template_id):
    """设置模板的部门流转顺序"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        if current_user['role'] != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        data = request.get_json()
        departments = data.get('departments', [])
        
        if not departments:
            return jsonify({'success': False, 'message': '部门列表不能为空'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 开始事务
            connection.begin()
            
            try:
                # 删除现有的部门流转顺序
                cursor.execute("DELETE FROM template_department_flow WHERE template_id = %s", (template_id,))
                
                # 插入新的部门流转顺序
                for dept in departments:
                    dept_id = dept.get('department_id')
                    flow_order = dept.get('flow_order')
                    is_required = dept.get('is_required', True)
                    auto_skip = dept.get('auto_skip', False)
                    timeout_hours = dept.get('timeout_hours', 24)
                    
                    if not dept_id or not flow_order:
                        continue
                    
                    cursor.execute("""
                        INSERT INTO template_department_flow 
                        (template_id, department_id, flow_order, is_required, auto_skip, timeout_hours, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    """, (template_id, dept_id, flow_order, is_required, auto_skip, timeout_hours))
                
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': '模板部门流转顺序设置成功'
                })
            
            except Exception as e:
                connection.rollback()
                raise e
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'设置模板部门流转顺序失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

@flow_bp.route('/cards/<int:card_id>/start', methods=['POST'])
@jwt_required()
def start_card_flow(card_id):
    """启动流转卡流转"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 检查流转卡是否存在
            cursor.execute("SELECT * FROM transfer_cards WHERE id = %s", (card_id,))
            card = cursor.fetchone()
            if not card:
                return jsonify({'success': False, 'message': '流转卡不存在'}), 404
            
            # 检查是否需要启动流转（draft状态 或 in_progress状态但未设置当前部门）
            if card['status'] not in ['draft', 'in_progress']:
                return jsonify({'success': False, 'message': '只有草稿或进行中状态的流转卡可以启动流转'}), 400
            
            # 如果是in_progress状态但已有当前部门，则无需再次启动
            if card['status'] == 'in_progress' and card['current_department_id'] is not None:
                return jsonify({'success': False, 'message': '流转卡已在流转中'}), 400
        
        # 使用FlowManager初始化流转
        flow_manager = FlowManager()
        flow_manager.initialize_card_flow(card_id, card['template_id'])
        
        # 获取流转步骤信息
        flow_steps = flow_manager.get_template_flow_steps(card['template_id'])
        
        # 记录操作日志
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO flow_operation_logs 
                (card_id, operation_type, operator_id, notes, created_at)
                VALUES (%s, 'start_flow', %s, %s, NOW())
            """, (card_id, current_user['id'], f"启动流转，流转至{flow_steps[0]['department_name']}"))
            connection.commit()
        
        return jsonify({
            'success': True,
            'message': '流转卡流转启动成功',
            'data': {
                'current_department': flow_steps[0]['department_name'],
                'total_steps': len(flow_steps)
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'启动流转失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

@flow_bp.route('/cards/<int:card_id>/submit', methods=['POST'])
@jwt_required()
def submit_to_next_department(card_id):
    """提交到下一个部门"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        data = request.get_json()
        notes = data.get('notes', '')
        skip = data.get('skip', False)
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 检查流转卡和当前状态
            cursor.execute("""
                SELECT tc.*, 
                       cfs.flow_order as current_step, 
                       cfs.department_id as current_dept_id
                FROM transfer_cards tc
                LEFT JOIN card_flow_status cfs ON tc.id = cfs.card_id AND cfs.status = 'processing'
                WHERE tc.id = %s
            """, (card_id,))
            result = cursor.fetchone()
            
            if not result:
                return jsonify({'success': False, 'message': '流转卡不存在或未启动流转'}), 404
            
            # 管理员可以跳过部门权限检查
            is_admin = current_user['role'] == 'admin'
            if not is_admin and result['current_dept_id'] != current_user['department_id']:
                return jsonify({'success': False, 'message': f'只有当前处理部门可以提交流转，当前部门：{current_user["department_name"]}'}), 403
        
        # 使用FlowManager提交到下一部门
        flow_manager = FlowManager()
        flow_result = flow_manager.submit_to_next_department(card_id, current_user['id'], notes)
        
        if not flow_result['success']:
            return jsonify({'success': False, 'message': flow_result.get('message', '提交流转失败')}), 400
        
        return jsonify({
            'success': True,
            'message': flow_result['message'],
            'data': {
                'next_department_name': flow_result['next_department'],
                'next_department': flow_result['next_department'],
                'is_completed': flow_result['is_completed']
            }
        })
    
    except Exception as e:
        print(f"❌ 提交流转失败: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'提交流转失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

@flow_bp.route('/cards/<int:card_id>/status', methods=['GET'])
@jwt_required()
def get_card_flow_status(card_id):
    """获取流转卡流转状态"""
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
                SELECT tc.*, d.name as current_department_name
                FROM transfer_cards tc
                LEFT JOIN departments d ON tc.current_department_id = d.id
                WHERE tc.id = %s
            """, (card_id))
            card = cursor.fetchone()
            
            if not card:
                return jsonify({'success': False, 'message': '流转卡不存在'}), 404
            
            # 获取所有流转状态
            cursor.execute("""
                SELECT cfs.*, d.name as department_name, u.username as processed_by_name
                FROM card_flow_status cfs
                LEFT JOIN departments d ON cfs.department_id = d.id
                LEFT JOIN users u ON cfs.processed_by = u.id
                WHERE cfs.card_id = %s
                ORDER BY cfs.flow_order
            """, (card_id))
            flow_status = cursor.fetchall()
            
            # 获取流转历史
            cursor.execute("""
                SELECT fol.*, 
                       fd.name as from_department_name,
                       td.name as to_department_name,
                       u.username as operator_name
                FROM flow_operation_logs fol
                LEFT JOIN departments fd ON fol.from_department_id = fd.id
                LEFT JOIN departments td ON fol.to_department_id = td.id
                LEFT JOIN users u ON fol.operator_id = u.id
                WHERE fol.card_id = %s
                ORDER BY fol.created_at DESC
            """, (card_id))
            flow_history = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'data': {
                    'card_info': card,
                    'flow_status': flow_status,
                    'flow_history': flow_history,
                    'current_user_department': current_user['department_id'],
                    'is_current_processor': card['current_department_id'] == current_user['department_id']
                }
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取流转状态失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

@flow_bp.route('/cards/<int:card_id>/reject', methods=['POST'])
@jwt_required()
def reject_card_flow(card_id):
    """驳回流转卡"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        data = request.get_json()
        notes = data.get('notes', '')
        
        if not notes:
            return jsonify({'success': False, 'message': '驳回备注不能为空'}), 400
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 开始事务
            connection.begin()
            
            try:
                # 检查流转卡和当前状态
                cursor.execute("""
                    SELECT tc.*, cfs.department_id as current_dept_id
                    FROM transfer_cards tc
                    LEFT JOIN card_flow_status cfs ON tc.id = cfs.card_id AND cfs.status = 'processing'
                    WHERE tc.id = %s
                """, (card_id))
                result = cursor.fetchone()
                
                if not result:
                    return jsonify({'success': False, 'message': '流转卡不存在或未启动流转'}), 404
                
                if result['current_dept_id'] != current_user['department_id']:
                    return jsonify({'success': False, 'message': '只有当前处理部门可以驳回流转'}), 403
                
                # 更新流转卡状态为驳回
                cursor.execute("""
                    UPDATE transfer_cards 
                    SET status = 'rejected', flow_completed_at = NOW()
                    WHERE id = %s
                """, (card_id,))
                
                # 更新当前流转状态
                cursor.execute("""
                    UPDATE card_flow_status 
                    SET status = 'completed', completed_at = NOW(), processed_by = %s, notes = %s
                    WHERE card_id = %s AND department_id = %s AND status = 'processing'
                """, (current_user['id'], notes, card_id, current_user['department_id']))
                
                # 记录操作日志
                cursor.execute("""
                    INSERT INTO flow_operation_logs 
                    (card_id, from_department_id, operation_type, operator_id, notes, created_at)
                    VALUES (%s, %s, 'reject', %s, %s, NOW())
                """, (card_id, current_user['department_id'], current_user['id'], notes))
                
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': '流转卡已驳回'
                })
            
            except Exception as e:
                connection.rollback()
                raise e
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'驳回流转失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

@flow_bp.route('/cards/<int:card_id>/restart', methods=['POST'])
@jwt_required()
def restart_card_flow(card_id):
    """管理员重新启动已完成的流转卡"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        # 只有管理员可以重新启动流转
        if current_user['role'] != 'admin':
            return jsonify({'success': False, 'message': '只有管理员可以重新启动流转'}), 403
        
        data = request.get_json()
        target_department_id = data.get('department_id')  # 可选：指定要流转到的部门ID
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 开始事务
            connection.begin()
            
            try:
                # 检查流转卡
                cursor.execute("SELECT * FROM transfer_cards WHERE id = %s", (card_id,))
                card = cursor.fetchone()
                if not card:
                    return jsonify({'success': False, 'message': '流转卡不存在'}), 404
                
                # 只能重启已完成或已驳回的流转卡
                if card['status'] not in ['completed', 'rejected']:
                    return jsonify({'success': False, 'message': '只能重启已完成或已驳回的流转卡'}), 400
                
                # 获取模板的部门流转顺序
                cursor.execute("""
                    SELECT tdf.*, d.name as department_name
                    FROM template_department_flow tdf
                    LEFT JOIN departments d ON tdf.department_id = d.id
                    WHERE tdf.template_id = %s
                    ORDER BY tdf.flow_order
                """, (card['template_id']))
                flow_steps = cursor.fetchall()
                
                if not flow_steps:
                    return jsonify({'success': False, 'message': '模板未配置部门流转顺序'}), 400
                
                # 确定要流转到的部门
                if target_department_id:
                    # 找到指定部门的流转步骤
                    target_step = next((step for step in flow_steps if step['department_id'] == target_department_id), None)
                    if not target_step:
                        return jsonify({'success': False, 'message': '指定的部门不在流转顺序中'}), 400
                    restart_department = target_step
                else:
                    # 默认重启到第一个部门
                    restart_department = flow_steps[0]
                
                # 更新流转卡状态为进行中
                cursor.execute("""
                    UPDATE transfer_cards 
                    SET status = 'in_progress', 
                        current_department_id = %s, 
                        flow_completed_at = NULL,
                        flow_started_at = NOW()
                    WHERE id = %s
                """, (restart_department['department_id'], card_id))
                
                # 重置所有流转状态
                cursor.execute("""
                    UPDATE card_flow_status 
                    SET status = 'pending', 
                        completed_at = NULL, 
                        processed_by = NULL, 
                        started_at = NULL,
                        notes = NULL
                    WHERE card_id = %s
                """, (card_id,))
                
                # 设置指定部门为处理中
                cursor.execute("""
                    UPDATE card_flow_status 
                    SET status = 'processing', started_at = NOW()
                    WHERE card_id = %s AND department_id = %s
                """, (card_id, restart_department['department_id']))
                
                # 记录操作日志
                cursor.execute("""
                    INSERT INTO flow_operation_logs 
                    (card_id, from_department_id, to_department_id, operation_type, operator_id, notes, created_at)
                    VALUES (%s, %s, %s, 'restart', %s, %s, NOW())
                """, (card_id, card['current_department_id'], restart_department['department_id'], 
                      current_user['id'], f'重新启动流转，流转至{restart_department["department_name"]}'))
                
                connection.commit()
                
                return jsonify({
                    'success': True,
                    'message': f'流转卡已重新启动，流转至{restart_department["department_name"]}',
                    'data': {
                        'current_department': restart_department['department_name'],
                        'status': 'in_progress'
                    }
                })
            
            except Exception as e:
                connection.rollback()
                raise e
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'重新启动流转失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

@flow_bp.route('/pending', methods=['GET'])
@jwt_required()
def get_pending_flow_cards():
    """获取当前用户需要处理的流转卡"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 获取需要当前用户处理的流转卡
            cursor.execute("""
                SELECT 
                    tc.*,
                    d.name as current_department_name,
                    cfs.flow_order as current_step,
                    cfs.started_at as processing_started_at,
                    tdf.total_steps,
                    completed.completed_count,
                    CASE 
                        WHEN cfs.flow_order = tdf.total_steps THEN 1 
                        ELSE 0 
                    END as is_last_department
                FROM transfer_cards tc
                JOIN card_flow_status cfs ON tc.id = cfs.card_id AND cfs.status = 'processing'
                JOIN departments d ON cfs.department_id = d.id
                LEFT JOIN (
                    SELECT 
                        template_id,
                        COUNT(*) as total_steps
                    FROM template_department_flow
                    GROUP BY template_id
                ) tdf ON tc.template_id = tdf.template_id
                LEFT JOIN (
                    SELECT 
                        card_id,
                        COUNT(*) as completed_count
                    FROM card_flow_status
                    WHERE status = 'completed'
                    GROUP BY card_id
                ) completed ON tc.id = completed.card_id
                WHERE cfs.department_id = %s
                AND tc.status IN ('draft', 'in_progress')
                ORDER BY cfs.started_at DESC
            """, (current_user['department_id']))
            pending_cards = cursor.fetchall()
            
            return jsonify({
                'success': True,
                'data': pending_cards
            })
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取待处理流转卡失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

@flow_bp.route('/history', methods=['GET'])
@jwt_required()
def get_flow_history():
    """获取流转历史"""
    try:
        current_user = get_current_user_info()
        if not current_user:
            return jsonify({'success': False, 'message': '用户信息获取失败'}), 401
        
        # 获取分页参数
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        connection = get_db_connection()
        if not connection:
            return jsonify({'success': False, 'message': '数据库连接失败'}), 500
        
        with connection.cursor() as cursor:
            # 构建WHERE条件
            where_conditions = []
            params = []
            
            if current_user['role'] != 'admin':
                # 普通用户只能看到自己部门的流转历史
                where_conditions.append("(fol.from_department_id = %s OR fol.to_department_id = %s)")
                params.extend([current_user['department_id'], current_user['department_id']])
            
            where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
            
            # 获取总记录数
            count_sql = f"""
                SELECT COUNT(*) as total_count 
                FROM flow_operation_logs fol
                LEFT JOIN transfer_cards tc ON fol.card_id = tc.id
                {where_clause}
            """
            cursor.execute(count_sql, params)
            total_result = cursor.fetchone()
            total_count = total_result['total_count'] if total_result else 0
            
            # 获取分页数据
            offset = (page - 1) * page_size
            sql = f"""
                SELECT 
                    fol.*,
                    tc.card_number,
                    tc.title as card_title,
                    fd.name as from_department_name,
                    td.name as to_department_name,
                    u.username as operator_name
                FROM flow_operation_logs fol
                LEFT JOIN transfer_cards tc ON fol.card_id = tc.id
                LEFT JOIN departments fd ON fol.from_department_id = fd.id
                LEFT JOIN departments td ON fol.to_department_id = td.id
                LEFT JOIN users u ON fol.operator_id = u.id
                {where_clause}
                ORDER BY fol.created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql, params + [page_size, offset])
            history = cursor.fetchall()
            
            # 格式化数据
            for item in history:
                if item.get('created_at'):
                    item['created_at'] = item['created_at'].isoformat()
                
                # 格式化操作类型
                operation_type_map = {
                    'start_flow': '启动流转',
                    'submit_to_next': '提交至下一部门',
                    'approve': '审核通过',
                    'reject': '驳回',
                    'skip': '跳过',
                    'complete': '完成流转'
                }
                item['operation_type_text'] = operation_type_map.get(item['operation_type'], item['operation_type'])
            
            # 计算分页信息
            total_pages = (total_count + page_size - 1) // page_size
            has_more = page < total_pages
            
            return jsonify({
                'success': True,
                'data': {
                    'history': history,
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
        return jsonify({'success': False, 'message': f'获取流转历史失败: {str(e)}'}), 500
    finally:
        if 'connection' in locals():
            connection.close()

# 注册蓝图
def register_flow_blueprint(app):
    """注册流转API蓝图"""
    app.register_blueprint(flow_bp)
    print("✅ 部门流转API已注册")
