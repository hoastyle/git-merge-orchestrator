"""
Git Merge Orchestrator - 主控制器（支持双版本）
整合所有模块，提供统一的API接口，支持Legacy和Standard两种合并策略
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from config import DEFAULT_MAX_FILES_PER_GROUP, DEFAULT_MAX_TASKS_PER_PERSON
from utils.file_helper import FileHelper
from ui.display_helper import DisplayHelper
from core.git_operations import GitOperations
from core.contributor_analyzer import ContributorAnalyzer
from core.optimized_contributor_analyzer import OptimizedContributorAnalyzer
from core.optimized_task_assigner import OptimizedTaskAssigner
from core.task_assigner import TaskAssigner
from core.merge_executor_factory import MergeExecutorFactory
from core.plan_manager import PlanManager


class GitMergeOrchestrator:
    """Git合并编排器主控制器 - 支持双版本合并策略"""

    def __init__(
        self,
        source_branch,
        target_branch,
        repo_path=".",
        max_files_per_group=DEFAULT_MAX_FILES_PER_GROUP,
    ):
        self.source_branch = source_branch
        self.target_branch = target_branch
        self.repo_path = Path(repo_path)
        self.max_files_per_group = max_files_per_group

        # 初始化核心组件
        self.git_ops = GitOperations(repo_path)
        self.file_helper = FileHelper(repo_path, max_files_per_group)
        self.contributor_analyzer = OptimizedContributorAnalyzer(self.git_ops)
        self.task_assigner = OptimizedTaskAssigner(self.contributor_analyzer)

        # 初始化合并执行器工厂
        self.merge_executor_factory = MergeExecutorFactory(repo_path)

        self.plan_manager = PlanManager(
            self.git_ops, self.file_helper, self.contributor_analyzer
        )

        # 缓存集成分支名
        self._integration_branch = None

        # 延迟加载交互式合并执行器（避免循环导入）
        self._interactive_executor = None

    @property
    def integration_branch(self):
        """获取集成分支名"""
        if self._integration_branch is None:
            plan = self.file_helper.load_plan()
            if plan:
                self._integration_branch = plan.get("integration_branch")
        return self._integration_branch

    @property
    def interactive_executor(self):
        """获取交互式合并执行器（延迟加载）"""
        if self._interactive_executor is None:
            try:
                from core.interactive_merge_executor import InteractiveMergeExecutor

                self._interactive_executor = InteractiveMergeExecutor(
                    self.git_ops, self.file_helper
                )
            except ImportError as e:
                DisplayHelper.print_error(f"无法加载交互式合并模块: {e}")
                return None
        return self._interactive_executor

    def get_current_merge_executor(self):
        """获取当前合并执行器实例"""
        return self.merge_executor_factory.create_executor(
            self.git_ops, self.file_helper
        )

    def get_merge_strategy_info(self):
        """获取当前合并策略信息"""
        return self.merge_executor_factory.get_status_info()

    def switch_merge_strategy(self):
        """交互式切换合并策略"""
        return self.merge_executor_factory.switch_mode_interactive()

    def set_merge_strategy(self, strategy):
        """设置合并策略"""
        try:
            self.merge_executor_factory.set_merge_mode(strategy)
            return True
        except ValueError as e:
            DisplayHelper.print_error(f"设置合并策略失败: {e}")
            return False

    def analyze_divergence(self):
        """分析分支分叉情况"""
        result = self.plan_manager.analyze_divergence(
            self.source_branch, self.target_branch
        )
        if result:
            self._integration_branch = result["integration_branch"]
        return result

    def create_merge_plan(self):
        """创建智能合并计划"""
        plan = self.plan_manager.create_merge_plan(
            self.source_branch, self.target_branch, self.max_files_per_group
        )
        if plan:
            self._integration_branch = plan["integration_branch"]
        return plan

    def auto_assign_tasks(
        self,
        exclude_authors=None,
        max_tasks_per_person=DEFAULT_MAX_TASKS_PER_PERSON,
        include_fallback=True,
    ):
        """智能自动分配任务（优化版）"""
        plan = self.file_helper.load_plan()
        if not plan:
            DisplayHelper.print_error("合并计划文件不存在，请先运行创建合并计划")
            return None

        # 使用优化版分配器
        result = self.task_assigner.turbo_auto_assign_tasks(
            plan, exclude_authors, max_tasks_per_person, include_fallback
        )

        if result:
            # 保存更新后的计划
            self.file_helper.save_plan(plan)

            # 显示性能优化报告
            if "performance_stats" in result:
                perf_report = self.task_assigner.get_optimization_report(
                    result["performance_stats"]
                )
                print(perf_report)

            # 原有的分配总结显示
            active_contributors = result["active_contributors"]
            inactive_contributors = result["inactive_contributors"]
            assignment_count = result["assignment_count"]
            unassigned_groups = result["unassigned_groups"]

            print(f"\n📊 自动分配总结:")
            print(f"🎯 活跃贡献者: {len(active_contributors)} 位")
            print(f"🚫 自动排除: {len(inactive_contributors)} 位（近3个月无提交）")
            print(f"🔧 手动排除: {len(exclude_authors or [])} 位")

            summary = DisplayHelper.format_assignment_summary(
                assignment_count, unassigned_groups
            )
            print(summary)

            DisplayHelper.print_success("涡轮增压自动分配完成")

        return plan

    def manual_assign_tasks(self, assignments):
        """手动分配任务"""
        plan = self.file_helper.load_plan()
        if not plan:
            DisplayHelper.print_error("合并计划文件不存在，请先运行创建合并计划")
            return None

        updated_plan = self.task_assigner.manual_assign_tasks(plan, assignments)
        self.file_helper.save_plan(updated_plan)

        DisplayHelper.print_success("任务分配完成")
        return updated_plan

    def check_status(self, show_full_names=False):
        """检查合并状态"""
        if show_full_names:
            self._show_full_group_names()
        else:
            self.plan_manager.check_status()

    def _show_full_group_names(self):
        """显示完整的组名列表"""
        plan = self.file_helper.load_plan()
        if not plan:
            DisplayHelper.print_error("合并计划文件不存在，请先运行创建合并计划")
            return

        print("📋 完整组名列表:")
        print("=" * 100)

        for i, group in enumerate(plan.get("groups", []), 1):
            group_name = group.get("name", "N/A")
            assignee = group.get("assignee", "未分配")
            file_count = group.get("file_count", len(group.get("files", [])))
            status = (
                "✅"
                if group.get("status") == "completed"
                else "🔄"
                if assignee != "未分配"
                else "⏳"
            )
            group_type = group.get("group_type", "unknown")

            print(f"{i:3d}. {status} {group_name}")
            print(f"     类型: {group_type} | 文件数: {file_count} | 负责人: {assignee}")

            # 显示分配原因（简短版）
            assignment_reason = group.get("assignment_reason", "未指定")
            if len(assignment_reason) > 80:
                assignment_reason = assignment_reason[:77] + "..."
            print(f"     原因: {assignment_reason}")
            print()

        # 显示统计摘要
        stats = self.file_helper.get_completion_stats(plan)
        completion_info = DisplayHelper.format_completion_stats(stats)
        print("=" * 100)
        print(completion_info)

        # 显示当前合并策略
        strategy_info = self.get_merge_strategy_info()
        print(f"📊 当前合并策略: {strategy_info['mode_name']}")

    def show_contributor_analysis(self):
        """显示贡献者分析报告"""
        plan = self.file_helper.load_plan()
        if not plan:
            DisplayHelper.print_error("合并计划文件不存在，请先运行创建合并计划")
            return

        DisplayHelper.print_section_header("👥 智能贡献者分析报告 (重点关注一年内活跃度)")
        print("💡 评分规则：一年内提交数 × 3 + 历史总提交数 × 1")
        print("🎯 分配策略：优先分配给近期活跃且熟悉相关文件的开发者")
        print("🚫 自动排除：近3个月无提交的人员")

        # 获取活跃贡献者信息
        active_contributors = self.contributor_analyzer.get_active_contributors(3)

        # 显示每个组的贡献者信息
        for group in plan["groups"]:
            print(
                f"\n📁 组: {group['name']} ({group.get('file_count', len(group['files']))} 文件)"
            )

            assignee = group.get("assignee", "未分配")
            fallback_reason = group.get("fallback_reason", "")

            if assignee != "未分配":
                if fallback_reason:
                    print(f" 当前分配: {assignee} [备选分配: {fallback_reason}]")
                else:
                    print(f" 当前分配: {assignee}")
            else:
                print(f" 当前分配: 未分配")

            if "contributors" in group and group["contributors"]:
                print(" 贡献者排名 (一年内|历史总计|综合得分|活跃状态):")
                sorted_contributors = sorted(
                    group["contributors"].items(),
                    key=lambda x: x[1]["score"] if isinstance(x[1], dict) else x[1],
                    reverse=True,
                )
                for i, (author, stats) in enumerate(sorted_contributors[:3], 1):
                    if isinstance(stats, dict):
                        recent = stats["recent_commits"]
                        total = stats["total_commits"]
                        score = stats["score"]

                        activity_info = DisplayHelper.get_activity_info(
                            recent, author in active_contributors
                        )
                        activity_display = (
                            f"{activity_info['icon']}{activity_info['name']}"
                        )

                        print(
                            f" {i}. {author}: {recent}|{total}|{score} {activity_display}"
                        )
                    else:
                        activity_display = (
                            "📊历史" if author in active_contributors else "💤静默"
                        )
                        print(f" {i}. {author}: ?|{stats}|{stats} {activity_display}")
            else:
                print(" ⚠️ 贡献者数据未分析，请先运行自动分配任务")

        # 显示全局贡献者排名
        all_contributors_global = self.contributor_analyzer.calculate_global_contributor_stats(
            plan
        )
        if all_contributors_global:
            print(f"\n🏆 全局贡献者智能排名 (基于一年内活跃度):")

            contrib_data = []
            sorted_global = sorted(
                all_contributors_global.items(),
                key=lambda x: x[1]["score"],
                reverse=True,
            )

            for i, (author, stats) in enumerate(sorted_global[:20], 1):
                recent = stats["recent_commits"]
                total = stats["total_commits"]
                score = stats["score"]
                contributed = stats["groups_contributed"]
                assigned = len(stats["groups_assigned"])
                is_active = stats["is_active"]

                activity_info = DisplayHelper.get_activity_info(recent, is_active)
                activity_display = f"{activity_info['icon']}{activity_info['name']}"

                assigned_display = f"{assigned}组" if assigned > 0 else "无"
                active_status = "✅" if is_active else "❌"

                contrib_data.append(
                    [
                        str(i),
                        author,
                        str(recent),
                        str(total),
                        str(score),
                        activity_display,
                        str(contributed),
                        assigned_display,
                        active_status,
                    ]
                )

            DisplayHelper.print_table("contributor_ranking", contrib_data)

            print(f"\n📊 活跃度说明 (基于一年内提交 + 近3个月活跃度):")
            print("🔥高: 15+次 📈中: 5-14次 📊低: 1-4次 📊近期: 近期有活动 💤静默: 近3个月无提交")
            print("✅: 近3个月活跃 ❌: 近3个月静默")
            print("\n🎯 建议: 优先将任务分配给✅且🔥📈级别的开发者，确保合并质量和效率")
        else:
            print("\n⚠️ 暂无贡献者数据，请先运行自动分配任务以分析贡献度")

    def view_group_details(self, group_name=None):
        """查看分组详细信息"""
        plan = self.file_helper.load_plan()
        if not plan:
            DisplayHelper.print_error("合并计划文件不存在，请先运行创建合并计划")
            return []

        if group_name:
            # 查看指定组的详细信息
            target_group = self.file_helper.find_group_by_name(plan, group_name)
            if not target_group:
                DisplayHelper.print_error(f"未找到组: {group_name}")
                return []

            DisplayHelper.display_group_detail(target_group, self.file_helper)
            return [target_group]
        else:
            # 交互式选择查看
            print("📋 可用分组列表:")

            table_data = []
            for i, group in enumerate(plan["groups"], 1):
                assignee = group.get("assignee", "未分配")
                status = (
                    "✅"
                    if group.get("status") == "completed"
                    else "🔄"
                    if assignee != "未分配"
                    else "⏳"
                )
                group_type = group.get("group_type", "unknown")
                file_count = group.get("file_count", len(group["files"]))

                table_data.append(
                    [
                        str(i),
                        group["name"],
                        group_type,
                        str(file_count),
                        assignee,
                        status,
                    ]
                )

            DisplayHelper.print_table("group_list", table_data)

            try:
                choice = input("请输入要查看的组序号 (回车返回): ").strip()
                if not choice:
                    return []

                index = int(choice) - 1
                if 0 <= index < len(plan["groups"]):
                    selected_group = plan["groups"][index]
                    DisplayHelper.display_group_detail(selected_group, self.file_helper)
                    return [selected_group]
                else:
                    DisplayHelper.print_error("无效的序号")
                    return []
            except ValueError:
                DisplayHelper.print_error("请输入有效的数字")
                return []

    def show_assignment_reasons(self):
        """显示所有组的分配原因分析"""
        plan = self.file_helper.load_plan()
        if not plan:
            DisplayHelper.print_error("合并计划文件不存在，请先运行创建合并计划")
            return

        DisplayHelper.print_section_header("📊 任务分配原因分析报告")

        # 统计分配原因类型
        reason_stats = self.contributor_analyzer.get_assignment_reason_stats(plan)

        print("📈 分配原因统计:")
        for reason_type, groups in reason_stats.items():
            print(f"   {reason_type}: {len(groups)} 个组")

        print()

        # 显示分配原因表格
        table_data = []
        for group in plan["groups"]:
            assignee = group.get("assignee", "未分配")
            file_count = group.get("file_count", len(group["files"]))
            assignment_reason = group.get("assignment_reason", "未指定")
            reason_type = DisplayHelper.categorize_assignment_reason(assignment_reason)

            # 截断过长的原因说明
            short_reason = (
                assignment_reason[:45] + "..."
                if len(assignment_reason) > 45
                else assignment_reason
            )

            table_data.append(
                [group["name"], assignee, str(file_count), reason_type, short_reason]
            )

        DisplayHelper.print_table("assignment_reasons", table_data)

        # 分类详细展示
        print(f"\n📋 分类详细分析:")
        for reason_type, groups in reason_stats.items():
            if not groups:
                continue

            print(f"\n🔍 {reason_type} ({len(groups)} 个组):")
            for group in groups[:5]:  # 只显示前5个
                assignee = group.get("assignee", "未分配")
                assignment_reason = group.get("assignment_reason", "未指定")
                print(f"   - {group['name']} → {assignee}")
                print(f"     原因: {assignment_reason}")

            if len(groups) > 5:
                print(f"   ... 还有 {len(groups) - 5} 个组")

    def search_assignee_tasks(self, assignee_name):
        """根据负责人搜索其负责的所有模块"""
        plan = self.file_helper.load_plan()
        if not plan:
            DisplayHelper.print_error("合并计划文件不存在，请先运行创建合并计划")
            return []

        assignee_groups = self.file_helper.get_assignee_groups(plan, assignee_name)
        total_files = sum(g.get("file_count", len(g["files"])) for g in assignee_groups)

        if not assignee_groups:
            print(f"📋 负责人 '{assignee_name}' 暂无分配的任务")
            return []

        print(f"👤 负责人: {assignee_name}")
        print(f"📊 总览: {len(assignee_groups)} 个组, {total_files} 个文件")

        # 构建任务表格数据
        table_data = []
        completed = 0
        pending = 0

        for group in assignee_groups:
            status = group.get("status", "pending")
            status_icon = "✅" if status == "completed" else "🔄"
            file_count = group.get("file_count", len(group["files"]))
            group_type = group.get("group_type", "unknown")
            assignment_reason = group.get("assignment_reason", "未指定")

            if status == "completed":
                completed += 1
            else:
                pending += 1

            # 截断长的分配原因
            short_reason = (
                assignment_reason[:35] + "..."
                if len(assignment_reason) > 35
                else assignment_reason
            )

            table_data.append(
                [group["name"], str(file_count), status_icon, group_type, short_reason]
            )

        DisplayHelper.print_table("assignee_tasks", table_data)
        print(f"📈 进度: {completed}/{len(assignee_groups)} 组已完成, {pending} 组待处理")

        # 显示详细文件列表
        if len(assignee_groups) <= 3:  # 只有少量组时显示详细信息
            print(f"\n📄 详细文件列表:")
            for i, group in enumerate(assignee_groups, 1):
                print(
                    f"\n{i}. 组: {group['name']} ({group.get('file_count', len(group['files']))} 文件)"
                )
                assignment_reason = group.get("assignment_reason", "未指定")
                print(f"   分配原因: {assignment_reason}")
                for file in group["files"][:5]:  # 最多显示5个文件
                    print(f"   - {file}")
                if len(group["files"]) > 5:
                    print(f"   ... 还有 {len(group['files']) - 5} 个文件")

        return assignee_groups

    def merge_group(self, group_name):
        """合并指定组的文件 - 根据当前策略选择执行器"""
        if not self.integration_branch:
            DisplayHelper.print_error("无法确定集成分支，请先创建合并计划")
            return False

        # 获取当前合并执行器
        merge_executor = self.get_current_merge_executor()
        strategy_info = self.get_merge_strategy_info()

        print(f"📊 当前合并策略: {strategy_info['mode_name']}")
        print(f"📝 策略说明: {strategy_info['description']}")

        return merge_executor.merge_group(
            group_name, self.source_branch, self.target_branch, self.integration_branch
        )

    def merge_assignee_tasks(self, assignee_name):
        """合并指定负责人的所有任务 - 根据当前策略选择执行器"""
        if not self.integration_branch:
            DisplayHelper.print_error("无法确定集成分支，请先创建合并计划")
            return False

        # 获取当前合并执行器
        merge_executor = self.get_current_merge_executor()
        strategy_info = self.get_merge_strategy_info()

        print(f"📊 当前合并策略: {strategy_info['mode_name']}")
        print(f"📝 策略说明: {strategy_info['description']}")

        return merge_executor.merge_assignee_tasks(
            assignee_name,
            self.source_branch,
            self.target_branch,
            self.integration_branch,
        )

    def interactive_merge_group(self, group_name):
        """交互式合并指定组"""
        if not self.integration_branch:
            DisplayHelper.print_error("无法确定集成分支，请先创建合并计划")
            return False

        if not self.interactive_executor:
            DisplayHelper.print_error("交互式合并模块不可用")
            return False

        return self.interactive_executor.interactive_merge_group(
            group_name, self.source_branch, self.target_branch, self.integration_branch
        )

    def mark_group_completed(self, group_name):
        """标记指定组为已完成"""
        return self.plan_manager.mark_group_completed(group_name)

    def mark_assignee_completed(self, assignee_name):
        """标记指定负责人的所有任务为已完成"""
        return self.plan_manager.mark_assignee_completed(assignee_name)

    def auto_check_remote_status(self):
        """自动检查远程分支状态"""
        return self.plan_manager.auto_check_remote_status()

    def finalize_merge(self):
        """完成最终合并 - 根据当前策略选择执行器"""
        if not self.integration_branch:
            DisplayHelper.print_error("无法确定集成分支，请先创建合并计划")
            return False

        # 获取当前合并执行器
        merge_executor = self.get_current_merge_executor()
        strategy_info = self.get_merge_strategy_info()

        print(f"📊 使用合并策略: {strategy_info['mode_name']}")

        return merge_executor.finalize_merge(self.integration_branch)

    def get_plan_summary(self):
        """获取计划摘要信息"""
        try:
            plan = self.file_helper.load_plan()
            if not plan:
                return None

            stats = self.file_helper.get_completion_stats(plan)
            workload = self.contributor_analyzer.get_workload_distribution(plan)
            strategy_info = self.get_merge_strategy_info()

            return {
                "plan": plan,
                "stats": stats,
                "workload": workload,
                "source_branch": self.source_branch,
                "target_branch": self.target_branch,
                "integration_branch": self.integration_branch,
                "merge_strategy": strategy_info,
            }
        except Exception as e:
            # 如果获取摘要失败，返回None而不是抛出异常
            return None

    def show_merge_strategy_status(self):
        """显示合并策略状态"""
        strategy_info = self.get_merge_strategy_info()
        available_modes = self.merge_executor_factory.list_available_modes()

        print("🔧 合并策略状态")
        print("=" * 80)
        print(f"📊 当前策略: {strategy_info['mode_name']}")
        print(f"📝 描述: {strategy_info['description']}")
        print(f"📁 配置文件: {strategy_info['config_file']}")
        print(f"💾 配置存在: {'✅' if strategy_info['config_exists'] else '❌'}")
        print()

        print("📋 可用策略:")
        for mode_info in available_modes:
            current_indicator = (
                " ← 当前" if mode_info["mode"] == strategy_info["current_mode"] else ""
            )
            print(f"  • {mode_info['name']}{current_indicator}")
            print(f"    {mode_info['description']}")
            print(f"    {mode_info['suitable']}")
            print()
