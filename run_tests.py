#!/usr/bin/env python3
"""
Git Merge Orchestrator - 测试快捷入口
将测试调用重定向到tests目录
"""

import sys
import subprocess
from pathlib import Path

def main():
    """调用tests目录中的测试运行器"""
    tests_runner = Path(__file__).parent / "tests" / "run_tests.py"
    
    if not tests_runner.exists():
        print("❌ 测试运行器不存在：tests/run_tests.py")
        return 1
    
    print("🔄 重定向到 tests/run_tests.py...")
    
    # 将所有参数传递给tests目录中的运行器
    cmd = [sys.executable, str(tests_runner)] + sys.argv[1:]
    return subprocess.call(cmd)

if __name__ == "__main__":
    sys.exit(main())
