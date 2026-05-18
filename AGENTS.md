# AGENTS.md — PostgreSQL + PostGIS Docker 镜像

> 本文档面向 AI 编码助手。如果你从未接触过本项目，请先阅读此文件再动手修改代码。

---

## 项目概述

本项目是一个 **Docker 镜像打包工程**，目标是为 PostgreSQL 官方镜像叠加 PostGIS 3、pgRouting 及 30+ 个常用扩展，构建多架构（linux/amd64、linux/arm64）容器镜像，并通过 GitHub Actions 自动追踪上游补丁版本、自动构建与发布到 GHCR（GitHub Container Registry）。

镜像仓库：`ghcr.io/freemankevin/postgresql-postgis`

**不是**常规的应用程序代码库，**没有**单元测试框架、依赖管理文件（如 package.json / pyproject.toml / Cargo.toml）或运行时服务代码。核心交付物是 Dockerfile、初始化脚本与 CI 工作流。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 基础镜像 | `postgres:${PG_VERSION}-bookworm` (Debian 12) |
| 扩展包 | PostGIS 3、pgRouting、pgaudit、auto_explain、pg_wait_sampling、pg_stat_kcache、postgresql-contrib 等 |
| 脚本语言 | Bash（初始化与日志着色）、Python 3.11（构建辅助） |
| CI/CD | GitHub Actions |
| 镜像仓库 | GHCR (GitHub Packages) |
| 容器编排 | Docker Compose（仅本地示例） |

---

## 目录结构

```
postgresql-postgis/
├── Dockerfile                          # 镜像构建定义
├── docker-compose.yml                  # 本地快速启动示例
├── pg_version.json                     # 维护的 PG 版本映射 {主版本: 完整版本}
├── README.md                           # 面向用户的文档（中文）
├── LICENSE                             # Apache-2.0
├── Scripts/
│   ├── 01-install-extensions-template1.sql   # 在 template1 中安装扩展，使新库自动继承
│   ├── 03-create-extra-databases.sh          # 根据 POSTGRES_EXTRA_DATABASES 创建额外数据库
│   ├── 99-enable-all-extensions.sql          # 在 POSTGRES_DB 目标库中启用扩展
│   ├── docker-entrypoint.sh                  # 包装官方 entrypoint，注入默认配置与日志着色
│   ├── pg-log-formatter.sh                   # 日志着色函数库（ANSI 颜色）
│   └── build-helper.py                       # CI 辅助：版本检查、构建决策、README 同步、旧镜像清理
└── .github/
    └── workflows/
        └── ci.yml                          # 完整 CI/CD：版本检查 → 构建矩阵 → 多平台推送 → 清理旧标签
```

**关键约定**：
- `Scripts/*.sql` 按数字前缀顺序执行（`01-*`、`03-*`、`99-*`），由官方 postgres 镜像的 `/docker-entrypoint-initdb.d/` 机制在首次启动时自动运行。
- `pg_version.json` 是 CI 与本地构建的唯一版本事实来源，必须保持与 `Dockerfile` 的 `ARG` 默认值同步。

---

## 运行时架构

### 启动流程

1. 容器启动 → 执行 `docker-entrypoint-wrapper.sh`（即 `Scripts/docker-entrypoint.sh`）。
2. 如果 `POSTGRES_DB` 包含逗号，脚本将其拆分为 `POSTGRES_DB`（第一个）和 `POSTGRES_EXTRA_DATABASES`（其余）。
3. 若用户未通过命令行参数覆盖，则注入默认 PostgreSQL 配置项：
   - `shared_preload_libraries=pg_stat_statements,pgaudit,auto_explain`
   - `pg_stat_statements.track=all`
   - `pgaudit.log=write,ddl`
   - `auto_explain.log_min_duration=1000`
   - 各类日志参数（连接、断开、锁等待、检查点、临时文件等）
4. 如果 `POSTGRES_COLORIZE_LOGS=true`（默认），将官方 entrypoint 的标准输出通过 `colorize_log` 管道着色。
5. 官方 postgres entrypoint 接管，执行 initdb（如数据目录为空）。
6. initdb 完成后，按字母/数字顺序执行 `/docker-entrypoint-initdb.d/` 中的脚本：
   - `01-install-extensions-template1.sql`：在 `template1` 创建扩展，后续新建数据库自动继承。
   - `03-create-extra-databases.sh`：创建逗号分隔的额外数据库。
   - `99-enable-all-extensions.sql`：在目标数据库显式启用扩展。

