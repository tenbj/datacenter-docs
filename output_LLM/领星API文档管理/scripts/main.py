# -*- coding: utf-8 -*-
"""
main.py - 领星API文档管理主控脚本

功能：
串联所有步骤，一键执行完整流程：
1. 抓取网页源码
2. 解析为Markdown
3. 解析为CSV
4. 比对更新版本

使用方法：
    python main.py                  # 执行完整流程
    python main.py --skip-fetch     # 跳过抓取步骤
    python main.py --only-fetch     # 仅执行抓取步骤

作者：Antigravity
创建时间：2026-01-28
"""

import argparse
import subprocess
import sys
import io
from datetime import datetime
from pathlib import Path

# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class PipelineExecutor:
    """流水线执行器"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.scripts_dir = project_root / "scripts"
        self.html_dir = project_root / "html"
        self.md_dir = project_root / "md"
        self.csv_dir = project_root / "csv"
        
        # 今日日期
        self.today = datetime.now().strftime('%Y%m%d')
        
        # 文件路径
        self.html_file = self.html_dir / f"lx_api_{self.today}.html"
        self.md_file = self.md_dir / f"领星API接口列表_{self.today}.md"
        self.csv_file = self.csv_dir / f"领星API接口列表_{self.today}.csv"
    
    def run_script(self, script_name: str, args: list = None) -> tuple:
        """
        运行Python脚本
        
        Args:
            script_name: 脚本名称
            args: 命令行参数列表
            
        Returns:
            (成功标志, 输出内容)
        """
        script_path = self.scripts_dir / script_name
        
        if not script_path.exists():
            return False, f"脚本不存在: {script_path}"
        
        cmd = [sys.executable, str(script_path)]
        if args:
            cmd.extend(args)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=str(self.scripts_dir)
            )
            
            output = result.stdout
            if result.stderr:
                output += "\n" + result.stderr
            
            return result.returncode == 0, output
        except Exception as e:
            return False, f"执行错误: {e}"
    
    def step1_fetch_html(self) -> bool:
        """步骤1：抓取网页源码"""
        print("\n" + "=" * 60)
        print("【步骤1】抓取网页源码")
        print("=" * 60)
        
        success, output = self.run_script(
            "01_fetch_html.py",
            ["--output-dir", str(self.html_dir)]
        )
        
        print(output)
        
        if success:
            print(f"✓ HTML文件: {self.html_file}")
        else:
            print("✗ 抓取失败")
        
        return success
    
    def step2_parse_to_md(self) -> bool:
        """步骤2：解析为Markdown"""
        print("\n" + "=" * 60)
        print("【步骤2】解析为Markdown")
        print("=" * 60)
        
        # 查找HTML文件
        html_file = self._find_latest_html()
        if not html_file:
            print("✗ 未找到HTML文件")
            return False
        
        success, output = self.run_script(
            "02_parse_to_md.py",
            ["--input-file", str(html_file), "--output-dir", str(self.md_dir)]
        )
        
        print(output)
        
        if success:
            print(f"✓ MD文件: {self.md_file}")
        else:
            print("✗ 解析失败")
        
        return success
    
    def step3_parse_to_csv(self) -> bool:
        """步骤3：解析为CSV"""
        print("\n" + "=" * 60)
        print("【步骤3】解析为CSV")
        print("=" * 60)
        
        # 查找HTML文件
        html_file = self._find_latest_html()
        if not html_file:
            print("✗ 未找到HTML文件")
            return False
        
        success, output = self.run_script(
            "03_parse_to_csv.py",
            ["--input-file", str(html_file), "--output-dir", str(self.csv_dir)]
        )
        
        print(output)
        
        if success:
            print(f"✓ CSV文件: {self.csv_file}")
        else:
            print("✗ 解析失败")
        
        return success
    
    def step4_compare_update(self) -> bool:
        """步骤4：比对更新版本"""
        print("\n" + "=" * 60)
        print("【步骤4】比对更新版本")
        print("=" * 60)
        
        # 查找MD文件
        md_file = self._find_latest_md()
        if not md_file:
            print("✗ 未找到MD文件")
            return False
        
        success, output = self.run_script(
            "04_compare_update.py",
            [
                "--daily-file", str(md_file),
                "--official-dir", str(self.project_root),
                "--archive-dir", str(self.project_root / "过期文件")
            ]
        )
        
        print(output)
        
        return success
    
    def _find_latest_html(self) -> Path:
        """查找最新的HTML文件"""
        if self.html_file.exists():
            return self.html_file
        
        # 查找目录中最新的HTML文件
        html_files = list(self.html_dir.glob("lx_api_*.html"))
        if html_files:
            return max(html_files, key=lambda f: f.stat().st_mtime)
        
        return None
    
    def _find_latest_md(self) -> Path:
        """查找最新的MD文件"""
        if self.md_file.exists():
            return self.md_file
        
        # 查找目录中最新的MD文件
        md_files = list(self.md_dir.glob("领星API接口列表_*.md"))
        if md_files:
            return max(md_files, key=lambda f: f.stat().st_mtime)
        
        return None
    
    def run_full_pipeline(self, skip_fetch: bool = False, only_fetch: bool = False) -> bool:
        """
        运行完整流水线
        
        Args:
            skip_fetch: 是否跳过抓取步骤
            only_fetch: 是否仅执行抓取步骤
        """
        print("\n" + "=" * 60)
        print("领星API文档管理系统")
        print(f"项目目录: {self.project_root}")
        print(f"执行日期: {self.today}")
        print("=" * 60)
        
        steps_success = []
        
        # 步骤1：抓取
        if only_fetch or not skip_fetch:
            success = self.step1_fetch_html()
            steps_success.append(("抓取HTML", success))
            
            if only_fetch:
                self._print_summary(steps_success)
                return success
            
            if not success:
                print("\n警告: 抓取失败，尝试使用现有HTML文件继续...")
        
        # 步骤2：解析MD
        success = self.step2_parse_to_md()
        steps_success.append(("解析为MD", success))
        
        if not success:
            print("\n错误: MD解析失败，无法继续")
            self._print_summary(steps_success)
            return False
        
        # 步骤3：解析CSV
        success = self.step3_parse_to_csv()
        steps_success.append(("解析为CSV", success))
        
        # 步骤4：比对更新
        success = self.step4_compare_update()
        steps_success.append(("比对更新", success))
        
        self._print_summary(steps_success)
        
        return all(s[1] for s in steps_success)
    
    def _print_summary(self, steps: list):
        """打印执行摘要"""
        print("\n" + "=" * 60)
        print("执行摘要")
        print("=" * 60)
        
        for step_name, success in steps:
            status = "✓ 成功" if success else "✗ 失败"
            print(f"  {step_name}: {status}")
        
        print("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='领星API文档管理主控脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：
    python main.py                  # 执行完整流程
    python main.py --skip-fetch     # 跳过抓取步骤（使用现有HTML）
    python main.py --only-fetch     # 仅执行抓取步骤
        """
    )
    
    parser.add_argument(
        '--skip-fetch',
        action='store_true',
        help='跳过抓取步骤，使用现有HTML文件'
    )
    
    parser.add_argument(
        '--only-fetch',
        action='store_true',
        help='仅执行抓取步骤'
    )
    
    args = parser.parse_args()
    
    # 确定项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    # 创建执行器
    executor = PipelineExecutor(project_root)
    
    # 执行流水线
    success = executor.run_full_pipeline(
        skip_fetch=args.skip_fetch,
        only_fetch=args.only_fetch
    )
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
