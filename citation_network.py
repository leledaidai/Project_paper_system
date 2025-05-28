import sqlite3
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import matplotlib.font_manager as fm

# # 最简单有效的配置（适合本地开发环境）
# plt.rcParams['font.sans-serif'] = ['SimHei', 'SimSun', 'Microsoft YaHei']
# plt.rcParams['axes.unicode_minus'] = False

# 加载本地中文字体文件
font_path = "./fonts/SimHei.ttf"  
my_font = fm.FontProperties(fname=font_path)

print(f"使用字体：{my_font.get_name()}")

def draw_citation_graph():
    conn = sqlite3.connect("paper.db")
    cur = conn.cursor()

    cur.execute("SELECT citing_id, cited_id FROM citations")
    edges = cur.fetchall()

    G = nx.DiGraph()
    G.add_edges_from(edges)

    if not G.nodes:
        print("⚠️ 没有引用数据，请先手动添加引用关系。")
        return

    pos = nx.kamada_kawai_layout(G)

    plt.figure(figsize=(10, 6))
    nx.draw_networkx(
        G,
        pos=pos,
        with_labels=True,
        node_color='lightblue',
        edge_color='gray',
        font_size=10,
        font_properties=my_font  # 使用我们手动加载的字体
    )
    plt.title("引用网络图")
    plt.tight_layout()

    os.makedirs("static", exist_ok=True)
    plt.savefig("static/graph.png", format="png", bbox_inches="tight")
    plt.close()
    conn.close()

# 调用函数
draw_citation_graph()