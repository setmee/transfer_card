# 流转卡模板删除Bug修复总结

## 问题描述
当直接删除流转卡模板时，关联的所有流转卡也会消失，但流转卡号在数据库中仍被占用，导致前端无法查看这些流转卡。

## 问题根源
1. `transfer_cards`表通过`template_id`字段关联`templates`表
2. 当模板被删除时，由于外键约束或查询逻辑问题，导致流转卡数据无法正确显示
3. 模板被修改或删除后，基于模板创建的流转卡失去了原始模板信息

## 解决方案：模板快照机制

### 1. 新增表结构

#### template_snapshots表
```sql
CREATE TABLE `template_snapshots` (
  `snapshot_id` varchar(50) NOT NULL COMMENT '快照ID（自动生成唯一值）',
  `template_id` int DEFAULT NULL COMMENT '模板ID',
  `template_name` varchar(200) DEFAULT NULL COMMENT '模板名称（快照时保存）',
  `template_description` text COMMENT '模板描述（快照时保存）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`snapshot_id`),
  KEY `idx_template_id` (`template_id`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `template_snapshots_ibfk_1` FOREIGN KEY (`template_id`) REFERENCES `templates` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 2. 修改transfer_cards表
添加`snapshot_id`字段：
```sql
ALTER TABLE transfer_cards ADD COLUMN `snapshot_id` varchar(50) DEFAULT NULL COMMENT '模板快照ID';
ALTER TABLE transfer_cards ADD KEY `idx_snapshot` (`snapshot_id`);
ALTER TABLE transfer_cards ADD CONSTRAINT `transfer_cards_ibfk_3` FOREIGN KEY (`snapshot_id`) REFERENCES `template_snapshots` (`snapshot_id`) ON DELETE SET NULL;
```

### 3. 后端逻辑修改

#### 创建流转卡时
```python
# 生成唯一的快照ID
snapshot_id = f"snap_{int(time.time() * 1000)}"

# 创建模板快照
cursor.execute("""
    INSERT INTO template_snapshots (snapshot_id, template_id, template_name, template_description)
    VALUES (%s, %s, %s, %s)
""", (snapshot_id, template_id, template['template_name'], template['template_description']))

# 创建流转卡时关联快照
cursor.execute("""
    INSERT INTO transfer_cards (card_number, template_id, snapshot_id, title, description, status, created_by)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
""", (card_number, template_id, snapshot_id, title, description, 'draft', user_id))
```

#### 查询流转卡时
```python
# 使用LEFT JOIN确保即使模板被删除也能显示流转卡
sql = """
SELECT tc.*, 
       COALESCE(ts.template_name, t.template_name, '未知模板') as template_name,
       u.username as creator_name,
       (SELECT COUNT(*) FROM card_data cdr WHERE cdr.card_id = tc.id) as row_count
FROM transfer_cards tc
LEFT JOIN template_snapshots ts ON tc.snapshot_id = ts.snapshot_id
LEFT JOIN templates t ON tc.template_id = t.id
LEFT JOIN users u ON tc.created_by = u.id
ORDER BY tc.created_at DESC
"""
```

### 4. 字符集问题修复
修复了`template_snapshots`表的字符集排序规则，统一为`utf8mb4_unicode_ci`：
```sql
ALTER TABLE template_snapshots CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 修复效果

### 修复前
- ❌ 删除模板后，相关流转卡无法查看
- ❌ 流转卡号被占用但数据无法访问
- ❌ 模板修改影响已创建的流转卡
- ❌ 流转卡管理页面不显示模板被删除的流转卡（普通用户）

### 修复后
- ✅ 删除模板后，流转卡仍然可以正常查看（使用快照信息）
- ✅ 流转卡号不会因模板删除而失效
- ✅ 模板修改不影响已创建的流转卡
- ✅ 流转卡显示模板名称（优先使用快照中的名称）
- ✅ 流转卡管理页面正常显示所有流转卡（包括模板被删除的）

## 测试验证

### 测试步骤
1. 创建一个新的流转卡模板
2. 基于该模板创建多个流转卡
3. 删除该模板
4. 验证：流转卡列表中仍能看到这些流转卡，显示"未知模板"或快照中的模板名称
5. 验证：可以正常查看和编辑这些流转卡

### 测试SQL查询
```bash
python test_sql_query.py
```

## 已完成的修改

### 数据库层面
1. ✅ 创建`template_snapshots`表
2. ✅ 在`transfer_cards`表添加`snapshot_id`字段
3. ✅ 修复字符集排序规则冲突
4. ✅ 更新`database/schema.sql`脚本

### 后端层面
1. ✅ 修改创建流转卡API，创建模板快照
2. ✅ 修改查询流转卡API，使用LEFT JOIN关联快照
3. ✅ 修复缩进和语法错误

### 文档层面
1. ✅ 更新`database/schema.sql`完整表结构定义
2. ✅ 创建本修复总结文档

## 注意事项

1. **现有流转卡**：之前创建的流转卡没有`snapshot_id`，会显示"未知模板"，但数据不受影响
2. **新流转卡**：所有新创建的流转卡都会创建快照，不再受模板删除影响
3. **性能**：快照机制会增加少量存储，但确保了数据完整性和独立性
4. **迁移**：如需为现有流转卡补充快照，可运行`migrate_existing_cards.py`脚本

## 相关文件

- `database/schema.sql` - 完整的数据库表结构定义
- `backend/app.py` - 后端API逻辑
- `test_sql_query.py` - SQL查询测试脚本
- `migrate_existing_cards.py` - 现有流转卡快照迁移脚本（可选）

## 修复日期
2026-01-06
