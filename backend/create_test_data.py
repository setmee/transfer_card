#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建测试数据脚本
用于测试流转卡编辑功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Department, Field, Template, TemplateField, TemplateCard, CardData
import json
from datetime import datetime

def create_test_data():
    """创建测试数据"""
    app = create_app()
    
    with app.app_context():
        print("🚀 开始创建测试数据...")
        
        # 1. 确保部门存在
        departments = [
            {'name': '研发部', 'description': '负责产品研发'},
            {'name': '采购部', 'description': '负责物料采购'},
            {'name': '生产部', 'description': '负责生产制造'},
            {'name': '质检部', 'description': '负责质量检验'},
            {'name': '仓库部', 'description': '负责仓储管理'}
        ]
        
        for dept_data in departments:
            dept = Department.query.filter_by(name=dept_data['name']).first()
            if not dept:
                dept = Department(**dept_data)
                db.session.add(dept)
                print(f"✅ 创建部门: {dept_data['name']}")
        
        db.session.commit()
        
        # 2. 确保字段存在
        fields_data = [
            {'name': 'field_001', 'display_name': '物料名称', 'field_type': 'text', 'department_name': '采购部', 'is_required': True},
            {'name': 'field_002', 'display_name': '物料编码', 'field_type': 'text', 'department_name': '采购部', 'is_required': True},
            {'name': 'field_003', 'display_name': '数量', 'field_type': 'number', 'department_name': '仓库部', 'is_required': True},
            {'name': 'field_004', 'display_name': '单价', 'field_type': 'number', 'department_name': '采购部', 'is_required': False},
            {'name': 'field_005', 'display_name': '供应商', 'field_type': 'text', 'department_name': '采购部', 'is_required': False},
            {'name': 'field_006', 'display_name': '生产日期', 'field_type': 'date', 'department_name': '生产部', 'is_required': False},
            {'name': 'field_007', 'display_name': '质检结果', 'field_type': 'select', 'department_name': '质检部', 'is_required': False, 'options': '["合格", "不合格", "待检"]'},
            {'name': 'field_008', 'display_name': '入库状态', 'field_type': 'boolean', 'department_name': '仓库部', 'is_required': False},
        ]
        
        for field_data in fields_data:
            field = Field.query.filter_by(name=field_data['name']).first()
            if not field:
                field = Field(**field_data)
                db.session.add(field)
                print(f"✅ 创建字段: {field_data['display_name']}")
        
        db.session.commit()
        
        # 3. 确保模板存在
        template = Template.query.filter_by(template_name='生产流转卡测试').first()
        if not template:
            template = Template(
                template_name='生产流转卡测试',
                template_description='用于测试的生产流转卡模板',
                is_active=True,
                created_by=1  # 假设管理员ID为1
            )
            db.session.add(template)
            db.session.flush()  # 获取模板ID
            print(f"✅ 创建模板: 生产流转卡测试")
        
        # 4. 为模板添加字段
        existing_fields = TemplateField.query.filter_by(template_id=template.id).all()
        if not existing_fields:
            fields = Field.query.filter(Field.name.like('field_%')).limit(5).all()
            for i, field in enumerate(fields):
                template_field = TemplateField(
                    template_id=template.id,
                    field_name=field.name,
                    field_order=i + 1,
                    is_required=field.is_required if i < 3 else False,  # 前3个字段设为必填
                    default_value=''
                )
                db.session.add(template_field)
                print(f"✅ 添加模板字段: {field.display_name}")
        
        db.session.commit()
        
        # 5. 创建测试流转卡
        test_card = TemplateCard.query.filter_by(card_number='TC20251201001').first()
        if not test_card:
            test_card = TemplateCard(
                template_id=template.id,
                card_number='TC20251201001',
                title='测试生产流转卡',
                description='这是一个用于测试的流转卡',
                row_count=3,
                responsible_person='测试用户',
                create_date=datetime.now(),
                status='draft',
                created_by=1
            )
            db.session.add(test_card)
            db.session.flush()  # 获取流转卡ID
            print(f"✅ 创建流转卡: TC20251201001")
        
        # 6. 为流转卡添加测试数据
        existing_data = CardData.query.filter_by(card_id=test_card.id).all()
        if not existing_data:
            template_fields = TemplateField.query.filter_by(template_id=template.id).all()
            
            for row_index in range(3):  # 创建3行数据
                for field_order, template_field in enumerate(template_fields):
                    field = Field.query.filter_by(name=template_field.field_name).first()
                    if field:
                        # 根据字段类型生成测试数据
                        if field.field_type == 'text':
                            value = f"测试数据_{row_index+1}_{field_order+1}" if row_index == 0 else f"数据_{row_index+1}"
                        elif field.field_type == 'number':
                            value = (row_index + 1) * 10 + field_order
                        elif field.field_type == 'date':
                            value = datetime.now().date()
                        elif field.field_type == 'select':
                            options = json.loads(field.options or '[]')
                            value = options[0] if options else '合格'
                        elif field.field_type == 'boolean':
                            value = row_index % 2 == 0
                        else:
                            value = ''
                        
                        card_data = CardData(
                            card_id=test_card.id,
                            row_number=row_index + 1,
                            field_name=field.name,
                            field_value=str(value) if isinstance(value, (datetime, bool)) else value
                        )
                        db.session.add(card_data)
            
            print(f"✅ 创建测试数据: 3行 x {len(template_fields)}个字段")
        
        db.session.commit()
        
        print("\n🎉 测试数据创建完成！")
        print("\n📋 测试账号信息:")
        print("管理员: admin / admin123")
        print("普通用户: user1 / password123 (研发部)")
        print("普通用户: user2 / password123 (采购部)")
        print("\n🔧 测试步骤:")
        print("1. 登录系统")
        print("2. 进入 '流转卡管理' 页面")
        print("3. 找到流转卡 'TC20251201001'")
        print("4. 点击 '填写数据' 按钮")
        print("5. 应该可以看到可编辑的输入框")

if __name__ == '__main__':
    create_test_data()
