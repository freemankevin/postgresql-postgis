# 🐘 PostgreSQL with PostGIS Docker 镜像

📦 本仓库提供了一个包含 PostGIS 扩展的 PostgreSQL Docker 镜像。

## ✨ 功能
- ✅ 支持 PostgreSQL 12 到 17 版本
- 🌍 包含 PostGIS 3 和 pgRouting 扩展
- 🔄 通过 GitHub Actions 自动更新版本

## 🚀 使用方式
1. 构建镜像：
   ```bash
   docker build -t postgresql-postgis .
   ```
2. 运行容器：
   ```bash
   docker run -d -p 5432:5432 postgresql-postgis
   ```

## ⚙️ CI/CD
- 🔄 自动构建，由 PostgreSQL 版本更新触发
- 🖥️ 多平台支持（linux/amd64, linux/arm64）

## 📜 开源协议
Apache 2.0