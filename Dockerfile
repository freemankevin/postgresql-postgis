ARG PG_MAJOR=17
ARG PG_VERSION=17.9

FROM postgres:${PG_VERSION}-bookworm
ENV DEBIAN_FRONTEND=noninteractive

LABEL org.opencontainers.image.version="${PG_VERSION}"
LABEL org.opencontainers.image.source="https://github.com/freemankevin/postgresql-postgis"

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    lsb-release \
    && curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc  | gpg --dearmor -o /usr/share/keyrings/postgresql-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/postgresql-keyring.gpg] http://apt.postgresql.org/pub/repos/apt  $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    postgresql-${PG_MAJOR}-postgis-3 \
    postgresql-${PG_MAJOR}-postgis-3-scripts \
    postgresql-${PG_MAJOR}-pgrouting \
    && rm -rf /var/lib/apt/lists/*

COPY Scripts/01-install-extensions-template1.sql /docker-entrypoint-initdb.d/
COPY Scripts/03-create-extra-databases.sh /docker-entrypoint-initdb.d/
COPY Scripts/99-enable-all-extensions.sql /docker-entrypoint-initdb.d/
COPY Scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint-wrapper.sh
RUN chmod +x /usr/local/bin/docker-entrypoint-wrapper.sh

ENTRYPOINT ["docker-entrypoint-wrapper.sh"]
CMD ["postgres"]