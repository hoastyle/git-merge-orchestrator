#!/usr/bin/env python3
"""
Git Merge Orchestrator - 增强分析功能演示
展示行数权重分析优化的实际效果
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.git_operations import GitOperations
from core.enhanced_contributor_analyzer import EnhancedContributorAnalyzer
from config import ENHANCED_CONTRIBUTOR_ANALYSIS


def demo_line_weight_analysis():
    """演示行数权重分析功能"""
    print("🎯 演示：行数权重分析优化")
    print("=" * 50)

    git_ops = GitOperations()
    analyzer = EnhancedContributorAnalyzer(git_ops)

    # 获取最近变更的文件
    changed_files = git_ops.run_command("git diff --name-only HEAD~5 HEAD")
    if not changed_files:
        print("⚠️  未找到变更文件")
        return

    demo_files = [f for f in changed_files.split("\n")[:3] if f.strip()]

    print(f"📁 演示文件: {demo_files}")

    for file_path in demo_files:
        print(f"\n🔍 分析文件: {file_path}")
        print("-" * 40)

        # 基础分析
        print("1️⃣ 基础分析结果:")
        basic_contributors = git_ops.get_file_contributors_analysis(file_path)

        for author, info in list(basic_contributors.items())[:2]:
            print(f"  👤 {author}")
            print(f"    总提交数: {info.get('total_commits', 0)}")
            print(f"    近期提交数: {info.get('recent_commits', 0)}")
            print(f"    基础评分: {info.get('score', 0):.3f}")

        # 增强分析
        print("\n2️⃣ 增强分析结果（含行数权重）:")
        enhanced_contributors = analyzer.analyze_file_contributors(
            file_path, enable_line_analysis=True
        )

        for author, info in list(enhanced_contributors.items())[:2]:
            print(f"  👤 {author}")
            print(f"    总提交数: {info.get('total_commits', 0)}")
            print(f"    行数变更: {info.get('total_changes', 0)}")
            print(f"    增强评分: {info.get('enhanced_score', 0):.3f}")

            # 显示评分分解
            if "score_breakdown" in info:
                breakdown = info["score_breakdown"]
                print(f"    评分分解:")
                print(f"      基础提交分数: {breakdown.get('commit_score', 0):.3f}")
                print(f"      行数权重分数: {breakdown.get('line_weight_score', 0):.3f}")
                print(f"      时间权重分数: {breakdown.get('time_weight_score', 0):.3f}")
                print(f"      一致性分数: {breakdown.get('consistency_score', 0):.3f}")

        # 推荐分配
        best_author, best_info, reason = analyzer.get_best_assignee(
            enhanced_contributors
        )
        if best_author:
            print(f"\n🎯 推荐分配: {best_author}")
            print(f"   理由: {reason}")
            print(f"   评分: {best_info.get('enhanced_score', 0):.3f}")


def demo_algorithm_comparison():
    """演示不同算法的效果对比"""
    print("\n🧠 演示：算法效果对比")
    print("=" * 50)

    # 临时修改配置进行对比
    original_algorithm = ENHANCED_CONTRIBUTOR_ANALYSIS["assignment_algorithm"]

    algorithms = ["simple", "weighted", "comprehensive"]
    test_file = "config.py"  # 使用一个稳定的文件

    git_ops = GitOperations()

    print(f"📁 测试文件: {test_file}")
    print("\n🔄 算法对比:")

    for algorithm in algorithms:
        print(f"\n{algorithm.upper()} 算法:")
        print("-" * 20)

        # 临时切换算法
        ENHANCED_CONTRIBUTOR_ANALYSIS["assignment_algorithm"] = algorithm

        analyzer = EnhancedContributorAnalyzer(git_ops)
        contributors = analyzer.analyze_file_contributors(test_file)

        if contributors:
            # 获取最佳分配
            best_author, best_info, reason = analyzer.get_best_assignee(contributors)

            if best_author:
                print(f"  推荐: {best_author}")
                print(f"  评分: {best_info.get('enhanced_score', 0):.3f}")
                print(f"  理由: {reason}")

                # 显示算法特有的评分信息
                if "score_breakdown" in best_info:
                    breakdown = best_info["score_breakdown"]
                    if algorithm != "simple":
                        print(f"  行数权重: {breakdown.get('line_weight_score', 0):.3f}")
                    if algorithm == "comprehensive":
                        print(f"  一致性分数: {breakdown.get('consistency_score', 0):.3f}")

    # 恢复原始配置
    ENHANCED_CONTRIBUTOR_ANALYSIS["assignment_algorithm"] = original_algorithm


def demo_performance_benefits():
    """演示性能提升效果"""
    print("\n⚡ 演示：性能优化效果")
    print("=" * 50)

    git_ops = GitOperations()

    # 获取多个测试文件
    changed_files = git_ops.run_command("git diff --name-only HEAD~10 HEAD")
    if not changed_files:
        print("⚠️  未找到测试文件")
        return

    test_files = [f for f in changed_files.split("\n")[:5] if f.strip()]

    print(f"📊 性能测试: {len(test_files)} 个文件")

    from datetime import datetime

    # 单独分析性能
    print("\n1️⃣ 单独增强分析:")
    start_time = datetime.now()
    individual_results = {}
    for file_path in test_files:
        individual_results[file_path] = git_ops.get_enhanced_file_contributors(
            file_path
        )
    individual_time = (datetime.now() - start_time).total_seconds()
    print(f"   用时: {individual_time:.3f}s")

    # 批量分析性能
    print("\n2️⃣ 批量增强分析:")
    start_time = datetime.now()
    batch_results = git_ops.get_enhanced_contributors_batch(test_files)
    batch_time = (datetime.now() - start_time).total_seconds()
    print(f"   用时: {batch_time:.3f}s")

    # 性能提升
    if batch_time > 0:
        speedup = individual_time / batch_time
        print(f"\n📈 性能提升: {speedup:.2f}x")
        print(f"💾 时间节省: {(individual_time - batch_time):.3f}s")


def demo_configuration_flexibility():
    """演示配置灵活性"""
    print("\n⚙️  演示：配置灵活性")
    print("=" * 50)

    print("🔧 当前配置:")
    config_items = [
        ("启用状态", ENHANCED_CONTRIBUTOR_ANALYSIS.get("enabled", False)),
        ("算法类型", ENHANCED_CONTRIBUTOR_ANALYSIS.get("assignment_algorithm", "unknown")),
        ("行数权重", ENHANCED_CONTRIBUTOR_ANALYSIS.get("line_weight_enabled", False)),
        ("时间权重", ENHANCED_CONTRIBUTOR_ANALYSIS.get("time_weight_enabled", False)),
        (
            "一致性权重",
            ENHANCED_CONTRIBUTOR_ANALYSIS.get("consistency_weight_enabled", False),
        ),
        ("行数算法", ENHANCED_CONTRIBUTOR_ANALYSIS.get("line_weight_algorithm", "unknown")),
        ("缓存启用", ENHANCED_CONTRIBUTOR_ANALYSIS.get("cache_enabled", False)),
        ("并行处理", ENHANCED_CONTRIBUTOR_ANALYSIS.get("parallel_processing", False)),
    ]

    for name, value in config_items:
        status = "✅" if value else "❌"
        print(f"  {status} {name}: {value}")

    print("\n🎛️  权重因子:")
    weight_factors = [
        ("行数权重因子", ENHANCED_CONTRIBUTOR_ANALYSIS.get("line_weight_factor", 0)),
        ("时间权重因子", ENHANCED_CONTRIBUTOR_ANALYSIS.get("time_weight_factor", 0)),
        ("一致性奖励因子", ENHANCED_CONTRIBUTOR_ANALYSIS.get("consistency_bonus_factor", 0)),
    ]

    for name, value in weight_factors:
        print(f"  📊 {name}: {value}")


def main():
    """主演示函数"""
    print("🚀 Git Merge Orchestrator - 增强分析功能演示")
    print("=" * 60)
    print("展示行数权重分析优化的实际效果和性能提升")

    # 检查是否在Git仓库中
    if not os.path.exists(".git"):
        print("❌ 请在Git仓库目录中运行此演示脚本")
        sys.exit(1)

    try:
        # 1. 行数权重分析演示
        demo_line_weight_analysis()

        # 2. 算法对比演示
        demo_algorithm_comparison()

        # 3. 性能优化演示
        demo_performance_benefits()

        # 4. 配置灵活性演示
        demo_configuration_flexibility()

        print(f"\n{'=' * 60}")
        print("🎉 演示完成!")
        print("=" * 60)
        print("💡 主要特性:")
        print("  ✅ 行数权重分析：考虑代码变更规模")
        print("  ✅ 时间衰减权重：重视近期贡献")
        print("  ✅ 一致性评分：奖励持续贡献")
        print("  ✅ 多算法支持：simple, weighted, comprehensive")
        print("  ✅ 批量处理：显著提升分析性能")
        print("  ✅ 配置灵活：支持细粒度调整")
        print("\n🎯 使用建议:")
        print("  • 对于大型项目，推荐使用 comprehensive 算法")
        print("  • 对于性能敏感场景，可选择 weighted 算法")
        print("  • 批量分析比单独分析快 5-10 倍")
        print("  • 可根据项目特点调整权重因子")

    except Exception as e:
        print(f"❌ 演示过程出现错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
