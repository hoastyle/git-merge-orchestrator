#!/usr/bin/env python3
"""
Git Merge Orchestrator - 增强分析功能测试脚本
用于验证行数权重分析优化的实现效果
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from core.git_operations import GitOperations
    from core.enhanced_contributor_analyzer import EnhancedContributorAnalyzer
    from core.enhanced_task_assigner import EnhancedTaskAssigner
    from config import ENHANCED_CONTRIBUTOR_ANALYSIS

    print("✅ 所有增强模块导入成功")
except ImportError as e:
    print(f"❌ 模块导入失败: {e}")
    sys.exit(1)


def test_enhanced_git_log_parsing():
    """测试增强Git日志解析功能"""
    print("\n🔍 测试 1: 增强Git日志解析功能")
    print("=" * 50)

    git_ops = GitOperations()

    # 获取一些测试文件
    print("获取变更文件...")
    changed_files = git_ops.run_command("git diff --name-only HEAD~10 HEAD")
    if not changed_files:
        print("⚠️  未找到变更文件，跳过此测试")
        return False

    test_files = changed_files.split("\n")[:3]  # 取前3个文件测试
    test_files = [f for f in test_files if f.strip()]

    if not test_files:
        print("⚠️  没有有效的测试文件")
        return False

    print(f"测试文件: {test_files}")

    for test_file in test_files:
        print(f"\n📁 分析文件: {test_file}")

        try:
            # 测试增强分析
            contributors = git_ops.get_enhanced_file_contributors(
                test_file, months=12, enable_line_analysis=True
            )

            if contributors:
                print(f"  ✅ 找到 {len(contributors)} 个贡献者")

                # 显示详细信息
                for author, info in list(contributors.items())[:2]:  # 只显示前2个
                    print(f"  👤 {author}:")
                    print(f"    提交数: {info.get('total_commits', 0)}")
                    print(f"    行数变更: {info.get('total_changes', 0)}")
                    print(f"    增强评分: {info.get('enhanced_score', 0):.3f}")

                    # 显示评分详情
                    if "score_breakdown" in info:
                        breakdown = info["score_breakdown"]
                        print(f"    评分详情:")
                        for key, value in breakdown.items():
                            print(f"      {key}: {value:.3f}")
            else:
                print("  ⚠️  未找到贡献者")

        except Exception as e:
            print(f"  ❌ 分析失败: {e}")
            return False

    print("\n✅ Git日志解析测试完成")
    return True


def test_enhanced_contributor_analyzer():
    """测试增强贡献者分析器"""
    print("\n🧠 测试 2: 增强贡献者分析器")
    print("=" * 50)

    git_ops = GitOperations()
    analyzer = EnhancedContributorAnalyzer(git_ops)

    if not analyzer.is_enabled():
        print("⚠️  增强分析器未启用，检查配置")
        return False

    # 获取测试文件
    changed_files = git_ops.run_command("git diff --name-only HEAD~5 HEAD")
    if not changed_files:
        print("⚠️  未找到测试文件")
        return False

    test_files = [f for f in changed_files.split("\n")[:2] if f.strip()]

    print(f"测试文件: {test_files}")

    try:
        # 测试单文件分析
        print("\n📊 单文件分析测试:")
        for test_file in test_files:
            contributors = analyzer.analyze_file_contributors(
                test_file, enable_line_analysis=True
            )

            if contributors:
                print(f"  📁 {test_file}: {len(contributors)} 个贡献者")

                # 获取最佳分配对象
                best_author, best_info, reason = analyzer.get_best_assignee(
                    contributors
                )
                if best_author:
                    print(f"    🎯 推荐: {best_author} - {reason}")
                    print(f"    📊 评分: {best_info.get('enhanced_score', 0):.3f}")

        # 测试批量分析
        print(f"\n📦 批量分析测试:")
        batch_result = analyzer.analyze_contributors_batch(
            test_files, enable_line_analysis=True
        )

        print(f"  批量分析结果: {len(batch_result)} 个文件")
        for file_path, contributors in batch_result.items():
            print(f"    📁 {file_path}: {len(contributors)} 个贡献者")

            # 获取统计信息
            stats = analyzer.get_analysis_statistics(contributors)
            print(f"      活跃贡献者: {stats.get('active_contributors', 0)}")
            print(f"      平均评分: {stats.get('avg_score', 0):.3f}")
            print(f"      使用算法: {stats.get('algorithm_used', 'unknown')}")

        print("\n✅ 增强贡献者分析器测试完成")
        return True

    except Exception as e:
        print(f"❌ 分析器测试失败: {e}")
        return False


def test_enhanced_task_assigner():
    """测试增强任务分配器"""
    print("\n🎯 测试 3: 增强任务分配器")
    print("=" * 50)

    git_ops = GitOperations()
    assigner = EnhancedTaskAssigner(git_ops)

    if not assigner.is_enhanced_enabled():
        print("⚠️  增强任务分配器未启用")
        return False

    # 创建模拟计划
    class MockPlan:
        def __init__(self):
            self.processing_mode = "file_level"
            self.files = []

    # 获取测试文件
    changed_files = git_ops.run_command("git diff --name-only HEAD~3 HEAD")
    if not changed_files:
        print("⚠️  未找到测试文件")
        return False

    test_files = [f for f in changed_files.split("\n")[:3] if f.strip()]

    # 创建模拟计划
    mock_plan = MockPlan()
    for file_path in test_files:
        mock_plan.files.append(
            {
                "path": file_path,
                "assignee": None,
                "status": "pending",
                "assignment_reason": None,
            }
        )

    print(f"模拟计划包含 {len(mock_plan.files)} 个文件")

    try:
        # 执行增强任务分配
        success_count, failed_count, stats = assigner.enhanced_auto_assign_tasks(
            mock_plan,
            exclude_authors=[],
            max_tasks_per_person=10,
            enable_line_analysis=True,
        )

        print(f"\n📊 分配结果:")
        print(f"  成功: {success_count}")
        print(f"  失败: {failed_count}")
        print(f"  用时: {stats.get('elapsed_time', 0):.2f}s")
        print(f"  涉及贡献者: {stats.get('contributors_involved', 0)}")

        # 显示分配详情
        print(f"\n📋 分配详情:")
        for file_info in mock_plan.files:
            assignee = file_info.get("assignee", "未分配")
            reason = file_info.get("assignment_reason", "unknown")
            print(f"  📁 {file_info['path']}: {assignee} - {reason}")

        # 获取分析报告
        report = assigner.get_assignment_analysis_report(mock_plan)
        print(f"\n📈 分析报告:")
        print(f"  总项目: {report['total_items']}")
        print(f"  已分配: {report['assigned_items']}")
        print(f"  未分配: {report['unassigned_items']}")
        print(f"  使用增强分析: {report['enhanced_analysis_used']}")

        print("\n✅ 增强任务分配器测试完成")
        return True

    except Exception as e:
        print(f"❌ 任务分配器测试失败: {e}")
        return False


def test_configuration_system():
    """测试配置系统"""
    print("\n⚙️  测试 4: 增强配置系统")
    print("=" * 50)

    try:
        # 显示配置信息
        print("增强贡献者分析配置:")
        print(f"  启用状态: {ENHANCED_CONTRIBUTOR_ANALYSIS.get('enabled', False)}")
        print(
            f"  算法版本: {ENHANCED_CONTRIBUTOR_ANALYSIS.get('algorithm_version', 'unknown')}"
        )
        print(
            f"  分配算法: {ENHANCED_CONTRIBUTOR_ANALYSIS.get('assignment_algorithm', 'unknown')}"
        )
        print(
            f"  行数权重: {ENHANCED_CONTRIBUTOR_ANALYSIS.get('line_weight_enabled', False)}"
        )
        print(
            f"  时间权重: {ENHANCED_CONTRIBUTOR_ANALYSIS.get('time_weight_enabled', False)}"
        )
        print(
            f"  一致性权重: {ENHANCED_CONTRIBUTOR_ANALYSIS.get('consistency_weight_enabled', False)}"
        )

        # 权重算法配置
        line_algorithm = ENHANCED_CONTRIBUTOR_ANALYSIS.get(
            "line_weight_algorithm", "logarithmic"
        )
        print(f"  行数权重算法: {line_algorithm}")

        magnitude_scaling = ENHANCED_CONTRIBUTOR_ANALYSIS.get("magnitude_scaling", {})
        print(f"  规模缩放配置:")
        for key, value in magnitude_scaling.items():
            print(f"    {key}: {value}")

        print("\n✅ 配置系统测试完成")
        return True

    except Exception as e:
        print(f"❌ 配置系统测试失败: {e}")
        return False


def run_performance_comparison():
    """运行性能对比测试"""
    print("\n⚡ 性能对比测试")
    print("=" * 50)

    git_ops = GitOperations()

    # 获取测试文件
    changed_files = git_ops.run_command("git diff --name-only HEAD~10 HEAD")
    if not changed_files:
        print("⚠️  未找到测试文件")
        return False

    test_files = [f for f in changed_files.split("\n")[:5] if f.strip()]

    print(f"测试 {len(test_files)} 个文件的性能...")

    try:
        # 基础分析性能测试
        start_time = datetime.now()
        basic_results = {}
        for file_path in test_files:
            basic_results[file_path] = git_ops.get_file_contributors_analysis(file_path)
        basic_time = (datetime.now() - start_time).total_seconds()

        print(f"🔧 基础分析用时: {basic_time:.3f}s")

        # 增强分析性能测试
        start_time = datetime.now()
        enhanced_results = {}
        for file_path in test_files:
            enhanced_results[file_path] = git_ops.get_enhanced_file_contributors(
                file_path
            )
        enhanced_time = (datetime.now() - start_time).total_seconds()

        print(f"🚀 增强分析用时: {enhanced_time:.3f}s")

        # 批量分析性能测试
        start_time = datetime.now()
        batch_results = git_ops.get_enhanced_contributors_batch(test_files)
        batch_time = (datetime.now() - start_time).total_seconds()

        print(f"📦 批量分析用时: {batch_time:.3f}s")

        # 性能对比
        print(f"\n📊 性能对比:")
        if enhanced_time > 0:
            basic_ratio = basic_time / enhanced_time
            print(f"  增强vs基础: {basic_ratio:.2f}x")

        if batch_time > 0:
            enhanced_ratio = enhanced_time / batch_time
            print(f"  批量vs单独: {enhanced_ratio:.2f}x")

        print(f"\n✅ 性能对比测试完成")
        return True

    except Exception as e:
        print(f"❌ 性能测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🚀 Git Merge Orchestrator - 增强分析功能测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 检查是否在Git仓库中
    if not os.path.exists(".git"):
        print("❌ 请在Git仓库目录中运行此测试脚本")
        sys.exit(1)

    test_results = []

    # 运行所有测试
    tests = [
        ("增强Git日志解析", test_enhanced_git_log_parsing),
        ("增强贡献者分析器", test_enhanced_contributor_analyzer),
        ("增强任务分配器", test_enhanced_task_assigner),
        ("配置系统", test_configuration_system),
        ("性能对比", run_performance_comparison),
    ]

    for test_name, test_func in tests:
        print(f"\n{'=' * 60}")
        try:
            result = test_func()
            test_results.append((test_name, result))
            if result:
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"⚠️  {test_name} 测试失败或跳过")
        except Exception as e:
            print(f"❌ {test_name} 测试出错: {e}")
            test_results.append((test_name, False))

    # 总结
    print(f"\n{'=' * 60}")
    print("🏁 测试总结")
    print("=" * 60)

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")

    print(f"\n📊 总体结果: {passed}/{total} 测试通过")

    if passed == total:
        print("🎉 所有测试通过！增强分析功能工作正常")
        return 0
    else:
        print("⚠️  部分测试未通过，请检查相关功能")
        return 1


if __name__ == "__main__":
    sys.exit(main())
