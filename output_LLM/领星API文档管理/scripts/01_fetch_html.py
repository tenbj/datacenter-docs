# -*- coding: utf-8 -*-
"""
01_fetch_html.py - 抓取领星API文档网页源码

功能：
使用Playwright无头浏览器访问领星API文档网站，
等待页面加载完成后提取左侧导航栏的HTML源码。

使用方法：
    python 01_fetch_html.py --output-dir ../html/
    python 01_fetch_html.py --output-file lx_api_20260128.html

作者：Antigravity
创建时间：2026-01-28
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path


def fetch_api_html(output_dir: Path, output_file: str = None) -> Path:
    """
    抓取领星API文档网页源码
    
    Args:
        output_dir: 输出目录
        output_file: 输出文件名（可选，默认自动添加日期后缀）
        
    Returns:
        保存的文件路径
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("错误: 请先安装 playwright")
        print("运行: pip install playwright && playwright install chromium")
        sys.exit(1)
    
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成输出文件名
    if output_file:
        output_path = output_dir / output_file
    else:
        today = datetime.now().strftime('%Y%m%d')
        output_path = output_dir / f"lx_api_{today}.html"
    
    print(f"正在启动浏览器...")
    
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # 访问目标页面
        url = "https://apidoc.lingxing.com/"
        print(f"正在访问: {url}")
        page.goto(url, wait_until="networkidle")
        
        # 等待左侧导航栏加载完成
        print("等待页面内容加载...")
        try:
            page.wait_for_selector(".sidebar-links", timeout=30000)
        except:
            print("警告: 未找到标准导航栏选择器，尝试等待页面稳定...")
            page.wait_for_timeout(5000)
        
        # 获取左侧导航栏HTML
        sidebar_html = None
        
        # 尝试多种选择器
        selectors = [
            ".sidebar-links",
            ".sidebar",
            "nav",
            ".menu"
        ]
        
        for selector in selectors:
            try:
                element = page.query_selector(selector)
                if element:
                    sidebar_html = element.inner_html()
                    print(f"成功获取导航栏内容 (选择器: {selector})")
                    break
            except:
                continue
        
        if not sidebar_html:
            # 如果找不到特定元素，获取整个页面的HTML
            print("未找到导航栏，获取完整页面内容...")
            sidebar_html = page.content()
        
        # 关闭浏览器
        browser.close()
    
    # 保存到文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(sidebar_html)
    
    print(f"HTML源码已保存到: {output_path}")
    print(f"文件大小: {output_path.stat().st_size / 1024:.2f} KB")
    
    return output_path


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='抓取领星API文档网页源码',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='../html/',
        help='HTML输出目录（默认: ../html/）'
    )
    
    parser.add_argument(
        '--output-file',
        type=str,
        default=None,
        help='输出文件名（可选，默认自动添加日期后缀）'
    )
    
    args = parser.parse_args()
    
    # 处理路径
    script_dir = Path(__file__).parent
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = script_dir / output_dir
    
    print("=" * 50)
    print("领星API文档抓取工具")
    print("=" * 50)
    
    try:
        output_path = fetch_api_html(output_dir, args.output_file)
        print("\n抓取完成!")
        return 0
    except Exception as e:
        print(f"\n错误: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
