#!/usr/bin/env python3
"""
Git Merge Orchestrator - 主入口文件（配置增强版）
支持自动配置保存和无参数运行
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from git_merge_orchestrator import GitMergeOrchestrator
from ui.display_helper import DisplayHelper
from ui.flat_menu_manager import FlatMenuManager
from utils.config_manager import ProjectConfigManager


def parse_arguments():
    """解析命令行参数（增强配置支持）"""
    parser = argparse.ArgumentParser(
        description="Git大分叉智能分步合并工具 - 配置增强版（支持无参数运行）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 首次运行（自动保存配置）
  python main.py feature/big-feature main

  # 后续运行（自动读取配置）
  python main.py

  # 更新配置
  python main.py new-branch main --update-config

  # 指定处理模式和合并策略
  python main.py feature/test main --processing-mode file_level --strategy legacy

  # 非交互式自动化执行（测试和CI/CD）
  python main.py feature main --auto-plan --quiet        # 自动创建计划
  python main.py feature main --auto-workflow --quiet    # 自动完整流程

配置管理特性:
  • 🔄 自动配置保存 - 首次运行后自动保存分支和设置信息
  • 📖 自动配置读取 - 后续运行无需参数，自动使用保存的配置
  • 🔧 配置更新支持 - 使用 --update-config 明确更新配置
  • 💾 配置文件位置 - .merge_work/project_config.json
  • 🎯 智能参数处理 - 优先级：命令行 > 配置文件 > 交互式输入

核心功能:
  • 智能文件分组 - 按目录结构自动分组，每组最多5个文件
  • 贡献者分析 - 基于Git历史分析文件贡献者和活跃度
  • 自动任务分配 - 优先分配给近期活跃且熟悉相关文件的开发者
  • 双合并策略 - Legacy快速覆盖 vs Standard三路合并
  • 批量操作支持 - 支持按负责人批量合并和状态管理
  • 进度跟踪 - 完整的任务状态跟踪和远程分支检测

扁平化菜单系统:
  • 12个直接功能，1级操作，快速高效
  • 数字1-12直接选择功能，q退出，h帮助

核心功能:
  1. 🚀 快速全流程 - 新用户推荐，一键完成
  2. 🔍 分析分叉 - 分支差异分析
  3. 📋 创建计划 - 智能合并计划
  4. ⚡ 自动分配 - 任务智能分配
  5. 📊 项目状态 - 实时进度查看
  6. 🔍 高级查询 - 多维度搜索
  7. 👤 搜索/分配任务 - 任务管理
  8. 📁 合并指定组 - 单组合并
  9. 🎯 批量合并 - 批量处理
  10. 🎉 最终合并 - 完成项目
  11. ⚙️ 系统设置 - 配置管理
  12. 💡 帮助 - 使用指导
        """,
    )

    # 可选的位置参数（支持无参数运行）
    parser.add_argument("source_branch", nargs="?", help="源分支名称（可选，未提供时从配置文件读取）")  # 可选参数
    parser.add_argument("target_branch", nargs="?", help="目标分支名称（可选，未提供时从配置文件读取）")  # 可选参数

    # 配置管理参数
    parser.add_argument("--update-config", action="store_true", help="更新已保存的配置（当提供分支参数时）")
    parser.add_argument("--no-save-config", action="store_true", help="不保存或更新配置（仅本次使用指定参数）")
    parser.add_argument("--show-config", action="store_true", help="显示当前保存的配置信息")
    parser.add_argument("--reset-config", action="store_true", help="重置（删除）保存的配置")

    # 原有参数
    parser.add_argument("--max-files", type=int, default=5, help="每组最大文件数 (默认: 5，仅组模式使用)")
    parser.add_argument("--repo", default=".", help="Git仓库路径 (默认: 当前目录)")
    parser.add_argument(
        "--strategy",
        choices=["legacy", "standard"],
        help="合并策略 (legacy: 快速覆盖, standard: 三路合并)",
    )
    parser.add_argument(
        "--processing-mode",
        choices=["file_level", "group_based"],
        default="file_level",
        help="处理模式：file_level（文件级处理）或 group_based（传统组模式）（默认: file_level）",
    )
    parser.add_argument("--version", action="version", version="Git Merge Orchestrator 2.2 (文件级架构)")

    # 非交互式自动化参数（用于测试和CI/CD）
    parser.add_argument("--auto-analyze", action="store_true", help="自动执行分叉分析后退出（非交互式）")
    parser.add_argument("--auto-plan", action="store_true", help="自动创建合并计划后退出（非交互式）")
    parser.add_argument("--auto-assign", action="store_true", help="自动分配任务后退出（非交互式）")
    parser.add_argument("--auto-workflow", action="store_true", help="自动执行完整流程后退出（非交互式）")
    parser.add_argument("--quiet", action="store_true", help="静默模式，减少输出信息")

    return parser.parse_args()


