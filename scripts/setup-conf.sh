#!/bin/bash

# PostGIS 配置
export POSTGRES_MULTIPLE_EXTENSIONS=${POSTGRES_MULTIPLE_EXTENSIONS:-"postgis,hstore,postgis_topology,postgis_raster,pgrouting"}
export ALLOW_IP_RANGE=${ALLOW_IP_RANGE:-"0.0.0.0/0"}

# PostgreSQL 基础配置
export POSTGRES_MAX_CONNECTIONS=${POSTGRES_MAX_CONNECTIONS:-1000}
export POSTGRES_DATA_DIR=${POSTGRES_DATA_DIR:-/var/lib/postgresql/data}
export POSTGRES_LOG_DIR=${POSTGRES_LOG_DIR:-/var/log/postgresql}

# WAL 配置
export POSTGRES_WAL_LEVEL=${POSTGRES_WAL_LEVEL:-replica}
export POSTGRES_ARCHIVE_MODE=${POSTGRES_ARCHIVE_MODE:-off}
export POSTGRES_ARCHIVE_COMMAND=${POSTGRES_ARCHIVE_COMMAND:-""}
export POSTGRES_WAL_KEEP_SIZE=${POSTGRES_WAL_KEEP_SIZE:-1GB}

# 性能调优参数
export POSTGRES_SHARED_BUFFERS=${POSTGRES_SHARED_BUFFERS:-128MB}
export POSTGRES_WORK_MEM=${POSTGRES_WORK_MEM:-4MB}
export POSTGRES_MAINTENANCE_WORK_MEM=${MAINTENANCE_WORK_MEM:-64MB}
export POSTGRES_EFFECTIVE_CACHE_SIZE=${POSTGRES_EFFECTIVE_CACHE_SIZE:-4GB}

# 日志配置
export POSTGRES_LOG_MIN_DURATION_STATEMENT=${POSTGRES_LOG_MIN_DURATION_STATEMENT:-1000}
export POSTGRES_LOG_STATEMENT=${POSTGRES_LOG_STATEMENT:-none}
export POSTGRES_LOG_LINE_PREFIX=${POSTGRES_LOG_LINE_PREFIX:-'%t [%p]: [%l-1] user=%u,db=%d '}

# 创建必要的目录
mkdir -p "${POSTGRES_LOG_DIR}"
chown -R postgres:postgres "${POSTGRES_LOG_DIR}"
chmod 700 "${POSTGRES_LOG_DIR}"

# 生成PostgreSQL配置
cat > "${POSTGRES_DATA_DIR}/postgresql.conf.custom" << EOF
# 连接设置
max_connections = ${POSTGRES_MAX_CONNECTIONS}
listen_addresses = '*'

# 内存配置
shared_buffers = ${POSTGRES_SHARED_BUFFERS}
work_mem = ${POSTGRES_WORK_MEM}
maintenance_work_mem = ${POSTGRES_MAINTENANCE_WORK_MEM}
effective_cache_size = ${POSTGRES_EFFECTIVE_CACHE_SIZE}

# WAL设置
wal_level = ${POSTGRES_WAL_LEVEL}
archive_mode = ${POSTGRES_ARCHIVE_MODE}
archive_command = '${POSTGRES_ARCHIVE_COMMAND}'
wal_keep_size = ${POSTGRES_WAL_KEEP_SIZE}

# 日志设置
log_directory = '${POSTGRES_LOG_DIR}'
log_min_duration_statement = ${POSTGRES_LOG_MIN_DURATION_STATEMENT}
log_statement = '${POSTGRES_LOG_STATEMENT}'
log_line_prefix = '${POSTGRES_LOG_LINE_PREFIX}'
logging_collector = on
log_filename = 'postgresql-%Y-%m-%d.log'
log_rotation_age = 1d
log_rotation_size = 100MB
EOF

# 如果postgresql.conf存在，则添加包含指令
if [ -f "${POSTGRES_DATA_DIR}/postgresql.conf" ]; then
    echo "include 'postgresql.conf.custom'" >> "${POSTGRES_DATA_DIR}/postgresql.conf"
fi