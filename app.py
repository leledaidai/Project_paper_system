# app.py
from flask import Flask, render_template, request, redirect, send_file, make_response, flash, url_for
import os
import time
from database import (
    init_db, add_reference, search_references, add_citation,
    get_all_references, get_all_citations, get_reference_by_id,
    update_reference, delete_reference, clear_all_references,
    DatabaseManager
)
from utils import get_score_by_category, export_references_to_excel
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from collections import defaultdict
import datetime

# 配置
DATA_FOLDER = 'data'
PDF_FOLDER = os.path.join(DATA_FOLDER, 'pdfs')
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

app = Flask(__name__)
app.config['PDF_FOLDER'] = PDF_FOLDER
app.config['SECRET_KEY'] = 'dev'  # 用于session等
app.config['DEBUG'] = True  # 开发模式

# 添加全局缓存控制中间件
@app.after_request
def add_header(response):
    # 对于HTML页面，添加缓存控制头
    if response.mimetype == 'text/html':
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# 创建数据库管理器实例
db = DatabaseManager()
init_db()

# 确保必要的目录存在
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)

# 设置matplotlib中文字体
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file):
    if not file or file.filename == '':
        return False, '❌ 未选择文件', None
    
    if not allowed_file(file.filename):
        return False, '❌ 只允许上传PDF文件', None
    
    filename = f"{os.path.splitext(file.filename)[0]}_{int(time.time())}.pdf"
    save_path = os.path.join(app.config['PDF_FOLDER'], filename)
    
    try:
        file.save(save_path)
        return True, '✅ 文件上传成功！', filename
    except Exception as e:
        return False, f'❌ 上传出错: {str(e)}', None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        try:
            add_reference(
                title=request.form['title'],
                authors=request.form['authors'],
                date=request.form['date'],
                journal=request.form['journal'],
                category=request.form['category'],
                doi=request.form['doi'],
                paper_url=request.form['paper_url']
            )
            return redirect('/')
        except ValueError as e:
            return render_template('add.html', error=str(e), categories=categories, now=datetime.datetime.now())
    
    categories = ["CCF-A", "CCF-B", "CCF-C", "SCI", "EI", "其他"]
    return render_template('add.html', categories=categories, now=datetime.datetime.now())

@app.route('/search', methods=['GET'])
def search():
    keyword = request.args.get('q', '')
    category = request.args.get('category', '')
    categories = ["CCF-A", "CCF-B", "CCF-C", "SCI", "EI", "其他"]
    
    results = search_references(keyword, category if category else None)
    return render_template('search.html',
                         keyword=keyword,
                         results=results,
                         categories=categories,
                         selected_category=category)

