"""
MCP MySQL Server - 让 AI 能够查询 MySQL 数据库

功能：
1. 获取数据库表列表
2. 获取表结构信息
3. 执行 SQL 查询
4. 执行 SQL 修改（INSERT/UPDATE/DELETE）

使用方式：
- 直接运行：python server.py
- 通过 MCP Client 配置调用
"""

import asyncio
import json
from typing import Any

import mysql.connector
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
)

from config import MYSQL_CONFIG, SECURITY_CONFIG


# ============================================================
# 第一部分：创建 MCP Server 实例
# ============================================================

# 创建 Server 实例
server = Server("mysql-mcp-server")


# ============================================================
# 第二部分：定义 Resources（资源）
# 资源是可读取的数据，类似于 REST API 的 GET 请求
# ============================================================

@server.list_resources()
async def list_resources() -> list[Resource]:
    """列出所有可用的资源"""
    return [
        Resource(
            uri="mysql://tables",
            name="数据库表列表",
            description="获取数据库中所有表的列表",
            mimeType="application/json",
        ),
        Resource(
            uri="mysql://schema/{table_name}",
            name="表结构",
            description="获取指定表的结构信息，将 {table_name} 替换为实际表名",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """读取资源内容"""
    
    if uri == "mysql://tables":
        # 获取所有表名
        tables = await execute_query("SHOW TABLES")
        return json.dumps(tables, ensure_ascii=False, indent=2)
    
    elif uri.startswith("mysql://schema/"):
        # 获取表结构
        table_name = uri.split("/")[-1]
        # 安全检查：防止 SQL 注入
        if not table_name.isidentifier():
            raise ValueError(f"无效的表名: {table_name}")
        schema = await execute_query(f"DESCRIBE `{table_name}`")
        return json.dumps(schema, ensure_ascii=False, indent=2)
    
    raise ValueError(f"未知资源: {uri}")


# ============================================================
# 第三部分：定义 Tools（工具）
# 工具是可执行的操作，类似于 REST API 的 POST 请求
# ============================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的工具"""
    return [
        Tool(
            name="query",
            description="执行 SQL 查询语句（仅支持 SELECT）",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "要执行的 SQL 查询语句",
                    },
                    "limit": {
                        "type": "integer",
                        "description": f"返回结果的最大行数，默认 {SECURITY_CONFIG['default_limit']}，最大 {SECURITY_CONFIG['max_limit']}",
                        "default": SECURITY_CONFIG["default_limit"],
                    },
                },
                "required": ["sql"],
            },
        ),
        Tool(
            name="execute",
            description="执行 SQL 修改语句（INSERT/UPDATE/DELETE）",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {
                        "type": "string",
                        "description": "要执行的 SQL 语句",
                    },
                },
                "required": ["sql"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """执行工具调用"""
    
    if name == "query":
        # 执行查询
        sql = arguments["sql"]
        limit = min(
            arguments.get("limit", SECURITY_CONFIG["default_limit"]),
            SECURITY_CONFIG["max_limit"]
        )
        
        # 安全检查：只允许 SELECT 和 SHOW
        sql_upper = sql.strip().upper()
        if not (sql_upper.startswith("SELECT") or sql_upper.startswith("SHOW")):
            return [TextContent(
                type="text",
                text="错误：query 工具只支持 SELECT 和 SHOW 语句"
            )]
        
        # 添加 LIMIT（如果没有的话）
        if "LIMIT" not in sql_upper:
            sql = f"{sql} LIMIT {limit}"
        
        try:
            result = await execute_query(sql)
            return [TextContent(
                type="text",
                text=json.dumps(result, ensure_ascii=False, indent=2, default=str)
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"查询错误: {str(e)}"
            )]
    
    elif name == "execute":
        # 执行修改
        sql = arguments["sql"]
        
        # 安全检查：禁止危险操作
        sql_upper = sql.strip().upper()
        for forbidden in SECURITY_CONFIG["forbidden_operations"]:
            if sql_upper.startswith(forbidden):
                return [TextContent(
                    type="text",
                    text=f"错误：禁止执行 {forbidden} 操作"
                )]
        
        try:
            affected_rows = await execute_modify(sql)
            return [TextContent(
                type="text",
                text=f"执行成功，影响行数：{affected_rows}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"执行错误: {str(e)}"
            )]
    
    raise ValueError(f"未知工具: {name}")


# ============================================================
# 第四部分：数据库操作辅助函数
# ============================================================

async def execute_query(sql: str) -> list[dict]:
    """执行查询并返回结果"""
    def _query():
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return result
    
    # 在线程池中执行阻塞操作
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _query)


async def execute_modify(sql: str) -> int:
    """执行修改并返回影响行数"""
    def _modify():
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
        conn.close()
        return affected
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _modify)


# ============================================================
# 第五部分：启动 Server
# ============================================================

async def main():
    """启动 MCP Server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
