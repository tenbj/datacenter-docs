# -*- coding: utf-8 -*-
"""
修正数据域详情文档元数据区换行格式
将Tab换行改为Markdown标准的两个空格换行
"""

import os
import re

def fix_metadata_lines(filepath):
    """修正文件顶部元数据区的换行格式"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    fixed_lines = []
    in_metadata = False
    
    for i, line in enumerate(lines):
        # 检测元数据区开始和结束
        if line.startswith('> **'):
            in_metadata = True
            # 将行尾的Tab替换为两个空格
            if line.endswith('\t'):
                line = line[:-1] + '  '
            elif not line.endswith('  '):
                line = line + '  '
        elif in_metadata and line.strip() == '---':
            in_metadata = False
        
        fixed_lines.append(line)
    
    fixed_content = '\n'.join(fixed_lines)
    
    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"修正完成: {os.path.basename(filepath)}")

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 获取所有需要处理的v1.1文件（除了01_交易域，用户已手动修正）
    files_to_process = []
    for filename in os.listdir(script_dir):
        if filename.endswith('_v1.1.md') and not filename.startswith('01_'):
            files_to_process.append(os.path.join(script_dir, filename))
    
    print(f"找到 {len(files_to_process)} 个文件待修正")
    
    for filepath in sorted(files_to_process):
        fix_metadata_lines(filepath)
    
    print("\n全部修正完成！")

if __name__ == '__main__':
    main()