def resolve_branches_and_config(args):
    """解析分支参数和配置

    优先级：命令行参数 > 配置文件 > 交互式输入
    """
    config_manager = ProjectConfigManager(args.repo)

    # 处理配置管理命令
    if args.show_config:
        config_manager.show_current_config()
        return None, None, None

    if args.reset_config:
        if config_manager.reset_config():
            print("💡 下次运行时需要提供分支参数或进行交互式配置")
        return None, None, None

    # 情况1: 提供了完整的命令行参数
    if args.source_branch and args.target_branch:
        print(f"📝 使用命令行提供的分支: {args.source_branch} → {args.target_branch}")

        # 保存或更新配置（除非明确禁止）
        if not args.no_save_config:
            if args.update_config or not config_manager.has_valid_config():
                action = "更新" if config_manager.has_valid_config() else "保存"
                if config_manager.save_config(
                    args.source_branch,
                    args.target_branch,
                    args.repo,
                    args.max_files,
                    args.strategy,
                ):
                    print(f"✅ 配置已{action}，下次可直接运行 'python main.py'")

        return args.source_branch, args.target_branch, config_manager

    # 情况2: 只提供了部分参数
    if args.source_branch or args.target_branch:
        print("❌ 请提供完整的分支参数，或者不提供参数使用保存的配置")
        print("💡 正确格式: python main.py <源分支> <目标分支>")
        return None, None, None

    # 情况3: 没有提供分支参数，尝试从配置文件读取
    if config_manager.has_valid_config():
        source_branch, target_branch = config_manager.get_branches_from_config()
        print(f"📖 从配置文件读取分支: {source_branch} → {target_branch}")

        # 检查配置是否过期
        if config_manager.is_config_outdated():
            print("⚠️ 警告: 配置文件较旧（超过30天），建议检查分支是否仍然有效")

        return source_branch, target_branch, config_manager

    # 情况4: 没有参数且没有配置，交互式获取
    print("🆕 检测到首次运行，需要配置项目信息")
    print("💡 完成配置后，下次可直接运行 'python main.py'")

    source_branch, target_branch = get_branches_interactively(args.repo)
    if source_branch and target_branch:
        # 保存配置
        if config_manager.save_config(source_branch, target_branch, args.repo, args.max_files, args.strategy):
            print(f"✅ 初始配置已保存，下次可直接运行 'python main.py'")

    return source_branch, target_branch, config_manager


def get_branches_interactively(repo_path):
    """交互式获取分支信息"""
    from core.git_operations import GitOperations

    git_ops = GitOperations(repo_path)

    print("\n🔍 正在检测可用分支...")

    # 获取当前分支作为默认源分支
    current_branch = git_ops.run_command("git branch --show-current")

    # 获取所有分支
    all_branches_output = git_ops.run_command("git branch -a")
    if all_branches_output:
        branches = []
        for line in all_branches_output.split("\n"):
            branch = line.strip().replace("*", "").strip()
            if branch and not branch.startswith("remotes/origin/HEAD"):
                if branch.startswith("remotes/origin/"):
                    branch = branch.replace("remotes/origin/", "")
                if branch not in branches:
                    branches.append(branch)

        print(f"📋 发现分支: {', '.join(branches[:10])}" + ("..." if len(branches) > 10 else ""))

    # 交互式输入
    print(f"\n🎯 请配置分支信息:")

    if current_branch:
        source_input = input(f"源分支 (当前分支: {current_branch}，回车使用当前分支): ").strip()
        source_branch = source_input if source_input else current_branch
    else:
        source_branch = input("源分支: ").strip()

    target_branch = input("目标分支 (常用: main, master, develop): ").strip()

    if not source_branch or not target_branch:
        print("❌ 分支信息不完整")
        return None, None

    return source_branch, target_branch


