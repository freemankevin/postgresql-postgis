#!/usr/bin/env python3
"""
GitHub Actions 构建辅助脚本
负责版本管理、构建决策和镜像检查
"""
import sys
import json
import os
import requests
from typing import Dict, List, Optional


def load_versions() -> Dict[str, str]:
    """加载版本配置"""
    try:
        with open('pg_version.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ pg_version.json 文件不存在")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析错误: {e}")
        sys.exit(1)


def get_build_matrix(pg_version: Optional[str] = None) -> List[str]:
    """
    生成构建矩阵
    
    Args:
        pg_version: 指定的版本号，None 表示构建所有版本
    
    Returns:
        版本号列表
    """
    versions = load_versions()
    
    # 排除 PG12 (EOL)
    supported_versions = [v for v in versions.keys() if v != "12"]
    
    if pg_version and pg_version != "all":
        if pg_version not in supported_versions:
            print(f"❌ 不支持的版本: {pg_version}")
            sys.exit(1)
        return [pg_version]
    
    return sorted(supported_versions, key=int)


def check_upstream_image_exists(pg_major: str, pg_version: str) -> bool:
    """
    检查 Docker Hub 上 postgres 官方镜像是否存在（冗余检查，确保万无一失）
    
    Args:
        pg_major: 主版本号 (如 "14")
        pg_version: 完整版本号 (如 "14.21")
    
    Returns:
        True 如果上游镜像存在
    """
    url = f"https://hub.docker.com/v2/repositories/library/postgres/tags/{pg_version}-bookworm/"
    
    try:
        response = requests.get(url, timeout=10)
        exists = response.status_code == 200
        
        if exists:
            print(f"✓ 上游镜像存在: postgres:{pg_version}-bookworm")
        else:
            print(f"✗ 上游镜像不存在: postgres:{pg_version}-bookworm")
        
        return exists
    except requests.RequestException as e:
        print(f"⚠ 检查上游镜像失败: {e}")
        # 如果检查失败，假设存在（因为 search-version.py 已经检查过了）
        return True


def check_image_exists(version: str, registry: str = "freelabspace/postgresql-postgis") -> bool:
    """
    检查我们的镜像是否已存在
    
    Args:
        version: 版本号 (如 "14.21")
        registry: 镜像仓库名
    
    Returns:
        True 如果镜像存在
    """
    url = f"https://hub.docker.com/v2/repositories/{registry}/tags/{version}/"
    
    try:
        response = requests.get(url, timeout=10)
        exists = response.status_code == 200
        
        if exists:
            print(f"✓ 镜像已存在: {registry}:{version}")
        else:
            print(f"○ 镜像不存在: {registry}:{version}")
        
        return exists
    except requests.RequestException as e:
        print(f"⚠ 检查镜像失败: {e}")
        return False


def should_build(
    pg_major: str,
    force_rebuild: bool = False,
    manual_trigger: bool = False
) -> bool:
    """
    判断是否应该构建镜像
    
    Args:
        pg_major: PostgreSQL 主版本号
        force_rebuild: 是否强制重建
        manual_trigger: 是否手动触发
    
    Returns:
        True 如果应该构建
    """
    versions = load_versions()
    version = versions.get(pg_major)
    
    if not version:
        print(f"❌ 未找到 PostgreSQL {pg_major} 的版本信息")
        return False
    
    # 强制重建
    if force_rebuild:
        print(f"🔨 强制重建: PostgreSQL {pg_major} ({version})")
        return True
    
    # 双重检查：确认上游镜像存在（防止 search-version.py 和实际构建之间的时间差）
    if not check_upstream_image_exists(pg_major, version):
        print(f"⛔ 上游镜像不存在，跳过构建: PostgreSQL {pg_major} ({version})")
        return False
    
    # 检查我们的镜像是否已存在
    exists = check_image_exists(version)
    
    # 镜像不存在，需要构建
    if not exists:
        print(f"📦 需要构建: PostgreSQL {pg_major} ({version})")
        return True
    
    # 手动触发且镜像存在，仍然构建
    if manual_trigger:
        print(f"🔄 手动触发，重新构建: PostgreSQL {pg_major} ({version})")
        return True
    
    print(f"⏭️ 跳过构建: PostgreSQL {pg_major} ({version})")
    return False


def generate_build_summary(pg_major: str, built: bool) -> str:
    """
    生成构建摘要
    
    Args:
        pg_major: PostgreSQL 主版本号
        built: 是否实际构建了镜像
    
    Returns:
        Markdown 格式的摘要
    """
    versions = load_versions()
    version = versions.get(pg_major, "unknown")
    
    if built:
        return f"""### ✅ PostgreSQL {pg_major} 构建完成

- **版本**: {version}
- **镜像**: `freelabspace/postgresql-postgis:{version}`
- **平台**: linux/amd64, linux/arm64
"""
    else:
        return f"""### ⏭️ PostgreSQL {pg_major} 跳过构建

镜像 `freelabspace/postgresql-postgis:{version}` 已存在
"""


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: build-helper.py <command> [args...]")
        print("命令:")
        print("  matrix [version]           - 生成构建矩阵")
        print("  check <pg_major>           - 检查镜像是否存在")
        print("  should-build <pg_major> [--force] [--manual]  - 判断是否应该构建")
        print("  summary <pg_major> <built> - 生成构建摘要")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == "matrix":
            # 生成构建矩阵
            pg_version = sys.argv[2] if len(sys.argv) > 2 else None
            versions = get_build_matrix(pg_version)
            
            # 输出 JSON 格式供 GitHub Actions 使用
            matrix_json = json.dumps(versions)
            print(matrix_json)
            
            # 设置 GitHub Actions 输出
            if os.getenv('GITHUB_OUTPUT'):
                with open(os.getenv('GITHUB_OUTPUT'), 'a') as f:
                    f.write(f"matrix={matrix_json}\n")
        
        elif command == "check":
            # 检查镜像是否存在
            if len(sys.argv) < 3:
                print("❌ 缺少参数: pg_major")
                sys.exit(1)
            
            pg_major = sys.argv[2]
            versions = load_versions()
            version = versions.get(pg_major)
            
            if not version:
                print(f"❌ 未找到版本信息")
                sys.exit(1)
            
            exists = check_image_exists(version)
            
            # 设置 GitHub Actions 输出
            if os.getenv('GITHUB_OUTPUT'):
                with open(os.getenv('GITHUB_OUTPUT'), 'a') as f:
                    f.write(f"exists={'true' if exists else 'false'}\n")
                    f.write(f"version={version}\n")
        
        elif command == "should-build":
            # 判断是否应该构建
            if len(sys.argv) < 3:
                print("❌ 缺少参数: pg_major")
                sys.exit(1)
            
            pg_major = sys.argv[2]
            force_rebuild = "--force" in sys.argv
            manual_trigger = "--manual" in sys.argv
            
            should = should_build(pg_major, force_rebuild, manual_trigger)
            
            # 设置 GitHub Actions 输出
            if os.getenv('GITHUB_OUTPUT'):
                versions = load_versions()
                version = versions.get(pg_major, "")
                
                with open(os.getenv('GITHUB_OUTPUT'), 'a') as f:
                    f.write(f"should_build={'true' if should else 'false'}\n")
                    f.write(f"version={version}\n")
            
            sys.exit(0 if should else 1)
        
        elif command == "summary":
            # 生成构建摘要
            if len(sys.argv) < 4:
                print("❌ 缺少参数: pg_major, built")
                sys.exit(1)
            
            pg_major = sys.argv[2]
            built = sys.argv[3].lower() in ('true', '1', 'yes')
            
            summary = generate_build_summary(pg_major, built)
            print(summary)
            
            # 追加到 GitHub Actions 摘要
            if os.getenv('GITHUB_STEP_SUMMARY'):
                with open(os.getenv('GITHUB_STEP_SUMMARY'), 'a') as f:
                    f.write(summary)
        
        else:
            print(f"❌ 未知命令: {command}")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()