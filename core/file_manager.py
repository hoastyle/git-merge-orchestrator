"""
Git Merge Orchestrator - 文件级管理器
负责文件级处理，替代原有的组分配系统，实现更精确的文件级任务分配和合并
"""

import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from config import WORK_DIR_NAME


class FileManager:
    """文件级管理器 - 支持文件级任务分配和处理"""

    def __init__(self, repo_path=".", ignore_manager=None):
        self.repo_path = Path(repo_path)
        self.ignore_manager = ignore_manager
        self.work_dir = self.repo_path / WORK_DIR_NAME
        self.work_dir.mkdir(exist_ok=True)
        self.file_plan_path = self.work_dir / "file_plan.json"

    def create_file_plan(
        self, source_branch, target_branch, integration_branch, changed_files
    ):
        """创建文件级合并计划"""
        print(f"📋 创建文件级合并计划: {len(changed_files)} 个文件")

        file_plan = {
            "created_at": datetime.now().isoformat(),
            "source_branch": source_branch,
            "target_branch": target_branch,
            "integration_branch": integration_branch,
            "total_files": len(changed_files),
            "processing_mode": "file_level",
            "files": [],
        }

        # 为每个文件创建独立记录
        for file_path in changed_files:
            file_info = {
                "path": file_path,
                "status": "pending",  # pending, assigned, in_progress, completed
                "assignee": "",
                "assigned_at": "",
                "completed_at": "",
                "conflicts": [],
                "notes": "",
                "directory": str(Path(file_path).parent),
                "filename": Path(file_path).name,
                "extension": Path(file_path).suffix,
                "priority": "normal",  # high, normal, low
                "contributors": {},
                "assignment_reason": "",
                "merge_strategy": "default",
            }
            file_plan["files"].append(file_info)

        # 保存文件级计划
        self.save_file_plan(file_plan)
        print(f"✅ 文件级合并计划已保存: {self.file_plan_path}")

        return file_plan

    def save_file_plan(self, file_plan):
        """保存文件级计划"""
        with open(self.file_plan_path, "w", encoding="utf-8") as f:
            json.dump(file_plan, f, indent=2, ensure_ascii=False)

    def load_file_plan(self):
        """加载文件级计划"""
        if not self.file_plan_path.exists():
            return None

        with open(self.file_plan_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def assign_file_to_contributor(self, file_path, assignee, reason=""):
        """将文件分配给贡献者"""
        file_plan = self.load_file_plan()
        if not file_plan:
            return False

        for file_info in file_plan["files"]:
            if file_info["path"] == file_path:
                file_info["assignee"] = assignee
                file_info["status"] = "assigned"
                file_info["assigned_at"] = datetime.now().isoformat()
                file_info["assignment_reason"] = reason

                self.save_file_plan(file_plan)
                return True

        return False

    def get_files_by_assignee(self, assignee):
        """获取指定负责人的所有文件"""
        file_plan = self.load_file_plan()
        if not file_plan:
            return []

        return [
            f for f in file_plan["files"] if f["assignee"].lower() == assignee.lower()
        ]

    def get_files_by_directory(self, directory):
        """获取指定目录的所有文件"""
        file_plan = self.load_file_plan()
        if not file_plan:
            return []

        return [f for f in file_plan["files"] if f["directory"] == directory]

    def get_files_by_status(self, status):
        """获取指定状态的文件"""
        file_plan = self.load_file_plan()
        if not file_plan:
            return []

        return [f for f in file_plan["files"] if f["status"] == status]

    def mark_file_completed(self, file_path, notes=""):
        """标记文件为已完成"""
        file_plan = self.load_file_plan()
        if not file_plan:
            return False

        for file_info in file_plan["files"]:
            if file_info["path"] == file_path:
                file_info["status"] = "completed"
                file_info["completed_at"] = datetime.now().isoformat()
                if notes:
                    file_info["notes"] = notes

                self.save_file_plan(file_plan)
                return True

        return False

    def mark_assignee_files_completed(self, assignee):
        """标记指定负责人的所有文件为已完成"""
        file_plan = self.load_file_plan()
        if not file_plan:
            return 0

        completed_count = 0
        completion_time = datetime.now().isoformat()

        for file_info in file_plan["files"]:
            if (
                file_info["assignee"].lower() == assignee.lower()
                and file_info["status"] != "completed"
            ):
                file_info["status"] = "completed"
                file_info["completed_at"] = completion_time
                completed_count += 1

        if completed_count > 0:
            self.save_file_plan(file_plan)

        return completed_count

    def get_completion_stats(self):
        """获取完成统计"""
        file_plan = self.load_file_plan()
        if not file_plan:
            return {
                "total_files": 0,
                "assigned_files": 0,
                "completed_files": 0,
                "pending_files": 0,
                "in_progress_files": 0,
            }

        files = file_plan["files"]
        total_files = len(files)
        assigned_files = len([f for f in files if f["assignee"]])
        completed_files = len([f for f in files if f["status"] == "completed"])
        pending_files = len([f for f in files if f["status"] == "pending"])
        in_progress_files = len([f for f in files if f["status"] == "in_progress"])

        return {
            "total_files": total_files,
            "assigned_files": assigned_files,
            "completed_files": completed_files,
            "pending_files": pending_files,
            "in_progress_files": in_progress_files,
            "completion_rate": (completed_files / total_files * 100)
            if total_files > 0
            else 0,
            "assignment_rate": (assigned_files / total_files * 100)
            if total_files > 0
            else 0,
        }

    def get_workload_distribution(self):
        """获取工作负载分布"""
        file_plan = self.load_file_plan()
        if not file_plan:
            return {}

        workload = defaultdict(
            lambda: {"assigned": 0, "completed": 0, "pending": 0, "files": []}
        )

        for file_info in file_plan["files"]:
            assignee = file_info["assignee"]
            if not assignee:
                continue

            workload[assignee]["files"].append(file_info)

            if file_info["status"] == "completed":
                workload[assignee]["completed"] += 1
            elif file_info["status"] in ["assigned", "in_progress"]:
                workload[assignee]["pending"] += 1

            workload[assignee]["assigned"] += 1

        return dict(workload)

    def get_directory_summary(self):
        """获取目录级汇总信息"""
        file_plan = self.load_file_plan()
        if not file_plan:
            return {}

        directory_stats = defaultdict(
            lambda: {
                "total_files": 0,
                "assigned_files": 0,
                "completed_files": 0,
                "assignees": set(),
                "files": [],
            }
        )

        for file_info in file_plan["files"]:
            directory = file_info["directory"]
            directory_stats[directory]["total_files"] += 1
            directory_stats[directory]["files"].append(file_info)

            if file_info["assignee"]:
                directory_stats[directory]["assigned_files"] += 1
                directory_stats[directory]["assignees"].add(file_info["assignee"])

            if file_info["status"] == "completed":
                directory_stats[directory]["completed_files"] += 1

        # 转换 set 为 list 以便 JSON 序列化
        for stats in directory_stats.values():
            stats["assignees"] = list(stats["assignees"])

        return dict(directory_stats)

    def find_file_by_path(self, file_path):
        """根据路径查找文件信息"""
        file_plan = self.load_file_plan()
        if not file_plan:
            return None

        for file_info in file_plan["files"]:
            if file_info["path"] == file_path:
                return file_info

        return None

    def update_file_priority(self, file_path, priority):
        """更新文件优先级"""
        file_plan = self.load_file_plan()
        if not file_plan:
            return False

        for file_info in file_plan["files"]:
            if file_info["path"] == file_path:
                file_info["priority"] = priority
                self.save_file_plan(file_plan)
                return True

        return False

    def get_files_by_priority(self, priority):
        """获取指定优先级的文件"""
        file_plan = self.load_file_plan()
        if not file_plan:
            return []

        return [
            f for f in file_plan["files"] if f.get("priority", "normal") == priority
        ]

    def batch_assign_files(self, assignments):
        """批量分配文件
        
        Args:
            assignments: List of dict with keys: file_path, assignee, reason
        """
        file_plan = self.load_file_plan()
        if not file_plan:
            return 0

        assigned_count = 0
        assignment_time = datetime.now().isoformat()

        for assignment in assignments:
            file_path = assignment.get("file_path")
            assignee = assignment.get("assignee")
            reason = assignment.get("reason", "")

            for file_info in file_plan["files"]:
                if file_info["path"] == file_path:
                    file_info["assignee"] = assignee
                    file_info["status"] = "assigned"
                    file_info["assigned_at"] = assignment_time
                    file_info["assignment_reason"] = reason
                    assigned_count += 1
                    break

        if assigned_count > 0:
            self.save_file_plan(file_plan)

        return assigned_count
