#!/bin/bash

# 等待PostgreSQL服务就绪
until pg_isready -U postgres -h localhost; do
    echo "等待PostgreSQL启动..."
    sleep 2
done

# 启动cron服务
/etc/init.d/cron start

# 执行初始化脚本
python3 /usr/local/bin/docker-entrypoint.py