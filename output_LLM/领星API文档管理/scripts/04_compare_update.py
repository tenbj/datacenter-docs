# -*- coding: utf-8 -*-
"""
04_compare_update.py - 比对差异并更新版本

功能：
比对每日MD和正式文档的差异，识别新增/删除/修改的接口，
自动更新版本号并添加更新记录到表格中。

使用方法：
    python 04_compare_update.py --daily-file ../md/领星API接口列表_20260128.md
    python 04_compare_update.py --daily-file ../md/领星API接口列表_20260128.md --official-dir ../

作者：Antigravity
创建时间：2026-01-28
"""

import argparse
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
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
        return hash(self.path)
    
    def __eq__(self, other):
        if isinstance(other, ApiInfo):
            return self.path == other.path
        return False


class ApiContentParser:
    """API接口内容解析器"""
    
    @staticmethod
    def parse_apis_from_markdown(content: str) -> Dict[str, ApiInfo]:
        """从Markdown内容中解析API接口信息"""
        apis = {}
        current_cat1 = ""
        current_cat2 = ""
        
        row_pattern = re.compile(r'<tr>(.*?)</tr>', re.DOTALL)
        
        for row_match in row_pattern.finditer(content):
            row_content = row_match.group(1)
            
            td_pattern = re.compile(r'<td[^>]*>(.*?)</td>', re.DOTALL)
            tds = td_pattern.findall(row_content)
            
            if not tds:
                continue
            
            link_pattern = re.compile(r'<a[^>]*href="([^"]+)"[^>]*>.*?</a>')
            has_link = any(link_pattern.search(td) for td in tds)
            
            if not has_link:
                continue
            
            # 提取路径
            path = ""
            for td in reversed(tds):
                link_match = link_pattern.search(td)
                if link_match:
                    path = link_match.group(1)
                    break
            
            if not path:
                continue
            
            path_idx = -1
            for i, td in enumerate(tds):
                if link_pattern.search(td):
                    path_idx = i
                    break
            
            if path_idx < 2:
                continue
            
            name = tds[path_idx - 1].strip()
            seq = tds[path_idx - 2].strip()
            
            cat1 = ""
            cat2 = ""
            
            for i, td in enumerate(tds):
                if i >= path_idx - 2:
                    break
                td_clean = td.strip()
                if re.match(r'^[一二三四五六七八九十]+$', td_clean):
                    continue
                if td_clean == '-':
                    continue
                if not cat1:
                    cat1 = td_clean
                elif not cat2:
                    cat2 = td_clean
            
            if cat1:
                current_cat1 = cat1
            else:
                cat1 = current_cat1
            
            if cat2:
                current_cat2 = cat2
            else:
                cat2 = current_cat2
            
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
        """比较两个API列表的差异"""
        old_paths = set(old_apis.keys())
        new_paths = set(new_apis.keys())
        
        added_paths = new_paths - old_paths
        added_apis = [new_apis[p] for p in added_paths]
        
        removed_paths = old_paths - new_paths
        removed_apis = [old_apis[p] for p in removed_paths]
        
        common_paths = old_paths & new_paths
        modified_apis = []
        for path in common_paths:
            old_api = old_apis[path]
            new_api = new_apis[path]
            if old_api.name != new_api.name:
                modified_apis.append({'old': old_api, 'new': new_api})
        
        return {
            'added': added_apis,
            'removed': removed_apis,
            'modified': modified_apis,
            'old_count': len(old_apis),
            'new_count': len(new_apis)
        }


