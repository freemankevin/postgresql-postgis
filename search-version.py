#!/usr/bin/env python3
import sys
import requests
import re
import json
import os
from typing import Optional, Dict
from time import sleep

def get_postgresql_versions_from_endoflife() -> Dict[str, str]:
    """从endoflife.date API获取PostgreSQL版本信息"""
    versions = {}
    
    try:
        print("从 endoflife.date API 获取版本信息...")
        response = requests.get("https://endoflife.date/api/postgresql.json", timeout=15)
        response.raise_for_status()
        
        eol_data = response.json()
        for item in eol_data:
            # 检查版本是否已经EOL
            eol = item.get('eol')
            cycle = item.get('cycle')
            latest = item.get('latest')
            
            # 只获取未EOL的版本
            if cycle and latest and cycle.isdigit():
                major_ver = int(cycle)
                if 12 <= major_ver <= 18:  # 扩展到18以便未来使用
                    # eol为False或者是未来的日期才认为是支持的版本
                    if eol == False or (isinstance(eol, str) and eol > '2024-12-03'):
                        versions[str(major_ver)] = latest
                        print(f"✓ PostgreSQL {major_ver}: {latest} (EOL: {eol})")
        
        return versions
            
    except Exception as e:
        print(f"✗ 从 endoflife.date API 获取失败: {e}", file=sys.stderr)
        return {}

def get_version_from_official_release_page(major_version: int, max_retries: int = 3) -> Optional[str]:
    """从PostgreSQL官方发布页面获取特定主版本的最新小版本"""
    
    # 尝试从官方文档的release notes页面获取
    urls = [
        f"https://www.postgresql.org/docs/{major_version}/release-{major_version}.html",
        f"https://www.postgresql.org/docs/release/{major_version}.0/",
    ]
    
    for url in urls:
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=15)
                response.raise_for_status()
                
                # 匹配版本号，格式如 "Release 17.2" 或 "E.1. Release 17.2"
                patterns = [
                    rf'Release {major_version}\.(\d+)',
                    rf'>{major_version}\.(\d+)<',
                    rf'Version {major_version}\.(\d+)',
                ]
                
                all_patches = []
                for pattern in patterns:
                    matches = re.findall(pattern, response.text)
                    all_patches.extend([int(m) for m in matches])
                
                if all_patches:
                    latest_patch = max(all_patches)
                    return f"{major_version}.{latest_patch}"
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    sleep(2)
                else:
                    print(f"  尝试 {url} 失败: {e}", file=sys.stderr)
    
    return None

def get_versions_from_ftp(max_retries: int = 3) -> Dict[str, str]:
    """从PostgreSQL FTP服务器获取版本信息（备用方法）"""
    url = "https://ftp.postgresql.org/pub/source/"
    versions = {}
    
    print("从 PostgreSQL FTP 服务器获取版本信息...")
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # 改进的正则表达式，匹配 href="vX.Y/"
        for major_version in range(12, 19):
            pattern = rf'href="v({major_version}\.\d+)/"'
            matches = re.findall(pattern, response.text)
            
            if matches:
                # 提取所有匹配的完整版本号
                version_tuples = []
                for match in matches:
                    try:
                        parts = match.split('.')
                        if len(parts) == 2:
                            version_tuples.append((int(parts[0]), int(parts[1]), match))
                    except:
                        continue
                
                if version_tuples:
                    # 按版本号排序，取最新的
                    version_tuples.sort()
                    latest_version = version_tuples[-1][2]
                    versions[str(major_version)] = latest_version
                    print(f"  PostgreSQL {major_version}: {latest_version}")
    
    except Exception as e:
        print(f"✗ FTP方法失败: {e}", file=sys.stderr)
    
    return versions

def get_all_versions() -> Dict[str, str]:
    """综合多种方法获取PostgreSQL版本"""
    
    # 方法1: 优先使用 endoflife.date API
    versions = get_postgresql_versions_from_endoflife()
    
    if len(versions) >= 5:
        print(f"✓ 成功从 endoflife.date 获取 {len(versions)} 个版本")
        return versions
    
    print("endoflife.date 数据不完整，尝试其他方法...")
    
    # 方法2: 尝试从官方文档获取
    for major_version in range(12, 18):
        if str(major_version) not in versions:
            print(f"尝试获取 PostgreSQL {major_version}...")
            version = get_version_from_official_release_page(major_version)
            if version:
                versions[str(major_version)] = version
                print(f"  ✓ {version}")
    
    if len(versions) >= 5:
        print(f"✓ 成功从官方文档获取 {len(versions)} 个版本")
        return versions
    
    # 方法3: 最后尝试FTP
    print("尝试FTP方法...")
    ftp_versions = get_versions_from_ftp()
    for major, version in ftp_versions.items():
        if major not in versions:
            versions[major] = version
    
    # 如果仍然获取失败，使用已知的最新版本作为fallback
    if len(versions) < 5:
        print("⚠ 所有方法都失败，使用fallback版本")
        fallback_versions = {
            "12": "12.22",  # EOL
            "13": "13.18",
            "14": "14.15",
            "15": "15.10",
            "16": "16.6",
            "17": "17.2",
        }
        for major, version in fallback_versions.items():
            if major not in versions:
                versions[major] = version
    
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
    changed = False
    for major in sorted(new_versions.keys()):
        old_ver = old_versions.get(major, "0.0")
        new_ver = new_versions.get(major, "0.0")
        if old_ver != new_ver:
            print(f"📦 版本变化: PostgreSQL {major}: {old_ver} -> {new_ver}")
            changed = True
    return changed

def main():
    print("=" * 60)
    print("PostgreSQL 版本检查")
    print("=" * 60)
    
    # 加载现有版本
    old_versions = load_existing_versions()
    if old_versions:
        print(f"\n当前版本:")
        for major in sorted(old_versions.keys()):
            print(f"  PostgreSQL {major}: {old_versions[major]}")
    
    print("\n开始检查最新版本...\n")
    
    # 获取最新版本
    new_versions = get_all_versions()
    
    print(f"\n最新版本:")
    for major in sorted(new_versions.keys()):
        print(f"  PostgreSQL {major}: {new_versions[major]}")
    
    # 检查是否有变化
    has_changed = has_version_changed(old_versions, new_versions)
    
    # 更新版本文件
    try:
        with open('pg_version.json', 'w') as f:
            json.dump(new_versions, f, indent=2, sort_keys=True)
        print("\n✓ pg_version.json 文件已更新")
    except Exception as e:
        print(f"\n✗ 更新版本文件失败: {e}", file=sys.stderr)
        sys.exit(1)
    
    # 输出结果供GitHub Actions使用
    print(f"\n版本JSON: {json.dumps(new_versions)}")
    print(f"是否变化: {has_changed}")
    
    # 如果在GitHub Actions环境中，设置输出变量
    if os.getenv('GITHUB_OUTPUT'):
        versions_json = json.dumps(new_versions, separators=(',', ':'))
        # 重要：changed 必须是字符串 'true' 或 'false'，不能是布尔值
        changed_str = 'true' if has_changed else 'false'
        with open(os.getenv('GITHUB_OUTPUT'), 'a') as f:
            f.write(f"versions={versions_json}\n")
            f.write(f"changed={changed_str}\n")
        print(f"\n✓ GitHub Actions 输出变量已设置:")
        print(f"  - versions: {versions_json}")
        print(f"  - changed: {changed_str}")
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)

if __name__ == "__main__":
    main()