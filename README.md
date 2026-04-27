# 🐘 PostgreSQL + PostGIS 镜像  

📦 集成 PostGIS 扩展的 PostgreSQL Docker镜像

## ✨ 功能

- ✅ 支持 PostgreSQL 官方维护期内的安全版本（14-18）
- 🖥️ 多平台支持（linux/amd64, linux/arm64）
- 🌍 包含 PostGIS 3 和 pgRouting 等常用 GIS 插件扩展
- 🔄 通过 GitHub Actions 自动追溯官方最新补丁版本并同步更新与发布
- 🔧 内置扩展自动启用（33个常用扩展）
- 📊 默认启用 pg_stat_statements 监控
- 🔒 默认启用 pgaudit 审计日志
- 🔍 默认启用 auto_explain 慢查询执行计划记录
- 🗃️ 支持多数据库创建（POSTGRES_DB逗号分隔）
- 🎯 新建数据库自动继承扩展（template1机制）

## 🚀 快速开始

```bash
# 拉取镜像
docker pull ghcr.io/freemankevin/postgresql-postgis:18.3

# 使用 docker-compose 启动
docker-compose up -d
```

## 🔧 环境变量

### 基础配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `POSTGRES_USER` | `postgres` | 超级用户名 |
| `POSTGRES_PASSWORD` | - | 超级用户密码（必填） |
| `POSTGRES_DB` | `postgres` | 数据库名（支持逗号分隔创建多个） |
| `POSTGRES_INITDB_ARGS` | - | initdb 额外参数 |
| `POSTGRES_INITDB_WALDIR` | - | WAL 目录位置 |
| `POSTGRES_HOST_AUTH_METHOD` | - | 主机认证方法 |
| `PGDATA` | `/var/lib/postgresql/data` | 数据目录 |
| `TZ` | `UTC` | 时区设置 |

### 性能调优

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `POSTGRES_SHARED_PRELOAD_LIBRARIES` | `pg_stat_statements,pgaudit,auto_explain` | 预加载共享库 |
| `POSTGRES_PG_STAT_STATEMENTS_TRACK` | `all` | 语句跟踪级别 |
| `POSTGRES_PG_STAT_STATEMENTS_MAX` | `10000` | 最大跟踪语句数 |

### 慢查询分析

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `POSTGRES_AUTO_EXPLAIN_LOG_MIN_DURATION` | `1000` | 自动记录执行计划阈值（毫秒） |
| `POSTGRES_AUTO_EXPLAIN_LOG_ANALYZE` | `on` | 执行实际分析（EXPLAIN ANALYZE） |
| `POSTGRES_AUTO_EXPLAIN_LOG_BUFFERS` | `on` | 记录缓冲区使用情况 |
| `POSTGRES_AUTO_EXPLAIN_LOG_TIMING` | `on` | 记录执行时间 |

### 审计配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `POSTGRES_PGAUDIT_LOG` | `write,ddl` | 审计日志类别（read/write/ddl/function/role/misc/all） |
| `POSTGRES_PGAUDIT_LOG_RELATION` | `on` | 记录表引用 |
| `POSTGRES_PGAUDIT_LOG_PARAMETER` | `on` | 记录 SQL 参数值 |

### 日志配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `POSTGRES_COLORIZE_LOGS` | `true` | 启用彩色日志输出 |
| `POSTGRES_LOG_LINE_PREFIX` | `%m [%p] %q%u@%d }` | 日志行前缀格式 |
| `POSTGRES_LOG_STATEMENT` | `ddl` | 记录语句级别（none/ddl/mod/all） |
| `POSTGRES_LOG_MIN_DURATION_STATEMENT` | `1000` | 慢查询阈值（毫秒），-1 禁用 |
| `POSTGRES_LOG_CONNECTIONS` | `on` | 记录连接事件 |
| `POSTGRES_LOG_DISCONNECTIONS` | `on` | 记录断开连接事件 |
| `POSTGRES_LOG_LOCK_WAITS` | `on` | 记录锁等待事件 |
| `POSTGRES_LOG_CHECKPOINTS` | `on` | 记录检查点事件 |
| `POSTGRES_LOG_TEMP_FILES` | `0` | 记录临时文件（0 记录所有） |

## 📋 内置扩展

镜像在首次启动时自动启用以下扩展：

| 类别 | 扩展列表 |
|------|---------|
| **PostGIS 核心** | postgis, postgis_topology, postgis_raster |
| **地址编码** | postgis_tiger_geocoder, address_standardizer |
| **搜索/文本** | pg_trgm, unaccent, fuzzystrmatch |
| **存储/索引** | hstore, btree_gin, btree_gist, intarray |
| **跨库访问** | dblink, postgres_fdw, file_fdw |
| **监控运维** | pg_stat_statements, pg_buffercache, pg_prewarm, pgaudit |
| **故障排查** | pg_surgery, pageinspect, amcheck, pgrowlocks, pgstattuple, pg_visibility, pg_freespacemap |
| **性能分析** | pg_stat_kcache, pg_wait_sampling, auto_explain |
| **开发工具** | pg_surgery, pageinspect, amcheck |
| **其他** | uuid-ossp, pgcrypto, tablefunc |

