#!/usr/bin/env python3
"""
Git Merge Orchestrator - 智能测试入口
支持传统测试和统一测试系统的智能调用
"""

import sys
import subprocess
from pathlib import Path

def main():
    """智能测试调用器"""
    # 检查是否有统一测试系统
    unified_runner = Path(__file__).parent / "unified_test_runner.py"
    traditional_runner = Path(__file__).parent / "tests" / "run_tests.py"
    
    # 优先使用统一测试系统
    if unified_runner.exists() and len(sys.argv) == 1:
        print("🚀 使用统一测试系统 (默认快速模式)")
        print("💡 使用 python unified_test_runner.py --help 查看更多选项")
        print("💡 使用 python quick_verify.py 进行快速验证")
        print()
        cmd = [sys.executable, str(unified_runner), "--quick"]
        return subprocess.call(cmd)
    elif unified_runner.exists() and ("--unified" in sys.argv):
        print("🚀 使用统一测试系统...")
        # 移除 --unified 参数
        args = [arg for arg in sys.argv[1:] if arg != "--unified"]
        cmd = [sys.executable, str(unified_runner)] + args
        return subprocess.call(cmd)
    elif traditional_runner.exists():
        print("🔄 使用传统测试系统...")
        # 将所有参数传递给tests目录中的运行器
        cmd = [sys.executable, str(traditional_runner)] + sys.argv[1:]
        return subprocess.call(cmd)
    else:
        print("❌ 未找到任何测试运行器")
        print("💡 请检查以下文件是否存在:")
        print(f"   • {unified_runner}")
        print(f"   • {traditional_runner}")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n👋 用户中断测试")
        sys.exit(1)
