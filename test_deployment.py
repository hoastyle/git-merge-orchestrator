#!/usr/bin/env python3
"""
部署测试脚本 - 验证优化功能是否正常工作
"""

import sys
from pathlib import Path


def test_imports():
    """测试所有导入是否正常"""
    print("🧪 测试1: 验证模块导入...")

    try:
        from core.optimized_contributor_analyzer import OptimizedContributorAnalyzer

        print("✅ OptimizedContributorAnalyzer 导入成功")

        from core.optimized_task_assigner import OptimizedTaskAssigner

        print("✅ OptimizedTaskAssigner 导入成功")

        from utils.performance_monitor import performance_monitor, timing_context

        print("✅ performance_monitor 导入成功")

        return True
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return False


def test_basic_functionality():
    """测试基本功能"""
    print("\n🧪 测试2: 验证基本功能...")

    try:
        from core.git_operations import GitOperations
        from core.optimized_contributor_analyzer import OptimizedContributorAnalyzer
        from core.optimized_task_assigner import OptimizedTaskAssigner

        # 初始化组件
        git_ops = GitOperations(".")
        analyzer = OptimizedContributorAnalyzer(git_ops)
        assigner = OptimizedTaskAssigner(analyzer)

        print("✅ 组件初始化成功")

        # 测试性能统计
        stats = analyzer.get_performance_stats()
        print(f"✅ 性能统计正常: {len(stats)} 项指标")

        return True
    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        return False


def test_performance_monitor():
    """测试性能监控"""
    print("\n🧪 测试3: 验证性能监控...")

    try:
        from utils.performance_monitor import performance_monitor, timing_context

        @performance_monitor("测试函数")
        def test_func():
            import time

            time.sleep(0.1)  # 模拟耗时操作
            return "success"

        result = test_func()
        print(f"✅ 性能监控正常: {result}")

        # 测试上下文管理器
        with timing_context("测试上下文"):
            import time

            time.sleep(0.1)

        print("✅ 上下文管理器正常")

        return True
    except Exception as e:
        print(f"❌ 性能监控测试失败: {e}")
        return False


def test_cache_functionality():
    """测试缓存功能"""
    print("\n🧪 测试4: 验证缓存功能...")

    try:
        from core.git_operations import GitOperations
        from core.optimized_contributor_analyzer import OptimizedContributorAnalyzer

        git_ops = GitOperations(".")
        analyzer = OptimizedContributorAnalyzer(git_ops)

        # 测试缓存加载
        cache_loaded = analyzer.load_persistent_cache()
        print(f"✅ 缓存加载测试: {'有缓存' if cache_loaded else '无缓存(正常)'}")

        # 测试缓存状态
        stats = analyzer.get_performance_stats()
        print(f"✅ 缓存状态查询正常")

        return True
    except Exception as e:
        print(f"❌ 缓存功能测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 Git Merge Orchestrator 部署测试")
    print("=" * 50)

    # 检查环境
    if not Path(".git").exists():
        print("⚠️ 警告: 不在Git仓库中，某些功能可能无法完全测试")

    tests = [
        test_imports,
        test_basic_functionality,
        test_performance_monitor,
        test_cache_functionality,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        else:
            print("   建议检查文件是否正确创建和修改")

    print(f"\n📊 测试结果: {passed}/{total} 项测试通过")

    if passed == total:
        print("🎉 部署成功！所有功能正常")
        print("\n📋 下一步:")
        print("   1. 运行 python main.py <源分支> <目标分支>")
        print("   2. 选择菜单项3体验涡轮增压分配")
        print("   3. 选择菜单项15管理性能缓存")
    else:
        print("⚠️ 部分功能异常，请检查部署步骤")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
