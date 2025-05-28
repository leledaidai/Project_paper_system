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
    """导出参考文献到Excel文件"""
    conn = sqlite3.connect('paper.db')
    try:
        # 只选择需要的字段
        query = """
        SELECT title, authors, date, journal, category, doi, paper_url 
        FROM "paper_references"
        """
        df = pd.read_sql_query(query, conn)
        
        # 重命名列
        df.columns = ['标题', '作者', '日期', '期刊', '分类', 'DOI', '论文地址']
        
        # 保存到Excel
        df.to_excel(filepath, index=False, engine='openpyxl')
    finally:
        conn.close()

def export_search_results_to_excel(filepath, keyword='', category=None):
    """导出搜索结果到Excel文件"""
    conn = sqlite3.connect('paper.db')
    try:
        # 构建查询条件
        conditions = []
        params = []
        if keyword:
            conditions.append("(title LIKE ? OR authors LIKE ? OR journal LIKE ?)")
            params.extend([f'%{keyword}%'] * 3)
        if category:
            conditions.append("category = ?")
            params.append(category)
        
        # 构建完整的查询语句
        query = """
        SELECT title, authors, date, journal, category, doi, paper_url 
        FROM "paper_references"
        """
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # 执行查询
        df = pd.read_sql_query(query, conn, params=tuple(params))
        
        # 重命名列
        df.columns = ['标题', '作者', '日期', '期刊', '分类', 'DOI', '论文地址']
        
        # 保存到Excel
        df.to_excel(filepath, index=False, engine='openpyxl')
    finally:
        conn.close()

def export_workload_to_excel(filepath):
    """导出工作量统计到Excel文件"""
    conn = sqlite3.connect('paper.db')
    try:
        # 获取所有文献
        query = "SELECT authors, category FROM \"paper_references\""
        df = pd.read_sql_query(query, conn)
        
        # 计算每个作者的工作量
        workload_stats = {}
        for _, row in df.iterrows():
            authors = [a.strip() for a in row['authors'].split(';')]
            score = get_score_by_category(row['category'])
            for author in authors:
                if author:
                    if author not in workload_stats:
                        workload_stats[author] = {'count': 0, 'score': 0}
                    workload_stats[author]['count'] += 1
                    workload_stats[author]['score'] += score
        
        # 转换为DataFrame
        workload_df = pd.DataFrame([
            {"作者": k, "论文数量": v["count"], "工作量分数": v["score"]}
            for k, v in workload_stats.items()
        ])
        
        # 按工作量分数降序排序
        workload_df = workload_df.sort_values('工作量分数', ascending=False)
        
        # 保存到Excel
        workload_df.to_excel(filepath, index=False, engine='openpyxl')
    finally:
        conn.close()

def get_score_by_category(category):
    """根据分类获取工作量分数"""
    scores = {
        'CCF-A': 10,
        'CCF-B': 7,
        'CCF-C': 5,
        'SCI': 8,
        'EI': 4,
        '其他': 2
    }
    return scores.get(category, 0)