### 默认启用的扩展（33+）

| 类别 | 扩展 |
|------|------|
| PostGIS 核心 | postgis, postgis_topology, postgis_raster |
| 地址编码 | postgis_tiger_geocoder, address_standardizer, address_standardizer_data_us |
| 搜索/文本 | pg_trgm, unaccent, fuzzystrmatch |
| 存储/索引 | hstore, btree_gin, btree_gist, intarray |
| 跨库访问 | dblink, postgres_fdw, file_fdw |
| 监控运维 | pg_stat_statements, pg_buffercache, pg_prewarm, pgaudit |
| 性能分析 | pg_stat_kcache, pg_wait_sampling, auto_explain |
| 开发/诊断 | pg_surgery, pageinspect, amcheck, pgrowlocks, pgstattuple, pg_freespacemap, pg_visibility |
| 其他 | uuid-ossp, pgcrypto, tablefunc |

---

## 构建与测试

### 本地构建

```bash
# 构建指定版本（以 PG 18 为例）
docker build \
  --build-arg PG_MAJOR=18 \
  --build-arg PG_VERSION=18.3 \
  -t postgresql-postgis:18.3 .

# 本地启动测试
docker-compose up -d
```

### 构建辅助脚本

`Scripts/build-helper.py` 是 CI 的核心，也可在本地调试使用：

```bash
# 检查 Docker Hub 上是否有新补丁版本，并更新 pg_version.json
python Scripts/build-helper.py check-versions

# 更新 README.md 中的版本表格
python Scripts/build-helper.py update-readme

# 生成构建矩阵（JSON）
python Scripts/build-helper.py matrix all

# 判断某个主版本是否需要构建
python Scripts/build-helper.py should-build 18 --manual

# 清理 GHCR 上该主版本的旧镜像标签（需 GITHUB_TOKEN）
python Scripts/build-helper.py cleanup 18
```

**注意**：辅助脚本依赖 `requests`（`pip install requests`）。

### 测试策略

本项目**没有传统单元测试**，验证方式如下：

1. **镜像构建测试**：`docker build` 成功即表示 Dockerfile 与 apt 包名正确。
2. **运行时功能测试**：启动容器后执行 `SELECT postgis_version();` 或 `\dx` 验证扩展是否加载。
3. **多数据库测试**：设置 `POSTGRES_DB=postgres,db1,db2`，确认三个数据库均存在且扩展已继承。
4. **CI 门禁**：GitHub Actions 在合并到 `main` 分支或手动触发时执行完整构建。

建议修改后至少执行：

```bash
docker build --build-arg PG_MAJOR=18 --build-arg PG_VERSION=18.3 -t pg-test .
docker run --rm -e POSTGRES_PASSWORD=test -e POSTGRES_DB=postgres,db2 -p 5432:5432 pg-test
# 在另一个终端验证
docker exec -it <container> psql -U postgres -c "\dx"
docker exec -it <container> psql -U postgres -d db2 -c "\dx"
```

---

## CI/CD 流程

工作流文件：`.github/workflows/ci.yml`

### 触发条件

- **定时触发**：每天 02:00 UTC 检查上游新版本。
- **Push 触发**：`main` 分支的 `Dockerfile`、`Scripts/**`、`.github/workflows/ci.yml` 变更。
- **手动触发**：`workflow_dispatch`，可选指定版本、强制重建、跳过旧镜像清理。

### 作业流程

1. **check-versions**
   - 运行 `build-helper.py check-versions` 查询 Docker Hub 的 `postgres:*-bookworm` 标签。
   - 若版本变化，自动提交 `pg_version.json` 并更新 `README.md`。
   - 输出版本矩阵供下游使用。

2. **build**（矩阵并行，max-parallel=6）
   - 对每个主版本运行 `should-build` 决策：
     - 若 GHCR 上已存在对应标签且非强制重建，则跳过。
     - 双重检查上游镜像是否在 Docker Hub 存在。
   - 使用 `docker buildx` 构建多平台镜像并推送至 GHCR。
   - 构建完成后清理该主版本的旧 GHCR 标签（仅保留当前最新补丁版本）。

### 权限要求

- `contents: write`（自动提交版本更新）
- `packages: write`（推送与删除 GHCR 镜像）

---

## 代码风格与开发约定

### 语言与注释

