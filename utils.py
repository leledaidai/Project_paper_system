# utils.py
import requests
import os

def download_pdf(url, filename):
    try:
        # 添加 verify=True 参数以验证 SSL 证书（默认）
        response = requests.get(url, timeout=10, verify=True)
        if response.status_code == 200:
            filepath = os.path.join('data', f"{filename}.pdf")
            with open(filepath, 'wb') as f:
                f.write(response.content)
            return True, f"✅ 下载成功: {filepath}"
        else:
            return False, f"❌ 下载失败，状态码: {response.status_code}"
    except requests.exceptions.SSLError as e:
        return False, f"❌ SSL 错误: {e}"
    except Exception as e:
        return False, f"❌ 出现错误: {e}"


import sqlite3
import pandas as pd

def export_references_to_excel(filepath):
    conn = sqlite3.connect('paper.db')
    df = pd.read_sql_query("SELECT * FROM \"references\"", conn)
    df.to_excel(filepath, index=False)
    conn.close()

    
def get_score_by_category(category):
    rules = {
        "CCF-A": 3,
        "CCF-B": 2,
        "CCF-C": 1,
        "SCI": 2.5,
        "EI": 2,
        "其他": 1,
    }
    return rules.get(category, 1)
