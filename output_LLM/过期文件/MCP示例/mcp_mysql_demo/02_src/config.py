"""
MCP MySQL Server 配置文件
从环境变量读取数据库连接信息
"""

import os
from dotenv import load_dotenv

# 加载环境变量（从 .env 文件）
load_dotenv()

# MySQL 数据库配置
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "172.17.1.141"),
    "port": int(os.getenv("MYSQL_PORT", "3307")),
    "user": os.getenv("MYSQL_USER", "test_ai"),
    "password": os.getenv("MYSQL_PASSWORD", "EB1FF34BA2C33780"),
    "database": os.getenv("MYSQL_DATABASE", "test_ai"),
}

# 安全配置
SECURITY_CONFIG = {
    # 允许的 SQL 操作类型
    "allowed_operations": ["SELECT", "SHOW", "DESCRIBE"],
    # 禁止的 SQL 操作类型
    "forbidden_operations": ["DROP", "TRUNCATE", "ALTER", "CREATE"],
    # 最大返回行数
    "max_limit": 1000,
    # 默认返回行数
    "default_limit": 100,
}
