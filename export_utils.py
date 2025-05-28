# paper_manager/export_utils.py
import sqlite3
import pandas as pd

def export_references_to_excel(filepath):
    conn = sqlite3.connect("paper.db")
    df = pd.read_sql_query("SELECT * FROM references", conn)
    df.to_excel(filepath, index=False)
    conn.close()
    print(f"✅ 导出成功: {filepath}")
