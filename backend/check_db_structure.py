import pymysql
import json

with open('config/config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

db_config = config['database']
db_config['cursorclass'] = pymysql.cursors.DictCursor

conn = pymysql.connect(**db_config)
cursor = conn.cursor()

# 查看transfer_cards表结构
print('=== transfer_cards 表结构 ===')
cursor.execute('SHOW CREATE TABLE transfer_cards')
result = cursor.fetchone()
print(result['Create Table'])
print()

# 查看templates表结构
print('=== templates 表结构 ===')
cursor.execute('SHOW CREATE TABLE templates')
result = cursor.fetchone()
print(result['Create Table'])
print()

# 查看template_fields表结构
print('=== template_fields 表结构 ===')
cursor.execute('SHOW CREATE TABLE template_fields')
result = cursor.fetchone()
print(result['Create Table'])
print()

# 查看template_department_flow表结构
print('=== template_department_flow 表结构 ===')
cursor.execute('SHOW CREATE TABLE template_department_flow')
result = cursor.fetchone()
print(result['Create Table'])
print()

# 查看template_field_permissions表结构
print('=== template_field_permissions 表结构 ===')
cursor.execute('SHOW CREATE TABLE template_field_permissions')
result = cursor.fetchone()
print(result['Create Table'])

cursor.close()
conn.close()
