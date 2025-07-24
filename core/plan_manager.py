"""
Git Merge Orchestrator - 合并计划管理
负责创建、加载、更新和状态管理合并计划
"""

from datetime import datetime
from collections import defaultdict


class PlanManager:
    """合并计划管理器"""

    def __init__(self, git_ops, file_helper, contributor_analyzer):
        self.git_ops = git_ops
        self.file_helper = file_helper
        self.contributor_analyzer = contributor_analyzer

    def analyze_divergence(self, source_branch, target_branch):
        """分析分支分叉情况"""
        print("🔍 正在分析分支分叉情况...")

        # 获取分叉点
        merge_base = self.git_ops.get_merge_base(source_branch, target_branch)
        if merge_base:
            print(f"分叉点: {merge_base}")
        else:
            print("❌ 无法确定分叉点")
            return None

        # 统计差异
        diff_stats = self.git_ops.get_diff_stats(source_branch, target_branch)
        if diff_stats:
            print(f"\n📊 差异统计:\n{diff_stats}")

        # 创建集成分支
        integration_branch = self.git_ops.create_integration_branch(source_branch, target_branch)
        if not integration_branch:
            return None

        # 预览合并结果
        merge_result = self.git_ops.preview_merge(source_branch)

        return {
            "merge_base": merge_base,
            "diff_stats": diff_stats,
            "integration_branch": integration_branch,
            "merge_preview": merge_result
        }

    def create_merge_plan(self, source_branch, target_branch, max_files_per_group=5):
        """创建智能合并计划"""
        print(f"📋 正在创建智能合并计划（每组最多{max_files_per_group}个文件）...")

        # 获取所有变更文件
        changed_files = self.git_ops.get_changed_files(source_branch, target_branch)
        if not changed_files:
            print("⚠️ 没有发现文件差异")
            return None

        print(f"🔍 发现 {len(changed_files)} 个变更文件，开始智能分组...")

        # 创建集成分支
        integration_branch = self.git_ops.create_integration_branch(source_branch, target_branch)
        if not integration_branch:
            return None

        # 迭代分组文件（避免递归深度问题）
        try:
            self.file_helper.max_files_per_group = max_files_per_group
            file_groups = self.file_helper.iterative_group_files(changed_files)
        except Exception as e:
            print(f"❌ 分组过程中出错: {e}")
            print("🔄 回退到简单批量分组模式...")
            # 回退到简单分组
            file_groups = []
            for i in range(0, len(changed_files), max_files_per_group):
                batch_files = changed_files[i:i+max_files_per_group]
                batch_name = f"batch-{i//max_files_per_group + 1:03d}"
                file_groups.append({
                    "name": batch_name,
                    "files": batch_files,
                    "file_count": len(batch_files),
                    "type": "fallback_batch"
                })

        print(f"📊 分组完成: {len(file_groups)} 个组")
        for i, group in enumerate(file_groups[:10]):
            print(f" - {group['name']}: {group['file_count']} 个文件 ({group['type']})")
        if len(file_groups) > 10:
            print(f" ... 还有 {len(file_groups) - 10} 个组")

        # 生成合并计划
        merge_plan = self.file_helper.create_merge_plan_structure(
            source_branch, target_branch, integration_branch, changed_files, file_groups
        )

        # 保存计划
        self.file_helper.save_plan(merge_plan)

        print(f"✅ 智能合并计划已保存至: {self.file_helper.plan_file_path}")
        print(f"📁 共生成 {len(file_groups)} 个分组，平均每组 {len(changed_files)/len(file_groups):.1f} 个文件")

        # 显示分组统计
        group_types = defaultdict(int)
        for group in file_groups:
            group_types[group["type"]] += 1

        print(f"📊 分组类型统计:")
        for group_type, count in group_types.items():
            print(f" - {group_type}: {count} 个组")

        return merge_plan

    def check_status(self):
        """检查合并状态"""
        plan = self.file_helper.load_plan()
        if not plan:
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return

        print("📊 智能合并状态概览:")
        print(f"源分支: {plan['source_branch']}")
        print(f"目标分支: {plan['target_branch']}")
        print(f"集成分支: {plan['integration_branch']}")
        print(f"总文件数: {plan['total_files']}")
        print(f"每组最大文件数: {plan.get('max_files_per_group', 5)}")
        print()

        # 获取统计信息
        stats = self.file_helper.get_completion_stats(plan)
        workload = self.contributor_analyzer.get_workload_distribution(plan)

        print("📋 智能分组与任务分配状态:")

        # 构建状态表格数据
        from ui.display_helper import DisplayHelper

        table_data = []
        fallback_assigned = 0

        for group in plan["groups"]:
            status_icon = "✅" if group["status"] == "completed" else "🔄" if group.get("assignee") else "⏳"
            assignee = group.get("assignee", "未分配")
            file_count = group.get("file_count", len(group["files"]))

            # 获取分配类型
            assignment_reason = group.get("assignment_reason", "未指定")
            assignment_type = DisplayHelper.categorize_assignment_reason(assignment_reason)

            # 获取推荐信息
            recommended_info = "N/A"
            is_fallback = bool(group.get("fallback_reason", ""))
            if is_fallback:
                fallback_assigned += 1

            if assignee != "未分配" and 'contributors' in group and group['contributors']:
                if assignee in group['contributors']:
                    contributor_stats = group['contributors'][assignee]
                    if isinstance(contributor_stats, dict):
                        recent_commits = contributor_stats.get('recent_commits', 0)
                        score = contributor_stats.get('score', 0)
                        if is_fallback:
                            recommended_info = f"[备选]{group['fallback_reason'][:15]}"
                        else:
                            recommended_info = f"得分:{score}(近期:{recent_commits})"
                    else:
                        recommended_info = f"历史提交:{contributor_stats}"
                elif group['contributors']:
                    # 显示最推荐的贡献者
                    try:
                        best_contributor = max(group['contributors'].items(),
                                             key=lambda x: x[1]['score'] if isinstance(x[1], dict) else x[1])
                        contributor_name = best_contributor[0]
                        stats = best_contributor[1]
                        if isinstance(stats, dict):
                            recommended_info = f"推荐:{contributor_name}({stats['score']})"
                        else:
                            recommended_info = f"推荐:{contributor_name}({stats})"
                    except:
                        recommended_info = "分析中..."

            table_data.append([
                group['name'], str(file_count), assignee, status_icon, assignment_type, recommended_info
            ])

        DisplayHelper.print_table('status_overview', table_data)

        completion_info = DisplayHelper.format_completion_stats(stats)
        print(completion_info)
        print(f"🔄 备选分配: {fallback_assigned} 组通过目录分析分配")

        if stats['assigned_groups'] < stats['total_groups']:
            unassigned = [g['name'] for g in plan['groups'] if not g.get('assignee')]
            print(f"\n⚠️ 未分配的组: {', '.join(unassigned[:5])}" + ("..." if len(unassigned) > 5 else ""))

        # 显示负载分布
        workload_info = DisplayHelper.format_workload_distribution(workload)
        if workload_info:
            print(workload_info)

    def mark_group_completed(self, group_name):
        """标记指定组为已完成"""
        plan = self.file_helper.load_plan()
        if not plan:
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return False

        completion_time = datetime.now().isoformat()
        success = self.file_helper.update_group_status(plan, group_name, "completed", completion_time)

        if success:
            group = self.file_helper.find_group_by_name(plan, group_name)
            assignee = group.get("assignee", "未分配")
            file_count = group.get("file_count", len(group["files"]))

            print(f"✅ 组 '{group_name}' 已标记为完成")
            print(f"   负责人: {assignee}")
            print(f"   文件数: {file_count}")
            print(f"   状态变更: pending → completed")

            # 保存更新
            self.file_helper.save_plan(plan)

            # 显示整体进度
            stats = self.file_helper.get_completion_stats(plan)
            print(f"📊 整体进度: {stats['completed_groups']}/{stats['total_groups']} 组已完成 ({stats['completed_groups']/stats['total_groups']*100:.1f}%)")

            return True
        else:
            print(f"❌ 未找到组: {group_name}")
            return False

    def mark_assignee_completed(self, assignee_name):
        """标记指定负责人的所有任务为已完成"""
        plan = self.file_helper.load_plan()
        if not plan:
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return False

        # 找到负责人的所有任务
        assignee_groups = self.file_helper.get_assignee_groups(plan, assignee_name)
        if not assignee_groups:
            print(f"❌ 负责人 '{assignee_name}' 没有分配的任务")
            return False

        # 标记所有任务为完成
        completion_time = datetime.now().isoformat()
        completed_count = 0

        for group in assignee_groups:
            if group.get("status") != "completed":
                group["status"] = "completed"
                group["completed_at"] = completion_time
                completed_count += 1

        # 保存更新
        self.file_helper.save_plan(plan)

        total_files = sum(g.get("file_count", len(g["files"])) for g in assignee_groups)

        print(f"✅ 负责人 '{assignee_name}' 的所有任务已标记完成")
        print(f"   完成组数: {completed_count}/{len(assignee_groups)}")
        print(f"   涉及文件: {total_files} 个")

        # 显示整体进度
        stats = self.file_helper.get_completion_stats(plan)
        print(f"📊 整体进度: {stats['completed_groups']}/{stats['total_groups']} 组已完成 ({stats['completed_groups']/stats['total_groups']*100:.1f}%)")

        return True

    def auto_check_remote_status(self):
        """自动检查远程分支状态，推断哪些组可能已完成"""
        plan = self.file_helper.load_plan()
        if not plan:
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return False

        print("🔍 正在检查远程分支状态...")

        # 获取所有远程分支
        remote_branches = self.git_ops.get_remote_branches()
        print(f"📡 发现 {len(remote_branches)} 个远程分支")

        # 检查每个组对应的远程分支
        potentially_completed = []

        for group in plan["groups"]:
            if group.get("status") == "completed":
                continue  # 已经标记完成的跳过

            assignee = group.get("assignee")
            if not assignee:
                continue  # 未分配的跳过

            group_name = group["name"]

            # 生成可能的分支名
            possible_branch_names = [
                f"feat/merge-{group_name.replace('/', '-')}-{assignee.replace(' ', '-')}",
                f"feat/merge-batch-{assignee.replace(' ', '-')}"
            ]

            # 检查是否有对应的远程分支
            for branch_name in possible_branch_names:
                if any(branch_name in rb for rb in remote_branches):
                    potentially_completed.append({
                        "group": group,
                        "branch": branch_name,
                        "assignee": assignee
                    })
                    break

        if potentially_completed:
            print(f"\n🎯 发现 {len(potentially_completed)} 个可能已完成的组:")
            print("-" * 80)

            confirmed_completed = []
            for item in potentially_completed:
                group = item["group"]
                branch = item["branch"]
                assignee = item["assignee"]
                file_count = group.get("file_count", len(group["files"]))

                print(f"组: {group['name']:<25} 负责人: {assignee:<15} 分支: {branch}")
                print(f"   文件数: {file_count}")

                # 询问是否标记为完成
                confirm = input(f"   是否标记为完成? (y/N): ").strip().lower()
                if confirm == 'y':
                    group["status"] = "completed"
                    group["completed_at"] = datetime.now().isoformat()
                    group["auto_detected"] = True
                    confirmed_completed.append(group['name'])
                    print(f"   ✅ 已标记完成")
                else:
                    print(f"   ⏭️ 跳过")
                print()

            # 保存更新
            if confirmed_completed:
                self.file_helper.save_plan(plan)

                print(f"📊 本次自动检查结果:")
                print(f"   自动标记完成: {len(confirmed_completed)} 个组")
                for group_name in confirmed_completed:
                    print(f"   - {group_name}")

            # 显示整体进度
            stats = self.file_helper.get_completion_stats(plan)
            print(f"\n📈 整体进度: {stats['completed_groups']}/{stats['total_groups']} 组已完成 ({stats['completed_groups']/stats['total_groups']*100:.1f}%)")

            if potentially_completed and not confirmed_completed:
                print("\n💡 提示: 如果这些分支确实对应已完成的合并，建议手动标记完成")
        else:
            print("未发现可能已完成的组")

        return True