def show_welcome_banner(orchestrator, config_manager=None):
    """显示欢迎横幅（配置增强版）"""
    mode_info = orchestrator.get_processing_mode_info()
    print(f"🚀 Git大分叉智能分步合并工具 (v2.2 - {mode_info['mode_name']})")
    print("=" * 80)
    print(f"源分支: {orchestrator.source_branch}")
    print(f"目标分支: {orchestrator.target_branch}")
    print(f"处理模式: {mode_info['mode_name']}")
    print(f"模式描述: {mode_info['description']}")
    if orchestrator.processing_mode == "group_based":
        print(f"每组最大文件数: {orchestrator.max_files_per_group}")
    print(f"工作目录: {orchestrator.repo_path}")

    # 显示配置信息
    if config_manager:
        config_file_path = config_manager.get_config_file_path()
        if config_manager.has_valid_config():
            print(f"📋 配置文件: {config_file_path} ✅")
            print(f"💡 下次可直接运行: python main.py")
        else:
            print(f"📋 配置文件: 将保存到 {config_file_path}")

    # 显示当前合并策略
    strategy_info = orchestrator.get_merge_strategy_info()
    print(f"🔧 当前合并策略: {strategy_info['mode_name']}")
    print(f"📝 策略说明: {strategy_info['description']}")

    # 显示增强分析系统状态
    if hasattr(orchestrator, "use_enhanced_analysis"):
        analysis_mode = "增强智能分析 v2.3" if orchestrator.use_enhanced_analysis else "基础分析系统"
        print(f"🧠 分析系统: {analysis_mode}")
        if orchestrator.use_enhanced_analysis:
            print(f"💡 增强特性: 行数权重、时间衰减、一致性评分")

    # 显示版本特性
    version_label = "v2.3" if getattr(orchestrator, "use_enhanced_analysis", False) else "v2.2"
    print(f"\n🆕 {version_label} 架构特性:")
    print("   • 📁 文件级处理: 更精确的任务分配和进度跟踪")
    print("   • 🔄 双模式支持: 文件级处理 + 传统组模式兼容")

    if getattr(orchestrator, "use_enhanced_analysis", False):
        print("   • 🚀 增强分析: 多维度贡献者评分系统")
        print("   • 📊 行数权重: 基于代码变更量的智能分配")
    else:
        print("   • 🎯 智能分配: 基于文件贡献度的精确分配")

    print("   • ⚖️ 负载均衡: 自动优化工作负载分布")
    print("   • 📖 自动配置: 后续运行无需参数")

    # 显示计划摘要（如果存在）
    try:
        summary = orchestrator.get_plan_summary()
        if summary:
            print(f"\n📊 当前计划状态:")

            if orchestrator.processing_mode == "file_level":
                # 文件级模式显示
                stats = summary.get("completion_stats", {})
                print(f"   总文件: {stats.get('total_files', 0)} 个")
                print(f"   已分配: {stats.get('assigned_files', 0)} 个 ({stats.get('assignment_rate', 0):.1f}%)")
                print(f"   已完成: {stats.get('completed_files', 0)} 个 ({stats.get('completion_rate', 0):.1f}%)")
                print(f"   待处理: {stats.get('pending_files', 0)} 个")

                workload = summary.get("workload_distribution", {})
                if workload:
                    print(f"   参与人数: {len(workload)} 位")

                # 智能建议
                if stats.get("total_files", 0) == 0:
                    print("💡 建议: 使用快速开始向导创建文件级合并计划")
                elif stats.get("assigned_files", 0) == 0:
                    print("💡 建议: 使用文件级智能分配系统")
                elif stats.get("completed_files", 0) < stats.get("total_files", 0):
                    print("💡 建议: 检查文件完成状态或使用负载均衡")
            else:
                # 组模式显示（向后兼容）
                stats = summary.get("stats", {})
                print(f"   总分组: {stats.get('total_groups', 0)} 个")
                print(f"   总文件: {stats.get('total_files', 0)} 个")
                print(f"   已分配: {stats.get('assigned_groups', 0)} 组 ({stats.get('assigned_files', 0)} 文件)")
                print(f"   已完成: {stats.get('completed_groups', 0)} 组 ({stats.get('completed_files', 0)} 文件)")

                # 智能建议
                if stats.get("total_groups", 0) == 0:
                    print("💡 建议: 使用快速开始向导创建合并计划")
                elif stats.get("assigned_groups", 0) == 0:
                    print("💡 建议: 使用涡轮增压自动分配任务")

            if summary.get("integration_branch"):
                print(f"   集成分支: {summary['integration_branch']}")
            elif stats["completed_groups"] < stats["total_groups"]:
                print("💡 建议: 继续执行合并操作")
            else:
                print("💡 建议: 执行最终合并完成项目")
    except Exception:
        # 如果获取摘要失败，不影响主程序运行
        pass

    print("=" * 80)


