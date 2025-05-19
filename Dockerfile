# Dockerfile

ARG PG_MAJOR=17

# 阶段 1：获取最新补丁版本
FROM debian:bookworm-slim AS version-fetcher
ARG PG_MAJOR
RUN apt-get update && apt-get install -y curl grep sed gawk coreutils && \
    for i in {1..3}; do \
      VERSION=$(curl -s https://ftp.postgresql.org/pub/source/ | \
      grep -oP "v${PG_MAJOR}\.\d+(?=/)" | sort -V | tail -n1) && \
      if [ ! -z "$VERSION" ]; then \
        echo "$VERSION" > /pg_version && break; \
      else \
        sleep 5; \
      fi; \
    done && \
    [ -s /pg_version ] || echo "v${PG_MAJOR}.0" > /pg_version

# 阶段 2：主构建
FROM postgres:${PG_MAJOR}-bookworm
ARG PG_MAJOR
COPY --from=version-fetcher /pg_version /pg_version
RUN PG_VERSION=$(cat /pg_version) && echo "Using PostgreSQL version: $PG_VERSION"

RUN echo "Types: deb\nURIs: http://deb.debian.org/debian\nSuites: bookworm bookworm-updates\nComponents: main contrib non-free" > /etc/apt/sources.list.d/debian.sources \
 && echo "Types: deb\nURIs: http://deb.debian.org/debian-security\nSuites: bookworm-security\nComponents: main" > /etc/apt/sources.list.d/debian.security.sources \
 && apt-get update && apt-get install -y --no-install-recommends \
    postgresql-${PG_MAJOR}-postgis-3 \
    postgresql-${PG_MAJOR}-postgis-3-scripts \
    postgresql-${PG_MAJOR}-pgrouting \
    ca-certificates \
 && rm -rf /var/lib/apt/lists/*

ENV POSTGRES_MULTIPLE_EXTENSIONS=postgis,hstore,postgis_topology,postgis_raster,pgrouting \
    ALLOW_IP_RANGE=0.0.0.0/0
EXPOSE 5432
VOLUME /var/lib/postgresql/data
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD pg_isready -U postgres || exit 1
CMD ["docker-entrypoint.sh", "postgres"]