## ⚙️ 默认配置

镜像内置以下 PostgreSQL 参数：

- `shared_preload_libraries=pg_stat_statements,pgaudit,auto_explain`
- `pg_stat_statements.track=all`
- `pg_stat_statements.max=10000`
- `pgaudit.log=write,ddl`
- `pgaudit.log_relation=on`
- `pgaudit.log_parameter=on`
- `auto_explain.log_min_duration=1000`
- `auto_explain.log_analyze=on`
- `auto_explain.log_buffers=on`
- `auto_explain.log_timing=on`

### 日志颜色说明

| 日志级别 | 颜色 |
|----------|------|
| FATAL / PANIC / ERROR | 🔴 红色 |
| WARNING | 🟡 黄色 |
| LOG / INFO | 🔵 青色 |
| DEBUG | 🟣 紫色 |
| SQL 语句 | 🟢 绿色 |
| 连接信息 | 🔵 蓝色 |

## 🔧 配置覆盖

### 命令参数方式

```yaml
command: >
  postgres
  -c shared_preload_libraries=pg_stat_statements,pgaudit,auto_explain,pg_wait_sampling
  -c pg_stat_statements.track=top
  -c pg_stat_statements.max=5000
  -c auto_explain.log_min_duration=500
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

## 🔒 审计日志

镜像默认启用 `pgaudit` 扩展进行操作审计：

### 审计内容

默认记录以下操作：
- **DDL 操作**: CREATE/ALTER/DROP 等结构变更
- **写入操作**: INSERT/UPDATE/DELETE 数据变更
- **表引用**: 记录操作涉及的表名
- **参数值**: 记录 SQL 语句中的参数

### 审计日志示例

```
2026-04-27 10:00:00.123 CST [123] postgres@testdb LOG:  AUDIT: SESSION,1,1,WRITE,INSERT,,,"INSERT INTO users (name) VALUES ('test')"
```

### 自定义审计配置

```yaml
environment:
  # 记录所有操作（包括 SELECT）
  - POSTGRES_PGAUDIT_LOG=read,write,ddl
  
  # 仅记录写入和 DDL
  - POSTGRES_PGAUDIT_LOG=write,ddl
  
  # 禁用参数记录（敏感数据）
  - POSTGRES_PGAUDIT_LOG_PARAMETER=off
```

### 禁用审计

```yaml
environment:
  - POSTGRES_SHARED_PRELOAD_LIBRARIES=pg_stat_statements
  - POSTGRES_PGAUDIT_LOG=
```

## 🔧 故障排查

镜像内置多种诊断工具，方便排查数据库问题：

### 慢查询分析

**auto_explain** 自动记录超过阈值的查询执行计划：

```
2026-04-27 10:00:00.123 CST [123] postgres@testdb LOG:  duration: 1500.123 ms  plan:
Query Text: SELECT * FROM large_table WHERE status = 'active'
Index Scan using idx_status on large_table  (cost=0.43..1000.00 rows=1000 width=100)
  Index Cond: (status = 'active'::text)
```

### 等待事件分析

```sql
-- 查看当前等待事件
SELECT * FROM pg_wait_sampling_current;

-- 等待事件统计历史
SELECT * FROM pg_wait_sampling_history ORDER BY count DESC LIMIT 10;
```

### CPU/IO 分析

```sql
-- 内核级 CPU 和磁盘 I/O 统计
SELECT * FROM pg_stat_kcache;

-- 按查询分析资源消耗
SELECT queryid, calls, 
       plan_cpu_time, exec_cpu_time, 
       plan_reads, exec_reads
FROM pg_stat_kcache_queries 
ORDER BY exec_cpu_time DESC LIMIT 10;
```

### 数据损坏检查

```sql
-- 检查索引完整性
SELECT * FROM bt_index_check('idx_name');

-- 检查表页面
SELECT * FROM pageinspect_get_page_raw('tablename', 0);

-- 可见性问题排查
SELECT * FROM pg_visibility_map('tablename');

-- 空闲空间检查
SELECT * FROM pg_freespacemap_pages('tablename');
```

### 行锁诊断

```sql
-- 查看被锁住的行
SELECT * FROM pgrowlocks('tablename');

-- 当前锁等待
SELECT blocked.pid, blocked.query, blocking.pid, blocking.query
FROM pg_locks blocked
JOIN pg_locks blocking ON blocked.locktype = blocking.locktype
WHERE blocked.granted = false AND blocking.granted = true;
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

