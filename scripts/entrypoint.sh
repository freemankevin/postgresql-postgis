#!/bin/bash

# 设置环境变量默认值
BACKUP_SCHEDULE=${BACKUP_SCHEDULE:-"0 2 * * *"}
LOCAL_BACKUP_DIR=${LOCAL_BACKUP_DIR:-/backups}

# 等待PostgreSQL服务就绪
until pg_isready -U postgres -h localhost; do
    echo "等待PostgreSQL启动..."
    sleep 2
done

# 为postgres用户设置cron任务
echo "${BACKUP_SCHEDULE} /usr/local/bin/backup.sh && /usr/local/bin/cleanup.sh >> /var/log/cron.log 2>&1" > /tmp/postgres_cron
su - postgres -c "crontab /tmp/postgres_cron"
rm -f /tmp/postgres_cron

# 启动cron服务
/etc/init.d/cron start

# 输出配置信息
echo "\n备份配置信息："
echo "备份计划: ${BACKUP_SCHEDULE}"
echo "本地备份目录: ${LOCAL_BACKUP_DIR}"
echo "保留天数: ${BACKUP_RETENTION_DAYS:-7}"
echo

# 加载PostgreSQL配置
source /usr/local/bin/setup-conf.sh

# 执行官方entrypoint脚本
exec docker-entrypoint.sh "$@"