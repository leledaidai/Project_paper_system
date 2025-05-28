# app.py
from flask import Flask, render_template, request, redirect, send_file
from isort import file
from database import init_db, add_reference, search_references
import os
from werkzeug.utils import secure_filename
import sqlite3
import matplotlib.font_manager as fm
from database import get_all_references, get_all_citations, add_citation
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import time
import pandas as pd


UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf'}


app = Flask(__name__)
init_db()  # 初始化数据库
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

font_path = "./fonts/SimHei.ttf"
my_font = fm.FontProperties(fname=font_path)

# 设置全局字体（这样 nx.draw 会自动使用这个字体）
plt.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        title = request.form['title']
        authors = request.form['authors']
        year = request.form['year']
        journal = request.form['journal']
        category = request.form['category']
        doi = request.form['doi']
        pdf_link = request.form['pdf_link']
        add_reference(title, authors, year, journal, category, doi, pdf_link)
        return redirect('/')
    return render_template('add.html')


@app.route('/search', methods=['GET'])
def search():
    keyword = request.args.get('q', '')
    results = search_references(keyword)
    return render_template('search.html', keyword=keyword, results=results)


from downloader import download_pdf

@app.route('/download', methods=['GET', 'POST'])
def download():
    message = ''
    if request.method == 'POST':
        url = request.form['url']
        filename = request.form['filename']
        title = request.form['title']
        authors = request.form['authors']
        year = int(request.form['year'])
        journal = request.form['journal']
        category = request.form['category']
        doi = request.form['doi']

        success, msg = download_pdf(url, filename, title, authors, year, journal, category, doi)
        message = msg
    return render_template('download.html', message=message)

from utils import export_references_to_excel


from flask import send_file, make_response

@app.route('/export')
def export():
    import time
    timestamp = int(time.time())
    filename = f'references_{timestamp}.xlsx'
    filepath = os.path.join('data', filename)

    export_references_to_excel(filepath)

    # 使用 make_response 并设置 Cache-Control
    response = make_response(send_file(
        filepath,
        as_attachment=True,
        attachment_filename=filename  # 新版 Flask 推荐使用 download_name
    ))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response



@app.route('/graph', methods=['GET', 'POST'])
def graph():
    refs = get_all_references()
    message = ''
    if request.method == 'POST':
        from_id = int(request.form['from_id'])
        to_id = int(request.form['to_id'])
        add_citation(from_id, to_id)
        message = '引用关系已添加！'

    # 创建引用网络图
    citations = get_all_citations()
    G = nx.DiGraph()
    id_title_map = dict(refs)
    for id, title in refs:
        G.add_node(id, label=title)
    for from_id, to_id in citations:
        G.add_edge(from_id, to_id)

    # 生成图像
    plt.figure(figsize=(10, 7),constrained_layout=True)
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, labels=id_title_map, node_size=1500, node_color='skyblue', font_size=8, arrows=True)
    # plt.tight_layout()

    graph_path = os.path.join('static', 'graph.png')
    plt.savefig(graph_path)
    plt.close()
    timestamp = int(time.time())  # 👈 获取当前时间戳

    return render_template('graph.html', refs=refs, message=message, timestamp=timestamp)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    message = ''
    if request.method == 'POST':
        file = request.files['pdf']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(save_path)

            # 提交论文元信息和 PDF 路径
            title = request.form['title']
            authors = request.form['authors']
            year = int(request.form['year'])
            journal = request.form['journal']
            category = request.form['category']
            doi = request.form['doi']
            pdf_link = ''
            local_pdf = filename

            conn = sqlite3.connect('paper.db')
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO "references" (title, authors, year, journal, category, doi, pdf_link, local_pdf)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, authors, year, journal, category, doi, pdf_link, local_pdf))
            
            conn.commit()
            conn.close()

            message = '✅ 文件上传并保存成功！'
        else:
            message = '❌ 请选择有效的 PDF 文件上传！'

    return render_template('upload.html', message=message)

from utils import get_score_by_category
from collections import defaultdict

@app.route('/workload')
def workload():
    conn = sqlite3.connect('paper.db')
    cur = conn.cursor()
    cur.execute("SELECT authors, category FROM \"references\"")
    data = cur.fetchall()
    conn.close()

    workload_stats = defaultdict(lambda: {'count': 0, 'score': 0})

    for authors_str, category in data:
        authors = [a.strip() for a in authors_str.split(',')]
        score = get_score_by_category(category)
        for author in authors:
            workload_stats[author]['count'] += 1
            workload_stats[author]['score'] += score

    return render_template('workload.html', stats=workload_stats)


@app.route('/export_workload')
def export_workload():

    import time
    timestamp = int(time.time())
    filename = f'workload_{timestamp}.xlsx'
    filepath = os.path.join('data', filename)

    conn = sqlite3.connect('paper.db')
    cur = conn.cursor()
    cur.execute("SELECT authors, category FROM \"references\"")
    data = cur.fetchall()
    conn.close()

    workload_stats = defaultdict(lambda: {'count': 0, 'score': 0})
    for authors_str, category in data:
        authors = [a.strip() for a in authors_str.split(',')]
        score = get_score_by_category(category)
        for author in authors:
            workload_stats[author]['count'] += 1
            workload_stats[author]['score'] += score

    df = pd.DataFrame([
        {"作者": k, "论文数量": v["count"], "工作量分数": v["score"]}
        for k, v in workload_stats.items()
    ])

    
    df.to_excel(filepath, index=False)

    # 使用 make_response 设置 Cache-Control
    response = make_response(send_file(filepath, as_attachment=True, attachment_filename=filename))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response

@app.route('/manage')
def manage():
    conn = sqlite3.connect('paper.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM \"references\"")
    refs = cur.fetchall()
    conn.close()
    return render_template('manage.html', refs=refs)


@app.route('/edit/<int:ref_id>', methods=['GET', 'POST'])
def edit(ref_id):
    conn = sqlite3.connect('paper.db')
    cur = conn.cursor()
    if request.method == 'POST':
        title = request.form['title']
        authors = request.form['authors']
        year = int(request.form['year'])
        journal = request.form['journal']
        category = request.form['category']
        doi = request.form['doi']
        pdf_link = request.form['pdf_link']

        cur.execute('''
            UPDATE "references" SET title=?, authors=?, year=?, journal=?, category=?, doi=?, pdf_link=? 
            WHERE id=?
        ''', (title, authors, year, journal, category, doi, pdf_link, ref_id))
        conn.commit()
        conn.close()
        return redirect('/manage')
    else:
        cur.execute("SELECT * FROM \"references\" WHERE id=?", (ref_id,))
        ref = cur.fetchone()
        conn.close()
        return render_template('edit.html', ref=ref)

@app.route('/delete/<int:ref_id>')
def delete(ref_id):
    conn = sqlite3.connect('paper.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM \"references\" WHERE id=?", (ref_id,))
    conn.commit()
    conn.close()
    return redirect('/manage')


if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    app.run(debug=True)
