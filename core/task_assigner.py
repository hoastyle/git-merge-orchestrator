"""
Git Merge Orchestrator - 任务分配管理
负责智能任务分配逻辑和分配策略
"""

from config import DEFAULT_MAX_TASKS_PER_PERSON, DEFAULT_ACTIVE_MONTHS, ASSIGNMENT_STRATEGY


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
        """智能自动分配合并任务（支持文件级分配）"""
        exclude_authors = exclude_authors or []

        # 检查是否启用文件级分配
        if ASSIGNMENT_STRATEGY.get("file_level_assignment", False):
            print("🎯 启用文件级智能分配模式...")
            return self._file_level_auto_assign(plan, exclude_authors, max_tasks_per_person, include_fallback)
        else:
            print("📁 使用传统组级分配模式...")
            return self._group_level_auto_assign(plan, exclude_authors, max_tasks_per_person, include_fallback)

    def _group_level_auto_assign(
        self,
        plan,
        exclude_authors=None,
        max_tasks_per_person=DEFAULT_MAX_TASKS_PER_PERSON,
        include_fallback=True,
    ):
        """传统组级自动分配（原有逻辑）"""
        exclude_authors = exclude_authors or []

        print("🤖 正在基于一年内贡献度自动分配任务...")
        print("💡 评分规则：一年内提交数 × 3 + 历史提交数 × 1")
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

            # 获取主要贡献者（重点关注一年内）
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
                    assignment_reason = f"基于文件贡献度直接分配 (一年内:{stats['recent_commits']}, 历史:{stats['total_commits']}, 得分:{stats['score']})"
                    print(f" ✅ 分配给: {main_contributor}")
                    print(
                        f" 一年内提交: {stats['recent_commits']}, 历史提交: {stats['total_commits']}, 综合得分: {stats['score']}"
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
                            assignment_reason = f"负载均衡分配 (原推荐{main_contributor}已满负荷, 一年内:{stats['recent_commits']}, 历史:{stats['total_commits']}, 得分:{stats['score']})"
                            print(f" ✅ 分配给: {author}")
                            print(
                                f" 一年内提交: {stats['recent_commits']}, 历史提交: {stats['total_commits']}, 综合得分: {stats['score']}"
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
                        assignment_reason = f"备选目录分配 (来源:{fallback_source}, 一年内:{fallback_stats['recent_commits']}, 历史:{fallback_stats['total_commits']}, 得分:{fallback_stats['score']})"
                        print(f" ✅ 备选分配给: {fallback_assignee} (来源: {fallback_source})")
                        print(
                            f" 目录贡献 - 一年内: {fallback_stats['recent_commits']}, 历史: {fallback_stats['total_commits']}, 得分: {fallback_stats['score']}"
                        )
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
                                f"建议: {main_contributor} (近期:{main_stats['recent_commits']},历史:{main_stats['total_commits']},得分:{main_stats['score']}) 已手动排除"
                            )
                    else:
                        assignment_reason = f"主要贡献者{main_contributor}已达最大任务数{max_tasks_per_person}"
                        main_stats = all_contributors[main_contributor]
                        group["notes"] = (
                            f"建议: {main_contributor} (近期:{main_stats['recent_commits']},历史:{main_stats['total_commits']},得分:{main_stats['score']}) 但已达最大任务数"
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

    def _file_level_auto_assign(
        self,
        plan,
        exclude_authors=None,
        max_tasks_per_person=DEFAULT_MAX_TASKS_PER_PERSON,
        include_fallback=True,
    ):
        """文件级智能自动分配"""
        exclude_authors = exclude_authors or []

        print("🎯 正在进行文件级智能分配...")
        if ASSIGNMENT_STRATEGY.get("enhanced_scoring", False):
            print("🚀 启用增强评分算法 (提交数 + 修改行数)")
        print("🔍 自动排除近3个月无提交的人员")

        # 获取活跃贡献者
        active_contributors = self.contributor_analyzer.get_active_contributors(DEFAULT_ACTIVE_MONTHS)
        all_contributors = self.contributor_analyzer.get_all_contributors()
        inactive_contributors = all_contributors - active_contributors

        if inactive_contributors:
            print(f"🚫 自动排除近3个月无提交的 {len(inactive_contributors)} 位贡献者:")
            for contributor in sorted(list(inactive_contributors))[:5]:
                print(f"   - {contributor}")
            if len(inactive_contributors) > 5:
                print(f"   ... 还有 {len(inactive_contributors) - 5} 位")

        all_excluded = set(exclude_authors) | inactive_contributors
        assignment_count = {}
        unassigned_groups = []
        file_assignments = {}  # 存储文件级分配结果

        for group in plan["groups"]:
            print(f"\n📁 分析组: {group['name']} ({group['file_count']} 个文件)")

            # 对组内每个文件进行独立分析
            group_file_assignments = {}
            group_contributors = {}

            for file_path in group["files"]:
                print(f"  📄 分析文件: {file_path}")

                # 分析单个文件的贡献者
                file_contributors = self.contributor_analyzer.analyze_file_contributors(file_path)

                if file_contributors:
                    # 找到该文件的最佳负责人
                    best_contributor = max(file_contributors.items(), key=lambda x: x[1]["score"])
                    contributor_name, contributor_stats = best_contributor

                    # 检查是否可分配
                    if (
                        contributor_name not in all_excluded
                        and assignment_count.get(contributor_name, 0) < max_tasks_per_person
                    ):

                        group_file_assignments[file_path] = {
                            "assignee": contributor_name,
                            "stats": contributor_stats,
                            "assignment_type": "文件级直接分配",
                        }

                        # 累计贡献者信息到组级别
                        if contributor_name not in group_contributors:
                            group_contributors[contributor_name] = {
                                "files": [],
                                "total_score": 0,
                                "stats": contributor_stats,
                            }
                        group_contributors[contributor_name]["files"].append(file_path)
                        group_contributors[contributor_name]["total_score"] += contributor_stats["score"]

                        print(f"    ✅ 分配给: {contributor_name} (得分: {contributor_stats['score']:.2f})")
                    else:
                        # 文件级分配失败，记录原因
                        reason = "已排除" if contributor_name in all_excluded else "任务已满"
                        group_file_assignments[file_path] = {
                            "assignee": None,
                            "recommended": contributor_name,
                            "reason": reason,
                            "stats": contributor_stats,
                        }
                        print(f"    ⚠️ 无法分配给推荐的 {contributor_name} ({reason})")
                else:
                    group_file_assignments[file_path] = {"assignee": None, "reason": "无贡献者信息"}
                    print(f"    ❌ 无法找到贡献者信息")

            # 基于文件级分配结果确定组级负责人
            if group_contributors:
                # 选择在该组中得分最高的贡献者作为组负责人
                group_leader = max(group_contributors.items(), key=lambda x: x[1]["total_score"])
                leader_name, leader_info = group_leader

                group["assignee"] = leader_name
                assignment_count[leader_name] = assignment_count.get(leader_name, 0) + 1

                # 生成详细的分配原因
                files_count = len(leader_info["files"])
                assignment_reason = f"文件级分配 (负责{files_count}个文件, 总得分:{leader_info['total_score']:.2f})"

                print(f" ✅ 组负责人: {leader_name} (负责 {files_count}/{len(group['files'])} 个文件)")

                # 保存文件级分配详情
                group["file_assignments"] = group_file_assignments
                group["assignment_reason"] = assignment_reason
                group["contributors"] = group_contributors

            else:
                # 文件级分配全部失败，尝试回退到组级分配
                if ASSIGNMENT_STRATEGY.get("fallback_to_group", True) and include_fallback:
                    print(f" 🔄 文件级分配失败，回退到组级分配...")
                    group_result = self._assign_group_fallback(
                        group, active_contributors, all_excluded, assignment_count, max_tasks_per_person
                    )
                    if group_result:
                        assignment_count[group_result["assignee"]] = (
                            assignment_count.get(group_result["assignee"], 0) + 1
                        )
                        group.update(group_result)
                    else:
                        unassigned_groups.append(group["name"])
                        group["assignment_reason"] = "文件级和组级分配均失败"
                else:
                    unassigned_groups.append(group["name"])
                    group["assignment_reason"] = "文件级分配失败"
                    print(f" ❌ 组 {group['name']} 无法分配")

        return {
            "assignment_count": assignment_count,
            "unassigned_groups": unassigned_groups,
            "active_contributors": active_contributors,
            "inactive_contributors": inactive_contributors,
            "file_level_assignments": file_assignments,
        }

    def _assign_group_fallback(self, group, active_contributors, all_excluded, assignment_count, max_tasks_per_person):
        """组级分配回退方案"""
        main_contributor, all_contributors = self.contributor_analyzer.get_group_main_contributor(group["files"])

        if main_contributor and main_contributor not in all_excluded:
            current_count = assignment_count.get(main_contributor, 0)
            if current_count < max_tasks_per_person:
                stats = all_contributors[main_contributor]
                return {
                    "assignee": main_contributor,
                    "assignment_reason": f"组级回退分配 (得分:{stats['score']:.2f})",
                    "contributors": all_contributors,
                }

        return None

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
