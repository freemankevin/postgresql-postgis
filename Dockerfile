# 使用构建参数指定 PostgreSQL 主版本
ARG PG_MAJOR=17

# 阶段 1：查询最新补丁版本
FROM debian:bookworm-slim AS version-fetcher
RUN apt-get update && apt-get install -y --no-install-recommends curl jq && rm -rf /var/lib/apt/lists/*
ARG PG_MAJOR
RUN for i in {1..3}; do \
      curl -s "https://registry.hub.docker.com/v2/repositories/library/postgres/tags?page_size=100" | \
      jq -r --arg major "$PG_MAJOR" '.results[] | .name | select(test("^[0-9]+\\.[0-9]+-bookworm$")) | select(startswith($major + "."))' | \
      sort -V | tail -n 1 | cut -d'-' -f1 > /pg_version && break || sleep 5; \
    done || echo "$PG_MAJOR.0" > /pg_version

# 阶段 2：主构建
FROM postgres:${PG_MAJOR}-bookworm

# 重新声明构建参数
ARG PG_MAJOR

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive

# 从版本查询阶段复制补丁版本
COPY --from=version-fetcher /pg_version /pg_version
RUN PG_VERSION=$(cat /pg_version) && echo "Using PostgreSQL version: $PG_VERSION"

# 添加 Debian 安全源
RUN echo "Types: deb" > /etc/apt/sources.list.d/debian.security.sources \
    && echo "URIs: http://deb.debian.org/debian-security" >> /etc/apt/sources.list.d/debian.security.sources \
    && echo "Suites: bookworm-security" >> /etc/apt/sources.list.d/debian.security.sources \
    && echo "Components: main" >> /etc/apt/sources.list.d/debian.security.sources

# 更新包列表并安装依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-${PG_MAJOR}-postgis-3 \
    postgresql-${PG_MAJOR}-postgis-3-scripts \
    postgresql-${PG_MAJOR}-pgrouting \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 设置默认环境变量
ENV POSTGRES_MULTIPLE_EXTENSIONS=postgis,hstore,postgis_topology,postgis_raster,pgrouting \
    ALLOW_IP_RANGE=0.0.0.0/0

# 暴露 PostgreSQL 默认端口
EXPOSE 5432

# 挂载卷用于持久化数据
VOLUME /var/lib/postgresql/data

# 添加健康检查
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD pg_isready -U postgres || exit 1

# 启动 PostgreSQL
CMD ["docker-entrypoint.sh", "postgres"]