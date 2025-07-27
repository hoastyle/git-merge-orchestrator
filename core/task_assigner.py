"""
Git Merge Orchestrator - 任务分配管理
负责智能任务分配逻辑和分配策略
"""

from config import DEFAULT_MAX_TASKS_PER_PERSON, DEFAULT_ACTIVE_MONTHS


class TaskAssigner:
    """任务分配管理器"""

    def __init__(self, contributor_analyzer):
        self.contributor_analyzer = contributor_analyzer

    def auto_assign_tasks(
        self,
        plan,
        exclude_authors=None,
        max_tasks_per_person=DEFAULT_MAX_TASKS_PER_PERSON,
        include_fallback=True,
    ):
        """基于综合贡献度（提交次数+修改行数）自动分配合并任务，支持备选方案和活跃度过滤"""
        exclude_authors = exclude_authors or []

        print("🤖 正在基于综合贡献度（提交次数+修改行数）自动分配任务...")
        print("💡 评分规则：近期提交×2 + 近期行数×0.1 + 历史提交×1 + 历史行数×0.05")
        print("🔍 自动排除近3个月无提交的人员")

        # 获取活跃贡献者
        active_contributors = self.contributor_analyzer.get_active_contributors(DEFAULT_ACTIVE_MONTHS)

        # 自动添加不活跃的人员到排除列表
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

        assignment_count = {}
        unassigned_groups = []

        for group in plan["groups"]:
            print(f"\n分析组: {group['name']} ({group['file_count']} 个文件)")

            # 获取主要贡献者（基于综合评分）
            main_contributor, all_contributors = self.contributor_analyzer.get_group_main_contributor(group["files"])

            assigned = False
            assignment_reason = ""

            if main_contributor and main_contributor not in all_excluded:
                # 检查负载均衡
                current_count = assignment_count.get(main_contributor, 0)
                if current_count < max_tasks_per_person:
                    group["assignee"] = main_contributor
                    assignment_count[main_contributor] = current_count + 1
                    stats = all_contributors[main_contributor]
                    assignment_reason = f"基于综合贡献度直接分配 (近期提交:{stats.get('recent_commits', 0)}, 近期行数:{stats.get('recent_lines', 0)}, 历史提交:{stats.get('total_commits', 0)}, 历史行数:{stats.get('total_lines', 0)}, 综合得分:{stats.get('score', 0):.1f})"
                    print(f" ✅ 分配给: {main_contributor}")
                    print(
                        f" 综合统计: 近期提交{stats.get('recent_commits', 0)}, 近期行数{stats.get('recent_lines', 0)}, 历史提交{stats.get('total_commits', 0)}, 历史行数{stats.get('total_lines', 0)}, 综合得分{stats.get('score', 0):.1f}"
                    )
                    assigned = True
                else:
                    # 找第二合适的人选
                    sorted_contributors = sorted(
                        all_contributors.items(),
                        key=lambda x: x[1]["score"],
                        reverse=True,
                    )
                    for author, stats in sorted_contributors[1:]:
                        if author not in all_excluded and assignment_count.get(author, 0) < max_tasks_per_person:
                            group["assignee"] = author
                            assignment_count[author] = assignment_count.get(author, 0) + 1
                            assignment_reason = f"负载均衡分配 (原推荐{main_contributor}已满负荷, 近期提交:{stats.get('recent_commits', 0)}, 近期行数:{stats.get('recent_lines', 0)}, 历史提交:{stats.get('total_commits', 0)}, 历史行数:{stats.get('total_lines', 0)}, 综合得分:{stats.get('score', 0):.1f})"
                            print(f" ✅ 分配给: {author}")
                            print(
                                f" 综合统计: 近期提交{stats.get('recent_commits', 0)}, 近期行数{stats.get('recent_lines', 0)}, 历史提交{stats.get('total_commits', 0)}, 历史行数{stats.get('total_lines', 0)}, 综合得分{stats.get('score', 0):.1f}"
                            )
                            print(f" (原推荐 {main_contributor} 已满负荷)")
                            assigned = True
                            break

            # 如果还未分配且启用备选方案，尝试目录级分配
            if not assigned and include_fallback:
                print(f" 🔄 启用备选分配方案...")
                fallback_assignee, fallback_stats, fallback_source = self.contributor_analyzer.find_fallback_assignee(
                    group["files"], active_contributors
                )

                if fallback_assignee and fallback_assignee not in all_excluded:
                    current_count = assignment_count.get(fallback_assignee, 0)
                    if current_count < max_tasks_per_person:
                        group["assignee"] = fallback_assignee
                        assignment_count[fallback_assignee] = current_count + 1
                        group["fallback_reason"] = f"通过{fallback_source}目录分析分配"
                        assignment_reason = (
                            f"备选目录分配 (来源:{fallback_source}, 综合得分:{fallback_stats.get('score', 0):.1f})"
                        )
                        print(f" ✅ 备选分配给: {fallback_assignee} (来源: {fallback_source})")
                        print(f" 目录贡献 - 综合得分: {fallback_stats.get('score', 0):.1f}")
                        assigned = True

            if not assigned:
                unassigned_groups.append(group["name"])
                if main_contributor:
                    if main_contributor in all_excluded:
                        if main_contributor in inactive_contributors:
                            assignment_reason = f"主要贡献者{main_contributor}近3个月无活跃提交，已自动排除"
                            print(f" ⚠️ 主要贡献者 {main_contributor} 近3个月无活跃提交，已自动排除")
                            group["notes"] = f"建议: {main_contributor} (近期活跃度不足，已自动排除)"
                        else:
                            assignment_reason = f"主要贡献者{main_contributor}在手动排除列表中"
                            print(f" ⚠️ 主要贡献者 {main_contributor} 在手动排除列表中")
                            main_stats = all_contributors[main_contributor]
                            group["notes"] = (
                                f"建议: {main_contributor} (综合得分:{main_stats.get('score', 0):.1f}) 已手动排除"
                            )
                    else:
                        assignment_reason = f"主要贡献者{main_contributor}已达最大任务数{max_tasks_per_person}"
                        main_stats = all_contributors[main_contributor]
                        group["notes"] = (
                            f"建议: {main_contributor} (综合得分:{main_stats.get('score', 0):.1f}) 但已达最大任务数"
                        )
                        print(f" ⚠️ 主要贡献者 {main_contributor} 已达最大任务数")
                else:
                    assignment_reason = "无法确定主要贡献者"
                    print(f" ⚠️ 无法确定主要贡献者，请手动分配")
                    group["notes"] = "无法确定主要贡献者"

            # 保存分配原因和贡献者信息
            group["assignment_reason"] = assignment_reason
            group["contributors"] = all_contributors

        return {
            "assignment_count": assignment_count,
            "unassigned_groups": unassigned_groups,
            "active_contributors": active_contributors,
            "inactive_contributors": inactive_contributors,
        }

    def manual_assign_tasks(self, plan, assignments):
        """手动分配合并任务"""
        for group_name, assignee in assignments.items():
            for group in plan["groups"]:
                if group["name"] == group_name:
                    group["assignee"] = assignee
                    group["assignment_reason"] = "手动分配"
                    break

        return plan

    def get_assignment_suggestions(self, group, active_contributors, max_tasks_per_person, current_assignments):
        """获取分配建议"""
        main_contributor, all_contributors = self.contributor_analyzer.get_group_main_contributor(group["files"])

        suggestions = []

        if not all_contributors:
            return suggestions

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
            suggestions.append(suggestion)

        return suggestions

    def validate_assignment(self, plan, max_tasks_per_person):
        """验证分配结果"""
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

    def rebalance_assignments(self, plan, max_tasks_per_person):
        """重新平衡任务分配"""
        validation_result = self.validate_assignment(plan, max_tasks_per_person)

        if validation_result["is_valid"]:
            return plan

        print("🔄 检测到负载不均衡，正在重新分配...")

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

        # 重新分配超载的任务
        for group in overloaded_groups:
            suggestions = self.get_assignment_suggestions(
                group, active_contributors, max_tasks_per_person, assignment_count
            )

            for suggestion in suggestions:
                if suggestion["can_assign"] and suggestion["is_active"]:
                    group["assignee"] = suggestion["author"]
                    group["assignment_reason"] = "负载重平衡分配"
                    assignment_count[suggestion["author"]] = assignment_count.get(suggestion["author"], 0) + 1
                    print(f" ✅ 重新分配组 {group['name']} 给 {suggestion['author']}")
                    break
            else:
                print(f" ⚠️ 无法重新分配组 {group['name']}")

        return plan
