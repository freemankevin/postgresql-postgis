#!/usr/bin/env python3
"""
GitHub Actions 构建辅助脚本
负责版本管理、构建决策和镜像检查
"""
import sys
import json
import os
import requests
import re
from typing import Dict, List, Optional


def parse_version(version_str: str) -> tuple:
    """将版本号字符串转换为可比较的元组"""
    try:
        parts = version_str.split('.')
        return tuple(int(x) for x in parts)
    except:
        return (0, 0)


def get_docker_hub_tags(max_pages: int = 10) -> Dict[str, str]:
    """从 Docker Hub 获取 postgres 镜像的所有 bookworm 标签，提取最新版本"""
    versions = {}
    url = "https://hub.docker.com/v2/repositories/library/postgres/tags/"
    
    print("从 Docker Hub 获取 postgres 镂像版本信息...")
    
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
                
                match = re.match(r'^(\d+)\.(\d+)-bookworm$', tag_name)
                if match:
                    major = match.group(1)
                    minor = match.group(2)
                    full_version = f"{major}.{minor}"
                    
                    if 14 <= int(major) <= 18:
                        current = versions.get(major, "0.0")
                        if parse_version(full_version) > parse_version(current):
                            versions[major] = full_version
                            print(f"  发现更新: PostgreSQL {major}: {full_version}")
            
            if not data.get("next"):
                break
                
        except Exception as e:
            print(f"✗ 获取第 {page} 页失败: {e}", file=sys.stderr)
            break
    
    return versions


def get_versions_from_official_site() -> Dict[str, str]:
    """备用方案：从 PostgreSQL 官方 FTP 获取版本"""
    print("尝试从 PostgreSQL FTP 获取版本作为备用...")
    versions = {}
    
    try:
        response = requests.get(
            "https://ftp.postgresql.org/pub/source/",
            timeout=30
        )
        response.raise_for_status()
        
        for major in range(14, 19):
            pattern = rf'href="v({major}\.\d+)/"'
            matches = re.findall(pattern, response.text)
            
            if matches:
                sorted_versions = sorted(matches, key=lambda x: [int(n) for n in x.split('.')])
                latest = sorted_versions[-1]
                versions[str(major)] = latest
                print(f"  PostgreSQL {major}: {latest} (from FTP)")
                
    except Exception as e:
        print(f"✗ FTP 方法失败: {e}", file=sys.stderr)
    
    return versions


def has_version_changed(old_versions: Dict[str, str], new_versions: Dict[str, str]) -> bool:
    """检查版本是否有变化"""
    changed = False
    
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
    
    for major in ["14", "15", "16", "17", "18"]:
        if major not in new_versions:
            print(f"⚠️ 警告: PostgreSQL {major} 在 Docker Hub 未找到")
    
    return changed


def check_versions() -> bool:
    """检查 PostgreSQL 版本更新"""
    print("=" * 60)
    print("PostgreSQL Docker 镜像版本检查")
    print("=" * 60)
    
    old_versions = load_versions()
    if old_versions:
        print(f"\n当前记录的版本:")
        for major in sorted(old_versions.keys()):
            print(f"  PostgreSQL {major}: {old_versions[major]}")
    
    print("\n开始检查 Docker Hub 上的最新版本...\n")
    
    new_versions = get_docker_hub_tags()
    
    if len(new_versions) < 4:
        print(f"\n⚠️ Docker Hub 只获取到 {len(new_versions)} 个版本，尝试备用方案...")
        ftp_versions = get_versions_from_official_site()
        for major, version in ftp_versions.items():
            if major not in new_versions:
                new_versions[major] = version
    
    print(f"\nDocker Hub 最新可用版本:")
    for major in sorted(new_versions.keys()):
        print(f"  PostgreSQL {major}: {new_versions[major]}")
    
    has_changed = has_version_changed(old_versions, new_versions)
    
    try:
        with open('pg_version.json', 'w') as f:
            json.dump(new_versions, f, indent=2, sort_keys=True)
        print("\n✓ pg_version.json 文件已更新")
    except Exception as e:
        print(f"\n✗ 更新版本文件失败: {e}", file=sys.stderr)
        sys.exit(1)
    
    if has_changed:
        update_readme()
    
    print(f"\n版本JSON: {json.dumps(new_versions)}")
    print(f"是否变化: {has_changed}")
    
    github_output = os.getenv('GITHUB_OUTPUT')
    if github_output:
        versions_json = json.dumps(new_versions, separators=(',', ':'))
        changed_str = 'true' if has_changed else 'false'
        with open(github_output, 'a') as f:
            f.write(f"versions={versions_json}\n")
            f.write(f"changed={changed_str}\n")
        print(f"\n✓ GitHub Actions 输出变量已设置:")
        print(f"  - versions: {versions_json}")
        print(f"  - changed: {changed_str}")
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)
    
    return has_changed


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
    
    # 排除 PG13 及以下 (EOL)
    supported_versions = [v for v in versions.keys() if int(v) >= 14]
    
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
        return True


