# 论文管理系统

一个基于Flask的现代化论文管理系统，帮助研究人员高效管理学术文献、追踪引用关系、统计工作量。

## 功能特点

### 1. 文献管理

- 📝 添加、编辑、删除文献信息
- 🔍 多维度搜索（标题、作者、期刊、分类）
- 📊 分类管理（CCF-A/B/C、SCI、EI等）
- 📑 PDF文件管理（上传、在线预览）
- 📤 数据导出（Excel格式）

### 2. 引用关系

- 🔗 可视化引用网络
- 📈 动态展示文献间的引用关系
- 🎨 智能布局，清晰展示引用强度

### 3. 工作量统计

- 👥 作者工作量统计
- 📊 分类权重计算
- 📈 数据可视化展示
- 📤 统计结果导出

### 4. 用户界面

- 🎨 现代化UI设计
- 📱 响应式布局
- ⚡ 流畅的交互体验
- 🎯 直观的操作方式

## 技术栈

- **后端框架**：Flask
- **数据库**：SQLite
- **前端框架**：Bootstrap 5
- **数据可视化**：Matplotlib, NetworkX
- **数据处理**：Pandas
- **其他技术**：
  - HTML5/CSS3
  - JavaScript
  - Bootstrap Icons
  - Font Awesome

## 系统要求

- Python 3.7+
- 现代浏览器（Chrome, Firefox, Edge等）

## 安装部署

1. 克隆项目
   
   ```bash
   git clone https://github.com/leledaidai/Project_paper_system.git
   cd paper-management-system
   ```

2. 安装依赖
   
   ```bash
   pip install -r requirements.txt
   ```

3. 初始化数据库
   
   ```bash
   python init_db.py
   ```

4. 运行应用
   
   ```bash
   python app.py
   ```

## 使用说明

1. **文献管理**
   
   - 点击"添加文献"添加新文献
   - 使用搜索框进行多维度搜索
   - 在管理页面进行编辑、删除操作

2. **引用关系**
   
   - 在关系图谱页面添加引用关系
   - 查看文献间的引用网络
   - 分析引用强度分布

3. **工作量统计**
   
   - 查看作者工作量统计
   - 导出统计数据
   - 分析研究产出

4. **PDF管理**
   
   - 上传文献PDF文件
   - 在线预览PDF
   - 管理本地PDF文件
