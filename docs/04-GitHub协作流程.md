# GitHub 协作流程

## 第一次上传仓库

由项目负责人执行：

```bash
cd D:\梦境馆\dream-archive-python-mvp
git init
git add .
git commit -m "init dream archive python mvp"
git branch -M main
git remote add origin https://github.com/你的用户名/你的仓库名.git
git push -u origin main
```

## 每个人第一次拉取

```bash
git clone https://github.com/你的用户名/你的仓库名.git
cd 你的仓库名
```

## 每个人创建自己的分支

前端：

```bash
git checkout -b feature/frontend-pages
```

后端：

```bash
git checkout -b feature/backend-api
```

中间数据流：

```bash
git checkout -b feature/data-flow-skill
```

产品经理：

```bash
git checkout -b feature/product-docs
```

## 每次开始写代码前

```bash
git checkout main
git pull origin main
git checkout 你的分支名
git merge main
```

## 每次提交自己的修改

```bash
git status
git add .
git commit -m "说明这次改了什么"
git push origin 你的分支名
```

## 合并流程

1. 在 GitHub 上创建 Pull Request
2. 让至少一个组员检查
3. 没问题后合并到 `main`
4. 其他人执行 `git pull origin main` 更新

## 协作建议

1. 前端尽量只改 `frontend-vue/`
2. 后端尽量只改 `backend-python/app/main.py`、`auth.py`、`database.py`
3. 中间数据流主要改 `analysis_skill.py` 和接口文档
4. 产品经理主要改 `docs/` 和 `README.md`
5. 不要把 `.venv/`、`node_modules/`、数据库 `.db` 文件上传

