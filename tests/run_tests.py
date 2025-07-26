#!/usr/bin/env python3
"""
Git Merge Orchestrator - 统一测试运行器
提供简单易用的测试入口，支持多种测试模式
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent.parent))


def show_test_menu():
    """显示测试菜单"""
    print("🧪 Git Merge Orchestrator 测试套件")
    print("=" * 60)
    print("1. 🚀 运行完整测试套件 (推荐)")
    print("2. 📋 配置管理测试")
    print("3. 🚀 部署和模块测试")
    print("4. ⚡ 性能测试")
    print("5. 🔧 合并策略测试")
    print("6. 🔄 集成测试")
    print("7. 🛡️ 错误处理测试")
    print("8. 🎯 运行特定测试")
    print("9. 📊 快速健康检查")
    print("0. 退出")


def run_quick_health_check():
    """快速健康检查 - 运行最关键的测试"""
    print("🏥 运行快速健康检查...")

    try:
        from comprehensive_test import ComprehensiveTestSuite

        suite = ComprehensiveTestSuite()

        # 运行关键测试
        critical_tests = [
            ("模块导入", suite.test_module_imports),
            ("配置管理", suite.test_config_manager_basic),
            ("Git基础操作", suite.test_git_operations_basic),
            ("合并策略", suite.test_merge_executor_factory),
        ]

        passed = 0
        total = len(critical_tests)

        for test_name, test_func in critical_tests:
            print(f"\n🧪 检查 {test_name}...")
            if test_func():
                print(f"✅ {test_name} 正常")
                passed += 1
            else:
                print(f"❌ {test_name} 异常")

        suite.cleanup()

        print(f"\n📊 健康检查结果: {passed}/{total} 项正常")

        if passed == total:
            print("🎉 系统健康状况良好！")
            return True
        elif passed >= total * 0.75:
            print("⚠️ 系统基本正常，但有些问题需要关注")
            return True
        else:
            print("❌ 系统存在严重问题，建议运行完整测试")
            return False

    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False


def run_specific_test_interactive():
    """交互式运行特定测试"""
    print("\n🎯 可用的特定测试:")
    tests = {
        "1": ("config_basic", "配置管理基本功能"),
        "2": ("config_expiry", "配置过期检测"),
        "3": ("config_files", "配置文件操作"),
        "4": ("imports", "模块导入测试"),
        "5": ("git_basic", "Git基础操作"),
        "6": ("file_helper", "文件助手功能"),
        "7": ("performance", "性能监控"),
        "8": ("large_scale", "大规模文件分组"),
        "9": ("merge_factory", "合并执行器工厂"),
        "10": ("dry_strategies", "DRY架构策略"),
        "11": ("integration", "主控制器集成"),
        "12": ("error_handling", "错误处理"),
    }

    for key, (test_id, desc) in tests.items():
        print(f"  {key}. {desc}")

    choice = input("\n请选择要运行的测试 (1-12): ").strip()

    if choice in tests:
        test_id, desc = tests[choice]
        print(f"\n🚀 运行测试: {desc}")

        try:
            from comprehensive_test import ComprehensiveTestSuite

            suite = ComprehensiveTestSuite()
            success = suite.run_specific_test(test_id)

            if success:
                print(f"✅ 测试 '{desc}' 通过")
            else:
                print(f"❌ 测试 '{desc}' 失败")

            return success

        except Exception as e:
            print(f"❌ 运行测试时出错: {e}")
            return False
    else:
        print("❌ 无效选择")
        return False


def run_category_test(category):
    """运行指定类别的测试"""
    try:
        from comprehensive_test import ComprehensiveTestSuite

        suite = ComprehensiveTestSuite()
        suite.run_all_tests([category])
        return True
    except Exception as e:
        print(f"❌ 运行测试时出错: {e}")
        return False


def main():
    """主函数"""
    try:
        while True:
            show_test_menu()
            choice = input("\n请选择测试选项 (0-9): ").strip()

            if choice == "0":
                print("👋 测试结束")
                break
            elif choice == "1":
                print("🚀 运行完整测试套件...")
                try:
                    from comprehensive_test import ComprehensiveTestSuite

                    suite = ComprehensiveTestSuite()
                    suite.run_all_tests()
                except Exception as e:
                    print(f"❌ 运行完整测试套件时出错: {e}")
            elif choice == "2":
                run_category_test("config")
            elif choice == "3":
                run_category_test("deployment")
            elif choice == "4":
                run_category_test("performance")
            elif choice == "5":
                run_category_test("merge_strategies")
            elif choice == "6":
                run_category_test("integration")
            elif choice == "7":
                run_category_test("error_handling")
            elif choice == "8":
                run_specific_test_interactive()
            elif choice == "9":
                run_quick_health_check()
            else:
                print("❌ 无效选择，请输入 0-9")

            if choice != "0":
                input("\n按回车键继续...")

    except KeyboardInterrupt:
        print("\n\n👋 用户中断，测试退出")
    except Exception as e:
        print(f"❌ 测试运行器出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 支持命令行快速调用
    if len(sys.argv) > 1:
        if sys.argv[1] == "--health":
            success = run_quick_health_check()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "--full":
            try:
                from comprehensive_test import ComprehensiveTestSuite

                suite = ComprehensiveTestSuite()
                suite.run_all_tests()
            except Exception as e:
                print(f"❌ 运行测试失败: {e}")
                sys.exit(1)
        elif sys.argv[1] == "--help":
            print("🧪 Git Merge Orchestrator 测试运行器")
            print("用法:")
            print("  python run_tests.py           # 交互式菜单")
            print("  python run_tests.py --health  # 快速健康检查")
            print("  python run_tests.py --full    # 完整测试套件")
            print("  python run_tests.py --help    # 显示此帮助")
        else:
            print("❌ 未知参数，使用 --help 查看用法")
            sys.exit(1)
    else:
        main()