def validate_environment(orchestrator):
    """验证运行环境"""
    # 检查是否在Git仓库中
    git_dir = orchestrator.repo_path / ".git"
    if not git_dir.exists():
        DisplayHelper.print_error("当前目录不是Git仓库")
        return False

    # 检查分支是否存在
    result = orchestrator.git_ops.run_command(f"git rev-parse --verify {orchestrator.source_branch}")
    if result is None:
        DisplayHelper.print_error(f"源分支 '{orchestrator.source_branch}' 不存在")
        return False

    result = orchestrator.git_ops.run_command(f"git rev-parse --verify {orchestrator.target_branch}")
    if result is None:
        DisplayHelper.print_error(f"目标分支 '{orchestrator.target_branch}' 不存在")
        return False

    return True


def execute_non_interactive(orchestrator, args):
    """执行非交互式自动化功能"""
    from ui.menu_commands import MenuCommands

    # 创建命令执行器
    commands = MenuCommands(orchestrator)

    try:
        if args.auto_analyze:
            if not args.quiet:
                print("🔍 执行自动分叉分析...")
            commands.execute_analyze_divergence()
            if not args.quiet:
                print("✅ 分叉分析完成")
            return True

        elif args.auto_plan:
            if not args.quiet:
                print("📋 执行自动计划创建...")
            commands.execute_create_plan()
            if not args.quiet:
                print("✅ 合并计划创建完成")
            return True

        elif args.auto_assign:
            if not args.quiet:
                print("⚡ 执行自动任务分配...")
            commands.execute_auto_assign()
            if not args.quiet:
                print("✅ 任务分配完成")
            return True

        elif args.auto_workflow:
            if not args.quiet:
                print("🚀 执行自动完整流程...")
            # 执行完整流程：分析 -> 创建计划 -> 分配任务
            commands.execute_analyze_divergence()
            if not args.quiet:
                print("  ✅ 分叉分析完成")
            commands.execute_create_plan()
            if not args.quiet:
                print("  ✅ 合并计划创建完成")
            commands.execute_auto_assign()
            if not args.quiet:
                print("✅ 完整流程执行完成")
            return True

        return False  # 没有匹配的自动化参数

    except Exception as e:
        if not args.quiet:
            print(f"❌ 自动化执行失败: {e}")
        return False


def main():
    """主函数"""
    try:
        # 解析命令行参数
        args = parse_arguments()

        # 解析分支和配置
        source_branch, target_branch, config_manager = resolve_branches_and_config(args)

        # 如果是配置管理命令，直接返回
        if source_branch is None and target_branch is None:
            if args.show_config or args.reset_config:
                return  # 正常退出
            else:
                print("❌ 无法确定分支信息")
                sys.exit(1)

        # 创建主控制器
        orchestrator = GitMergeOrchestrator(
            source_branch=source_branch,
            target_branch=target_branch,
            repo_path=args.repo,
            max_files_per_group=args.max_files,
            processing_mode=args.processing_mode,
        )

        # 设置命令行指定的策略
        if args.strategy:
            strategy_map = {"legacy": "legacy", "standard": "standard"}
            if orchestrator.set_merge_strategy(strategy_map[args.strategy]):
                print(f"✅ 已设置合并策略为: {args.strategy}")
                # 如果有配置管理器且允许保存，更新策略到配置
                if config_manager and not args.no_save_config:
                    config_manager.update_config(merge_strategy=args.strategy)
            else:
                print(f"⚠️ 设置合并策略失败，使用默认策略")

        # 验证环境
        if not validate_environment(orchestrator):
            sys.exit(1)

        # 检查是否为非交互式自动化执行
        if args.auto_analyze or args.auto_plan or args.auto_assign or args.auto_workflow:
            if not args.quiet:
                # 简化的欢迎信息
                mode_info = orchestrator.get_processing_mode_info()
                print(f"🤖 Git Merge Orchestrator 非交互模式 (v2.2 - {mode_info['mode_name']})")
                print(f"源分支: {orchestrator.source_branch} → 目标分支: {orchestrator.target_branch}")
                print("=" * 60)

            # 执行非交互式功能
            success = execute_non_interactive(orchestrator, args)
            sys.exit(0 if success else 1)

        # 显示欢迎信息（交互式模式）
        show_welcome_banner(orchestrator, config_manager)

        # 启动扁平化菜单（交互式模式）
        menu_manager = FlatMenuManager(orchestrator)
        print("🚀 启动扁平化菜单界面...")
        menu_manager.run_interactive_menu()

    except KeyboardInterrupt:
        print("\n\n👋 用户中断，正在退出...")
        sys.exit(0)
    except Exception as e:
        DisplayHelper.print_error(f"程序运行出现错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
