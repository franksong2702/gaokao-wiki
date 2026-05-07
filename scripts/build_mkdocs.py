#!/usr/bin/env python3
"""
构建高考文言文 Wiki 的 MkDocs 站点。

步骤：
1. 复制所有 .md 文件到临时 docs/ 目录
2. 转换 wikilinks 为标准 markdown 链接
3. 转换 Obsidian 图片嵌入 ![[...]] 为 markdown 图片
4. 从 docs/ 目录结构生成 nav 配置
5. 写入 mkdocs.yml

此脚本不修改任何源文件。所有转换仅在输出目录中执行。
"""

import os
import re
import sys
import yaml
from pathlib import Path

# 顶层文件
TOP_FILES = ["README"]

# 需要跳过的文件/目录
SKIP = {
    "AGENTS.md",
    ".obsidian",
    ".git",
}

# 目录映射
DIR_NAMES = {
    "gaokao-review": "高考文言文复习",
}


def wiki_to_relative_path(source_rel, target_abs):
    """
    将 Obsidian 完整路径链接转换为相对于源文件的相对链接。

    source_rel: 源文件相对于 wiki 根的路径
    target_abs: 目标文件的 Obsidian 绝对路径或 wiki 路径
    返回: 相对于源文件的链接路径
    """
    target = target_abs
    if target.startswith("[[") and target.endswith("]]"):
        target = target[2:-2]
    if "|" in target:
        target = target.split("|")[0]
    target = target.strip()
    if not target:
        return None

    # 去掉 Obsidian 根前缀（根据实际路径调整）
    prefix = "02_Learn/gaokao-review/"
    if target.startswith(prefix):
        target_rel = target[len(prefix):]
    else:
        # 检查是否是相对路径（不含 / 开头）
        if not target.startswith("/"):
            return target
        # 外部链接，不转换
        return None

    # 计算相对路径
    source_dir = os.path.dirname(source_rel)
    if not source_dir:
        source_dir = "."

    rel = os.path.relpath(target_rel, source_dir)
    rel = rel.replace("\\", "/")
    return rel


def convert_wikilink_in_file(content, source_rel):
    """转换文件中的所有 wikilinks 和 Obsidian 图片嵌入。"""

    # 1. 转换图片嵌入: ![[path|size]] -> ![alt](path)
    def replace_image(match):
        full = match.group(1)
        parts = full.split("|", 1)
        img_path = parts[0].strip()

        prefix = "02_Learn/gaokao-review/"
        if img_path.startswith(prefix):
            img_path = img_path[len(prefix):]

        source_dir = os.path.dirname(source_rel)
        if not source_dir:
            source_dir = "."
        rel = os.path.relpath(img_path, source_dir).replace("\\", "/")

        alt = os.path.basename(img_path).rsplit(".", 1)[0]
        return f"![{alt}]({rel})"

    content = re.sub(r'!\[\[(.+?)\]\]', replace_image, content)

    # 2. 转换 wikilinks: [[path|label]] -> [label](path)
    def replace_wikilink(match):
        full = match.group(1)
        if "|" in full:
            path, label = full.split("|", 1)
        else:
            path = full
            label = None

        path = path.strip()
        if not path:
            return match.group(0)

        rel = wiki_to_relative_path(source_rel, path)
        if rel is None:
            if label:
                return label
            fname = path.split("/")[-1]
            if fname.endswith(".md"):
                fname = fname[:-3]
            return fname

        if not rel.endswith(".md"):
            rel += ".md"

        if label is None or label.strip() == "":
            fname = os.path.basename(path)
            if fname.endswith(".md"):
                fname = fname[:-3]
            label = fname
        else:
            label = label.strip()

        return f"[{label}]({rel})"

    content = re.sub(r'\[\[(.+?)\]\]', replace_wikilink, content)

    # 3. 处理表格中转义的 wikilinks
    content = content.replace("[[", "[[").replace("]]", "]]")
    content = re.sub(r'\\\|', '|ESCAPED_PIPE|', content)
    content = re.sub(r'\[\[(.+?)\]\]', replace_wikilink, content)
    content = content.replace('|ESCAPED_PIPE|', '|')

    # 4. 转换 Obsidian block anchors 为 HTML 锚点
    content = re.sub(r'\s*\^([a-zA-Z0-9\u4e00-\u9fff-]+)(?:\s|$)',
                     r' <a id="\1"></a> ', content)

    # 5. 修复锚点链接
    content = re.sub(r'\.md#\^([a-zA-Z0-9\u4e00-\u9fff-]+)\.md',
                     r'#\1', content)
    content = re.sub(r'#\^([a-zA-Z0-9\u4e00-\u9fff-]+)\.md',
                     r'#\1', content)
    content = re.sub(r'#\^([a-zA-Z0-9\u4e00-\u9fff-]+)',
                     r'#\1', content)

    return content


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico"}
ASSET_EXTENSIONS = {".css", ".js"}


def copy_and_convert(src_root, dst_root):
    """复制文件并转换 wikilinks。"""
    converted_files = []

    for root, dirs, files in os.walk(src_root):
        # 跳过隐藏的目录和构建目录
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(".") and d != "_mkdocs_build"]

        for fname in files:
            if fname in SKIP:
                continue

            src = os.path.join(root, fname)
            src_rel = os.path.relpath(src, src_root)
            dst = os.path.join(dst_root, src_rel)

            os.makedirs(os.path.dirname(dst), exist_ok=True)

            # 图片等静态资源直接复制
            ext = os.path.splitext(fname)[1].lower()
            if ext in IMAGE_EXTENSIONS or ext in ASSET_EXTENSIONS:
                with open(src, "rb") as f_in, open(dst, "wb") as f_out:
                    f_out.write(f_in.read())
                converted_files.append(src_rel)
                continue

            if not fname.endswith(".md"):
                continue

            with open(src, "r", encoding="utf-8") as f:
                content = f.read()

            content = convert_wikilink_in_file(content, src_rel)

            with open(dst, "w", encoding="utf-8") as f:
                f.write(content)

            converted_files.append(src_rel)

    return converted_files


