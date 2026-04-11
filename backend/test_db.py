import os
import sys
import traceback

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from app import app, db
    print("DB URI:", app.config['SQLALCHEMY_DATABASE_URI'])
    with app.app_context():
        print("Tables:", db.engine.table_names() if hasattr(db.engine, 'table_names') else db.inspect(db.engine).get_table_names())
except Exception as e:
    traceback.print_exc()
