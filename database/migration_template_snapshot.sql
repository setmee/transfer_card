-- Template snapshot migration script
-- Execute this script to implement template snapshot functionality

USE `transfer_card_system`;

-- ========================================
-- Step 1: Create template snapshot tables
-- ========================================

-- 1.1 Create card template fields snapshot table
CREATE TABLE IF NOT EXISTS `card_template_fields` (
  `id` int NOT NULL AUTO_INCREMENT,
  `card_id` int NOT NULL COMMENT 'Card ID',
  `field_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Field name',
  `field_display_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Field display name',
  `field_type` enum('text','number','date','select','boolean') COLLATE utf8mb4_unicode_ci DEFAULT 'text' COMMENT 'Field type',
  `field_order` int DEFAULT '1' COMMENT 'Field order',
  `is_required` tinyint(1) DEFAULT '0' COMMENT 'Is required',
  `default_value` text COLLATE utf8mb4_unicode_ci COMMENT 'Default value',
  `options` text COLLATE utf8mb4_unicode_ci COMMENT 'Options (JSON format)',
  `department_id` int DEFAULT NULL COMMENT 'Department ID',
  `department_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Department name',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_card_field_order` (`card_id`,`field_order`),
  KEY `idx_card` (`card_id`),
  KEY `idx_field` (`field_name`),
  KEY `idx_order` (`field_order`),
  KEY `idx_department` (`department_id`),
  CONSTRAINT `card_template_fields_ibfk_1` FOREIGN KEY (`card_id`) REFERENCES `transfer_cards` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 1.2 Create card department flow snapshot table
CREATE TABLE IF NOT EXISTS `card_department_flow` (
  `id` int NOT NULL AUTO_INCREMENT,
  `card_id` int NOT NULL COMMENT 'Card ID',
  `department_id` int NOT NULL COMMENT 'Department ID',
  `flow_order` int NOT NULL COMMENT 'Flow order',
  `is_required` tinyint(1) DEFAULT '1' COMMENT 'Is required department',
  `auto_skip` tinyint(1) DEFAULT '0' COMMENT 'Auto skip if no data',
  `timeout_hours` int DEFAULT '24' COMMENT 'Timeout hours',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_card_department` (`card_id`,`department_id`),
  KEY `idx_card` (`card_id`),
  KEY `idx_department` (`department_id`),
  KEY `idx_flow_order` (`card_id`,`flow_order`),
  CONSTRAINT `card_department_flow_ibfk_1` FOREIGN KEY (`card_id`) REFERENCES `transfer_cards` (`id`) ON DELETE CASCADE,
  CONSTRAINT `card_department_flow_ibfk_2` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 1.3 Create card field permissions snapshot table
CREATE TABLE IF NOT EXISTS `card_field_permissions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `card_id` int NOT NULL COMMENT 'Card ID',
  `field_name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Field name',
  `department_id` int NOT NULL COMMENT 'Department ID',
  `can_read` tinyint(1) DEFAULT '1' COMMENT 'Can read',
  `can_write` tinyint(1) DEFAULT '1' COMMENT 'Can write',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_card_field_dept` (`card_id`,`field_name`,`department_id`),
  KEY `idx_card` (`card_id`),
  KEY `idx_field` (`field_name`),
  KEY `idx_department` (`department_id`),
  CONSTRAINT `card_field_permissions_ibfk_1` FOREIGN KEY (`card_id`) REFERENCES `transfer_cards` (`id`) ON DELETE CASCADE,
  CONSTRAINT `card_field_permissions_ibfk_2` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ========================================
-- Step 2: Modify foreign key constraints
-- ========================================

-- 2.1 Modify template_fields table - add foreign keys
ALTER TABLE `template_fields` 
ADD CONSTRAINT `template_fields_ibfk_1` FOREIGN KEY (`template_id`) REFERENCES `templates` (`id`) ON DELETE SET NULL,
ADD CONSTRAINT `template_fields_ibfk_2` FOREIGN KEY (`field_id`) REFERENCES `fields` (`id`) ON DELETE SET NULL;

-- 2.2 Modify template_department_flow table
-- First allow NULL for template_id
ALTER TABLE `template_department_flow` MODIFY COLUMN `template_id` int DEFAULT NULL;

-- Drop and recreate foreign keys
ALTER TABLE `template_department_flow` DROP FOREIGN KEY `template_department_flow_ibfk_1`;
ALTER TABLE `template_department_flow` DROP FOREIGN KEY `template_department_flow_ibfk_2`;

ALTER TABLE `template_department_flow` 
ADD CONSTRAINT `template_department_flow_ibfk_1` FOREIGN KEY (`template_id`) REFERENCES `templates` (`id`) ON DELETE SET NULL,
ADD CONSTRAINT `template_department_flow_ibfk_2` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE CASCADE;

-- 2.3 Modify template_field_permissions table
ALTER TABLE `template_field_permissions` MODIFY COLUMN `template_id` int DEFAULT NULL;

ALTER TABLE `template_field_permissions` DROP FOREIGN KEY `template_field_permissions_ibfk_1`;
ALTER TABLE `template_field_permissions` DROP FOREIGN KEY `template_field_permissions_ibfk_2`;

ALTER TABLE `template_field_permissions` 
ADD CONSTRAINT `template_field_permissions_ibfk_1` FOREIGN KEY (`template_id`) REFERENCES `templates` (`id`) ON DELETE SET NULL,
ADD CONSTRAINT `template_field_permissions_ibfk_2` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE CASCADE;

-- ========================================
-- Complete
-- ========================================

SELECT 'Template snapshot migration completed!' AS message;
