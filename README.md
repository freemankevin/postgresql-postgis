# 🐘 PostgreSQL + PostGIS 镜像  


📦 集成 PostGIS 扩展的 PostgreSQL Docker镜像

## ✨ 功能
- ✅ 支持 PostgreSQL 官方维护期内的安全版本
- 🖥️ 多平台支持（linux/amd64, linux/arm64）
- 🌍 包含 PostGIS 3 和 pgRouting 等常用 GIS 插件扩展
- 🔄 通过 GitHub Actions 自动追溯官方最新补丁版本并同步更新与发布


## 🚀 使用方式
```bash
# 拉取代码
git clone https://github.com/freemankevin/postgresql-postgis.git
cd postgresql-postgis

# 拉取镜像
docker pull freelabspace/postgresql-postgis:18.1

# 使用 docker-compose 启动
docker-compose up -d
```