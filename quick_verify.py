#!/usr/bin/env python3
"""
Git Merge Orchestrator - 快速验证脚本
提供开发过程中的快速验证入口
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from unified_test_runner import UnifiedTestRunner


def quick_health_check():
    """快速健康检查 - 最快的验证方式"""
    print("⚡ 快速健康检查 (预期 < 10秒)")
    print("=" * 40)
    
    runner = UnifiedTestRunner()
    
    # 只运行健康检查
    results = []
    
    # 主项目健康检查
    if runner.env_status.main_tests_available:
        result = runner._run_main_health_check()
        results.append(result)
        
        # 显示即时结果
        icon = "✅" if result.passed else "❌"
        print(f"{icon} {result.name} ({result.duration:.1f}s)")
    
    # test-environment健康检查  
    if runner.env_status.test_environment_available:
        result = runner._run_test_environment_health()
        results.append(result)
        
        # 显示即时结果
        icon = "✅" if result.passed else "❌"
        print(f"{icon} {result.name} ({result.duration:.1f}s)")
    
    # 总结
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    
    if passed == total:
        print(f"\n🎉 健康检查通过 ({passed}/{total})")
        return True
    else:
        print(f"\n❌ 健康检查失败 ({passed}/{total})")
        return False


def verify_after_code_change():
    """代码变更后的验证 - 平衡速度和覆盖"""
    print("🔄 代码变更验证 (预期 30-60秒)")
    print("=" * 40)
    
    # 使用统一测试运行器的快速模式
    runner = UnifiedTestRunner()
    runner.test_results = runner.run_quick_test()
    
    # 生成简化报告
    report = runner.generate_report("code_change_verification")
    
    print(f"\n📊 验证结果:")
    print(f"   通过: {report.passed_tests}/{report.total_tests}")
    print(f"   成功率: {report.success_rate:.1f}%")
    print(f"   耗时: {report.total_duration:.1f}s")
    
    if report.failed_tests == 0:
        print("✅ 代码变更验证通过，可以继续开发")
        return True
    else:
        print("❌ 发现问题，建议修复后再继续")
        for result in report.test_results:
            if not result.passed:
                print(f"   ⚠️ {result.name}: {result.error_message}")
        return False


def verify_before_commit():
    """提交前验证 - 更全面的检查"""
    print("📤 提交前验证 (预期 2-5分钟)")
    print("=" * 40)
    
    # 运行场景测试
    runner = UnifiedTestRunner()
    scenarios = ["config", "file_level", "git"]
    runner.test_results = runner.run_scenario_test(scenarios)
    
    # 生成报告
    report = runner.generate_report("pre_commit_verification")
    
    print(f"\n📊 验证结果:")
    print(f"   通过: {report.passed_tests}/{report.total_tests}")
    print(f"   成功率: {report.success_rate:.1f}%")  
    print(f"   耗时: {report.total_duration:.1f}s")
    
    # 建议
    if report.success_rate >= 95:
        print("✅ 验证优秀，可以安全提交")
        return True
    elif report.success_rate >= 80:
        print("⚠️ 验证良好，建议检查后提交")
        return True
    else:
        print("❌ 验证失败，不建议提交")
        return False


def verify_performance():
    """性能验证 - 专门检查v2.3优化效果"""
    print("🚀 性能验证 (预期 1-3分钟)")
    print("=" * 40)
    
    # 运行性能测试
    runner = UnifiedTestRunner()
    performance_result = runner._run_performance_test()
    
    icon = "✅" if performance_result.passed else "❌"
    print(f"{icon} {performance_result.name} ({performance_result.duration:.1f}s)")
    
    if performance_result.passed:
        print("✅ v2.3性能优化正常工作")
        return True
    else:
        print(f"❌ 性能测试失败: {performance_result.error_message}")
        return False


def interactive_verification_menu():
    """交互式验证菜单"""
    while True:
        print("\n🧪 Git Merge Orchestrator - 快速验证")
        print("=" * 50)
        print("1. ⚡ 快速健康检查 (< 10秒)")
        print("2. 🔄 代码变更验证 (30-60秒)")
        print("3. 📤 提交前验证 (2-5分钟)")
        print("4. 🚀 性能验证 (1-3分钟)")
        print("5. 🌟 完整测试 (10-15分钟)")
        print("6. 📋 显示环境状态")
        print("0. 退出")
        
        choice = input("\n请选择验证类型 (0-6): ").strip()
        
        if choice == "0":
            print("👋 退出验证")
            break
        elif choice == "1":
            quick_health_check()
        elif choice == "2":
            verify_after_code_change()
        elif choice == "3":
            verify_before_commit()
        elif choice == "4":
            verify_performance()
        elif choice == "5":
            os.system("python unified_test_runner.py --full")
        elif choice == "6":
            runner = UnifiedTestRunner()
            runner.print_environment_status()
        else:
            print("❌ 无效选择")
        
        if choice != "0":
            input("\n按回车继续...")


def main():
    """主函数 - 支持命令行快速调用"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Git Merge Orchestrator 快速验证工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
快速验证选项:
  --health     快速健康检查 (< 10秒)
  --change     代码变更验证 (30-60秒)  
  --commit     提交前验证 (2-5分钟)
  --perf       性能验证 (1-3分钟)
  --interactive 交互式菜单

使用示例:
  python quick_verify.py --health      # 最快的检查
  python quick_verify.py --change      # 代码修改后
  python quick_verify.py --commit      # 提交前验证
  python quick_verify.py               # 交互式菜单
        """
    )
    
    parser.add_argument("--health", action="store_true", help="快速健康检查")
    parser.add_argument("--change", action="store_true", help="代码变更验证")
    parser.add_argument("--commit", action="store_true", help="提交前验证")
    parser.add_argument("--perf", action="store_true", help="性能验证")
    parser.add_argument("--interactive", action="store_true", help="交互式菜单")
    
    args = parser.parse_args()
    
    # 根据参数执行对应的验证
    success = True
    
    if args.health:
        success = quick_health_check()
    elif args.change:
        success = verify_after_code_change()
    elif args.commit:
        success = verify_before_commit()
    elif args.perf:
        success = verify_performance()
    elif args.interactive:
        interactive_verification_menu()
        return  # 交互模式不返回退出码
    else:
        # 默认显示交互菜单
        interactive_verification_menu()
        return
    
    # 返回适当的退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 验证工具异常: {e}")
        sys.exit(1)