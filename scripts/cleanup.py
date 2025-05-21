#!/usr/bin/env python3
import os
import sys
import glob
import time
from datetime import datetime, timedelta
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

@retry_operation
def cleanup_local_backups():
    print(f"[{datetime.now()}] 开始清理本地过期备份...")
    try:
        backup_dir = os.environ.get('LOCAL_BACKUP_DIR', '/backups')
        retention_days = int(os.environ.get('BACKUP_RETENTION_DAYS', '7'))
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        # 查找并删除过期的备份文件
        backup_pattern = os.path.join(backup_dir, 'postgres_*_backup_*.sql.gz')
        for backup_file in glob.glob(backup_pattern):
            try:
                # 从文件名中提取日期（格式：postgres_VERSION_backup_YYYYMMDD_HHMMSS.sql.gz）
                date_str = os.path.basename(backup_file).split('_')[3].split('.')[0]
                file_date = datetime.strptime(date_str, '%Y%m%d')
                
                if file_date < cutoff_date:
                    os.remove(backup_file)
                    print(f"[{datetime.now()}] 已删除过期备份: {backup_file}")
            except (ValueError, IndexError) as e:
                print(f"[{datetime.now()}] 无法解析文件日期: {backup_file}, 错误: {e}")
                continue

    except Exception as e:
        print(f"[{datetime.now()}] 清理本地备份时出错: {e}")
        raise

@retry_operation
def cleanup_minio_backups():
    if os.environ.get('REMOTE_BACKUP_ENABLED', 'false').lower() != 'true':
        return

    print(f"[{datetime.now()}] 开始清理MinIO中的过期备份...")
    try:
        client = Minio(
            os.environ['MINIO_ENDPOINT'],
            access_key=os.environ['MINIO_ACCESS_KEY'],
            secret_key=os.environ['MINIO_SECRET_KEY'],
            secure=True
        )

        retention_days = int(os.environ.get('BACKUP_RETENTION_DAYS', '7'))
        cutoff_date = datetime.now() - timedelta(days=retention_days)

        bucket_name = os.environ['MINIO_BUCKET']
        objects = client.list_objects(bucket_name, prefix='postgres_backups/')
        for obj in objects:
            try:
                # 从文件名中提取日期
                date_str = obj.object_name.split('_')[3].split('.')[0]
                obj_date = datetime.strptime(date_str, '%Y%m%d')
                
                if obj_date < cutoff_date:
                    client.remove_object(bucket_name, obj.object_name)
                    print(f"[{datetime.now()}] 已删除MinIO中的过期备份: {obj.object_name}")
            except (ValueError, IndexError) as e:
                print(f"[{datetime.now()}] 无法解析MinIO对象日期: {obj.object_name}, 错误: {e}")
                continue

    except S3Error as e:
        print(f"[{datetime.now()}] MinIO清理失败: {e}")
        raise
    except Exception as e:
        print(f"[{datetime.now()}] 清理MinIO备份时出错: {e}")
        raise

def main():
    try:
        cleanup_local_backups()
        cleanup_minio_backups()
    except Exception as e:
        print(f"[{datetime.now()}] 清理任务失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()