@app.route('/graph', methods=['GET', 'POST'])
def graph():
    message = ''
    if request.method == 'POST':
        try:
            from_id = int(request.form['from_id'])
            to_id = int(request.form['to_id'])
            if from_id == to_id:
                message = '❌ 不能引用自己！'
            else:
                add_citation(from_id, to_id)
                message = '✅ 引用关系已添加！'
        except ValueError:
            message = '❌ 请选择有效的文献！'

    # 生成引用网络图
    refs = get_all_references()
    citations = get_all_citations()
    G = nx.DiGraph()
    
    # 处理标题，添加换行
    id_title_map = {}
    for id, title in refs:
        # 每20个字符添加换行，但避免在单词中间换行
        words = title.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= 20:  # +1 for space
                current_line.append(word)
                current_length += len(word) + 1
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        id_title_map[id] = '\n'.join(lines)
    
    # 添加节点和边
    for id, title in refs:
        G.add_node(id, label=id_title_map[id])
    for from_id, to_id in citations:
        if from_id in id_title_map and to_id in id_title_map:
            G.add_edge(from_id, to_id)

    # 设置图形样式
    plt.figure(figsize=(12, 8), facecolor='#f8f9fa')  # 使用浅灰色背景
    
    # 使用紧凑的布局
    pos = nx.spring_layout(G, k=0.3, iterations=50)  # 减小k值使布局更紧凑
    
    # 计算节点的入度和出度
    in_degrees = dict(G.in_degree())
    out_degrees = dict(G.out_degree())
    
    # 根据节点的入度和出度设置节点大小
    node_sizes = [1500 + (in_degrees[node] + out_degrees[node]) * 300 for node in G.nodes()]
    
    # 使用更好看的配色方案
    cmap = plt.cm.plasma  # 使用plasma色板，颜色更鲜艳
    node_colors = [cmap(in_degrees[node] / max(in_degrees.values()) if in_degrees.values() else 0) for node in G.nodes()]
    
    # 绘制节点
    nx.draw_networkx_nodes(
        G, pos,
        node_size=node_sizes,
        node_color=node_colors,
        alpha=0.9,
        linewidths=1.5,
        edgecolors='white'
    )
    
    # 绘制边
    nx.draw_networkx_edges(
        G, pos,
        edge_color='#4a4a4a',  # 更深的灰色
        arrows=True,
        arrowsize=15,
        width=1.5,
        alpha=0.5,
        connectionstyle='arc3,rad=0.15'  # 增加弧度
    )
    
    # 绘制标签
    nx.draw_networkx_labels(
        G, pos,
        labels=id_title_map,
        font_size=7,
        font_family='Microsoft YaHei',
        font_weight='bold',
        bbox=dict(
            facecolor='white',
            edgecolor='#e0e0e0',
            alpha=0.9,
            pad=2,
            boxstyle='round,pad=0.3'
        )
    )
    
    # 设置标题和样式
    plt.title('引用网络图', 
             fontsize=16, 
             pad=20, 
             fontweight='bold',
             color='#2c3e50')  # 深蓝灰色标题
    
    plt.axis('off')
    
    # 添加图例说明
    plt.figtext(
        0.02, 0.02,
        '节点大小表示引用关系数量\n节点颜色表示被引用次数',
        fontsize=9,
        color='#2c3e50',
        bbox=dict(
            facecolor='white',
            alpha=0.9,
            edgecolor='#e0e0e0',
            boxstyle='round,pad=0.5'
        )
    )
    
    # 保存图片
    os.makedirs('static', exist_ok=True)
    graph_path = os.path.join('static', 'graph.png')
    plt.savefig(
        graph_path,
        dpi=300,
        bbox_inches='tight',
        pad_inches=0.1,  # 减小边距
        facecolor='#f8f9fa',
        edgecolor='none'
    )
    plt.close()
    
    return render_template('graph.html', 
                         refs=refs, 
                         message=message, 
                         timestamp=int(time.time()))

@app.route('/workload')
def workload():
    workload_stats = defaultdict(lambda: {'count': 0, 'score': 0})
    
    for ref in search_references():
        authors_str = ref[2]
        category = ref[5]
        authors = [a.strip() for a in authors_str.split(';')]
        score = get_score_by_category(category)
        for author in authors:
            if author:
                workload_stats[author]['count'] += 1
                workload_stats[author]['score'] += score
    
    # 将统计结果转换为列表并按工作量分数从高到低排序
    sorted_stats = sorted(
        workload_stats.items(),
        key=lambda x: x[1]['score'],
        reverse=True
    )
    
    # 将排序后的结果转换为列表
    stats_list = list(sorted_stats)
    
    return render_template('workload.html', stats=dict(stats_list))

@app.route('/manage')
def manage():
    return render_template('manage.html', refs=search_references())

@app.route('/edit/<int:ref_id>', methods=['GET', 'POST'])
def edit(ref_id):
    if request.method == 'POST':
        try:
            update_reference(ref_id,
                title=request.form['title'],
                authors=request.form['authors'],
                date=request.form['date'],
                journal=request.form['journal'],
                category=request.form['category'],
                doi=request.form['doi'],
                paper_url=request.form['paper_url']
            )
            return redirect('/manage')
        except ValueError as e:
            return render_template('edit.html', error=str(e), ref=get_reference_by_id(ref_id), now=datetime.datetime.now())
    
    ref = get_reference_by_id(ref_id)
    if not ref:
        return redirect('/manage')
    return render_template('edit.html', ref=ref, now=datetime.datetime.now())

@app.route('/delete/<int:ref_id>')
def delete(ref_id):
    delete_reference(ref_id)
    return redirect('/manage')

