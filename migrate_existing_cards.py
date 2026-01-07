#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migrate existing transfer cards to use template snapshots
This script copies template configuration to card snapshot tables
"""

import pymysql
from datetime import datetime
import json

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'LGY@lgy1109',
    'database': 'transfer_card_system',
    'charset': 'utf8mb4'
}

def migrate_cards():
    """Migrate existing transfer cards"""
    
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    try:
        print("Starting migration of existing transfer cards...")
        
        # Get all transfer cards
        cursor.execute("SELECT id, card_number, template_id FROM transfer_cards")
        cards = cursor.fetchall()
        
        total_cards = len(cards)
        print(f"Found {total_cards} transfer cards to migrate")
        
        migrated = 0
        skipped = 0
        
        for card_id, card_number, template_id in cards:
            if template_id is None:
                print(f"  Skipping card {card_number} - no template_id")
                skipped += 1
                continue
            
            try:
                # Migrate template fields
                cursor.execute("""
                    INSERT INTO card_template_fields 
                    (card_id, field_name, field_display_name, field_type, field_order, 
                     is_required, default_value, options, department_id, department_name)
                    SELECT %s, tf.field_name, tf.field_display_name, tf.field_type, 
                           tf.field_order, tf.is_required, tf.default_value, tf.options,
                           f.department_id, f.department_name
                    FROM template_fields tf
                    LEFT JOIN fields f ON tf.field_id = f.id
                    WHERE tf.template_id = %s
                """, (card_id, template_id))
                
                fields_count = cursor.rowcount
                
                # Migrate department flow
                cursor.execute("""
                    INSERT INTO card_department_flow 
                    (card_id, department_id, flow_order, is_required, auto_skip, timeout_hours)
                    SELECT %s, tdf.department_id, tdf.flow_order, tdf.is_required, 
                           tdf.auto_skip, tdf.timeout_hours
                    FROM template_department_flow tdf
                    WHERE tdf.template_id = %s
                """, (card_id, template_id))
                
                flow_count = cursor.rowcount
                
                # Migrate field permissions
                cursor.execute("""
                    INSERT INTO card_field_permissions 
                    (card_id, field_name, department_id, can_read, can_write)
                    SELECT %s, tfp.field_name, tfp.department_id, tfp.can_read, tfp.can_write
                    FROM template_field_permissions tfp
                    WHERE tfp.template_id = %s
                """, (card_id, template_id))
                
                perms_count = cursor.rowcount
                
                print(f"  Migrated card {card_number}: {fields_count} fields, {flow_count} flow steps, {perms_count} permissions")
                migrated += 1
                
            except Exception as e:
                print(f"  Error migrating card {card_number}: {e}")
                conn.rollback()
                continue
        
        conn.commit()
        print(f"\nMigration completed:")
        print(f"  Total cards: {total_cards}")
        print(f"  Migrated: {migrated}")
        print(f"  Skipped: {skipped}")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    migrate_cards()
