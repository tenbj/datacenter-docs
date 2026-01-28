"""
数据库连接测试脚本
用于验证 MySQL 连接是否正常

使用方法：
    cd output_LLM/mcp_mysql_demo/02_src
    python ../05_examples/test_connection.py
"""

import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '02_src'))

from config import MYSQL_CONFIG
import mysql.connector


def test_connection():
    """测试数据库连接"""
    print("=" * 50)
    print("MySQL 连接测试")
    print("=" * 50)
    
    print(f"\n连接信息：")
    print(f"  Host: {MYSQL_CONFIG['host']}")
    print(f"  Port: {MYSQL_CONFIG['port']}")
    print(f"  Database: {MYSQL_CONFIG['database']}")
    print(f"  User: {MYSQL_CONFIG['user']}")
    
    try:
        print(f"\n正在连接...")
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        print("✅ 连接成功！")
        
        # 获取数据库版本
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        print(f"\nMySQL 版本: {version}")
        
        # 获取表列表
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"\n数据库中的表 ({len(tables)} 个):")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        print("\n✅ 测试完成，连接已关闭")
        return True
        
    except mysql.connector.Error as e:
        print(f"\n❌ 连接失败: {e}")
        return False


def test_simple_query():
    """测试简单查询"""
    print("\n" + "=" * 50)
    print("简单查询测试")
    print("=" * 50)
    
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(dictionary=True)
        
        # 获取第一个表的前 5 条记录
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if tables:
            first_table = list(tables[0].values())[0]
            print(f"\n查询表 '{first_table}' 的前 5 条记录:")
            
            cursor.execute(f"SELECT * FROM `{first_table}` LIMIT 5")
            rows = cursor.fetchall()
            
            if rows:
                # 打印列名
                columns = list(rows[0].keys())
                print(f"  列: {', '.join(columns)}")
                print(f"  记录数: {len(rows)}")
                for i, row in enumerate(rows, 1):
                    print(f"  [{i}] {row}")
            else:
                print("  表为空")
        else:
            print("数据库中没有表")
        
        cursor.close()
        conn.close()
        print("\n✅ 查询测试完成")
        return True
        
    except mysql.connector.Error as e:
        print(f"\n❌ 查询失败: {e}")
        return False


if __name__ == "__main__":
    print("\n🚀 开始数据库连接测试...\n")
    
    # 运行测试
    connection_ok = test_connection()
    
    if connection_ok:
        test_simple_query()
    
    print("\n" + "=" * 50)
    print("测试结束")
    print("=" * 50)