- **文档与注释使用中文**。README.md、脚本内注释、CI 输出均使用中文。
- SQL 脚本使用大写的关键字（`CREATE EXTENSION IF NOT EXISTS`）。

### Dockerfile 约定

- 使用 `ARG PG_MAJOR` 与 `ARG PG_VERSION` 支持多版本构建。
- 非核心包使用 `(apt-get install ... || true)` 容错，防止个别扩展在某一 PG 主版本中不存在导致构建失败。
- 最后清理 `/var/lib/apt/lists/*` 减小镜像体积。

### Bash 脚本约定

- 所有脚本以 `#!/usr/bin/env bash` 开头并 `set -e`。
- `docker-entrypoint.sh` 通过检查 `$@` 中是否已存在某参数来决定是否注入默认值，**允许用户通过命令行完全覆盖**。
- 日志着色通过管道实现，仅当 `POSTGRES_COLORIZE_LOGS=true` 且主命令为 `postgres` 时生效。

### SQL 脚本约定

- 使用 `IF NOT EXISTS` 防止重复创建报错。
- 脚本按数字前缀排序：`01-*`（template1 扩展）、`03-*`（多数据库）、`99-*`（目标库扩展）。
- 末尾添加 `SELECT ... AS status` 便于在日志中确认执行结果。

### 版本管理

- 唯一版本源：`pg_version.json`。
- 支持的 PostgreSQL 主版本范围：**14 – 18**（对应官方维护周期）。
- 新增主版本支持时，需同时更新：
  1. `pg_version.json`
  2. `Dockerfile` 中的默认 `ARG`
  3. `README.md` 版本表格（可由 `build-helper.py update-readme` 自动生成）
  4. `.github/workflows/ci.yml` 中的 `workflow_dispatch` options 列表

---

## 安全与隐私考量

1. **审计日志默认开启**：`pgaudit` 默认记录 `write,ddl`，且默认记录 SQL 参数（`pgaudit.log_parameter=on`）。处理敏感数据时，用户应通过环境变量关闭参数记录或调整审计类别。
2. **镜像来源**：基于 Docker Hub 官方 `postgres` 镜像，通过 apt.postgresql.org PGDG 仓库安装扩展。构建时应确保 GPG key 与源列表可信。
3. **GHCR 清理**：CI 会自动删除旧补丁版本的镜像标签。若需保留历史版本，应在触发工作流时勾选 `skip_cleanup`。
4. **密码管理**：`POSTGRES_PASSWORD` 为必填环境变量，镜像本身不存储任何默认密码。
5. **日志着色管道**：`docker-entrypoint.sh` 中的 `2>&1 | colorize_log` 仅做文本着色，不会将日志发送到外部。

---

## 常见修改场景指南

| 场景 | 修改位置 | 注意事项 |
|------|---------|---------|
| 新增/删除 PostgreSQL 扩展 | `Scripts/01-install-extensions-template1.sql` 与 `Scripts/99-enable-all-extensions.sql` | 两个文件需同步修改；template1 脚本包含审计/诊断扩展，目标库脚本可能略有差异 |
| 修改默认 PostgreSQL 参数 | `Scripts/docker-entrypoint.sh` | 在 `if [ "$1" = 'postgres' ]` 块内添加/修改 `-c` 参数；同时添加 `has_xxx` 检测以允许用户覆盖 |
| 调整日志着色规则 | `Scripts/pg-log-formatter.sh` | 修改 `colorize_message` 中的 `case` 或正则匹配 |
| 新增支持的 PG 主版本 | `pg_version.json`、`Dockerfile`、`ci.yml` | 同步四处，并验证 Docker Hub 已存在对应 `-bookworm` 标签 |
| 调整构建触发策略 | `.github/workflows/ci.yml` | 注意 `should-build` 与 `cleanup` 步骤的条件表达式 |
| 更新 README 版本表格 | 无需手动修改 | 运行 `python Scripts/build-helper.py update-readme` |

---

## 快速验证清单

在提交修改前，确认以下事项：

- [ ] `Dockerfile` 可成功构建（至少一个主版本）。
- [ ] 若修改了 SQL 脚本，容器首次启动无报错，且 `\dx` 列出预期扩展。
- [ ] 若修改了 `docker-entrypoint.sh`，验证用户自定义命令行参数可正确覆盖默认值。
- [ ] `pg_version.json` 与 `Dockerfile` 的默认 `ARG` 一致。
- [ ] `README.md` 中的版本表格已同步（如版本有变）。
