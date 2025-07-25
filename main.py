#!/usr/bin/env python3
"""
Git Merge Orchestrator - 主入口文件（支持双版本）
提供命令行界面和交互式菜单系统，支持Legacy和Standard两种合并策略
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from git_merge_orchestrator import GitMergeOrchestrator
from ui.display_helper import DisplayHelper


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Git大分叉智能分步合并工具 - 多人协作版（双策略支持）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py feature/big-feature main
  python main.py feature/big-feature main --max-files 8
  python main.py feature/big-feature main --repo /path/to/repo

功能特性:
  • 智能文件分组 - 按目录结构自动分组，每组最多5个文件
  • 贡献者分析 - 基于Git历史分析文件贡献者和活跃度
  • 自动任务分配 - 优先分配给近期活跃且熟悉相关文件的开发者
  • 双合并策略 - Legacy快速覆盖 vs Standard三路合并
  • 备选分配策略 - 文件级→目录级→根目录级的层次化分配
  • 批量操作支持 - 支持按负责人批量合并和状态管理
  • 进度跟踪 - 完整的任务状态跟踪和远程分支检测
  • 交互式合并 - 支持文件级策略选择，适用于大分叉场景

合并策略说明:
  Legacy模式: 快速覆盖，源分支内容直接覆盖目标分支，无冲突标记
  Standard模式: 标准Git三路合并，产生冲突标记 <<<<<<< ======= >>>>>>>
        """,
    )

    parser.add_argument("source_branch", help="源分支名称")
    parser.add_argument("target_branch", help="目标分支名称")
    parser.add_argument("--max-files", type=int, default=5, help="每组最大文件数 (默认: 5)")
    parser.add_argument("--repo", default=".", help="Git仓库路径 (默认: 当前目录)")
    parser.add_argument(
        "--strategy",
        choices=["legacy", "standard"],
        help="合并策略 (legacy: 快速覆盖, standard: 三路合并)",
    )
    parser.add_argument(
        "--version", action="version", version="Git Merge Orchestrator 2.2 (双策略版)"
    )

    return parser.parse_args()


def show_welcome_banner(orchestrator):
    """显示欢迎横幅"""
    print("🚀 Git大分叉智能分步合并工具 (双策略增强版)")
    print("=" * 80)
    print(f"源分支: {orchestrator.source_branch}")
    print(f"目标分支: {orchestrator.target_branch}")
    print(f"每组最大文件数: {orchestrator.max_files_per_group}")
    print(f"工作目录: {orchestrator.repo_path}")

    # 显示当前合并策略
    strategy_info = orchestrator.get_merge_strategy_info()
    print(f"🔧 当前合并策略: {strategy_info['mode_name']}")
    print(f"📝 策略说明: {strategy_info['description']}")

    # 显示计划摘要（如果存在）
    try:
        summary = orchestrator.get_plan_summary()
        if summary and summary.get("stats"):
            stats = summary["stats"]
            print(f"\n📊 当前计划状态:")
            print(f"   总分组: {stats.get('total_groups', 0)} 个")
            print(f"   总文件: {stats.get('total_files', 0)} 个")
            print(
                f"   已分配: {stats.get('assigned_groups', 0)} 组 ({stats.get('assigned_files', 0)} 文件)"
            )
            print(
                f"   已完成: {stats.get('completed_groups', 0)} 组 ({stats.get('completed_files', 0)} 文件)"
            )
            if summary.get("integration_branch"):
                print(f"   集成分支: {summary['integration_branch']}")
    except Exception as e:
        # 如果获取摘要失败，不影响主程序运行
        pass

    print("=" * 80)


def handle_auto_assign_menu(orchestrator):
    """处理自动分配菜单"""
    print("🤖 涡轮增压智能自动分配模式 (活跃度过滤+备选方案)")

    exclude_input = input("请输入要排除的作者列表 (用逗号分隔，回车跳过): ").strip()
    exclude_authors = (
        [name.strip() for name in exclude_input.split(",")] if exclude_input else []
    )

    max_tasks_input = input("每人最大任务数 (默认3): ").strip()
    max_tasks = int(max_tasks_input) if max_tasks_input.isdigit() else 3

    fallback_input = input("启用备选分配方案? (Y/n): ").strip().lower()
    include_fallback = fallback_input != "n"

    orchestrator.auto_assign_tasks(exclude_authors, max_tasks, include_fallback)


