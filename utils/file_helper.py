"""
Git Merge Orchestrator - 文件操作工具
负责文件系统操作、路径处理和文件分组逻辑
"""

import os
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from config import WORK_DIR_NAME, PLAN_FILE_NAME, GROUP_TYPES


class FileHelper:
    """文件操作助手类"""

    def __init__(self, repo_path=".", max_files_per_group=5):
        self.repo_path = Path(repo_path)
        self.max_files_per_group = max_files_per_group
        self.work_dir = self.repo_path / WORK_DIR_NAME
        self.work_dir.mkdir(exist_ok=True)

    @property
    def plan_file_path(self):
        """获取合并计划文件路径"""
        return self.work_dir / PLAN_FILE_NAME

    def load_plan(self):
        """加载合并计划"""
        if not self.plan_file_path.exists():
            return None

        with open(self.plan_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_plan(self, plan):
        """保存合并计划"""
        with open(self.plan_file_path, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)

    def create_merge_plan_structure(self, source_branch, target_branch,
                                  integration_branch, changed_files, groups):
        """创建合并计划结构"""
        return {
            "created_at": datetime.now().isoformat(),
            "source_branch": source_branch,
            "target_branch": target_branch,
            "integration_branch": integration_branch,
            "total_files": len(changed_files),
            "total_groups": len(groups),
            "max_files_per_group": self.max_files_per_group,
            "groups": [
                {
                    "name": group_info["name"],
                    "files": group_info["files"],
                    "file_count": group_info["file_count"],
                    "group_type": group_info["type"],
                    "status": "pending",
                    "assignee": "",
                    "conflicts": [],
                    "notes": "",
                    "contributors": {},
                    "fallback_reason": "",
                    "assignment_reason": ""
                }
                for group_info in groups
            ]
        }

    def iterative_group_files(self, file_paths):
        """迭代式文件分组，避免递归深度问题"""
        print(f"🔄 使用迭代算法处理 {len(file_paths)} 个文件...")

        # 按目录层次分析文件
        path_analysis = {}
        for file_path in file_paths:
            parts = file_path.split('/')
            depth = len(parts) - 1

            if depth == 0:
                key = "root"
            else:
                key = parts[0]

            if key not in path_analysis:
                path_analysis[key] = []
            path_analysis[key].append(file_path)

        print(f"📊 发现 {len(path_analysis)} 个顶级目录/分组")

        groups = []
        for base_path, files in path_analysis.items():
            print(f" 处理 {base_path}: {len(files)} 个文件")

            if len(files) <= self.max_files_per_group:
                groups.append({
                    "name": base_path,
                    "files": files,
                    "file_count": len(files),
                    "type": "simple_group"
                })
            else:
                sub_groups = self._split_large_group(base_path, files)
                groups.extend(sub_groups)

        print(f"✅ 分组完成：共 {len(groups)} 个组")
        return groups

    def _split_large_group(self, base_path, files):
        """分割大文件组为小组"""
        groups = []

        if base_path == "root":
            return self._split_by_alphabet(base_path, files)

        # 非根目录：先按子目录分组
        subdir_groups = defaultdict(list)
        direct_files = []

        for file_path in files:
            if file_path.startswith(base_path + "/"):
                relative_path = file_path[len(base_path + "/"):]
                if "/" in relative_path:
                    next_dir = relative_path.split("/")[0]
                    subdir_groups[f"{base_path}/{next_dir}"].append(file_path)
                else:
                    direct_files.append(file_path)
            else:
                direct_files.append(file_path)

        # 处理直接文件
        if direct_files:
            if len(direct_files) <= self.max_files_per_group:
                groups.append({
                    "name": f"{base_path}/direct",
                    "files": direct_files,
                    "file_count": len(direct_files),
                    "type": "direct_files"
                })
            else:
                batch_groups = self._split_into_batches(f"{base_path}/direct", direct_files)
                groups.extend(batch_groups)

        # 处理子目录
        for subdir_path, subdir_files in subdir_groups.items():
            if len(subdir_files) <= self.max_files_per_group:
                groups.append({
                    "name": subdir_path,
                    "files": subdir_files,
                    "file_count": len(subdir_files),
                    "type": "subdir_group"
                })
            else:
                sub_groups = self._split_large_group(subdir_path, subdir_files)
                groups.extend(sub_groups)

        return groups

    def _split_by_alphabet(self, base_name, files):
        """按字母分组文件"""
        alpha_groups = defaultdict(list)
        for file_path in files:
            filename = file_path.split('/')[-1]
            first_char = filename[0].lower()

            if first_char.isalpha():
                alpha_groups[first_char].append(file_path)
            elif first_char.isdigit():
                alpha_groups['0-9'].append(file_path)
            else:
                alpha_groups['other'].append(file_path)

        groups = []
        for alpha, alpha_files in alpha_groups.items():
            if len(alpha_files) <= self.max_files_per_group:
                groups.append({
                    "name": f"{base_name}-{alpha}",
                    "files": alpha_files,
                    "file_count": len(alpha_files),
                    "type": "alpha_group"
                })
            else:
                batch_groups = self._split_into_batches(f"{base_name}-{alpha}", alpha_files)
                groups.extend(batch_groups)

        return groups

    def _split_into_batches(self, base_name, files):
        """将文件分批处理"""
        groups = []
        for i in range(0, len(files), self.max_files_per_group):
            batch_files = files[i:i+self.max_files_per_group]
            batch_num = i // self.max_files_per_group + 1
            groups.append({
                "name": f"{base_name}-batch{batch_num}",
                "files": batch_files,
                "file_count": len(batch_files),
                "type": "batch_group"
            })
        return groups

    def create_script_file(self, script_name, script_content):
        """创建并保存脚本文件"""
        script_file = self.work_dir / f"{script_name}.sh"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)

        os.chmod(script_file, 0o755)
        return script_file

    def get_group_type_description(self, group_type):
        """获取分组类型的描述"""
        return GROUP_TYPES.get(group_type, '未知类型')

    def find_group_by_name(self, plan, group_name):
        """根据组名查找组"""
        for group in plan["groups"]:
            if group["name"] == group_name:
                return group
        return None

    def get_assignee_groups(self, plan, assignee_name):
        """获取指定负责人的所有组"""
        assignee_groups = []
        for group in plan["groups"]:
            if group.get("assignee", "").lower() == assignee_name.lower():
                assignee_groups.append(group)
        return assignee_groups

    def get_unassigned_groups(self, plan):
        """获取未分配的组"""
        return [group for group in plan["groups"] if not group.get("assignee")]

    def get_completed_groups(self, plan):
        """获取已完成的组"""
        return [group for group in plan["groups"] if group.get("status") == "completed"]

    def update_group_status(self, plan, group_name, status, completion_time=None):
        """更新组状态"""
        group = self.find_group_by_name(plan, group_name)
        if group:
            group["status"] = status
            if completion_time:
                group["completed_at"] = completion_time
            return True
        return False

    def get_completion_stats(self, plan):
        """获取完成统计"""
        total_groups = len(plan["groups"])
        assigned_groups = sum(1 for g in plan["groups"] if g.get("assignee"))
        completed_groups = sum(1 for g in plan["groups"] if g.get("status") == "completed")

        total_files = plan["total_files"]
        assigned_files = sum(g.get("file_count", len(g["files"])) for g in plan["groups"] if g.get("assignee"))
        completed_files = sum(g.get("file_count", len(g["files"])) for g in plan["groups"] if g.get("status") == "completed")

        return {
            "total_groups": total_groups,
            "assigned_groups": assigned_groups,
            "completed_groups": completed_groups,
            "total_files": total_files,
            "assigned_files": assigned_files,
            "completed_files": completed_files
        }