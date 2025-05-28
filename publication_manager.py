# paper_manager/publication_manager.py
import sqlite3

def add_publication(reference_id, author_order, score):
    conn = sqlite3.connect("paper.db")
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO publications (reference_id, author_order, score)
        VALUES (?, ?, ?)
    ''', (reference_id, author_order, score))
    conn.commit()
    conn.close()
    print("✅ 发表记录添加成功")
