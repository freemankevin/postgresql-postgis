ARG PG_MAJOR=17
ARG PG_VERSION

FROM postgres:${PG_VERSION}-bookworm
ENV DEBIAN_FRONTEND=noninteractive

RUN echo "Types: deb\nURIs: http://deb.debian.org/debian\nSuites: bookworm bookworm-updates\nComponents: main contrib non-free" > /etc/apt/sources.list.d/debian.sources \
    && echo "Types: deb\nURIs: http://deb.debian.org/debian-security\nSuites: bookworm-security\nComponents: main" > /etc/apt/sources.list.d/debian.security.sources \
    && apt-get update && apt-get install -y --no-install-recommends \
    postgresql-${PG_MAJOR}-postgis-3 \
    postgresql-${PG_MAJOR}-postgis-3-scripts \
    postgresql-${PG_MAJOR}-pgrouting \
    ca-certificates \
    curl \
    cron \
    && rm -rf /var/lib/apt/lists/*

ENV POSTGRES_MULTIPLE_EXTENSIONS=postgis,hstore,postgis_topology,postgis_raster,pgrouting \
	TZ=Asia/Shanghai \
    ALLOW_IP_RANGE=0.0.0.0/0 \
	POSTGRES_MAX_CONNECTIONS=1000 \
	POSTGRES_SHARED_BUFFERS=128MB \
	POSTGRES_WORK_MEM=4MB \
	POSTGRES_MAINTENANCE_WORK_MEM=64MB \
	POSTGRES_EFFECTIVE_CACHE_SIZE=4GB \
	POSTGRES_LOG_MIN_DURATION_STATEMENT=1000