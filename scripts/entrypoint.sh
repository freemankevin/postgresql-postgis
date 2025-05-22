#!/bin/bash

# 设置环境变量默认值
BACKUP_SCHEDULE=${BACKUP_SCHEDULE:-"0 2 * * *"}
LOCAL_BACKUP_DIR=${LOCAL_BACKUP_DIR:-/backups}

# 确保/var/run目录存在并有正确权限
mkdir -p /var/run/cron
chown postgres:postgres /var/run/cron

# 为postgres用户设置cron任务（不使用su）
echo "${BACKUP_SCHEDULE} /usr/local/bin/backup.sh && /usr/local/bin/cleanup.sh >> /var/log/cron.log 2>&1" | crontab -u postgres -

# 启动cron服务（以前台模式运行）
cron -f &

# 输出配置信息
echo -e "\n备份配置信息："
echo "备份计划: ${BACKUP_SCHEDULE}"
echo "本地备份目录: ${LOCAL_BACKUP_DIR}"
echo "保留天数: ${BACKUP_RETENTION_DAYS:-7}"
echo

# 执行官方entrypoint脚本
exec docker-entrypoint.sh "$@"