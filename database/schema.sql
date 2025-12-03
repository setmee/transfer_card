-- 流转卡系统数据库结构
-- 创建时间: 2024-01-01
-- 字符集: utf8mb4
-- 排序规则: utf8mb4_unicode_ci

-- 部门表
CREATE TABLE departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE COMMENT '部门名称',
    description TEXT COMMENT '部门描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='部门表';

-- 用户表
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码(哈希值)',
    real_name VARCHAR(100) COMMENT '真实姓名',
    email VARCHAR(100) COMMENT '邮箱',
    role ENUM('admin', 'user') DEFAULT 'user' COMMENT '角色',
    department_id INT NULL COMMENT '部门ID',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
    INDEX idx_username (username),
    INDEX idx_department (department_id),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 字段定义表 (包含24个指定字段 + 26个占位字段)
CREATE TABLE fields (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE COMMENT '字段名称(英文)',
    display_name VARCHAR(100) NOT NULL COMMENT '字段显示名称',
    field_type ENUM('text', 'number', 'date', 'select', 'boolean') DEFAULT 'text' COMMENT '字段类型',
    department_id INT NULL COMMENT '负责部门ID',
    department_name VARCHAR(100) COMMENT '负责部门名称',
    category VARCHAR(100) COMMENT '字段分类',
    validation_rules TEXT COMMENT '验证规则',
    options TEXT COMMENT '选项(JSON格式，用于select类型)',
    is_required BOOLEAN DEFAULT FALSE COMMENT '是否必填',
    is_hidden BOOLEAN DEFAULT FALSE COMMENT '是否隐藏(价格敏感字段)',
    field_position INT DEFAULT 0 COMMENT '字段位置(1-50)',
    is_placeholder BOOLEAN DEFAULT FALSE COMMENT '是否为占位字段',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
    INDEX idx_name (name),
    INDEX idx_department (department_id),
    INDEX idx_category (category),
    INDEX idx_position (field_position)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='字段定义表';

-- 模板表
CREATE TABLE templates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_name VARCHAR(200) NOT NULL COMMENT '模板名称',
    template_description TEXT COMMENT '模板描述',
    department_id INT NULL COMMENT '适用部门ID',
    created_by INT NOT NULL COMMENT '创建者ID',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_name (template_name),
    INDEX idx_department (department_id),
    INDEX idx_creator (created_by),
    INDEX idx_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模板表';

-- 模板字段关联表
CREATE TABLE template_fields (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_id INT NOT NULL COMMENT '模板ID',
    field_id INT NOT NULL COMMENT '字段ID',
    field_name VARCHAR(100) NOT NULL COMMENT '字段名称(冗余字段)',
    field_display_name VARCHAR(100) NOT NULL COMMENT '字段显示名称(冗余字段)',
    field_type ENUM('text', 'number', 'date', 'select', 'boolean') DEFAULT 'text' COMMENT '字段类型(冗余字段)',
    field_position INT NOT NULL COMMENT '字段在模板中的位置(1-50)',
    is_required BOOLEAN DEFAULT FALSE COMMENT '是否必填',
    default_value TEXT COMMENT '默认值',
    options TEXT COMMENT '选项(JSON格式，冗余字段)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE,
    FOREIGN KEY (field_id) REFERENCES fields(id) ON DELETE CASCADE,
    UNIQUE KEY uk_template_field_position (template_id, field_position),
    INDEX idx_template (template_id),
    INDEX idx_field (field_id),
    INDEX idx_position (field_position)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模板字段关联表';

-- 流转卡主表
CREATE TABLE transfer_cards (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_number VARCHAR(50) NOT NULL UNIQUE COMMENT '流转卡编号',
    template_id INT NULL COMMENT '模板ID',
    title VARCHAR(200) COMMENT '流转卡标题',
    description TEXT COMMENT '流转卡描述',
    status ENUM('draft', 'in_progress', 'completed', 'cancelled') DEFAULT 'draft' COMMENT '状态',
    created_by INT NOT NULL COMMENT '创建者ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_number (card_number),
    INDEX idx_status (status),
    INDEX idx_creator (created_by),
    INDEX idx_template (template_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='流转卡主表';

-- 流转卡数据表 (支持50个动态字段)
CREATE TABLE card_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id INT NOT NULL COMMENT '流转卡ID',
    -- 24个指定字段
    field_01_pcs_project TEXT COMMENT 'PCS项目',
    field_02_spec_model TEXT COMMENT '规格型号',
    field_03_manufacturer TEXT COMMENT '制造商',
    field_04_manufacturer_desc TEXT COMMENT '制造商说明',
    field_05_origin_country TEXT COMMENT '原产国',
    field_06_origin_country_cn TEXT COMMENT '原产国中文名称',
    field_07_material_desc TEXT COMMENT '物料说明',
    field_08_stock_unit TEXT COMMENT '库存单位',
    field_09_material_group TEXT COMMENT '物料组',
    field_10_material_group_desc TEXT COMMENT '物料组说明',
    field_11_material_group2 TEXT COMMENT '物料组二',
    field_12_material_group2_desc TEXT COMMENT '物料组二说明',
    field_13_product_type TEXT COMMENT '产品类型',
    field_14_product_type_desc TEXT COMMENT '产品类型说明',
    field_15_product_category TEXT COMMENT '产品大类',
    field_16_product_category_desc TEXT COMMENT '产品大类说明',
    field_17_product_classification TEXT COMMENT '产品分类',
    field_18_product_classification_desc TEXT COMMENT '产品分类说明',
    field_19_weight DECIMAL(10,4) COMMENT '重量',
    field_20_special_part TEXT COMMENT '专用件',
    field_21_batch_control TEXT COMMENT '批次控制',
    field_22_material_signal TEXT COMMENT '物料信号',
    field_23_effective_date DATE COMMENT '生效日期',
    field_24_expiry_date DATE COMMENT '失效日期',
    -- 26个占位字段
    field_25 TEXT COMMENT '预留字段25',
    field_26 TEXT COMMENT '预留字段26',
    field_27 TEXT COMMENT '预留字段27',
    field_28 TEXT COMMENT '预留字段28',
    field_29 TEXT COMMENT '预留字段29',
    field_30 TEXT COMMENT '预留字段30',
    field_31 TEXT COMMENT '预留字段31',
    field_32 TEXT COMMENT '预留字段32',
    field_33 TEXT COMMENT '预留字段33',
    field_34 TEXT COMMENT '预留字段34',
    field_35 TEXT COMMENT '预留字段35',
    field_36 TEXT COMMENT '预留字段36',
    field_37 TEXT COMMENT '预留字段37',
    field_38 TEXT COMMENT '预留字段38',
    field_39 TEXT COMMENT '预留字段39',
    field_40 TEXT COMMENT '预留字段40',
    field_41 TEXT COMMENT '预留字段41',
    field_42 TEXT COMMENT '预留字段42',
    field_43 TEXT COMMENT '预留字段43',
    field_44 TEXT COMMENT '预留字段44',
    field_45 TEXT COMMENT '预留字段45',
    field_46 TEXT COMMENT '预留字段46',
    field_47 TEXT COMMENT '预留字段47',
    field_48 TEXT COMMENT '预留字段48',
    field_49 TEXT COMMENT '预留字段49',
    field_50 TEXT COMMENT '预留字段50',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (card_id) REFERENCES transfer_cards(id) ON DELETE CASCADE,
    INDEX idx_card (card_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='流转卡数据表';

-- 流转卡数据行表 (管理每行的状态和部门归属)
CREATE TABLE card_data_rows (
    id INT AUTO_INCREMENT PRIMARY KEY,
    card_id INT NOT NULL COMMENT '流转卡ID',
    `row_number` INT NOT NULL COMMENT '行号',
    department_id INT COMMENT '负责部门ID',
    status ENUM('draft', 'submitted', 'approved') DEFAULT 'draft' COMMENT '状态',
    submitted_by INT COMMENT '提交人ID',
    submitted_at TIMESTAMP NULL COMMENT '提交时间',
    approved_by INT COMMENT '审核人ID',
    approved_at TIMESTAMP NULL COMMENT '审核时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (card_id) REFERENCES transfer_cards(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE SET NULL,
    FOREIGN KEY (submitted_by) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL,
    UNIQUE KEY uk_card_row (card_id, `row_number`),
    INDEX idx_card (card_id),
    INDEX idx_department (department_id),
    INDEX idx_status (status),
    INDEX idx_submitted_by (submitted_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='流转卡数据行表';

-- 模板字段权限表 (定义模板中哪些字段对哪些部门可见)
CREATE TABLE template_field_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    template_id INT NOT NULL COMMENT '模板ID',
    field_name VARCHAR(100) NOT NULL COMMENT '字段名称',
    department_id INT NOT NULL COMMENT '部门ID',
    can_read BOOLEAN DEFAULT TRUE COMMENT '是否可读',
    can_write BOOLEAN DEFAULT TRUE COMMENT '是否可写',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (template_id) REFERENCES templates(id) ON DELETE CASCADE,
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE CASCADE,
    UNIQUE KEY uk_template_field_dept (template_id, field_name, department_id),
    INDEX idx_template (template_id),
    INDEX idx_field (field_name),
    INDEX idx_department (department_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模板字段权限表';

-- 操作日志表
CREATE TABLE operation_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    operation_type VARCHAR(50) NOT NULL COMMENT '操作类型',
    target_type VARCHAR(50) COMMENT '目标类型',
    target_id INT COMMENT '目标ID',
    description TEXT COMMENT '操作描述',
    old_data JSON COMMENT '旧数据',
    new_data JSON COMMENT '新数据',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id),
    INDEX idx_operation (operation_type),
    INDEX idx_target (target_type, target_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- 插入初始部门数据
INSERT INTO departments (id, name, description) VALUES
(1, '研发部', '负责产品研发和设计'),
(2, '采购部', '负责原材料采购'),
(3, '销售部', '负责产品销售'),
(4, '生产部', '负责产品生产'),
(5, '质检部', '负责质量检验'),
(6, '仓库部', '负责仓储管理');

-- 插入24个指定字段
INSERT INTO fields (name, display_name, field_type, department_id, department_name, category, field_position, is_placeholder) VALUES
('field_01_pcs_project', 'PCS项目', 'text', 1, '研发部', '基本信息', 1, FALSE),
('field_02_spec_model', '规格型号', 'text', 1, '研发部', '基本信息', 2, FALSE),
('field_03_manufacturer', '制造商', 'text', 2, '采购部', '采购信息', 3, FALSE),
('field_04_manufacturer_desc', '制造商说明', 'text', 2, '采购部', '采购信息', 4, FALSE),
('field_05_origin_country', '原产国', 'text', 2, '采购部', '采购信息', 5, FALSE),
('field_06_origin_country_cn', '原产国中文名称', 'text', 2, '采购部', '采购信息', 6, FALSE),
('field_07_material_desc', '物料说明', 'text', 1, '研发部', '基本信息', 7, FALSE),
('field_08_stock_unit', '库存单位', 'text', 4, '生产部', '生产信息', 8, FALSE),
('field_09_material_group', '物料组', 'text', 1, '研发部', '基本信息', 9, FALSE),
('field_10_material_group_desc', '物料组说明', 'text', 1, '研发部', '基本信息', 10, FALSE),
('field_11_material_group2', '物料组二', 'text', 1, '研发部', '基本信息', 11, FALSE),
('field_12_material_group2_desc', '物料组二说明', 'text', 1, '研发部', '基本信息', 12, FALSE),
('field_13_product_type', '产品类型', 'text', 1, '研发部', '产品信息', 13, FALSE),
('field_14_product_type_desc', '产品类型说明', 'text', 1, '研发部', '产品信息', 14, FALSE),
('field_15_product_category', '产品大类', 'text', 1, '研发部', '产品信息', 15, FALSE),
('field_16_product_category_desc', '产品大类说明', 'text', 1, '研发部', '产品信息', 16, FALSE),
('field_17_product_classification', '产品分类', 'text', 1, '研发部', '产品信息', 17, FALSE),
('field_18_product_classification_desc', '产品分类说明', 'text', 1, '研发部', '产品信息', 18, FALSE),
('field_19_weight', '重量', 'number', 4, '生产部', '生产信息', 19, FALSE),
('field_20_special_part', '专用件', 'text', 1, '研发部', '基本信息', 20, FALSE),
('field_21_batch_control', '批次控制', 'text', 4, '生产部', '生产信息', 21, FALSE),
('field_22_material_signal', '物料信号', 'text', 1, '研发部', '基本信息', 22, FALSE),
('field_23_effective_date', '生效日期', 'date', 2, '采购部', '采购信息', 23, FALSE),
('field_24_expiry_date', '失效日期', 'date', 2, '采购部', '采购信息', 24, FALSE);

-- 插入26个占位字段
INSERT INTO fields (name, display_name, field_type, department_id, department_name, category, field_position, is_placeholder) VALUES
('field_25', '预留字段25', 'text', NULL, NULL, '预留字段', 25, TRUE),
('field_26', '预留字段26', 'text', NULL, NULL, '预留字段', 26, TRUE),
('field_27', '预留字段27', 'text', NULL, NULL, '预留字段', 27, TRUE),
('field_28', '预留字段28', 'text', NULL, NULL, '预留字段', 28, TRUE),
('field_29', '预留字段29', 'text', NULL, NULL, '预留字段', 29, TRUE),
('field_30', '预留字段30', 'text', NULL, NULL, '预留字段', 30, TRUE),
('field_31', '预留字段31', 'text', NULL, NULL, '预留字段', 31, TRUE),
('field_32', '预留字段32', 'text', NULL, NULL, '预留字段', 32, TRUE),
('field_33', '预留字段33', 'text', NULL, NULL, '预留字段', 33, TRUE),
('field_34', '预留字段34', 'text', NULL, NULL, '预留字段', 34, TRUE),
('field_35', '预留字段35', 'text', NULL, NULL, '预留字段', 35, TRUE),
('field_36', '预留字段36', 'text', NULL, NULL, '预留字段', 36, TRUE),
('field_37', '预留字段37', 'text', NULL, NULL, '预留字段', 37, TRUE),
('field_38', '预留字段38', 'text', NULL, NULL, '预留字段', 38, TRUE),
('field_39', '预留字段39', 'text', NULL, NULL, '预留字段', 39, TRUE),
('field_40', '预留字段40', 'text', NULL, NULL, '预留字段', 40, TRUE),
('field_41', '预留字段41', 'text', NULL, NULL, '预留字段', 41, TRUE),
('field_42', '预留字段42', 'text', NULL, NULL, '预留字段', 42, TRUE),
('field_43', '预留字段43', 'text', NULL, NULL, '预留字段', 43, TRUE),
('field_44', '预留字段44', 'text', NULL, NULL, '预留字段', 44, TRUE),
('field_45', '预留字段45', 'text', NULL, NULL, '预留字段', 45, TRUE),
('field_46', '预留字段46', 'text', NULL, NULL, '预留字段', 46, TRUE),
('field_47', '预留字段47', 'text', NULL, NULL, '预留字段', 47, TRUE),
('field_48', '预留字段48', 'text', NULL, NULL, '预留字段', 48, TRUE),
('field_49', '预留字段49', 'text', NULL, NULL, '预留字段', 49, TRUE),
('field_50', '预留字段50', 'text', NULL, NULL, '预留字段', 50, TRUE);
