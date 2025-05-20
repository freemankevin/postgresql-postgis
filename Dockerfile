# 全局声明 PG_MAJOR，设置默认值为 17
ARG PG_MAJOR=17

# 阶段 1：查询最新补丁版本
FROM debian:bookworm-slim AS version-fetcher
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates && rm -rf /var/lib/apt/lists/*
RUN set -x && for i in 1 2 3; do \
    echo "Attempt $i to fetch PostgreSQL source version" && \
    curl -sL "https://ftp.postgresql.org/pub/source/" -o /tmp/pg_versions.txt && \
    VERSION=$(cat /tmp/pg_versions.txt | grep -oP "<a href=\"v${PG_MAJOR}\.\d+/\"" | sort -V | tail -n 1 | sed 's/^<a href="v//;s/\/"$//' | tr -d '\n') && \
    echo "Found version: $VERSION" && \
    if [ -n "$VERSION" ]; then \
      echo "$VERSION" > /pg_version && \
      echo "PG$PG_MAJOR 最新补丁版本号：$VERSION" && \
      break; \
    else \
      echo "Failed to fetch version, retrying in 5 seconds..." && \
      cat /tmp/pg_versions.txt >&2 && \
      sleep 5; \
    fi; \
  done; \
  if [ ! -s /pg_version ]; then \
    echo "ERROR: Failed to fetch PostgreSQL version after 3 attempts" >&2 && \
    echo "$PG_MAJOR.0" > /pg_version; \
  fi

# 阶段 2：主构建
FROM postgres:${PG_MAJOR}-bookworm
# 重新声明 PG_MAJOR 以在该阶段使用
ARG PG_MAJOR
ENV DEBIAN_FRONTEND=noninteractive

# 从版本查询阶段复制补丁版本
COPY --from=version-fetcher /pg_version /pg_version
RUN PG_VERSION=$(cat /pg_version) && echo "Using PostgreSQL version: ${PG_MAJOR}-${PG_VERSION}"

# 配置 APT 源并安装 PostGIS 和相关扩展
RUN echo "Types: deb\nURIs: http://deb.debian.org/debian\nSuites: bookworm bookworm-updates\nComponents: main contrib non-free" > /etc/apt/sources.list.d/debian.sources \
    && echo "Types: deb\nURIs: http://deb.debian.org/debian-security\nSuites: bookworm-security\nComponents: main" > /etc/apt/sources.list.d/debian.security.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
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
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD pg_isready -U postgres || exit 1

# 启动 PostgreSQL
CMD ["docker-entrypoint.sh", "postgres"]