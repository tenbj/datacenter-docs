# -*- coding: utf-8 -*-
"""
02_parse_to_md.py - 解析HTML生成Markdown文档

功能：
读取HTML文件，解析API接口信息，
生成带有分类合并单元格的Markdown表格。

使用方法：
    python 02_parse_to_md.py --input-file ../html/lx_api_20260128.html
    python 02_parse_to_md.py --input-file ../html/lx_api_20260128.html --output-dir ../md/

作者：Antigravity
创建时间：2026-01-28
"""

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class ApiInfo:
    """API接口信息"""
    category1: str      # 一级分类
    category2: str      # 二级分类
    name: str           # 接口名称
    path: str           # 接口路径


def parse_html_to_apis(html_content: str, source_file: str) -> List[ApiInfo]:
    """
    解析HTML内容，提取API接口信息
    适配嵌套的 ul/li 结构（领星API文档格式）
    
    Args:
        html_content: HTML内容
        source_file: 源文件名（用于日志）
        
    Returns:
        API接口列表
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    apis = []
    
    def extract_apis_from_list(ul_element, category1: str = "", category2: str = ""):
        """递归提取API接口"""
        if ul_element is None:
            return
        
        for li in ul_element.find_all('li', recursive=False):
            # 检查是否是文件夹（分类）
            is_folder = 'folder' in li.get('class', [])
            is_level1 = 'level-1' in li.get('class', [])
            is_level2 = 'level-2' in li.get('class', [])
            
            # 获取分类名称（可能在直接文本、p标签或作为第一个文本节点）
            folder_name = ""
            if is_folder or is_level1 or is_level2:
                # 查找分类名称
                p_tag = li.find('p', recursive=False)
                if p_tag:
                    folder_name = p_tag.get_text(strip=True)
                else:
                    # 获取li的直接文本内容（排除子元素）
                    for content in li.children:
                        if isinstance(content, str):
                            text = content.strip()
                            if text:
                                folder_name = text
                                break
                        elif content.name != 'ul' and content.name != 'a':
                            text = content.get_text(strip=True)
                            if text:
                                folder_name = text
                                break
            
            # 确定新的分类层级
            new_cat1 = category1
            new_cat2 = category2
            
            if is_level1 or (is_folder and not category1):
                new_cat1 = folder_name if folder_name else category1
                new_cat2 = "-"  # 重置二级分类
            elif is_level2 or (is_folder and category1):
                new_cat2 = folder_name if folder_name else category2
            
            # 查找直接的链接（接口）
            is_file = 'file' in li.get('class', [])
            if is_file:
                link = li.find('a', recursive=False)
                if link:
                    href = link.get('href', '')
                    name = link.get_text(strip=True)
                    
                    if name and href:
                        # 构建完整路径
                        if href.startswith('#'):
                            full_path = f"https://apidoc.lingxing.com/{href}"
                        elif href.startswith('/'):
                            full_path = f"https://apidoc.lingxing.com{href}"
                        elif not href.startswith('http'):
                            full_path = f"https://apidoc.lingxing.com/#/{href}"
                        else:
                            full_path = href
                        
                        # 如果没有一级分类，使用默认值
                        cat1 = new_cat1 if new_cat1 else "其他"
                        cat2 = new_cat2 if new_cat2 else "-"
                        
                        api = ApiInfo(
                            category1=cat1,
                            category2=cat2,
                            name=name,
                            path=full_path
                        )
                        apis.append(api)
            
            # 递归处理子列表
            sub_ul = li.find('ul', recursive=False)
            if sub_ul:
                extract_apis_from_list(sub_ul, new_cat1, new_cat2)
    
    # 查找所有顶级ul
    for ul in soup.find_all('ul', recursive=False):
        extract_apis_from_list(ul, "", "")
    
    # 如果没找到，尝试从div内查找
    if not apis:
        div = soup.find('div', class_='sidebar-nav')
        if div:
            for ul in div.find_all('ul', recursive=False):
                extract_apis_from_list(ul, "", "")
    
    print(f"共解析到 {len(apis)} 个接口")
    return apis


def generate_markdown(apis: List[ApiInfo], source_file: str) -> str:
    """
    生成Markdown内容
    
    Args:
        apis: API接口列表
        source_file: 源文件名
        
    Returns:
        Markdown内容
    """
    today = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 文件头
    md_content = f"""# 领星API接口列表  

> 来源文件: {source_file}  
> 转换时间: {today}  
> 接口总数: {len(apis)}  

