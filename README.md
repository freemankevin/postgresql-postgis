# 🐘 PostgreSQL with PostGIS Docker 镜像

📦 本仓库提供了一个包含 PostGIS 扩展的 PostgreSQL Docker 镜像。

## ✨ 功能
- ✅ 支持 PostgreSQL 12 到 17 版本
- 🌍 包含 PostGIS 3 和 pgRouting 扩展
- 🔄 通过 GitHub Actions 自动更新版本

## 🚀 使用方式
1. 拉取镜像：
   ```bash
   docker.io/freelabspace/postgresql-postgis:12.22
   ```
2. 运行容器：
   ```bash
   docker-compose up -d
   ```

## ⚙️ CI/CD
- 🔄 自动构建，由 PostgreSQL 版本更新触发
- 🖥️ 多平台支持（linux/amd64, linux/arm64）

## 📜 开源协议
Apache 2.0