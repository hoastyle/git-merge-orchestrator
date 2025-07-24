"""
Git Merge Orchestrator - 加速优化的贡献者分析器
通过批量Git命令、智能缓存和并行处理大幅提升分析速度
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


class OptimizedContributorAnalyzer:
    """优化的贡献者分析器 - 大幅提升性能"""

    def __init__(self, git_ops):
        self.git_ops = git_ops
        self.cache_file = (
            Path(git_ops.repo_path) / ".merge_work" / "contributor_cache.json"
        )
        self.cache_lock = threading.Lock()

        # 内存缓存
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

    @performance_monitor("批量分析所有文件")
    def batch_analyze_all_files(self, file_list):
        """批量分析所有文件的贡献者信息 - 核心加速函数"""
        if self._batch_computed:
            return self._batch_file_data

        print(f"🚀 开始批量分析 {len(file_list)} 个文件的贡献者信息...")
        start_time = datetime.now()

        # 检查是否有缓存
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

        # 批量获取一年内的贡献统计 - 修复版
        one_year_ago = (
            datetime.now() - timedelta(days=DEFAULT_ANALYSIS_MONTHS * 30)
        ).strftime("%Y-%m-%d")

        # 分批处理文件，避免命令行过长
        batch_size = 50  # 每批处理50个文件
        recent_contributors = {}
        total_contributors = {}

        for i in range(0, len(uncached_files), batch_size):
            batch_files = uncached_files[i : i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(uncached_files) + batch_size - 1) // batch_size

            print(f"  📦 处理批次 {batch_num}/{total_batches} ({len(batch_files)} 文件)")

            # 构建文件参数，去掉 --follow 选项
            files_arg = " ".join([f'"{f}"' for f in batch_files])

            # 一次性获取这批文件的近期贡献者（去掉--follow）
            recent_cmd = f'git log --since="{one_year_ago}" --format="%an|%H|%s" --name-only -- {files_arg}'
            recent_result = self.git_ops.run_command(recent_cmd)

            # 一次性获取这批文件的历史贡献者（去掉--follow）
            total_cmd = f'git log --format="%an|%H|%s" --name-only -- {files_arg}'
            total_result = self.git_ops.run_command(total_cmd)

            # 解析批量结果并合并
            batch_recent = self._parse_batch_git_output(recent_result, batch_files)
            batch_total = self._parse_batch_git_output(total_result, batch_files)

            recent_contributors.update(batch_recent)
            total_contributors.update(batch_total)

        # 计算每个文件的贡献者统计
        for file_path in uncached_files:
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

            # 缓存结果
            cache_key = self._get_file_cache_key(file_path)
            self._file_contributors_cache[cache_key] = contributors
            self._batch_file_data[file_path] = contributors

        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"⚡ 批量分析完成，用时 {elapsed:.2f} 秒")
        print(f"📊 处理文件: {len(file_list)} 个，缓存命中: {len(cached_files)} 个")

        # 保存缓存
        self.save_persistent_cache()
        self._batch_computed = True
        return self._batch_file_data

    # 如果需要文件重命名跟踪功能，添加单独的方法
    def analyze_file_with_follow(self, filepath):
        """单文件分析（支持重命名跟踪）- 用于重要文件"""
        print(f"🔍 深度分析文件: {filepath} (支持重命名跟踪)")

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

            return contributors
        except Exception as e:
            print(f"深度分析文件 {filepath} 时出错: {e}")
            return {}

    def _parse_batch_git_output(self, git_output, target_files):
        """解析批量Git输出，提取每个文件的贡献者统计"""
        if not git_output:
            return {}

        contributors_by_file = defaultdict(lambda: defaultdict(int))
        current_author = None
        current_files = []

        lines = git_output.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 解析提交信息行 (格式: author|hash|subject)
            if "|" in line:
                parts = line.split("|", 2)
                if len(parts) >= 1:
                    current_author = parts[0]
                    current_files = []
            else:
                # 这是文件名行
                if current_author and line in target_files:
                    contributors_by_file[line][current_author] += 1

        return dict(contributors_by_file)

    def _get_file_cache_key(self, file_path):
        """生成文件缓存键（基于文件路径和最后修改时间）"""
        try:
            # 获取文件的最后提交hash作为缓存键的一部分
            cmd = f'git log -1 --format="%H" -- "{file_path}"'
            last_commit = self.git_ops.run_command(cmd)
            if last_commit:
                return f"{file_path}:{last_commit}"
        except:
            pass

        # 回退方案：使用文件路径
        return file_path

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
        self.smart_batch_analyze_files(all_files)

        # 并行处理每个组
        results = {}
        with ThreadPoolExecutor(max_workers=min(4, len(groups))) as executor:
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

        with ThreadPoolExecutor(max_workers=3) as executor:
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
            self.smart_batch_analyze_files([filepath])

        return self._batch_file_data.get(filepath, {})

    def get_group_main_contributor(self, files):
        """获取组主要贡献者（兼容接口）"""
        if not self._batch_computed:
            self.smart_batch_analyze_files(files)

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

    # 混合策略：重要文件使用follow，其他文件批量处理
    def smart_batch_analyze_files(self, file_list, important_files=None):
        """智能批量分析：重要文件深度分析，其他文件批量处理"""
        important_files = important_files or []

        # 分离重要文件和普通文件
        important_set = set(important_files)
        regular_files = [f for f in file_list if f not in important_set]
        existing_important_files = [f for f in file_list if f in important_set]

        print(f"🎯 智能分析策略:")
        print(f"   重要文件 (深度分析): {len(existing_important_files)} 个")
        print(f"   普通文件 (批量分析): {len(regular_files)} 个")

        # 批量处理普通文件
        if regular_files:
            self.batch_analyze_all_files(regular_files)

        # 深度分析重要文件
        for important_file in existing_important_files:
            if important_file not in self._batch_file_data:
                contributors = self.analyze_file_with_follow(important_file)
                self._batch_file_data[important_file] = contributors

                # 更新缓存
                cache_key = self._get_file_cache_key(important_file)
                self._file_contributors_cache[cache_key] = contributors

        return self._batch_file_data
