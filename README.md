---
title: git用法
katex: true
date: 2025-03-31 14:30:46
tags: git
categories: 网络研究
---
# Git 使用指南

## 目录
1. [基础操作](#基础操作)
2. [SSH 密钥配置](#ssh-密钥配置)
3. [拉取/同步/推送](#拉取同步推送)
4. [Sparse Checkout](#sparse-checkout)
5. [更多实用指令](#更多实用指令)
6. [注意事项](#注意事项)

---

## 基础操作

### 初始化仓库并连接远程
```bash
# 新建文件夹并初始化 Git
mkdir project && cd project
git init

# 关联远程仓库
git remote add origin git@github.com:zhouzhou12203/documents.git

# 查看远程仓库地址
git remote -v

# 首次推送代码
git add .
git commit -m "Initial commit"
git push -u origin main  # 若默认分支为 main

# 检出指定文件到工作区
git checkout origin/main -- python/test/star.py

# 下载远程文件到本地（不修改 Git 记录）
git show origin/main:python/test/star.py > py-win/test/star.py

#设置本地分支的追踪信息(origin/mainy远程；main本地)
git branch --set-upstream-to=origin/main main

```

---

## SSH 密钥配置

### 生成 SSH 密钥
```bash
ssh-keygen -t ed25519 -C "your_email@example.com"
# 默认保存路径：~/.ssh/id_ed25519
```
### 修改远程仓库 SSH 地址
```bash
git remote set-url origin git@github.com:zhouzhou12203/documents.git
```
### 添加密钥到 Git 平台
1. 复制公钥内容：
```bash
cat ~/.ssh/id_ed25519.pub
```
2. 粘贴到 GitHub/GitLab 的 **SSH Keys** 设置中

### 测试连接
```bash
ssh -T git@github.com  # GitHub
ssh -T git@gitlab.com  # GitLab
```

---

## 拉取/同步/推送

### 拉取远程变更
```bash
git pull origin main       # 拉取并合并
git reset --hard origin/main  #将本地重置为远程
git fetch origin          # 仅获取远程变更（不合并）
git log origin/main        #查看 origin/main 的最新提交
git diff main origin/main   #比较你的本地 main 分支和远程 origin/main 分支的差异


#合并远程分支的更新
git checkout main  # 确保你在 main 分支
git merge origin/main

```

### 推送本地变更
```bash
git push origin main      # 推送到指定分支
git push -f origin main   # 强制推送（谨慎使用）
```

### 解决冲突后同步
```bash
git pull origin main
# 手动解决冲突后
git add .
git commit -m "Resolve conflicts"
git push origin main
```

---

## Sparse Checkout

### 使用场景
仅克隆仓库的特定目录（适用于大型仓库）

### 操作步骤
```bash
mkdir repo && cd repo
git init
git remote add origin git@github.com:username/repo.git
git config core.sparseCheckout true

# 查看稀疏检出配置
cat .git/info/sparse-checkout

# 指定需要拉取的目录
echo "src/docs/" >> .git/info/sparse-checkout
echo "config/" >> .git/info/sparse-checkout

# 拉取文件
git pull origin main

```

---

## 更多实用指令

### 分支管理
```bash
git branch -a                  # 查看所有分支
git checkout -b feature        # 创建并切换分支
git merge feature              # 合并分支到当前分支
git branch -d feature          # 删除本地分支
git checkout main              # 切换到 main 分支
git branch --set-upstream-to=origin/main main # 设置追踪关系
```

### 撤销操作
```bash
git reset --soft HEAD^         # 撤销 commit，保留更改
git reset --hard HEAD^         # 彻底丢弃最近一次 commit
git checkout -- file.txt      # 撤销文件的未暂存修改
```

### 日志与对比
```bash
git log --oneline --graph      # 简洁版提交历史
git diff HEAD~1..HEAD          # 对比最近两次提交
```

### 高级功能
```bash
git stash                      # 临时保存未提交的更改
git tag v1.0                   # 创建标签
git rebase main                # 变基到 main 分支
git clean -fd                  # 删除未跟踪的文件/文件夹
```

---

## 注意事项
1. **强制推送风险**：`git push -f` 会覆盖远程历史，需团队协商后使用
2. **冲突处理**：拉取代码时优先解决冲突再推送
3. **SSH 权限**：确保密钥文件的权限为 `600`（`chmod 600 ~/.ssh/id_ed25519`）
4. **Sparse Checkout**：后续新增目录需手动添加到 `.git/info/sparse-checkout`

> 更多细节参考 [Git 官方文档](https://git-scm.com/doc)



# 设置代理
```bash
git config --global http.proxy socks5 127.0.0.1:7890
git config --global https.proxy socks5 127.0.0.1:7890
git config --global http.proxy 127.0.0.1:7890
git config --global https.proxy 127.0.0.1:7890
```
#查看代理
```bash
git config --global --get http.proxy
git config --global --get https.proxy
```
清除代理
```bash
git config --global --unset http.proxy
git config --global --unset https.proxy
```
