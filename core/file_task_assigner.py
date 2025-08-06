"""
Git Merge Orchestrator - 文件级任务分配器
基于文件贡献度分析进行精确的文件级任务分配，替代原有的组分配系统
"""

from datetime import datetime, timedelta
from collections import defaultdict
import json
from pathlib import Path
from utils.progress_indicator import ProgressTracker, ProgressIndicator


class FileTaskAssigner:
    """文件级任务分配器 - 基于贡献度分析的智能文件分配"""

    def __init__(self, contributor_analyzer, file_manager):
        self.contributor_analyzer = contributor_analyzer
        self.file_manager = file_manager

    def auto_assign_files(
        self, exclude_authors=None, max_tasks_per_person=200, include_fallback=True
    ):
        """智能自动分配文件给贡献者"""
        # 性能监控开始
        main_start = datetime.now()
        print(f"🚀 [PERF] 开始文件任务分配... (开始时间: {main_start.timestamp():.3f})")
        
        file_plan = self.file_manager.load_file_plan()
        if not file_plan:
            print("❌ 文件级计划不存在，请先创建合并计划")
            return None

        total_files = len(file_plan["files"])

        steps = ["获取活跃贡献者", "分析文件贡献度", "智能分配文件", "保存分配结果"]
        tracker = ProgressTracker(len(steps), "文件任务分配")

        # 步骤 1: 获取活跃贡献者
        step1_start = datetime.now()
        tracker.step("获取活跃贡献者")
        exclude_authors = exclude_authors or []
        active_contributors = self.contributor_analyzer.get_active_contributors(3)

        step1_time = (datetime.now() - step1_start).total_seconds()
        print(f"⏱️  [PERF] 步骤1-获取活跃贡献者: {step1_time:.3f}s")
        print(f"   🎯 活跃贡献者: {len(active_contributors)} 位")
        print(f"   🚫 手动排除: {len(exclude_authors)} 位")

        # 步骤 2: 分析文件贡献度（使用批量分析优化）
        tracker.step(f"分析文件贡献度")
        
        unassigned_files = [f for f in file_plan["files"] if not f.get("assignee")]
        
        # 🚀 使用批量分析替代逐个文件分析
        print(f"🚀 [PERF] 使用批量分析优化 {len(unassigned_files)} 个文件...")
        batch_start = datetime.now()
        
        # 提取文件路径列表
        file_paths = [f["path"] for f in unassigned_files]
        
        # 批量分析所有文件
        batch_contributors = self.contributor_analyzer.batch_analyze_all_files(file_paths)
        
        batch_time = (datetime.now() - batch_start).total_seconds()
        print(f"✅ [PERF] 批量分析完成: {batch_time:.3f}s ({batch_time/len(file_paths)*1000:.1f}ms/文件)")
        
        # 将批量分析结果分配给文件信息，并转换格式
        print(f"🔄 [PERF] 转换数据格式以兼容任务分配...")
        format_start = datetime.now()
        
        for file_info in unassigned_files:
            file_path = file_info["path"]
            raw_contributors = batch_contributors.get(file_path, {})
            
            # 转换数据格式：{author: count} -> {author: {"score": count, ...}}
            file_contributors = {}
            for author, count in raw_contributors.items():
                if isinstance(count, dict):
                    # 已经是正确格式（包含score等字段）
                    file_contributors[author] = count
                else:
                    # 需要转换格式：简单数字 -> 完整字典
                    file_contributors[author] = {
                        "recent_commits": count,
                        "total_commits": count,
                        "score": count
                    }
            
            file_info["contributors"] = file_contributors
        
        format_time = (datetime.now() - format_start).total_seconds()
        print(f"✅ [PERF] 数据格式转换完成: {format_time:.3f}s")

        # 统计变量
        assignment_stats = {
            "direct_assignment": 0,
            "directory_fallback": 0,
            "load_balancing": 0,
            "unassigned": 0,
        }

        workload_counter = defaultdict(int)
        assignments = []

        # 步骤 3: 智能分配文件
        step3_start = datetime.now()
        tracker.step(f"智能分配 {len(unassigned_files)} 个文件")

        # 使用进度指示器处理文件分配（不再需要分析）
        progress_indicator = ProgressIndicator(f"分配 {len(unassigned_files)} 个文件")
        progress_indicator.start()

        try:
            for i, file_info in enumerate(unassigned_files):
                file_path = file_info["path"]
                directory = file_info["directory"]

                # 文件贡献者已经通过批量分析获得
                file_contributors = file_info["contributors"]

                # 尝试直接分配
                assignee, reason = self._assign_file_to_best_contributor(
                    file_contributors,
                    active_contributors,
                    exclude_authors,
                    workload_counter,
                    max_tasks_per_person,
                )

                if assignee:
                    assignment_stats["direct_assignment"] += 1
                elif include_fallback:
                    # 尝试目录级回退分配
                    assignee, reason = self._assign_file_by_directory_fallback(
                        directory,
                        active_contributors,
                        exclude_authors,
                        workload_counter,
                        max_tasks_per_person,
                    )
                    if assignee:
                        assignment_stats["directory_fallback"] += 1
                        reason = f"[目录回退] {reason}"

                if assignee:
                    workload_counter[assignee] += 1
                    assignments.append(
                        {"file_path": file_path, "assignee": assignee, "reason": reason}
                    )
                else:
                    assignment_stats["unassigned"] += 1

                # 每处理50个文件显示一次进度
                if (i + 1) % 50 == 0 or (i + 1) == len(unassigned_files):
                    progress_indicator.update_message(
                        f"已分析 {i + 1}/{len(unassigned_files)} 个文件"
                    )

            progress_indicator.stop(f"文件分析完成")
        except Exception as e:
            progress_indicator.stop(error_message=f"文件分析失败: {str(e)}")
            raise

        step3_time = (datetime.now() - step3_start).total_seconds()
        print(f"⏱️  [PERF] 步骤3-智能分配: {step3_time:.3f}s")

        # 步骤 4: 批量分配文件
        step4_start = datetime.now()
        tracker.step("保存分配结果")
        assigned_count = self.file_manager.batch_assign_files(assignments)
        
        step4_time = (datetime.now() - step4_start).total_seconds()
        print(f"⏱️  [PERF] 步骤4-保存分配结果: {step4_time:.3f}s")

        tracker.finish(f"文件任务分配完成，成功分配 {assigned_count} 个文件")

        # 显示分配结果
        print(f"\n📊 分配结果详情:")
        print(f"   ✅ 直接分配: {assignment_stats['direct_assignment']} 个文件")
        print(f"   🔄 目录回退: {assignment_stats['directory_fallback']} 个文件")
        print(f"   ⚠️ 未分配: {assignment_stats['unassigned']} 个文件")

        # 显示工作负载分布
        print(f"\n👥 工作负载分布:")
        sorted_workload = sorted(
            workload_counter.items(), key=lambda x: x[1], reverse=True
        )
        for assignee, count in sorted_workload[:10]:  # 显示前10位
            print(f"   {assignee}: {count} 个文件")

        if len(sorted_workload) > 10:
            print(f"   ... 还有 {len(sorted_workload) - 10} 位贡献者")

        # 性能监控结束
        total_time = (datetime.now() - main_start).total_seconds()
        print(f"✅ [PERF] 文件任务分配总完成时间: {total_time:.3f}s")
        print(f"📊 [PERF] 处理统计: 总计{total_files}个文件, 平均{total_time/total_files*1000:.1f}ms/文件")
        
        # 保存性能日志
        self._save_performance_log(total_files, total_time, {
            'get_contributors': step1_time,
            'batch_analysis': batch_time,
            'format_conversion': format_time,
            'file_assignment': step3_time,
            'save_results': step4_time,
            'mode': 'file_task_assigner'
        })

        return {
            "assigned_count": assigned_count,
            "assignment_stats": assignment_stats,
            "workload_distribution": dict(workload_counter),
            "active_contributors": active_contributors,
            "exclude_authors": exclude_authors,
        }

    def _analyze_file_contributors(self, file_path):
        """分析单个文件的贡献者"""
        try:
            # 获取一年内的贡献者
            one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
            recent_contributors = self.contributor_analyzer.git_ops.get_contributors_since(
                file_path, one_year_ago
            )

            # 获取所有历史贡献者
            all_contributors = self.contributor_analyzer.git_ops.get_all_contributors(
                file_path
            )

            # 合并统计信息
            contributors = {}
            for author, recent_count in recent_contributors.items():
                total_count = all_contributors.get(author, recent_count)
                contributors[author] = {
                    "recent_commits": recent_count,
                    "total_commits": total_count,
                    "score": recent_count * 3 + total_count,  # 近期权重更高
                }

            # 添加仅有历史贡献的作者
            for author, total_count in all_contributors.items():
                if author not in contributors:
                    contributors[author] = {
                        "recent_commits": 0,
                        "total_commits": total_count,
                        "score": total_count,
                    }

            return contributors

        except Exception as e:
            print(f"⚠️ 分析文件 {file_path} 贡献者时出错: {e}")
            return {}

    def _assign_file_to_best_contributor(
        self,
        file_contributors,
        active_contributors,
        exclude_authors,
        workload_counter,
        max_tasks_per_person,
    ):
        """将文件分配给最佳贡献者"""
        if not file_contributors:
            return None, "无贡献者数据"

        # 按得分排序贡献者
        sorted_contributors = sorted(
            file_contributors.items(), key=lambda x: x[1]["score"], reverse=True
        )

        for author, stats in sorted_contributors:
            # 检查排除条件
            if author in exclude_authors:
                continue

            # 检查活跃度
            if author not in active_contributors:
                continue

            # 检查工作负载
            if workload_counter[author] >= max_tasks_per_person:
                continue

            # 找到合适的分配对象
            reason = f"文件主要贡献者(得分:{stats['score']}, 近期:{stats['recent_commits']}, 历史:{stats['total_commits']})"
            return author, reason

        return None, "无合适的活跃贡献者"

    def _assign_file_by_directory_fallback(
        self,
        directory,
        active_contributors,
        exclude_authors,
        workload_counter,
        max_tasks_per_person,
    ):
        """基于目录分析进行回退分配"""
        try:
            # 分析目录级贡献者
            directory_contributors = self.contributor_analyzer.git_ops.get_directory_contributors(
                directory
            )

            if not directory_contributors:
                return None, "目录无贡献者数据"

            # 按得分排序
            sorted_contributors = sorted(
                directory_contributors.items(),
                key=lambda x: x[1]["score"],
                reverse=True,
            )

            for author, stats in sorted_contributors:
                # 检查排除条件
                if author in exclude_authors:
                    continue

                # 检查活跃度
                if author not in active_contributors:
                    continue

                # 检查工作负载
                if workload_counter[author] >= max_tasks_per_person:
                    continue

                # 找到合适的分配对象
                reason = f"目录主要贡献者(得分:{stats['score']}, 目录:{directory})"
                return author, reason

            return None, "目录无合适的活跃贡献者"

        except Exception as e:
            print(f"⚠️ 目录回退分配失败: {e}")
            return None, "目录分析失败"

    def manual_assign_file(self, file_path, assignee, reason="手动分配"):
        """手动分配单个文件"""
        success = self.file_manager.assign_file_to_contributor(
            file_path, assignee, reason
        )
        if success:
            print(f"✅ 文件 '{file_path}' 已分配给 '{assignee}'")
            print(f"   原因: {reason}")
        else:
            print(f"❌ 分配失败: 文件 '{file_path}' 不存在")

        return success

    def manual_assign_files_batch(self, assignments):
        """手动批量分配文件
        
        Args:
            assignments: List of dict with keys: file_path, assignee, reason
        """
        for assignment in assignments:
            assignment["reason"] = assignment.get("reason", "手动批量分配")

        assigned_count = self.file_manager.batch_assign_files(assignments)
        print(f"✅ 批量分配完成: {assigned_count} 个文件")

        return assigned_count

    def reassign_files_by_assignee(self, old_assignee, new_assignee, reason="重新分配"):
        """重新分配指定负责人的所有文件"""
        files = self.file_manager.get_files_by_assignee(old_assignee)
        if not files:
            print(f"❌ 负责人 '{old_assignee}' 没有分配的文件")
            return 0

        assignments = []
        for file_info in files:
            assignments.append(
                {
                    "file_path": file_info["path"],
                    "assignee": new_assignee,
                    "reason": f"从 {old_assignee} 重新分配: {reason}",
                }
            )

        assigned_count = self.file_manager.batch_assign_files(assignments)
        print(f"✅ 重新分配完成: {assigned_count} 个文件从 '{old_assignee}' 转给 '{new_assignee}'")

        return assigned_count

    def balance_workload(self, max_tasks_per_person=50):
        """负载均衡 - 重新分配过载用户的文件"""
        workload = self.file_manager.get_workload_distribution()

        # 找出过载的用户
        overloaded_users = []
        underloaded_users = []

        for assignee, stats in workload.items():
            assigned_count = stats["assigned"]
            if assigned_count > max_tasks_per_person:
                overloaded_users.append(
                    (assignee, assigned_count - max_tasks_per_person)
                )
            elif assigned_count < max_tasks_per_person * 0.7:  # 70%以下视为负载不足
                underloaded_users.append(
                    (assignee, max_tasks_per_person - assigned_count)
                )

        if not overloaded_users:
            print("✅ 当前工作负载分布合理，无需调整")
            return 0

        print(f"🔄 发现 {len(overloaded_users)} 个过载用户，开始负载均衡...")

        reassignments = []
        total_reassigned = 0

        for overloaded_user, excess_count in overloaded_users:
            # 获取该用户的文件（按优先级和分配时间排序）
            user_files = self.file_manager.get_files_by_assignee(overloaded_user)

            # 选择最近分配的、优先级较低的文件进行重新分配
            candidates = sorted(
                [f for f in user_files if f["status"] != "completed"],
                key=lambda x: (
                    x.get("priority", "normal") == "high",
                    x.get("assigned_at", ""),
                ),
                reverse=False,
            )

            files_to_reassign = candidates[:excess_count]

            # 分配给负载不足的用户
            for file_info in files_to_reassign:
                if underloaded_users:
                    target_user, capacity = underloaded_users[0]
                    reassignments.append(
                        {
                            "file_path": file_info["path"],
                            "assignee": target_user,
                            "reason": f"负载均衡: 从 {overloaded_user} 转移",
                        }
                    )

                    # 更新容量
                    underloaded_users[0] = (target_user, capacity - 1)
                    if capacity <= 1:
                        underloaded_users.pop(0)

                    total_reassigned += 1

        if reassignments:
            assigned_count = self.file_manager.batch_assign_files(reassignments)
            print(f"✅ 负载均衡完成: 重新分配了 {assigned_count} 个文件")
            return assigned_count
        else:
            print("⚠️ 无法找到合适的重新分配目标")
            return 0

    def get_assignment_summary(self):
        """获取分配情况汇总"""
        file_plan = self.file_manager.load_file_plan()
        if not file_plan:
            return None

        stats = self.file_manager.get_completion_stats()
        workload = self.file_manager.get_workload_distribution()
        directory_summary = self.file_manager.get_directory_summary()

        # 分析分配原因类型
        reason_stats = defaultdict(int)
        for file_info in file_plan["files"]:
            if file_info.get("assignment_reason"):
                reason = file_info["assignment_reason"]
                if "目录回退" in reason:
                    reason_stats["目录回退分配"] += 1
                elif "手动" in reason:
                    reason_stats["手动分配"] += 1
                elif "重新分配" in reason:
                    reason_stats["重新分配"] += 1
                elif "负载均衡" in reason:
                    reason_stats["负载均衡"] += 1
                else:
                    reason_stats["直接分配"] += 1

        return {
            "completion_stats": stats,
            "workload_distribution": workload,
            "directory_summary": directory_summary,
            "assignment_reasons": dict(reason_stats),
            "total_contributors": len(workload),
            "plan_info": {
                "source_branch": file_plan.get("source_branch"),
                "target_branch": file_plan.get("target_branch"),
                "integration_branch": file_plan.get("integration_branch"),
                "created_at": file_plan.get("created_at"),
            },
        }
    
    def _save_performance_log(self, file_count, total_time, step_times):
        """保存性能日志到文件"""
        try:
            # 设置日志文件路径
            if hasattr(self.contributor_analyzer, 'git_ops') and hasattr(self.contributor_analyzer.git_ops, 'repo_path'):
                repo_path = Path(self.contributor_analyzer.git_ops.repo_path)
            else:
                repo_path = Path(".")
                
            log_file = repo_path / ".merge_work" / "performance_log.json"
            log_file.parent.mkdir(exist_ok=True)
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'file_count': file_count,
                'total_time': total_time,
                'avg_time_per_file': total_time / file_count * 1000,  # ms
                'step_times': step_times,
                'mode': step_times.get('mode', 'file_task_assigner')
            }
            
            # 如果文件存在，加载现有日志
            logs = []
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                except:
                    logs = []
            
            # 添加新日志（保留最近50条）
            logs.append(log_entry)
            logs = logs[-50:]
            
            # 保存日志
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
            
            print(f"📝 [PERF] 性能日志已保存: {log_file}")
            
        except Exception as e:
            print(f"⚠️ [PERF] 保存性能日志失败: {e}")