@app.route('/upload_pdf/<int:ref_id>', methods=['POST'])
def upload_pdf(ref_id):
    if 'pdf' not in request.files:
        return render_template('upload_pdf_page.html', 
                             ref_id=ref_id, 
                             message='❌ 请选择要上传的文件',
                             message_type='danger')
    
    file = request.files['pdf']
    if not file or file.filename == '':
        return render_template('upload_pdf_page.html', 
                             ref_id=ref_id, 
                             message='❌ 未选择文件',
                             message_type='danger')
    
    if not allowed_file(file.filename):
        return render_template('upload_pdf_page.html', 
                             ref_id=ref_id, 
                             message='❌ 只允许上传PDF文件',
                             message_type='danger')
    
    try:
        # 生成唯一的文件名
        filename = f"{int(time.time())}_{file.filename}"
        save_path = os.path.join(app.config['PDF_FOLDER'], filename)
        
        # 保存文件
        file.save(save_path)
        
        # 更新数据库
        update_reference(ref_id, local_pdf=filename)
        
        return render_template('upload_pdf_page.html',
                             ref_id=ref_id,
                             message='✅ 文件上传成功！',
                             message_type='success')
    except Exception as e:
        return render_template('upload_pdf_page.html',
                             ref_id=ref_id,
                             message=f'❌ 上传失败：{str(e)}',
                             message_type='danger')

@app.route('/view_pdf/<filename>')
def view_pdf(filename):
    """直接查看PDF文件"""
    pdf_path = os.path.join(app.config['PDF_FOLDER'], filename)
    if not os.path.exists(pdf_path):
        return '文件不存在', 404
    return send_file(pdf_path, mimetype='application/pdf')

@app.route('/export')
def export():
    timestamp = int(time.time())
    filename = f'references_{timestamp}.xlsx'
    filepath = os.path.join('data', filename)
    
    export_references_to_excel(filepath)
    
    response = make_response(send_file(filepath, as_attachment=True, download_name=filename))
    response.headers.update({
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    })
    return response

@app.route('/export_workload')
def export_workload():
    workload_stats = defaultdict(lambda: {'count': 0, 'score': 0})
    
    for ref in search_references():
        authors_str = ref[2]
        category = ref[5]
        authors = [a.strip() for a in authors_str.split(';')]
        score = get_score_by_category(category)
        for author in authors:
            if author:
                workload_stats[author]['count'] += 1
                workload_stats[author]['score'] += score
    
    df = pd.DataFrame([
        {"作者": k, "论文数量": v["count"], "工作量分数": v["score"]}
        for k, v in workload_stats.items()
    ])
    
    timestamp = int(time.time())
    filename = f'workload_{timestamp}.xlsx'
    filepath = os.path.join('data', filename)
    
    df.to_excel(filepath, index=False)
    
    response = make_response(send_file(filepath, as_attachment=True, download_name=filename))
    response.headers.update({
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    })
    return response

@app.route('/export_search')
def export_search():
    keyword = request.args.get('q', '')
    category = request.args.get('category', '')
    
    results = search_references(keyword, category if category else None)
    df = pd.DataFrame(results, columns=['ID', '标题', '作者', '年份', '期刊', '分类', 
                                      'DOI', 'PDF链接', '本地PDF', '作者位置', '级别'])
    
    timestamp = int(time.time())
    filename = f'search_results_{timestamp}.xlsx'
    filepath = os.path.join('data', filename)
    
    df.to_excel(filepath, index=False)
    
    response = make_response(send_file(filepath, as_attachment=True, download_name=filename))
    response.headers.update({
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
    })
    return response

@app.route('/clear_all', methods=['POST'])
def clear_all():
    try:
        # 关闭所有数据库连接
        with db.get_connection() as conn:
            conn.close()
        
        # 删除数据库文件
        if os.path.exists('paper.db'):
            os.remove('paper.db')
        
        # 重新初始化数据库
        init_db()
        
        return redirect('/manage')
    except Exception as e:
        return render_template('manage.html', 
                             refs=search_references(),
                             error=f'清空失败：{str(e)}')

@app.route('/upload_pdf_page/<int:ref_id>')
def upload_pdf_page(ref_id):
    """显示上传PDF的页面"""
    ref = get_reference_by_id(ref_id)
    if not ref:
        flash('文献不存在', 'error')
        return redirect(url_for('search'))
    return render_template('upload_pdf.html', ref=ref)

if __name__ == '__main__':
    app.run(debug=True)
