#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重构流转卡流转逻辑 - 完整方案

本方案彻底重构流转逻辑，确保流转顺序清晰、状态管理准确、无恶性bug。
"""

import pymysql
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config.config import get_db_config

class FlowManager:
    """流转管理器 - 单一职责，管理流转逻辑"""
    
    def __init__(self):
        self.db_config = get_db_config()
        self.db_config['cursorclass'] = pymysql.cursors.DictCursor
    
    def get_connection(self):
        """获取数据库连接"""
        return pymysql.connect(**self.db_config)
    
    def get_template_flow_steps(self, template_id):
        """
        获取模板的流转步骤
        
        返回: 按flow_order排序的部门列表
        [
            {'department_id': 1, 'department_name': '研发部', 'flow_order': 1, 'is_required': True},
            {'department_id': 3, 'department_name': '销售部', 'flow_order': 2, 'is_required': True},
            ...
        ]
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT tdf.department_id, d.name as department_name, 
                           tdf.flow_order, tdf.is_required
                    FROM template_department_flow tdf
                    LEFT JOIN departments d ON tdf.department_id = d.id
                    WHERE tdf.template_id = %s
                    ORDER BY tdf.flow_order
                """, (template_id,))
                return cursor.fetchall()
    
    def get_card_flow_status(self, card_id):
        """
        获取流转卡的流转状态
        
        返回: 按flow_order排序的状态列表
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT cfs.*, d.name as department_name
                    FROM card_flow_status cfs
                    LEFT JOIN departments d ON cfs.department_id = d.id
                    WHERE cfs.card_id = %s
                    ORDER BY cfs.flow_order
                """, (card_id,))
                return cursor.fetchall()
    
    def get_current_step(self, card_id):
        """
        获取流转卡的当前步骤
        
        返回: {
            'flow_order': 2,
            'department_id': 3,
            'department_name': '销售部',
            'is_last': False,
            'total_steps': 3
        }
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # 获取流转卡信息
                cursor.execute("""
                    SELECT tc.template_id, tc.current_department_id
                    FROM transfer_cards tc
                    WHERE tc.id = %s
                """, (card_id,))
                card = cursor.fetchone()
                
                if not card:
                    return None
                
                # 获取模板流转步骤
                steps = self.get_template_flow_steps(card['template_id'])
                total_steps = len(steps)
                
                # 找到当前部门在流转步骤中的位置
                current_step = None
                for i, step in enumerate(steps):
                    if step['department_id'] == card['current_department_id']:
                        current_step = step
                        current_step['is_last'] = (i == total_steps - 1)
                        current_step['total_steps'] = total_steps
                        break
                
                return current_step
    
    def initialize_card_flow(self, card_id, template_id):
        """
        初始化流转卡的流转状态
        
        为流转卡创建所有流转步骤的记录，第一个步骤为processing，其他为pending
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # 获取模板流转步骤
                steps = self.get_template_flow_steps(template_id)
                
                if not steps:
                    raise Exception(f"模板 {template_id} 没有配置流转步骤")
                
                # 删除旧的流转状态记录（如果存在）
                cursor.execute("DELETE FROM card_flow_status WHERE card_id = %s", (card_id,))
                
                # 插入新的流转状态记录
                for i, step in enumerate(steps):
                    status = 'processing' if i == 0 else 'pending'
                    if i == 0:
                        cursor.execute("""
                            INSERT INTO card_flow_status 
                            (card_id, department_id, flow_order, status, started_at)
                            VALUES (%s, %s, %s, %s, NOW())
                        """, (card_id, step['department_id'], step['flow_order'], status))
                    else:
                        cursor.execute("""
                            INSERT INTO card_flow_status 
                            (card_id, department_id, flow_order, status, started_at)
                            VALUES (%s, %s, %s, %s, NULL)
                        """, (card_id, step['department_id'], step['flow_order'], status))
                
                # 更新流转卡的当前部门和流转状态
                cursor.execute("""
                    UPDATE transfer_cards 
                    SET current_department_id = %s,
                        total_flow_steps = %s,
                        completed_flow_steps = 0,
                        flow_started_at = NOW(),
                        status = 'in_progress'
                    WHERE id = %s
                """, (steps[0]['department_id'], len(steps), card_id))
                
                conn.commit()
                return True
    
    def submit_to_next_department(self, card_id, user_id, notes=None):
        """
        提交到下一部门
        
        核心逻辑：
        1. 查找当前处理中的步骤
        2. 将其状态改为completed
        3. 查找下一步骤
        4. 如果有下一步骤，将其状态改为processing，更新流转卡的current_department_id
        5. 如果没有下一步骤，将流转卡状态改为completed
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # 1. 获取流转卡的当前步骤
                current_step = self.get_current_step(card_id)
                
                if not current_step:
                    raise Exception(f"流转卡 {card_id} 的当前步骤不存在")
                
                # 2. 将当前步骤状态改为completed
                cursor.execute("""
                    UPDATE card_flow_status
                    SET status = 'completed',
                        completed_at = NOW(),
                        processed_by = %s,
                        notes = %s
                    WHERE card_id = %s 
                      AND department_id = %s
                      AND status = 'processing'
                """, (user_id, notes, card_id, current_step['department_id']))
                
                # 3. 判断是否为最后步骤
                if current_step['is_last']:
                    # 是最后步骤，完成流转
                    cursor.execute("""
                        UPDATE transfer_cards
                        SET status = 'completed',
                            flow_completed_at = NOW(),
                            completed_flow_steps = total_flow_steps
                        WHERE id = %s
                    """, (card_id,))
                    
                    # 记录操作日志
                    self._log_flow_operation(conn, card_id, None, None, 
                                            'complete', user_id, notes)
                    
                    conn.commit()
                    return {
                        'success': True,
                        'message': '流转已完成',
                        'next_department': None,
                        'is_completed': True
                    }
                else:
                    # 不是最后步骤，流转到下一部门
                    # 查找下一部门
                    next_flow_order = current_step['flow_order'] + 1
                    cursor.execute("""
                        SELECT cfs.*, d.name as department_name
                        FROM card_flow_status cfs
                        LEFT JOIN departments d ON cfs.department_id = d.id
                        WHERE cfs.card_id = %s 
                          AND cfs.flow_order = %s
                    """, (card_id, next_flow_order))
                    
                    next_step = cursor.fetchone()
                    
                    if not next_step:
                        raise Exception(f"找不到流转卡 {card_id} 的下一步骤 (order: {next_flow_order})")
                    
                    # 更新下一步骤状态为processing
                    cursor.execute("""
                        UPDATE card_flow_status
                        SET status = 'processing',
                            started_at = NOW()
                        WHERE card_id = %s 
                          AND flow_order = %s
                    """, (card_id, next_flow_order))
                    
                    # 更新流转卡的当前部门和已完成步骤数
                    cursor.execute("""
                        UPDATE transfer_cards
                        SET current_department_id = %s,
                            completed_flow_steps = completed_flow_steps + 1
                        WHERE id = %s
                    """, (next_step['department_id'], card_id))
                    
                    # 记录操作日志
                    self._log_flow_operation(conn, card_id, 
                                           current_step['department_id'],
                                           next_step['department_id'],
                                           'submit_to_next', user_id, notes)
                    
                    conn.commit()
                    return {
                        'success': True,
                        'message': f'已提交到 {next_step["department_name"]}',
                        'next_department': next_step['department_name'],
                        'is_completed': False
                    }
    
    def _log_flow_operation(self, conn, card_id, from_dept_id, to_dept_id, 
                           operation_type, operator_id, notes):
        """记录流转操作日志"""
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO flow_operation_logs
                (card_id, from_department_id, to_department_id, 
                 operation_type, operator_id, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (card_id, from_dept_id, to_dept_id, 
                 operation_type, operator_id, notes))


