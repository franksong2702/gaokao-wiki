# 高考文言文 Wiki

高考必背文言文篇目 · Cross Reading 复习资料

## 篇目

- [赤壁赋 · 苏轼](01-赤壁赋-苏轼.md)
- [过秦论 · 贾谊](02-过秦论-贾谊.md)
- [六国论 · 苏洵](03-六国论-苏洵.md)
- [兰亭集序 · 王羲之](04-兰亭集序-王羲之.md)
- [陈情表 · 李密](05-陈情表-李密.md)
- [阿房宫赋 · 杜牧](06-阿房宫赋-杜牧.md)

## 说明

本项目使用 Obsidian Markdown 编写，通过 MkDocs Material 主题发布为网页。

源文件位于 [Obsidian Vault](file:///Users/xuefusong/syncthings/Obsidian/Obsidian%20Vault/02_Learn/gaokao-review/)，
构建脚本 `scripts/build_mkdocs.py` 会自动转换 wikilinks 并生成站点配置。

## 本地开发

```bash
pip install mkdocs-material pyyaml
python scripts/build_mkdocs.py
cd _mkdocs_build
mkdocs serve -f mkdocs.yml
```
