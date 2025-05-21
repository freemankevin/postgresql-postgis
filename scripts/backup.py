#!/usr/bin/env python3
import os
import sys
import subprocess
import time
from datetime import datetime
from minio import Minio
from minio.error import S3Error

def retry_operation(operation, max_retries=3, delay=5):
    """重试机制装饰器"""
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return operation(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                print(f"操作失败: {e}, {delay}秒后重试...")
                time.sleep(delay)
    return wrapper

def get_backup_filename():
    """生成备份文件名，包含完整的版本信息"""
    backup_date = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.environ.get('LOCAL_BACKUP_DIR', '/backups')
    pg_version = subprocess.check_output(['postgres', '--version']).decode().split()[2]
    return f"{backup_dir}/postgres_{pg_version}_backup_{backup_date}.sql.gz"

@retry_operation
def create_backup():
    # 设置备份文件名
    backup_file = get_backup_filename()
    os.makedirs(os.path.dirname(backup_file), exist_ok=True)

    print(f"[{datetime.now()}] 开始备份数据库...")
    try:
        # 使用pg_dumpall并通过管道传输到gzip
        dump_process = subprocess.Popen(
            ['pg_dumpall', '-U', 'postgres'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        gzip_process = subprocess.Popen(
            ['gzip'],
            stdin=dump_process.stdout,
            stdout=open(backup_file, 'wb'),
            stderr=subprocess.PIPE
        )
        
        # 等待进程完成
        dump_process.stdout.close()
        _, stderr = gzip_process.communicate()
        
        if gzip_process.returncode == 0:
            print(f"[{datetime.now()}] 本地备份已完成: {backup_file}")
            return backup_file
        else:
            error_msg = stderr.decode() if stderr else "未知错误"
            print(f"[{datetime.now()}] 备份失败: {error_msg}")
            return None
    except Exception as e:
        print(f"[{datetime.now()}] 备份过程出错: {e}")
        return None

@retry_operation
def upload_to_minio(backup_file):
    if os.environ.get('REMOTE_BACKUP_ENABLED', 'false').lower() != 'true':
        return

    print(f"[{datetime.now()}] 开始上传备份到MinIO...")
    try:
        client = Minio(
            os.environ['MINIO_ENDPOINT'],
            access_key=os.environ['MINIO_ACCESS_KEY'],
            secret_key=os.environ['MINIO_SECRET_KEY'],
            secure=True
        )

        bucket_name = os.environ['MINIO_BUCKET']
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)

        object_name = f"postgres_backups/{os.path.basename(backup_file)}"
        client.fput_object(
            bucket_name,
            object_name,
            backup_file,
            progress=lambda size: print(f"[{datetime.now()}] 已上传: {size} bytes")
        )
        print(f"[{datetime.now()}] 备份已成功上传到MinIO: {object_name}")

    except S3Error as e:
        print(f"[{datetime.now()}] MinIO上传失败: {e}")
        raise
    except Exception as e:
        print(f"[{datetime.now()}] 上传过程出错: {e}")
        raise

def main():
    try:
        backup_file = create_backup()
        if backup_file:
            upload_to_minio(backup_file)
    except Exception as e:
        print(f"[{datetime.now()}] 备份任务失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()