def test_refactored_logic():
    """测试重构后的流转逻辑"""
    print("=" * 80)
    print("测试重构后的流转逻辑")
    print("=" * 80)
    
    flow_manager = FlowManager()
    
    # 测试1: 获取模板流转步骤
    print("\n📋 测试1: 获取模板25的流转步骤")
    steps = flow_manager.get_template_flow_steps(25)
    print(f"✅ 找到 {len(steps)} 个流转步骤:")
    for step in steps:
        print(f"   {step['flow_order']}. {step['department_name']}")
    
    # 测试2: 创建测试流转卡并初始化流转
    print("\n📋 测试2: 创建测试流转卡并初始化流转")
    import time
    timestamp = int(time.time())
    with flow_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            # 创建测试流转卡
            cursor.execute("""
                INSERT INTO transfer_cards 
                (card_number, title, template_id, status, created_by)
                VALUES (%s, '测试流转逻辑', 25, 'draft', 1)
            """, (f'TEST_FLOW_{timestamp}',))
            card_id = cursor.lastrowid
            conn.commit()
    
    print(f"✅ 创建测试流转卡: ID={card_id}")
    
    # 初始化流转
    flow_manager.initialize_card_flow(card_id, 25)
    print("✅ 初始化流转状态")
    
    # 检查流转状态
    print("\n📋 测试3: 检查流转状态")
    flow_status = flow_manager.get_card_flow_status(card_id)
    for status in flow_status:
        status_text = "🔄 处理中" if status['status'] == 'processing' else "⏳ 等待中"
        print(f"   {status['flow_order']}. {status['department_name']} - {status_text}")
    
    # 测试4: 提交到下一部门
    print("\n📋 测试4: 提交到下一部门")
    result = flow_manager.submit_to_next_department(card_id, 1, "第一次提交")
    print(f"✅ {result['message']}")
    
    # 检查流转状态
    flow_status = flow_manager.get_card_flow_status(card_id)
    for status in flow_status:
        status_text = "🔄 处理中" if status['status'] == 'processing' else \
                     "⏳ 等待中" if status['status'] == 'pending' else "✅ 已完成"
        print(f"   {status['flow_order']}. {status['department_name']} - {status_text}")
    
    # 测试5: 再次提交
    print("\n📋 测试5: 再次提交到下一部门")
    result = flow_manager.submit_to_next_department(card_id, 1, "第二次提交")
    print(f"✅ {result['message']}")
    
    # 检查流转状态
    flow_status = flow_manager.get_card_flow_status(card_id)
    for status in flow_status:
        status_text = "🔄 处理中" if status['status'] == 'processing' else \
                     "⏳ 等待中" if status['status'] == 'pending' else "✅ 已完成"
        print(f"   {status['flow_order']}. {status['department_name']} - {status_text}")
    
    # 测试6: 完成流转
    print("\n📋 测试6: 完成流转")
    result = flow_manager.submit_to_next_department(card_id, 1, "完成流转")
    print(f"✅ {result['message']}")
    
    # 检查流转状态
    flow_status = flow_manager.get_card_flow_status(card_id)
    for status in flow_status:
        status_text = "✅ 已完成" if status['status'] == 'completed' else status['status']
        print(f"   {status['flow_order']}. {status['department_name']} - {status_text}")
    
    # 检查流转卡状态
    with flow_manager.get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM transfer_cards WHERE id = %s", (card_id,))
            card = cursor.fetchone()
            print(f"\n✅ 转流卡最终状态: {card['status']}")
            print(f"   已完成步骤: {card['completed_flow_steps']}/{card['total_flow_steps']}")
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)


if __name__ == '__main__':
    try:
        test_refactored_logic()
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
