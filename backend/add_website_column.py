import pymysql

def add_website_column():
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',
            db='digitalpds'
        )
        with connection.cursor() as cursor:
            # Check if column exists
            cursor.execute("SHOW COLUMNS FROM clinics LIKE 'website'")
            if not cursor.fetchone():
                cursor.execute("ALTER TABLE clinics ADD COLUMN website VARCHAR(255) NULL AFTER longitude")
                print("Added 'website' column to 'clinics' table")
            else:
                print("'website' column already exists")
        connection.commit()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    add_website_column()
