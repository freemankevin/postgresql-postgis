#!/bin/bash

set -e

# 拉取 PostgreSQL 源码目录并提取 12-17 的最高补丁版本
curl -s https://ftp.postgresql.org/pub/source/ | \
grep -oP 'v1[2-7]\.\d+(?=/)' | sort -V | \
sed 's/^v//' | \
awk -F. '{
  key = $1;
  if (!latest[key] || $2 > latest[key]) latest[key] = $2;
}
END {
  for (k in latest) {
    printf "%s.%s\n", k, latest[k];
  }
}' | sort -V


for PG_MAJOR in {12..17}; do
  VERSION=$(curl -s "https://ftp.postgresql.org/pub/source/" | \
    grep -oP "v$PG_MAJOR\.\d+(?=/)" | \
    sort -V | tail -n 1 | sed 's/^v//' | tr -d '\n')
  echo "PostgreSQL $PG_MAJOR 最新补丁版本号: $VERSION"
done