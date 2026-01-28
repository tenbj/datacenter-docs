# 领星API文档管理系统

此目录用于管理领星API文档的自动化抓取、解析和版本控制。

## 目录结构

```
领星API文档管理/
├── 领星API接口列表_vX.X.md    # 正式文档（最新版）
├── csv/                        # CSV输出目录
├── md/                         # MD临时输出目录
├── html/                       # HTML源码缓存
├── scripts/                    # 脚本目录
└── 过期文件/                   # 归档的旧版本
```

## 使用方法

```bash
# 一键执行完整流程
python scripts/main.py

# 跳过抓取步骤（使用现有HTML）
python scripts/main.py --skip-fetch

# 仅执行抓取步骤
python scripts/main.py --only-fetch
```

## 脚本说明

| 脚本                 | 功能                     |
| -------------------- | ------------------------ |
| 01_fetch_html.py     | 抓取领星API文档网页源码  |
| 02_parse_to_md.py    | 解析HTML生成Markdown文档 |
| 03_parse_to_csv.py   | 解析HTML生成CSV文件      |
| 04_compare_update.py | 比对差异并更新版本       |
| main.py              | 主控脚本，串联所有步骤   |
