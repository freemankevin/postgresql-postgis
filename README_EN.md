# 🐘 PostgreSQL + PostGIS Docker Image [中文](README.md)

📦 Docker image of PostgreSQL with PostGIS extension

## ✨ Features
- ✅ Supports PostgreSQL versions 12 to 17
- 🖥️ Multi-platform support (linux/amd64, linux/arm64)
- 🌍 Includes PostGIS 3 and pgRouting extensions
- 🔄 Automatically tracks latest patch versions via GitHub Actions

## 🚀 Usage
```bash
# Clone the repository
git clone https://github.com/freemankevin/postgresql-postgis.git
cd postgresql-postgis

# Pull the image
docker pull freelabspace/postgresql-postgis:12.22

# Start with docker-compose
docker-compose up -d
```