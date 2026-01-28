"""
领星API HTML解析脚本
功能：解析HTML导航菜单，输出Markdown表格和CSV文件
"""

import re
import csv
from pathlib import Path
from html.parser import HTMLParser

# API文档基础URL
BASE_URL = "https://apidoc.lingxing.com/#/"


class APIMenuParser(HTMLParser):
    """解析领星API HTML菜单结构"""
    
    def __init__(self):
        super().__init__()
        self.apis = []  # 存储所有API信息
        self.current_level1 = ""  # 一级分类
        self.current_level2 = ""  # 二级分类
        self.in_link = False
        self.current_href = ""
        self.current_text = ""
        self.folder_stack = []  # 文件夹层级栈
        
    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        
        if tag == "li":
            class_attr = attrs_dict.get("class", "")
            if "folder" in class_attr:
                # 进入文件夹层级
                if "level-1" in class_attr or ("folder" in class_attr and "level" not in class_attr):
                    self.folder_stack.append(1)
                elif "level-2" in class_attr:
                    self.folder_stack.append(2)
                    
        elif tag == "a":
            href = attrs_dict.get("href", "")
            # 只处理API链接，排除锚点链接
            if href and href.startswith("#/docs/") and "?id=" not in href:
                self.in_link = True
                self.current_href = href.replace("#/", "")
                self.current_text = ""
                
    def handle_endtag(self, tag):
        if tag == "a" and self.in_link:
            # 保存API信息
            if self.current_text.strip():
                self.apis.append({
                    "level1": self.current_level1,
                    "level2": self.current_level2,
                    "name": self.current_text.strip(),
                    "path": BASE_URL + self.current_href
                })
            self.in_link = False
            self.current_href = ""
            self.current_text = ""
            
        elif tag == "ul":
            # 退出文件夹层级时重置
            if self.folder_stack:
                level = self.folder_stack.pop()
                if level == 2:
                    self.current_level2 = ""
                    
    def handle_data(self, data):
        data = data.strip()
        if not data:
            return
            
        if self.in_link:
            self.current_text += data
        else:
            # 检测文件夹名称
            if self.folder_stack:
                level = self.folder_stack[-1] if self.folder_stack else 0
                if level == 1 and data and not self.in_link:
                    # 一级分类
                    if data not in ["ul", "li", "p"]:
                        self.current_level1 = data
                        self.current_level2 = ""
                elif level == 2 and data and not self.in_link:
                    # 二级分类
                    if data not in ["ul", "li", "p"]:
                        self.current_level2 = data


def parse_html_simple(html_content):
    """使用正则表达式简单解析HTML"""
    apis = []
    
    # 匹配一级分类
    level1_pattern = r'<li class="folder[^"]*level-1[^"]*">(?:<p>)?([^<]+)(?:</p>)?<ul>(.*?)</ul>\s*</li>'
    # 匹配二级分类
    level2_pattern = r'<li class="folder[^"]*level-2[^"]*">(?:<p>)?([^<]+)(?:</p>)?<ul>(.*?)</ul>\s*</li>'
    # 匹配链接
    link_pattern = r'<a href="#/docs/([^"]+)">([^<]+)</a>'
    
    # 提取所有分类结构
    lines = html_content.split('\n')
    
    current_level1 = ""
    current_level2 = ""
    in_level1_folder = False
    in_level2_folder = False
    
    for line in lines:
        line = line.strip()
        
        # 检测一级分类开始
        if 'class="folder level-1"' in line or ('class="folder"' in line and 'level-2' not in line):
            in_level1_folder = True
            in_level2_folder = False
            current_level2 = ""
            
        # 检测二级分类开始    
        if 'class="folder level-2"' in line:
            in_level2_folder = True
            
        # 提取分类名称
        if in_level1_folder and not in_level2_folder:
            # 匹配一级分类名
            m = re.search(r'>([^<>]+)<(?:ul|/li)', line)
            if m:
                name = m.group(1).strip()
                if name and name not in ['ul', 'li']:
                    current_level1 = name
                    current_level2 = ""
                    
        if in_level2_folder:
            # 匹配二级分类名
            m = re.search(r'level-2">([^<]+)<ul', line)
            if m:
                current_level2 = m.group(1).strip()
                
        # 匹配API链接
        link_match = re.search(r'<a href="#/docs/([^"?]+)"[^>]*>([^<]+)</a>', line)
        if link_match:
            path = link_match.group(1)
            name = link_match.group(2).strip()
            if name:
                apis.append({
                    "level1": current_level1,
                    "level2": current_level2,
                    "name": name,
                    "path": BASE_URL + f"docs/{path}"
                })
                
    return apis


