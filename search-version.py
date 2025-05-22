#!/usr/bin/env python3
import sys
import requests
import re
import json
import os
from typing import Optional
from time import sleep

def get_all_latest_patch_versions(max_retries: int = 3) -> dict:
    """一次性获取所有 PostgreSQL 主版本（12-17）的最新补丁版本"""
    url = "https://ftp.postgresql.org/pub/source/"
    versions = {}
    
    for major_version in range(12, 18):
        pattern = rf"v{major_version}\.\d+/"
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                # 查找所有匹配的版本
                matches = re.findall(pattern, response.text)
                if not matches:
                    print(f"未找到PostgreSQL {major_version}.x的版本信息", file=sys.stderr)
                    versions[str(major_version)] = f"{major_version}.0"
                    break
                    
                # 提取版本号并排序
                patch_versions = [v.strip('v/').split('.')[1] for v in matches]
                patch_versions.sort(key=int)
                
                if patch_versions:
                    latest_version = f"{major_version}.{patch_versions[-1]}"
                    print(f"找到PostgreSQL {major_version}的最新补丁版本：{latest_version}")
                    versions[str(major_version)] = latest_version
                    break
                    
            except requests.RequestException as e:
                print(f"获取版本信息失败（尝试 {attempt + 1}/{max_retries}）：{str(e)}", file=sys.stderr)
                if attempt < max_retries - 1:
                    sleep(5)
                    continue
                else:
                    versions[str(major_version)] = f"{major_version}.0"
                    print(f"警告：无法获取版本信息，使用默认版本 {major_version}.0", file=sys.stderr)
    
    return versions

def main():
    versions = get_all_latest_patch_versions()
    with open('pg_version.json', 'w') as f:  
        json.dump(versions, f, indent=2)
    print(json.dumps(versions))

if __name__ == "__main__":
    main()