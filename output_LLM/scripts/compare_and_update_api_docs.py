# -*- coding: utf-8 -*-
"""
领星API接口文档差异比对和版本更新脚本

功能：
1. 比对每日脚本生成的文档和正式文档的差异
2. 智能识别新增、删除、修改的API接口
3. 自动创建新版本并生成详细的更新记录
4. 移动旧版本到过期文件夹

使用方法：
    python compare_and_update_api_docs.py
    
作者：Antigravity
创建时间：2026-01-28
更新时间：2026-01-28 - 增加API接口级别的差异识别
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path
import difflib
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ApiInfo:
    """API接口信息"""
    seq: str           # 序号
    name: str          # 接口名称
    path: str          # 接口路径
    category1: str     # 一级分类
    category2: str     # 二级分类
    
    def __hash__(self):
        # 使用接口路径作为唯一标识
        return hash(self.path)
    
    def __eq__(self, other):
        if isinstance(other, ApiInfo):
            return self.path == other.path
        return False


class ApiContentParser:
    """API接口内容解析器"""
    
    @staticmethod
    def parse_apis_from_markdown(content: str) -> Dict[str, ApiInfo]:
        """
        从Markdown内容中解析API接口信息
        
        Args:
            content: Markdown文件内容
            
        Returns:
            以接口路径为key的API信息字典
        """
        apis = {}
        
        # 匹配表格中的每一行数据
        # 格式: <td>序号</td> <td>接口名称</td> <td><a href="路径">路径</a></td>
        
        # 首先找出所有的分类信息（通过 rowspan 标识）
        current_cat1 = ""
        current_cat2 = ""
        
        # 使用正则提取每个表格行
        row_pattern = re.compile(r'<tr>(.*?)</tr>', re.DOTALL)
        
        for row_match in row_pattern.finditer(content):
            row_content = row_match.group(1)
            
            # 提取所有 td 内容
            td_pattern = re.compile(r'<td[^>]*>(.*?)</td>', re.DOTALL)
            tds = td_pattern.findall(row_content)
            
            if not tds:
                continue
            
            # 解析行内容
            # 行可能有以下几种格式:
            # 1. 完整行: 编号, 一级分类, 二级分类, 序号, 接口名称, 接口路径
            # 2. 部分行（分类已合并）: 序号, 接口名称, 接口路径
            # 3. 部分行（只有二级分类）: 二级分类, 序号, 接口名称, 接口路径
            
            # 检查是否包含链接（接口路径指示器）
            link_pattern = re.compile(r'<a[^>]*href="([^"]+)"[^>]*>.*?</a>')
            
            has_link = any(link_pattern.search(td) for td in tds)
            
            if not has_link:
                # 不包含链接的行，可能是包含分类信息的行头
                # 检查是否有 rowspan（分类标识）
                for td in tds:
                    td_clean = td.strip()
                    # 跳过编号列（中文数字）
                    if re.match(r'^[一二三四五六七八九十]+$', td_clean):
                        continue
                    # 跳过序号列（阿拉伯数字）
                    if re.match(r'^\d+$', td_clean):
                        continue
                    # 跳过"-"
                    if td_clean == '-':
                        continue
                continue
            
            # 包含链接的行，解析API信息
            # 从后向前解析：最后一个是路径，倒数第二个是名称，倒数第三个是序号
            
            # 提取路径
            path = ""
            for td in reversed(tds):
                link_match = link_pattern.search(td)
                if link_match:
                    path = link_match.group(1)
                    break
            
            if not path:
                continue
            
            # 找到路径所在的 td 索引
            path_idx = -1
            for i, td in enumerate(tds):
                if link_pattern.search(td):
                    path_idx = i
                    break
            
            if path_idx < 2:
                continue
            
            # 序号和名称
            name = tds[path_idx - 1].strip()
            seq = tds[path_idx - 2].strip()
            
            # 提取分类信息（从行首的 td 开始）
            cat1 = ""
            cat2 = ""
            
            for i, td in enumerate(tds):
                if i >= path_idx - 2:
                    break
                td_clean = td.strip()
                # 跳过编号列（中文数字）
                if re.match(r'^[一二三四五六七八九十]+$', td_clean):
                    continue
                # 跳过"-"
                if td_clean == '-':
                    continue
                # 这应该是分类信息
                if not cat1:
                    cat1 = td_clean
                elif not cat2:
                    cat2 = td_clean
            
            # 如果没有解析到分类，使用上一行的分类
            if cat1:
                current_cat1 = cat1
            else:
                cat1 = current_cat1
            
            if cat2:
                current_cat2 = cat2
            else:
                cat2 = current_cat2
            
            # 创建 API 信息对象
            api = ApiInfo(
                seq=seq,
                name=name,
                path=path,
                category1=cat1,
                category2=cat2
            )
            
            apis[path] = api
        
        return apis
    
    @staticmethod
    def compare_apis(old_apis: Dict[str, ApiInfo], new_apis: Dict[str, ApiInfo]) -> dict:
        """
        比较两个API列表的差异
        
        Args:
            old_apis: 旧版本的API列表
            new_apis: 新版本的API列表
            
        Returns:
            差异信息字典
        """
        old_paths = set(old_apis.keys())
        new_paths = set(new_apis.keys())
        
        # 新增的接口
        added_paths = new_paths - old_paths
        added_apis = [new_apis[p] for p in added_paths]
        
        # 删除的接口
        removed_paths = old_paths - new_paths
        removed_apis = [old_apis[p] for p in removed_paths]
        
        # 修改的接口（路径相同但名称不同）
        common_paths = old_paths & new_paths
        modified_apis = []
        for path in common_paths:
            old_api = old_apis[path]
            new_api = new_apis[path]
            if old_api.name != new_api.name:
                modified_apis.append({
                    'old': old_api,
                    'new': new_api
                })
        
        return {
            'added': added_apis,
            'removed': removed_apis,
            'modified': modified_apis,
            'old_count': len(old_apis),
            'new_count': len(new_apis)
        }


class ApiDocVersionManager:
    """API文档版本管理器"""
    
    def __init__(self, output_dir: str):
        """
        初始化版本管理器
        
        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = Path(output_dir)
        self.expired_dir = self.output_dir / "过期文件"
        self.parser = ApiContentParser()
        
        # 确保过期文件夹存在
        self.expired_dir.mkdir(exist_ok=True)
    
    def extract_version(self, filename: str) -> tuple:
        """
        从文件名中提取版本号
        
        Args:
            filename: 文件名
            
        Returns:
            (major, minor) 版本号元组，如果没有版本号返回 (0, 0)
        """
        match = re.search(r'_v(\d+)\.(\d+)', filename)
        if match:
            return (int(match.group(1)), int(match.group(2)))
        return (0, 0)
    
    def increment_version(self, version: tuple, is_major: bool = False) -> tuple:
        """
        增加版本号
        
        Args:
            version: 当前版本号 (major, minor)
            is_major: 是否增加大版本号
            
        Returns:
            新版本号元组
        """
        major, minor = version
        if is_major:
            return (major + 1, 0)
        else:
            return (major, minor + 1)
    
    def normalize_content(self, content: str) -> str:
        """
        标准化内容用于比较（忽略转换时间等元数据）
        
        Args:
            content: 文件内容
            
        Returns:
            标准化后的内容
        """
        lines = content.split('\n')
        normalized_lines = []
        
        for line in lines:
            # 忽略转换时间行
            if line.strip().startswith('> 转换时间:'):
                continue
            # 忽略空白差异
            normalized_lines.append(line.rstrip())
        
        return '\n'.join(normalized_lines)
    
    def compare_files(self, daily_file: Path, official_file: Path) -> dict:
        """
        比对两个文件的差异
        
        Args:
            daily_file: 每日脚本生成的文件路径
            official_file: 正式文档路径
            
        Returns:
            差异信息字典
        """
        result = {
            'has_diff': False,
            'daily_exists': daily_file.exists(),
            'official_exists': official_file.exists(),
            'diff_lines': [],
            'diff_summary': '',
            'api_diff': None
        }
        
        if not result['daily_exists']:
            result['diff_summary'] = f"每日文件不存在: {daily_file}"
            return result
        
        # 读取每日文件内容
        with open(daily_file, 'r', encoding='utf-8') as f:
            daily_content = f.read()
        
        if not result['official_exists']:
            result['has_diff'] = True
            # 解析新文件的API
            new_apis = self.parser.parse_apis_from_markdown(daily_content)
            result['api_diff'] = {
                'added': list(new_apis.values()),
                'removed': [],
                'modified': [],
                'old_count': 0,
                'new_count': len(new_apis)
            }
            result['diff_summary'] = f"正式文档不存在，将创建新版本（包含 {len(new_apis)} 个接口）"
            return result
        
        # 读取正式文档内容
        with open(official_file, 'r', encoding='utf-8') as f:
            official_content = f.read()
        
        # 标准化后比较
        daily_normalized = self.normalize_content(daily_content)
        official_normalized = self.normalize_content(official_content)
        
        if daily_normalized == official_normalized:
            result['diff_summary'] = "文件内容相同，无需更新"
            return result
        
        # 有差异，解析API级别的差异
        result['has_diff'] = True
        
        # 解析两个文件的API列表
        old_apis = self.parser.parse_apis_from_markdown(official_content)
        new_apis = self.parser.parse_apis_from_markdown(daily_content)
        
        # 比较API差异
        api_diff = self.parser.compare_apis(old_apis, new_apis)
        result['api_diff'] = api_diff
        
        # 生成差异摘要
        summaries = []
        if api_diff['added']:
            summaries.append(f"新增 {len(api_diff['added'])} 个接口")
        if api_diff['removed']:
            summaries.append(f"删除 {len(api_diff['removed'])} 个接口")
        if api_diff['modified']:
            summaries.append(f"修改 {len(api_diff['modified'])} 个接口")
        
        if summaries:
            result['diff_summary'] = '，'.join(summaries)
        else:
            # 如果没有API级别的差异但文件内容不同，可能是格式变化
            result['diff_summary'] = "文档格式或其他内容有变化"
        
        return result
    
    def determine_version_type(self, diff_result: dict) -> bool:
        """
        根据差异大小判断是否为大版本更新
        
        Args:
            diff_result: 差异比较结果
            
        Returns:
            True 表示大版本更新，False 表示小版本更新
        """
        api_diff = diff_result.get('api_diff')
        if not api_diff:
            return False
        
        # 如果新增或删除超过10个接口，认为是大版本更新
        total_changes = len(api_diff['added']) + len(api_diff['removed'])
        return total_changes > 10
    
    def generate_detailed_update_note(self, api_diff: dict) -> str:
        """
        生成详细的更新说明（用于表格的说明列）
        
        Args:
            api_diff: API差异信息
            
        Returns:
            详细的更新说明文本（适合放在表格单元格中）
        """
        parts = []
        
        # 新增接口
        if api_diff['added']:
            added_names = [api.name for api in api_diff['added'][:5]]
            if len(api_diff['added']) > 5:
                added_str = f"新增{len(api_diff['added'])}个接口: {', '.join(added_names)}等"
            else:
                added_str = f"新增{len(api_diff['added'])}个接口: {', '.join(added_names)}"
            parts.append(added_str)
        
        # 删除接口
        if api_diff['removed']:
            removed_names = [api.name for api in api_diff['removed'][:5]]
            if len(api_diff['removed']) > 5:
                removed_str = f"删除{len(api_diff['removed'])}个接口: {', '.join(removed_names)}等"
            else:
                removed_str = f"删除{len(api_diff['removed'])}个接口: {', '.join(removed_names)}"
            parts.append(removed_str)
        
        # 修改接口
        if api_diff['modified']:
            modified_items = [f"{mod['old'].name}→{mod['new'].name}" for mod in api_diff['modified'][:3]]
            if len(api_diff['modified']) > 3:
                modified_str = f"修改{len(api_diff['modified'])}个接口名称: {', '.join(modified_items)}等"
            else:
                modified_str = f"修改{len(api_diff['modified'])}个接口名称: {', '.join(modified_items)}"
            parts.append(modified_str)
        
        # 接口总数变化
        if api_diff['old_count'] != api_diff['new_count']:
            parts.append(f"接口总数{api_diff['old_count']}→{api_diff['new_count']}")
        
        if parts:
            return '; '.join(parts)
        else:
            return "文档格式或其他内容更新"
    
    def create_new_version(self, daily_file: Path, official_file: Path, 
                           new_version: tuple, update_note: str, 
                           detailed_note: str = None) -> Path:
        """
        创建新版本文件
        
        Args:
            daily_file: 每日脚本生成的文件路径
            official_file: 原正式文档路径
            new_version: 新版本号
            update_note: 更新说明（简短版，备用）
            detailed_note: 详细更新说明
            
        Returns:
            新文件路径
        """
        # 构建新文件名
        base_name = re.sub(r'_v\d+\.\d+', '', official_file.stem)
        # 移除日期后缀（如 _20260128）
        base_name = re.sub(r'_\d{8}$', '', base_name)
        new_filename = f"{base_name}_v{new_version[0]}.{new_version[1]}{official_file.suffix}"
        new_file = self.output_dir / new_filename
        
        # 读取每日文件内容
        with open(daily_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 生成更新记录行（用于表格）
        today = datetime.now().strftime('%Y-%m-%d')
        version_str = f"v{new_version[0]}.{new_version[1]}"
        
        # 使用详细说明或简短说明
        description = detailed_note if detailed_note else update_note
        
        # 构建新的表格行
        new_table_row = f"| {version_str} | {today} | {description} |"
        
        # 查找并更新更新记录表格
        # 表格格式: | 版本 | 日期 | 说明 |
        #          |------|------|------|
        #          | v1.0 | 2026-01-28 | ... |
        
        # 使用正则匹配表格头部，在表格头部后面插入新行
        # 匹配模式: | 版本 | 日期 | 说明 |\n|---...---|\n
        table_header_pattern = re.compile(
            r'(\|\s*版本\s*\|\s*日期\s*\|\s*说明\s*\|\s*\n\s*\|[-\s|]+\|\s*\n)',
            re.IGNORECASE
        )
        
        match = table_header_pattern.search(content)
        if match:
            # 在表格头部后面插入新行
            insert_pos = match.end()
            content = content[:insert_pos] + new_table_row + "\n" + content[insert_pos:]
        else:
            # 如果没有找到更新记录表格，创建一个新的
            update_section = f"""

---

## 更新记录

| 版本 | 日期 | 说明 |
|------|------|------|
{new_table_row}
"""
            # 检查是否已有更新记录部分
            if '## 更新记录' in content:
                # 在更新记录部分后添加表格
                content = re.sub(
                    r'(## 更新记录\s*\n)',
                    f'\\1\n| 版本 | 日期 | 说明 |\n|------|------|------|\n{new_table_row}\n',
                    content
                )
            else:
                content += update_section
        
        # 写入新文件
        with open(new_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return new_file
    
    def archive_old_version(self, old_file: Path) -> Path:
        """
        将旧版本移动到过期文件夹
        
        Args:
            old_file: 旧版本文件路径
            
        Returns:
            移动后的文件路径
        """
        if not old_file.exists():
            return None
        
        archived_file = self.expired_dir / old_file.name
        
        # 如果目标已存在，添加时间戳避免覆盖
        if archived_file.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archived_file = self.expired_dir / f"{old_file.stem}_{timestamp}{old_file.suffix}"
        
        shutil.move(str(old_file), str(archived_file))
        return archived_file
    
    def process_update(self, daily_pattern: str, official_pattern: str) -> dict:
        """
        处理文档更新的主流程
        
        Args:
            daily_pattern: 每日文件名模式（如 "领星API接口列表_20260128"）
            official_pattern: 正式文档名模式（如 "领星API接口列表"）
            
        Returns:
            处理结果
        """
        result = {
            'status': 'unknown',
            'message': '',
            'actions': []
        }
        
        # 查找文件
        daily_file = None
        official_file = None
        
        for f in self.output_dir.iterdir():
            if f.is_file() and f.suffix == '.md':
                if daily_pattern in f.name and '_v' not in f.name:
                    daily_file = f
                elif official_pattern in f.name and '_v' in f.name:
                    if official_file is None or self.extract_version(f.name) > self.extract_version(official_file.name):
                        official_file = f
        
        if daily_file is None:
            result['status'] = 'error'
            result['message'] = f"未找到每日文件: {daily_pattern}"
            return result
        
        print(f"  每日文件: {daily_file.name}")
        print(f"  正式文档: {official_file.name if official_file else '不存在'}")
        
        # 比对差异
        diff_result = self.compare_files(daily_file, official_file or Path(""))
        print(f"  比对结果: {diff_result['diff_summary']}")
        
        if not diff_result['has_diff']:
            result['status'] = 'no_change'
            result['message'] = '文件内容相同，无需更新'
            return result
        
        # 打印详细的差异信息
        api_diff = diff_result.get('api_diff')
        if api_diff:
            print()
            print("  详细变更:")
            if api_diff['added']:
                print(f"    [+] 新增 {len(api_diff['added'])} 个接口:")
                for api in api_diff['added'][:5]:
                    print(f"        - {api.name}")
                if len(api_diff['added']) > 5:
                    print(f"        ... 等共 {len(api_diff['added'])} 个")
            
            if api_diff['removed']:
                print(f"    [-] 删除 {len(api_diff['removed'])} 个接口:")
                for api in api_diff['removed'][:5]:
                    print(f"        - {api.name}")
                if len(api_diff['removed']) > 5:
                    print(f"        ... 等共 {len(api_diff['removed'])} 个")
            
            if api_diff['modified']:
                print(f"    [~] 修改 {len(api_diff['modified'])} 个接口:")
                for mod in api_diff['modified'][:5]:
                    print(f"        - {mod['old'].name} → {mod['new'].name}")
            
            print()
        
        # 确定版本号
        if official_file:
            current_version = self.extract_version(official_file.name)
        else:
            current_version = (0, 0)
        
        is_major = self.determine_version_type(diff_result)
        new_version = self.increment_version(current_version, is_major)
        
        version_type = "大版本" if is_major else "小版本"
        print(f"  版本更新: v{current_version[0]}.{current_version[1]} -> v{new_version[0]}.{new_version[1]} ({version_type}更新)")
        
        # 生成详细更新说明
        detailed_note = None
        if api_diff:
            detailed_note = self.generate_detailed_update_note(api_diff)
        
        # 创建新版本
        new_file = self.create_new_version(
            daily_file, 
            official_file or daily_file, 
            new_version, 
            diff_result['diff_summary'],
            detailed_note
        )
        result['actions'].append(f"创建新版本: {new_file.name}")
        print(f"  创建新版本: {new_file.name}")
        
        # 归档旧版本
        if official_file and official_file.exists():
            archived = self.archive_old_version(official_file)
            if archived:
                result['actions'].append(f"归档旧版本: {official_file.name} -> 过期文件/{archived.name}")
                print(f"  归档旧版本: {official_file.name} -> 过期文件/{archived.name}")
        
        result['status'] = 'updated'
        result['message'] = f"已更新到 v{new_version[0]}.{new_version[1]}"
        
        return result


def main():
    """主函数"""
    print("=" * 60)
    print("领星API接口文档差异比对和版本更新工具 v2.0")
    print("=" * 60)
    print()
    
    # 设置目录
    output_dir = Path(__file__).parent.parent  # output_LLM 目录
    
    print(f"工作目录: {output_dir}")
    print()
    
    # 创建版本管理器
    manager = ApiDocVersionManager(str(output_dir))
    
    # 处理 Markdown 文档
    print("[1] 处理 Markdown 文档")
    print("-" * 40)
    
    # 获取今天的日期
    today = datetime.now().strftime('%Y%m%d')
    daily_pattern = f"领星API接口列表_{today}"
    official_pattern = "领星API接口列表"
    
    result = manager.process_update(daily_pattern, official_pattern)
    
    print()
    print(f"处理结果: {result['status']}")
    print(f"信息: {result['message']}")
    
    if result['actions']:
        print("操作记录:")
        for action in result['actions']:
            print(f"  - {action}")
    
    print()
    print("=" * 60)
    print("处理完成")
    print("=" * 60)


if __name__ == '__main__':
    main()