---

<table>
    <thead>
        <tr>
            <th>编号</th>
            <th>一级分类</th>
            <th>二级分类</th>
            <th>序号</th>
            <th>接口名称</th>
            <th>接口路径</th>
        </tr>
    </thead>
    <tbody>
"""
    
    # 按一级分类分组
    categories: Dict[str, List[ApiInfo]] = {}
    for api in apis:
        if api.category1 not in categories:
            categories[api.category1] = []
        categories[api.category1].append(api)
    
    # 中文数字映射
    cn_numbers = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
                  '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八',
                  '十九', '二十', '二十一', '二十二', '二十三', '二十四', '二十五']
    
    seq = 0
    cat_idx = 0
    
    for cat1, cat_apis in categories.items():
        cat_count = len(cat_apis)
        cn_num = cn_numbers[cat_idx] if cat_idx < len(cn_numbers) else str(cat_idx + 1)
        
        # 按二级分类分组
        sub_categories: Dict[str, List[ApiInfo]] = {}
        for api in cat_apis:
            if api.category2 not in sub_categories:
                sub_categories[api.category2] = []
            sub_categories[api.category2].append(api)
        
        first_in_cat1 = True
        
        for cat2, sub_apis in sub_categories.items():
            sub_count = len(sub_apis)
            first_in_cat2 = True
            
            for api in sub_apis:
                seq += 1
                
                row = "        <tr>\n"
                
                # 编号列（一级分类合并）
                if first_in_cat1:
                    row += f'            <td rowspan="{cat_count}">{cn_num}</td>\n'
                    row += f'            <td rowspan="{cat_count}">{cat1}</td>\n'
                    first_in_cat1 = False
                
                # 二级分类列
                if first_in_cat2:
                    row += f'            <td rowspan="{sub_count}">{cat2}</td>\n'
                    first_in_cat2 = False
                
                # 序号、名称、路径
                row += f'            <td>{seq}</td>\n'
                row += f'            <td>{api.name}</td>\n'
                row += f'            <td><a href="{api.path}" target="_blank">{api.path}</a></td>\n'
                row += "        </tr>\n"
                
                md_content += row
        
        cat_idx += 1
    
    md_content += """    </tbody>
</table>

---

## 更新记录  

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | """ + datetime.now().strftime('%Y-%m-%d') + """ | 初始版本，通过Python脚本从HTML自动解析生成 |
"""
    
    return md_content


def parse_html_to_markdown(input_file: Path, output_dir: Path, output_file: str = None) -> Path:
    """
    主解析函数
    
    Args:
        input_file: 输入HTML文件路径
        output_dir: 输出目录
        output_file: 输出文件名（可选）
        
    Returns:
        输出文件路径
    """
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 读取HTML文件
    print(f"读取文件: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 解析API
    apis = parse_html_to_apis(html_content, input_file.name)
    
    if not apis:
        print("警告: 未解析到任何API接口")
    
    # 生成Markdown
    md_content = generate_markdown(apis, input_file.name)
    
    # 生成输出文件名
    if output_file:
        output_path = output_dir / output_file
    else:
        # 从输入文件名提取日期
        date_match = re.search(r'(\d{8})', input_file.name)
        if date_match:
            date_str = date_match.group(1)
        else:
            date_str = datetime.now().strftime('%Y%m%d')
        output_path = output_dir / f"领星API接口列表_{date_str}.md"
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"Markdown文件已保存到: {output_path}")
    print(f"文件大小: {output_path.stat().st_size / 1024:.2f} KB")
    
    return output_path


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='解析HTML生成Markdown文档',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--input-file',
        type=str,
        required=True,
        help='输入HTML文件路径（必须）'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='../md/',
        help='MD输出目录（默认: ../md/）'
    )
    
    parser.add_argument(
        '--output-file',
        type=str,
        default=None,
        help='输出文件名（可选）'
    )
    
    args = parser.parse_args()
    
    # 处理路径
    script_dir = Path(__file__).parent
    
    input_file = Path(args.input_file)
    if not input_file.is_absolute():
        input_file = script_dir / input_file
    
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = script_dir / output_dir
    
    # 检查输入文件
    if not input_file.exists():
        print(f"错误: 输入文件不存在: {input_file}")
        return 1
    
    print("=" * 50)
    print("HTML转Markdown工具")
    print("=" * 50)
    
    try:
        output_path = parse_html_to_markdown(input_file, output_dir, args.output_file)
        print("\n转换完成!")
        return 0
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