def get_all_ghcr_tags(registry: str = "freemankevin/postgresql-postgis") -> List[str]:
    """
    获取 GHCR 上所有镜像标签
    
    Args:
        registry: 镜像仓库名
    
    Returns:
        标签列表
    """
    owner = registry.split("/")[0]
    package_name = registry.split("/")[1]
    
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("⚠ 未设置 GITHUB_TOKEN，无法获取 GHCR 标签")
        return []
    
    url = f"https://api.github.com/users/{owner}/packages/container/{package_name}/versions"
    
    try:
        response = requests.get(
            url, 
            headers={"Authorization": f"token {token}"}, 
            timeout=30
        )
        
        if response.status_code == 200:
            versions = response.json()
            tags = []
            for version in versions:
                version_tags = version.get("metadata", {}).get("container", {}).get("tags", [])
                tags.extend(version_tags)
            return tags
        elif response.status_code == 404:
            return []
        else:
            print(f"⚠ 获取 GHCR 标签失败: HTTP {response.status_code}")
            return []
    except requests.RequestException as e:
        print(f"⚠ 获取 GHCR 标签失败: {e}")
        return []


def get_ghcr_tags_for_major(pg_major: str, registry: str = "freemankevin/postgresql-postgis") -> List[str]:
    """
    获取 GHCR 上指定主版本的所有标签
    
    Args:
        pg_major: PostgreSQL 主版本号
        registry: 镜像仓库名
    
    Returns:
        该主版本的所有标签列表
    """
    all_tags = get_all_ghcr_tags(registry)
    pattern = re.compile(rf"^{pg_major}\.\d+$")
    return [tag for tag in all_tags if pattern.match(tag)]


def delete_ghcr_tag(tag: str, token: str, registry: str = "freemankevin/postgresql-postgis") -> bool:
    """
    删除 GHCR 上的镜像标签
    
    Args:
        tag: 要删除的标签
        token: GitHub Token (需要 delete:packages 权限)
        registry: 镜像仓库名
    
    Returns:
        True 如果删除成功
    """
    owner = registry.split("/")[0]
    package_name = registry.split("/")[1]
    
    url = f"https://api.github.com/users/{owner}/packages/container/{package_name}/versions"
    
    try:
        response = requests.get(url, headers={"Authorization": f"token {token}"}, timeout=30)
        response.raise_for_status()
        versions = response.json()
        
        for version in versions:
            if tag in version.get("metadata", {}).get("container", {}).get("tags", []):
                version_id = version.get("id")
                if version_id:
                    delete_url = f"https://api.github.com/users/{owner}/packages/container/{package_name}/versions/{version_id}"
                    del_response = requests.delete(
                        delete_url, 
                        headers={"Authorization": f"token {token}"},
                        timeout=30
                    )
                    if del_response.status_code == 204:
                        print(f"✓ 已删除旧镜像标签: {tag}")
                        return True
                    else:
                        print(f"✗ 删除标签 {tag} 失败: HTTP {del_response.status_code}")
                        return False
        
        print(f"⚠ 未找到标签 {tag} 对应的版本")
        return False
        
    except requests.RequestException as e:
        print(f"✗ 删除标签 {tag} 失败: {e}")
        return False


def cleanup_old_versions(
    pg_major: str,
    keep_version: str,
    dry_run: bool = True,
    registry: str = "freemankevin/postgresql-postgis"
) -> List[str]:
    """
    清理指定主版本的旧镜像标签
    
    Args:
        pg_major: PostgreSQL 主版本号
        keep_version: 要保留的版本
        dry_run: 是否仅模拟运行
        registry: 镜像仓库名
    
    Returns:
        已删除（或将要删除）的标签列表
    """
    print(f"\n🔍 检查 PostgreSQL {pg_major} 的旧镜像标签...")
    
    old_tags = get_ghcr_tags_for_major(pg_major, registry)
    deleted_tags = []
    
    if not old_tags:
        print(f"  未找到 PostgreSQL {pg_major} 的旧镜像标签")
        return deleted_tags
    
    for tag in old_tags:
        if tag != keep_version:
            print(f"  发现旧版本: {tag} (当前保留: {keep_version})")
            
            if not dry_run:
                token = os.getenv("GITHUB_TOKEN")
                if token:
                    if delete_ghcr_tag(tag, token, registry):
                        deleted_tags.append(tag)
                else:
                    print(f"  ⚠ 未设置 GITHUB_TOKEN，无法删除")
            else:
                print(f"  [DRY-RUN] 将删除: {tag}")
                deleted_tags.append(tag)
    
    return deleted_tags


def check_image_exists(version: str, registry: str = "ghcr.io/freemankevin/postgresql-postgis") -> bool:
    """
    检查我们的镜像是否已存在
    
    Args:
        version: 版本号 (如 "14.21")
        registry: 镜像仓库名
    
    Returns:
        True 如果镜像存在
    """
    if registry.startswith("ghcr.io/"):
        return check_ghcr_image_exists(version, registry.replace("ghcr.io/", ""))
    
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


