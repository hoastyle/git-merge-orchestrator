"""
Git Merge Orchestrator - 文件级计划管理器
替代原有的组计划管理器，实现文件级的合并计划创建、状态管理和进度跟踪
"""

from datetime import datetime
from collections import defaultdict
from pathlib import Path
from utils.progress_indicator import ProgressTracker, ProgressIndicator


class FilePlanManager:
    """文件级计划管理器 - 支持文件级合并计划管理"""

    def __init__(self, git_ops, file_manager, contributor_analyzer):
        self.git_ops = git_ops
        self.file_manager = file_manager
        self.contributor_analyzer = contributor_analyzer

    def analyze_divergence(self, source_branch, target_branch):
        """分析分支分叉情况"""
        steps = ["获取分叉点", "统计文件差异", "创建集成分支", "预览合并结果"]
        tracker = ProgressTracker(len(steps), "分析分支分叉")

        # 步骤 1: 获取分叉点
        tracker.step("获取分叉点")
        merge_base = self.git_ops.get_merge_base(source_branch, target_branch)
        if merge_base:
            print(f"   🎯 分叉点: {merge_base[:8]}")
        else:
            print("   ❌ 无法确定分叉点")
            return None

        # 步骤 2: 统计差异
        tracker.step("统计文件差异")
        diff_stats = self.git_ops.get_diff_stats(source_branch, target_branch)
        if diff_stats:
            # 简化差异统计显示
            lines = diff_stats.strip().split("\n")
            if lines:
                summary_line = lines[-1] if "file" in lines[-1] else "差异统计获取完成"
                print(f"   📊 {summary_line}")
        else:
            print("   ⚠️ 无文件差异")

        # 步骤 3: 创建集成分支
        tracker.step("创建集成分支")
        integration_branch = self.git_ops.create_integration_branch(
            source_branch, target_branch
        )
        if not integration_branch:
            print("   ❌ 集成分支创建失败")
            return None
        print(f"   ✅ 集成分支: {integration_branch}")

        # 步骤 4: 预览合并结果
        tracker.step("预览合并结果")
        merge_result = self.git_ops.preview_merge(source_branch)
        if merge_result:
            print(f"   🔍 合并预览完成")
        else:
            print(f"   ⚠️ 合并预览未返回结果")

        tracker.finish("分支分叉分析完成")

        return {
            "merge_base": merge_base,
            "diff_stats": diff_stats,
            "integration_branch": integration_branch,
            "merge_preview": merge_result,
        }

    def create_file_merge_plan(self, source_branch, target_branch):
        """创建文件级智能合并计划"""
        steps = ["获取变更文件列表", "创建集成分支", "生成文件级计划", "分析文件分布"]
        tracker = ProgressTracker(len(steps), "创建合并计划")

        # 步骤 1: 获取所有变更文件
        tracker.step("获取变更文件列表")
        changed_files = self.git_ops.get_changed_files(source_branch, target_branch)
        if not changed_files:
            print("   ⚠️ 没有发现文件差异")
            return None

        print(f"   📁 发现 {len(changed_files)} 个变更文件")

        # 步骤 2: 创建集成分支
        tracker.step("创建集成分支")
        integration_branch = self.git_ops.create_integration_branch(
            source_branch, target_branch
        )
        if not integration_branch:
            print("   ❌ 集成分支创建失败")
            return None
        print(f"   ✅ 集成分支: {integration_branch}")

        # 步骤 3: 创建文件级计划
        tracker.step("生成文件级计划")
        progress_indicator = ProgressIndicator(f"分析 {len(changed_files)} 个文件")
        progress_indicator.start()

        try:
            file_plan = self.file_manager.create_file_plan(
                source_branch, target_branch, integration_branch, changed_files
            )
            progress_indicator.stop("文件分析完成")
        except Exception as e:
            progress_indicator.stop(error_message=f"文件分析失败: {str(e)}")
            raise

        # 步骤 4: 分析文件分布
        tracker.step("分析文件分布")
        self._analyze_file_distribution(file_plan)

        tracker.finish(f"合并计划创建完成，包含 {len(changed_files)} 个文件")

        return file_plan

    def _analyze_file_distribution(self, file_plan):
        """分析文件分布情况"""
        directory_stats = defaultdict(int)
        extension_stats = defaultdict(int)

        for file_info in file_plan["files"]:
            directory = file_info["directory"]
            extension = file_info["extension"]

            directory_stats[directory] += 1
            extension_stats[extension] += 1

        print(f"\n📊 文件分布分析:")
        print(f"📁 目录分布: {len(directory_stats)} 个目录")

        # 显示前10个目录
        sorted_dirs = sorted(directory_stats.items(), key=lambda x: x[1], reverse=True)
        for directory, count in sorted_dirs[:10]:
            print(f"  {directory}: {count} 个文件")
        if len(sorted_dirs) > 10:
            print(f"  ... 还有 {len(sorted_dirs) - 10} 个目录")

        print(f"\n📄 文件类型分布:")
        sorted_exts = sorted(extension_stats.items(), key=lambda x: x[1], reverse=True)
        for extension, count in sorted_exts[:10]:
            ext_display = extension if extension else "无扩展名"
            print(f"  {ext_display}: {count} 个文件")

    def check_file_status(self):
        """检查文件级合并状态"""
        file_plan = self.file_manager.load_file_plan()
        if not file_plan:
            print("❌ 文件级计划不存在，请先创建合并计划")
            return

        print("📊 文件级合并状态概览:")
        print(f"源分支: {file_plan.get('source_branch', 'N/A')}")
        print(f"目标分支: {file_plan.get('target_branch', 'N/A')}")
        print(f"集成分支: {file_plan.get('integration_branch', 'N/A')}")
        print(f"处理模式: {file_plan.get('processing_mode', 'N/A')}")
        print(f"总文件数: {file_plan.get('total_files', 0)}")
        print()

        # 获取统计信息
        stats = self.file_manager.get_completion_stats()
        workload = self.file_manager.get_workload_distribution()
        directory_summary = self.file_manager.get_directory_summary()

        # 显示完成统计
        from ui.display_helper import DisplayHelper

        print("📋 文件处理状态:")
        print(f"  总文件数: {stats['total_files']}")
        print(f"  已分配: {stats['assigned_files']} ({stats['assignment_rate']:.1f}%)")
        print(f"  已完成: {stats['completed_files']} ({stats['completion_rate']:.1f}%)")
        print(f"  待处理: {stats['pending_files']}")
        print(f"  进行中: {stats['in_progress_files']}")

        # 显示工作负载分布
        if workload:
            print(f"\n👥 工作负载分布 ({len(workload)} 位贡献者):")
            sorted_workload = sorted(
                workload.items(), key=lambda x: x[1]["assigned"], reverse=True
            )

            for assignee, load_info in sorted_workload[:10]:
                assigned = load_info["assigned"]
                completed = load_info["completed"]
                pending = load_info["pending"]
                completion_rate = (completed / assigned * 100) if assigned > 0 else 0

                print(
                    f"  {assignee}: {assigned} 个文件 (完成:{completed}, 待处理:{pending}, {completion_rate:.1f}%)"
                )

            if len(sorted_workload) > 10:
                print(f"  ... 还有 {len(sorted_workload) - 10} 位贡献者")

        # 显示目录汇总
        if directory_summary:
            print(f"\n📁 目录处理状态:")
            sorted_dirs = sorted(
                directory_summary.items(),
                key=lambda x: x[1]["total_files"],
                reverse=True,
            )

            for directory, dir_stats in sorted_dirs[:10]:
                total = dir_stats["total_files"]
                assigned = dir_stats["assigned_files"]
                completed = dir_stats["completed_files"]
                assignees = dir_stats["assignees"]

                print(
                    f"  {directory}: {total} 个文件 (已分配:{assigned}, 已完成:{completed}, 负责人:{len(assignees)})"
                )

            if len(sorted_dirs) > 10:
                print(f"  ... 还有 {len(sorted_dirs) - 10} 个目录")

    def mark_file_completed(self, file_path, notes=""):
        """标记单个文件为已完成"""
        success = self.file_manager.mark_file_completed(file_path, notes)

        if success:
            file_info = self.file_manager.find_file_by_path(file_path)
            assignee = file_info.get("assignee", "未分配")

            print(f"✅ 文件 '{file_path}' 已标记为完成")
            print(f"   负责人: {assignee}")
            if notes:
                print(f"   备注: {notes}")
            print(f"   状态变更: pending/assigned → completed")

            # 显示整体进度
            stats = self.file_manager.get_completion_stats()
            print(
                f"📊 整体进度: {stats['completed_files']}/{stats['total_files']} 文件已完成 ({stats['completion_rate']:.1f}%)"
            )

            return True
        else:
            print(f"❌ 未找到文件: {file_path}")
            return False

    def mark_assignee_completed(self, assignee_name):
        """标记指定负责人的所有文件为已完成"""
        completed_count = self.file_manager.mark_assignee_files_completed(assignee_name)

        if completed_count > 0:
            print(f"✅ 负责人 '{assignee_name}' 的所有文件已标记完成")
            print(f"   完成文件数: {completed_count}")

            # 显示整体进度
            stats = self.file_manager.get_completion_stats()
            print(
                f"📊 整体进度: {stats['completed_files']}/{stats['total_files']} 文件已完成 ({stats['completion_rate']:.1f}%)"
            )

            return True
        else:
            print(f"❌ 负责人 '{assignee_name}' 没有待完成的文件")
            return False

    def mark_directory_completed(self, directory_path):
        """标记指定目录的所有文件为已完成"""
        files = self.file_manager.get_files_by_directory(directory_path)

        if not files:
            print(f"❌ 目录 '{directory_path}' 没有文件")
            return False

        completed_count = 0
        completion_time = datetime.now().isoformat()

        file_plan = self.file_manager.load_file_plan()
        if not file_plan:
            return False

        for file_info in file_plan["files"]:
            if (
                file_info["directory"] == directory_path
                and file_info["status"] != "completed"
            ):
                file_info["status"] = "completed"
                file_info["completed_at"] = completion_time
                completed_count += 1

        if completed_count > 0:
            self.file_manager.save_file_plan(file_plan)

        print(f"✅ 目录 '{directory_path}' 的所有文件已标记完成")
        print(f"   完成文件数: {completed_count}/{len(files)}")

        # 显示整体进度
        stats = self.file_manager.get_completion_stats()
        print(
            f"📊 整体进度: {stats['completed_files']}/{stats['total_files']} 文件已完成 ({stats['completion_rate']:.1f}%)"
        )

        return True

    def auto_check_remote_status(self):
        """自动检查远程分支状态，推断哪些文件可能已完成"""
        file_plan = self.file_manager.load_file_plan()
        if not file_plan:
            print("❌ 文件级计划不存在，请先创建合并计划")
            return False

        print("🔍 正在检查远程分支状态...")

        # 获取所有远程分支
        remote_branches = self.git_ops.get_remote_branches()
        print(f"📡 发现 {len(remote_branches)} 个远程分支")

        # 按负责人分组待完成的文件
        assignee_files = defaultdict(list)
        for file_info in file_plan["files"]:
            if file_info.get("status") != "completed" and file_info.get("assignee"):
                assignee_files[file_info["assignee"]].append(file_info)

        if not assignee_files:
            print("✅ 所有文件都已完成或未分配")
            return True

        # 检查每个负责人对应的远程分支
        potentially_completed = []

        for assignee, files in assignee_files.items():
            # 生成可能的分支名模式
            possible_branch_patterns = [
                f"feat/merge-batch-{assignee.replace(' ', '-')}",
                f"feat/{assignee.replace(' ', '-')}",
                f"feature/{assignee.replace(' ', '-')}",
            ]

            # 检查是否有对应的远程分支
            for pattern in possible_branch_patterns:
                matching_branches = [
                    rb
                    for rb in remote_branches
                    if pattern in rb or rb.endswith(pattern)
                ]
                if matching_branches:
                    potentially_completed.append(
                        {
                            "assignee": assignee,
                            "files": files,
                            "branches": matching_branches,
                            "file_count": len(files),
                        }
                    )
                    break

        if potentially_completed:
            print(f"\n🎯 发现 {len(potentially_completed)} 位负责人可能已完成工作:")
            print("-" * 80)

            confirmed_completed = []
            for item in potentially_completed:
                assignee = item["assignee"]
                files = item["files"]
                branches = item["branches"]
                file_count = item["file_count"]

                print(f"负责人: {assignee}")
                print(f"  文件数: {file_count}")
                print(f"  可能的分支: {', '.join(branches[:3])}")
                if len(branches) > 3:
                    print(f"  ... 还有 {len(branches) - 3} 个分支")

                # 询问是否标记为完成
                confirm = input(f"  是否标记该负责人的所有文件为完成? (y/N): ").strip().lower()
                if confirm == "y":
                    completed_count = self.file_manager.mark_assignee_files_completed(
                        assignee
                    )
                    confirmed_completed.append(assignee)
                    print(f"  ✅ 已标记完成 {completed_count} 个文件")
                else:
                    print(f"  ⏭️ 跳过")
                print()

            # 显示汇总结果
            if confirmed_completed:
                print(f"📊 本次自动检查结果:")
                print(f"   自动标记完成: {len(confirmed_completed)} 位负责人")
                for assignee in confirmed_completed:
                    print(f"   - {assignee}")

            # 显示整体进度
            stats = self.file_manager.get_completion_stats()
            print(
                f"\n📈 整体进度: {stats['completed_files']}/{stats['total_files']} 文件已完成 ({stats['completion_rate']:.1f}%)"
            )

        else:
            print("未发现可能已完成的工作")

        return True

    def get_plan_summary(self):
        """获取文件级计划摘要信息"""
        try:
            file_plan = self.file_manager.load_file_plan()
            if not file_plan:
                return None

            stats = self.file_manager.get_completion_stats()
            workload = self.file_manager.get_workload_distribution()
            directory_summary = self.file_manager.get_directory_summary()

            return {
                "file_plan": file_plan,
                "completion_stats": stats,
                "workload_distribution": workload,
                "directory_summary": directory_summary,
                "source_branch": file_plan.get("source_branch"),
                "target_branch": file_plan.get("target_branch"),
                "integration_branch": file_plan.get("integration_branch"),
                "processing_mode": "file_level",
                "created_at": file_plan.get("created_at"),
            }
        except Exception as e:
            print(f"⚠️ 获取计划摘要失败: {e}")
            return None

    def search_files_by_assignee(self, assignee_name):
        """根据负责人搜索其负责的所有文件"""
        files = self.file_manager.get_files_by_assignee(assignee_name)

        if not files:
            print(f"📋 负责人 '{assignee_name}' 暂无分配的文件")
            return []

        print(f"👤 负责人: {assignee_name}")
        print(f"📊 总览: {len(files)} 个文件")

        # 统计状态分布
        status_stats = defaultdict(int)
        for file_info in files:
            status_stats[file_info["status"]] += 1

        print(f"📈 状态分布:")
        for status, count in status_stats.items():
            status_display = {
                "pending": "待处理",
                "assigned": "已分配",
                "in_progress": "进行中",
                "completed": "已完成",
            }.get(status, status)
            print(f"  {status_display}: {count} 个文件")

        # 显示文件列表
        print(f"\n📄 文件详情:")
        for i, file_info in enumerate(files[:20], 1):  # 最多显示20个文件
            status_icon = {
                "pending": "⏳",
                "assigned": "📋",
                "in_progress": "🔄",
                "completed": "✅",
            }.get(file_info["status"], "❓")

            print(f"  {i:2d}. {status_icon} {file_info['path']}")
            if file_info.get("assignment_reason"):
                print(f"      原因: {file_info['assignment_reason'][:50]}...")

        if len(files) > 20:
            print(f"  ... 还有 {len(files) - 20} 个文件")

        return files

    def search_files_by_directory(self, directory_path):
        """根据目录搜索文件"""
        files = self.file_manager.get_files_by_directory(directory_path)

        if not files:
            print(f"📁 目录 '{directory_path}' 没有文件")
            return []

        print(f"📁 目录: {directory_path}")
        print(f"📊 总览: {len(files)} 个文件")

        # 统计负责人分布
        assignee_stats = defaultdict(int)
        status_stats = defaultdict(int)

        for file_info in files:
            assignee = file_info.get("assignee", "未分配")
            assignee_stats[assignee] += 1
            status_stats[file_info["status"]] += 1

        print(f"👥 负责人分布:")
        for assignee, count in sorted(
            assignee_stats.items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {assignee}: {count} 个文件")

        print(f"📈 状态分布:")
        for status, count in status_stats.items():
            status_display = {
                "pending": "待处理",
                "assigned": "已分配",
                "in_progress": "进行中",
                "completed": "已完成",
            }.get(status, status)
            print(f"  {status_display}: {count} 个文件")

        return files
