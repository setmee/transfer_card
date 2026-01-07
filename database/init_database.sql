-- ========================================
-- 流转卡系统数据库初始化脚本
-- ========================================
-- 数据库: transfer_card_system
-- 字符集: utf8mb4
-- 排序规则: utf8mb4_unicode_ci
-- 版本: 2.0
-- 更新日期: 2026-01-07
-- ========================================

-- ========================================
-- 第一步：创建数据库
-- ========================================
DROP DATABASE IF EXISTS `transfer_card_system`;
CREATE DATABASE `transfer_card_system` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `transfer_card_system`;

-- ========================================
-- 第二步：创建基础表（无外键依赖）
-- ========================================

-- 1. departments 部门表
CREATE TABLE `departments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL COMMENT '部门名称',
  `description` text COMMENT '部门描述',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部门表';

-- 2. users 用户表
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `username` varchar(50) NOT NULL COMMENT '用户名',
  `password` varchar(255) NOT NULL COMMENT '密码(哈希值)',
  `real_name` varchar(100) DEFAULT NULL COMMENT '真实姓名',
  `email` varchar(100) DEFAULT NULL COMMENT '邮箱',
  `role` enum('admin','user') DEFAULT 'user' COMMENT '角色',
  `department_id` int DEFAULT NULL COMMENT '部门ID',
  `is_active` tinyint(1) DEFAULT 1 COMMENT '是否激活',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `idx_username` (`username`),
  KEY `idx_department` (`department_id`),
  KEY `idx_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 3. fields 字段定义表
CREATE TABLE `fields` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL COMMENT '字段名称(英文)',
  `display_name` varchar(100) NOT NULL COMMENT '字段显示名称',
  `field_type` enum('text','number','date','select','boolean') DEFAULT 'text' COMMENT '字段类型',
  `department_id` int DEFAULT NULL COMMENT '负责部门ID',
  `department_name` varchar(100) DEFAULT NULL COMMENT '负责部门名称',
  `category` varchar(100) DEFAULT NULL COMMENT '字段分类',
  `validation_rules` text COMMENT '验证规则',
  `options` text COMMENT '选项(JSON格式，用于select类型)',
  `is_required` tinyint(1) DEFAULT 0 COMMENT '是否必填',
  `is_hidden` tinyint(1) DEFAULT 0 COMMENT '是否隐藏(价格敏感字段)',
  `field_position` int DEFAULT 0 COMMENT '字段位置(1-50)',
  `is_placeholder` tinyint(1) DEFAULT 0 COMMENT '是否为占位字段',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  KEY `idx_name` (`name`),
  KEY `idx_department` (`department_id`),
  KEY `idx_category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='字段定义表';

-- ========================================
-- 第三步：创建业务表（有外键依赖）
-- ========================================

-- 4. templates 模板表
CREATE TABLE `templates` (
  `id` int NOT NULL AUTO_INCREMENT,
  `template_name` varchar(200) NOT NULL COMMENT '模板名称',
  `template_description` text COMMENT '模板描述',
  `department_id` int DEFAULT NULL COMMENT '适用部门ID',
  `created_by` int NOT NULL COMMENT '创建者ID',
  `is_active` tinyint(1) DEFAULT 1 COMMENT '是否启用',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_name` (`template_name`),
  KEY `idx_department` (`department_id`),
  KEY `idx_creator` (`created_by`),
  KEY `idx_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模板表';

-- 5. template_snapshots 模板快照表
CREATE TABLE `template_snapshots` (
  `id` int NOT NULL AUTO_INCREMENT,
  `template_id` int DEFAULT NULL COMMENT '模板ID',
  `snapshot_id` varchar(50) NOT NULL COMMENT '快照ID（自动生成唯一值）',
  `template_name` varchar(100) NOT NULL COMMENT '模板名称（快照时保存）',
  `department_id` int NOT NULL COMMENT '部门ID',
  `is_active` tinyint(1) DEFAULT 1 COMMENT '是否激活',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `snapshot_id` (`snapshot_id`),
  KEY `idx_template_id` (`template_id`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模板快照表';

-- 6. transfer_cards 流转卡主表
CREATE TABLE `transfer_cards` (
  `id` int NOT NULL AUTO_INCREMENT,
  `card_number` varchar(50) NOT NULL COMMENT '流转卡编号',
  `template_id` int DEFAULT NULL COMMENT '模板ID',
  `snapshot_id` varchar(50) DEFAULT NULL COMMENT '模板快照ID',
  `title` varchar(200) DEFAULT NULL COMMENT '流转卡标题',
  `description` text COMMENT '流转卡描述',
  `status` enum('draft','in_progress','flowing','completed','cancelled','rejected') DEFAULT 'draft' COMMENT '状态',
  `created_by` int NOT NULL COMMENT '创建者ID',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `current_department_id` int DEFAULT NULL COMMENT '当前流转部门ID',
  `flow_started_at` timestamp NULL DEFAULT NULL COMMENT '流转开始时间',
  `flow_completed_at` timestamp NULL DEFAULT NULL COMMENT '流转完成时间',
  `total_flow_steps` int DEFAULT 0 COMMENT '总流转步骤数',
  `completed_flow_steps` int DEFAULT 0 COMMENT '已完成流转步骤数',
  PRIMARY KEY (`id`),
  UNIQUE KEY `card_number` (`card_number`),
  KEY `idx_number` (`card_number`),
  KEY `idx_status` (`status`),
  KEY `idx_creator` (`created_by`),
  KEY `idx_template` (`template_id`),
  KEY `idx_snapshot` (`snapshot_id`),
  KEY `idx_current_department` (`current_department_id`),
  KEY `idx_transfer_cards_status_dept` (`status`,`current_department_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='流转卡主表';

