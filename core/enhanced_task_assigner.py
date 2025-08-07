"""
Git Merge Orchestrator - 增强任务分配器（v2.3）
结合增强的贡献者分析器，支持行数权重分析的智能任务分配
"""

from datetime import datetime
from config import (
    DEFAULT_MAX_TASKS_PER_PERSON,
    DEFAULT_ACTIVE_MONTHS,
    ENHANCED_CONTRIBUTOR_ANALYSIS,
)
from utils.performance_monitor import performance_monitor, global_performance_stats
from .enhanced_contributor_analyzer import EnhancedContributorAnalyzer


class EnhancedTaskAssigner:
    """增强的任务分配器 - 支持多维度权重分析"""

    def __init__(self, git_ops, fallback_assigner=None):
        self.git_ops = git_ops
        self.enhanced_analyzer = EnhancedContributorAnalyzer(git_ops)
        self.fallback_assigner = fallback_assigner  # 可选的回退分配器

        # 检查增强功能是否启用
        self.enhanced_enabled = self.enhanced_analyzer.is_enabled()

        if not self.enhanced_enabled:
            print("⚠️  增强任务分配器未启用，将使用基础分配逻辑")

    def is_enhanced_enabled(self):
        """检查增强功能是否启用"""
        return self.enhanced_enabled

    @performance_monitor("增强智能任务分配")
    def enhanced_auto_assign_tasks(
        self,
        plan,
        exclude_authors=None,
        max_tasks_per_person=None,
        enable_line_analysis=True,
        include_fallback=True,
    ):
        """
        增强的智能任务分配
        
        Args:
            plan: 合并计划对象
            exclude_authors: 排除的作者列表
            max_tasks_per_person: 每人最大任务数
            enable_line_analysis: 是否启用行数权重分析
            include_fallback: 是否包含回退分配
            
        Returns:
            tuple: (成功数量, 失败数量, 分配统计)
        """
        exclude_authors = exclude_authors or []
        max_tasks_per_person = max_tasks_per_person or DEFAULT_MAX_TASKS_PER_PERSON
        start_time = datetime.now()

        print("🚀 启动增强智能任务分配...")

        # 检查功能状态
        if not self.enhanced_enabled:
            print("⚠️  增强功能未启用，使用回退分配器")
            if self.fallback_assigner:
                return self.fallback_assigner.turbo_auto_assign_tasks(
                    plan, exclude_authors, max_tasks_per_person, include_fallback
                )
            else:
                return self._basic_assignment_fallback(
                    plan, exclude_authors, max_tasks_per_person
                )

        # 显示算法信息
        algorithm_config = self.enhanced_analyzer.get_algorithm_config()
        algorithm_type = ENHANCED_CONTRIBUTOR_ANALYSIS.get(
            "assignment_algorithm", "comprehensive"
        )
        print(f"🧠 使用 {algorithm_type} 算法进行智能分析")
        print(f"⚡ 行数权重分析: {'启用' if enable_line_analysis else '禁用'}")

        # 特性说明
        features = []
        if algorithm_config.get("use_line_weight", False):
            features.append("行数权重")
        if algorithm_config.get("use_time_weight", False):
            features.append("时间衰减")
        if algorithm_config.get("use_consistency_weight", False):
            features.append("一致性评分")
        if algorithm_config.get("use_file_relationship", False):
            features.append("文件关联")

        if features:
            print(f"🎯 启用特性: {', '.join(features)}")

        # 获取活跃贡献者
        active_contributors = self.git_ops.get_active_contributors(
            DEFAULT_ACTIVE_MONTHS
        )

        # 处理不同的处理模式
        processing_mode = getattr(plan, "processing_mode", "file_level")

        if processing_mode == "file_level":
            return self._assign_file_level_enhanced(
                plan,
                exclude_authors,
                max_tasks_per_person,
                enable_line_analysis,
                active_contributors,
                start_time,
            )
        else:
            return self._assign_group_level_enhanced(
                plan,
                exclude_authors,
                max_tasks_per_person,
                enable_line_analysis,
                active_contributors,
                start_time,
            )

    def _assign_file_level_enhanced(
        self,
        plan,
        exclude_authors,
        max_tasks_per_person,
        enable_line_analysis,
        active_contributors,
        start_time,
    ):
        """文件级增强分配"""
        files = getattr(plan, "files", [])
        if not files:
            print("❌ 无文件需要分配")
            return 0, 0, {}

        print(f"📁 准备分配 {len(files)} 个文件...")

        # 提取文件路径
        file_paths = [file_info.get("path", "") for file_info in files]
        file_paths = [path for path in file_paths if path]

        if not file_paths:
            print("❌ 无有效文件路径")
            return 0, 0, {}

        # 批量分析文件贡献者
        print("🔍 正在进行批量增强贡献者分析...")
        batch_contributors = self.enhanced_analyzer.analyze_contributors_batch(
            file_paths, enable_line_analysis=enable_line_analysis
        )

        # 执行文件分配
        success_count = 0
        failed_count = 0
        assignment_stats = {
            "total_files": len(files),
            "analyzed_files": len(batch_contributors),
            "active_contributors": len(active_contributors),
            "assignment_reasons": {},
            "algorithm_type": ENHANCED_CONTRIBUTOR_ANALYSIS.get(
                "assignment_algorithm", "comprehensive"
            ),
        }

        # 跟踪每人的任务数
        person_task_count = {}

        for file_info in files:
            file_path = file_info.get("path", "")
            if not file_path:
                failed_count += 1
                continue

            contributors = batch_contributors.get(file_path, {})

            # 获取最佳分配对象
            best_author, author_info, reason = self.enhanced_analyzer.get_best_assignee(
                contributors, exclude_inactive=True
            )

            if not best_author or best_author in exclude_authors:
                # 尝试回退分配
                if include_fallback:
                    best_author, reason = self._fallback_assignment(
                        file_path, exclude_authors
                    )

                if not best_author:
                    file_info["assignee"] = "未分配"
                    file_info["status"] = "pending"
                    file_info["assignment_reason"] = "无可用贡献者"
                    failed_count += 1
                    continue

            # 检查任务数量限制
            current_tasks = person_task_count.get(best_author, 0)
            if current_tasks >= max_tasks_per_person:
                # 寻找替代分配
                alternative_assigned = self._find_alternative_assignee(
                    contributors,
                    exclude_authors,
                    person_task_count,
                    max_tasks_per_person,
                )

                if alternative_assigned:
                    best_author, reason = alternative_assigned
                else:
                    file_info["assignee"] = "未分配"
                    file_info["status"] = "pending"
                    file_info["assignment_reason"] = "超出任务限额"
                    failed_count += 1
                    continue

            # 执行分配
            file_info["assignee"] = best_author
            file_info["status"] = "assigned"
            file_info["assignment_reason"] = reason

            # 更新统计
            person_task_count[best_author] = person_task_count.get(best_author, 0) + 1
            assignment_stats["assignment_reasons"][file_path] = reason
            success_count += 1

        # 分配完成统计
        elapsed = (datetime.now() - start_time).total_seconds()

        print(f"\n✅ 增强任务分配完成!")
        print(f"📊 分配统计: 成功 {success_count}, 失败 {failed_count}, 用时 {elapsed:.2f}s")
        print(f"👥 涉及 {len(person_task_count)} 位贡献者")

        # 显示负载分布
        self._show_workload_distribution(person_task_count)

        assignment_stats.update(
            {
                "success_count": success_count,
                "failed_count": failed_count,
                "elapsed_time": elapsed,
                "contributors_involved": len(person_task_count),
                "workload_distribution": person_task_count,
            }
        )

        return success_count, failed_count, assignment_stats

    def _assign_group_level_enhanced(
        self,
        plan,
        exclude_authors,
        max_tasks_per_person,
        enable_line_analysis,
        active_contributors,
        start_time,
    ):
        """组级增强分配（向后兼容）"""
        groups = getattr(plan, "groups", [])
        if not groups:
            print("❌ 无分组需要分配")
            return 0, 0, {}

        print(f"📁 准备分配 {len(groups)} 个组...")

        success_count = 0
        failed_count = 0
        assignment_stats = {
            "total_groups": len(groups),
            "active_contributors": len(active_contributors),
            "assignment_reasons": {},
            "algorithm_type": ENHANCED_CONTRIBUTOR_ANALYSIS.get(
                "assignment_algorithm", "comprehensive"
            ),
        }

        person_task_count = {}

        for group in groups:
            group_name = group.get("name", "")
            group_files = group.get("files", [])

            if not group_files:
                failed_count += 1
                continue

            # 分析组内文件的贡献者
            batch_contributors = self.enhanced_analyzer.analyze_contributors_batch(
                group_files, enable_line_analysis=enable_line_analysis
            )

            # 合并组级贡献者统计
            group_contributors = self._merge_group_contributors(batch_contributors)

            # 获取最佳分配对象
            best_author, author_info, reason = self.enhanced_analyzer.get_best_assignee(
                group_contributors, exclude_inactive=True
            )

            if not best_author or best_author in exclude_authors:
                if include_fallback:
                    best_author, reason = self._fallback_group_assignment(
                        group_name, exclude_authors
                    )

                if not best_author:
                    group["assignee"] = "未分配"
                    group["status"] = "pending"
                    group["assignment_reason"] = "无可用贡献者"
                    failed_count += 1
                    continue

            # 检查任务数量限制
            current_tasks = person_task_count.get(best_author, 0)
            if current_tasks >= max_tasks_per_person:
                alternative_assigned = self._find_alternative_assignee(
                    group_contributors,
                    exclude_authors,
                    person_task_count,
                    max_tasks_per_person,
                )

                if alternative_assigned:
                    best_author, reason = alternative_assigned
                else:
                    group["assignee"] = "未分配"
                    group["status"] = "pending"
                    group["assignment_reason"] = "超出任务限额"
                    failed_count += 1
                    continue

            # 执行分配
            group["assignee"] = best_author
            group["status"] = "assigned"
            group["assignment_reason"] = reason

            person_task_count[best_author] = person_task_count.get(best_author, 0) + 1
            assignment_stats["assignment_reasons"][group_name] = reason
            success_count += 1

        # 完成统计
        elapsed = (datetime.now() - start_time).total_seconds()

        print(f"\n✅ 增强组级任务分配完成!")
        print(f"📊 分配统计: 成功 {success_count}, 失败 {failed_count}, 用时 {elapsed:.2f}s")
        print(f"👥 涉及 {len(person_task_count)} 位贡献者")

        self._show_workload_distribution(person_task_count)

        assignment_stats.update(
            {
                "success_count": success_count,
                "failed_count": failed_count,
                "elapsed_time": elapsed,
                "contributors_involved": len(person_task_count),
                "workload_distribution": person_task_count,
            }
        )

        return success_count, failed_count, assignment_stats

    def _merge_group_contributors(self, batch_contributors):
        """合并组内文件的贡献者统计"""
        merged_contributors = {}

        for file_path, contributors in batch_contributors.items():
            for author, info in contributors.items():
                if author not in merged_contributors:
                    merged_contributors[author] = {
                        "total_commits": 0,
                        "recent_commits": 0,
                        "total_changes": 0,
                        "total_additions": 0,
                        "total_deletions": 0,
                        "score": 0,
                        "enhanced_score": 0,
                        "files_contributed": [],
                    }

                # 合并统计
                merged = merged_contributors[author]
                merged["total_commits"] += info.get("total_commits", 0)
                merged["recent_commits"] += info.get("recent_commits", 0)
                merged["total_changes"] += info.get("total_changes", 0)
                merged["total_additions"] += info.get("total_additions", 0)
                merged["total_deletions"] += info.get("total_deletions", 0)
                merged["enhanced_score"] += info.get("enhanced_score", 0)
                merged["files_contributed"].append(file_path)

        return merged_contributors

    def _find_alternative_assignee(
        self, contributors, exclude_authors, person_task_count, max_tasks
    ):
        """寻找替代分配对象"""
        ranking = self.enhanced_analyzer.get_contributor_ranking(contributors)

        for author, info in ranking:
            if (
                author not in exclude_authors
                and person_task_count.get(author, 0) < max_tasks
            ):
                reason = (
                    self.enhanced_analyzer._generate_assignment_reason(author, info)
                    + "（负载均衡分配）"
                )
                return (author, reason)

        return None

    def _fallback_assignment(self, file_path, exclude_authors):
        """单文件回退分配"""
        # 尝试目录级分析
        import os

        directory = os.path.dirname(file_path)

        if directory:
            dir_contributors = self.git_ops.get_directory_contributors(directory)
            if dir_contributors:
                # 获取最高分且不在排除列表的贡献者
                sorted_contributors = sorted(
                    dir_contributors.items(),
                    key=lambda x: x[1].get("score", 0),
                    reverse=True,
                )

                for author, info in sorted_contributors:
                    if author not in exclude_authors:
                        return author, "目录级回退分配"

        return None, "回退分配失败"

    def _fallback_group_assignment(self, group_name, exclude_authors):
        """组级回退分配"""
        # 使用组名作为路径进行目录级分析
        dir_contributors = self.git_ops.get_directory_contributors(group_name)
        if dir_contributors:
            sorted_contributors = sorted(
                dir_contributors.items(),
                key=lambda x: x[1].get("score", 0),
                reverse=True,
            )

            for author, info in sorted_contributors:
                if author not in exclude_authors:
                    return author, "组级回退分配"

        return None, "回退分配失败"

    def _show_workload_distribution(self, person_task_count):
        """显示工作负载分布"""
        if not person_task_count:
            return

        print("\n👥 工作负载分布:")
        sorted_workload = sorted(
            person_task_count.items(), key=lambda x: x[1], reverse=True
        )

        for author, count in sorted_workload[:10]:  # 只显示前10名
            print(f"  📋 {author}: {count} 个任务")

        if len(sorted_workload) > 10:
            print(f"  ... 另外 {len(sorted_workload) - 10} 位贡献者")

    def _basic_assignment_fallback(self, plan, exclude_authors, max_tasks_per_person):
        """基础分配回退（当增强功能不可用时）"""
        print("⚠️  使用基础分配逻辑")

        # 这里可以调用原有的基础分配逻辑
        # 或者返回最小化的分配结果

        processing_mode = getattr(plan, "processing_mode", "file_level")
        items = getattr(
            plan, "files" if processing_mode == "file_level" else "groups", []
        )

        # 简单的轮询分配
        active_contributors = self.git_ops.get_active_contributors(
            DEFAULT_ACTIVE_MONTHS
        )
        available_contributors = [
            c for c in active_contributors if c not in exclude_authors
        ]

        if not available_contributors:
            return 0, len(items), {"error": "无可用贡献者"}

        success_count = 0
        for i, item in enumerate(items):
            assignee = available_contributors[i % len(available_contributors)]
            item["assignee"] = assignee
            item["status"] = "assigned"
            item["assignment_reason"] = "基础轮询分配"
            success_count += 1

        return (
            success_count,
            0,
            {"basic_assignment": True, "contributors": len(available_contributors)},
        )

    def get_assignment_analysis_report(self, plan):
        """获取分配分析报告"""
        processing_mode = getattr(plan, "processing_mode", "file_level")
        items = getattr(
            plan, "files" if processing_mode == "file_level" else "groups", []
        )

        report = {
            "total_items": len(items),
            "assigned_items": 0,
            "unassigned_items": 0,
            "contributors_involved": set(),
            "assignment_reasons": {},
            "enhanced_analysis_used": self.enhanced_enabled,
        }

        for item in items:
            assignee = item.get("assignee")
            if assignee and assignee != "未分配":
                report["assigned_items"] += 1
                report["contributors_involved"].add(assignee)
            else:
                report["unassigned_items"] += 1

            reason = item.get("assignment_reason", "unknown")
            report["assignment_reasons"][reason] = (
                report["assignment_reasons"].get(reason, 0) + 1
            )

        report["contributors_involved"] = len(report["contributors_involved"])

        return report
