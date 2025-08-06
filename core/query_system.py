"""
Git Merge Orchestrator - 高级查询系统
提供多维度查询功能，支持模糊匹配和反向查询
"""

import re
import difflib
from typing import List, Dict, Any, Optional, Union, Set
from pathlib import Path
import fnmatch
from datetime import datetime


class QuerySystem:
    """高级查询系统 - 支持多维度查询和模糊匹配"""

    def __init__(self, plan_manager, contributor_analyzer=None, ignore_manager=None):
        """
        初始化查询系统
        
        Args:
            plan_manager: 计划管理器
            contributor_analyzer: 贡献者分析器 (可选)
            ignore_manager: 忽略规则管理器 (可选)
        """
        self.plan_manager = plan_manager
        self.contributor_analyzer = contributor_analyzer
        self.ignore_manager = ignore_manager

        # 查询缓存
        self._query_cache = {}
        self._cache_timeout = 300  # 5分钟缓存过期

        # 模糊匹配阈值
        self.fuzzy_threshold = 0.6
        
    def _load_plan_data(self):
        """统一的计划数据加载方法，兼容不同的计划管理器"""
        try:
            # 支持不同的计划管理器接口
            if hasattr(self.plan_manager, 'load_plan'):
                # FileHelper 或 PlanManager
                return self.plan_manager.load_plan()
            elif hasattr(self.plan_manager, 'file_manager') and hasattr(self.plan_manager.file_manager, 'load_file_plan'):
                # FilePlanManager
                plan = self.plan_manager.file_manager.load_file_plan()
                if plan and 'files' in plan:
                    # 转换文件级计划为组格式以保持兼容性
                    return self._convert_file_plan_to_group_format(plan)
                return plan
            else:
                print("⚠️ 未识别的计划管理器类型")
                return None
        except Exception as e:
            print(f"⚠️ 加载计划数据失败: {e}")
            return None
            
    def _convert_file_plan_to_group_format(self, file_plan):
        """将文件级计划转换为组格式以保持查询兼容性"""
        try:
            # 创建虚拟组结构
            groups = []
            for file_data in file_plan.get('files', []):
                # 每个文件作为一个组
                group = {
                    'name': f"file_{file_data.get('path', 'unknown')}",
                    'group_name': file_data.get('path', 'unknown'),
                    'files': [file_data.get('path', 'unknown')],
                    'assignee': file_data.get('assignee', ''),
                    'status': file_data.get('status', 'pending'),
                    'assignment_reason': file_data.get('assignment_reason', ''),
                    'created_at': file_data.get('created_at', ''),
                    'updated_at': file_data.get('updated_at', ''),
                    'file_count': 1
                }
                groups.append(group)
                
            # 返回转换后的计划
            converted_plan = dict(file_plan)
            converted_plan['groups'] = groups
            return converted_plan
        except Exception as e:
            print(f"⚠️ 文件计划转换失败: {e}")
            return file_plan

    def query_by_assignee(
        self, name: str, fuzzy: bool = True, exact_match: bool = False
    ) -> Dict[str, Any]:
        """
        按负责人查询文件和状态
        
        Args:
            name: 负责人姓名或姓名模式
            fuzzy: 是否启用模糊匹配
            exact_match: 是否要求精确匹配
            
        Returns:
            Dict: 查询结果
        """
        cache_key = f"assignee_{name}_{fuzzy}_{exact_match}"
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result

        try:
            plan_data = self._load_plan_data()
            if not plan_data or "groups" not in plan_data:
                return self._empty_result("没有可用的计划数据")

            matched_assignees = self._match_assignees(
                name, plan_data["groups"], fuzzy, exact_match
            )

            result = {
                "query_type": "by_assignee",
                "query_pattern": name,
                "fuzzy_enabled": fuzzy,
                "exact_match": exact_match,
                "matched_assignees": list(matched_assignees),
                "results": [],
                "summary": {
                    "total_files": 0,
                    "total_groups": 0,
                    "status_breakdown": {},
                    "workload_stats": {},
                },
            }

            # 收集匹配的组和文件信息
            for group in plan_data["groups"]:
                assignee = group.get("assignee", "")
                if assignee in matched_assignees:
                    group_info = {
                        "group_name": group.get("group_name", ""),
                        "assignee": assignee,
                        "files": group.get("files", []),
                        "file_count": len(group.get("files", [])),
                        "status": group.get("status", "pending"),
                        "assignment_reason": group.get("assignment_reason", ""),
                        "created_at": group.get("created_at", ""),
                        "updated_at": group.get("updated_at", ""),
                    }

                    result["results"].append(group_info)
                    result["summary"]["total_files"] += group_info["file_count"]
                    result["summary"]["total_groups"] += 1

                    # 统计状态分布
                    status = group_info["status"]
                    result["summary"]["status_breakdown"][status] = (
                        result["summary"]["status_breakdown"].get(status, 0) + 1
                    )

            # 计算工作负载统计
            for assignee in matched_assignees:
                assignee_groups = [
                    r for r in result["results"] if r["assignee"] == assignee
                ]
                assignee_files = sum(g["file_count"] for g in assignee_groups)
                result["summary"]["workload_stats"][assignee] = {
                    "groups": len(assignee_groups),
                    "files": assignee_files,
                }

            # 缓存结果
            self._cache_result(cache_key, result)
            return result

        except Exception as e:
            return self._error_result(f"查询过程中出现错误: {e}")

    def query_by_file(
        self, pattern: str, fuzzy: bool = True, regex: bool = False
    ) -> Dict[str, Any]:
        """
        按文件名模式查询负责人和状态
        
        Args:
            pattern: 文件路径模式
            fuzzy: 是否启用模糊匹配
            regex: 是否使用正则表达式
            
        Returns:
            Dict: 查询结果
        """
        cache_key = f"file_{pattern}_{fuzzy}_{regex}"
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result

        try:
            plan_data = self._load_plan_data()
            if not plan_data or "groups" not in plan_data:
                return self._empty_result("没有可用的计划数据")

            result = {
                "query_type": "by_file",
                "query_pattern": pattern,
                "fuzzy_enabled": fuzzy,
                "regex_enabled": regex,
                "results": [],
                "summary": {
                    "matched_files": 0,
                    "matched_groups": 0,
                    "assignees": set(),
                    "status_breakdown": {},
                },
            }

            # 搜索匹配的文件
            for group in plan_data["groups"]:
                matched_files = []

                for file_path in group.get("files", []):
                    if self._match_file_pattern(file_path, pattern, fuzzy, regex):
                        matched_files.append(file_path)

                if matched_files:
                    group_info = {
                        "group_name": group.get("group_name", ""),
                        "assignee": group.get("assignee", ""),
                        "matched_files": matched_files,
                        "total_files": len(group.get("files", [])),
                        "match_count": len(matched_files),
                        "status": group.get("status", "pending"),
                        "assignment_reason": group.get("assignment_reason", ""),
                    }

                    result["results"].append(group_info)
                    result["summary"]["matched_files"] += len(matched_files)
                    result["summary"]["matched_groups"] += 1
                    result["summary"]["assignees"].add(group_info["assignee"])

                    # 统计状态分布
                    status = group_info["status"]
                    result["summary"]["status_breakdown"][status] = (
                        result["summary"]["status_breakdown"].get(status, 0) + 1
                    )

            # 转换集合为列表以便JSON序列化
            result["summary"]["assignees"] = list(result["summary"]["assignees"])

            # 缓存结果
            self._cache_result(cache_key, result)
            return result

        except Exception as e:
            return self._error_result(f"查询过程中出现错误: {e}")

    def query_by_status(
        self, status: str, include_details: bool = True
    ) -> Dict[str, Any]:
        """
        按合并状态查询
        
        Args:
            status: 状态名称 (pending, in_progress, completed, conflict 等)
            include_details: 是否包含详细信息
            
        Returns:
            Dict: 查询结果
        """
        cache_key = f"status_{status}_{include_details}"
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            return cached_result

        try:
            plan_data = self._load_plan_data()
            if not plan_data or "groups" not in plan_data:
                return self._empty_result("没有可用的计划数据")

            result = {
                "query_type": "by_status",
                "query_status": status,
                "include_details": include_details,
                "results": [],
                "summary": {
                    "total_groups": 0,
                    "total_files": 0,
                    "assignees": set(),
                    "assignment_reasons": {},
                },
            }

            # 搜索匹配状态的组
            for group in plan_data["groups"]:
                if group.get("status", "pending").lower() == status.lower():
                    group_info = {
                        "group_name": group.get("group_name", ""),
                        "assignee": group.get("assignee", ""),
                        "file_count": len(group.get("files", [])),
                        "status": group.get("status", "pending"),
                        "assignment_reason": group.get("assignment_reason", ""),
                        "created_at": group.get("created_at", ""),
                        "updated_at": group.get("updated_at", ""),
                    }

                    if include_details:
                        group_info["files"] = group.get("files", [])

                    result["results"].append(group_info)
                    result["summary"]["total_groups"] += 1
                    result["summary"]["total_files"] += group_info["file_count"]
                    result["summary"]["assignees"].add(group_info["assignee"])

                    # 统计分配原因
                    reason = group_info["assignment_reason"]
                    result["summary"]["assignment_reasons"][reason] = (
                        result["summary"]["assignment_reasons"].get(reason, 0) + 1
                    )

            # 转换集合为列表
            result["summary"]["assignees"] = list(result["summary"]["assignees"])

            # 缓存结果
            self._cache_result(cache_key, result)
            return result

        except Exception as e:
            return self._error_result(f"查询过程中出现错误: {e}")

    def advanced_search(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        高级组合查询
        
        Args:
            criteria: 查询条件字典
                - assignee: 负责人模式
                - file_pattern: 文件模式  
                - status: 状态
                - min_files: 最小文件数
                - max_files: 最大文件数
                - assignment_reason: 分配原因模式
                - date_range: 日期范围
                
        Returns:
            Dict: 查询结果
        """
        try:
            plan_data = self._load_plan_data()
            if not plan_data or "groups" not in plan_data:
                return self._empty_result("没有可用的计划数据")

            result = {
                "query_type": "advanced_search",
                "criteria": criteria,
                "results": [],
                "summary": {
                    "total_groups": 0,
                    "total_files": 0,
                    "matched_criteria": [],
                    "filter_stats": {},
                },
            }

            # 应用各种过滤条件
            for group in plan_data["groups"]:
                if self._match_advanced_criteria(group, criteria):
                    group_info = {
                        "group_name": group.get("group_name", ""),
                        "assignee": group.get("assignee", ""),
                        "files": group.get("files", []),
                        "file_count": len(group.get("files", [])),
                        "status": group.get("status", "pending"),
                        "assignment_reason": group.get("assignment_reason", ""),
                        "created_at": group.get("created_at", ""),
                        "updated_at": group.get("updated_at", ""),
                        "matched_criteria": self._get_matched_criteria(group, criteria),
                    }

                    result["results"].append(group_info)
                    result["summary"]["total_groups"] += 1
                    result["summary"]["total_files"] += group_info["file_count"]

            return result

        except Exception as e:
            return self._error_result(f"高级查询过程中出现错误: {e}")

    def reverse_query(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """
        反向查询 - 根据结果特征查找满足条件的记录
        
        Args:
            criteria: 反向查询条件
                - unassigned: 查找未分配的文件
                - overloaded: 查找工作量过重的负责人
                - empty_groups: 查找空组
                - conflicted: 查找有冲突的组
                
        Returns:
            Dict: 查询结果
        """
        try:
            plan_data = self._load_plan_data()
            if not plan_data or "groups" not in plan_data:
                return self._empty_result("没有可用的计划数据")

            result = {
                "query_type": "reverse_query",
                "criteria": criteria,
                "results": {
                    "unassigned_files": [],
                    "overloaded_assignees": [],
                    "empty_groups": [],
                    "problematic_groups": [],
                },
                "summary": {"issues_found": 0, "recommendations": []},
            }

            # 查找未分配的文件
            if criteria.get("unassigned", False):
                unassigned = self._find_unassigned_files(plan_data)
                result["results"]["unassigned_files"] = unassigned
                if unassigned:
                    result["summary"]["issues_found"] += len(unassigned)
                    result["summary"]["recommendations"].append(
                        f"发现 {len(unassigned)} 个未分配文件，建议重新分配"
                    )

            # 查找工作量过重的负责人
            if criteria.get("overloaded", False):
                overloaded = self._find_overloaded_assignees(
                    plan_data, criteria.get("max_files", 10)
                )
                result["results"]["overloaded_assignees"] = overloaded
                if overloaded:
                    result["summary"]["issues_found"] += len(overloaded)
                    result["summary"]["recommendations"].append(
                        f"发现 {len(overloaded)} 个负责人工作量过重，建议重新平衡"
                    )

            # 查找空组
            if criteria.get("empty_groups", False):
                empty = self._find_empty_groups(plan_data)
                result["results"]["empty_groups"] = empty
                if empty:
                    result["summary"]["issues_found"] += len(empty)
                    result["summary"]["recommendations"].append(
                        f"发现 {len(empty)} 个空组，建议清理"
                    )

            # 查找有问题的组
            if criteria.get("problematic", False):
                problematic = self._find_problematic_groups(plan_data)
                result["results"]["problematic_groups"] = problematic
                if problematic:
                    result["summary"]["issues_found"] += len(problematic)
                    result["summary"]["recommendations"].append(
                        f"发现 {len(problematic)} 个有问题的组，建议检查"
                    )

            return result

        except Exception as e:
            return self._error_result(f"反向查询过程中出现错误: {e}")

    def get_query_suggestions(self, partial_query: str) -> List[str]:
        """
        获取查询建议 - 基于历史数据提供智能建议
        
        Args:
            partial_query: 部分查询字符串
            
        Returns:
            List[str]: 建议列表
        """
        suggestions = []

        try:
            plan_data = self._load_plan_data()
            if not plan_data or "groups" not in plan_data:
                return suggestions

            # 收集所有可能的查询目标
            assignees = set()
            file_extensions = set()
            directories = set()
            statuses = set()

            for group in plan_data["groups"]:
                assignees.add(group.get("assignee", ""))
                statuses.add(group.get("status", "pending"))

                for file_path in group.get("files", []):
                    # 文件扩展名
                    ext = Path(file_path).suffix
                    if ext:
                        file_extensions.add(f"*{ext}")

                    # 目录路径
                    directory = str(Path(file_path).parent)
                    if directory != ".":
                        directories.add(f"{directory}/*")

            # 基于部分查询生成建议
            query_lower = partial_query.lower()

            # 负责人建议
            for assignee in assignees:
                if assignee and query_lower in assignee.lower():
                    suggestions.append(f"负责人: {assignee}")

            # 文件类型建议
            for ext in file_extensions:
                if query_lower in ext.lower():
                    suggestions.append(f"文件类型: {ext}")

            # 目录建议
            for directory in directories:
                if query_lower in directory.lower():
                    suggestions.append(f"目录: {directory}")

            # 状态建议
            for status in statuses:
                if query_lower in status.lower():
                    suggestions.append(f"状态: {status}")

            # 限制建议数量
            return suggestions[:10]

        except Exception:
            return suggestions

    # === 私有辅助方法 ===

    def _match_assignees(
        self, name: str, groups: List[Dict], fuzzy: bool, exact_match: bool
    ) -> Set[str]:
        """匹配负责人姓名"""
        matched = set()
        all_assignees = {
            group.get("assignee", "") for group in groups if group.get("assignee")
        }

        for assignee in all_assignees:
            if not assignee:
                continue

            if exact_match:
                if assignee == name:
                    matched.add(assignee)
            elif fuzzy:
                # 使用difflib进行模糊匹配
                similarity = difflib.SequenceMatcher(
                    None, name.lower(), assignee.lower()
                ).ratio()
                if similarity >= self.fuzzy_threshold:
                    matched.add(assignee)
                # 同时支持部分匹配
                elif (
                    name.lower() in assignee.lower() or assignee.lower() in name.lower()
                ):
                    matched.add(assignee)
            else:
                # 精确匹配（不区分大小写）
                if name.lower() == assignee.lower():
                    matched.add(assignee)

        return matched

    def _match_file_pattern(
        self, file_path: str, pattern: str, fuzzy: bool, regex: bool
    ) -> bool:
        """匹配文件路径模式"""
        if regex:
            try:
                return bool(re.search(pattern, file_path, re.IGNORECASE))
            except re.error:
                return False

        if fuzzy:
            # 模糊匹配：支持部分匹配和通配符
            if pattern.lower() in file_path.lower():
                return True
            # 尝试fnmatch模式匹配
            return fnmatch.fnmatch(file_path.lower(), pattern.lower())

        # 精确匹配
        return fnmatch.fnmatch(file_path, pattern)

    def _match_advanced_criteria(self, group: Dict, criteria: Dict) -> bool:
        """检查组是否匹配高级查询条件"""
        # 负责人条件
        if "assignee" in criteria:
            assignee_pattern = criteria["assignee"]
            group_assignee = group.get("assignee", "")
            if not self._match_assignees(assignee_pattern, [group], True, False):
                return False

        # 文件模式条件
        if "file_pattern" in criteria:
            file_pattern = criteria["file_pattern"]
            group_files = group.get("files", [])
            if not any(
                self._match_file_pattern(f, file_pattern, True, False)
                for f in group_files
            ):
                return False

        # 状态条件
        if "status" in criteria:
            if group.get("status", "pending").lower() != criteria["status"].lower():
                return False

        # 文件数量条件
        file_count = len(group.get("files", []))
        if "min_files" in criteria and file_count < criteria["min_files"]:
            return False
        if "max_files" in criteria and file_count > criteria["max_files"]:
            return False

        # 分配原因条件
        if "assignment_reason" in criteria:
            reason_pattern = criteria["assignment_reason"]
            group_reason = group.get("assignment_reason", "")
            if reason_pattern.lower() not in group_reason.lower():
                return False

        return True

    def _get_matched_criteria(self, group: Dict, criteria: Dict) -> List[str]:
        """获取匹配的条件列表"""
        matched = []

        if "assignee" in criteria and group.get("assignee"):
            matched.append("assignee")
        if "file_pattern" in criteria:
            matched.append("file_pattern")
        if "status" in criteria:
            matched.append("status")
        if "min_files" in criteria or "max_files" in criteria:
            matched.append("file_count")
        if "assignment_reason" in criteria:
            matched.append("assignment_reason")

        return matched

    def _find_unassigned_files(self, plan_data: Dict) -> List[str]:
        """查找未分配的文件"""
        unassigned = []
        for group in plan_data["groups"]:
            if not group.get("assignee") or group.get("assignee").strip() == "":
                unassigned.extend(group.get("files", []))
        return unassigned

    def _find_overloaded_assignees(self, plan_data: Dict, max_files: int) -> List[Dict]:
        """查找工作量过重的负责人"""
        assignee_workload = {}

        for group in plan_data["groups"]:
            assignee = group.get("assignee", "")
            if assignee:
                if assignee not in assignee_workload:
                    assignee_workload[assignee] = {"groups": 0, "files": 0}
                assignee_workload[assignee]["groups"] += 1
                assignee_workload[assignee]["files"] += len(group.get("files", []))

        overloaded = []
        for assignee, workload in assignee_workload.items():
            if workload["files"] > max_files:
                overloaded.append(
                    {
                        "assignee": assignee,
                        "file_count": workload["files"],
                        "group_count": workload["groups"],
                        "overload_ratio": workload["files"] / max_files,
                    }
                )

        return sorted(overloaded, key=lambda x: x["overload_ratio"], reverse=True)

    def _find_empty_groups(self, plan_data: Dict) -> List[Dict]:
        """查找空组"""
        empty = []
        for group in plan_data["groups"]:
            if not group.get("files") or len(group.get("files", [])) == 0:
                empty.append(
                    {
                        "group_name": group.get("group_name", ""),
                        "assignee": group.get("assignee", ""),
                        "status": group.get("status", "pending"),
                    }
                )
        return empty

    def _find_problematic_groups(self, plan_data: Dict) -> List[Dict]:
        """查找有问题的组"""
        problematic = []
        for group in plan_data["groups"]:
            issues = []

            # 检查是否有负责人
            if not group.get("assignee"):
                issues.append("missing_assignee")

            # 检查是否有文件
            if not group.get("files"):
                issues.append("no_files")

            # 检查状态是否合理
            status = group.get("status", "pending")
            if status not in ["pending", "in_progress", "completed", "conflict"]:
                issues.append("invalid_status")

            if issues:
                problematic.append(
                    {
                        "group_name": group.get("group_name", ""),
                        "assignee": group.get("assignee", ""),
                        "status": group.get("status", "pending"),
                        "issues": issues,
                        "issue_count": len(issues),
                    }
                )

        return sorted(problematic, key=lambda x: x["issue_count"], reverse=True)

    def _get_cached_result(self, cache_key: str) -> Optional[Dict]:
        """获取缓存结果"""
        if cache_key in self._query_cache:
            cached_data, timestamp = self._query_cache[cache_key]
            if (datetime.now().timestamp() - timestamp) < self._cache_timeout:
                return cached_data
            else:
                del self._query_cache[cache_key]
        return None

    def _cache_result(self, cache_key: str, result: Dict):
        """缓存查询结果"""
        self._query_cache[cache_key] = (result, datetime.now().timestamp())

    def _empty_result(self, message: str) -> Dict[str, Any]:
        """返回空结果"""
        return {"success": True, "message": message, "results": [], "summary": {}}

    def _error_result(self, message: str) -> Dict[str, Any]:
        """返回错误结果"""
        return {"success": False, "error": message, "results": [], "summary": {}}

    def clear_cache(self):
        """清除查询缓存"""
        self._query_cache.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        current_time = datetime.now().timestamp()
        active_entries = 0
        expired_entries = 0

        for cache_key, (_, timestamp) in self._query_cache.items():
            if (current_time - timestamp) < self._cache_timeout:
                active_entries += 1
            else:
                expired_entries += 1

        return {
            "total_entries": len(self._query_cache),
            "active_entries": active_entries,
            "expired_entries": expired_entries,
            "cache_timeout": self._cache_timeout,
            "hit_ratio": getattr(self, "_cache_hits", 0)
            / max(getattr(self, "_cache_requests", 1), 1),
        }