def handle_manual_assign_menu(orchestrator):
    """处理手动分配菜单"""
    assignments = {}
    print("请输入任务分配 (格式: 组名=负责人，输入空行结束):")
    while True:
        line = input().strip()
        if not line:
            break
        if "=" in line:
            group, assignee = line.split("=", 1)
            assignments[group.strip()] = assignee.strip()

    if assignments:
        orchestrator.manual_assign_tasks(assignments)
    else:
        DisplayHelper.print_warning("未输入任何分配信息")


def handle_group_details_menu(orchestrator):
    """处理查看分组详情菜单"""
    print("📋 查看分组详细信息:")
    print("a. 查看指定组详情")
    print("b. 交互式选择查看")
    print("c. 返回主菜单")

    sub_choice = input("请选择操作 (a-c): ").strip().lower()
    if sub_choice == "a":
        group_name = input("请输入组名: ").strip()
        orchestrator.view_group_details(group_name)
    elif sub_choice == "b":
        orchestrator.view_group_details()
    elif sub_choice == "c":
        return
    else:
        DisplayHelper.print_warning("无效选择")


def handle_status_management_menu(orchestrator):
    """处理状态管理菜单"""
    print("📋 完成状态管理:")
    print("a. 标记组完成")
    print("b. 标记负责人所有任务完成")
    print("c. 自动检查远程分支状态")
    print("d. 返回主菜单")

    sub_choice = input("请选择操作 (a-d): ").strip().lower()
    if sub_choice == "a":
        group_name = input("请输入已完成的组名: ").strip()
        orchestrator.mark_group_completed(group_name)
    elif sub_choice == "b":
        assignee_name = input("请输入负责人姓名: ").strip()
        orchestrator.mark_assignee_completed(assignee_name)
    elif sub_choice == "c":
        orchestrator.auto_check_remote_status()
    elif sub_choice == "d":
        return
    else:
        DisplayHelper.print_warning("无效选择")


def handle_interactive_merge_menu(orchestrator):
    """处理交互式合并菜单"""
    print("🎯 交互式智能合并:")
    print("a. 交互式合并指定组")
    print("b. 交互式合并指定负责人的所有任务 (开发中)")
    print("c. 返回主菜单")

    sub_choice = input("请选择操作 (a-c): ").strip().lower()
    if sub_choice == "a":
        group_name = input("请输入要交互式合并的组名: ").strip()
        if group_name:
            orchestrator.interactive_merge_group(group_name)
        else:
            DisplayHelper.print_warning("组名不能为空")

    elif sub_choice == "b":
        assignee_name = input("请输入负责人姓名: ").strip()
        if assignee_name:
            print("🔄 交互式批量合并功能开发中...")
            print("💡 建议：先使用单组交互式合并，积累经验后再批量处理")
            print("📋 您可以:")
            print("   1. 使用菜单7查看该负责人的所有任务")
            print("   2. 逐个使用交互式合并处理每个组")
            print("   3. 对于简单组，使用菜单6的自动合并")
        else:
            DisplayHelper.print_warning("负责人姓名不能为空")

    elif sub_choice == "c":
        return
    else:
        DisplayHelper.print_warning("无效选择")


