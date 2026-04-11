"""
Migration script: Add DELIVERED status to stock_requests table
Run this script once to update the database schema.

Usage: python add_delivered_status.py
"""

import pymysql

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "digital_pds",
    "charset": "utf8mb4"
}

def run_migration():
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # 1. Alter the status ENUM to include DELIVERED
        print("[1/2] Altering stock_requests.status ENUM to include DELIVERED...")
        cursor.execute("""
            ALTER TABLE stock_requests 
            MODIFY COLUMN status ENUM('PENDING','APPROVED','DISPATCHED','DELIVERED','REJECTED') 
            DEFAULT 'PENDING'
        """)
        print("  ✓ ENUM updated successfully")

        # 2. Add delivered_at column if it doesn't exist
        print("[2/2] Adding delivered_at column...")
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.columns 
            WHERE table_schema = %s 
            AND table_name = 'stock_requests' 
            AND column_name = 'delivered_at'
        """, (DB_CONFIG["database"],))

        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                ALTER TABLE stock_requests 
                ADD COLUMN delivered_at DATETIME NULL AFTER dispatched_at
            """)
            print("  ✓ delivered_at column added")
        else:
            print("  ✓ delivered_at column already exists (skipped)")

        conn.commit()
        print("\n✅ Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ Migration failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    run_migration()
