"""
Git Merge Orchestrator - 忽略规则管理器
负责管理文件和目录的忽略规则，支持多种匹配模式
"""

import os
import re
import fnmatch
from pathlib import Path
from typing import List, Dict, Set, Optional, Union
import json
from datetime import datetime

from config import (
    DEFAULT_IGNORE_PATTERNS,
    IGNORE_RULE_TYPES,
    WORK_DIR_NAME,
    IGNORE_FILE_NAME,
)


class IgnoreManager:
    """忽略规则管理器 - 支持多种匹配模式和配置方式"""

    def __init__(self, repo_path: str = "."):
        """
        初始化忽略管理器
        
        Args:
            repo_path: 仓库根目录路径
        """
        self.repo_path = Path(repo_path).resolve()
        self.work_dir = self.repo_path / WORK_DIR_NAME
        self.ignore_file = self.repo_path / IGNORE_FILE_NAME
        self.config_file = self.work_dir / "ignore_config.json"

        # 忽略规则存储
        self.rules: List[Dict] = []
        self.compiled_patterns: Dict = {}

        # 统计信息
        self.stats = {
            "total_rules": 0,
            "enabled_rules": 0,
            "ignored_files": 0,
            "last_updated": None,
        }

        # 初始化
        self._load_ignore_rules()

    def _load_ignore_rules(self):
        """加载忽略规则 - 从多个源加载"""
        try:
            # 1. 加载默认规则
            self._load_default_rules()

            # 2. 加载项目级忽略文件
            self._load_ignore_file()

            # 3. 加载配置文件中的自定义规则
            self._load_config_rules()

            # 4. 编译规则
            self._compile_rules()

            # 5. 更新统计信息
            self._update_stats()

        except Exception as e:
            print(f"⚠️ 加载忽略规则失败: {e}")
            # 使用默认规则作为后备
            self._load_default_rules()
            self._compile_rules()

    def _load_default_rules(self):
        """加载默认忽略规则"""
        self.rules = []
        for pattern in DEFAULT_IGNORE_PATTERNS:
            self.rules.append(
                {
                    "pattern": pattern,
                    "type": "glob",
                    "enabled": True,
                    "source": "default",
                    "description": f"默认规则: {pattern}",
                    "created_at": datetime.now().isoformat(),
                }
            )

    def _load_ignore_file(self):
        """加载项目级.merge_ignore文件"""
        if not self.ignore_file.exists():
            return

        try:
            with open(self.ignore_file, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # 跳过空行和注释
                    if not line or line.startswith("#"):
                        continue

                    # 解析规则行 (支持 pattern:type 格式)
                    if ":" in line:
                        pattern, rule_type = line.split(":", 1)
                        pattern = pattern.strip()
                        rule_type = rule_type.strip()
                    else:
                        pattern = line
                        rule_type = "glob"

                    # 验证规则类型
                    if rule_type not in IGNORE_RULE_TYPES:
                        rule_type = "glob"

                    self.rules.append(
                        {
                            "pattern": pattern,
                            "type": rule_type,
                            "enabled": True,
                            "source": "ignore_file",
                            "description": f"项目规则: {pattern}",
                            "line_number": line_num,
                            "created_at": datetime.now().isoformat(),
                        }
                    )

        except Exception as e:
            print(f"⚠️ 读取忽略文件失败 {self.ignore_file}: {e}")

    def _load_config_rules(self):
        """加载配置文件中的自定义规则"""
        if not self.config_file.exists():
            return

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            custom_rules = config.get("custom_rules", [])
            for rule in custom_rules:
                if self._validate_rule(rule):
                    rule["source"] = "config"
                    self.rules.append(rule)

        except Exception as e:
            print(f"⚠️ 读取配置文件失败 {self.config_file}: {e}")

    def _validate_rule(self, rule: Dict) -> bool:
        """验证规则格式"""
        required_fields = ["pattern", "type"]
        return all(field in rule for field in required_fields)

    def _compile_rules(self):
        """编译规则以提高匹配性能"""
        self.compiled_patterns = {
            "glob": [],
            "regex": [],
            "exact": set(),
            "prefix": [],
            "suffix": [],
        }

        for rule in self.rules:
            if not rule.get("enabled", True):
                continue

            pattern = rule["pattern"]
            rule_type = rule["type"]

            try:
                if rule_type == "glob":
                    # glob模式直接存储
                    self.compiled_patterns["glob"].append(pattern)

                elif rule_type == "regex":
                    # 编译正则表达式
                    compiled_regex = re.compile(pattern)
                    self.compiled_patterns["regex"].append(compiled_regex)

                elif rule_type == "exact":
                    # 精确匹配使用集合
                    self.compiled_patterns["exact"].add(pattern)

                elif rule_type == "prefix":
                    # 前缀匹配
                    self.compiled_patterns["prefix"].append(pattern)

                elif rule_type == "suffix":
                    # 后缀匹配
                    self.compiled_patterns["suffix"].append(pattern)

            except Exception as e:
                print(f"⚠️ 编译规则失败 {pattern}: {e}")

    def should_ignore(self, file_path: Union[str, Path]) -> bool:
        """
        检查文件是否应该被忽略
        
        Args:
            file_path: 文件路径 (相对或绝对)
            
        Returns:
            bool: True表示应该忽略
        """
        if isinstance(file_path, Path):
            file_path = str(file_path)

        # 规范化路径 (使用相对路径进行匹配)
        try:
            abs_path = Path(file_path).resolve()
            if abs_path.is_relative_to(self.repo_path):
                rel_path = abs_path.relative_to(self.repo_path)
                normalized_path = str(rel_path).replace("\\", "/")
            else:
                normalized_path = str(Path(file_path)).replace("\\", "/")
        except:
            normalized_path = str(Path(file_path)).replace("\\", "/")

        # 检查路径是否为目录
        is_directory = self._is_directory_path(file_path, normalized_path)

        # 按类型进行匹配，传递目录信息用于更精确的匹配
        return (
            self._match_exact(normalized_path)
            or self._match_glob_with_type(normalized_path, is_directory)
            or self._match_regex(normalized_path)
            or self._match_prefix(normalized_path)
            or self._match_suffix(normalized_path)
        )

    def _is_directory_path(self, original_path: str, normalized_path: str) -> bool:
        """
        判断路径是否为目录
        
        Args:
            original_path: 原始路径
            normalized_path: 规范化后的相对路径
            
        Returns:
            bool: True表示是目录
        """
        # 方法1: 路径以/结尾，明确表示目录
        if normalized_path.endswith("/") or original_path.endswith("/"):
            return True

        # 方法2: 检查实际文件系统（如果文件存在）
        try:
            full_path = self.repo_path / normalized_path
            if full_path.exists():
                return full_path.is_dir()
        except:
            pass

        # 方法3: 启发式判断 - 更保守的方法
        # 只有在明确指示为目录时才返回True，否则假设为文件
        # 这避免了将无扩展名文件误判为目录

        return False

    def _match_glob_with_type(self, path: str, is_directory: bool) -> bool:
        """带类型信息的glob匹配"""
        for pattern in self.compiled_patterns["glob"]:
            if self._match_single_pattern_with_type(path, pattern, is_directory):
                return True
        return False

    def _match_single_pattern_with_type(
        self, path: str, pattern: str, is_directory: bool
    ) -> bool:
        """考虑文件类型的单个模式匹配"""
        # 目录模式处理
        if pattern.endswith("/"):
            # 目录模式：只能匹配目录或目录内的文件，不能匹配同名文件
            return self._match_directory_pattern(path, pattern)
        else:
            # 文件模式：可以匹配文件或目录（取决于具体实现）
            # 但是对于通配符模式，优先使用fnmatch
            if "**" in pattern or "*" in pattern or "?" in pattern:
                if fnmatch.fnmatch(path, pattern):
                    return True

            # 精确文件匹配
            return self._match_file_pattern(path, pattern)

    def _path_in_directory(self, path: str, dir_pattern: str) -> bool:
        """检查路径是否在指定目录下"""
        dir_name = dir_pattern.rstrip("/")
        return path.startswith(dir_name + "/") or "/" + dir_name + "/" in path

    def _match_exact(self, path: str) -> bool:
        """精确匹配"""
        return path in self.compiled_patterns["exact"]

    def _match_glob(self, path: str) -> bool:
        """
        Glob模式匹配 - 支持精确匹配和通配符匹配 (兼容性方法)
        
        匹配规则:
        - `settings/` -> 只匹配根目录下的 settings/ 目录
        - `**/settings/` -> 匹配任意嵌套位置的 settings/ 目录
        - `*.py` -> 匹配任意位置的 .py 文件
        """
        # 使用改进的类型感知匹配
        is_directory = self._is_directory_path(path, path)
        return self._match_glob_with_type(path, is_directory)

    def _match_single_pattern(self, path: str, pattern: str) -> bool:
        """匹配单个glob模式"""
        # 直接glob匹配（处理通配符模式）
        if fnmatch.fnmatch(path, pattern):
            return True

        # 目录模式处理
        if pattern.endswith("/"):
            return self._match_directory_pattern(path, pattern)
        else:
            return self._match_file_pattern(path, pattern)

    def _match_directory_pattern(self, path: str, pattern: str) -> bool:
        """匹配目录模式"""
        pattern_without_slash = pattern.rstrip("/")

        # 检查是否为通配符模式 (**/directory/)
        if pattern.startswith("**/"):
            # 通配符模式：匹配任意嵌套位置
            clean_pattern = pattern_without_slash[3:]  # 移除 **/
            return self._match_nested_directory(path, clean_pattern)
        else:
            # 精确模式：只匹配根目录或指定位置
            return self._match_exact_directory(path, pattern_without_slash)

    def _match_exact_directory(self, path: str, pattern: str) -> bool:
        """精确目录匹配 - 只匹配根目录或精确路径位置"""
        # 情况1: 文件在目录下 (settings/ 匹配 settings/config.json)
        if path.startswith(pattern + "/"):
            return True

        # 情况2: 路径以/结尾，明确表示是目录，或者路径本身就是目录名
        if path.endswith("/") and (
            path == pattern + "/" or path.rstrip("/") == pattern
        ):
            return True

        # 情况2.5: 路径本身就是目录名（用于匹配目录本身）
        # 只有在路径明确是目录时才匹配，避免误匹配同名文件
        if path == pattern:
            full_path = self.repo_path / path
            try:
                if full_path.exists():
                    return full_path.is_dir()
            except:
                pass
            # 对于不存在的路径，不进行匹配（保守策略）
            return False

        # 情况3: 支持部分路径匹配 (如 app/settings/ 模式)
        if "/" in pattern:
            # 如果模式包含路径分隔符，需要精确路径匹配
            path_parts = path.split("/")
            pattern_parts = pattern.split("/")

            # 检查是否在任意起始位置匹配完整的模式路径
            for i in range(len(path_parts) - len(pattern_parts) + 1):
                if path_parts[i : i + len(pattern_parts)] == pattern_parts:
                    return True

        # 注意：对于settings/模式，不匹配单独的settings文件
        # 只有在路径明确是目录（包含子路径或以/结尾）时才匹配
        return False

    def _match_nested_directory(self, path: str, directory_name: str) -> bool:
        """嵌套目录匹配 - 匹配任意位置的目录"""
        path_parts = path.split("/")

        # 检查路径中是否有任何部分匹配目录名
        for i, part in enumerate(path_parts):
            if part == directory_name:
                # 确认这确实是一个目录（不是文件名的一部分）
                # 如果是最后一个部分，检查是否还有后续路径
                if i < len(path_parts) - 1:
                    return True
                # 如果是最后一个部分，但路径以/结尾，也算目录
                if path.endswith("/"):
                    return True

            # 支持通配符匹配目录名
            if fnmatch.fnmatch(part, directory_name):
                if i < len(path_parts) - 1 or path.endswith("/"):
                    return True

        return False

    def _match_file_pattern(self, path: str, pattern: str) -> bool:
        """文件模式匹配"""
        # 如果模式不包含路径分隔符，匹配任意位置的文件名
        if "/" not in pattern:
            filename = os.path.basename(path)
            # 精确匹配文件名
            return filename == pattern or fnmatch.fnmatch(filename, pattern)
        else:
            # 包含路径的精确匹配
            return fnmatch.fnmatch(path, pattern)

    def _match_regex(self, path: str) -> bool:
        """正则表达式匹配"""
        for compiled_regex in self.compiled_patterns["regex"]:
            if compiled_regex.search(path):
                return True
        return False

    def _match_prefix(self, path: str) -> bool:
        """前缀匹配"""
        for prefix in self.compiled_patterns["prefix"]:
            if path.startswith(prefix):
                return True
        return False

    def _match_suffix(self, path: str) -> bool:
        """后缀匹配"""
        for suffix in self.compiled_patterns["suffix"]:
            if path.endswith(suffix):
                return True
        return False

    def filter_files(self, file_list: List[str]) -> List[str]:
        """
        过滤文件列表，移除应该忽略的文件
        
        Args:
            file_list: 文件路径列表
            
        Returns:
            List[str]: 过滤后的文件列表
        """
        filtered_files = []
        ignored_count = 0

        for file_path in file_list:
            if self.should_ignore(file_path):
                ignored_count += 1
            else:
                filtered_files.append(file_path)

        # 更新统计信息
        self.stats["ignored_files"] = ignored_count

        return filtered_files

    def add_rule(
        self,
        pattern: str,
        rule_type: str = "glob",
        description: str = "",
        enabled: bool = True,
    ) -> bool:
        """
        添加新的忽略规则
        
        Args:
            pattern: 匹配模式
            rule_type: 规则类型
            description: 规则描述
            enabled: 是否启用
            
        Returns:
            bool: 添加是否成功
        """
        if rule_type not in IGNORE_RULE_TYPES:
            print(f"❌ 不支持的规则类型: {rule_type}")
            return False

        rule = {
            "pattern": pattern,
            "type": rule_type,
            "enabled": enabled,
            "source": "user_added",
            "description": description or f"用户添加: {pattern}",
            "created_at": datetime.now().isoformat(),
        }

        self.rules.append(rule)
        self._compile_rules()
        self._update_stats()

        # 保存到配置文件
        self._save_config()

        return True

    def remove_rule(self, pattern: str, rule_type: str = None) -> bool:
        """
        移除忽略规则
        
        Args:
            pattern: 匹配模式
            rule_type: 规则类型 (可选，用于精确匹配)
            
        Returns:
            bool: 移除是否成功
        """
        original_count = len(self.rules)

        if rule_type:
            self.rules = [
                r
                for r in self.rules
                if not (r["pattern"] == pattern and r["type"] == rule_type)
            ]
        else:
            self.rules = [r for r in self.rules if r["pattern"] != pattern]

        removed_count = original_count - len(self.rules)

        if removed_count > 0:
            self._compile_rules()
            self._update_stats()
            self._save_config()
            return True

        return False

    def toggle_rule(self, pattern: str, rule_type: str = None) -> bool:
        """
        切换规则启用状态
        
        Args:
            pattern: 匹配模式
            rule_type: 规则类型 (可选)
            
        Returns:
            bool: 操作是否成功
        """
        for rule in self.rules:
            if rule["pattern"] == pattern:
                if rule_type is None or rule["type"] == rule_type:
                    rule["enabled"] = not rule.get("enabled", True)
                    rule["updated_at"] = datetime.now().isoformat()

                    self._compile_rules()
                    self._update_stats()
                    self._save_config()
                    return True

        return False

    def list_rules(self, enabled_only: bool = False) -> List[Dict]:
        """
        列出所有忽略规则
        
        Args:
            enabled_only: 是否只返回启用的规则
            
        Returns:
            List[Dict]: 规则列表
        """
        if enabled_only:
            return [r for r in self.rules if r.get("enabled", True)]
        return self.rules.copy()

    def get_rule_stats(self) -> Dict:
        """获取规则统计信息"""
        return self.stats.copy()

    def _update_stats(self):
        """更新统计信息"""
        self.stats.update(
            {
                "total_rules": len(self.rules),
                "enabled_rules": len([r for r in self.rules if r.get("enabled", True)]),
                "last_updated": datetime.now().isoformat(),
            }
        )

    def _save_config(self):
        """保存配置到文件"""
        try:
            self.work_dir.mkdir(exist_ok=True)

            # 只保存用户添加的规则
            user_rules = [
                r for r in self.rules if r.get("source") in ["user_added", "config"]
            ]

            config = {
                "custom_rules": user_rules,
                "stats": self.stats,
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
            }

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"⚠️ 保存配置失败: {e}")

    def export_ignore_file(self, file_path: Optional[str] = None) -> bool:
        """
        导出忽略规则到.merge_ignore文件
        
        Args:
            file_path: 导出文件路径 (可选)
            
        Returns:
            bool: 导出是否成功
        """
        if file_path is None:
            file_path = self.ignore_file
        else:
            file_path = Path(file_path)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("# Git Merge Orchestrator 忽略规则文件\n")
                f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("# 格式: pattern 或 pattern:type\n")
                f.write("# 支持的类型: glob, regex, exact, prefix, suffix\n\n")

                # 按来源分组写入
                sources = ["default", "ignore_file", "config", "user_added"]
                for source in sources:
                    source_rules = [
                        r
                        for r in self.rules
                        if r.get("source") == source and r.get("enabled", True)
                    ]

                    if source_rules:
                        f.write(f"# {source.replace('_', ' ').title()} Rules\n")
                        for rule in source_rules:
                            pattern = rule["pattern"]
                            rule_type = rule["type"]

                            if rule_type == "glob":
                                f.write(f"{pattern}\n")
                            else:
                                f.write(f"{pattern}:{rule_type}\n")
                        f.write("\n")

            return True

        except Exception as e:
            print(f"❌ 导出忽略文件失败: {e}")
            return False

    def test_pattern(self, pattern: str, rule_type: str, test_files: List[str]) -> Dict:
        """
        测试忽略模式
        
        Args:
            pattern: 测试模式
            rule_type: 规则类型
            test_files: 测试文件列表
            
        Returns:
            Dict: 测试结果
        """
        # 创建临时规则进行测试
        temp_rule = {
            "pattern": pattern,
            "type": rule_type,
            "enabled": True,
            "source": "test",
        }

        # 保存当前规则
        original_rules = self.rules.copy()

        try:
            # 临时添加测试规则
            self.rules = [temp_rule]
            self._compile_rules()

            # 测试文件
            matched_files = []
            unmatched_files = []

            for file_path in test_files:
                if self.should_ignore(file_path):
                    matched_files.append(file_path)
                else:
                    unmatched_files.append(file_path)

            return {
                "pattern": pattern,
                "type": rule_type,
                "matched_files": matched_files,
                "unmatched_files": unmatched_files,
                "match_count": len(matched_files),
                "total_count": len(test_files),
            }

        finally:
            # 恢复原始规则
            self.rules = original_rules
            self._compile_rules()