-- 7. card_data 流转卡数据表
CREATE TABLE `card_data` (
  `id` int NOT NULL AUTO_INCREMENT,
  `card_id` int NOT NULL COMMENT '流转卡ID',
  `row_number` int NOT NULL COMMENT '行号（从1开始）',
  `department_id` int DEFAULT NULL COMMENT '负责部门ID',
  `status` enum('draft','submitted','approved') DEFAULT 'draft' COMMENT '状态',
  `submitted_by` int DEFAULT NULL COMMENT '提交人ID',
  `submitted_at` timestamp NULL DEFAULT NULL COMMENT '提交时间',
  `approved_by` int DEFAULT NULL COMMENT '审批人ID',
  `approved_at` timestamp NULL DEFAULT NULL COMMENT '审批时间',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `field_01_pcs_project` text COMMENT 'PCS项目',
  `field_02_spec_model` text COMMENT '规格型号',
  `field_03_manufacturer` text COMMENT '制造商',
  `field_04_manufacturer_desc` text COMMENT '制造商说明',
  `field_05_origin_country` text COMMENT '原产国',
  `field_06_origin_country_cn` text COMMENT '原产国中文名称',
  `field_07_material_desc` text COMMENT '物料说明',
  `field_08_stock_unit` text COMMENT '库存单位',
  `field_09_material_group` text COMMENT '物料组',
  `field_10_material_group_desc` text COMMENT '物料组说明',
  `field_11_material_group2` text COMMENT '物料组二',
  `field_12_material_group2_desc` text COMMENT '物料组二说明',
  `field_13_product_type` text COMMENT '产品类型',
  `field_14_product_type_desc` text COMMENT '产品类型说明',
  `field_15_product_category` text COMMENT '产品大类',
  `field_16_product_category_desc` text COMMENT '产品大类说明',
  `field_17_product_classification` text COMMENT '产品分类',
  `field_18_product_classification_desc` text COMMENT '产品分类说明',
  `field_19_weight` decimal(10,4) DEFAULT NULL COMMENT '重量',
  `field_20_special_part` text COMMENT '专用件',
  `field_21_batch_control` text COMMENT '批次控制',
  `field_22_material_signal` text COMMENT '物料信号',
  `field_23_effective_date` date DEFAULT NULL COMMENT '生效日期',
  `field_24_expiry_date` date DEFAULT NULL COMMENT '失效日期',
  `field_25` text COMMENT '预留字段25',
  `field_26` text COMMENT '预留字段26',
  `field_27` text COMMENT '预留字段27',
  `field_28` text COMMENT '预留字段28',
  `field_29` text COMMENT '预留字段29',
  `field_30` text COMMENT '预留字段30',
  `field_31` text COMMENT '预留字段31',
  `field_32` text COMMENT '预留字段32',
  `field_33` text COMMENT '预留字段33',
  `field_34` text COMMENT '预留字段34',
  `field_35` text COMMENT '预留字段35',
  `field_36` text COMMENT '预留字段36',
  `field_37` text COMMENT '预留字段37',
  `field_38` text COMMENT '预留字段38',
  `field_39` text COMMENT '预留字段39',
  `field_40` text COMMENT '预留字段40',
  `field_41` text COMMENT '预留字段41',
  `field_42` text COMMENT '预留字段42',
  `field_43` text COMMENT '预留字段43',
  `field_44` text COMMENT '预留字段44',
  `field_45` text COMMENT '预留字段45',
  `field_46` text COMMENT '预留字段46',
  `field_47` text COMMENT '预留字段47',
  `field_48` text COMMENT '预留字段48',
  `field_49` text COMMENT '预留字段49',
  `field_50` text COMMENT '预留字段50',
  `version` int DEFAULT 1 COMMENT '数据版本号，用于乐观锁',
  `last_updated_by` int DEFAULT NULL COMMENT '最后修改人ID',
  `last_updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后修改时间',
  `flow_step_id` int DEFAULT NULL COMMENT '流转步骤ID',
  `approval_notes` text COMMENT '审批备注',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_card_row` (`card_id`,`row_number`),
  KEY `idx_card_id` (`card_id`),
  KEY `idx_status` (`status`),
  KEY `idx_department` (`department_id`),
  KEY `idx_card_data_version` (`card_id`,`version`),
  KEY `fk_data_submitted_by` (`submitted_by`),
  KEY `fk_data_approved_by` (`approved_by`),
  KEY `fk_data_last_updated_by` (`last_updated_by`),
  KEY `idx_card_data_card_status` (`card_id`,`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='流转卡数据表';

-- 8. card_field_values 流转卡字段值表
CREATE TABLE `card_field_values` (
  `id` int NOT NULL AUTO_INCREMENT,
  `card_id` int NOT NULL COMMENT '流转卡ID',
  `field_name` varchar(100) NOT NULL COMMENT '字段名称',
  `field_value` text COMMENT '字段值',
  `field_type` varchar(50) DEFAULT NULL COMMENT '字段类型',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_card_field` (`card_id`,`field_name`),
  KEY `idx_card` (`card_id`),
  KEY `idx_field` (`field_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='流转卡字段值表';

-- 9. card_flow_status 流转卡流转状态表
CREATE TABLE `card_flow_status` (
  `id` int NOT NULL AUTO_INCREMENT,
  `card_id` int NOT NULL COMMENT '流转卡ID',
  `department_id` int NOT NULL COMMENT '部门ID',
  `flow_order` int NOT NULL COMMENT '流转顺序',
  `status` enum('pending','processing','completed','skipped') DEFAULT 'pending' COMMENT '流转状态',
  `started_at` timestamp NULL DEFAULT NULL COMMENT '开始处理时间',
  `completed_at` timestamp NULL DEFAULT NULL COMMENT '完成时间',
  `processed_by` int DEFAULT NULL COMMENT '处理人ID',
  `notes` text COMMENT '处理备注',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_card_department` (`card_id`,`department_id`),
  KEY `processed_by` (`processed_by`),
  KEY `idx_card` (`card_id`),
  KEY `idx_department` (`department_id`),
  KEY `idx_flow_order` (`card_id`,`flow_order`),
  KEY `idx_status` (`status`),
  KEY `idx_card_flow_status_card_order` (`card_id`,`flow_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='流转卡流转状态表';

-- 10. department_field_permissions 部门字段权限表
CREATE TABLE `department_field_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `department_id` int NOT NULL COMMENT '部门ID',
  `field_id` int NOT NULL COMMENT '字段ID',
  `can_read` tinyint(1) DEFAULT 1 COMMENT '是否可读',
  `can_write` tinyint(1) DEFAULT 1 COMMENT '是否可写',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_dept_field` (`department_id`,`field_id`),
  KEY `idx_department` (`department_id`),
  KEY `idx_field` (`field_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部门字段权限表';

-- 11. template_fields 模板字段关联表
CREATE TABLE `template_fields` (
  `id` int NOT NULL AUTO_INCREMENT,
  `template_id` int DEFAULT NULL COMMENT '模板ID',
  `field_id` int DEFAULT NULL COMMENT '字段ID',
  `field_name` varchar(100) NOT NULL COMMENT '字段名称(冗余字段)',
  `field_display_name` varchar(100) NOT NULL COMMENT '字段显示名称(冗余字段)',
  `field_type` enum('text','number','date','select','boolean') DEFAULT 'text' COMMENT '字段类型(冗余字段)',
  `field_order` int DEFAULT 1 COMMENT '字段排序',
  `is_required` tinyint(1) DEFAULT 0 COMMENT '是否必填',
  `default_value` text COMMENT '默认值',
  `options` text COMMENT '选项(JSON格式，冗余字段)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_template` (`template_id`),
  KEY `idx_field` (`field_id`),
  KEY `idx_order` (`field_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模板字段关联表';

-- 12. template_department_flow 模板部门流转顺序表
CREATE TABLE `template_department_flow` (
  `id` int NOT NULL AUTO_INCREMENT,
  `template_id` int DEFAULT NULL COMMENT '模板ID',
  `department_id` int NOT NULL COMMENT '部门ID',
  `flow_order` int NOT NULL COMMENT '流转顺序',
  `is_required` tinyint(1) DEFAULT 1 COMMENT '是否必须部门',
  `auto_skip` tinyint(1) DEFAULT 0 COMMENT '是否自动跳过(无数据时)',
  `timeout_hours` int DEFAULT 24 COMMENT '超时时间(小时)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `department_id` (`department_id`),
  KEY `idx_template` (`template_id`),
  KEY `idx_flow_order` (`template_id`,`flow_order`),
  KEY `idx_template_dept_flow_template_order` (`template_id`,`flow_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模板部门流转顺序表';

-- 13. template_field_permissions 模板字段权限表
CREATE TABLE `template_field_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `template_id` int DEFAULT NULL COMMENT '模板ID',
  `field_name` varchar(100) NOT NULL COMMENT '字段名称',
  `department_id` int NOT NULL COMMENT '部门ID',
  `can_read` tinyint(1) DEFAULT 1 COMMENT '是否可读',
  `can_write` tinyint(1) DEFAULT 1 COMMENT '是否可写',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_template` (`template_id`),
  KEY `idx_field` (`field_name`),
  KEY `idx_department` (`department_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模板字段权限表';

-- 14. operation_logs 操作日志表
CREATE TABLE `operation_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL COMMENT '用户ID',
  `operation_type` varchar(50) NOT NULL COMMENT '操作类型',
  `target_type` varchar(50) DEFAULT NULL COMMENT '目标类型',
  `target_id` int DEFAULT NULL COMMENT '目标ID',
  `description` text COMMENT '操作描述',
  `old_data` json DEFAULT NULL COMMENT '旧数据',
  `new_data` json DEFAULT NULL COMMENT '新数据',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `user_name` varchar(100) DEFAULT NULL COMMENT '用户名(冗余字段)',
  `department_name` varchar(100) DEFAULT NULL COMMENT '部门名称(冗余字段)',
  `ip_address` varchar(45) DEFAULT NULL COMMENT 'IP地址',
  `user_agent` text COMMENT '用户代理',
  PRIMARY KEY (`id`),
  KEY `idx_user` (`user_id`),
  KEY `idx_operation` (`operation_type`),
  KEY `idx_target` (`target_type`,`target_id`),
  KEY `idx_created` (`created_at`),
  KEY `idx_operation_logs_user_created` (`user_id`,`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- 15. flow_operation_logs 流转操作日志表
CREATE TABLE `flow_operation_logs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `card_id` int NOT NULL COMMENT '流转卡ID',
  `from_department_id` int DEFAULT NULL COMMENT '来源部门ID',
  `to_department_id` int DEFAULT NULL COMMENT '目标部门ID',
  `operation_type` enum('start_flow','submit_to_next','approve','reject','skip','complete') NOT NULL COMMENT '操作类型',
  `operator_id` int NOT NULL COMMENT '操作人ID',
  `notes` text COMMENT '操作备注',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `from_department_id` (`from_department_id`),
  KEY `to_department_id` (`to_department_id`),
  KEY `idx_card` (`card_id`),
  KEY `idx_operator` (`operator_id`),
  KEY `idx_operation_type` (`operation_type`),
  KEY `idx_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='流转操作日志表';

-- 16. card_template_fields 流转卡模板快照字段表
CREATE TABLE `card_template_fields` (
  `id` int NOT NULL AUTO_INCREMENT,
  `card_id` int NOT NULL COMMENT '流转卡ID',
  `field_name` varchar(100) NOT NULL COMMENT '字段名称',
  `field_display_name` varchar(100) NOT NULL COMMENT '字段显示名称',
  `field_type` enum('text','number','date','select','boolean') DEFAULT 'text' COMMENT '字段类型',
  `field_order` int DEFAULT 1 COMMENT '字段排序',
  `is_required` tinyint(1) DEFAULT 0 COMMENT '是否必填',
  `default_value` text COMMENT '默认值',
  `options` text COMMENT '选项(JSON格式)',
  `department_id` int DEFAULT NULL COMMENT '负责部门ID',
  `department_name` varchar(100) DEFAULT NULL COMMENT '负责部门名称',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_card_field_order` (`card_id`,`field_order`),
  KEY `idx_card` (`card_id`),
  KEY `idx_field` (`field_name`),
  KEY `idx_order` (`field_order`),
  KEY `idx_department` (`department_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='流转卡模板快照字段表';

-- 17. card_department_flow 流转卡模板快照部门流转顺序表
CREATE TABLE `card_department_flow` (
  `id` int NOT NULL AUTO_INCREMENT,
  `card_id` int NOT NULL COMMENT '流转卡ID',
  `department_id` int NOT NULL COMMENT '部门ID',
  `flow_order` int NOT NULL COMMENT '流转顺序',
  `is_required` tinyint(1) DEFAULT 1 COMMENT '是否必须部门',
  `auto_skip` tinyint(1) DEFAULT 0 COMMENT '是否自动跳过(无数据时)',
  `timeout_hours` int DEFAULT 24 COMMENT '超时时间(小时)',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_card_department` (`card_id`,`department_id`),
  KEY `idx_card` (`card_id`),
  KEY `idx_department` (`department_id`),
  KEY `idx_flow_order` (`card_id`,`flow_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='流转卡模板快照部门流转顺序表';

-- 18. card_field_permissions 流转卡模板快照字段权限表
CREATE TABLE `card_field_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `card_id` int NOT NULL COMMENT '流转卡ID',
  `field_name` varchar(100) NOT NULL COMMENT '字段名称',
  `department_id` int NOT NULL COMMENT '部门ID',
  `can_read` tinyint(1) DEFAULT 1 COMMENT '是否可读',
  `can_write` tinyint(1) DEFAULT 1 COMMENT '是否可写',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_card_field_dept` (`card_id`,`field_name`,`department_id`),
  KEY `idx_card` (`card_id`),
  KEY `idx_field` (`field_name`),
  KEY `idx_department` (`department_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='流转卡模板快照字段权限表';

-- ========================================
-- 第四步：创建视图
-- ========================================

-- 19. card_flow_history 流转卡流转历史视图
CREATE VIEW `card_flow_history` AS
SELECT 
  `tc`.`id` AS `card_id`,
  `tc`.`card_number` AS `card_number`,
  `tc`.`title` AS `title`,
  `d`.`name` AS `department_name`,
  `cfs`.`flow_order` AS `flow_order`,
  `cfs`.`status` AS `flow_status`,
  `cfs`.`started_at` AS `started_at`,
  `cfs`.`completed_at` AS `completed_at`,
  `u`.`username` AS `processed_by_name`,
  `cfs`.`notes` AS `notes`,
  CASE 
    WHEN (`cfs`.`status` = 'pending') THEN '待处理'
    WHEN (`cfs`.`status` = 'processing') THEN '处理中'
    WHEN (`cfs`.`status` = 'completed') THEN '已完成'
    WHEN (`cfs`.`status` = 'skipped') THEN '已跳过'
    ELSE '未知'
  END AS `flow_status_text`
FROM (((`transfer_cards` `tc`
  JOIN `card_flow_status` `cfs` ON ((`tc`.`id` = `cfs`.`card_id`)))
  JOIN `departments` `d` ON ((`cfs`.`department_id` = `d`.`id`)))
  LEFT JOIN `users` `u` ON ((`cfs`.`processed_by` = `u`.`id`)))
ORDER BY `tc`.`id`, `cfs`.`flow_order`;

-- ========================================
-- 第五步：添加外键约束（避免循环依赖）
-- ========================================

-- 添加外键：users.department_id -> departments.id
ALTER TABLE `users` 
ADD CONSTRAINT `users_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE SET NULL;

-- 添加外键：fields.department_id -> departments.id
ALTER TABLE `fields` 
ADD CONSTRAINT `fields_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE SET NULL;

-- 添加外键：templates.department_id -> departments.id
ALTER TABLE `templates` 
ADD CONSTRAINT `templates_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE SET NULL;

-- 添加外键：templates.created_by -> users.id
ALTER TABLE `templates` 
ADD CONSTRAINT `templates_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE CASCADE;

-- 添加外键：template_snapshots.template_id -> templates.id
ALTER TABLE `template_snapshots` 
ADD CONSTRAINT `template_snapshots_ibfk_1` FOREIGN KEY (`template_id`) REFERENCES `templates` (`id`) ON DELETE SET NULL;

-- 添加外键：transfer_cards.template_id -> templates.id
ALTER TABLE `transfer_cards` 
ADD CONSTRAINT `transfer_cards_ibfk_1` FOREIGN KEY (`template_id`) REFERENCES `templates` (`id`) ON DELETE SET NULL;

-- 添加外键：transfer_cards.created_by -> users.id
ALTER TABLE `transfer_cards` 
ADD CONSTRAINT `transfer_cards_ibfk_2` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE CASCADE;

-- 添加外键：transfer_cards.snapshot_id -> template_snapshots.snapshot_id
ALTER TABLE `transfer_cards` 
ADD CONSTRAINT `transfer_cards_ibfk_3` FOREIGN KEY (`snapshot_id`) REFERENCES `template_snapshots` (`snapshot_id`) ON DELETE SET NULL;

-- 添加外键：transfer_cards.current_department_id -> departments.id
ALTER TABLE `transfer_cards` 
ADD CONSTRAINT `fk_current_department` FOREIGN KEY (`current_department_id`) REFERENCES `departments` (`id`) ON DELETE SET NULL;

-- 添加外键：card_data.card_id -> transfer_cards.id
ALTER TABLE `card_data` 
ADD CONSTRAINT `fk_data_card` FOREIGN KEY (`card_id`) REFERENCES `transfer_cards` (`id`) ON DELETE CASCADE;

-- 添加外键：card_data.department_id -> departments.id
ALTER TABLE `card_data` 
ADD CONSTRAINT `fk_data_department` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE SET NULL;

-- 添加外键：card_data.submitted_by -> users.id
ALTER TABLE `card_data` 
ADD CONSTRAINT `fk_data_submitted_by` FOREIGN KEY (`submitted_by`) REFERENCES `users` (`id`) ON DELETE SET NULL;

-- 添加外键：card_data.approved_by -> users.id
ALTER TABLE `card_data` 
ADD CONSTRAINT `fk_data_approved_by` FOREIGN KEY (`approved_by`) REFERENCES `users` (`id`) ON DELETE SET NULL;

-- 添加外键：card_data.last_updated_by -> users.id
ALTER TABLE `card_data` 
ADD CONSTRAINT `fk_data_last_updated_by` FOREIGN KEY (`last_updated_by`) REFERENCES `users` (`id`) ON DELETE SET NULL;

-- 添加外键：card_field_values.card_id -> transfer_cards.id
ALTER TABLE `card_field_values` 
ADD CONSTRAINT `card_field_values_ibfk_1` FOREIGN KEY (`card_id`) REFERENCES `transfer_cards` (`id`) ON DELETE CASCADE;

-- 添加外键：card_flow_status.card_id -> transfer_cards.id
ALTER TABLE `card_flow_status` 
ADD CONSTRAINT `card_flow_status_ibfk_1` FOREIGN KEY (`card_id`) REFERENCES `transfer_cards` (`id`) ON DELETE CASCADE;

-- 添加外键：card_flow_status.department_id -> departments.id
ALTER TABLE `card_flow_status` 
ADD CONSTRAINT `card_flow_status_ibfk_2` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE CASCADE;

-- 添加外键：card_flow_status.processed_by -> users.id
ALTER TABLE `card_flow_status` 
ADD CONSTRAINT `card_flow_status_ibfk_3` FOREIGN KEY (`processed_by`) REFERENCES `users` (`id`) ON DELETE SET NULL;

-- 添加外键：department_field_permissions.department_id -> departments.id
ALTER TABLE `department_field_permissions` 
ADD CONSTRAINT `department_field_permissions_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE CASCADE;

-- 添加外键：department_field_permissions.field_id -> fields.id
ALTER TABLE `department_field_permissions` 
ADD CONSTRAINT `department_field_permissions_ibfk_2` FOREIGN KEY (`field_id`) REFERENCES `fields` (`id`) ON DELETE CASCADE;

-- 添加外键：template_fields.template_id -> templates.id
ALTER TABLE `template_fields` 
ADD CONSTRAINT `template_fields_ibfk_1` FOREIGN KEY (`template_id`) REFERENCES `templates` (`id`) ON DELETE CASCADE;

-- 添加外键：template_fields.field_id -> fields.id
ALTER TABLE `template_fields` 
ADD CONSTRAINT `template_fields_ibfk_2` FOREIGN KEY (`field_id`) REFERENCES `fields` (`id`) ON DELETE CASCADE;

-- 添加外键：template_department_flow.template_id -> templates.id
ALTER TABLE `template_department_flow` 
ADD CONSTRAINT `template_department_flow_ibfk_1` FOREIGN KEY (`template_id`) REFERENCES `templates` (`id`) ON DELETE CASCADE;

-- 添加外键：template_department_flow.department_id -> departments.id
ALTER TABLE `template_department_flow` 
ADD CONSTRAINT `template_department_flow_ibfk_2` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE CASCADE;

-- 添加外键：template_field_permissions.template_id -> templates.id
ALTER TABLE `template_field_permissions` 
ADD CONSTRAINT `template_field_permissions_ibfk_1` FOREIGN KEY (`template_id`) REFERENCES `templates` (`id`) ON DELETE CASCADE;

-- 添加外键：template_field_permissions.department_id -> departments.id
ALTER TABLE `template_field_permissions` 
ADD CONSTRAINT `template_field_permissions_ibfk_2` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE CASCADE;

-- 添加外键：operation_logs.user_id -> users.id
ALTER TABLE `operation_logs` 
ADD CONSTRAINT `operation_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

-- 添加外键：flow_operation_logs.card_id -> transfer_cards.id
ALTER TABLE `flow_operation_logs` 
ADD CONSTRAINT `flow_operation_logs_ibfk_1` FOREIGN KEY (`card_id`) REFERENCES `transfer_cards` (`id`) ON DELETE CASCADE;

-- 添加外键：flow_operation_logs.from_department_id -> departments.id
ALTER TABLE `flow_operation_logs` 
ADD CONSTRAINT `flow_operation_logs_ibfk_2` FOREIGN KEY (`from_department_id`) REFERENCES `departments` (`id`) ON DELETE SET NULL;

-- 添加外键：flow_operation_logs.to_department_id -> departments.id
ALTER TABLE `flow_operation_logs` 
ADD CONSTRAINT `flow_operation_logs_ibfk_3` FOREIGN KEY (`to_department_id`) REFERENCES `departments` (`id`) ON DELETE SET NULL;

-- 添加外键：flow_operation_logs.operator_id -> users.id
ALTER TABLE `flow_operation_logs` 
ADD CONSTRAINT `flow_operation_logs_ibfk_4` FOREIGN KEY (`operator_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

-- 添加外键：card_template_fields.card_id -> transfer_cards.id
ALTER TABLE `card_template_fields` 
ADD CONSTRAINT `card_template_fields_ibfk_1` FOREIGN KEY (`card_id`) REFERENCES `transfer_cards` (`id`) ON DELETE CASCADE;

-- 添加外键：card_department_flow.card_id -> transfer_cards.id
ALTER TABLE `card_department_flow` 
ADD CONSTRAINT `card_department_flow_ibfk_1` FOREIGN KEY (`card_id`) REFERENCES `transfer_cards` (`id`) ON DELETE CASCADE;

-- 添加外键：card_department_flow.department_id -> departments.id
ALTER TABLE `card_department_flow` 
ADD CONSTRAINT `card_department_flow_ibfk_2` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE CASCADE;

-- 添加外键：card_field_permissions.card_id -> transfer_cards.id
ALTER TABLE `card_field_permissions` 
ADD CONSTRAINT `card_field_permissions_ibfk_1` FOREIGN KEY (`card_id`) REFERENCES `transfer_cards` (`id`) ON DELETE CASCADE;

-- 添加外键：card_field_permissions.department_id -> departments.id
ALTER TABLE `card_field_permissions` 
ADD CONSTRAINT `card_field_permissions_ibfk_2` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE CASCADE;

-- ========================================
-- 完成
-- ========================================
-- 数据库初始化完成！
-- 说明：
-- 1. 本脚本会删除并重建数据库 transfer_card_system
-- 2. 所有表结构都与实际生产环境完全一致
-- 3. 外键约束已正确添加
-- 4. 支持模板快照功能，删除模板不会影响已创建的流转卡
-- ========================================
