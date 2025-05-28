import requests
import sqlite3
import os

def download_pdf(url, filename, title, authors, year, journal, category, doi):
    try:
        # 确保文件名以 .pdf 结尾
        if not filename.endswith('.pdf'):
            filename += '.pdf'

        # 创建保存路径
        save_path = os.path.join('data', filename)
        os.makedirs('data', exist_ok=True)  # 确保 data 文件夹存在

        # 下载文件
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            # 检查文件类型是否为 PDF
            content_type = response.headers.get('Content-Type', '')
            if content_type != 'application/pdf':
                print(f"⚠️ 提供的链接不是 PDF 文件，Content-Type: {content_type}")
                return False, f"下载失败：链接不是 PDF 文件，Content-Type: {content_type}"

            # 保存 PDF 文件
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✅ PDF 下载成功: {save_path}")

            # 插入文献信息到数据库
            conn = sqlite3.connect('paper.db')
            cur = conn.cursor()
            cur.execute('''
                INSERT INTO "references" (title, authors, year, journal, category, doi, pdf_link, local_pdf)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (title, authors, year, journal, category, doi, url, filename))
            conn.commit()
            conn.close()
            print("✅ 文献信息已保存到数据库")
            return True, "PDF 下载成功并已保存到数据库！"
        else:
            print(f"⚠️ 下载失败，状态码: {response.status_code}")
            return False, f"下载失败，状态码: {response.status_code}"
    except Exception as e:
        print(f"❌ 下载出错: {e}")
        return False, f"下载出错: {e}"