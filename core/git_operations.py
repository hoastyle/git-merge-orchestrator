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

    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path)

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
        """获取两个分支间的变更文件"""
        cmd = f"git diff --name-only {source_branch} {target_branch}"
        result = self.run_command(cmd)

        if not result:
            return []

        files = result.split("\n")
        return [f for f in files if f.strip()]

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
            result = self.run_command(f"git checkout -b {integration_branch} {target_branch}")
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

    def get_contributors_with_line_stats(self, file_path, since_date=None):
        """获取文件贡献者的详细统计信息（包括修改行数）"""
        authors_stats = {}

        # 构建基础命令
        cmd_base = f'git log --follow --numstat --format="COMMIT:%an:%at"'
        if since_date:
            cmd_base += f' --since="{since_date}"'
        cmd_base += f' -- "{file_path}"'

        result = self.run_command(cmd_base)
        if not result:
            return {}

        lines = result.split("\n")
        current_author = None
        current_timestamp = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("COMMIT:"):
                # 解析提交信息：COMMIT:作者:时间戳
                parts = line.split(":", 2)
                if len(parts) >= 2:
                    current_author = parts[1]
                    current_timestamp = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0

                    if current_author not in authors_stats:
                        authors_stats[current_author] = {
                            "commits": 0,
                            "added_lines": 0,
                            "deleted_lines": 0,
                            "modified_lines": 0,
                            "last_commit": current_timestamp,
                        }
                    authors_stats[current_author]["commits"] += 1

                    # 更新最后提交时间
                    if current_timestamp > authors_stats[current_author]["last_commit"]:
                        authors_stats[current_author]["last_commit"] = current_timestamp
            else:
                # 解析文件变更统计：added_lines	deleted_lines	filename
                if current_author and "\t" in line:
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        try:
                            added = int(parts[0]) if parts[0].isdigit() else 0
                            deleted = int(parts[1]) if parts[1].isdigit() else 0

                            authors_stats[current_author]["added_lines"] += added
                            authors_stats[current_author]["deleted_lines"] += deleted
                            authors_stats[current_author]["modified_lines"] += added + deleted
                        except (ValueError, IndexError):
                            # 忽略解析错误的行
                            continue

        return authors_stats

    def get_file_contributors_enhanced(self, file_path, include_recent=True, recent_months=12):
        """获取文件贡献者的增强统计信息"""
        contributors = {}

        if include_recent:
            # 获取最近N个月的详细统计
            cutoff_date = (datetime.now() - timedelta(days=recent_months * 30)).strftime("%Y-%m-%d")
            recent_stats = self.get_contributors_with_line_stats(file_path, cutoff_date)

            for author, stats in recent_stats.items():
                contributors[author] = {
                    "recent_commits": stats["commits"],
                    "recent_added_lines": stats["added_lines"],
                    "recent_deleted_lines": stats["deleted_lines"],
                    "recent_modified_lines": stats["modified_lines"],
                    "total_commits": stats["commits"],
                    "total_added_lines": stats["added_lines"],
                    "total_deleted_lines": stats["deleted_lines"],
                    "total_modified_lines": stats["modified_lines"],
                    "last_commit": stats["last_commit"],
                }

        # 获取所有历史统计
        all_stats = self.get_contributors_with_line_stats(file_path)

        for author, stats in all_stats.items():
            if author not in contributors:
                contributors[author] = {
                    "recent_commits": 0,
                    "recent_added_lines": 0,
                    "recent_deleted_lines": 0,
                    "recent_modified_lines": 0,
                    "total_commits": stats["commits"],
                    "total_added_lines": stats["added_lines"],
                    "total_deleted_lines": stats["deleted_lines"],
                    "total_modified_lines": stats["modified_lines"],
                    "last_commit": stats["last_commit"],
                }
            else:
                # 更新总计数据
                contributors[author]["total_commits"] = stats["commits"]
                contributors[author]["total_added_lines"] = stats["added_lines"]
                contributors[author]["total_deleted_lines"] = stats["deleted_lines"]
                contributors[author]["total_modified_lines"] = stats["modified_lines"]
                if stats["last_commit"] > contributors[author]["last_commit"]:
                    contributors[author]["last_commit"] = stats["last_commit"]

        return contributors

    def get_active_contributors(self, months=3):
        """获取近N个月有提交的活跃贡献者列表"""
        cutoff_date = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
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
                one_year_ago = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
                recent_cmd = f'git log --follow --since="{one_year_ago}" --format="%an" -- "{directory_path}"'
                recent_result = self.run_command(recent_cmd)

                if recent_result:
                    recent_authors = recent_result.split("\n")
                    recent_author_counts = {}
                    for author in recent_authors:
                        if author.strip():
                            recent_author_counts[author] = recent_author_counts.get(author, 0) + 1

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
                        contributors[author]["score"] = contributors[author]["recent_commits"] * 3 + count
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
        branch_name = BATCH_BRANCH_TEMPLATE.format(assignee=assignee.replace(" ", "-"), timestamp=timestamp)

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
        result = self.run_command(f"git show-ref --verify --quiet refs/heads/{branch_name}")
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
        result = self.run_command_silent(f"git show-ref --verify --quiet refs/heads/{branch_name}")
        return result is not None