class ApiDocVersionManager:
    """API文档版本管理器"""
    
    def __init__(self, official_dir: Path, archive_dir: Path):
        self.official_dir = official_dir
        self.archive_dir = archive_dir
        self.parser = ApiContentParser()
        
        self.archive_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_version(self, filename: str) -> tuple:
        """从文件名中提取版本号"""
        match = re.search(r'_v(\d+)\.(\d+)', filename)
        if match:
            return (int(match.group(1)), int(match.group(2)))
        return (0, 0)
    
    def increment_version(self, version: tuple, is_major: bool = False) -> tuple:
        """增加版本号"""
        major, minor = version
        if is_major:
            return (major + 1, 0)
        else:
            return (major, minor + 1)
    
    def normalize_content(self, content: str) -> str:
        """标准化内容用于比较"""
        lines = content.split('\n')
        normalized_lines = []
        
        for line in lines:
            if line.strip().startswith('> 转换时间:'):
                continue
            normalized_lines.append(line.rstrip())
        
        return '\n'.join(normalized_lines)
    
    def find_official_file(self) -> Optional[Path]:
        """查找最新版本的正式文档"""
        official_file = None
        
        for f in self.official_dir.iterdir():
            if f.is_file() and f.suffix == '.md' and '_v' in f.name:
                if '领星API接口列表' in f.name:
                    if official_file is None or self.extract_version(f.name) > self.extract_version(official_file.name):
                        official_file = f
        
        return official_file
    
    def compare_files(self, daily_file: Path, official_file: Optional[Path]) -> dict:
        """比对两个文件的差异"""
        result = {
            'has_diff': False,
            'daily_exists': daily_file.exists(),
            'official_exists': official_file.exists() if official_file else False,
            'diff_summary': '',
            'api_diff': None
        }
        
        if not result['daily_exists']:
            result['diff_summary'] = f"每日文件不存在: {daily_file}"
            return result
        
        with open(daily_file, 'r', encoding='utf-8') as f:
            daily_content = f.read()
        
        if not result['official_exists']:
            result['has_diff'] = True
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
        
        with open(official_file, 'r', encoding='utf-8') as f:
            official_content = f.read()
        
        daily_normalized = self.normalize_content(daily_content)
        official_normalized = self.normalize_content(official_content)
        
        if daily_normalized == official_normalized:
            result['diff_summary'] = "文件内容相同，无需更新"
            return result
        
        result['has_diff'] = True
        
        old_apis = self.parser.parse_apis_from_markdown(official_content)
        new_apis = self.parser.parse_apis_from_markdown(daily_content)
        
        api_diff = self.parser.compare_apis(old_apis, new_apis)
        result['api_diff'] = api_diff
        
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
            result['diff_summary'] = "文档格式或其他内容有变化"
        
        return result
    
    def determine_version_type(self, diff_result: dict) -> bool:
        """判断是否为大版本更新"""
        api_diff = diff_result.get('api_diff')
        if not api_diff:
            return False
        
        total_changes = len(api_diff['added']) + len(api_diff['removed'])
        return total_changes > 10
    
    def generate_update_note(self, api_diff: dict) -> str:
        """生成更新说明"""
        parts = []
        
        if api_diff['added']:
            added_names = [api.name for api in api_diff['added'][:5]]
            if len(api_diff['added']) > 5:
                added_str = f"新增{len(api_diff['added'])}个接口: {', '.join(added_names)}等"
            else:
                added_str = f"新增{len(api_diff['added'])}个接口: {', '.join(added_names)}"
            parts.append(added_str)
        
        if api_diff['removed']:
            removed_names = [api.name for api in api_diff['removed'][:5]]
            if len(api_diff['removed']) > 5:
                removed_str = f"删除{len(api_diff['removed'])}个接口: {', '.join(removed_names)}等"
            else:
                removed_str = f"删除{len(api_diff['removed'])}个接口: {', '.join(removed_names)}"
            parts.append(removed_str)
        
        if api_diff['modified']:
            modified_items = [f"{mod['old'].name}→{mod['new'].name}" for mod in api_diff['modified'][:3]]
            if len(api_diff['modified']) > 3:
                modified_str = f"修改{len(api_diff['modified'])}个接口名称: {', '.join(modified_items)}等"
            else:
                modified_str = f"修改{len(api_diff['modified'])}个接口名称: {', '.join(modified_items)}"
            parts.append(modified_str)
        
        if api_diff['old_count'] != api_diff['new_count']:
            parts.append(f"接口总数{api_diff['old_count']}→{api_diff['new_count']}")
        
        return '; '.join(parts) if parts else "文档格式或其他内容更新"
    
    def create_new_version(self, daily_file: Path, new_version: tuple, update_note: str) -> Path:
        """创建新版本文件"""
        new_filename = f"领星API接口列表_v{new_version[0]}.{new_version[1]}.md"
        new_file = self.official_dir / new_filename
        
        with open(daily_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        today = datetime.now().strftime('%Y-%m-%d')
        version_str = f"v{new_version[0]}.{new_version[1]}"
        new_table_row = f"| {version_str} | {today} | {update_note} |"
        
        table_header_pattern = re.compile(
            r'(\|\s*版本\s*\|\s*日期\s*\|\s*说明\s*\|\s*\n\s*\|[-\s|]+\|\s*\n)',
            re.IGNORECASE
        )
        
        match = table_header_pattern.search(content)
        if match:
            insert_pos = match.end()
            content = content[:insert_pos] + new_table_row + "\n" + content[insert_pos:]
        else:
            update_section = f"""

---

## 更新记录

| 版本 | 日期 | 说明 |
|------|------|------|
{new_table_row}
"""
            if '## 更新记录' in content:
                content = re.sub(
                    r'(## 更新记录\s*\n)',
                    f'\\1\n| 版本 | 日期 | 说明 |\n|------|------|------|\n{new_table_row}\n',
                    content
                )
            else:
                content += update_section
        
        with open(new_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return new_file
    
    def archive_old_version(self, old_file: Path) -> Optional[Path]:
        """将旧版本移动到过期文件夹"""
        if not old_file.exists():
            return None
        
        archived_file = self.archive_dir / old_file.name
        
        if archived_file.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            archived_file = self.archive_dir / f"{old_file.stem}_{timestamp}{old_file.suffix}"
        
        shutil.move(str(old_file), str(archived_file))
        return archived_file
    
    def process_update(self, daily_file: Path) -> dict:
        """处理文档更新的主流程"""
        result = {
            'status': 'unknown',
            'message': '',
            'actions': [],
            'new_file': None
        }
        
        official_file = self.find_official_file()
        
        print(f"  每日文件: {daily_file.name}")
        print(f"  正式文档: {official_file.name if official_file else '不存在'}")
        
        diff_result = self.compare_files(daily_file, official_file)
        print(f"  比对结果: {diff_result['diff_summary']}")
        
        if not diff_result['has_diff']:
            result['status'] = 'no_change'
            result['message'] = '文件内容相同，无需更新'
            return result
        
        api_diff = diff_result.get('api_diff')
        if api_diff:
            print()
            print("  详细变更:")
            if api_diff['added']:
                print(f"    [+] 新增 {len(api_diff['added'])} 个接口")
                for api in api_diff['added'][:5]:
                    print(f"        - {api.name}")
                if len(api_diff['added']) > 5:
                    print(f"        ... 等共 {len(api_diff['added'])} 个")
            
            if api_diff['removed']:
                print(f"    [-] 删除 {len(api_diff['removed'])} 个接口")
                for api in api_diff['removed'][:5]:
                    print(f"        - {api.name}")
            
            if api_diff['modified']:
                print(f"    [~] 修改 {len(api_diff['modified'])} 个接口")
            print()
        
        if official_file:
            current_version = self.extract_version(official_file.name)
        else:
            current_version = (0, 0)
        
        is_major = self.determine_version_type(diff_result)
        new_version = self.increment_version(current_version, is_major)
        
        version_type = "大版本" if is_major else "小版本"
        print(f"  版本更新: v{current_version[0]}.{current_version[1]} -> v{new_version[0]}.{new_version[1]} ({version_type}更新)")
        
        update_note = self.generate_update_note(api_diff) if api_diff else diff_result['diff_summary']
        
        new_file = self.create_new_version(daily_file, new_version, update_note)
        result['actions'].append(f"创建新版本: {new_file.name}")
        result['new_file'] = new_file
        print(f"  创建新版本: {new_file.name}")
        
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
    parser = argparse.ArgumentParser(
        description='比对差异并更新版本',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--daily-file',
        type=str,
        required=True,
        help='每日生成的MD文件路径（必须）'
    )
    
    parser.add_argument(
        '--official-dir',
        type=str,
        default='../',
        help='正式文档所在目录（默认: ../，即项目根目录）'
    )
    
    parser.add_argument(
        '--archive-dir',
        type=str,
        default='../过期文件/',
        help='过期文件归档目录（默认: ../过期文件/）'
    )
    
    args = parser.parse_args()
    
    # 处理路径
    script_dir = Path(__file__).parent
    
    daily_file = Path(args.daily_file)
    if not daily_file.is_absolute():
        daily_file = script_dir / daily_file
    
    official_dir = Path(args.official_dir)
    if not official_dir.is_absolute():
        official_dir = script_dir / official_dir
    
    archive_dir = Path(args.archive_dir)
    if not archive_dir.is_absolute():
        archive_dir = script_dir / archive_dir
    
    # 检查输入文件
    if not daily_file.exists():
        print(f"错误: 每日文件不存在: {daily_file}")
        return 1
    
    print("=" * 50)
    print("API文档版本比对更新工具")
    print("=" * 50)
    
    try:
        manager = ApiDocVersionManager(official_dir, archive_dir)
        result = manager.process_update(daily_file)
        
        print()
        print(f"处理结果: {result['status']}")
        print(f"信息: {result['message']}")
        
        if result['actions']:
            print("操作记录:")
            for action in result['actions']:
                print(f"  - {action}")
        
        print("\n比对完成!")
        return 0
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
