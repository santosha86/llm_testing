import sqlite3
import os

import sqlite3
import pandas as pd

def inspect_sqlite_database(db_path, max_sample_rows=5, max_static_values=10):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    db_info = {}

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]
    db_info["tables"] = tables
    db_info["tables_info"] = {}

    for table in tables:
        print(f"\n============================")
        print(f"TABLE: {table}")
        print("============================")

        # Count rows
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        row_count = cursor.fetchone()[0]
        print(f"Row Count: {row_count}")

        # Get schema
        cursor.execute(f"PRAGMA table_info({table});")
        schema = cursor.fetchall()

        columns = {col[1]: col[2] for col in schema}
        print("\nSchema:")
        for name, dtype in columns.items():
            print(f"  - {name}: {dtype}")

        # Fetch sample rows
        df = pd.read_sql_query(f"SELECT * FROM {table} LIMIT {max_sample_rows}", conn)
        print("\nSample Rows:")
        print(df)

        # Detect static (categorical) columns
        print("\nStatic Columns (<= 10 unique values):")
        static_fields = {}
        for col in columns.keys():
            try:
                cursor.execute(
                    f'SELECT DISTINCT "{col}" FROM {table} WHERE "{col}" IS NOT NULL LIMIT {max_static_values + 1};'
                )
                values = [v[0] for v in cursor.fetchall()]
                if 1 <= len(values) <= max_static_values:
                    static_fields[col] = values
                    print(f"  - {col}: {values}")
            except:
                pass

        if not static_fields:
            print("  None")

        # Save to dictionary
        db_info["tables_info"][table] = {
            "row_count": row_count,
            "columns": columns,
            "sample_rows": df.to_dict(orient="records"),
            "static_fields": static_fields
        }

    conn.close()
    return db_info


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "..", "all_waybills.db")

sechma = inspect_sqlite_database("all_waybills.db")

print(sechma)