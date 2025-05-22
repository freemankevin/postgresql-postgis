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