# 🐘 PostgreSQL + PostGIS 镜像  

📦 集成 PostGIS 扩展的 PostgreSQL Docker镜像

## ✨ 功能

- ✅ 支持 PostgreSQL 官方维护期内的安全版本（14-18）
- 🖥️ 多平台支持（linux/amd64, linux/arm64）
- 🌍 包含 PostGIS 3 和 pgRouting 等常用 GIS 插件扩展
- 🔄 通过 GitHub Actions 自动追溯官方最新补丁版本并同步更新与发布
- 🔧 内置扩展自动启用（28个常用扩展）
- 📊 默认启用 pg_stat_statements 监控
- 🗃️ 支持多数据库创建（POSTGRES_DB逗号分隔）
- 🎯 新建数据库自动继承扩展（template1机制）

## 🚀 快速开始

```bash
# 拉取镜像
docker pull ghcr.io/freemankevin/postgresql-postgis:18.3

# 使用 docker-compose 启动
docker-compose up -d
```

## 📋 内置扩展

镜像在首次启动时自动启用以下扩展：

| 类别 | 扩展列表 |
|------|---------|
| **PostGIS 核心** | postgis, postgis_topology, postgis_raster |
| **地址编码** | postgis_tiger_geocoder, address_standardizer |
| **搜索/文本** | pg_trgm, unaccent, fuzzystrmatch |
| **存储/索引** | hstore, btree_gin, btree_gist, intarray |
| **跨库访问** | dblink, postgres_fdw, file_fdw |
| **监控运维** | pg_stat_statements, pg_buffercache, pg_prewarm |
| **开发工具** | pg_surgery, pageinspect, amcheck, pgrowlocks, pgstattuple |
| **其他** | uuid-ossp, pgcrypto, tablefunc |

## ⚙️ 默认配置

镜像内置以下 PostgreSQL 参数：

- `shared_preload_libraries=pg_stat_statements`
- `pg_stat_statements.track=all`
- `pg_stat_statements.max=10000`

## 🔧 配置覆盖

### 方法 1：环境变量

```yaml
environment:
  - POSTGRES_SHARED_PRELOAD_LIBRARIES=pg_stat_statements,auto_explain
  - POSTGRES_PG_STAT_STATEMENTS_TRACK=top
  - POSTGRES_PG_STAT_STATEMENTS_MAX=5000
```

### 方法 2：命令参数

```yaml
command: >
  postgres
  -c shared_preload_libraries=pg_stat_statements,pgaudit
  -c pg_stat_statements.track=top
  -c pg_stat_statements.max=5000
  -c max_connections=200
  -c shared_buffers=256MB
```

## 🗃️ 多数据库支持

支持通过环境变量创建多个数据库：

```yaml
environment:
  - POSTGRES_DB=postgres,app_db,logging_db,analytics_db
```

**特性**：
- 第一个数据库作为主数据库（POSTGRES_DB）
- 其他数据库自动创建并继承 template1 的所有扩展
- 新建数据库无需手动安装扩展

## 📝 自定义初始化脚本

挂载额外脚本到 `/docker-entrypoint-initdb.d/`：

```yaml
volumes:
  - ./init-scripts:/docker-entrypoint-initdb.d:ro
```

## 🔍 监控支持

镜像内置监控扩展，支持外部监控服务：

```sql
-- SQL 执行统计
SELECT * FROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 10;

-- 数据库活动
SELECT * FROM pg_stat_activity;

-- 缓冲池状态
SELECT * FROM pg_buffercache;
```

**集成 Prometheus**：
```yaml
services:
  postgres_exporter:
    image: prometheuscommunity/postgres-exporter
    environment:
      DATA_SOURCE_NAME: "postgresql://postgres:password@postgres:5432/postgres"
    ports:
      - "9187:9187"
```

## 📦 可用版本

| PostgreSQL 版本 | 镜像标签 |
|----------------|---------|
| 18.x | `ghcr.io/freemankevin/postgresql-postgis:18.3` |
| 17.x | `ghcr.io/freemankevin/postgresql-postgis:17.9` |
| 16.x | `ghcr.io/freemankevin/postgresql-postgis:16.13` |
| 15.x | `ghcr.io/freemankevin/postgresql-postgis:15.17` |
| 14.x | `ghcr.io/freemankevin/postgresql-postgis:14.22` |

## 🛠️ 完整配置示例

```yaml
services:
  postgres:
    image: ghcr.io/freemankevin/postgresql-postgis:18.3
    container_name: postgres
    environment:
      - TZ=Asia/Shanghai
      - POSTGRES_DB=postgres,app_db
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=Postgres@123.com
    ports:
      - "5432:5432"
    volumes:
      - ./data/pgdata:/var/lib/postgresql
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "postgres"]
      interval: 30s
      timeout: 30s
      retries: 3
    restart: unless-stopped
```

## 📚 相关链接

- [PostgreSQL 官方文档](https://www.postgresql.org/docs/)
- [PostGIS 官方文档](https://postgis.net/documentation/)
- [GitHub 仓库](https://github.com/freemankevin/postgresql-postgis)