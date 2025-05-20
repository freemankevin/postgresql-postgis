# Dockerfile

ARG PG_MAJOR=17

# 阶段 1：查询最新补丁版本
FROM debian:bookworm-slim AS version-fetcher
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
ARG PG_MAJOR
RUN for i in {1..3}; do \
      VERSION=$(curl -s "https://ftp.postgresql.org/pub/source/" | \
      grep -oP "v$PG_MAJOR\.\d+(?=/)" | \
      sort -V | tail -n 1) && \
      if [ ! -z "$VERSION" ]; then \
        echo "$VERSION" > /pg_version && break; \
      else \
        sleep 5; \
      fi; \
    done; \
    if [ ! -s /pg_version ]; then \
      echo "v$PG_MAJOR.0" > /pg_version; \
    fi

# 阶段 2：主构建
FROM postgres:${PG_MAJOR}-bookworm

# 重新声明构建参数
ARG PG_MAJOR

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive

# 从版本查询阶段复制补丁版本
COPY --from=version-fetcher /pg_version /pg_version
RUN PG_VERSION=$(cat /pg_version) && echo "Using PostgreSQL version: $PG_VERSION"

# 配置 APT 源
RUN echo "Types: deb\nURIs: http://deb.debian.org/debian\nSuites: bookworm bookworm-updates\nComponents: main contrib non-free" > /etc/apt/sources.list.d/debian.sources \
    && echo "Types: deb\nURIs: http://deb.debian.org/debian-security\nSuites: bookworm-security\nComponents: main" > /etc/apt/sources.list.d/debian.security.sources

# 根据PostgreSQL版本设置PostGIS版本并安装
RUN PG_VERSION=$(cat /pg_version) && \
    if [ "${PG_MAJOR}" = "12" ]; then \
        POSTGIS_VERSION="3.4"; \
    else \
        POSTGIS_VERSION="3.5"; \
    fi && \
    apt-get update && apt-get install -y --no-install-recommends \
    postgresql-${PG_MAJOR}-postgis-${POSTGIS_VERSION} \
    postgresql-${PG_MAJOR}-postgis-${POSTGIS_VERSION}-scripts \
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

# 根据PostgreSQL版本设置PostGIS版本
RUN PG_VERSION=$(cat /pg_version) && \
    if [ "${PG_MAJOR}" = "12" ]; then \
        POSTGIS_VERSION="3.4.2"; \
    else \
        POSTGIS_VERSION="3.5.2"; \
    fi && \
    apt-get update && apt-get install -y --no-install-recommends \
    postgresql-${PG_MAJOR}-postgis-${POSTGIS_VERSION%.*} \
    postgresql-${PG_MAJOR}-postgis-${POSTGIS_VERSION%.*}-scripts \
    postgresql-${PG_MAJOR}-pgrouting \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV POSTGRES_MULTIPLE_EXTENSIONS=postgis,hstore,postgis_topology,postgis_raster,pgrouting \
    ALLOW_IP_RANGE=0.0.0.0/0
EXPOSE 5432
VOLUME /var/lib/postgresql/data
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD pg_isready -U postgres || exit 1
CMD ["docker-entrypoint.sh", "postgres"]
