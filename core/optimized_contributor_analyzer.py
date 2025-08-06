"""
Git Merge Orchestrator - 加速优化贡献者分析器
修复批量分析逻辑，确保结果准确性
"""

import json
import hashlib
import threading
from datetime import datetime, timedelta
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from config import (
    SCORING_WEIGHTS,
    DEFAULT_ANALYSIS_MONTHS,
    DEFAULT_ACTIVE_MONTHS,
    ENABLE_PERFORMANCE_MONITORING,
)
from core.ultra_fast_analyzer import UltraFastAnalyzer
from utils.performance_monitor import (
    performance_monitor,
    timing_context,
    global_performance_stats,
)
from utils.smart_cache import get_cache_manager


class OptimizedContributorAnalyzer:
    """优化贡献者分析器 - 修复批量分析逻辑"""

    def __init__(self, git_ops):
        self.git_ops = git_ops
        self.cache_file = (
            Path(git_ops.repo_path) / ".merge_work" / "contributor_cache.json"
        )
        self.cache_lock = threading.Lock()

        # 智能缓存管理器
        self.smart_cache = get_cache_manager(git_ops.repo_path)
        
        # 超高速分析器
        self.ultra_fast_analyzer = UltraFastAnalyzer(git_ops.repo_path)

        # 内存缓存（保留向后兼容）
        self._file_contributors_cache = {}
        self._directory_contributors_cache = {}
        self._active_contributors_cache = None
        self._all_contributors_cache = None

        # 批量数据缓存
        self._batch_file_data = {}
        self._batch_computed = False

    def load_persistent_cache(self):
        """加载持久化缓存"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)

                # 检查缓存有效性（24小时）
                cache_time = datetime.fromisoformat(
                    cache_data.get("created_at", "2000-01-01")
                )
                if datetime.now() - cache_time < timedelta(hours=24):
                    self._file_contributors_cache = cache_data.get(
                        "file_contributors", {}
                    )
                    self._directory_contributors_cache = cache_data.get(
                        "directory_contributors", {}
                    )
                    print(f"✅ 已加载贡献者缓存 ({len(self._file_contributors_cache)} 文件)")
                    return True
                else:
                    print("⏰ 缓存已过期，将重新计算")
        except Exception as e:
            print(f"⚠️ 加载缓存失败: {e}")
        return False

    def save_persistent_cache(self):
        """保存持久化缓存"""
        try:
            cache_data = {
                "created_at": datetime.now().isoformat(),
                "file_contributors": self._file_contributors_cache,
                "directory_contributors": self._directory_contributors_cache,
            }

            self.cache_file.parent.mkdir(exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            print(f"💾 已保存贡献者缓存")
        except Exception as e:
            print(f"⚠️ 保存缓存失败: {e}")

    @performance_monitor("批量分析")
    def batch_analyze_all_files(self, file_list, use_ultra_fast=True):
        """批量分析所有文件的贡献者信息
        
        Args:
            file_list: 文件列表
            use_ultra_fast: 是否使用超高速分析（默认True，>=10个文件时自动启用）
        """
        if self._batch_computed:
            return self._batch_file_data

        # 智能选择分析模式
        should_use_ultra = use_ultra_fast and len(file_list) >= 10
        
        if should_use_ultra:
            return self._ultra_fast_batch_analysis(file_list)
        else:
            return self._traditional_batch_analysis(file_list)
    
    def _ultra_fast_batch_analysis(self, file_list):
        """超高速批量分析"""
        main_start = datetime.now()
        print(f"🚀 [PERF] 使用超高速分析模式处理 {len(file_list)} 个文件... (开始时间: {main_start.timestamp():.3f})")
        
        # 使用超高速分析器
        ultra_start = datetime.now()
        ultra_results = self.ultra_fast_analyzer.analyze_contributors_ultra_fast(
            file_list, months=DEFAULT_ANALYSIS_MONTHS
        )
        ultra_time = (datetime.now() - ultra_start).total_seconds()
        print(f"⏱️  [PERF] 超高速分析器执行: {ultra_time:.3f}s")
        
        # 转换为兼容格式并缓存
        convert_start = datetime.now()
        for file_path, contributors in ultra_results.items():
            self._batch_file_data[file_path] = contributors
            # 同时更新文件缓存
            cache_key = self._get_file_cache_key(file_path)
            self._file_contributors_cache[cache_key] = contributors
        
        convert_time = (datetime.now() - convert_start).total_seconds()
        print(f"⏱️  [PERF] 格式转换和缓存: {convert_time:.3f}s")
        
        total_time = (datetime.now() - main_start).total_seconds()
        print(f"✅ [PERF] 超高速分析总完成时间: {total_time:.3f}s")
        print(f"📊 [PERF] 处理统计: 总计{len(file_list)}个文件, 平均{total_time/len(file_list)*1000:.1f}ms/文件")
        
        # 保存性能日志
        self._save_performance_log(file_list, total_time, {
            'ultra_analysis': ultra_time,
            'format_conversion': convert_time,
            'mode': 'optimized_ultra_fast'
        })
        
        self._batch_computed = True
        return self._batch_file_data
    
    def _traditional_batch_analysis(self, file_list):
        """传统批量分析（保留原有逻辑）"""
        main_start = datetime.now()
        print(f"📊 [PERF] 使用传统优化模式处理 {len(file_list)} 个文件... (开始时间: {main_start.timestamp():.3f})")
        print(f"⚡ [PERF] 性能优化提示：正在应用智能文件分类策略...")
        
        # 继续使用原有的传统分析逻辑，但添加详细计时
        print("🔍 [PERF] 开始传统分析流程...")

        # 继续使用原有的传统分析逻辑
        # 检查缓存
        cached_files = set()
        uncached_files = []

        for file_path in file_list:
            cache_key = self._get_file_cache_key(file_path)
            if cache_key in self._file_contributors_cache:
                self._batch_file_data[file_path] = self._file_contributors_cache[
                    cache_key
                ]
                cached_files.add(file_path)
            else:
                uncached_files.append(file_path)

        if cached_files:
            print(f"📦 从缓存获取 {len(cached_files)} 个文件的贡献者信息")

        if not uncached_files:
            print("✅ 所有文件都有缓存，跳过Git分析")
            self._batch_computed = True
            return self._batch_file_data

        print(f"🔍 需要分析 {len(uncached_files)} 个新文件")

        # 分离可能需要follow的文件和普通文件
        classification_start = datetime.now()
        critical_files, regular_files = self._classify_files_for_analysis(
            uncached_files
        )
        classification_time = (datetime.now() - classification_start).total_seconds()

        # 性能统计
        total_analysis_files = len(uncached_files)
        critical_ratio = (
            (len(critical_files) / total_analysis_files * 100)
            if total_analysis_files > 0
            else 0
        )

        print(f"📊 智能文件分类完成 ({classification_time:.3f}s):")
        print(
            f"   🎯 关键文件: {len(critical_files)} 个 ({critical_ratio:.1f}%) - 使用深度分析（--follow）"
        )
        print(f"   📋 普通文件: {len(regular_files)} 个 ({100-critical_ratio:.1f}%) - 使用批量分析")

        # 显示优化详情
        if critical_files:
            print(f"   📝 关键文件类型分析:")
            cpp_files = [
                f for f in critical_files if f.endswith((".cpp", ".h", ".hpp", ".c"))
            ]
            config_files = [
                f
                for f in critical_files
                if f.endswith((".json", ".yml", ".yaml", ".txt"))
            ]
            root_files = [f for f in critical_files if "/" not in f]

            if cpp_files:
                print(f"      • C++核心文件: {len(cpp_files)} 个")
            if config_files:
                print(f"      • 配置文件: {len(config_files)} 个")
            if root_files:
                print(f"      • 根目录文件: {len(root_files)} 个")

        if critical_ratio > 20:
            print(f"⚠️  性能警告：{critical_ratio:.1f}%的文件将使用深度分析，可能影响性能")
        elif critical_ratio > 10:
            print(f"💡 性能提示：{critical_ratio:.1f}%的文件使用深度分析，性能中等")
        else:
            print(f"✅ 性能优秀：仅{critical_ratio:.1f}%的文件使用深度分析，预期快速完成")

        # 对关键文件使用深度分析
        if critical_files:
            deep_analysis_start = datetime.now()
            for file_path in critical_files:
                contributors = self._analyze_single_file_with_follow(file_path)
                cache_key = self._get_file_cache_key(file_path)
                self._file_contributors_cache[cache_key] = contributors
                self._batch_file_data[file_path] = contributors
            deep_analysis_time = (datetime.now() - deep_analysis_start).total_seconds()
            avg_time_per_deep_file = deep_analysis_time / len(critical_files)
            print(
                f"🎯 深度分析完成: {len(critical_files)} 个文件, 耗时 {deep_analysis_time:.2f}s (平均 {avg_time_per_deep_file:.3f}s/文件)"
            )

        # 对普通文件使用批量分析
        if regular_files:
            batch_analysis_start = datetime.now()
            batch_results = self._fixed_batch_analyze_files(regular_files)
            for file_path, contributors in batch_results.items():
                cache_key = self._get_file_cache_key(file_path)
                self._file_contributors_cache[cache_key] = contributors
                self._batch_file_data[file_path] = contributors
            batch_analysis_time = (
                datetime.now() - batch_analysis_start
            ).total_seconds()
            avg_time_per_batch_file = (
                batch_analysis_time / len(regular_files) if regular_files else 0
            )
            print(
                f"📊 批量分析完成: {len(regular_files)} 个文件, 耗时 {batch_analysis_time:.2f}s (平均 {avg_time_per_batch_file:.3f}s/文件)"
            )

            # 性能对比
            if critical_files and regular_files:
                speedup_ratio = avg_time_per_deep_file / max(
                    avg_time_per_batch_file, 0.001
                )
                print(f"⚡ 性能对比：批量分析比深度分析快 {speedup_ratio:.1f}x")

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"⚡ 批量分析完成，用时 {elapsed:.2f} 秒")
        print(
            f"📊 处理统计: 总计{len(file_list)}, 缓存{len(cached_files)}, 深度分析{len(critical_files)}, 批量分析{len(regular_files)}"
        )

        # 性能监控报告 - 如果启用了性能监控
        if ENABLE_PERFORMANCE_MONITORING:
            analysis_stats = {
                "total_time": elapsed,
                "batch_time": batch_analysis_time if regular_files else 0,
                "single_time": deep_analysis_time if critical_files else 0,
                "total_files": len(file_list),
                "batch_files": len(regular_files),
                "single_files": len(critical_files),
                "critical_ratio": len(critical_files) / max(len(file_list), 1) * 100,
                "follow_usage": len(critical_files) / max(len(file_list), 1) * 100,
            }
            performance_report = self._generate_performance_report(analysis_stats)
            print("\n" + performance_report)

        # 保存缓存
        self.save_persistent_cache()
        
        # 保存性能日志
        total_time = (datetime.now() - main_start).total_seconds()
        self._save_performance_log(file_list, total_time, {
            'cache_check': cache_check_time if 'cache_check_time' in locals() else 0,
            'file_classification': classification_time if 'classification_time' in locals() else 0,
            'batch_analysis': batch_analysis_time if 'batch_analysis_time' in locals() else 0,
            'deep_analysis': deep_analysis_time if 'deep_analysis_time' in locals() else 0,
            'mode': 'optimized_traditional'
        })
        
        self._batch_computed = True
        return self._batch_file_data

    def _classify_files_for_analysis(self, file_list):
        """分类文件：哪些需要深度分析（--follow），哪些可以批量分析
        
        优化策略：大幅减少深度分析文件数量，只对真正可能重命名的核心文件使用--follow
        """
        critical_files = []
        regular_files = []

        # 更严格的关键文件判断条件，避免过度使用深度分析
        for file_path in file_list:
            is_critical = False

            # 1. 只有极少数核心文件才需要深度分析
            # Python/JavaScript核心文件
            python_js_patterns = [
                "main.py",
                "index.js",
                "index.ts",
                "app.py",
                "server.py",
                "__init__.py",
                "setup.py",
                "manage.py",
                "wsgi.py",
                "asgi.py",
            ]

            # C++核心文件
            cpp_patterns = [
                "main.cpp",
                "main.c",
                "main.h",
                "main.hpp",
                "app.cpp",
                "application.cpp",
                "core.cpp",
                "core.h",
                "engine.cpp",
                "engine.h",
                "manager.cpp",
                "manager.h",
            ]

            # 其他核心文件
            other_patterns = [
                "CMakeLists.txt",
                "Makefile",
                "configure",
                "config.h",
                "package.json",
                "pom.xml",
                "build.gradle",
            ]

            all_core_patterns = python_js_patterns + cpp_patterns + other_patterns

            file_name = file_path.split("/")[-1]
            if file_name in all_core_patterns:
                is_critical = True

            # 2. 根目录的重要配置文件
            elif "/" not in file_path and file_path.endswith(
                (".py", ".js", ".ts", ".json", ".yml", ".yaml", ".cpp", ".h", ".hpp")
            ):
                is_critical = True

            # 3. 明确的框架入口文件
            elif any(
                pattern in file_path.lower()
                for pattern in ["main/", "/main.", "entry", "bootstrap"]
            ):
                is_critical = True

            # 4. 数据文件和二进制文件永远不需要深度分析
            elif self._is_data_or_binary_file(file_path):
                is_critical = False  # 明确标记为非关键文件

            # 5. 检查是否可能有重命名历史（更严格的条件）
            elif self._should_check_rename_history_strict(file_path):
                is_critical = True

            if is_critical:
                critical_files.append(file_path)
            else:
                regular_files.append(file_path)

        # 安全限制：即使满足条件，也限制深度分析文件的比例
        total_files = len(file_list)
        max_critical_files = max(
            1, min(10, total_files // 10)
        )  # 最多10%的文件使用深度分析，至少1个，最多10个

        if len(critical_files) > max_critical_files:
            # 按重要性排序，只保留最重要的文件
            sorted_critical = self._sort_files_by_importance(critical_files)
            demoted_files = sorted_critical[max_critical_files:]
            critical_files = sorted_critical[:max_critical_files]
            regular_files.extend(demoted_files)

            print(
                f"⚡ 性能优化：限制深度分析文件数量从 {len(sorted_critical)} 降至 {len(critical_files)} 个"
            )

        return critical_files, regular_files

    def _is_data_or_binary_file(self, file_path):
        """检查是否为数据文件或二进制文件，这些文件通常不需要--follow分析"""
        data_extensions = [
            # 数据文件
            ".pcd",
            ".ply",
            ".las",
            ".laz",  # 点云数据
            ".bag",
            ".rosbag",  # ROS数据
            ".csv",
            ".xlsx",
            ".xls",
            ".db",
            ".sqlite",  # 表格数据
            ".json",
            ".xml",
            ".yaml",
            ".yml",  # 配置数据（但不在根目录）
            # 媒体文件
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".bmp",
            ".svg",  # 图片
            ".mp4",
            ".avi",
            ".mkv",
            ".mov",  # 视频
            ".mp3",
            ".wav",
            ".ogg",  # 音频
            # 二进制文件
            ".so",
            ".dll",
            ".dylib",  # 库文件
            ".exe",
            ".bin",
            ".out",  # 可执行文件
            ".zip",
            ".tar",
            ".gz",
            ".7z",
            ".rar",  # 压缩文件
            ".pdf",
            ".doc",
            ".docx",  # 文档文件
            # 缓存和临时文件
            ".cache",
            ".tmp",
            ".temp",
            ".log",
            ".pyc",
            ".pyo",
            ".class",  # 编译文件
        ]

        file_lower = file_path.lower()

        # 特殊处理：根目录的配置文件不应该被视为数据文件
        if "/" not in file_path and file_path.lower().endswith(
            (".json", ".yaml", ".yml", ".xml")
        ):
            return False

        # 检查文件扩展名
        if any(file_lower.endswith(ext) for ext in data_extensions):
            return True

        # 检查是否在数据目录中
        data_dirs = [
            "data/",
            "dataset/",
            "assets/",
            "resources/",
            "media/",
            "cache/",
            "tmp/",
        ]
        if any(data_dir in file_path.lower() for data_dir in data_dirs):
            return True

        return False

    def _should_check_rename_history_strict(self, file_path):
        """更严格的重命名历史检查，减少误判"""
        try:
            # 只有真正可能被重命名的文件才需要--follow
            refactor_indicators = [
                "legacy",
                "old",
                "deprecated",
                "migration",
                "refactor",
                "v1",
                "v2",
                "v3",
                "backup",
                "temp",
                "new",
                "tmp",
            ]

            path_lower = file_path.lower()
            # 检查文件名或目录名中是否有重构标识
            path_parts = path_lower.split("/")
            for part in path_parts:
                if any(indicator in part for indicator in refactor_indicators):
                    return True

            # 大幅降低深度阈值 - 只有极深的目录才可能有移动历史
            depth = file_path.count("/")
            if depth >= 6:  # 从4提高到6，减少误判
                # 但排除明显的数据目录
                if any(
                    data_dir in path_lower
                    for data_dir in [
                        "data/",
                        "dataset/",
                        "test/",
                        "tests/",
                        "examples/",
                    ]
                ):
                    return False
                return True

            return False
        except:
            return False

    def _should_check_rename_history(self, file_path):
        """判断文件是否可能有重命名历史，需要使用--follow"""
        try:
            # 快速检查：如果文件路径包含常见的重构标识，可能需要跟踪重命名
            refactor_indicators = [
                "legacy",
                "old",
                "deprecated",
                "migration",
                "refactor",
                "v1",
                "v2",
                "backup",
                "temp",
                "new",
            ]

            path_lower = file_path.lower()
            if any(indicator in path_lower for indicator in refactor_indicators):
                return True

            # 检查文件是否在深层目录（可能被移动过）
            depth = file_path.count("/")
            if depth >= 4:  # 深度>=4的文件更可能有移动历史
                return True

            return False
        except:
            return False

    def _sort_files_by_importance(self, file_list):
        """按重要性对文件排序，用于限制深度分析数量时的优先级"""

        def importance_score(file_path):
            score = 0
            file_name = file_path.split("/")[-1]

            # 核心文件得分最高
            if file_name in ["main.py", "index.js", "index.ts", "app.py"]:
                score += 100

            # 根目录文件得分较高
            if "/" not in file_path:
                score += 50

            # 特定关键词加分
            if any(
                keyword in file_path.lower()
                for keyword in ["main", "core", "entry", "bootstrap"]
            ):
                score += 30

            # 配置文件加分
            if file_path.endswith((".json", ".yml", ".yaml", ".cfg", ".ini")):
                score += 20

            return score

        return sorted(file_list, key=importance_score, reverse=True)

    def _analyze_single_file_with_follow(self, filepath):
        """单文件深度分析（支持重命名跟踪）- 使用智能缓存"""
        # 先检查智能缓存
        cache_result = self.smart_cache.get(
            "file_contributors", filepath, max_age_hours=12
        )
        if cache_result is not None:
            return cache_result

        try:
            contributors = {}

            # 获取一年内的贡献统计（使用--follow）
            one_year_ago = (
                datetime.now() - timedelta(days=DEFAULT_ANALYSIS_MONTHS * 30)
            ).strftime("%Y-%m-%d")

            recent_cmd = f'git log --follow --since="{one_year_ago}" --format="%an" -- "{filepath}"'
            recent_result = self.git_ops.run_command(recent_cmd)

            if recent_result:
                recent_authors = recent_result.split("\n")
                recent_author_counts = {}
                for author in recent_authors:
                    if author.strip():
                        recent_author_counts[author] = (
                            recent_author_counts.get(author, 0) + 1
                        )

                for author, count in recent_author_counts.items():
                    contributors[author] = {
                        "total_commits": count,
                        "recent_commits": count,
                        "score": count * SCORING_WEIGHTS["recent_commits"],
                    }

            # 获取总体贡献统计（使用--follow）
            total_cmd = f'git log --follow --format="%an" -- "{filepath}"'
            total_result = self.git_ops.run_command(total_cmd)

            if total_result:
                authors = total_result.split("\n")
                author_counts = {}
                for author in authors:
                    if author.strip():
                        author_counts[author] = author_counts.get(author, 0) + 1

                for author, count in author_counts.items():
                    if author in contributors:
                        contributors[author]["total_commits"] = count
                        contributors[author]["score"] = (
                            contributors[author]["recent_commits"]
                            * SCORING_WEIGHTS["recent_commits"]
                            + count * SCORING_WEIGHTS["total_commits"]
                        )
                    else:
                        contributors[author] = {
                            "total_commits": count,
                            "recent_commits": 0,
                            "score": count * SCORING_WEIGHTS["total_commits"],
                        }

            # 存储到智能缓存
            self.smart_cache.put("file_contributors", filepath, contributors)
            return contributors
        except Exception as e:
            print(f"深度分析文件 {filepath} 时出错: {e}")
            return {}

    def _fixed_batch_analyze_files(self, file_list):
        """批量文件分析方法"""
        print(f"📊 开始批量分析 {len(file_list)} 个文件")

        batch_results = {}
        one_year_ago = (
            datetime.now() - timedelta(days=DEFAULT_ANALYSIS_MONTHS * 30)
        ).strftime("%Y-%m-%d")

        # 分批处理，避免命令行过长
        batch_size = 500  # 增大批量大小以提高性能，同时保持准确性

        for i in range(0, len(file_list), batch_size):
            batch_files = file_list[i : i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(file_list) + batch_size - 1) // batch_size

            print(f"  📦 处理批次 {batch_num}/{total_batches} ({len(batch_files)} 文件)")

            # 获取近期贡献者（简化格式）
            recent_contributors = self._get_batch_contributors(
                batch_files, one_year_ago
            )

            # 获取历史贡献者（简化格式）
            total_contributors = self._get_batch_contributors(batch_files, None)

            # 合并结果并计算每个文件的贡献者统计
            for file_path in batch_files:
                contributors = {}

                # 处理近期贡献
                recent_authors = recent_contributors.get(file_path, {})
                for author, count in recent_authors.items():
                    contributors[author] = {
                        "total_commits": count,
                        "recent_commits": count,
                        "score": count * SCORING_WEIGHTS["recent_commits"],
                    }

                # 处理历史贡献
                total_authors = total_contributors.get(file_path, {})
                for author, count in total_authors.items():
                    if author in contributors:
                        contributors[author]["total_commits"] = count
                        contributors[author]["score"] = (
                            contributors[author]["recent_commits"]
                            * SCORING_WEIGHTS["recent_commits"]
                            + count * SCORING_WEIGHTS["total_commits"]
                        )
                    else:
                        contributors[author] = {
                            "total_commits": count,
                            "recent_commits": 0,
                            "score": count * SCORING_WEIGHTS["total_commits"],
                        }

                batch_results[file_path] = contributors

        return batch_results

    def _get_batch_contributors(self, file_list, since_date=None):
        """获取批量文件的贡献者信息 - 增强的错误处理和重试机制"""
        max_retries = 2

        for attempt in range(max_retries + 1):
            try:
                # 尝试使用git_operations中的批量方法
                batch_results = self.git_ops.get_contributors_batch(
                    file_list, since_date
                )

                # 验证结果质量
                if self._validate_batch_results(batch_results, file_list):
                    if attempt > 0:
                        print(f"   ✅ 重试成功 (第{attempt + 1}次尝试)")
                    return batch_results
                else:
                    if attempt < max_retries:
                        print(f"   ⚠️ 批量结果质量不佳，准备重试 (第{attempt + 1}次)")
                        continue
                    else:
                        print(f"   ⚠️ 多次重试后结果仍不理想，使用fallback方法")

            except Exception as e:
                if attempt < max_retries:
                    print(f"   ⚠️ 批量处理失败 (第{attempt + 1}次): {str(e)[:100]}...")
                    print(f"   🔄 正在重试...")
                    continue
                else:
                    print(f"   ❌ 批量处理多次失败，回退到传统方法: {str(e)[:100]}...")

        # 所有尝试都失败了，使用fallback方法
        return self._get_batch_contributors_fallback(file_list, since_date)

    def _validate_batch_results(self, batch_results, file_list):
        """验证批量分析结果的质量"""
        if not batch_results:
            return False

        # 检查结果覆盖率
        covered_files = len(
            [f for f in file_list if f in batch_results and batch_results[f]]
        )
        coverage_rate = covered_files / len(file_list) if file_list else 0

        # 至少应该覆盖30%的文件（考虑到有些文件可能没有提交历史）
        return coverage_rate >= 0.3

    def _get_batch_contributors_fallback(self, file_list, since_date=None):
        """批量贡献者获取的回退方法 - 增强版"""
        print(f"   📦 使用fallback方法分析 {len(file_list)} 个文件")
        contributors_by_file = defaultdict(lambda: defaultdict(int))

        # 如果文件太多，分批处理
        batch_size = 200  # 减小批量大小，避免命令行过长
        for i in range(0, len(file_list), batch_size):
            batch_files = file_list[i : i + batch_size]
            batch_contributors = self._process_file_batch_fallback(
                batch_files, since_date
            )

            # 合并结果
            for file_path, contributors in batch_contributors.items():
                for author, count in contributors.items():
                    contributors_by_file[file_path][author] += count

        return dict(contributors_by_file)

    def _process_file_batch_fallback(self, file_list, since_date=None):
        """处理单个批次的文件"""
        contributors_by_file = defaultdict(lambda: defaultdict(int))

        try:
            # 构建文件参数，使用更安全的方式
            files_arg = " ".join([f'"{f}"' for f in file_list])

            # 构建Git命令
            if since_date:
                cmd = f'git log --since="{since_date}" --format="COMMIT:%an" --name-only -- {files_arg}'
            else:
                cmd = f'git log --format="COMMIT:%an" --name-only -- {files_arg}'

            result = self.git_ops.run_command(cmd)
            if not result:
                return dict(contributors_by_file)

            # 解析输出
            lines = result.strip().split("\n")
            current_author = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line.startswith("COMMIT:"):
                    # 提取作者名
                    current_author = line[7:].strip()  # 去掉 'COMMIT:' 前缀并清理
                elif current_author and line in file_list:
                    # 这是一个文件名行，且是我们关注的文件
                    contributors_by_file[line][current_author] += 1

        except Exception as e:
            print(f"   ⚠️ 批次处理出错: {str(e)[:50]}...")
            # 如果批量也失败了，尝试单个文件分析
            for file_path in file_list:
                try:
                    single_result = self._analyze_single_file_simple(
                        file_path, since_date
                    )
                    if single_result:
                        contributors_by_file[file_path] = single_result
                except:
                    # 单个文件也失败了，跳过
                    continue

        return dict(contributors_by_file)

    def _analyze_single_file_simple(self, file_path, since_date=None):
        """简单的单文件分析，不使用--follow"""
        try:
            if since_date:
                cmd = f'git log --since="{since_date}" --format="%an" -- "{file_path}"'
            else:
                cmd = f'git log --format="%an" -- "{file_path}"'

            result = self.git_ops.run_command(cmd)
            if not result:
                return {}

            contributors = defaultdict(int)
            for author in result.split("\n"):
                author = author.strip()
                if author:
                    contributors[author] += 1

            return dict(contributors)
        except:
            return {}

    def _get_file_cache_key(self, file_path):
        """生成文件缓存键 - 性能优化版本，避免额外Git调用"""
        # 简化缓存键生成，避免每个文件都执行Git命令
        # 使用文件路径 + 当前日期作为缓存键，依靠时间过期机制保证数据新鲜度
        from datetime import datetime

        date_key = datetime.now().strftime("%Y-%m-%d")
        return f"{file_path}@{date_key}"

    @performance_monitor("并行分析组")
    def parallel_analyze_groups(self, groups):
        """并行分析多个组的贡献者信息"""
        print(f"🔄 开始并行分析 {len(groups)} 个组...")
        start_time = datetime.now()

        # 首先确保批量数据已准备好
        all_files = []
        for group in groups:
            all_files.extend(group.get("files", []))

        # 批量获取所有文件的贡献者信息
        self.batch_analyze_all_files(all_files)

        # 并行处理每个组
        results = {}
        # 动态确定线程数：基于CPU核心数和任务数
        import multiprocessing

        max_workers = min(
            multiprocessing.cpu_count() * 2,  # I/O密集任务可以使用更多线程
            len(groups),
            12,  # 避免创建过多线程
        )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_group = {
                executor.submit(self._analyze_single_group, group): group
                for group in groups
            }

            for future in as_completed(future_to_group):
                group = future_to_group[future]
                try:
                    group_name = group["name"]
                    main_contributor, all_contributors = future.result()
                    results[group_name] = {
                        "main_contributor": main_contributor,
                        "all_contributors": all_contributors,
                    }
                except Exception as e:
                    print(f"⚠️ 分析组 {group.get('name', 'Unknown')} 时出错: {e}")
                    results[group.get("name", "Unknown")] = {
                        "main_contributor": None,
                        "all_contributors": {},
                    }

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"⚡ 并行分析完成，用时 {elapsed:.2f} 秒")
        return results

    def _analyze_single_group(self, group):
        """分析单个组的主要贡献者（使用缓存数据）"""
        files = group.get("files", [])
        all_contributors = {}

        for file in files:
            # 从批量数据中获取贡献者信息
            contributors = self._batch_file_data.get(file, {})

            for author, stats in contributors.items():
                if author not in all_contributors:
                    all_contributors[author] = {
                        "total_commits": 0,
                        "recent_commits": 0,
                        "score": 0,
                        "file_count": 0,
                    }

                all_contributors[author]["total_commits"] += stats["total_commits"]
                all_contributors[author]["recent_commits"] += stats["recent_commits"]
                all_contributors[author]["score"] += stats["score"]
                all_contributors[author]["file_count"] += 1

        if not all_contributors:
            return None, {}

        # 返回综合得分最高的作者
        main_contributor = max(all_contributors.items(), key=lambda x: x[1]["score"])
        return main_contributor[0], all_contributors

    @performance_monitor("批量分析目录")
    def batch_analyze_directories(self, directory_paths):
        """批量分析目录贡献者信息"""
        print(f"📁 开始批量分析 {len(directory_paths)} 个目录...")

        results = {}
        uncached_dirs = []

        # 检查缓存
        for dir_path in directory_paths:
            if dir_path in self._directory_contributors_cache:
                results[dir_path] = self._directory_contributors_cache[dir_path]
            else:
                uncached_dirs.append(dir_path)

        if not uncached_dirs:
            return results

        # 批量分析未缓存的目录
        one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

        # 动态线程池配置
        import multiprocessing

        max_workers = min(
            multiprocessing.cpu_count() * 2, len(uncached_dirs), 8  # 目录分析的合理上限
        )

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_dir = {
                executor.submit(
                    self._analyze_single_directory, dir_path, one_year_ago
                ): dir_path
                for dir_path in uncached_dirs
            }

            for future in as_completed(future_to_dir):
                dir_path = future_to_dir[future]
                try:
                    contributors = future.result()
                    results[dir_path] = contributors
                    self._directory_contributors_cache[dir_path] = contributors
                except Exception as e:
                    print(f"⚠️ 分析目录 {dir_path} 时出错: {e}")
                    results[dir_path] = {}

        return results

    def _analyze_single_directory(self, directory_path, one_year_ago):
        """分析单个目录的贡献者"""
        contributors = {}

        # 获取一年内的贡献统计（目录分析通常不需要跟踪重命名）
        recent_cmd = (
            f'git log --since="{one_year_ago}" --format="%an" -- "{directory_path}"'
        )
        recent_result = self.git_ops.run_command(recent_cmd)

        if recent_result:
            recent_authors = recent_result.split("\n")
            recent_author_counts = {}
            for author in recent_authors:
                if author.strip():
                    recent_author_counts[author] = (
                        recent_author_counts.get(author, 0) + 1
                    )

            for author, count in recent_author_counts.items():
                contributors[author] = {
                    "total_commits": count,
                    "recent_commits": count,
                    "score": count * 3,
                }

        # 获取总体贡献统计（目录分析通常不需要跟踪重命名）
        cmd = f'git log --format="%an" -- "{directory_path}"'
        total_result = self.git_ops.run_command(cmd)

        if total_result:
            authors = total_result.split("\n")
            author_counts = {}
            for author in authors:
                if author.strip():
                    author_counts[author] = author_counts.get(author, 0) + 1

            for author, count in author_counts.items():
                if author in contributors:
                    contributors[author]["total_commits"] = count
                    contributors[author]["score"] = (
                        contributors[author]["recent_commits"] * 3 + count
                    )
                else:
                    contributors[author] = {
                        "total_commits": count,
                        "recent_commits": 0,
                        "score": count,
                    }

        return contributors

    def get_active_contributors(self, months=DEFAULT_ACTIVE_MONTHS):
        """获取活跃贡献者（优化版）"""
        if self._active_contributors_cache is not None:
            return self._active_contributors_cache

        print(f"🔍 正在分析近{months}个月的活跃贡献者...")
        active_contributors = self.git_ops.get_active_contributors(months)

        self._active_contributors_cache = active_contributors
        print(f"📊 发现 {len(active_contributors)} 位近{months}个月活跃的贡献者")
        return active_contributors

    @performance_monitor("优化备选分配查找")
    def optimized_find_fallback_assignee(self, file_paths, active_contributors):
        """优化的备选分配查找"""
        print(f"🔍 正在为未分配组寻找备选负责人...")

        # 收集需要分析的目录
        directories_to_check = set()
        for file_path in file_paths:
            path_parts = file_path.split("/")
            for i in range(len(path_parts) - 1, 0, -1):
                parent_dir = "/".join(path_parts[:i])
                if parent_dir:
                    directories_to_check.add(parent_dir)

        # 按目录层级排序
        sorted_dirs = sorted(
            directories_to_check, key=lambda x: x.count("/"), reverse=True
        )

        # 批量分析目录
        dir_contributors = self.batch_analyze_directories(sorted_dirs)

        # 查找最佳候选人
        for directory in sorted_dirs:
            print(f"  检查目录: {directory}")
            contributors = dir_contributors.get(directory, {})

            if contributors:
                active_dir_contributors = {
                    author: stats
                    for author, stats in contributors.items()
                    if author in active_contributors
                }

                if active_dir_contributors:
                    best_contributor = max(
                        active_dir_contributors.items(), key=lambda x: x[1]["score"]
                    )
                    print(
                        f"  ✅ 在目录 {directory} 找到候选人: {best_contributor[0]} (得分: {best_contributor[1]['score']})"
                    )
                    return best_contributor[0], best_contributor[1], directory

        # 检查根目录
        print("  检查根目录...")
        root_contributors = dir_contributors.get(".", {})
        if root_contributors:
            active_root_contributors = {
                author: stats
                for author, stats in root_contributors.items()
                if author in active_contributors
            }

            if active_root_contributors:
                best_contributor = max(
                    active_root_contributors.items(), key=lambda x: x[1]["score"]
                )
                print(
                    f"  ✅ 在根目录找到候选人: {best_contributor[0]} (得分: {best_contributor[1]['score']})"
                )
                return best_contributor[0], best_contributor[1], "根目录"

        print("  ❌ 未找到合适的候选人")
        return None, None, None

    # 保持与原接口的兼容性
    def analyze_file_contributors(self, filepath, include_recent=True):
        """文件贡献者分析（兼容接口）"""
        if not self._batch_computed:
            # 如果没有批量计算，单独分析这个文件
            self.batch_analyze_all_files([filepath])

        return self._batch_file_data.get(filepath, {})

    def get_group_main_contributor(self, files):
        """获取组主要贡献者（兼容接口）"""
        if not self._batch_computed:
            self.batch_analyze_all_files(files)

        group = {"files": files}
        return self._analyze_single_group(group)

    def find_fallback_assignee(self, file_paths, active_contributors):
        """备选分配（兼容接口）"""
        return self.optimized_find_fallback_assignee(file_paths, active_contributors)

    def get_all_contributors(self):
        """获取所有历史贡献者"""
        if self._all_contributors_cache is not None:
            return self._all_contributors_cache

        all_contributors = self.git_ops.get_all_contributors_global()
        self._all_contributors_cache = all_contributors
        return all_contributors

    def get_performance_stats(self):
        """获取性能统计信息"""
        return {
            "cached_files": len(self._file_contributors_cache),
            "cached_directories": len(self._directory_contributors_cache),
            "batch_computed": self._batch_computed,
            "cache_file_exists": self.cache_file.exists(),
        }

    # 计算全局贡献者统计（保持兼容性）
    def calculate_global_contributor_stats(self, plan):
        """计算全局贡献者统计"""
        all_contributors_global = {}

        for group in plan["groups"]:
            contributors = group.get("contributors", {})
            for author, stats in contributors.items():
                if author not in all_contributors_global:
                    all_contributors_global[author] = {
                        "total_commits": 0,
                        "recent_commits": 0,
                        "score": 0,
                        "groups_contributed": 0,
                        "groups_assigned": [],
                        "is_active": author in self.get_active_contributors(),
                    }

                if isinstance(stats, dict):
                    all_contributors_global[author]["recent_commits"] += stats[
                        "recent_commits"
                    ]
                    all_contributors_global[author]["total_commits"] += stats[
                        "total_commits"
                    ]
                    all_contributors_global[author]["score"] += stats["score"]
                else:
                    all_contributors_global[author]["total_commits"] += stats
                    all_contributors_global[author]["score"] += stats

                all_contributors_global[author]["groups_contributed"] += 1

                # 检查是否被分配到这个组
                if group.get("assignee") == author:
                    all_contributors_global[author]["groups_assigned"].append(
                        group["name"]
                    )

        return all_contributors_global

    def get_workload_distribution(self, plan):
        """获取负载分布统计"""
        if not plan or "groups" not in plan:
            return {}

        assignee_workload = {}
        for group in plan["groups"]:
            assignee = group.get("assignee")
            if assignee and assignee != "未分配":
                if assignee not in assignee_workload:
                    assignee_workload[assignee] = {
                        "groups": 0,
                        "files": 0,
                        "completed": 0,
                        "fallback": 0,
                    }
                assignee_workload[assignee]["groups"] += 1
                assignee_workload[assignee]["files"] += group.get(
                    "file_count", len(group.get("files", []))
                )
                if group.get("status") == "completed":
                    assignee_workload[assignee]["completed"] += 1
                if group.get("fallback_reason"):
                    assignee_workload[assignee]["fallback"] += 1

        return assignee_workload

    def get_assignment_reason_stats(self, plan):
        """获取分配原因统计"""
        from ui.display_helper import DisplayHelper

        reason_stats = {}
        for group in plan["groups"]:
            assignment_reason = group.get("assignment_reason", "未指定")
            reason_type = DisplayHelper.categorize_assignment_reason(assignment_reason)

            if reason_type not in reason_stats:
                reason_stats[reason_type] = []
            reason_stats[reason_type].append(group)

        return reason_stats

    def _generate_performance_report(self, analysis_stats):
        """生成性能分析报告"""
        if not analysis_stats:
            return "⚠️ 无性能数据可用"

        total_time = analysis_stats.get("total_time", 0)
        batch_time = analysis_stats.get("batch_time", 0)
        single_time = analysis_stats.get("single_time", 0)
        total_files = analysis_stats.get("total_files", 0)
        batch_files = analysis_stats.get("batch_files", 0)
        single_files = analysis_stats.get("single_files", 0)
        critical_ratio = analysis_stats.get("critical_ratio", 0)
        follow_usage = analysis_stats.get("follow_usage", 0)

        # 计算性能指标
        avg_time_per_file = total_time / max(total_files, 1)
        batch_efficiency = batch_time / max(batch_files, 1) if batch_files > 0 else 0
        single_efficiency = (
            single_time / max(single_files, 1) if single_files > 0 else 0
        )

        # 性能等级评估
        if avg_time_per_file < 0.1:
            perf_level = "🚀 优秀"
        elif avg_time_per_file < 0.5:
            perf_level = "✅ 良好"
        elif avg_time_per_file < 1.0:
            perf_level = "⚠️ 一般"
        else:
            perf_level = "❌ 需优化"

        report = [
            f"⚡ 性能分析报告:",
            f"   • 总耗时: {total_time:.2f}秒",
            f"   • 平均每文件: {avg_time_per_file:.3f}秒",
            f"   • 性能等级: {perf_level}",
            f"   • 关键文件比例: {critical_ratio:.1f}%",
            f"   • --follow使用率: {follow_usage:.1f}%",
            "",
            f"📈 处理分析:",
            f"   • 批量处理: {batch_files}个文件 ({batch_time:.2f}秒)",
            f"   • 单独处理: {single_files}个文件 ({single_time:.2f}秒)",
        ]

        if batch_files > 0:
            report.append(f"   • 批量效率: {batch_efficiency:.3f}秒/文件")
        if single_files > 0:
            report.append(f"   • 单独效率: {single_efficiency:.3f}秒/文件")

        # 优化建议
        suggestions = []
        if critical_ratio > 15:
            suggestions.append("建议：减少关键文件分类以提升批量处理效率")
        if follow_usage > 20:
            suggestions.append("建议：优化文件分类策略以减少--follow使用")
        if avg_time_per_file > 0.5:
            suggestions.append("建议：检查Git仓库大小和网络连接")

        if suggestions:
            report.append("")
            report.append("💡 优化建议:")
            for suggestion in suggestions:
                report.append(f"   • {suggestion}")

        return "\n".join(report)
    
    def _save_performance_log(self, file_list, total_time, step_times):
        """保存性能日志到文件"""
        try:
            # 设置日志文件路径
            if hasattr(self.git_ops, 'repo_path'):
                repo_path = Path(self.git_ops.repo_path)
            else:
                repo_path = Path(".")
                
            log_file = repo_path / ".merge_work" / "performance_log.json"
            log_file.parent.mkdir(exist_ok=True)
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'file_count': len(file_list),
                'total_time': total_time,
                'avg_time_per_file': total_time / len(file_list) * 1000,  # ms
                'step_times': step_times,
                'mode': step_times.get('mode', 'optimized_traditional')
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
