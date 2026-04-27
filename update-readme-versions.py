#!/usr/bin/env python3
"""
自动更新 README.md 中的版本表格
"""
import json
import re
import sys

def load_versions():
    """从 pg_version.json 加载版本信息"""
    with open('pg_version.json', 'r') as f:
        return json.load(f)

def generate_version_table(versions):
    """生成 Markdown 版本表格"""
    table = "## 📦 可用版本\n\n"
    table += "| PostgreSQL 版本 | 镜像标签 |\n"
    table += "|----------------|---------|\n"
    
    for major in sorted(versions.keys(), reverse=True):
        version = versions[major]
        table += f"| {major}.x | `ghcr.io/freemankevin/postgresql-postgis:{version}` |\n"
    
    return table

def update_readme(table):
    """更新 README.md 中的版本表格"""
    with open('README.md', 'r') as f:
        content = f.read()
    
    # 查找版本表格部分并替换
    pattern = r'## 📦 可用版本.*?(?=##|$)'
    replacement = table + "\n"
    
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    
    with open('README.md', 'w') as f:
        f.write(new_content)
    
    print("✓ README.md 版本表格已更新")

def main():
    """主函数"""
    try:
        versions = load_versions()
        print(f"当前版本: {versions}")
        
        table = generate_version_table(versions)
        print("生成的表格:")
        print(table)
        
        update_readme(table)
        
        print("\n✓ 版本表格更新完成")
        return 0
        
    except Exception as e:
        print(f"✗ 错误: {e}", file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())