def parse_html_v2(html_content):
    """改进版解析：逐行分析结构"""
    apis = []
    
    lines = html_content.split('\n')
    
    level1_stack = []  # 一级分类栈
    level2_stack = []  # 二级分类栈
    current_level1 = ""
    current_level2 = ""
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # 检测一级或无层级文件夹
        if '<li class="folder level-1">' in line or ('<li class="folder">' in line and 'level-' not in line):
            # 提取分类名：可能在同一行或下一行
            name_match = re.search(r'>([^<>]+)<', line)
            if not name_match and i + 1 < len(lines):
                # 检查下一行是否有 <p> 标签
                next_line = lines[i + 1].strip()
                name_match = re.search(r'<p>([^<]+)</p>', next_line)
                if not name_match:
                    name_match = re.search(r'>([^<>]+)<', next_line)
            
            if name_match:
                folder_name = name_match.group(1).strip()
                if folder_name and folder_name not in ['ul', 'li', '']:
                    current_level1 = folder_name
                    current_level2 = ""
                    
        # 检测二级文件夹
        elif '<li class="folder level-2">' in line:
            # 提取分类名
            name_match = re.search(r'level-2">(?:<p>)?([^<]+)', line)
            if not name_match and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                name_match = re.search(r'<p>([^<]+)</p>', next_line)
                if not name_match:
                    name_match = re.search(r'>([^<>]+)<', next_line)
                    
            if name_match:
                folder_name = name_match.group(1).strip()
                if folder_name and folder_name not in ['ul', 'li', '', 'p']:
                    current_level2 = folder_name
                    
        # 匹配API链接
        link_match = re.search(r'<a href="#/docs/([^"?]+)"[^>]*>([^<]+)</a>', line)
        if link_match:
            path = link_match.group(1)
            name = link_match.group(2).strip()
            if name:
                apis.append({
                    "level1": current_level1,
                    "level2": current_level2,
                    "name": name,
                    "path": BASE_URL + f"docs/{path}"
                })
                
        # 检测文件夹结束
        if '</ul>' in line:
            # 可能需要重置层级
            pass
            
        i += 1
        
    return apis


def export_to_csv(apis, output_path):
    """导出为CSV文件"""
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['序号', '一级分类', '二级分类', '接口名称', '接口路径'])
        for idx, api in enumerate(apis, 1):
            writer.writerow([
                idx,
                api['level1'],
                api['level2'],
                api['name'],
                api['path']
            ])
    print(f"CSV文件已生成: {output_path}")


def export_to_markdown(apis, output_path):
    """导出为Markdown表格（使用HTML表格支持合并单元格）"""
    
    # 按一级分类和二级分类分组统计
    groups = {}
    for api in apis:
        key1 = api['level1'] or '其他'
        key2 = api['level2'] or '-'
        if key1 not in groups:
            groups[key1] = {}
        if key2 not in groups[key1]:
            groups[key1][key2] = []
        groups[key1][key2].append(api)
    
    # 生成Markdown内容
    content = """# 领星API接口列表  

> 来源文件: lx_api.html  
> 转换时间: 2026-01-28  
> 接口总数: """ + str(len(apis)) + """  

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
    
    level1_num = 0
    seq = 0
    chinese_nums = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十', 
                    '十一', '十二', '十三', '十四', '十五', '十六', '十七', '十八', '十九', '二十',
                    '二十一', '二十二', '二十三', '二十四', '二十五', '二十六', '二十七', '二十八', '二十九', '三十']
    
    for level1, level2_dict in groups.items():
        level1_num += 1
        level1_cn = chinese_nums[level1_num - 1] if level1_num <= len(chinese_nums) else str(level1_num)
        
        # 计算一级分类的总行数
        level1_total = sum(len(apis_list) for apis_list in level2_dict.values())
        
        first_row_in_level1 = True
        
        for level2, apis_list in level2_dict.items():
            level2_count = len(apis_list)
            first_row_in_level2 = True
            
            for api in apis_list:
                seq += 1
                content += "        <tr>\n"
                
                # 一级分类单元格（合并行）
                if first_row_in_level1:
                    content += f'            <td rowspan="{level1_total}">{level1_cn}</td>\n'
                    content += f'            <td rowspan="{level1_total}">{level1}</td>\n'
                    first_row_in_level1 = False
                
                # 二级分类单元格（合并行）
                if first_row_in_level2:
                    content += f'            <td rowspan="{level2_count}">{level2}</td>\n'
                    first_row_in_level2 = False
                    
                # 序号、接口名称、路径（带超链接）
                content += f'            <td>{seq}</td>\n'
                content += f'            <td>{api["name"]}</td>\n'
                content += f'            <td><a href="{api["path"]}" target="_blank">{api["path"]}</a></td>\n'
                content += "        </tr>\n"
    
    content += """    </tbody>
</table>

---

## 更新记录  

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0 | 2026-01-28 | 初始版本，通过Python脚本从HTML自动解析生成 |
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Markdown文件已生成: {output_path}")


def main():
    """主函数"""
    # 路径配置
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    input_html = project_root / "个人文件" / "lx_api.html"
    output_dir = script_dir.parent
    output_md = output_dir / "领星API接口列表_v1.0.md"
    output_csv = output_dir / "领星API接口列表_v1.0.csv"
    
    print(f"输入文件: {input_html}")
    print(f"输出目录: {output_dir}")
    
    # 读取HTML文件
    with open(input_html, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 解析HTML
    print("正在解析HTML...")
    apis = parse_html_v2(html_content)
    print(f"共解析到 {len(apis)} 个API接口")
    
    # 导出文件
    export_to_csv(apis, output_csv)
    export_to_markdown(apis, output_md)
    
    print("\n完成!")


if __name__ == "__main__":
    main()
