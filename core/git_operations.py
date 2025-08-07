"""
Git Merge Orchestrator - Git操作管理
负责所有Git命令的执行和分支操作
"""

import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from config import (
    INTEGRATION_BRANCH_TEMPLATE,
    MERGE_BRANCH_TEMPLATE,
    BATCH_BRANCH_TEMPLATE,
)


class GitOperations:
    """Git操作管理类"""

    def __init__(self, repo_path=".", ignore_manager=None):
        self.repo_path = Path(repo_path)
        self.ignore_manager = ignore_manager

    def run_command(self, cmd):
        """执行git命令并返回结果"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Git命令执行失败: {cmd}")
            print(f"错误: {e.stderr}")
            return None

    def get_changed_files(self, source_branch, target_branch):
        """获取两个分支间的变更文件 - 支持忽略规则过滤"""
        cmd = f"git diff --name-only {source_branch} {target_branch}"
        result = self.run_command(cmd)

        if not result:
            return []

        files = result.split("\n")
        files = [f for f in files if f.strip()]

        # 应用忽略规则过滤
        if self.ignore_manager:
            original_count = len(files)
            files = self.ignore_manager.filter_files(files)
            filtered_count = original_count - len(files)

            if filtered_count > 0:
                print(f"📋 忽略规则过滤了 {filtered_count} 个文件，剩余 {len(files)} 个文件")

        return files

    def get_merge_base(self, source_branch, target_branch):
        """获取两个分支的分叉点"""
        cmd = f"git merge-base {source_branch} {target_branch}"
        return self.run_command(cmd)

    def get_diff_stats(self, source_branch, target_branch):
        """获取分支差异统计"""
        cmd = f"git diff --stat {source_branch} {target_branch}"
        return self.run_command(cmd)

    def create_integration_branch(self, source_branch, target_branch):
        """创建或切换到集成分支"""
        integration_branch = INTEGRATION_BRANCH_TEMPLATE.format(
            source=source_branch.replace("/", "-"),
            target=target_branch.replace("/", "-"),
        )

        print(f"🔄 准备集成分支: {integration_branch}")

        # 使用静默检查方法
        if not self.branch_exists(integration_branch):
            # 分支不存在，创建新分支
            print(f"📝 分支不存在，正在创建...")
            result = self.run_command(
                f"git checkout -b {integration_branch} {target_branch}"
            )
            if result is not None:
                print(f"✅ 已创建集成分支: {integration_branch}")
            else:
                print(f"❌ 创建集成分支失败: {integration_branch}")
                return None
        else:
            # 分支已存在，切换到该分支
            print(f"📋 分支已存在，正在切换...")
            result = self.run_command(f"git checkout {integration_branch}")
            if result is not None:
                print(f"✅ 已切换到集成分支: {integration_branch}")
            else:
                print(f"❌ 切换到集成分支失败: {integration_branch}")
                return None

        return integration_branch

    def preview_merge(self, source_branch):
        """预览合并结果"""
        merge_result = self.run_command(
            f"git merge --no-commit --no-ff {source_branch} 2>&1 || echo 'merge conflicts detected'"
        )

        # 重置合并状态
        self.run_command("git merge --abort 2>/dev/null || true")

        return merge_result

    def get_contributors_since(self, file_path, since_date):
        """获取指定日期以来的文件贡献者"""
        cmd = f'git log --follow --since="{since_date}" --format="%an" -- "{file_path}"'
        result = self.run_command(cmd)

        if not result:
            return {}

        authors = result.split("\n")
        author_counts = {}
        for author in authors:
            if author.strip():
                author_counts[author] = author_counts.get(author, 0) + 1

        return author_counts

    def get_all_contributors(self, file_path):
        """获取文件的所有历史贡献者"""
        cmd = f'git log --follow --format="%an" -- "{file_path}"'
        result = self.run_command(cmd)

        if not result:
            return {}

        authors = result.split("\n")
        author_counts = {}
        for author in authors:
            if author.strip():
                author_counts[author] = author_counts.get(author, 0) + 1

        return author_counts

    def get_contributors_batch(self, file_paths, since_date=None):
        """批量获取多个文件的贡献者 - 性能优化版本"""
        if not file_paths:
            return {}

        # 限制单次批量处理的文件数量，避免命令行过长
        batch_size = min(len(file_paths), 1000)
        file_paths = file_paths[:batch_size]

        # 构建批量查询命令
        files_arg = " ".join([f'"{path}"' for path in file_paths])

        if since_date:
            cmd = f'git log --since="{since_date}" --format="COMMIT:%an" --name-only -- {files_arg}'
        else:
            cmd = f'git log --format="COMMIT:%an" --name-only -- {files_arg}'

        result = self.run_command(cmd)
        if not result:
            return {path: {} for path in file_paths}

        # 解析批量结果
        file_contributors = {path: {} for path in file_paths}
        current_author = None

        for line in result.split("\n"):
            line = line.strip()
            if not line:
                continue

            if line.startswith("COMMIT:"):
                current_author = line[7:].strip()  # 移除 'COMMIT:' 前缀
            elif current_author and line in file_paths:
                # 这是一个文件路径，记录当前作者对该文件的贡献
                if current_author not in file_contributors[line]:
                    file_contributors[line][current_author] = 0
                file_contributors[line][current_author] += 1

        return file_contributors

    def get_contributors_batch_optimized(
        self, file_paths, since_date=None, max_commits=None
    ):
        """高度优化的批量贡献者获取 - 支持采样和缓存"""
        if not file_paths:
            return {}

        # 对于大量文件，使用目录级分组来减少Git调用
        directory_groups = self._group_files_by_directory(file_paths)
        all_results = {}

        for directory, files_in_dir in directory_groups.items():
            if len(files_in_dir) > 50:
                # 大目录使用采样策略
                result = self._get_directory_contributors_with_sampling(
                    directory, files_in_dir, since_date, max_commits
                )
            else:
                # 小目录使用常规批量处理
                result = self.get_contributors_batch(files_in_dir, since_date)

            all_results.update(result)

        return all_results

    def _group_files_by_directory(self, file_paths):
        """按目录分组文件路径"""
        from collections import defaultdict
        import os

        directory_groups = defaultdict(list)
        for file_path in file_paths:
            directory = os.path.dirname(file_path) or "."
            directory_groups[directory].append(file_path)

        return dict(directory_groups)

    def _get_directory_contributors_with_sampling(
        self, directory, file_paths, since_date=None, max_commits=200
    ):
        """使用采样策略获取目录级贡献者 - 适用于大目录"""
        # 先获取目录级的提交历史（采样）
        if since_date:
            cmd = f'git log --since="{since_date}" -n {max_commits or 200} --format="COMMIT:%an" --name-only -- "{directory}"'
        else:
            cmd = f'git log -n {max_commits or 200} --format="COMMIT:%an" --name-only -- "{directory}"'

        result = self.run_command(cmd)
        if not result:
            return {path: {} for path in file_paths}

        # 解析结果并分配到具体文件
        file_contributors = {path: {} for path in file_paths}
        current_author = None

        for line in result.split("\n"):
            line = line.strip()
            if not line:
                continue

            if line.startswith("COMMIT:"):
                current_author = line[7:].strip()
            elif current_author and line in file_paths:
                if current_author not in file_contributors[line]:
                    file_contributors[line][current_author] = 0
                file_contributors[line][current_author] += 1

        return file_contributors

    def get_active_contributors(self, months=3):
        """获取近N个月有提交的活跃贡献者列表"""
        cutoff_date = (datetime.now() - timedelta(days=months * 30)).strftime(
            "%Y-%m-%d"
        )
        cmd = f'git log --since="{cutoff_date}" --format="%an" --all'
        result = self.run_command(cmd)

        active_contributors = set()
        if result:
            for author in result.split("\n"):
                if author.strip():
                    active_contributors.add(author.strip())

        return active_contributors

    def get_all_contributors_global(self):
        """获取所有历史贡献者"""
        cmd = 'git log --format="%an" --all'
        result = self.run_command(cmd)

        all_contributors = set()
        if result:
            for author in result.split("\n"):
                if author.strip():
                    all_contributors.add(author.strip())

        return all_contributors

    def get_directory_contributors(self, directory_path, include_recent=True):
        """分析目录级别的主要贡献者"""
        try:
            contributors = {}

            # 获取一年内的贡献统计
            if include_recent:
                one_year_ago = (datetime.now() - timedelta(days=365)).strftime(
                    "%Y-%m-%d"
                )
                recent_cmd = f'git log --since="{one_year_ago}" --format="%an" -- "{directory_path}"'
                recent_result = self.run_command(recent_cmd)

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
            cmd = f'git log --format="%an" -- "{directory_path}"'
            total_result = self.run_command(cmd)

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
        except Exception as e:
            print(f"分析目录 {directory_path} 时出错: {e}")
            return {}

    def create_merge_branch(self, group_name, assignee, integration_branch):
        """为指定任务创建合并分支"""
        branch_name = MERGE_BRANCH_TEMPLATE.format(
            group=group_name.replace("/", "-"), assignee=assignee.replace(" ", "-")
        )

        # 创建工作分支
        self.run_command(f"git checkout {integration_branch}")
        result = self.run_command(f"git checkout -b {branch_name}")

        if result is not None:
            print(f"✅ 已创建合并分支: {branch_name}")
        else:
            print(f"⚠️ 分支 {branch_name} 可能已存在，正在切换")
            self.run_command(f"git checkout {branch_name}")

        return branch_name

    def create_batch_merge_branch(self, assignee, integration_branch):
        """创建批量合并分支"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = BATCH_BRANCH_TEMPLATE.format(
            assignee=assignee.replace(" ", "-"), timestamp=timestamp
        )

        self.run_command(f"git checkout {integration_branch}")
        result = self.run_command(f"git checkout -b {branch_name}")

        if result is None:
            print(f"⚠️ 分支创建可能失败，尝试切换到现有分支")
            self.run_command(f"git checkout {branch_name}")

        return branch_name

    def get_remote_branches(self):
        """获取所有远程分支"""
        self.run_command("git fetch --all")

        remote_branches_output = self.run_command("git branch -r")
        if not remote_branches_output:
            return set()

        remote_branches = set()
        for line in remote_branches_output.split("\n"):
            branch = line.strip()
            if branch and not branch.startswith("origin/HEAD"):
                remote_branches.add(branch.replace("origin/", ""))

        return remote_branches

    def merge_branch_to_integration(self, branch_name, group_name, integration_branch):
        """将分支合并到集成分支"""
        self.run_command(f"git checkout {integration_branch}")

        merge_cmd = f"git merge --no-ff -m 'Merge branch {branch_name}: {group_name}' {branch_name}"
        result = self.run_command(merge_cmd)

        return result is not None

    def get_branch_exists(self, branch_name):
        """检查分支是否存在"""
        result = self.run_command(
            f"git show-ref --verify --quiet refs/heads/{branch_name}"
        )
        return result is not None

    def run_command_silent(self, cmd):
        """静默执行git命令，用于检查操作，不打印错误信息"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            # 静默处理错误，不打印信息
            return None

    def check_file_existence(self, files, branch):
        """检查文件在指定分支中是否存在（静默检查）"""
        existing_files = []
        missing_files = []

        print(f"🔍 正在检查 {len(files)} 个文件在分支 {branch} 中的存在性...")

        for file in files:
            # 使用静默命令检查，避免打印错误信息
            result = self.run_command_silent(f"git cat-file -e {branch}:{file}")
            if result is not None:
                existing_files.append(file)
            else:
                missing_files.append(file)

        print(f"📊 检查完成: {len(existing_files)} 个已存在, {len(missing_files)} 个新增")
        return existing_files, missing_files

    def branch_exists(self, branch_name):
        """检查分支是否存在（静默检查）"""
        result = self.run_command_silent(
            f"git show-ref --verify --quiet refs/heads/{branch_name}"
        )
        return result is not None

    # === 文件级分支操作方法 ===

    def create_file_merge_branch(self, file_path, assignee, integration_branch):
        """为单个文件创建合并分支"""
        # 使用文件路径创建安全的分支名
        safe_file_name = file_path.replace("/", "-").replace(" ", "_").replace(".", "_")
        safe_assignee = assignee.replace(" ", "-").replace(".", "_")

        branch_name = f"feat/merge-file-{safe_file_name}-{safe_assignee}"

        # 限制分支名长度，避免过长
        if len(branch_name) > 100:
            # 只保留文件名的后部分
            file_suffix = (
                safe_file_name[-30:] if len(safe_file_name) > 30 else safe_file_name
            )
            branch_name = f"feat/merge-file-{file_suffix}-{safe_assignee}"

            # 如果还是太长，使用时间戳
            if len(branch_name) > 100:
                timestamp = datetime.now().strftime("%m%d_%H%M")
                branch_name = f"feat/merge-file-{timestamp}-{safe_assignee[:20]}"

        # 创建工作分支
        self.run_command(f"git checkout {integration_branch}")
        result = self.run_command(f"git checkout -b {branch_name}")

        if result is not None:
            print(f"✅ 已创建文件合并分支: {branch_name}")
        else:
            print(f"⚠️ 分支 {branch_name} 可能已存在，正在切换")
            self.run_command(f"git checkout {branch_name}")

        return branch_name

    def create_file_batch_merge_branch(self, assignee, integration_branch):
        """创建文件批量合并分支"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_assignee = assignee.replace(" ", "-").replace(".", "_")
        branch_name = f"feat/merge-file-batch-{safe_assignee}-{timestamp}"

        # 限制分支名长度
        if len(branch_name) > 100:
            short_assignee = safe_assignee[:20]
            branch_name = f"feat/merge-file-batch-{short_assignee}-{timestamp}"

        self.run_command(f"git checkout {integration_branch}")
        result = self.run_command(f"git checkout -b {branch_name}")

        if result is None:
            print(f"⚠️ 分支创建可能失败，尝试切换到现有分支")
            self.run_command(f"git checkout {branch_name}")
        else:
            print(f"✅ 已创建文件批量合并分支: {branch_name}")

        return branch_name

    def get_file_contributors_analysis(self, file_path, months=12):
        """分析单个文件的贡献者信息"""
        try:
            contributors = {}

            # 获取最近N个月的贡献统计
            cutoff_date = (datetime.now() - timedelta(days=months * 30)).strftime(
                "%Y-%m-%d"
            )
            recent_cmd = f'git log --follow --since="{cutoff_date}" --format="%an" -- "{file_path}"'
            recent_result = self.run_command(recent_cmd)

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
                        "score": count * 3,  # 近期提交权重更高
                    }

            # 获取总体贡献统计
            total_cmd = f'git log --follow --format="%an" -- "{file_path}"'
            total_result = self.run_command(total_cmd)

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
        except Exception as e:
            print(f"分析文件 {file_path} 时出错: {e}")
            return {}

    # === 增强的Git日志解析功能（v2.3新增）===

    def get_enhanced_file_contributors(
        self, file_path, months=12, enable_line_analysis=True
    ):
        """
        增强的文件贡献者分析（支持行数权重）
        
        Args:
            file_path: 文件路径
            months: 分析时间范围（月）
            enable_line_analysis: 是否启用行数变更分析
        
        Returns:
            dict: 增强的贡献者信息 {作者: {基础信息 + 行数信息}}
        """
        try:
            from config import ENHANCED_CONTRIBUTOR_ANALYSIS

            if not ENHANCED_CONTRIBUTOR_ANALYSIS.get("enabled", True):
                # 回退到简单分析
                return self.get_file_contributors_analysis(file_path, months)

            contributors = {}

            # 获取时间范围
            cutoff_date = (datetime.now() - timedelta(days=months * 30)).strftime(
                "%Y-%m-%d"
            )

            if enable_line_analysis and ENHANCED_CONTRIBUTOR_ANALYSIS.get(
                "line_weight_enabled", True
            ):
                # 使用 --numstat 获取行数变更信息
                enhanced_cmd = (
                    f'git log --follow --since="{cutoff_date}" '
                    f'--format="COMMIT:%H|%an|%at" --numstat -- "{file_path}"'
                )
                enhanced_result = self.run_command(enhanced_cmd)

                if enhanced_result:
                    contributors = self._parse_enhanced_git_log(
                        enhanced_result, file_path
                    )

            # 如果增强分析失败，回退到基础分析
            if not contributors:
                print(f"⚠️  增强分析失败，回退到基础分析: {file_path}")
                return self.get_file_contributors_analysis(file_path, months)

            # 应用权重算法
            contributors = self._apply_enhanced_scoring(contributors, file_path)

            return contributors

        except Exception as e:
            print(f"增强分析文件 {file_path} 时出错: {e}")
            # 回退到基础分析
            return self.get_file_contributors_analysis(file_path, months)

    def _parse_enhanced_git_log(self, git_output, file_path):
        """
        解析增强的git log输出（包含--numstat信息）
        
        Args:
            git_output: git log --numstat 的输出
            file_path: 目标文件路径
            
        Returns:
            dict: 解析后的贡献者信息
        """
        contributors = {}
        current_commit = None

        lines = git_output.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            # 解析提交信息行：COMMIT:hash|author|timestamp
            if line.startswith("COMMIT:"):
                try:
                    _, commit_info = line.split(":", 1)
                    commit_hash, author, timestamp_str = commit_info.split("|")
                    timestamp = int(timestamp_str)

                    current_commit = {
                        "hash": commit_hash,
                        "author": author,
                        "timestamp": timestamp,
                        "files": [],
                    }
                except ValueError as e:
                    print(f"解析提交信息失败: {line}, 错误: {e}")
                    current_commit = None

            # 解析文件变更统计：additions deletions filename
            elif current_commit and "\t" in line:
                try:
                    parts = line.split("\t")
                    if len(parts) >= 3:
                        additions_str, deletions_str, filename = (
                            parts[0],
                            parts[1],
                            parts[2],
                        )

                        # 只处理目标文件
                        if filename == file_path:
                            additions = (
                                0 if additions_str == "-" else int(additions_str)
                            )
                            deletions = (
                                0 if deletions_str == "-" else int(deletions_str)
                            )

                            current_commit["files"].append(
                                {
                                    "filename": filename,
                                    "additions": additions,
                                    "deletions": deletions,
                                    "total_changes": additions + deletions,
                                }
                            )

                            # 更新贡献者统计
                            author = current_commit["author"]
                            if author not in contributors:
                                contributors[author] = {
                                    "total_commits": 0,
                                    "recent_commits": 0,
                                    "total_additions": 0,
                                    "total_deletions": 0,
                                    "total_changes": 0,
                                    "commits_detail": [],
                                    "score": 0,
                                }

                            contributors[author]["total_commits"] += 1
                            contributors[author][
                                "recent_commits"
                            ] += 1  # 由于是since查询，都是recent
                            contributors[author]["total_additions"] += additions
                            contributors[author]["total_deletions"] += deletions
                            contributors[author]["total_changes"] += (
                                additions + deletions
                            )

                            contributors[author]["commits_detail"].append(
                                {
                                    "hash": current_commit["hash"],
                                    "timestamp": current_commit["timestamp"],
                                    "additions": additions,
                                    "deletions": deletions,
                                    "total_changes": additions + deletions,
                                }
                            )

                except (ValueError, IndexError) as e:
                    # 忽略解析失败的行
                    pass

            i += 1

        return contributors

    def _apply_enhanced_scoring(self, contributors, file_path):
        """
        应用增强的评分算法
        
        Args:
            contributors: 基础贡献者信息
            file_path: 文件路径
            
        Returns:
            dict: 应用增强评分后的贡献者信息
        """
        from config import ENHANCED_CONTRIBUTOR_ANALYSIS
        import math

        if not contributors:
            return contributors

        algorithm = ENHANCED_CONTRIBUTOR_ANALYSIS.get(
            "assignment_algorithm", "comprehensive"
        )

        for author, data in contributors.items():
            base_score = data.get("score", 0)

            # 基础提交分数
            commit_score = data["recent_commits"] * ENHANCED_CONTRIBUTOR_ANALYSIS.get(
                "base_commit_score", 1.0
            )

            # 行数权重分数
            line_weight_score = 0
            if ENHANCED_CONTRIBUTOR_ANALYSIS.get("line_weight_enabled", True):
                line_weight_score = self._calculate_line_weight_score(data)

            # 时间权重分数
            time_weight_score = 0
            if ENHANCED_CONTRIBUTOR_ANALYSIS.get("time_weight_enabled", True):
                time_weight_score = self._calculate_time_weight_score(data)

            # 一致性权重分数
            consistency_score = 0
            if (
                ENHANCED_CONTRIBUTOR_ANALYSIS.get("consistency_weight_enabled", True)
                and algorithm == "comprehensive"
            ):
                consistency_score = self._calculate_consistency_score(data)

            # 综合评分
            if algorithm == "simple":
                final_score = commit_score
            elif algorithm == "weighted":
                final_score = commit_score + line_weight_score + time_weight_score
            else:  # comprehensive
                final_score = (
                    commit_score
                    + line_weight_score
                    + time_weight_score
                    + consistency_score
                )

            # 更新分数
            data["enhanced_score"] = final_score
            data["score"] = final_score  # 保持兼容性

            # 保存详细评分信息
            data["score_breakdown"] = {
                "base_score": base_score,
                "commit_score": commit_score,
                "line_weight_score": line_weight_score,
                "time_weight_score": time_weight_score,
                "consistency_score": consistency_score,
                "final_score": final_score,
            }

        return contributors

    def _calculate_line_weight_score(self, contributor_data):
        """计算行数权重分数"""
        from config import ENHANCED_CONTRIBUTOR_ANALYSIS
        import math

        total_changes = contributor_data.get("total_changes", 0)
        if total_changes == 0:
            return 0

        line_weight_factor = ENHANCED_CONTRIBUTOR_ANALYSIS.get(
            "line_weight_factor", 0.3
        )
        algorithm = ENHANCED_CONTRIBUTOR_ANALYSIS.get(
            "line_weight_algorithm", "logarithmic"
        )

        if algorithm == "logarithmic":
            log_base = ENHANCED_CONTRIBUTOR_ANALYSIS.get("magnitude_scaling", {}).get(
                "log_base", 10
            )
            score = line_weight_factor * math.log(total_changes + 1, log_base)
        elif algorithm == "linear":
            linear_factor = ENHANCED_CONTRIBUTOR_ANALYSIS.get(
                "magnitude_scaling", {}
            ).get("linear_factor", 0.01)
            score = line_weight_factor * total_changes * linear_factor
        elif algorithm == "sigmoid":
            steepness = ENHANCED_CONTRIBUTOR_ANALYSIS.get("magnitude_scaling", {}).get(
                "sigmoid_steepness", 0.1
            )
            score = line_weight_factor * (
                2 / (1 + math.exp(-steepness * total_changes)) - 1
            )
        else:
            # 默认使用对数算法
            score = line_weight_factor * math.log(total_changes + 1, 10)

        # 应用最大权重限制
        max_multiplier = ENHANCED_CONTRIBUTOR_ANALYSIS.get(
            "max_line_weight_multiplier", 3.0
        )
        score = min(score, max_multiplier)

        return score

    def _calculate_time_weight_score(self, contributor_data):
        """计算时间权重分数"""
        from config import ENHANCED_CONTRIBUTOR_ANALYSIS
        import time
        import math

        commits_detail = contributor_data.get("commits_detail", [])
        if not commits_detail:
            return 0

        current_time = time.time()
        half_life_days = ENHANCED_CONTRIBUTOR_ANALYSIS.get("time_half_life_days", 180)
        time_weight_factor = ENHANCED_CONTRIBUTOR_ANALYSIS.get(
            "time_weight_factor", 0.4
        )

        total_time_weight = 0
        half_life_seconds = half_life_days * 24 * 3600

        for commit in commits_detail:
            commit_time = commit.get("timestamp", current_time)
            time_diff = current_time - commit_time

            # 时间衰减权重：使用指数衰减
            time_weight = math.exp(-time_diff / half_life_seconds)
            change_weight = commit.get("total_changes", 0)

            total_time_weight += time_weight * change_weight

        return time_weight_factor * total_time_weight / 1000  # 归一化

    def _calculate_consistency_score(self, contributor_data):
        """计算一致性权重分数"""
        from config import ENHANCED_CONTRIBUTOR_ANALYSIS
        import statistics

        commits_detail = contributor_data.get("commits_detail", [])
        min_commits = ENHANCED_CONTRIBUTOR_ANALYSIS.get(
            "min_commits_for_consistency", 3
        )

        if len(commits_detail) < min_commits:
            return 0

        # 计算提交时间间隔的一致性
        timestamps = sorted([c.get("timestamp", 0) for c in commits_detail])
        if len(timestamps) < 2:
            return 0

        intervals = []
        for i in range(1, len(timestamps)):
            interval = timestamps[i] - timestamps[i - 1]
            intervals.append(interval)

        if not intervals:
            return 0

        # 一致性评分：间隔越稳定，分数越高
        try:
            mean_interval = statistics.mean(intervals)
            if mean_interval == 0:
                return 0

            # 使用变异系数衡量一致性
            std_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0
            consistency_ratio = 1 - min(std_interval / mean_interval, 1)

            consistency_factor = ENHANCED_CONTRIBUTOR_ANALYSIS.get(
                "consistency_bonus_factor", 0.2
            )
            return consistency_factor * consistency_ratio * len(commits_detail)

        except (statistics.StatisticsError, ZeroDivisionError):
            return 0

    def get_enhanced_contributors_batch(
        self, file_paths, months=12, enable_line_analysis=True
    ):
        """
        批量获取增强的贡献者信息
        
        Args:
            file_paths: 文件路径列表
            months: 分析时间范围
            enable_line_analysis: 是否启用行数分析
            
        Returns:
            dict: {文件路径: 增强贡献者信息}
        """
        from config import ENHANCED_CONTRIBUTOR_ANALYSIS

        if not ENHANCED_CONTRIBUTOR_ANALYSIS.get("enabled", True):
            # 回退到基础批量分析
            return self.get_contributors_batch_optimized(
                file_paths,
                since_date=(datetime.now() - timedelta(days=months * 30)).strftime(
                    "%Y-%m-%d"
                ),
            )

        result = {}
        batch_size = min(
            len(file_paths), ENHANCED_CONTRIBUTOR_ANALYSIS.get("max_parallel_files", 50)
        )

        # 分批处理，避免命令行过长
        for i in range(0, len(file_paths), batch_size):
            batch_files = file_paths[i : i + batch_size]
            batch_result = self._process_enhanced_batch(
                batch_files, months, enable_line_analysis
            )
            result.update(batch_result)

        return result

    def _process_enhanced_batch(self, file_paths, months, enable_line_analysis):
        """处理一批文件的增强分析"""
        try:
            cutoff_date = (datetime.now() - timedelta(days=months * 30)).strftime(
                "%Y-%m-%d"
            )
            result = {}

            if enable_line_analysis:
                # 构建批量增强查询
                files_arg = " ".join([f'"{path}"' for path in file_paths])
                enhanced_cmd = (
                    f'git log --since="{cutoff_date}" '
                    f'--format="COMMIT:%H|%an|%at" --numstat -- {files_arg}'
                )

                enhanced_result = self.run_command(enhanced_cmd)
                if enhanced_result:
                    result = self._parse_enhanced_batch_log(enhanced_result, file_paths)

            # 对于未处理的文件，使用基础分析
            for file_path in file_paths:
                if file_path not in result:
                    result[file_path] = self.get_file_contributors_analysis(
                        file_path, months
                    )
                else:
                    # 应用增强评分
                    result[file_path] = self._apply_enhanced_scoring(
                        result[file_path], file_path
                    )

            return result

        except Exception as e:
            print(f"批量增强分析失败: {e}")
            # 回退到基础批量分析
            fallback_result = {}
            for file_path in file_paths:
                fallback_result[file_path] = self.get_file_contributors_analysis(
                    file_path, months
                )
            return fallback_result

    def _parse_enhanced_batch_log(self, git_output, file_paths):
        """解析批量增强git log输出"""
        contributors_by_file = {path: {} for path in file_paths}
        current_commit = None

        lines = git_output.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            if not line:
                i += 1
                continue

            # 解析提交信息
            if line.startswith("COMMIT:"):
                try:
                    _, commit_info = line.split(":", 1)
                    commit_hash, author, timestamp_str = commit_info.split("|")
                    timestamp = int(timestamp_str)

                    current_commit = {
                        "hash": commit_hash,
                        "author": author,
                        "timestamp": timestamp,
                    }
                except ValueError:
                    current_commit = None

            # 解析文件变更统计
            elif current_commit and "\t" in line:
                try:
                    parts = line.split("\t")
                    if len(parts) >= 3:
                        additions_str, deletions_str, filename = (
                            parts[0],
                            parts[1],
                            parts[2],
                        )

                        # 只处理目标文件
                        if filename in file_paths:
                            additions = (
                                0 if additions_str == "-" else int(additions_str)
                            )
                            deletions = (
                                0 if deletions_str == "-" else int(deletions_str)
                            )

                            author = current_commit["author"]

                            if author not in contributors_by_file[filename]:
                                contributors_by_file[filename][author] = {
                                    "total_commits": 0,
                                    "recent_commits": 0,
                                    "total_additions": 0,
                                    "total_deletions": 0,
                                    "total_changes": 0,
                                    "commits_detail": [],
                                    "score": 0,
                                }

                            contributor = contributors_by_file[filename][author]
                            contributor["total_commits"] += 1
                            contributor["recent_commits"] += 1
                            contributor["total_additions"] += additions
                            contributor["total_deletions"] += deletions
                            contributor["total_changes"] += additions + deletions

                            contributor["commits_detail"].append(
                                {
                                    "hash": current_commit["hash"],
                                    "timestamp": current_commit["timestamp"],
                                    "additions": additions,
                                    "deletions": deletions,
                                    "total_changes": additions + deletions,
                                }
                            )

                except (ValueError, IndexError):
                    pass

            i += 1

        return contributors_by_file
