#!/usr/bin/env python3
"""
Git Merge Orchestrator - 主入口文件
提供命令行界面和交互式菜单系统
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
        description='Git大分叉智能分步合并工具 - 多人协作版',
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
  • 备选分配策略 - 文件级→目录级→根目录级的层次化分配
  • 批量操作支持 - 支持按负责人批量合并和状态管理
  • 进度跟踪 - 完整的任务状态跟踪和远程分支检测
        """
    )

    parser.add_argument('source_branch', help='源分支名称')
    parser.add_argument('target_branch', help='目标分支名称')
    parser.add_argument('--max-files', type=int, default=5,
                       help='每组最大文件数 (默认: 5)')
    parser.add_argument('--repo', default='.',
                       help='Git仓库路径 (默认: 当前目录)')
    parser.add_argument('--version', action='version', version='Git Merge Orchestrator 2.0')

    return parser.parse_args()


def show_welcome_banner(orchestrator):
    """显示欢迎横幅"""
    print("🚀 Git大分叉智能分步合并工具 (重构增强版)")
    print("="*80)
    print(f"源分支: {orchestrator.source_branch}")
    print(f"目标分支: {orchestrator.target_branch}")
    print(f"每组最大文件数: {orchestrator.max_files_per_group}")
    print(f"工作目录: {orchestrator.repo_path}")

    # 显示计划摘要（如果存在）
    try:
        summary = orchestrator.get_plan_summary()
        if summary and summary.get('stats'):
            stats = summary['stats']
            print(f"\n📊 当前计划状态:")
            print(f"   总分组: {stats.get('total_groups', 0)} 个")
            print(f"   总文件: {stats.get('total_files', 0)} 个")
            print(f"   已分配: {stats.get('assigned_groups', 0)} 组 ({stats.get('assigned_files', 0)} 文件)")
            print(f"   已完成: {stats.get('completed_groups', 0)} 组 ({stats.get('completed_files', 0)} 文件)")
            if summary.get('integration_branch'):
                print(f"   集成分支: {summary['integration_branch']}")
    except Exception as e:
        # 如果获取摘要失败，不影响主程序运行
        pass

    print("="*80)


def handle_auto_assign_menu(orchestrator):
    """处理自动分配菜单"""
    print("🤖 智能自动分配模式 (活跃度过滤+备选方案)")

    exclude_input = input("请输入要排除的作者列表 (用逗号分隔，回车跳过): ").strip()
    exclude_authors = [name.strip() for name in exclude_input.split(',')] if exclude_input else []

    max_tasks_input = input("每人最大任务数 (默认3): ").strip()
    max_tasks = int(max_tasks_input) if max_tasks_input.isdigit() else 3

    fallback_input = input("启用备选分配方案? (Y/n): ").strip().lower()
    include_fallback = fallback_input != 'n'

    orchestrator.auto_assign_tasks(exclude_authors, max_tasks, include_fallback)


def handle_manual_assign_menu(orchestrator):
    """处理手动分配菜单"""
    assignments = {}
    print("请输入任务分配 (格式: 组名=负责人，输入空行结束):")
    while True:
        line = input().strip()
        if not line:
            break
        if '=' in line:
            group, assignee = line.split('=', 1)
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
    if sub_choice == 'a':
        group_name = input("请输入组名: ").strip()
        orchestrator.view_group_details(group_name)
    elif sub_choice == 'b':
        orchestrator.view_group_details()
    elif sub_choice == 'c':
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
    if sub_choice == 'a':
        group_name = input("请输入已完成的组名: ").strip()
        orchestrator.mark_group_completed(group_name)
    elif sub_choice == 'b':
        assignee_name = input("请输入负责人姓名: ").strip()
        orchestrator.mark_assignee_completed(assignee_name)
    elif sub_choice == 'c':
        orchestrator.auto_check_remote_status()
    elif sub_choice == 'd':
        return
    else:
        DisplayHelper.print_warning("无效选择")


def run_interactive_menu(orchestrator):
    """运行交互式菜单"""
    while True:
        DisplayHelper.show_menu()

        try:
            choice = input("\n请选择操作 (0-13): ").strip()

            if choice == '0':
                print("👋 感谢使用Git Merge Orchestrator！")
                break

            elif choice == '1':
                orchestrator.analyze_divergence()

            elif choice == '2':
                orchestrator.create_merge_plan()

            elif choice == '3':
                handle_auto_assign_menu(orchestrator)

            elif choice == '4':
                handle_manual_assign_menu(orchestrator)

            elif choice == '5':
                orchestrator.show_contributor_analysis()

            elif choice == '6':
                group_name = input("请输入要合并的组名: ").strip()
                if group_name:
                    orchestrator.merge_group(group_name)
                else:
                    DisplayHelper.print_warning("组名不能为空")

            elif choice == '7':
                assignee_name = input("请输入负责人姓名: ").strip()
                if assignee_name:
                    orchestrator.search_assignee_tasks(assignee_name)
                else:
                    DisplayHelper.print_warning("负责人姓名不能为空")

            elif choice == '8':
                assignee_name = input("请输入要合并任务的负责人姓名: ").strip()
                if assignee_name:
                    orchestrator.merge_assignee_tasks(assignee_name)
                else:
                    DisplayHelper.print_warning("负责人姓名不能为空")

            elif choice == '9':
                orchestrator.check_status()

            elif choice == '10':
                handle_group_details_menu(orchestrator)

            elif choice == '11':
                orchestrator.show_assignment_reasons()

            elif choice == '12':
                handle_status_management_menu(orchestrator)

            elif choice == '13':
                orchestrator.finalize_merge()

            else:
                DisplayHelper.print_warning("无效选择，请输入0-13之间的数字")

        except KeyboardInterrupt:
            print("\n\n👋 用户中断，正在退出...")
            break
        except Exception as e:
            DisplayHelper.print_error(f"操作过程中出现错误: {e}")
            print("请检查输入并重试，或选择其他操作")


def validate_environment(orchestrator):
    """验证运行环境"""
    # 检查是否在Git仓库中
    git_dir = orchestrator.repo_path / '.git'
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
            max_files_per_group=args.max_files
        )

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