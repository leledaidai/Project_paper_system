# database.py
import sqlite3

def init_db():
    conn = sqlite3.connect('paper.db')
    cur = conn.cursor()
    # 原始表
    cur.execute('''
        CREATE TABLE IF NOT EXISTS "references" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            authors TEXT,
            year INTEGER,
            journal TEXT,
            category TEXT,
            doi TEXT,
            pdf_link TEXT,
            local_pdf TEXT,
            author_position INTEGER,
            level TEXT
        )
    ''')
    # 引用关系表（引用者引用被引用者）
    cur.execute('''
        CREATE TABLE IF NOT EXISTS "citations" (
            from_id INTEGER,
            to_id INTEGER,
            FOREIGN KEY(from_id) REFERENCES "references"(id),
            FOREIGN KEY(to_id) REFERENCES "references"(id)
        )
    ''')
    # 新增发表论文表
    cur.execute('''
        CREATE TABLE IF NOT EXISTS publications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            authors TEXT,
            year INTEGER,
            journal TEXT,
            category TEXT,
            author_position INTEGER,
            level TEXT,
            score REAL
        )
    ''')
    conn.commit()
    conn.close()

def add_reference(title, authors, year, journal, category, doi, pdf_link):
    conn = sqlite3.connect('paper.db')
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO "references" (title, authors, year, journal, category, doi, pdf_link)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, authors, year, journal, category, doi, pdf_link))
    conn.commit()
    conn.close()

def search_references(keyword):
    conn = sqlite3.connect('paper.db')
    cur = conn.cursor()
    cur.execute('''
        SELECT * FROM "references"
        WHERE title LIKE ? OR authors LIKE ? OR journal LIKE ?
    ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
    results = cur.fetchall()
    conn.close()
    return results

def add_citation(from_id, to_id):
    conn = sqlite3.connect('paper.db')
    cur = conn.cursor()
    cur.execute("INSERT INTO citations (from_id, to_id) VALUES (?, ?)", (from_id, to_id))
    conn.commit()
    conn.close()

def get_all_references():
    conn = sqlite3.connect('paper.db')
    cur = conn.cursor()
    cur.execute("SELECT id, title FROM \"references\"")
    results = cur.fetchall()
    conn.close()
    return results

def get_all_citations():
    conn = sqlite3.connect('paper.db')
    cur = conn.cursor()
    cur.execute("SELECT from_id, to_id FROM \"citations\"")
    results = cur.fetchall()
    conn.close()
    return results