def make_title(name):
    """从文件名或目录名生成中文标题。"""
    if name in DIR_NAMES:
        return DIR_NAMES[name]
    title = name.replace(".md", "")
    # 处理 01-赤壁赋-苏轼.md -> 赤壁赋 · 苏轼
    title = re.sub(r'^\d+-', '', title)
    title = title.replace('-', ' · ')
    return title


def generate_nav(docs_root):
    """从目录结构生成 MkDocs nav 配置。"""
    nav = []

    # 顶层文件
    for fname in TOP_FILES:
        fpath = f"{fname}.md"
        full = os.path.join(docs_root, fpath)
        if os.path.exists(full):
            nav.append({make_title(fname): fpath})

    # 目录和文件
    for entry in sorted(os.listdir(docs_root)):
        if entry.startswith(".") or entry in SKIP:
            continue

        if entry.endswith(".md") and entry.replace(".md", "") in [f.replace(".md", "") for f in TOP_FILES]:
            continue

        fpath = os.path.join(docs_root, entry)
        if os.path.isdir(fpath):
            subdir_nav = build_subdir_nav(entry, fpath, docs_root)
            if subdir_nav:
                nav.append({make_title(entry): subdir_nav})
        elif entry.endswith(".md"):
            nav.append({make_title(entry): entry})

    return nav


def build_subdir_nav(dirname, dirpath, docs_root):
    """构建子目录的 nav 条目。"""
    entries = []

    md_files = sorted([f for f in os.listdir(dirpath) if f.endswith(".md") and f not in SKIP])
    for fname in md_files:
        rel = os.path.relpath(os.path.join(dirpath, fname), docs_root)
        entries.append({make_title(fname): rel})

    for subname in sorted(os.listdir(dirpath)):
        subpath = os.path.join(dirpath, subname)
        if not os.path.isdir(subpath) or subname.startswith("."):
            continue

        sub_entries = build_subdir_nav(subname, subpath, docs_root)
        if sub_entries:
            entries.append({make_title(subname): sub_entries})

    return entries


def write_mkdocs_config(nav, dst_dir):
    """写入 mkdocs.yml 配置文件。"""
    config = {
        "site_name": "高考文言文 Wiki",
        "site_description": "高考必背文言文篇目 · Cross Reading 复习资料",
        "site_author": "学夫",
        "repo_url": "https://github.com/franksong2702/gaokao-wiki",
        "repo_name": "franksong2702/gaokao-wiki",
        "docs_dir": "docs",
        "site_dir": "../_site",

        "theme": {
            "name": "material",
            "language": "zh",
            "features": [
                "navigation.sections",
                "navigation.expand",
                "navigation.top",
                "navigation.tracking",
                "search.highlight",
                "search.share",
                "search.suggest",
                "content.tabs.link",
                "content.code.copy",
            ],
            "palette": [
                {
                    "media": "(prefers-color-scheme: light)",
                    "scheme": "default",
                    "toggle": {"icon": "material/brightness-7", "name": "切换到暗色模式"},
                },
                {
                    "media": "(prefers-color-scheme: dark)",
                    "scheme": "slate",
                    "toggle": {"icon": "material/brightness-4", "name": "切换到亮色模式"},
                },
            ],
            "icon": {
                "repo": "fontawesome/brands/github",
            },
        },

        "nav": nav,

        "markdown_extensions": [
            "tables",
            "fenced_code",
            "attr_list",
            "md_in_html",
            "def_list",
            "footnotes",
            "admonition",
            "pymdownx.details",
            {"toc": {"permalink": True}},
        ],

        "plugins": [
            {"search": {
                "lang": ["zh"],
                "separator": r"[\s\-,:!=\[\]()\"'/]+",
            }},
        ],

        "extra_css": [
            "assets/stylesheets/extra.css",
        ],

        "extra": {
            "social": [
                {
                    "icon": "fontawesome/brands/github",
                    "link": "https://github.com/franksong2702",
                    "name": "GitHub",
                },
            ],
        },
    }

    yml_path = os.path.join(dst_dir, "mkdocs.yml")
    with open(yml_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)

    return yml_path


def main():
    if len(sys.argv) > 1:
        wiki_root = sys.argv[1]
    else:
        wiki_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    build_dir = os.path.join(wiki_root, "_mkdocs_build")
    docs_dir = os.path.join(build_dir, "docs")

    # 清理旧构建
    if os.path.exists(build_dir):
        import shutil
        shutil.rmtree(build_dir)

    print(f"源目录: {wiki_root}")
    print(f"构建目录: {build_dir}")

    # 1. 复制并转换
    print("正在转换文件...")
    files = copy_and_convert(wiki_root, docs_dir)
    print(f"转换了 {len(files)} 个文件")

    # 2. 生成 nav
    print("正在生成导航...")
    nav = generate_nav(docs_dir)

    # 3. 写入配置
    print("正在写入 mkdocs.yml...")
    write_mkdocs_config(nav, build_dir)

    print(f"完成！构建目录: {build_dir}")
    print(f"运行: mkdocs build -f {os.path.join(build_dir, 'mkdocs.yml')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
