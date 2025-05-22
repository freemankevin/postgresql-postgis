#!/bin/bash

# 设置变量
BACKUP_DIR=${LOCAL_BACKUP_DIR:-/backups}
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-7}

# 输出开始信息
echo "[$(date)] 开始清理过期备份..."

# 检查备份目录是否存在
if [ ! -d "${BACKUP_DIR}" ]; then
    echo "[$(date)] 备份目录不存在: ${BACKUP_DIR}"
    exit 1
fi

# 删除超过保留天数的备份文件
find "${BACKUP_DIR}" -name "postgres_*_backup_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete -print | while read file; do
    echo "[$(date)] 已删除过期备份: ${file}"
done

echo "[$(date)] 清理完成"
exit 0