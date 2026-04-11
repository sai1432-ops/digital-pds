import os
import sys
import traceback

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from sqlalchemy import text

def run_migration():
    try:
        with app.app_context():
            result = db.session.execute(text("SHOW COLUMNS FROM users")).fetchall()
            columns = [row[0] for row in result] # In MySQL SHOW COLUMNS, Field (name) is the 1st column [0]
            print("Existing columns in users:", columns)
            
            queries = []
            if 'address' not in columns:
                queries.append("ALTER TABLE users ADD COLUMN address TEXT")
            if 'age' not in columns:
                queries.append("ALTER TABLE users ADD COLUMN age INTEGER")
            if 'gender' not in columns:
                queries.append("ALTER TABLE users ADD COLUMN gender VARCHAR(20)")
            if 'education' not in columns:
                queries.append("ALTER TABLE users ADD COLUMN education VARCHAR(100)")
            if 'employment' not in columns:
                queries.append("ALTER TABLE users ADD COLUMN employment VARCHAR(100)")
                
            for q in queries:
                try:
                    db.session.execute(text(q))
                    print(f"Executed: {q}")
                except Exception as e:
                    print(f"Error executing {q}: {e}")
            
            db.session.commit()
            print("Migration completed successfully.")
    except Exception as e:
        print("Outer Error:")
        traceback.print_exc()

if __name__ == "__main__":
    run_migration()