def check_ghcr_image_exists(version: str, registry: str) -> bool:
    """
    检查 GHCR 上镜像是否已存在
    
    Args:
        version: 版本号 (如 "14.21")
        registry: GHCR 仓库名 (如 "freemankevin/postgresql-postgis")
    
    Returns:
        True 如果镜像存在
    """
    all_tags = get_all_ghcr_tags(registry)
    exists = version in all_tags
    
    if exists:
        print(f"✓ 镜像已存在: ghcr.io/{registry}:{version}")
    else:
        print(f"○ 镜像不存在: ghcr.io/{registry}:{version}")
    
    return exists


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
- **镜像**: `ghcr.io/freemankevin/postgresql-postgis:{version}`
- **平台**: linux/amd64, linux/arm64
"""
    else:
        return f"""### ⏭️ PostgreSQL {pg_major} 跳过构建

镜像 `ghcr.io/freemankevin/postgresql-postgis:{version}` 已存在
"""


def generate_version_table() -> str:
    """生成 Markdown 版本表格"""
    versions = load_versions()
    
    table = "## 📦 可用版本\n\n"
    table += "| PostgreSQL 版本 | 镜像标签 |\n"
    table += "|----------------|---------|\n"
    
    for major in sorted(versions.keys(), reverse=True):
        version = versions[major]
        table += f"| {major}.x | `ghcr.io/freemankevin/postgresql-postgis:{version}` |\n"
    
    return table


def update_readme() -> bool:
    """更新 README.md 中的版本表格"""
    try:
        table = generate_version_table()
        
        with open('README.md', 'r', encoding='utf-8') as f:
            content = f.read()
        
        pattern = r'## 📦 可用版本.*?(?=##|$)'
        replacement = table + "\n"
        
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("[OK] README.md version table updated")
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to update README.md: {e}")
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: build-helper.py <command> [args...]")
        print("命令:")
        print("  check-versions             - 检查 PostgreSQL 版本更新")
        print("  update-readme              - 更新 README.md 版本表格")
        print("  matrix [version]           - 生成构建矩阵")
        print("  check <pg_major>           - 检查镜像是否存在")
        print("  should-build <pg_major> [--force] [--manual]  - 判断是否应该构建")
        print("  summary <pg_major> <built> - 生成构建摘要")
        print("  cleanup <pg_major>         - 清理旧版本镜像")
        print("  cleanup-all                - 清理所有主版本的旧镜像")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == "check-versions":
            check_versions()
        
        elif command == "update-readme":
            success = update_readme()
            sys.exit(0 if success else 1)
        
        elif command == "matrix":
            # 生成构建矩阵
            pg_version = sys.argv[2] if len(sys.argv) > 2 else None
            versions = get_build_matrix(pg_version)
            
            # 输出 JSON 格式供 GitHub Actions 使用
            matrix_json = json.dumps(versions)
            print(matrix_json)
            
            # 设置 GitHub Actions 输出
            github_output = os.getenv('GITHUB_OUTPUT')
            if github_output:
                with open(github_output, 'a') as f:
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
            github_output = os.getenv('GITHUB_OUTPUT')
            if github_output:
                with open(github_output, 'a') as f:
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
            github_output = os.getenv('GITHUB_OUTPUT')
            if github_output:
                versions = load_versions()
                version = versions.get(pg_major, "")
                
                with open(github_output, 'a') as f:
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
            github_step_summary = os.getenv('GITHUB_STEP_SUMMARY')
            if github_step_summary:
                with open(github_step_summary, 'a') as f:
                    f.write(summary)
        
        elif command == "cleanup":
            # 清理指定主版本的旧镜像
            if len(sys.argv) < 3:
                print("❌ 缺少参数: pg_major")
                sys.exit(1)
            
            pg_major = sys.argv[2]
            versions = load_versions()
            keep_version = versions.get(pg_major)
            
            if not keep_version:
                print(f"❌ 未找到 PostgreSQL {pg_major} 的版本信息")
                sys.exit(1)
            
            deleted = cleanup_old_versions(pg_major, keep_version, dry_run=False)
            
            # 设置 GitHub Actions 输出
            github_output = os.getenv('GITHUB_OUTPUT')
            if github_output:
                with open(github_output, 'a') as f:
                    f.write(f"deleted_tags={json.dumps(deleted)}\n")
        
        elif command == "cleanup-all":
            # 清理所有主版本的旧镜像
            versions = load_versions()
            all_deleted = {}
            
            for pg_major, keep_version in sorted(versions.items()):
                if int(pg_major) < 14:
                    continue
                deleted = cleanup_old_versions(pg_major, keep_version, dry_run=False)
                if deleted:
                    all_deleted[pg_major] = deleted
            
            # 设置 GitHub Actions 输出
            github_output = os.getenv('GITHUB_OUTPUT')
            if github_output:
                with open(github_output, 'a') as f:
                    f.write(f"all_deleted_tags={json.dumps(all_deleted)}\n")
            
            print(f"\n✓ 清理完成，共删除 {sum(len(v) for v in all_deleted.values())} 个旧镜像标签")
        
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