# database.py
import sqlite3
from contextlib import contextmanager
from typing import List, Tuple, Optional, Any
import os
import shutil
import time
import re
import datetime

class DatabaseManager:
    def __init__(self, db_path: str = 'paper.db'):
        self.db_path = db_path

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[Tuple]:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            return cur.fetchall()

    def execute_update(self, query: str, params: tuple = ()) -> None:
        with self.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()

# 创建全局数据库管理器实例
db = DatabaseManager()

def init_db():
    """初始化数据库"""
    with db.get_connection() as conn:
        cur = conn.cursor()
        # 创建文献引用表
        cur.execute('''
            CREATE TABLE IF NOT EXISTS "paper_references" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                authors TEXT NOT NULL CHECK (authors != ''),
                date TEXT NOT NULL,
                journal TEXT,
                category TEXT CHECK (category IN ('CCF-A', 'CCF-B', 'CCF-C', 'SCI', 'EI', '其他')),
                doi TEXT,
                paper_url TEXT,  -- 论文在线地址
                local_pdf TEXT,  -- 本地PDF文件名
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建引用关系表
        cur.execute('''
            CREATE TABLE IF NOT EXISTS "paper_citations" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_id INTEGER NOT NULL,
                to_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_id) REFERENCES "paper_references" (id) ON DELETE CASCADE,
                FOREIGN KEY (to_id) REFERENCES "paper_references" (id) ON DELETE CASCADE,
                CHECK (from_id != to_id)
            )
        ''')
        conn.commit()

def validate_reference_data(title: str, authors: str, date: str, journal: str, 
                          category: str, doi: str = '', paper_url: str = '') -> None:
    """验证文献数据的有效性"""
    if not title or not title.strip():
        raise ValueError("标题不能为空")
    
    if not authors or not authors.strip():
        raise ValueError("作者不能为空")
    
    # 验证作者格式（使用英文分号分隔）
    author_list = [a.strip() for a in authors.split(';')]
    if not all(author_list):
        raise ValueError("作者格式不正确，请使用英文分号(;)分隔多个作者")
    
    # 验证日期格式和范围
    try:
        date_obj = datetime.datetime.strptime(date, '%Y-%m-%d')
        min_date = datetime.datetime(1900, 1, 1)
        max_date = datetime.datetime.now()
        if not (min_date <= date_obj <= max_date):
            raise ValueError("日期必须在1900年1月1日至今的范围内")
    except ValueError as e:
        if "time data" in str(e):
            raise ValueError("日期格式无效，请使用YYYY-MM-DD格式")
        raise e
    
    if category not in ['CCF-A', 'CCF-B', 'CCF-C', 'SCI', 'EI', '其他']:
        raise ValueError("分类必须是：CCF-A、CCF-B、CCF-C、SCI、EI、其他")
    
    # 验证DOI格式
    if not doi or not doi.strip():
        raise ValueError("DOI不能为空")
    
    doi = doi.strip()
    # DOI格式验证：必须以10.开头，后面跟数字，然后是/，再跟任意字符
    doi_pattern = r'^10\.\d{4,}(?:\.\d+)*\/.+$'
    if not re.match(doi_pattern, doi):
        raise ValueError("DOI格式不正确，正确格式如：10.1000/182 或 10.1038/nphys1170")

def add_reference(title: str, authors: str, date: str, journal: str, 
                 category: str, doi: str = '', paper_url: str = '') -> None:
    """添加文献记录"""
    validate_reference_data(title, authors, date, journal, category, doi, paper_url)
    
    # 标准化作者格式（去除多余空格，确保分号后有空格）
    authors = '; '.join(a.strip() for a in authors.split(';'))
    
    db.execute_update(
        '''INSERT INTO "paper_references" (title, authors, date, journal, category, doi, paper_url, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))''',
        (title, authors, date, journal, category, doi, paper_url)
    )

def search_references(keyword: str = '', category: Optional[str] = None) -> List[Tuple]:
    query = '''SELECT * FROM "paper_references" WHERE 1=1'''
    params = []
    
    if keyword:
        query += ''' AND (title LIKE ? OR authors LIKE ? OR journal LIKE ?)'''
        params.extend([f'%{keyword}%'] * 3)
    
    if category:
        query += ' AND category = ?'
        params.append(category)
    
    return db.execute_query(query, tuple(params))

def add_citation(from_id: int, to_id: int) -> None:
    db.execute_update(
        '''INSERT INTO "paper_citations" (from_id, to_id) VALUES (?, ?)''',
        (from_id, to_id)
    )

def get_all_references() -> List[Tuple]:
    return db.execute_query('''SELECT id, title FROM "paper_references"''')

def get_all_citations() -> List[Tuple]:
    return db.execute_query('''SELECT from_id, to_id FROM "paper_citations"''')

def get_reference_by_id(ref_id: int) -> Optional[Tuple]:
    results = db.execute_query(
        '''SELECT * FROM "paper_references" WHERE id = ?''',
        (ref_id,)
    )
    return results[0] if results else None

def update_reference(ref_id: int, **kwargs) -> None:
    """更新文献记录"""
    if not kwargs:
        return
    
    # 获取当前记录
    current = get_reference_by_id(ref_id)
    if not current:
        raise ValueError("找不到指定的文献记录")
    
    # 合并当前值和更新值
    data = {
        'title': current[1],
        'authors': current[2],
        'date': current[3],
        'journal': current[4],
        'category': current[5],
        'doi': current[6],
        'paper_url': current[7],
        'local_pdf': current[8]
    }
    data.update(kwargs)
    
    # 验证更新后的数据
    validate_reference_data(
        data['title'], data['authors'], data['date'], 
        data['journal'], data['category'], data['doi'], 
        data['paper_url']
    )
    
    # 标准化作者格式
    if 'authors' in kwargs:
        data['authors'] = '; '.join(a.strip() for a in kwargs['authors'].split(';'))
    
    # 更新记录
    fields = ', '.join(f"{k} = ?" for k in kwargs.keys())
    query = f'''UPDATE "paper_references" SET {fields}, updated_at = datetime('now') WHERE id = ?'''
    params = list(kwargs.values()) + [ref_id]
    db.execute_update(query, tuple(params))

def delete_reference(ref_id: int) -> None:
    db.execute_update('''DELETE FROM "paper_references" WHERE id = ?''', (ref_id,))

def clear_all_references() -> None:
    """清空所有文献记录、引用关系和PDF文件"""
    try:
        with db.get_connection() as conn:
            cur = conn.cursor()
            # 开始事务
            cur.execute("BEGIN TRANSACTION")
            try:
                # 获取所有PDF文件名
                pdf_files = cur.execute('''SELECT local_pdf FROM "paper_references" WHERE local_pdf IS NOT NULL''').fetchall()
                
                # 删除PDF文件
                pdf_folder = os.path.abspath(os.path.join('data', 'pdfs'))
                for (pdf_file,) in pdf_files:
                    if pdf_file:
                        file_path = os.path.join(pdf_folder, pdf_file)
                        try:
                            if os.path.exists(file_path):
                                os.remove(file_path)
                        except Exception as e:
                            print(f"删除PDF文件失败: {file_path}, 错误: {str(e)}")
                            # 继续执行，不因为文件删除失败而中断整个操作
                
                # 先删除引用关系，因为外键约束
                cur.execute('''DELETE FROM "paper_citations"''')
                # 再删除文献记录
                cur.execute('''DELETE FROM "paper_references"''')
                # 重置自增ID
                cur.execute('''DELETE FROM sqlite_sequence WHERE name IN ('paper_references', 'paper_citations')''')
                
                # 提交事务
                conn.commit()
            except Exception as e:
                # 如果出现任何错误，回滚事务
                conn.rollback()
                raise e
    except Exception as e:
        print(f"清空数据库失败: {str(e)}")
        raise e

