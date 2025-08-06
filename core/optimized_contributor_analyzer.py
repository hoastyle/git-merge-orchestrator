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
from config import SCORING_WEIGHTS, DEFAULT_ANALYSIS_MONTHS, DEFAULT_ACTIVE_MONTHS
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
    def batch_analyze_all_files(self, file_list):
        """批量分析所有文件的贡献者信息"""
        if self._batch_computed:
            return self._batch_file_data

        print(f"🚀 开始批量分析 {len(file_list)} 个文件的贡献者信息...")
        print(f"⚡ 性能优化提示：正在应用智能文件分类策略...")
        start_time = datetime.now()

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

        print(f"📊 文件分类完成 ({classification_time:.3f}s):")
        print(
            f"   🎯 关键文件: {len(critical_files)} 个 ({critical_ratio:.1f}%) - 使用深度分析（--follow）"
        )
        print(f"   📋 普通文件: {len(regular_files)} 个 ({100-critical_ratio:.1f}%) - 使用批量分析")

        if critical_ratio > 20:  # 如果超过20%的文件使用深度分析，给出性能警告
            print(f"⚠️  性能警告：{critical_ratio:.1f}%的文件将使用深度分析，可能影响性能")
        else:
            print(f"✅ 性能优化：仅{critical_ratio:.1f}%的文件使用深度分析，性能良好")

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
            f"📊 处理: 总计{len(file_list)}, 缓存{len(cached_files)}, 深度分析{len(critical_files)}, 批量分析{len(regular_files)}"
        )

        # 保存缓存
        self.save_persistent_cache()
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
            core_patterns = [
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

            file_name = file_path.split("/")[-1]
            if file_name in core_patterns:
                is_critical = True

            # 2. 根目录的重要配置文件
            elif "/" not in file_path and file_path.endswith(
                (".py", ".js", ".ts", ".json", ".yml", ".yaml")
            ):
                is_critical = True

            # 3. 明确的框架入口文件
            elif any(
                pattern in file_path.lower()
                for pattern in ["main/", "/main.", "entry", "bootstrap"]
            ):
                is_critical = True

            # 4. 检查是否可能有重命名历史（基于文件大小和路径深度）
            elif self._should_check_rename_history(file_path):
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
        """获取批量文件的贡献者信息 - 使用优化的Git操作"""
        # 直接使用git_operations中的批量方法
        try:
            batch_results = self.git_ops.get_contributors_batch(file_list, since_date)
            return batch_results
        except Exception as e:
            print(f"⚠️ 批量处理失败，回退到传统方法: {str(e)}")
            return self._get_batch_contributors_fallback(file_list, since_date)

    def _get_batch_contributors_fallback(self, file_list, since_date=None):
        """批量贡献者获取的回退方法"""
        contributors_by_file = defaultdict(lambda: defaultdict(int))

        # 构建文件参数
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
                current_author = line[7:]  # 去掉 'COMMIT:' 前缀
            elif current_author and line in file_list:
                # 这是一个文件名行，且是我们关注的文件
                contributors_by_file[line][current_author] += 1

        return dict(contributors_by_file)

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

        # 获取一年内的贡献统计
        recent_cmd = f'git log --follow --since="{one_year_ago}" --format="%an" -- "{directory_path}"'
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

        # 获取总体贡献统计
        cmd = f'git log --follow --format="%an" -- "{directory_path}"'
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
