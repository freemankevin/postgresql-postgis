#!/usr/bin/env python3
"""
从 Docker Hub 获取 PostgreSQL 官方镜像实际存在的最新版本
"""
import sys
import requests
import re
import json
import os
from typing import Dict, Optional
from time import sleep


def get_docker_hub_tags(max_pages: int = 10) -> Dict[str, str]:
    """
    从 Docker Hub 获取 postgres 镜像的所有 bookworm 标签，提取最新版本
    
    Returns:
        Dict[major_version, full_version] 如 {"14": "14.21", "17": "17.8"}
    """
    versions = {}
    url = "https://hub.docker.com/v2/repositories/library/postgres/tags/"
    
    print("从 Docker Hub 获取 postgres 镜像版本信息...")
    
    for page in range(1, max_pages + 1):
        try:
            response = requests.get(
                url, 
                params={"page": page, "page_size": 100, "name": "bookworm"},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            for result in data.get("results", []):
                tag_name = result.get("name", "")
                
                # 匹配格式: 14.21-bookworm, 17.8-bookworm, 16-bookworm (不推荐)
                match = re.match(r'^(\d+)\.(\d+)-bookworm$', tag_name)
                if match:
                    major = match.group(1)
                    minor = match.group(2)
                    full_version = f"{major}.{minor}"
                    
                    # 只保留支持的版本 (13-18)
                    if 13 <= int(major) <= 18:
                        # 如果有多个版本，保留最大的
                        if major not in versions or full_version > versions[major]:
                            versions[major] = full_version
                            print(f"  发现: PostgreSQL {major}: {full_version}")
            
            # 检查是否还有下一页
            if not data.get("next"):
                break
                
        except Exception as e:
            print(f"✗ 获取第 {page} 页失败: {e}", file=sys.stderr)
            break
    
    return versions


def get_versions_from_official_site() -> Dict[str, str]:
    """
    备用方案：从 PostgreSQL 官方 FTP 获取版本（如果 Docker Hub 失败）
    """
    print("尝试从 PostgreSQL FTP 获取版本作为备用...")
    versions = {}
    
    try:
        response = requests.get(
            "https://ftp.postgresql.org/pub/source/", 
            timeout=30
        )
        response.raise_for_status()
        
        for major in range(13, 19):
            pattern = rf'href="v({major}\.\d+)/"'
            matches = re.findall(pattern, response.text)
            
            if matches:
                # 排序取最新
                sorted_versions = sorted(matches, key=lambda x: [int(n) for n in x.split('.')])
                latest = sorted_versions[-1]
                versions[str(major)] = latest
                print(f"  PostgreSQL {major}: {latest} (from FTP)")
                
    except Exception as e:
        print(f"✗ FTP 方法失败: {e}", file=sys.stderr)
    
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
    
    # 检查所有支持的版本
    all_majors = set(old_versions.keys()) | set(new_versions.keys())
    
    for major in sorted(all_majors):
        old_ver = old_versions.get(major, "0.0")
        new_ver = new_versions.get(major, "0.0")
        
        if old_ver != new_ver:
            if major in old_versions and major in new_versions:
                print(f"📦 版本变化: PostgreSQL {major}: {old_ver} -> {new_ver}")
            elif major not in old_versions:
                print(f"📦 新增版本: PostgreSQL {major}: {new_ver}")
            else:
                print(f"📦 移除版本: PostgreSQL {major}: {old_ver}")
            changed = True
    
    # 检查是否有版本缺失
    for major in ["13", "14", "15", "16", "17", "18"]:
        if major not in new_versions:
            print(f"⚠️ 警告: PostgreSQL {major} 在 Docker Hub 未找到")
    
    return changed


def main():
    print("=" * 60)
    print("PostgreSQL Docker 镜像版本检查")
    print("=" * 60)
    
    # 加载现有版本
    old_versions = load_existing_versions()
    if old_versions:
        print(f"\n当前记录的版本:")
        for major in sorted(old_versions.keys()):
            print(f"  PostgreSQL {major}: {old_versions[major]}")
    
    print("\n开始检查 Docker Hub 上的最新版本...\n")
    
    # 从 Docker Hub 获取版本
    new_versions = get_docker_hub_tags()
    
    # 如果 Docker Hub 获取失败，使用备用方案
    if len(new_versions) < 4:
        print(f"\n⚠️ Docker Hub 只获取到 {len(new_versions)} 个版本，尝试备用方案...")
        ftp_versions = get_versions_from_official_site()
        # 合并，优先使用 Docker Hub 的数据
        for major, version in ftp_versions.items():
            if major not in new_versions:
                new_versions[major] = version
    
    print(f"\nDocker Hub 最新可用版本:")
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
    
    # 输出结果供 GitHub Actions 使用
    print(f"\n版本JSON: {json.dumps(new_versions)}")
    print(f"是否变化: {has_changed}")
    
    # 如果在 GitHub Actions 环境中，设置输出变量
    if os.getenv('GITHUB_OUTPUT'):
        versions_json = json.dumps(new_versions, separators=(',', ':'))
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