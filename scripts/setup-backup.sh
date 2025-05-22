#!/bin/bash

# 设置日期格式
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=${LOCAL_BACKUP_DIR:-/backups}
PG_VERSION=$(postgres --version | awk '{print $3}')

# 创建备份目录
mkdir -p "${BACKUP_DIR}"
chown postgres:postgres "${BACKUP_DIR}"

# 设置备份文件名
BACKUP_FILE="${BACKUP_DIR}/postgres_${PG_VERSION}_backup_${DATE}.sql.gz"

# 输出开始信息
echo "[$(date)] 开始备份数据库..."

# 执行备份
if pg_dumpall -U postgres | gzip > "${BACKUP_FILE}"; then
    echo "[$(date)] 备份完成: ${BACKUP_FILE}"
    chmod 644 "${BACKUP_FILE}"
    exit 0
else
    echo "[$(date)] 备份失败"
    rm -f "${BACKUP_FILE}"
    exit 1
fi