"""
Git Merge Orchestrator - 加速优化的任务分配器
结合优化的贡献者分析器，大幅提升任务分配速度
"""

from datetime import datetime
from config import DEFAULT_MAX_TASKS_PER_PERSON, DEFAULT_ACTIVE_MONTHS
from utils.performance_monitor import performance_monitor, global_performance_stats


class OptimizedTaskAssigner:
    """优化的任务分配器 - 结合批量分析和并行处理"""

    def __init__(self, optimized_contributor_analyzer):
        self.contributor_analyzer = optimized_contributor_analyzer

    @performance_monitor("涡轮增压自动分配")
    def turbo_auto_assign_tasks(
        self,
        plan,
        exclude_authors=None,
        max_tasks_per_person=DEFAULT_MAX_TASKS_PER_PERSON,
        include_fallback=True,
    ):
        """涡轮增压版自动分配任务 - 显著提升性能"""
        exclude_authors = exclude_authors or []
        start_time = datetime.now()

        print("🚀 启动涡轮增压自动分配模式...")
        print("⚡ 正在进行性能优化预处理...")

        # 加载持久化缓存
        cache_loaded = self.contributor_analyzer.load_persistent_cache()
        if cache_loaded:
            print("📦 成功加载贡献者缓存，大幅提升分析速度")

        print("💡 评分规则：一年内提交数 × 3 + 历史提交数 × 1")
        print("🔍 自动排除近3个月无提交的人员")

        # Step 1: 批量获取活跃贡献者（优化）
        active_contributors = self.contributor_analyzer.get_active_contributors(DEFAULT_ACTIVE_MONTHS)

        # Step 2: 批量获取所有贡献者（优化）
        all_contributors = self.contributor_analyzer.get_all_contributors()
        inactive_contributors = all_contributors - active_contributors

        if inactive_contributors:
            print(f"🚫 自动排除近3个月无提交的 {len(inactive_contributors)} 位贡献者:")
            for contributor in sorted(list(inactive_contributors))[:5]:
                print(f"   - {contributor}")
            if len(inactive_contributors) > 5:
                print(f"   ... 还有 {len(inactive_contributors) - 5} 位")

        # 合并排除列表
        all_excluded = set(exclude_authors) | inactive_contributors

        # Step 3: 并行分析所有组的贑献者信息（核心优化）
        print(f"⚡ 开始并行分析 {len(plan['groups'])} 个组的贡献者...")
        group_analysis_results = self.contributor_analyzer.parallel_analyze_groups(plan["groups"])

        # Step 4: 快速分配任务
        assignment_count = {}
        unassigned_groups = []

        print(f"🎯 开始智能任务分配...")

        for group in plan["groups"]:
            group_name = group["name"]
            print(f"  处理组: {group_name} ({group['file_count']} 个文件)")

            # 从并行分析结果中获取贡献者信息
            analysis_result = group_analysis_results.get(group_name, {})
            main_contributor = analysis_result.get("main_contributor")
            all_contributors = analysis_result.get("all_contributors", {})

            assigned = False
            assignment_reason = ""

            # 主要分配逻辑（优化版）
            if main_contributor and main_contributor not in all_excluded:
                current_count = assignment_count.get(main_contributor, 0)
                if current_count < max_tasks_per_person:
                    group["assignee"] = main_contributor
                    assignment_count[main_contributor] = current_count + 1
                    stats = all_contributors[main_contributor]
                    assignment_reason = f"基于文件贡献度直接分配 (一年内:{stats['recent_commits']}, 历史:{stats['total_commits']}, 得分:{stats['score']})"
                    print(f"    ✅ 分配给: {main_contributor} (得分: {stats['score']})")
                    assigned = True
                else:
                    # 负载均衡：寻找第二候选人
                    assigned = self._try_load_balance_assignment(
                        group,
                        all_contributors,
                        all_excluded,
                        assignment_count,
                        max_tasks_per_person,
                        main_contributor,
                    )

            # 备选分配策略（如果启用且需要）
            if not assigned and include_fallback:
                assigned = self._try_fallback_assignment(
                    group,
                    active_contributors,
                    all_excluded,
                    assignment_count,
                    max_tasks_per_person,
                )

            # 处理未分配的情况
            if not assigned:
                unassigned_groups.append(group["name"])
                assignment_reason = self._get_unassigned_reason(
                    main_contributor,
                    all_contributors,
                    all_excluded,
                    inactive_contributors,
                    max_tasks_per_person,
                )

            # 保存分配信息
            group["assignment_reason"] = assignment_reason
            group["contributors"] = all_contributors

        # 计算性能统计
        elapsed = (datetime.now() - start_time).total_seconds()
        perf_stats = self.contributor_analyzer.get_performance_stats()

        print(f"\n⚡ 涡轮增压分配完成！")
        print(f"🚀 总用时: {elapsed:.2f} 秒")
        print(f"📊 性能提升详情:")
        print(f"   - 缓存文件数: {perf_stats['cached_files']}")
        print(f"   - 缓存目录数: {perf_stats['cached_directories']}")
        print(f"   - 批量计算: {'✅' if perf_stats['batch_computed'] else '❌'}")

        return {
            "assignment_count": assignment_count,
            "unassigned_groups": unassigned_groups,
            "active_contributors": active_contributors,
            "inactive_contributors": inactive_contributors,
            "performance_stats": {
                "elapsed_seconds": elapsed,
                "cache_hit_rate": perf_stats["cached_files"] / len(plan.get("groups", [])) if plan.get("groups") else 0,
                **perf_stats,
            },
        }

    def _try_load_balance_assignment(
        self,
        group,
        all_contributors,
        all_excluded,
        assignment_count,
        max_tasks_per_person,
        main_contributor,
    ):
        """尝试负载均衡分配"""
        sorted_contributors = sorted(all_contributors.items(), key=lambda x: x[1]["score"], reverse=True)

        for author, stats in sorted_contributors[1:]:  # 跳过主要贡献者
            if author not in all_excluded and assignment_count.get(author, 0) < max_tasks_per_person:
                group["assignee"] = author
                assignment_count[author] = assignment_count.get(author, 0) + 1
                group["assignment_reason"] = (
                    f"负载均衡分配 (原推荐{main_contributor}已满负荷, 一年内:{stats['recent_commits']}, 历史:{stats['total_commits']}, 得分:{stats['score']})"
                )
                print(f"    ✅ 负载均衡分配给: {author} (得分: {stats['score']})")
                return True

        return False

    def _try_fallback_assignment(
        self,
        group,
        active_contributors,
        all_excluded,
        assignment_count,
        max_tasks_per_person,
    ):
        """尝试备选分配策略（优化版）"""
        print(f"    🔄 启用备选分配方案...")

        fallback_assignee, fallback_stats, fallback_source = self.contributor_analyzer.optimized_find_fallback_assignee(
            group["files"], active_contributors
        )

        if fallback_assignee and fallback_assignee not in all_excluded:
            current_count = assignment_count.get(fallback_assignee, 0)
            if current_count < max_tasks_per_person:
                group["assignee"] = fallback_assignee
                assignment_count[fallback_assignee] = current_count + 1
                group["fallback_reason"] = f"通过{fallback_source}目录分析分配"
                group["assignment_reason"] = (
                    f"备选目录分配 (来源:{fallback_source}, 一年内:{fallback_stats['recent_commits']}, 历史:{fallback_stats['total_commits']}, 得分:{fallback_stats['score']})"
                )
                print(
                    f"    ✅ 备选分配给: {fallback_assignee} (来源: {fallback_source}, 得分: {fallback_stats['score']})"
                )
                return True

        return False

    def _get_unassigned_reason(
        self,
        main_contributor,
        all_contributors,
        all_excluded,
        inactive_contributors,
        max_tasks_per_person,
    ):
        """获取未分配原因"""
        if main_contributor:
            if main_contributor in all_excluded:
                if main_contributor in inactive_contributors:
                    return f"主要贡献者{main_contributor}近3个月无活跃提交，已自动排除"
                else:
                    return f"主要贡献者{main_contributor}在手动排除列表中"
            else:
                return f"主要贡献者{main_contributor}已达最大任务数{max_tasks_per_person}"
        else:
            return "无法确定主要贡献者"

    def batch_get_assignment_suggestions(self, groups, active_contributors, max_tasks_per_person, current_assignments):
        """批量获取分配建议"""
        print(f"💡 正在为 {len(groups)} 个组生成分配建议...")

        # 批量分析所有组
        group_analysis_results = self.contributor_analyzer.parallel_analyze_groups(groups)

        suggestions = {}
        for group in groups:
            group_name = group["name"]
            analysis_result = group_analysis_results.get(group_name, {})
            all_contributors = analysis_result.get("all_contributors", {})
            main_contributor = analysis_result.get("main_contributor")

            group_suggestions = []
            if all_contributors:
                # 按得分排序
                sorted_contributors = sorted(all_contributors.items(), key=lambda x: x[1]["score"], reverse=True)

                for author, stats in sorted_contributors[:5]:  # 前5名
                    is_active = author in active_contributors
                    current_load = current_assignments.get(author, 0)
                    can_assign = current_load < max_tasks_per_person

                    suggestion = {
                        "author": author,
                        "stats": stats,
                        "is_active": is_active,
                        "current_load": current_load,
                        "can_assign": can_assign,
                        "is_main": author == main_contributor,
                    }
                    group_suggestions.append(suggestion)

            suggestions[group_name] = group_suggestions

        return suggestions

    def intelligent_rebalance_assignments(self, plan, max_tasks_per_person):
        """智能重新平衡任务分配"""
        print("🔄 开始智能重新平衡...")

        # 获取活跃贡献者
        active_contributors = self.contributor_analyzer.get_active_contributors()

        # 收集超载的任务
        overloaded_groups = []
        assignment_count = {}

        for group in plan["groups"]:
            assignee = group.get("assignee")
            if assignee and assignee != "未分配":
                assignment_count[assignee] = assignment_count.get(assignee, 0) + 1

                if assignment_count[assignee] > max_tasks_per_person:
                    overloaded_groups.append(group)
                    group["assignee"] = ""  # 重置分配
                    assignment_count[assignee] -= 1

        if not overloaded_groups:
            print("✅ 当前分配已平衡，无需调整")
            return plan

        print(f"📊 发现 {len(overloaded_groups)} 个超载任务，正在重新分配...")

        # 批量获取分配建议
        suggestions_map = self.batch_get_assignment_suggestions(
            overloaded_groups,
            active_contributors,
            max_tasks_per_person,
            assignment_count,
        )

        # 重新分配超载的任务
        for group in overloaded_groups:
            group_name = group["name"]
            suggestions = suggestions_map.get(group_name, [])

            for suggestion in suggestions:
                if suggestion["can_assign"] and suggestion["is_active"]:
                    group["assignee"] = suggestion["author"]
                    group["assignment_reason"] = "智能负载重平衡分配"
                    assignment_count[suggestion["author"]] = assignment_count.get(suggestion["author"], 0) + 1
                    print(f" ✅ 重新分配组 {group['name']} 给 {suggestion['author']}")
                    break
            else:
                print(f" ⚠️ 无法重新分配组 {group['name']}")

        print("✅ 智能重新平衡完成")
        return plan

    def get_optimization_report(self, performance_stats):
        """生成优化报告"""
        report = []
        report.append("📊 性能优化报告:")
        report.append(f"   ⚡ 总执行时间: {performance_stats['elapsed_seconds']:.2f} 秒")
        report.append(f"   📦 缓存命中率: {performance_stats['cache_hit_rate']:.1%}")
        report.append(f"   🗂️ 缓存文件数: {performance_stats['cached_files']}")
        report.append(f"   📁 缓存目录数: {performance_stats['cached_directories']}")

        if performance_stats["elapsed_seconds"] < 5:
            report.append("   🚀 性能等级: 极速")
        elif performance_stats["elapsed_seconds"] < 15:
            report.append("   ⚡ 性能等级: 快速")
        elif performance_stats["elapsed_seconds"] < 30:
            report.append("   📈 性能等级: 良好")
        else:
            report.append("   ⏰ 性能等级: 需要优化")

        return "\n".join(report)

    # 保持与原接口的兼容性
    def auto_assign_tasks(
        self,
        plan,
        exclude_authors=None,
        max_tasks_per_person=DEFAULT_MAX_TASKS_PER_PERSON,
        include_fallback=True,
    ):
        """自动分配任务（兼容接口，使用优化版本）"""
        return self.turbo_auto_assign_tasks(plan, exclude_authors, max_tasks_per_person, include_fallback)

    def manual_assign_tasks(self, plan, assignments):
        """手动分配任务（保持不变）"""
        for group_name, assignee in assignments.items():
            for group in plan["groups"]:
                if group["name"] == group_name:
                    group["assignee"] = assignee
                    group["assignment_reason"] = "手动分配"
                    break
        return plan

    def validate_assignment(self, plan, max_tasks_per_person):
        """验证分配结果（保持不变）"""
        assignment_count = {}
        issues = []

        for group in plan["groups"]:
            assignee = group.get("assignee")
            if assignee and assignee != "未分配":
                assignment_count[assignee] = assignment_count.get(assignee, 0) + 1

                if assignment_count[assignee] > max_tasks_per_person:
                    issues.append(
                        f"负责人 {assignee} 的任务数({assignment_count[assignee]})超过最大限制({max_tasks_per_person})"
                    )

        return {
            "assignment_count": assignment_count,
            "issues": issues,
            "is_valid": len(issues) == 0,
        }