def handle_cache_management_menu(orchestrator):
    """处理缓存管理菜单"""
    print("⚡ 缓存管理:")
    print("a. 查看缓存状态")
    print("b. 清理缓存")
    print("c. 强制重建缓存")
    print("d. 返回主菜单")

    sub_choice = input("请选择操作 (a-d): ").strip().lower()
    if sub_choice == "a":
        stats = orchestrator.contributor_analyzer.get_performance_stats()
        print("📊 缓存状态:")
        print(f"   缓存文件数: {stats['cached_files']}")
        print(f"   缓存目录数: {stats['cached_directories']}")
        print(f"   缓存文件存在: {'✅' if stats['cache_file_exists'] else '❌'}")
        print(f"   批量计算状态: {'✅' if stats['batch_computed'] else '❌'}")

    elif sub_choice == "b":
        cache_file = orchestrator.contributor_analyzer.cache_file
        if cache_file.exists():
            cache_file.unlink()
            print("✅ 缓存已清理")
        else:
            print("ℹ️ 缓存文件不存在")

    elif sub_choice == "c":
        # 清理内存缓存，强制重新计算
        orchestrator.contributor_analyzer._file_contributors_cache = {}
        orchestrator.contributor_analyzer._directory_contributors_cache = {}
        orchestrator.contributor_analyzer._batch_computed = False
        print("✅ 缓存已重置，下次分析将重新计算")

    elif sub_choice == "d":
        return
    else:
        DisplayHelper.print_warning("无效选择")


def handle_merge_strategy_menu(orchestrator):
    """处理合并策略管理菜单"""
    print("🔧 合并策略管理:")
    print("a. 查看当前策略状态")
    print("b. 切换合并策略")
    print("c. 策略对比说明")
    print("d. 返回主菜单")

    sub_choice = input("请选择操作 (a-d): ").strip().lower()
    if sub_choice == "a":
        orchestrator.show_merge_strategy_status()

    elif sub_choice == "b":
        if orchestrator.switch_merge_strategy():
            print("💡 策略切换成功，后续合并操作将使用新策略")
        else:
            print("⚠️ 策略切换取消")

    elif sub_choice == "c":
        print("📊 合并策略对比:")
        print("=" * 80)

        modes = orchestrator.merge_executor_factory.list_available_modes()
        for mode_info in modes:
            print(f"🔧 {mode_info['name']}")
            print(f"   描述: {mode_info['description']}")
            print(f"   优点: {', '.join(mode_info['pros'])}")
            print(f"   缺点: {', '.join(mode_info['cons'])}")
            print(f"   {mode_info['suitable']}")
            print()

        print("💡 选择建议:")
        print("   - 如果确信源分支内容正确，需要快速合并 → 选择Legacy模式")
        print("   - 如果需要精确控制，保证代码质量 → 选择Standard模式")
        print("   - 大型团队协作，多人修改同一文件 → 建议Standard模式")
        print("   - 小型团队，信任度高的合并 → 可以选择Legacy模式")

    elif sub_choice == "d":
        return
    else:
        DisplayHelper.print_warning("无效选择")


def show_updated_menu():
    """显示更新后的主菜单"""
    print("\n📋 可用操作:")
    print("1. 分析分支分叉")
    print("2. 创建智能合并计划")
    print("3. 🚀 涡轮增压自动分配任务 (优化版)")
    print("4. 手动分配任务")
    print("5. 查看贡献者智能分析")
    print("6. 合并指定组 (根据当前策略)")
    print("7. 搜索负责人任务")
    print("8. 合并指定负责人的所有任务 (根据当前策略)")
    print("9. 检查状态 (可选择显示模式)")
    print("10. 查看分组详细信息")
    print("11. 查看分配原因分析")
    print("12. 完成状态管理 (标记完成/检查远程状态)")
    print("13. 完成最终合并")
    print("14. 🎯 交互式智能合并 (策略选择)")
    print("15. ⚡ 缓存管理 (清理/状态)")
    print("16. 🔧 合并策略管理 (Legacy/Standard)")  # 新增
    print("0. 退出")


