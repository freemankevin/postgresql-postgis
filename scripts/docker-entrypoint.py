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
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"备份脚本 {script_path} 不存在")
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
        subprocess.run(['/etc/init.d/cron', 'start'], check=True, capture_output=True, text=True)
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

def wait_for_postgres():
    """等待PostgreSQL服务就绪"""
    max_retries = 60
    retry_delay = 2
    
    pg_user = os.environ.get('POSTGRES_USER', 'postgres')
    pg_host = os.environ.get('PGHOST', 'localhost')
    
    for i in range(max_retries):
        try:
            # 检查PostgreSQL服务状态
            result = subprocess.run(
                ['pg_isready', '-U', pg_user, '-h', pg_host],
                capture_output=True,
                text=True
            )
            
            # 检查PostgreSQL进程是否运行
            pg_pid = subprocess.run(
                "ps -ef | grep '[p]ostgres'",
                shell=True,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print(f"[{datetime.now()}] PostgreSQL服务已就绪")
                return True
            else:
                error_msg = f"[{datetime.now()}] pg_isready检查失败 (尝试 {i+1}/{max_retries}): {result.stderr.strip()}"
                if pg_pid.returncode != 0:
                    error_msg += "\n[错误] PostgreSQL进程未运行"
                else:
                    error_msg += f"\n[状态] PostgreSQL进程正在运行 (PID: {pg_pid.stdout.strip()})"
                # 检查 PostgreSQL 日志
                try:
                    with open('/var/lib/postgresql/data/pg_log/postgresql.log', 'r') as f:
                        error_msg += f"\n[PostgreSQL日志] {f.read().strip()}"
                except FileNotFoundError:
                    error_msg += "\n[PostgreSQL日志] 日志文件未找到"
                print(error_msg)
                
        except subprocess.CalledProcessError as e:
            error_msg = f"[{datetime.now()}] PostgreSQL服务启动异常 (尝试 {i+1}/{max_retries})"
            error_msg += f"\n[错误类型] {type(e).__name__}"
            error_msg += f"\n[错误详情] {str(e)}"
            if hasattr(e, 'stderr') and e.stderr:
                error_msg += f"\n[错误输出] {e.stderr.strip()}"
            
            if i == max_retries - 1:
                error_msg += "\n[最终状态] PostgreSQL服务启动失败"
                print(error_msg)
                return False
            
            print(error_msg)
            
        time.sleep(retry_delay)
    return False

def wait_for_database():
    """等待PostgreSQL服务就绪"""
    # 等待PostgreSQL服务就绪
    if not wait_for_postgres():
        raise RuntimeError("PostgreSQL服务启动超时")
    print(f"[{datetime.now()}] PostgreSQL服务已就绪，可以开始备份任务")

def main():
    try:
        setup_cron()
        print_config()
        wait_for_database()
        print(f"[{datetime.now()}] 备份服务初始化完成")
    except Exception as e:
        print(f"[{datetime.now()}] 初始化失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()