# 梦境馆 Python MVP

这是“梦境记录 & 梦境解析档案馆”的 Python 版 MVP，可直接作为 GitHub 仓库上传和多人协作。

## 功能范围

第一版只做：

1. 梦境记录
2. 梦境分析
3. 匿名社区分享
4. 管理员监管和删除危险分享

## 项目结构

```text
dream-archive-python-mvp/
  backend-python/        Python FastAPI 后端
  frontend-vue/          Vue3 前端
  database/              SQLite 初始化脚本和说明
  docs/                  分工、接口、Skill、GitHub 协作说明
  .gitignore             Git 忽略规则
  README.md              项目总说明
```

## 技术栈

- 前端：Vue3 + Vite + Axios
- 后端：Python + FastAPI + SQLite
- 分析模块：关键词匹配 + 规则分析 + AI API 预留
- 协作方式：GitHub 分支开发 + Pull Request 合并

## 快速启动

### 1. 启动后端

```bash
cd backend-python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python init_db.py
uvicorn app.main:app --reload --port 8080
```

### 2. 启动前端

```bash
cd frontend-vue
npm install
npm run dev
```

访问：

```text
http://localhost:5173
```

## 演示账号

普通用户：

```text
alice / 123456
```

管理员：

```text
admin / admin123
```

## 上传 GitHub

```bash
git init
git add .
git commit -m "init dream archive python mvp"
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