def run_interactive_menu(orchestrator):
    """运行交互式菜单"""
    while True:
        show_updated_menu()

        # 显示当前合并策略
        strategy_info = orchestrator.get_merge_strategy_info()
        print(f"\n📊 当前合并策略: {strategy_info['mode_name']}")

        try:
            choice = input("\n请选择操作 (0-16): ").strip()

            if choice == "0":
                print("👋 感谢使用Git Merge Orchestrator！")
                break

            elif choice == "1":
                orchestrator.analyze_divergence()

            elif choice == "2":
                orchestrator.create_merge_plan()

            elif choice == "3":
                handle_auto_assign_menu(orchestrator)

            elif choice == "4":
                handle_manual_assign_menu(orchestrator)

            elif choice == "5":
                orchestrator.show_contributor_analysis()

            elif choice == "6":
                group_name = input("请输入要合并的组名: ").strip()
                if group_name:
                    orchestrator.merge_group(group_name)
                else:
                    DisplayHelper.print_warning("组名不能为空")

            elif choice == "7":
                assignee_name = input("请输入负责人姓名: ").strip()
                if assignee_name:
                    orchestrator.search_assignee_tasks(assignee_name)
                else:
                    DisplayHelper.print_warning("负责人姓名不能为空")

            elif choice == "8":
                assignee_name = input("请输入要合并任务的负责人姓名: ").strip()
                if assignee_name:
                    orchestrator.merge_assignee_tasks(assignee_name)
                else:
                    DisplayHelper.print_warning("负责人姓名不能为空")

            elif choice == "9":
                print("📊 检查状态选项:")
                print("a. 标准表格显示")
                print("b. 完整组名显示")
                print("c. 返回主菜单")

                sub_choice = input("请选择显示模式 (a-c): ").strip().lower()
                if sub_choice == "a":
                    orchestrator.check_status(show_full_names=False)
                elif sub_choice == "b":
                    orchestrator.check_status(show_full_names=True)
                elif sub_choice == "c":
                    continue
                else:
                    DisplayHelper.print_warning("无效选择")

            elif choice == "10":
                handle_group_details_menu(orchestrator)

            elif choice == "11":
                orchestrator.show_assignment_reasons()

            elif choice == "12":
                handle_status_management_menu(orchestrator)

            elif choice == "13":
                orchestrator.finalize_merge()

            elif choice == "14":
                handle_interactive_merge_menu(orchestrator)

            elif choice == "15":
                handle_cache_management_menu(orchestrator)

            elif choice == "16":
                handle_merge_strategy_menu(orchestrator)

            else:
                DisplayHelper.print_warning("无效选择，请输入0-16之间的数字")

        except KeyboardInterrupt:
            print("\n\n👋 用户中断，正在退出...")
            break
        except Exception as e:
            DisplayHelper.print_error(f"操作过程中出现错误: {e}")
            print("请检查输入并重试，或选择其他操作")


def validate_environment(orchestrator):
    """验证运行环境"""
    # 检查是否在Git仓库中
    git_dir = orchestrator.repo_path / ".git"
    if not git_dir.exists():
        DisplayHelper.print_error("当前目录不是Git仓库")
        return False

    # 检查分支是否存在
    result = orchestrator.git_ops.run_command(
        f"git rev-parse --verify {orchestrator.source_branch}"
    )
    if result is None:
        DisplayHelper.print_error(f"源分支 '{orchestrator.source_branch}' 不存在")
        return False

    result = orchestrator.git_ops.run_command(
        f"git rev-parse --verify {orchestrator.target_branch}"
    )
    if result is None:
        DisplayHelper.print_error(f"目标分支 '{orchestrator.target_branch}' 不存在")
        return False

    return True


def main():
    """主函数"""
    try:
        # 解析命令行参数
        args = parse_arguments()

        # 创建主控制器
        orchestrator = GitMergeOrchestrator(
            source_branch=args.source_branch,
            target_branch=args.target_branch,
            repo_path=args.repo,
            max_files_per_group=args.max_files,
        )

        # 设置命令行指定的策略
        if args.strategy:
            strategy_map = {"legacy": "legacy", "standard": "standard"}
            if orchestrator.set_merge_strategy(strategy_map[args.strategy]):
                print(f"✅ 已设置合并策略为: {args.strategy}")
            else:
                print(f"⚠️ 设置合并策略失败，使用默认策略")

        # 验证环境
        if not validate_environment(orchestrator):
            sys.exit(1)

        # 显示欢迎信息
        show_welcome_banner(orchestrator)

        # 运行交互式菜单
        run_interactive_menu(orchestrator)

    except KeyboardInterrupt:
        print("\n\n👋 用户中断，正在退出...")
        sys.exit(0)
    except Exception as e:
        DisplayHelper.print_error(f"程序运行出现错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
