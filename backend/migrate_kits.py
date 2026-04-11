from app import app, db
from sqlalchemy import text

def migrate():
    with app.app_context():
        try:
            # Add total_kits column
            db.session.execute(text("ALTER TABLE stock_requests ADD COLUMN total_kits INT DEFAULT 0 AFTER requested_quantity"))
            db.session.commit()
            print("Successfully added total_kits column to stock_requests table")
        except Exception as e:
            db.session.rollback()
            print(f"Error: {e}")

if __name__ == "__main__":
    migrate()
