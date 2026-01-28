"""
领星API文档自动抓取脚本
功能：自动从领星API文档网站抓取左侧导航HTML，并生成Markdown和CSV文件
依赖：pip install playwright
首次使用需要安装浏览器：playwright install chromium
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# 尝试导入playwright
try:
    from playwright.async_api import async_playwright
except ImportError:
    print("错误：未安装playwright库")
    print("请运行以下命令安装：")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)


# 配置
API_DOC_URL = "https://apidoc.lingxing.com/#/"
WAIT_TIMEOUT = 30000  # 等待超时时间（毫秒）
LOAD_DELAY = 5  # 页面加载后额外等待时间（秒）


async def fetch_sidebar_html(output_path: Path) -> bool:
    """
    使用Playwright抓取领星API文档左侧导航HTML
    
    Args:
        output_path: HTML文件保存路径
        
    Returns:
        bool: 是否成功
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始抓取领星API文档...")
    
    async with async_playwright() as p:
        # 启动浏览器（无头模式）
        print("启动浏览器...")
        browser = await p.chromium.launch(headless=True)
        
        try:
            # 创建页面
            page = await browser.new_page()
            
            # 访问页面
            print(f"访问页面: {API_DOC_URL}")
            await page.goto(API_DOC_URL, wait_until="networkidle", timeout=WAIT_TIMEOUT)
            
            # 等待页面JavaScript渲染完成
            print(f"等待页面渲染（{LOAD_DELAY}秒）...")
            await asyncio.sleep(LOAD_DELAY)
            
            # 等待侧边栏加载
            print("等待侧边栏加载...")
            sidebar_selector = ".sidebar-nav"
            try:
                await page.wait_for_selector(sidebar_selector, timeout=WAIT_TIMEOUT)
            except Exception:
                # 尝试其他可能的选择器
                alternative_selectors = [
                    ".sidebar",
                    "aside.sidebar",
                    "nav.sidebar",
                    ".app-nav",
                    "#sidebar"
                ]
                for selector in alternative_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=5000)
                        sidebar_selector = selector
                        print(f"使用备选选择器: {selector}")
                        break
                    except Exception:
                        continue
            
            # 获取侧边栏HTML
            print("提取侧边栏HTML...")
            sidebar_html = await page.evaluate(f'''
                () => {{
                    const sidebar = document.querySelector("{sidebar_selector}");
                    if (sidebar) {{
                        return sidebar.outerHTML;
                    }}
                    // 如果找不到，尝试获取整个侧边栏区域
                    const aside = document.querySelector("aside");
                    if (aside) {{
                        return aside.outerHTML;
                    }}
                    return null;
                }}
            ''')
            
            if not sidebar_html:
                print("错误：无法找到侧边栏元素")
                # 获取页面完整HTML用于调试
                full_html = await page.content()
                debug_path = output_path.parent / "debug_page.html"
                with open(debug_path, 'w', encoding='utf-8') as f:
                    f.write(full_html)
                print(f"已保存完整页面到 {debug_path} 用于调试")
                return False
            
            # 保存HTML文件
            print(f"保存HTML到: {output_path}")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(sidebar_html)
            
            print(f"成功！共 {len(sidebar_html)} 字节")
            return True
            
        except Exception as e:
            print(f"抓取过程出错: {e}")
            return False
            
        finally:
            await browser.close()
            print("浏览器已关闭")


def run_parse_script(html_path: Path, output_dir: Path):
    """
    运行解析脚本生成Markdown和CSV文件
    """
    import importlib.util
    
    parse_script = html_path.parent / "parse_lx_api_html.py"
    if not parse_script.exists():
        parse_script = output_dir / "scripts" / "parse_lx_api_html.py"
    
    if parse_script.exists():
        print(f"\n运行解析脚本: {parse_script}")
        
        # 动态导入并执行
        spec = importlib.util.spec_from_file_location("parse_lx_api_html", parse_script)
        module = importlib.util.module_from_spec(spec)
        
        # 修改输入路径
        original_main = None
        try:
            spec.loader.exec_module(module)
            
            # 读取HTML
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 解析
            apis = module.parse_html_v2(html_content)
            print(f"解析到 {len(apis)} 个API接口")
            
            # 生成带时间戳的文件名
            timestamp = datetime.now().strftime('%Y%m%d')
            md_path = output_dir / f"领星API接口列表_{timestamp}.md"
            csv_path = output_dir / f"领星API接口列表_{timestamp}.csv"
            
            # 导出
            module.export_to_csv(apis, csv_path)
            module.export_to_markdown(apis, md_path)
            
            print(f"\n生成文件:")
            print(f"  - {md_path}")
            print(f"  - {csv_path}")
            
        except Exception as e:
            print(f"解析脚本执行出错: {e}")
    else:
        print(f"警告：解析脚本不存在: {parse_script}")


async def main():
    """主函数"""
    # 路径配置
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    # 生成带时间戳的文件名
    timestamp = datetime.now().strftime('%Y%m%d')
    
    # 输出路径
    output_html = project_root / "个人文件" / f"lx_api_{timestamp}.html"
    output_dir = script_dir.parent  # output_LLM目录
    
    print("=" * 60)
    print("领星API文档自动抓取工具")
    print("=" * 60)
    print(f"目标URL: {API_DOC_URL}")
    print(f"输出HTML: {output_html}")
    print(f"输出目录: {output_dir}")
    print("=" * 60)
    
    # 抓取HTML
    success = await fetch_sidebar_html(output_html)
    
    if success:
        # 运行解析脚本
        run_parse_script(output_html, output_dir)
        print("\n" + "=" * 60)
        print("任务完成！")
        print("=" * 60)
    else:
        print("\n抓取失败，请检查网络连接或网站是否可访问")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
