#!/usr/bin/env python3
import sys
import requests
import re
import json
import os
from typing import Optional, Dict
from time import sleep

def get_postgresql_versions_from_api() -> Dict[str, str]:
    """尝试从更可靠的源获取PostgreSQL版本信息"""
    versions = {}
    
    # 方法1：尝试从endoflife.date API获取
    try:
        print("尝试从 endoflife.date API 获取版本信息...")
        response = requests.get("https://endoflife.date/api/postgresql.json", timeout=15)
        response.raise_for_status()
        
        eol_data = response.json()
        for item in eol_data:
            if not item.get('eol', False):  # 只取未EOL的版本
                cycle = item.get('cycle')
                latest = item.get('latest')
                if cycle and latest and cycle.isdigit():
                    major_ver = int(cycle)
                    if 12 <= major_ver <= 17:
                        versions[str(major_ver)] = latest
                        print(f"从 API 获取到 PostgreSQL {major_ver}: {latest}")
        
        if len(versions) >= 5:  # 如果获取到了足够的版本信息
            return versions
            
    except Exception as e:
        print(f"从 API 获取版本失败: {e}", file=sys.stderr)
    
    # 方法2：从PostgreSQL官方FTP获取（原方法的改进版）
    return get_versions_from_ftp()

def get_versions_from_ftp(max_retries: int = 3) -> Dict[str, str]:
    """从PostgreSQL FTP服务器获取版本信息（改进版）"""
    url = "https://ftp.postgresql.org/pub/source/"
    versions = {}
    
    print("从 PostgreSQL FTP 服务器获取版本信息...")
    
    for major_version in range(12, 18):
        print(f"检查 PostgreSQL {major_version}.x 版本...")
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=30)  # 增加超时时间
                response.raise_for_status()
                
                # 改进的正则表达式，更精确匹配
                pattern = rf'href="v{major_version}\.(\d+)/"'
                matches = re.findall(pattern, response.text)
                
                if not matches:
                    print(f"未找到 PostgreSQL {major_version}.x 的版本信息", file=sys.stderr)
                    # 设置默认版本作为fallback
                    fallback_versions = {
                        12: "12.22", 13: "13.22", 14: "14.19", 
                        15: "15.14", 16: "16.10", 17: "17.6"
                    }
                    versions[str(major_version)] = fallback_versions.get(major_version, f"{major_version}.0")
                    break
                
                # 转换为整数进行排序，然后取最大值
                patch_numbers = [int(patch) for patch in matches]
                patch_numbers.sort()
                latest_patch = patch_numbers[-1]
                latest_version = f"{major_version}.{latest_patch}"
                
                print(f"找到 PostgreSQL {major_version} 的最新版本: {latest_version}")
                versions[str(major_version)] = latest_version
                break
                
            except requests.RequestException as e:
                print(f"获取 PostgreSQL {major_version} 版本失败（尝试 {attempt + 1}/{max_retries}）：{str(e)}", file=sys.stderr)
                if attempt < max_retries - 1:
                    sleep(10)  # 增加重试间隔
                else:
                    # 使用已知的最新版本作为fallback
                    fallback_versions = {
                        12: "12.22", 13: "13.22", 14: "14.19", 
                        15: "15.14", 16: "16.10", 17: "17.6"
                    }
                    versions[str(major_version)] = fallback_versions.get(major_version, f"{major_version}.0")
                    print(f"使用 fallback 版本: {versions[str(major_version)]}")
    
    return versions

def load_existing_versions() -> Dict[str, str]:
    """加载现有的版本文件"""
    try:
        if os.path.exists('pg_version.json'):
            with open('pg_version.json', 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"读取现有版本文件失败: {e}", file=sys.stderr)
    return {}

def has_version_changed(old_versions: Dict[str, str], new_versions: Dict[str, str]) -> bool:
    """检查版本是否有变化"""
    for major in ['12', '13', '14', '15', '16', '17']:
        old_ver = old_versions.get(major, "0.0")
        new_ver = new_versions.get(major, "0.0")
        if old_ver != new_ver:
            print(f"检测到版本变化: PostgreSQL {major}: {old_ver} -> {new_ver}")
            return True
    return False

def main():
    print("开始检查 PostgreSQL 版本更新...")
    
    # 加载现有版本
    old_versions = load_existing_versions()
    print(f"当前版本: {old_versions}")
    
    # 获取最新版本
    new_versions = get_postgresql_versions_from_api()
    print(f"最新版本: {new_versions}")
    
    # 检查是否有变化
    has_changed = has_version_changed(old_versions, new_versions)
    
    # 更新版本文件
    try:
        with open('pg_version.json', 'w') as f:  
            json.dump(new_versions, f, indent=2)
        print("pg_version.json 文件已更新")
    except Exception as e:
        print(f"更新版本文件失败: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 输出结果供GitHub Actions使用
    print(json.dumps(new_versions))
    
    # 如果在GitHub Actions环境中，设置输出变量
    if os.getenv('GITHUB_OUTPUT'):
        with open(os.getenv('GITHUB_OUTPUT'), 'a') as f:
            f.write(f"versions={json.dumps(new_versions)}\n")
            f.write(f"changed={str(has_changed).lower()}\n")

if __name__ == "__main__":
    main()