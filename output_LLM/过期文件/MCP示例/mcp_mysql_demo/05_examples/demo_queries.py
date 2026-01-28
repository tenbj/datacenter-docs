"""
查询演示脚本
展示各种 SQL 查询场景

使用方法：
    cd output_LLM/mcp_mysql_demo/02_src
    python ../05_examples/demo_queries.py
"""

import sys
import os
import json

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '02_src'))

from config import MYSQL_CONFIG
import mysql.connector


def get_connection():
    """获取数据库连接"""
    return mysql.connector.connect(**MYSQL_CONFIG)


def execute_query(sql: str, description: str = ""):
    """执行查询并打印结果"""
    print(f"\n{'=' * 60}")
    if description:
        print(f"📋 {description}")
    print(f"SQL: {sql}")
    print("-" * 60)
    
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql)
        results = cursor.fetchall()
        
        if results:
            print(f"结果 ({len(results)} 条记录):")
            print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
        else:
            print("(无结果)")
        
        cursor.close()
        conn.close()
        return results
        
    except mysql.connector.Error as e:
        print(f"❌ 错误: {e}")
        return None


def demo_show_tables():
    """演示：查看所有表"""
    execute_query(
        "SHOW TABLES",
        "查看数据库中的所有表"
    )


def demo_describe_table():
    """演示：查看表结构"""
    # 先获取第一个表名
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if tables:
        table_name = tables[0][0]
        execute_query(
            f"DESCRIBE `{table_name}`",
            f"查看表 '{table_name}' 的结构"
        )


def demo_select_all():
    """演示：查询所有记录（限制条数）"""
    # 先获取第一个表名
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if tables:
        table_name = tables[0][0]
        execute_query(
            f"SELECT * FROM `{table_name}` LIMIT 5",
            f"查询表 '{table_name}' 的前 5 条记录"
        )


def demo_count():
    """演示：统计记录数"""
    # 先获取第一个表名
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    cursor.close()
    conn.close()
    
    if tables:
        table_name = tables[0][0]
        execute_query(
            f"SELECT COUNT(*) as total FROM `{table_name}`",
            f"统计表 '{table_name}' 的记录总数"
        )


def demo_database_info():
    """演示：获取数据库信息"""
    execute_query(
        "SELECT DATABASE() as current_db, VERSION() as mysql_version, USER() as current_user",
        "获取当前数据库信息"
    )


def demo_table_status():
    """演示：获取表状态信息"""
    execute_query(
        f"SELECT TABLE_NAME, TABLE_ROWS, DATA_LENGTH, CREATE_TIME FROM information_schema.TABLES WHERE TABLE_SCHEMA = '{MYSQL_CONFIG['database']}'",
        "获取数据库中所有表的状态信息"
    )


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("🎯 MCP MySQL Server 查询演示")
    print("=" * 60)
    
    print(f"\n📌 目标数据库: {MYSQL_CONFIG['database']}@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG['port']}")
    
    # 运行各种演示查询
    demo_database_info()
    demo_show_tables()
    demo_describe_table()
    demo_select_all()
    demo_count()
    demo_table_status()
    
    print("\n" + "=" * 60)
    print("✅ 演示完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
