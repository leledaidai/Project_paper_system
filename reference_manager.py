# paper_manager/reference_manager.py
import sqlite3

def add_reference(title, authors, year, journal, category, doi, pdf_link):
    conn = sqlite3.connect("paper.db")
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO references (title, authors, year, journal, category, doi, pdf_link)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, authors, year, journal, category, doi, pdf_link))
    conn.commit()
    conn.close()
    print("✅ 添加成功")

def query_references(keyword):
    conn = sqlite3.connect("paper.db")
    cur = conn.cursor()
    cur.execute('''
        SELECT * FROM references
        WHERE title LIKE ? OR authors LIKE ? OR journal LIKE ?
    ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
    results = cur.fetchall()
    conn.close()
    return results
