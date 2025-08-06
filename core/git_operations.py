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
                recent_cmd = f'git log --follow --since="{one_year_ago}" --format="%an" -- "{directory_path}"'
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
            cmd = f'git log --follow --format="%an" -- "{directory_path}"'
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
