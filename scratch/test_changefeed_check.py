import os
import sys

sys.path.insert(0, os.path.abspath("apps/api"))
sys.path.insert(0, os.path.abspath("."))

from sqlalchemy import text
from app.db.session import SessionLocal

def main():
    print("Testing CockroachDB Changefeed Support...")
    db = SessionLocal()
    try:
        # Check dialect
        dialect_name = db.bind.dialect.name if db.bind else "unknown"
        print(f"Database dialect: {dialect_name}")

        # Check version
        version = db.execute(text("SELECT version();")).scalar()
        print(f"CockroachDB version: {version}")

        # Check changefeed setting or permission
        try:
            # Let's test if rangefeed is enabled on cluster
            res = db.execute(text("SHOW CLUSTER SETTING kv.rangefeed.enabled;")).fetchall()
            print(f"kv.rangefeed.enabled setting: {res}")
        except Exception as e:
            print(f"Could not SHOW CLUSTER SETTING kv.rangefeed.enabled: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
