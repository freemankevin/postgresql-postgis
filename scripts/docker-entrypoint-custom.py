#!/usr/bin/env python3
import os
import sys
import time
import subprocess
from datetime import datetime

def retry_operation(operation, max_retries=3, delay=5):
    """重试机制装饰器"""
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"[{datetime.now()}] 操作失败: {e}, {delay}秒后重试...")
                time.sleep(delay)
    return wrapper

@retry_operation
def setup_cron():
    print(f"[{datetime.now()}] 开始设置定时备份任务...")
    
    # 确保备份脚本有执行权限
    for script in ['backup.py', 'cleanup.py']:
        script_path = f"/usr/local/bin/{script}"
        try:
            os.chmod(script_path, 0o755)
            print(f"[{datetime.now()}] 已设置{script}执行权限")
        except Exception as e:
            print(f"[{datetime.now()}] 设置{script}执行权限失败: {e}")
            raise

    # 创建cron任务
    backup_schedule = os.environ.get('BACKUP_SCHEDULE', '0 2 * * *')
    cron_file = '/etc/cron.d/postgres-backup'
    try:
        with open(cron_file, 'w') as f:
            # 添加备份任务，每次备份后执行清理
            f.write(f"{backup_schedule} /usr/local/bin/backup.py && /usr/local/bin/cleanup.py >> /var/log/cron.log 2>&1\n")
        os.chmod(cron_file, 0o644)
        print(f"[{datetime.now()}] 已创建定时备份任务: {backup_schedule}")
    except Exception as e:
        print(f"[{datetime.now()}] 创建cron任务失败: {e}")
        raise

    # 创建日志文件
    try:
        log_file = '/var/log/cron.log'
        open(log_file, 'a').close()
        os.chmod(log_file, 0o644)
        print(f"[{datetime.now()}] 已创建日志文件: {log_file}")
    except Exception as e:
        print(f"[{datetime.now()}] 创建日志文件失败: {e}")
        raise

    # 启动cron服务
    try:
        subprocess.run(['/etc/init.d/cron', 'start'], check=True)
        print(f"[{datetime.now()}] cron服务已启动")
    except subprocess.CalledProcessError as e:
        print(f"[{datetime.now()}] 启动cron服务失败: {e}")
        raise

def print_config():
    print("\n备份配置信息：")
    print(f"本地备份目录: {os.environ.get('LOCAL_BACKUP_DIR', '/backups')}")
    print(f"备份计划: {os.environ.get('BACKUP_SCHEDULE', '0 2 * * *')}")
    print(f"保留天数: {os.environ.get('BACKUP_RETENTION_DAYS', '7')}")

    if os.environ.get('REMOTE_BACKUP_ENABLED', 'false').lower() == 'true':
        print("远程备份已启用")
        print(f"MinIO端点: {os.environ.get('MINIO_ENDPOINT', '')}")
        print(f"MinIO存储桶: {os.environ.get('MINIO_BUCKET', '')}")
    else:
        print("远程备份未启用")
    print()

def main():
    try:
        setup_cron()
        print_config()
        
        print(f"[{datetime.now()}] 正在启动PostgreSQL服务...")
        os.execvp('docker-entrypoint.sh', ['docker-entrypoint.sh', 'postgres'])
    except Exception as e:
        print(f"[{datetime.now()}] 容器启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()