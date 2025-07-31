"""
Git Merge Orchestrator - 查询管理器
提供多维度查询功能：文件、文件夹、负责人查询
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from ui.display_helper import DisplayHelper


class QueryManager:
    """多维度查询管理器"""

    def __init__(self, file_helper, contributor_analyzer):
        self.file_helper = file_helper
        self.contributor_analyzer = contributor_analyzer

    def search_file_status(self, query: str, pattern_type: str = "simple") -> Dict[str, Any]:
        """按文件查询合并状态

        Args:
            query: 查询字符串（文件名或模式）
            pattern_type: 匹配类型 ('simple', 'glob', 'regex')

        Returns:
            包含查询结果的字典
        """
        plan = self.file_helper.load_plan()
        if not plan:
            return {"error": "未找到合并计划"}

        results = {
            "query": query,
            "pattern_type": pattern_type,
            "matches": [],
            "total_matches": 0,
            "groups_affected": 0,
        }

        groups_with_matches = set()

        for group in plan["groups"]:
            group_matches = []

            for file_path in group["files"]:
                if self._match_file(file_path, query, pattern_type):
                    # 获取文件级分配信息（如果存在）
                    file_assignment = None
                    if "file_assignments" in group:
                        file_assignment = group["file_assignments"].get(file_path, {})

                    match_info = {
                        "file_path": file_path,
                        "group_name": group["name"],
                        "group_assignee": group.get("assignee", "未分配"),
                        "group_status": group.get("status", "pending"),
                        "assignment_reason": group.get("assignment_reason", ""),
                        "file_assignment": file_assignment,
                    }

                    group_matches.append(match_info)
                    groups_with_matches.add(group["name"])

            results["matches"].extend(group_matches)

        results["total_matches"] = len(results["matches"])
        results["groups_affected"] = len(groups_with_matches)

        return results

    def search_directory_status(self, directory_path: str, recursive: bool = True) -> Dict[str, Any]:
        """按文件夹查询合并状态

        Args:
            directory_path: 目录路径
            recursive: 是否递归查询子目录

        Returns:
            包含查询结果的字典
        """
        plan = self.file_helper.load_plan()
        if not plan:
            return {"error": "未找到合并计划"}

        # 规范化目录路径
        normalized_dir = directory_path.rstrip("/")

        results = {
            "directory": normalized_dir,
            "recursive": recursive,
            "groups": [],
            "files": [],
            "summary": {
                "total_groups": 0,
                "total_files": 0,
                "assigned_groups": 0,
                "completed_groups": 0,
                "assignees": set(),
            },
        }

        for group in plan["groups"]:
            group_files_in_dir = []

            for file_path in group["files"]:
                if self._file_in_directory(file_path, normalized_dir, recursive):
                    group_files_in_dir.append(file_path)

            if group_files_in_dir:
                group_info = {
                    "name": group["name"],
                    "assignee": group.get("assignee", "未分配"),
                    "status": group.get("status", "pending"),
                    "assignment_reason": group.get("assignment_reason", ""),
                    "files_in_directory": group_files_in_dir,
                    "files_count": len(group_files_in_dir),
                    "total_files": group.get("file_count", len(group["files"])),
                }

                results["groups"].append(group_info)
                results["files"].extend(group_files_in_dir)

                # 更新统计信息
                results["summary"]["total_groups"] += 1
                results["summary"]["total_files"] += len(group_files_in_dir)

                if group.get("assignee") and group["assignee"] != "未分配":
                    results["summary"]["assigned_groups"] += 1
                    results["summary"]["assignees"].add(group["assignee"])

                if group.get("status") == "completed":
                    results["summary"]["completed_groups"] += 1

        # 转换 assignees 为列表
        results["summary"]["assignees"] = list(results["summary"]["assignees"])

        return results

    def search_assignee_status(self, assignee_name: str, fuzzy: bool = False) -> Dict[str, Any]:
        """按负责人查询任务状态（增强版）

        Args:
            assignee_name: 负责人姓名
            fuzzy: 是否模糊匹配

        Returns:
            包含查询结果的字典
        """
        plan = self.file_helper.load_plan()
        if not plan:
            return {"error": "未找到合并计划"}

        results = {
            "assignee": assignee_name,
            "fuzzy_search": fuzzy,
            "groups": [],
            "files": [],
            "summary": {
                "total_groups": 0,
                "total_files": 0,
                "completed_groups": 0,
                "completed_files": 0,
                "pending_groups": 0,
                "file_level_assignments": 0,
            },
        }

        for group in plan["groups"]:
            group_assignee = group.get("assignee", "")

            # 检查是否匹配
            if self._match_assignee(group_assignee, assignee_name, fuzzy):
                group_info = {
                    "name": group["name"],
                    "assignee": group_assignee,
                    "status": group.get("status", "pending"),
                    "assignment_reason": group.get("assignment_reason", ""),
                    "files": group["files"],
                    "file_count": group.get("file_count", len(group["files"])),
                    "file_assignments": group.get("file_assignments", {}),
                }

                results["groups"].append(group_info)
                results["files"].extend(group["files"])

                # 更新统计信息
                results["summary"]["total_groups"] += 1
                results["summary"]["total_files"] += len(group["files"])

                if group.get("status") == "completed":
                    results["summary"]["completed_groups"] += 1
                    results["summary"]["completed_files"] += len(group["files"])
                else:
                    results["summary"]["pending_groups"] += 1

                # 统计文件级分配
                if "file_assignments" in group:
                    file_level_count = sum(
                        1 for fa in group["file_assignments"].values() if fa.get("assignee") == assignee_name
                    )
                    results["summary"]["file_level_assignments"] += file_level_count

        return results

    def get_query_suggestions(self, query_type: str, partial_input: str = "") -> List[str]:
        """获取查询建议

        Args:
            query_type: 查询类型 ('file', 'directory', 'assignee')
            partial_input: 部分输入内容

        Returns:
            建议列表
        """
        plan = self.file_helper.load_plan()
        if not plan:
            return []

        suggestions = []

        if query_type == "file":
            # 收集所有文件名和扩展名
            file_extensions = set()
            file_names = set()

            for group in plan["groups"]:
                for file_path in group["files"]:
                    file_name = Path(file_path).name
                    file_ext = Path(file_path).suffix

                    if not partial_input or partial_input.lower() in file_name.lower():
                        file_names.add(file_name)

                    if file_ext:
                        file_extensions.add(f"*.{file_ext.lstrip('.')}")

            suggestions.extend(sorted(file_names)[:10])
            suggestions.extend(sorted(file_extensions))

        elif query_type == "directory":
            # 收集所有目录路径
            directories = set()

            for group in plan["groups"]:
                for file_path in group["files"]:
                    dir_path = str(Path(file_path).parent)
                    if dir_path != ".":
                        directories.add(dir_path)

                        # 添加父目录
                        parent_parts = Path(dir_path).parts
                        for i in range(1, len(parent_parts)):
                            parent_dir = "/".join(parent_parts[:i])
                            if parent_dir:
                                directories.add(parent_dir)

            if partial_input:
                suggestions = [d for d in directories if partial_input.lower() in d.lower()]
            else:
                suggestions = list(directories)

            suggestions = sorted(suggestions)[:15]

        elif query_type == "assignee":
            # 收集所有负责人
            assignees = set()

            for group in plan["groups"]:
                assignee = group.get("assignee")
                if assignee and assignee != "未分配":
                    assignees.add(assignee)

            if partial_input:
                suggestions = [a for a in assignees if partial_input.lower() in a.lower()]
            else:
                suggestions = list(assignees)

            suggestions = sorted(suggestions)

        return suggestions

    def _match_file(self, file_path: str, query: str, pattern_type: str) -> bool:
        """匹配文件路径"""
        if pattern_type == "simple":
            return query.lower() in file_path.lower()
        elif pattern_type == "glob":
            from fnmatch import fnmatch

            return fnmatch(file_path, query)
        elif pattern_type == "regex":
            try:
                return bool(re.search(query, file_path, re.IGNORECASE))
            except re.error:
                return False
        return False

    def _file_in_directory(self, file_path: str, directory: str, recursive: bool) -> bool:
        """检查文件是否在指定目录中"""
        file_dir = str(Path(file_path).parent)

        if not recursive:
            return file_dir == directory
        else:
            return file_dir == directory or file_dir.startswith(directory + "/")

    def _match_assignee(self, assignee: str, query: str, fuzzy: bool) -> bool:
        """匹配负责人姓名"""
        if not assignee or assignee == "未分配":
            return False

        if fuzzy:
            return query.lower() in assignee.lower()
        else:
            return assignee == query

    def generate_query_report(self, query_results: Dict[str, Any], output_format: str = "table") -> str:
        """生成查询结果报告

        Args:
            query_results: 查询结果
            output_format: 输出格式 ('table', 'summary', 'detailed')

        Returns:
            格式化的报告字符串
        """
        if "error" in query_results:
            return f"❌ 查询失败: {query_results['error']}"

        report = []

        if "query" in query_results:  # 文件查询结果
            report.append(f"📄 文件查询结果: {query_results['query']}")
            report.append(f"匹配模式: {query_results['pattern_type']}")
            report.append(f"找到 {query_results['total_matches']} 个文件，涉及 {query_results['groups_affected']} 个组")

            if output_format == "table" and query_results["matches"]:
                report.append("\n📋 详细结果:")
                for match in query_results["matches"][:10]:  # 限制显示数量
                    report.append(f"  📄 {match['file_path']}")
                    report.append(f"     组: {match['group_name']}")
                    report.append(f"     负责人: {match['group_assignee']}")
                    report.append(f"     状态: {match['group_status']}")
                    if match.get("file_assignment"):
                        fa = match["file_assignment"]
                        if fa.get("assignee"):
                            report.append(f"     文件负责人: {fa['assignee']}")
                    report.append("")

        elif "directory" in query_results:  # 目录查询结果
            report.append(f"📁 目录查询结果: {query_results['directory']}")
            report.append(f"递归查询: {'是' if query_results['recursive'] else '否'}")

            summary = query_results["summary"]
            report.append(f"📊 统计: {summary['total_groups']} 组, {summary['total_files']} 文件")
            report.append(f"已分配: {summary['assigned_groups']} 组, 已完成: {summary['completed_groups']} 组")

            if summary["assignees"]:
                report.append(f"涉及负责人: {', '.join(summary['assignees'])}")

        elif "assignee" in query_results:  # 负责人查询结果
            report.append(f"👤 负责人查询结果: {query_results['assignee']}")

            summary = query_results["summary"]
            report.append(f"📊 负责组数: {summary['total_groups']}")
            report.append(f"📄 负责文件数: {summary['total_files']}")
            report.append(f"✅ 已完成组数: {summary['completed_groups']}")
            report.append(f"⏳ 待处理组数: {summary['pending_groups']}")

            if summary.get("file_level_assignments", 0) > 0:
                report.append(f"📋 文件级分配: {summary['file_level_assignments']} 个文件")

        return "\n".join(report)
