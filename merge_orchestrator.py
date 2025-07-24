import subprocess
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import re

class GitMergeTool:
    def __init__(self, source_branch, target_branch, repo_path=".", max_files_per_group=5):
        self.source_branch = source_branch
        self.target_branch = target_branch
        self.repo_path = Path(repo_path)
        self.max_files_per_group = max_files_per_group
        self.integration_branch = f"integration-{source_branch.replace('/', '-')}-{target_branch.replace('/', '-')}"
        self.work_dir = self.repo_path / ".merge_work"
        self.work_dir.mkdir(exist_ok=True)

        # 缓存活跃用户列表
        self._active_contributors_cache = None
        self._all_contributors_cache = None

    def _get_display_width(self, text):
        """计算显示宽度，考虑中文字符"""
        width = 0
        for char in str(text):
            if ord(char) > 127:  # 中文字符
                width += 2
            else:  # 英文字符
                width += 1
        return width

    def _format_table_cell(self, text, width, align='left'):
        """格式化表格单元格，确保对齐"""
        text_str = str(text)
        display_width = self._get_display_width(text_str)
        padding = width - display_width

        if padding <= 0:
            return text_str[:width]

        if align == 'left':
            return text_str + ' ' * padding
        elif align == 'right':
            return ' ' * padding + text_str
        elif align == 'center':
            left_pad = padding // 2
            right_pad = padding - left_pad
            return ' ' * left_pad + text_str + ' ' * right_pad

        return text_str

    def _print_table_separator(self, widths):
        """打印表格分隔线"""
        total_width = sum(widths) + len(widths) - 1
        print('-' * total_width)

    def _print_table_header(self, headers, widths, aligns=None):
        """打印表格标题行"""
        if aligns is None:
            aligns = ['left'] * len(headers)

        row = []
        for i, (header, width, align) in enumerate(zip(headers, widths, aligns)):
            row.append(self._format_table_cell(header, width, align))

        print(' '.join(row))
        self._print_table_separator(widths)

    def _print_table_row(self, values, widths, aligns=None):
        """打印表格数据行"""
        if aligns is None:
            aligns = ['left'] * len(values)

        row = []
        for i, (value, width, align) in enumerate(zip(values, widths, aligns)):
            row.append(self._format_table_cell(value, width, align))

        print(' '.join(row))

    def run_git_command(self, cmd):
        """执行git命令并返回结果"""
        try:
            result = subprocess.run(
                cmd, shell=True, cwd=self.repo_path,
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Git命令执行失败: {cmd}")
            print(f"错误: {e.stderr}")
            return None

    def get_active_contributors(self, months=3):
        """获取近N个月有提交的活跃贡献者列表"""
        if self._active_contributors_cache is not None:
            return self._active_contributors_cache

        print(f"🔍 正在分析近{months}个月的活跃贡献者...")
        cutoff_date = (datetime.now() - timedelta(days=months * 30)).strftime('%Y-%m-%d')

        cmd = f'git log --since="{cutoff_date}" --format="%an" --all'
        result = self.run_git_command(cmd)

        active_contributors = set()
        if result:
            for author in result.split('\n'):
                if author.strip():
                    active_contributors.add(author.strip())

        self._active_contributors_cache = active_contributors
        print(f"📊 发现 {len(active_contributors)} 位近{months}个月活跃的贡献者")
        return active_contributors

    def get_all_contributors(self):
        """获取所有历史贡献者"""
        if self._all_contributors_cache is not None:
            return self._all_contributors_cache

        cmd = 'git log --format="%an" --all'
        result = self.run_git_command(cmd)

        all_contributors = set()
        if result:
            for author in result.split('\n'):
                if author.strip():
                    all_contributors.add(author.strip())

        self._all_contributors_cache = all_contributors
        return all_contributors

    def analyze_directory_contributors(self, directory_path, include_recent=True):
        """分析目录级别的主要贡献者"""
        try:
            contributors = {}

            # 获取目录下所有文件的贡献者信息
            if include_recent:
                one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
                recent_cmd = f'git log --follow --since="{one_year_ago}" --format="%an" -- "{directory_path}"'
                recent_result = self.run_git_command(recent_cmd)

                if recent_result:
                    recent_authors = recent_result.split('\n')
                    recent_author_counts = {}
                    for author in recent_authors:
                        if author.strip():
                            recent_author_counts[author] = recent_author_counts.get(author, 0) + 1

                    for author, count in recent_author_counts.items():
                        contributors[author] = {
                            'total_commits': count,
                            'recent_commits': count,
                            'score': count * 3
                        }

            # 获取总体贡献统计
            cmd = f'git log --follow --format="%an" -- "{directory_path}"'
            total_result = self.run_git_command(cmd)

            if total_result:
                authors = total_result.split('\n')
                author_counts = {}
                for author in authors:
                    if author.strip():
                        author_counts[author] = author_counts.get(author, 0) + 1

                for author, count in author_counts.items():
                    if author in contributors:
                        contributors[author]['total_commits'] = count
                        contributors[author]['score'] = contributors[author]['recent_commits'] * 3 + count
                    else:
                        contributors[author] = {
                            'total_commits': count,
                            'recent_commits': 0,
                            'score': count
                        }

            return contributors
        except Exception as e:
            print(f"分析目录 {directory_path} 时出错: {e}")
            return {}

    def find_fallback_assignee(self, file_paths, active_contributors):
        """为未分配的组寻找备选负责人"""
        print(f"🔍 正在为未分配组寻找备选负责人...")

        # 尝试从文件路径向上查找目录贡献者
        directories_to_check = set()

        for file_path in file_paths:
            path_parts = file_path.split('/')
            # 检查各级父目录
            for i in range(len(path_parts) - 1, 0, -1):
                parent_dir = '/'.join(path_parts[:i])
                if parent_dir:
                    directories_to_check.add(parent_dir)

        # 按目录层级排序，优先检查更具体的目录
        sorted_dirs = sorted(directories_to_check, key=lambda x: x.count('/'), reverse=True)

        for directory in sorted_dirs:
            print(f"  检查目录: {directory}")
            dir_contributors = self.analyze_directory_contributors(directory)

            if dir_contributors:
                # 找到活跃的贡献者
                active_dir_contributors = {
                    author: stats for author, stats in dir_contributors.items()
                    if author in active_contributors
                }

                if active_dir_contributors:
                    # 返回评分最高的活跃贡献者
                    best_contributor = max(active_dir_contributors.items(), key=lambda x: x[1]['score'])
                    print(f"  ✅ 在目录 {directory} 找到候选人: {best_contributor[0]} (得分: {best_contributor[1]['score']})")
                    return best_contributor[0], best_contributor[1], directory

        # 如果都没找到，检查根目录
        print("  检查根目录...")
        root_contributors = self.analyze_directory_contributors(".")
        if root_contributors:
            active_root_contributors = {
                author: stats for author, stats in root_contributors.items()
                if author in active_contributors
            }

            if active_root_contributors:
                best_contributor = max(active_root_contributors.items(), key=lambda x: x[1]['score'])
                print(f"  ✅ 在根目录找到候选人: {best_contributor[0]} (得分: {best_contributor[1]['score']})")
                return best_contributor[0], best_contributor[1], "根目录"

        print("  ❌ 未找到合适的候选人")
        return None, None, None

    def analyze_divergence(self):
        """分析分支分叉情况"""
        print("🔍 正在分析分支分叉情况...")

        # 获取分叉点
        merge_base = self.run_git_command(f"git merge-base {self.source_branch} {self.target_branch}")
        if merge_base:
            print(f"分叉点: {merge_base}")
        else:
            print("❌ 无法确定分叉点")
            return None

        # 统计差异
        diff_stats = self.run_git_command(f"git diff --stat {self.source_branch} {self.target_branch}")
        if diff_stats:
            print(f"\n📊 差异统计:\n{diff_stats}")

        # 检查集成分支是否存在
        branch_exists = self.run_git_command(f"git show-ref --verify --quiet refs/heads/{self.integration_branch}")

        if branch_exists is None:
            # 分支不存在，创建新分支
            self.run_git_command(f"git checkout -b {self.integration_branch} {self.target_branch}")
            print(f"✅ 已创建集成分支: {self.integration_branch}")
        else:
            # 分支已存在，切换到该分支
            self.run_git_command(f"git checkout {self.integration_branch}")
            print(f"✅ 已切换到集成分支: {self.integration_branch}")

        # 预览合并结果
        merge_result = self.run_git_command(f"git merge --no-commit --no-ff {self.source_branch} 2>&1 || echo 'merge conflicts detected'")

        # 重置合并状态
        self.run_git_command("git merge --abort 2>/dev/null || true")

        return {
            "merge_base": merge_base,
            "diff_stats": diff_stats,
            "merge_preview": merge_result
        }

    def iterative_group_files(self, file_paths):
        """迭代式分组文件，避免递归深度问题"""
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

    def analyze_file_contributors(self, filepath, include_recent=True):
        """分析文件的主要贡献者（重点关注一年内的贡献）"""
        try:
            contributors = {}

            # 获取一年内的贡献统计 (重点)
            if include_recent:
                one_year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
                recent_cmd = f'git log --follow --since="{one_year_ago}" --format="%an" -- "{filepath}"'
                recent_result = self.run_git_command(recent_cmd)

                if recent_result:
                    recent_authors = recent_result.split('\n')
                    recent_author_counts = {}
                    for author in recent_authors:
                        if author.strip():
                            recent_author_counts[author] = recent_author_counts.get(author, 0) + 1

                    for author, count in recent_author_counts.items():
                        contributors[author] = {
                            'total_commits': count,
                            'recent_commits': count,
                            'score': count * 3
                        }

            # 获取总体贡献统计 (补充)
            cmd = f'git log --follow --format="%an" -- "{filepath}"'
            total_result = self.run_git_command(cmd)

            if total_result:
                authors = total_result.split('\n')
                author_counts = {}
                for author in authors:
                    if author.strip():
                        author_counts[author] = author_counts.get(author, 0) + 1

                for author, count in author_counts.items():
                    if author in contributors:
                        contributors[author]['total_commits'] = count
                        contributors[author]['score'] = contributors[author]['recent_commits'] * 3 + count
                    else:
                        contributors[author] = {
                            'total_commits': count,
                            'recent_commits': 0,
                            'score': count
                        }

            return contributors
        except Exception as e:
            print(f"分析文件 {filepath} 时出错: {e}")
            return {}

    def get_group_main_contributor(self, files):
        """获取文件组的主要贡献者（重点基于一年内贡献）"""
        all_contributors = {}

        for file in files:
            contributors = self.analyze_file_contributors(file)
            for author, stats in contributors.items():
                if author not in all_contributors:
                    all_contributors[author] = {
                        'total_commits': 0,
                        'recent_commits': 0,
                        'score': 0,
                        'file_count': 0
                    }

                all_contributors[author]['total_commits'] += stats['total_commits']
                all_contributors[author]['recent_commits'] += stats['recent_commits']
                all_contributors[author]['score'] += stats['score']
                all_contributors[author]['file_count'] += 1

        if not all_contributors:
            return None, {}

        # 返回综合得分最高的作者（重点是近期贡献）
        main_contributor = max(all_contributors.items(), key=lambda x: x[1]['score'])
        return main_contributor[0], all_contributors

    def create_merge_plan(self):
        """创建智能合并计划 - 迭代分组直至文件数<5，避免递归深度问题"""
        print(f"📋 正在创建智能合并计划（每组最多{self.max_files_per_group}个文件）...")

        # 获取所有变更文件
        changed_files_output = self.run_git_command(f"git diff --name-only {self.source_branch} {self.target_branch}")
        if not changed_files_output:
            print("⚠️ 没有发现文件差异")
            return None

        changed_files = changed_files_output.split('\n')
        changed_files = [f for f in changed_files if f.strip()]

        if not changed_files:
            print("⚠️ 没有发现有效的文件差异")
            return None

        print(f"🔍 发现 {len(changed_files)} 个变更文件，开始智能分组...")

        # 迭代分组文件（避免递归深度问题）
        try:
            file_groups = self.iterative_group_files(changed_files)
        except Exception as e:
            print(f"❌ 分组过程中出错: {e}")
            print("🔄 回退到简单批量分组模式...")
            # 回退到简单分组
            file_groups = []
            for i in range(0, len(changed_files), self.max_files_per_group):
                batch_files = changed_files[i:i+self.max_files_per_group]
                batch_name = f"batch-{i//self.max_files_per_group + 1:03d}"
                file_groups.append({
                    "name": batch_name,
                    "files": batch_files,
                    "file_count": len(batch_files),
                    "type": "fallback_batch"
                })

        print(f"📊 分组完成: {len(file_groups)} 个组")
        for i, group in enumerate(file_groups[:10]):
            print(f" - {group['name']}: {group['file_count']} 个文件 ({group['type']})")
        if len(file_groups) > 10:
            print(f" ... 还有 {len(file_groups) - 10} 个组")

        # 生成合并计划
        merge_plan = {
            "created_at": datetime.now().isoformat(),
            "source_branch": self.source_branch,
            "target_branch": self.target_branch,
            "integration_branch": self.integration_branch,
            "total_files": len(changed_files),
            "total_groups": len(file_groups),
            "max_files_per_group": self.max_files_per_group,
            "groups": []
        }

        for group_info in file_groups:
            merge_plan["groups"].append({
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
                "assignment_reason": ""  # 新增：分配原因
            })

        # 保存计划
        plan_file = self.work_dir / "merge_plan.json"
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(merge_plan, f, indent=2, ensure_ascii=False)

        print(f"✅ 智能合并计划已保存至: {plan_file}")
        print(f"📁 共生成 {len(file_groups)} 个分组，平均每组 {len(changed_files)/len(file_groups):.1f} 个文件")

        # 显示分组统计
        group_types = defaultdict(int)
        for group in file_groups:
            group_types[group["type"]] += 1

        print(f"📊 分组类型统计:")
        for group_type, count in group_types.items():
            print(f" - {group_type}: {count} 个组")

        return merge_plan

    def auto_assign_tasks(self, exclude_authors=None, max_tasks_per_person=3, include_fallback=True):
        """基于一年内贡献度自动分配合并任务，支持备选方案和活跃度过滤"""
        exclude_authors = exclude_authors or []
        plan_file = self.work_dir / "merge_plan.json"

        if not plan_file.exists():
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return None

        with open(plan_file, 'r', encoding='utf-8') as f:
            plan = json.load(f)

        print("🤖 正在基于一年内贡献度自动分配任务...")
        print("💡 评分规则：一年内提交数 × 3 + 历史提交数 × 1")
        print("🔍 自动排除近3个月无提交的人员")

        # 获取活跃贡献者
        active_contributors = self.get_active_contributors(3)

        # 自动添加不活跃的人员到排除列表
        all_contributors = self.get_all_contributors()
        inactive_contributors = all_contributors - active_contributors

        if inactive_contributors:
            print(f"🚫 自动排除近3个月无提交的 {len(inactive_contributors)} 位贡献者:")
            for contributor in sorted(list(inactive_contributors))[:5]:
                print(f"   - {contributor}")
            if len(inactive_contributors) > 5:
                print(f"   ... 还有 {len(inactive_contributors) - 5} 位")

        # 合并排除列表
        all_excluded = set(exclude_authors) | inactive_contributors

        assignment_count = {}
        unassigned_groups = []

        for group in plan["groups"]:
            print(f"\n分析组: {group['name']} ({group['file_count']} 个文件)")

            # 获取主要贡献者（重点关注一年内）
            main_contributor, all_contributors = self.get_group_main_contributor(group['files'])

            assigned = False
            assignment_reason = ""

            if main_contributor and main_contributor not in all_excluded:
                # 检查负载均衡
                current_count = assignment_count.get(main_contributor, 0)
                if current_count < max_tasks_per_person:
                    group["assignee"] = main_contributor
                    assignment_count[main_contributor] = current_count + 1
                    stats = all_contributors[main_contributor]
                    assignment_reason = f"基于文件贡献度直接分配 (一年内:{stats['recent_commits']}, 历史:{stats['total_commits']}, 得分:{stats['score']})"
                    print(f" ✅ 分配给: {main_contributor}")
                    print(f" 一年内提交: {stats['recent_commits']}, 历史提交: {stats['total_commits']}, 综合得分: {stats['score']}")
                    assigned = True
                else:
                    # 找第二合适的人选
                    sorted_contributors = sorted(all_contributors.items(), key=lambda x: x[1]['score'], reverse=True)
                    for author, stats in sorted_contributors[1:]:
                        if author not in all_excluded and assignment_count.get(author, 0) < max_tasks_per_person:
                            group["assignee"] = author
                            assignment_count[author] = assignment_count.get(author, 0) + 1
                            assignment_reason = f"负载均衡分配 (原推荐{main_contributor}已满负荷, 一年内:{stats['recent_commits']}, 历史:{stats['total_commits']}, 得分:{stats['score']})"
                            print(f" ✅ 分配给: {author}")
                            print(f" 一年内提交: {stats['recent_commits']}, 历史提交: {stats['total_commits']}, 综合得分: {stats['score']}")
                            print(f" (原推荐 {main_contributor} 已满负荷)")
                            assigned = True
                            break

            # 如果还未分配且启用备选方案，尝试目录级分配
            if not assigned and include_fallback:
                print(f" 🔄 启用备选分配方案...")
                fallback_assignee, fallback_stats, fallback_source = self.find_fallback_assignee(group['files'], active_contributors)

                if fallback_assignee and fallback_assignee not in all_excluded:
                    current_count = assignment_count.get(fallback_assignee, 0)
                    if current_count < max_tasks_per_person:
                        group["assignee"] = fallback_assignee
                        assignment_count[fallback_assignee] = current_count + 1
                        group["fallback_reason"] = f"通过{fallback_source}目录分析分配"
                        assignment_reason = f"备选目录分配 (来源:{fallback_source}, 一年内:{fallback_stats['recent_commits']}, 历史:{fallback_stats['total_commits']}, 得分:{fallback_stats['score']})"
                        print(f" ✅ 备选分配给: {fallback_assignee} (来源: {fallback_source})")
                        print(f" 目录贡献 - 一年内: {fallback_stats['recent_commits']}, 历史: {fallback_stats['total_commits']}, 得分: {fallback_stats['score']}")
                        assigned = True

            if not assigned:
                unassigned_groups.append(group['name'])
                if main_contributor:
                    if main_contributor in all_excluded:
                        if main_contributor in inactive_contributors:
                            assignment_reason = f"主要贡献者{main_contributor}近3个月无活跃提交，已自动排除"
                            print(f" ⚠️ 主要贡献者 {main_contributor} 近3个月无活跃提交，已自动排除")
                            group["notes"] = f"建议: {main_contributor} (近期活跃度不足，已自动排除)"
                        else:
                            assignment_reason = f"主要贡献者{main_contributor}在手动排除列表中"
                            print(f" ⚠️ 主要贡献者 {main_contributor} 在手动排除列表中")
                            main_stats = all_contributors[main_contributor]
                            group["notes"] = f"建议: {main_contributor} (近期:{main_stats['recent_commits']},历史:{main_stats['total_commits']},得分:{main_stats['score']}) 已手动排除"
                    else:
                        assignment_reason = f"主要贡献者{main_contributor}已达最大任务数{max_tasks_per_person}"
                        main_stats = all_contributors[main_contributor]
                        group["notes"] = f"建议: {main_contributor} (近期:{main_stats['recent_commits']},历史:{main_stats['total_commits']},得分:{main_stats['score']}) 但已达最大任务数"
                        print(f" ⚠️ 主要贡献者 {main_contributor} 已达最大任务数")
                else:
                    assignment_reason = "无法确定主要贡献者"
                    print(f" ⚠️ 无法确定主要贡献者，请手动分配")
                    group["notes"] = "无法确定主要贡献者"

            # 保存分配原因和贡献者信息
            group["assignment_reason"] = assignment_reason
            group["contributors"] = all_contributors

        # 保存更新后的计划
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)

        # 显示分配总结
        print(f"\n📊 自动分配总结:")
        print(f"🎯 活跃贡献者: {len(active_contributors)} 位")
        print(f"🚫 自动排除: {len(inactive_contributors)} 位（近3个月无提交）")
        print(f"🔧 手动排除: {len(exclude_authors)} 位")
        print(f"\n👥 任务分配:")
        for person, count in sorted(assignment_count.items(), key=lambda x: x[1], reverse=True):
            print(f" {person}: {count} 个任务")

        if unassigned_groups:
            print(f"\n⚠️ 未分配的组 ({len(unassigned_groups)}个): {', '.join(unassigned_groups[:3])}" + ("..." if len(unassigned_groups) > 3 else ""))

        print("✅ 智能自动分配完成")
        return plan

    def assign_tasks(self, assignments=None):
        """分配合并任务（手动或自动）"""
        if assignments is None:
            return self.auto_assign_tasks()

        plan_file = self.work_dir / "merge_plan.json"
        if not plan_file.exists():
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return None

        with open(plan_file, 'r', encoding='utf-8') as f:
            plan = json.load(f)

        for group_name, assignee in assignments.items():
            for group in plan["groups"]:
                if group["name"] == group_name:
                    group["assignee"] = assignee
                    group["assignment_reason"] = "手动分配"
                    break

        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)

        print("✅ 任务分配完成")
        return plan

    def view_group_details(self, group_name=None):
        """查看分组详细信息 - 显示具体文件和分配原因"""
        plan_file = self.work_dir / "merge_plan.json"
        if not plan_file.exists():
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return []

        with open(plan_file, 'r', encoding='utf-8') as f:
            plan = json.load(f)

        if group_name:
            # 查看指定组的详细信息
            target_group = None
            for group in plan["groups"]:
                if group["name"] == group_name:
                    target_group = group
                    break

            if not target_group:
                print(f"❌ 未找到组: {group_name}")
                return []

            self._display_group_detail(target_group)
            return [target_group]
        else:
            # 交互式选择查看
            print("📋 可用分组列表:")

            # 优化表格显示 - 使用固定列宽
            headers = ["序号", "组名", "类型", "文件数", "负责人", "状态"]
            widths = [6, 30, 18, 8, 20, 8]
            aligns = ['center', 'left', 'left', 'center', 'left', 'center']

            self._print_table_header(headers, widths, aligns)

            for i, group in enumerate(plan["groups"], 1):
                assignee = group.get("assignee", "未分配")
                status = "✅" if group.get("status") == "completed" else "🔄" if assignee != "未分配" else "⏳"
                group_type = group.get("group_type", "unknown")
                file_count = group.get("file_count", len(group["files"]))

                values = [str(i), group['name'], group_type, str(file_count), assignee, status]
                self._print_table_row(values, widths, aligns)

            self._print_table_separator(widths)

            try:
                choice = input("请输入要查看的组序号 (回车返回): ").strip()
                if not choice:
                    return []

                index = int(choice) - 1
                if 0 <= index < len(plan["groups"]):
                    selected_group = plan["groups"][index]
                    self._display_group_detail(selected_group)
                    return [selected_group]
                else:
                    print("❌ 无效的序号")
                    return []
            except ValueError:
                print("❌ 请输入有效的数字")
                return []

    def _display_group_detail(self, group):
        """显示单个组的详细信息"""
        print("\n" + "="*100)
        print(f"📁 组详细信息: {group['name']}")
        print("="*100)

        # 基本信息
        print(f"📊 基本信息:")
        print(f"   组名: {group['name']}")
        print(f"   类型: {group.get('group_type', 'unknown')} ({self._get_group_type_description(group.get('group_type', 'unknown'))})")
        print(f"   文件数: {group.get('file_count', len(group['files']))} 个")
        print(f"   负责人: {group.get('assignee', '未分配')}")
        print(f"   状态: {'✅ 已完成' if group.get('status') == 'completed' else '🔄 进行中' if group.get('assignee') else '⏳ 待分配'}")

        # 分配原因
        assignment_reason = group.get('assignment_reason', '未指定')
        if assignment_reason:
            print(f"   分配原因: {assignment_reason}")

        # 备选分配信息
        fallback_reason = group.get('fallback_reason', '')
        if fallback_reason:
            print(f"   备选原因: {fallback_reason}")

        # 文件列表
        print(f"\n📄 包含文件列表:")
        files = group.get('files', [])
        for i, file_path in enumerate(files, 1):
            print(f"   {i:2d}. {file_path}")

        # 贡献者分析 - 优化表格显示
        contributors = group.get('contributors', {})
        if contributors:
            print(f"\n👥 贡献者分析 (基于一年内活跃度):")

            headers = ["排名", "贡献者", "一年内", "历史总计", "综合得分", "参与文件"]
            widths = [6, 25, 10, 12, 12, 12]
            aligns = ['center', 'left', 'center', 'center', 'center', 'center']

            self._print_table_header(headers, widths, aligns)

            sorted_contributors = sorted(contributors.items(), key=lambda x: x[1]['score'] if isinstance(x[1], dict) else x[1], reverse=True)
            for i, (author, stats) in enumerate(sorted_contributors[:10], 1):
                if isinstance(stats, dict):
                    recent = stats.get('recent_commits', 0)
                    total = stats.get('total_commits', 0)
                    score = stats.get('score', 0)
                    file_count = stats.get('file_count', 0)
                    values = [str(i), author, str(recent), str(total), str(score), str(file_count)]
                else:
                    values = [str(i), author, 'N/A', str(stats), str(stats), 'N/A']

                self._print_table_row(values, widths, aligns)

            if len(sorted_contributors) > 10:
                print(f"   ... 还有 {len(sorted_contributors) - 10} 位贡献者")

        # 备注信息
        notes = group.get('notes', '')
        if notes:
            print(f"\n📝 备注: {notes}")

        print("="*100)

    def _get_group_type_description(self, group_type):
        """获取分组类型的描述"""
        descriptions = {
            'simple_group': '简单分组 - 文件数量较少，直接分组',
            'direct_files': '直接文件 - 目录下的直接文件',
            'subdir_group': '子目录分组 - 按子目录划分',
            'alpha_group': '字母分组 - 根目录文件按首字母分组',
            'batch_group': '批量分组 - 大量文件分批处理',
            'fallback_batch': '回退批量 - 分组失败后的简单批量处理'
        }
        return descriptions.get(group_type, '未知类型')

    def show_assignment_reasons(self):
        """显示所有组的分配原因分析"""
        plan_file = self.work_dir / "merge_plan.json"
        if not plan_file.exists():
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return

        with open(plan_file, 'r', encoding='utf-8') as f:
            plan = json.load(f)

        print("\n📊 任务分配原因分析报告")
        print("="*120)

        # 统计分配原因类型
        reason_stats = defaultdict(list)
        for group in plan["groups"]:
            assignment_reason = group.get('assignment_reason', '未指定')
            reason_type = self._categorize_assignment_reason(assignment_reason)
            reason_stats[reason_type].append(group)

        print("📈 分配原因统计:")
        for reason_type, groups in reason_stats.items():
            print(f"   {reason_type}: {len(groups)} 个组")

        print()

        # 优化表格显示
        headers = ["组名", "负责人", "文件数", "分配类型", "详细原因"]
        widths = [30, 20, 8, 18, 50]
        aligns = ['left', 'left', 'center', 'left', 'left']

        self._print_table_header(headers, widths, aligns)

        for group in plan["groups"]:
            assignee = group.get('assignee', '未分配')
            file_count = group.get('file_count', len(group['files']))
            assignment_reason = group.get('assignment_reason', '未指定')
            reason_type = self._categorize_assignment_reason(assignment_reason)

            # 截断过长的原因说明
            short_reason = assignment_reason[:45] + "..." if len(assignment_reason) > 45 else assignment_reason

            values = [group['name'], assignee, str(file_count), reason_type, short_reason]
            self._print_table_row(values, widths, aligns)

        self._print_table_separator(widths)

        # 分类详细展示
        print(f"\n📋 分类详细分析:")
        for reason_type, groups in reason_stats.items():
            if not groups:
                continue

            print(f"\n🔍 {reason_type} ({len(groups)} 个组):")
            for group in groups[:5]:  # 只显示前5个
                assignee = group.get('assignee', '未分配')
                assignment_reason = group.get('assignment_reason', '未指定')
                print(f"   - {group['name']} → {assignee}")
                print(f"     原因: {assignment_reason}")

            if len(groups) > 5:
                print(f"   ... 还有 {len(groups) - 5} 个组")

    def _categorize_assignment_reason(self, reason):
        """将分配原因分类"""
        if not reason or reason == '未指定':
            return '未指定'
        elif '基于文件贡献度直接分配' in reason:
            return '直接分配'
        elif '负载均衡分配' in reason:
            return '负载均衡'
        elif '备选目录分配' in reason:
            return '备选分配'
        elif '手动分配' in reason:
            return '手动分配'
        elif '无法确定主要贡献者' in reason:
            return '无贡献者'
        elif '已自动排除' in reason:
            return '自动排除'
        elif '已达最大任务数' in reason:
            return '任务满载'
        else:
            return '其他'

    def search_assignee_tasks(self, assignee_name):
        """根据负责人搜索其负责的所有模块"""
        plan_file = self.work_dir / "merge_plan.json"
        if not plan_file.exists():
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return []

        with open(plan_file, 'r', encoding='utf-8') as f:
            plan = json.load(f)

        assignee_groups = []
        total_files = 0

        for group in plan["groups"]:
            if group.get("assignee", "").lower() == assignee_name.lower():
                assignee_groups.append(group)
                total_files += group.get("file_count", len(group["files"]))

        if not assignee_groups:
            print(f"📋 负责人 '{assignee_name}' 暂无分配的任务")
            return []

        print(f"👤 负责人: {assignee_name}")
        print(f"📊 总览: {len(assignee_groups)} 个组, {total_files} 个文件")

        # 优化表格显示
        headers = ["组名", "文件数", "状态", "类型", "分配原因"]
        widths = [30, 8, 8, 18, 40]
        aligns = ['left', 'center', 'center', 'left', 'left']

        self._print_table_header(headers, widths, aligns)

        completed = 0
        pending = 0

        for group in assignee_groups:
            status = group.get("status", "pending")
            status_icon = "✅" if status == "completed" else "🔄"
            file_count = group.get("file_count", len(group["files"]))
            group_type = group.get("group_type", "unknown")
            assignment_reason = group.get("assignment_reason", "未指定")

            if status == "completed":
                completed += 1
            else:
                pending += 1

            # 截断长的分配原因
            short_reason = assignment_reason[:35] + "..." if len(assignment_reason) > 35 else assignment_reason

            values = [group['name'], str(file_count), status_icon, group_type, short_reason]
            self._print_table_row(values, widths, aligns)

        self._print_table_separator(widths)
        print(f"📈 进度: {completed}/{len(assignee_groups)} 组已完成, {pending} 组待处理")

        # 显示详细文件列表
        if len(assignee_groups) <= 3:  # 只有少量组时显示详细信息
            print(f"\n📄 详细文件列表:")
            for i, group in enumerate(assignee_groups, 1):
                print(f"\n{i}. 组: {group['name']} ({group.get('file_count', len(group['files']))} 文件)")
                assignment_reason = group.get("assignment_reason", "未指定")
                print(f"   分配原因: {assignment_reason}")
                for file in group['files'][:5]:  # 最多显示5个文件
                    print(f"   - {file}")
                if len(group['files']) > 5:
                    print(f"   ... 还有 {len(group['files']) - 5} 个文件")

        return assignee_groups

    def create_merge_branch(self, group_name, assignee):
        """为指定任务创建合并分支"""
        branch_name = f"feat/merge-{group_name.replace('/', '-')}-{assignee.replace(' ', '-')}"

        # 创建工作分支
        self.run_git_command(f"git checkout {self.integration_branch}")
        result = self.run_git_command(f"git checkout -b {branch_name}")

        if result is not None:
            print(f"✅ 已创建合并分支: {branch_name}")
        else:
            print(f"⚠️ 分支 {branch_name} 可能已存在，正在切换")
            self.run_git_command(f"git checkout {branch_name}")

        return branch_name

    def check_file_existence(self, files, branch):
        """检查文件在指定分支中是否存在"""
        existing_files = []
        missing_files = []

        for file in files:
            # 检查文件是否在指定分支中存在
            result = self.run_git_command(f"git cat-file -e {branch}:{file} 2>/dev/null")
            if result is not None:
                existing_files.append(file)
            else:
                missing_files.append(file)

        return existing_files, missing_files

    def generate_smart_merge_script(self, group_name, assignee, files, branch_name):
        """生成智能合并脚本，处理新文件和已存在文件"""
        # 检查文件存在性
        existing_files, missing_files = self.check_file_existence(files, self.target_branch)

        print(f"📊 文件分析:")
        print(f"  - 已存在文件: {len(existing_files)} 个")
        print(f"  - 新增文件: {len(missing_files)} 个")

        # 生成处理脚本
        script_content = f"""#!/bin/bash
# 智能合并脚本 - {group_name} (负责人: {assignee})
# 文件数: {len(files)} (已存在: {len(existing_files)}, 新增: {len(missing_files)})
# 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

set -e # 遇到错误立即退出

echo "🚀 开始智能合并组: {group_name}"
echo "👤 负责人: {assignee}"
echo "🌿 工作分支: {branch_name}"
echo "📁 总文件数: {len(files)}"
echo "📊 已存在文件: {len(existing_files)}"
echo "📊 新增文件: {len(missing_files)}"
echo ""

# 切换到工作分支
echo "📋 切换到工作分支..."
git checkout {branch_name}

echo "📄 文件详情:"
"""

        if existing_files:
            script_content += f"""
echo "✅ 已存在文件 ({len(existing_files)}个):"
{chr(10).join([f'echo "  - {file}"' for file in existing_files])}
"""

        if missing_files:
            script_content += f"""
echo "🆕 新增文件 ({len(missing_files)}个):"
{chr(10).join([f'echo "  - {file}"' for file in missing_files])}
"""

        script_content += f"""
echo ""

# 智能合并策略
merge_success=true

echo "🔄 开始智能选择性合并..."
"""

        # 处理已存在文件
        if existing_files:
            script_content += f"""
echo "📝 处理已存在文件..."
if git checkout {self.source_branch} -- {' '.join([f'"{f}"' for f in existing_files])}; then
    echo "✅ 已存在文件合并成功"
else
    echo "⚠️ 已存在文件合并时出现问题"
    merge_success=false
fi
"""

        # 处理新增文件
        if missing_files:
            script_content += f"""
echo "🆕 处理新增文件..."
"""
            for file in missing_files:
                script_content += f"""
echo "  处理新文件: {file}"
# 创建目录结构
mkdir -p "$(dirname "{file}")"
# 从源分支复制文件内容
if git show {self.source_branch}:{file} > "{file}" 2>/dev/null; then
    git add "{file}"
    echo "    ✅ 新文件 {file} 添加成功"
else
    echo "    ❌ 无法从源分支获取文件: {file}"
    merge_success=false
fi
"""

        script_content += f"""
echo ""

if [ "$merge_success" = true ]; then
    echo "✅ 智能合并完成!"
    echo ""
    echo "📊 合并状态:"
    git status --short
    echo ""
    echo "🔍 文件差异概览:"
    git diff --cached --stat 2>/dev/null || echo "(新文件无差异显示)"
    echo ""
    echo "⏭️ 下一步操作："
    echo " 1. 检查合并结果: git diff --cached"
    echo " 2. 检查新文件内容: git diff --no-index /dev/null <文件名>"
    echo " 3. 提交更改: git commit -m 'Merge group: {group_name} ({len(files)} files)'"
    echo " 4. 推送分支: git push origin {branch_name}"
    echo ""
    echo "🔄 如需回滚: git reset --hard HEAD"
else
    echo "❌ 智能合并过程中出现问题"
    echo "🔧 可能的问题和解决方案："
    echo " 1. 文件在源分支中不存在 - 请检查分支和文件路径"
    echo " 2. 权限问题 - 请检查文件和目录权限"
    echo " 3. 路径问题 - 请检查文件路径是否正确"
    echo ""
    echo "📊 当前状态:"
    git status
    echo ""
    echo "🛠️ 手动处理步骤："
    echo " 1. 检查具体错误: 查看上方错误信息"
    echo " 2. 手动复制问题文件: cp source/path target/path"
    echo " 3. 添加文件: git add <files>"
    echo " 4. 提交: git commit -m 'Manual merge: {group_name}'"
    exit 1
fi
"""

        return script_content

    def merge_group(self, group_name):
        """合并指定组的文件 - 智能处理新文件和已存在文件"""
        plan_file = self.work_dir / "merge_plan.json"
        if not plan_file.exists():
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return False

        with open(plan_file, 'r', encoding='utf-8') as f:
            plan = json.load(f)

        # 找到对应组
        group_info = None
        for group in plan["groups"]:
            if group["name"] == group_name:
                group_info = group
                break

        if not group_info:
            print(f"❌ 未找到组: {group_name}")
            return False

        assignee = group_info["assignee"]
        if not assignee:
            print(f"❌ 组 {group_name} 尚未分配负责人")
            return False

        # 创建合并分支
        branch_name = self.create_merge_branch(group_name, assignee)

        # 生成智能合并脚本
        script_content = self.generate_smart_merge_script(
            group_name, assignee, group_info["files"], branch_name
        )

        script_file = self.work_dir / f"merge_{group_name.replace('/', '_')}.sh"
        with open(script_file, 'w') as f:
            f.write(script_content)

        os.chmod(script_file, 0o755)

        print(f"✅ 已生成智能合并脚本: {script_file}")
        print(f"🎯 请执行: ./{script_file}")

        return True

    def finalize_merge(self):
        """完成最终合并"""
        print("🎯 开始最终合并...")

        plan_file = self.work_dir / "merge_plan.json"
        if not plan_file.exists():
            print("❌ 合并计划文件不存在")
            return False

        with open(plan_file, 'r', encoding='utf-8') as f:
            plan = json.load(f)

        # 切换到集成分支
        self.run_git_command(f"git checkout {self.integration_branch}")

        # 检查哪些分支已完成
        completed_branches = []
        for group in plan["groups"]:
            if group["status"] == "completed" and group.get("assignee"):
                branch_name = f"feat/merge-{group['name'].replace('/', '-')}-{group['assignee'].replace(' ', '-')}"
                # 检查分支是否存在
                if self.run_git_command(f"git show-ref --verify --quiet refs/heads/{branch_name}") is not None:
                    completed_branches.append((branch_name, group))

        if not completed_branches:
            print("⚠️ 没有找到已完成的合并分支")
            return False

        print(f"🔍 发现 {len(completed_branches)} 个已完成的分支:")
        total_files = 0
        for branch_name, group in completed_branches:
            file_count = group.get('file_count', len(group['files']))
            total_files += file_count
            print(f" - {branch_name} ({file_count} 文件)")

        print(f"📊 总计将合并 {total_files} 个文件")

        # 合并所有完成的分支
        for branch_name, group in completed_branches:
            print(f"🔄 正在合并分支: {branch_name}")
            result = self.run_git_command(f"git merge --no-ff -m 'Merge branch {branch_name}: {group['name']}' {branch_name}")
            if result is not None:
                print(f" ✅ 成功合并 {branch_name}")
            else:
                print(f" ❌ 合并 {branch_name} 时出现问题")
                return False

        print("🎉 最终合并完成!")
        print(f"📋 集成分支 {self.integration_branch} 已包含所有更改")
        print(f"🚀 建议操作:")
        print(f" 1. 验证合并结果: git log --oneline -10")
        print(f" 2. 推送到远程: git push origin {self.integration_branch}")
        print(f" 3. 创建PR/MR合并到 {self.target_branch}")
        return True

    def merge_assignee_tasks(self, assignee_name):
        """合并指定负责人的所有任务 - 智能处理新文件和已存在文件"""
        plan_file = self.work_dir / "merge_plan.json"
        if not plan_file.exists():
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return False

        with open(plan_file, 'r', encoding='utf-8') as f:
            plan = json.load(f)

        # 找到负责人的所有任务
        assignee_groups = []
        for group in plan["groups"]:
            if group.get("assignee", "").lower() == assignee_name.lower():
                assignee_groups.append(group)

        if not assignee_groups:
            print(f"❌ 负责人 '{assignee_name}' 没有分配的任务")
            return False

        print(f"🎯 开始批量合并负责人 '{assignee_name}' 的所有任务...")
        print(f"📋 共 {len(assignee_groups)} 个组，总计 {sum(g.get('file_count', len(g['files'])) for g in assignee_groups)} 个文件")

        # 收集所有文件
        all_files = []
        for group in assignee_groups:
            all_files.extend(group["files"])

        if not all_files:
            print("❌ 没有找到需要合并的文件")
            return False

        # 检查文件存在性
        existing_files, missing_files = self.check_file_existence(all_files, self.target_branch)

        print(f"📊 批量合并文件分析:")
        print(f"  - 已存在文件: {len(existing_files)} 个")
        print(f"  - 新增文件: {len(missing_files)} 个")

        # 创建统一的合并分支
        batch_branch_name = f"feat/merge-batch-{assignee_name.replace(' ', '-')}-{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        print(f"\n🌿 创建批量合并分支: {batch_branch_name}")
        self.run_git_command(f"git checkout {self.integration_branch}")
        result = self.run_git_command(f"git checkout -b {batch_branch_name}")

        if result is None:
            print(f"⚠️ 分支创建可能失败，尝试切换到现有分支")
            self.run_git_command(f"git checkout {batch_branch_name}")

        # 生成智能批量合并脚本
        script_content = f"""#!/bin/bash
# 批量智能合并脚本 - 负责人: {assignee_name}
# 组数: {len(assignee_groups)} (文件总数: {len(all_files)}, 已存在: {len(existing_files)}, 新增: {len(missing_files)})
# 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

set -e # 遇到错误立即退出

echo "🚀 开始批量智能合并负责人 '{assignee_name}' 的所有任务"
echo "🌿 工作分支: {batch_branch_name}"
echo "📁 总文件数: {len(all_files)}"
echo "📊 已存在文件: {len(existing_files)}"
echo "📊 新增文件: {len(missing_files)}"
echo "📋 包含组: {', '.join([g['name'] for g in assignee_groups])}"
echo ""

# 切换到工作分支
echo "📋 切换到工作分支..."
git checkout {batch_branch_name}

echo "📄 组别详情:"
{chr(10).join([f'echo "  组 {g["name"]}: {g.get("file_count", len(g["files"]))} 个文件"' for g in assignee_groups])}
echo ""

# 智能合并策略
merge_success=true

echo "🔄 开始批量智能选择性合并..."
"""

        # 处理已存在文件
        if existing_files:
            script_content += f"""
echo "📝 处理已存在文件 ({len(existing_files)}个)..."
if git checkout {self.source_branch} -- {' '.join([f'"{f}"' for f in existing_files])}; then
    echo "✅ 已存在文件批量合并成功"
else
    echo "⚠️ 部分已存在文件合并时出现问题"
    merge_success=false
fi
"""

        # 处理新增文件
        if missing_files:
            script_content += f"""
echo "🆕 处理新增文件 ({len(missing_files)}个)..."
"""
            for file in missing_files:
                script_content += f"""
echo "  处理新文件: {file}"
# 创建目录结构
mkdir -p "$(dirname "{file}")"
# 从源分支复制文件内容
if git show {self.source_branch}:{file} > "{file}" 2>/dev/null; then
    git add "{file}"
    echo "    ✅ 新文件 {file} 添加成功"
else
    echo "    ❌ 无法从源分支获取文件: {file}"
    merge_success=false
fi
"""

        script_content += f"""
echo ""

if [ "$merge_success" = true ]; then
    echo "✅ 批量智能合并完成!"
    echo ""
    echo "📊 合并状态:"
    git status --short
    echo ""
    echo "🔍 文件差异概览:"
    git diff --cached --stat 2>/dev/null || echo "(新文件无差异显示)"
    echo ""
    echo "⏭️ 下一步操作："
    echo " 1. 检查合并结果: git diff --cached"
    echo " 2. 检查新文件内容 (如有): git diff --no-index /dev/null <文件名>"
    echo " 3. 提交更改: git commit -m 'Batch merge for {assignee_name}: {len(assignee_groups)} groups, {len(all_files)} files'"
    echo " 4. 推送分支: git push origin {batch_branch_name}"
    echo ""
    echo "🔄 如需回滚: git reset --hard HEAD"
else
    echo "❌ 批量智能合并过程中出现问题"
    echo ""
    echo "🔧 可能的问题和解决方案："
    echo " 1. 某些文件在源分支中不存在 - 请检查文件路径和分支"
    echo " 2. 权限问题 - 请检查文件和目录权限"
    echo " 3. 路径冲突 - 请检查文件路径是否正确"
    echo ""
    echo "📊 当前状态:"
    git status
    echo ""
    echo "🛠️ 手动处理步骤："
    echo " 1. 检查具体错误信息 (见上方输出)"
    echo " 2. 对于问题文件，手动复制: cp source_branch_checkout/path target/path"
    echo " 3. 添加文件: git add <files>"
    echo " 4. 提交: git commit -m 'Manual batch merge for {assignee_name}'"
    echo ""
    echo "💡 提示: 你可以分组处理，先处理成功的文件，再单独处理问题文件"
    exit 1
fi
"""

        script_file = self.work_dir / f"merge_batch_{assignee_name.replace(' ', '_')}.sh"
        with open(script_file, 'w') as f:
            f.write(script_content)

        os.chmod(script_file, 0o755)

        print(f"✅ 已生成智能批量合并脚本: {script_file}")
        print(f"🎯 请执行: ./{script_file}")

        return True

    def check_status(self):
        """检查合并状态"""
        plan_file = self.work_dir / "merge_plan.json"
        if not plan_file.exists():
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return

        with open(plan_file, 'r', encoding='utf-8') as f:
            plan = json.load(f)

        print("📊 智能合并状态概览:")
        print(f"源分支: {plan['source_branch']}")
        print(f"目标分支: {plan['target_branch']}")
        print(f"集成分支: {plan['integration_branch']}")
        print(f"总文件数: {plan['total_files']}")
        print(f"每组最大文件数: {plan.get('max_files_per_group', 5)}")
        print()

        assigned_count = 0
        completed_count = 0
        total_groups = len(plan["groups"])
        total_files_assigned = 0
        fallback_assigned = 0

        print("📋 智能分组与任务分配状态:")

        # 优化表格显示
        headers = ["组名", "文件数", "负责人", "状态", "分配类型", "推荐理由"]
        widths = [30, 8, 20, 8, 12, 35]
        aligns = ['left', 'center', 'left', 'center', 'left', 'left']

        self._print_table_header(headers, widths, aligns)

        for group in plan["groups"]:
            status_icon = "✅" if group["status"] == "completed" else "🔄" if group.get("assignee") else "⏳"
            assignee = group.get("assignee", "未分配")
            file_count = group.get("file_count", len(group["files"]))

            # 获取分配类型
            assignment_reason = group.get("assignment_reason", "未指定")
            assignment_type = self._categorize_assignment_reason(assignment_reason)

            # 获取推荐信息
            recommended_info = "N/A"

            # 检查是否是备选分配
            is_fallback = bool(group.get("fallback_reason", ""))
            if is_fallback:
                fallback_assigned += 1

            if assignee != "未分配" and 'contributors' in group and group['contributors']:
                if assignee in group['contributors']:
                    contributor_stats = group['contributors'][assignee]
                    if isinstance(contributor_stats, dict):
                        recent_commits = contributor_stats.get('recent_commits', 0)
                        total_commits = contributor_stats.get('total_commits', 0)
                        score = contributor_stats.get('score', 0)
                        if is_fallback:
                            recommended_info = f"[备选]{group['fallback_reason'][:15]}"
                        else:
                            recommended_info = f"得分:{score}(近期:{recent_commits})"
                    else:
                        recommended_info = f"历史提交:{contributor_stats}"
                elif 'contributors' in group and group['contributors']:
                    # 显示最推荐的贡献者
                    try:
                        best_contributor = max(group['contributors'].items(), key=lambda x: x[1]['score'] if isinstance(x[1], dict) else x[1])
                        contributor_name = best_contributor[0]
                        stats = best_contributor[1]
                        if isinstance(stats, dict):
                            recommended_info = f"推荐:{contributor_name}({stats['score']})"
                        else:
                            recommended_info = f"推荐:{contributor_name}({stats})"
                    except:
                        recommended_info = "分析中..."

            values = [group['name'], str(file_count), assignee, status_icon, assignment_type, recommended_info]
            self._print_table_row(values, widths, aligns)

            if assignee != "未分配":
                assigned_count += 1
                total_files_assigned += file_count
                if group["status"] == "completed":
                    completed_count += 1

        self._print_table_separator(widths)
        print(f"📈 进度统计: {assigned_count}/{total_groups} 组已分配 ({total_files_assigned}/{plan['total_files']} 文件), {completed_count}/{total_groups} 组已完成")
        print(f"🔄 备选分配: {fallback_assigned} 组通过目录分析分配")

        if assigned_count < total_groups:
            unassigned = [g['name'] for g in plan['groups'] if not g.get('assignee')]
            print(f"\n⚠️ 未分配的组: {', '.join(unassigned[:5])}" + ("..." if len(unassigned) > 5 else ""))

        # 显示负载分布
        assignee_workload = {}
        for group in plan["groups"]:
            assignee = group.get("assignee")
            if assignee and assignee != "未分配":
                if assignee not in assignee_workload:
                    assignee_workload[assignee] = {"groups": 0, "files": 0, "completed": 0, "fallback": 0}
                assignee_workload[assignee]["groups"] += 1
                assignee_workload[assignee]["files"] += group.get("file_count", len(group["files"]))
                if group["status"] == "completed":
                    assignee_workload[assignee]["completed"] += 1
                if group.get("fallback_reason"):
                    assignee_workload[assignee]["fallback"] += 1

        if assignee_workload:
            print(f"\n👥 负载分布:")
            for person, workload in sorted(assignee_workload.items(), key=lambda x: x[1]["files"], reverse=True):
                fallback_info = f"(含{workload['fallback']}个备选)" if workload['fallback'] > 0 else ""
                print(f" {person}: {workload['completed']}/{workload['groups']} 组完成, {workload['files']} 个文件 {fallback_info}")

    def show_contributor_analysis(self):
        """显示贡献者分析（重点关注一年内活跃度）"""
        plan_file = self.work_dir / "merge_plan.json"
        if not plan_file.exists():
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return

        with open(plan_file, 'r', encoding='utf-8') as f:
            plan = json.load(f)

        print("\n👥 智能贡献者分析报告 (重点关注一年内活跃度):")
        print("=" * 90)
        print("💡 评分规则：一年内提交数 × 3 + 历史总提交数 × 1")
        print("🎯 分配策略：优先分配给近期活跃且熟悉相关文件的开发者")
        print("🚫 自动排除：近3个月无提交的人员")

        # 获取活跃贡献者信息
        active_contributors = self.get_active_contributors(3)
        all_contributors_global = {}

        for group in plan["groups"]:
            print(f"\n📁 组: {group['name']} ({group.get('file_count', len(group['files']))} 文件)")

            assignee = group.get('assignee', '未分配')
            fallback_reason = group.get('fallback_reason', '')

            if assignee != '未分配':
                if fallback_reason:
                    print(f" 当前分配: {assignee} [备选分配: {fallback_reason}]")
                else:
                    print(f" 当前分配: {assignee}")
            else:
                print(f" 当前分配: 未分配")

            if 'contributors' in group and group['contributors']:
                print(" 贡献者排名 (一年内|历史总计|综合得分|活跃状态):")
                sorted_contributors = sorted(
                    group['contributors'].items(),
                    key=lambda x: x[1]['score'] if isinstance(x[1], dict) else x[1],
                    reverse=True
                )
                for i, (author, stats) in enumerate(sorted_contributors[:3], 1):
                    if isinstance(stats, dict):
                        recent = stats['recent_commits']
                        total = stats['total_commits']
                        score = stats['score']

                        # 活跃度和状态标识
                        if author in active_contributors:
                            if recent >= 10:
                                activity = "🔥活跃"
                            elif recent >= 3:
                                activity = "📈中等"
                            elif recent >= 1:
                                activity = "📊低等"
                            else:
                                activity = "📊近期"
                        else:
                            activity = "💤静默"

                        print(f" {i}. {author}: {recent}|{total}|{score} {activity}")
                    else:
                        activity = "📊历史" if author in active_contributors else "💤静默"
                        print(f" {i}. {author}: ?|{stats}|{stats} {activity}")

                    # 统计全局贡献
                    if author not in all_contributors_global:
                        all_contributors_global[author] = {
                            'total_commits': 0,
                            'recent_commits': 0,
                            'score': 0,
                            'groups_contributed': 0,
                            'groups_assigned': [],
                            'is_active': author in active_contributors
                        }

                    if isinstance(stats, dict):
                        all_contributors_global[author]['recent_commits'] += stats['recent_commits']
                        all_contributors_global[author]['total_commits'] += stats['total_commits']
                        all_contributors_global[author]['score'] += stats['score']
                    else:
                        all_contributors_global[author]['total_commits'] += stats
                        all_contributors_global[author]['score'] += stats

                    all_contributors_global[author]['groups_contributed'] += 1

                    # 检查是否被分配到这个组
                    if group.get('assignee') == author:
                        all_contributors_global[author]['groups_assigned'].append(group['name'])
            else:
                print(" ⚠️ 贡献者数据未分析，请先运行自动分配任务")

        if all_contributors_global:
            print(f"\n🏆 全局贡献者智能排名 (基于一年内活跃度):")

            # 优化表格显示
            headers = ["排名", "姓名", "近期", "历史", "得分", "活跃状态", "参与组", "分配组", "近期活跃"]
            widths = [6, 20, 6, 6, 8, 10, 8, 8, 10]
            aligns = ['center', 'left', 'center', 'center', 'center', 'center', 'center', 'center', 'center']

            self._print_table_header(headers, widths, aligns)

            sorted_global = sorted(all_contributors_global.items(), key=lambda x: x[1]['score'], reverse=True)

            for i, (author, stats) in enumerate(sorted_global[:20], 1):
                recent = stats['recent_commits']
                total = stats['total_commits']
                score = stats['score']
                contributed = stats['groups_contributed']
                assigned = len(stats['groups_assigned'])
                is_active = stats['is_active']

                # 活跃度判断 (重点关注近期)
                if not is_active:
                    activity = "💤静默"
                elif recent >= 15:
                    activity = "🔥高"
                elif recent >= 5:
                    activity = "📈中"
                elif recent >= 1:
                    activity = "📊低"
                else:
                    activity = "📊近期"

                assigned_display = f"{assigned}组" if assigned > 0 else "无"
                active_status = "✅" if is_active else "❌"

                values = [str(i), author, str(recent), str(total), str(score), activity, str(contributed), assigned_display, active_status]
                self._print_table_row(values, widths, aligns)

            print(f"\n📊 活跃度说明 (基于一年内提交 + 近3个月活跃度):")
            print("🔥高: 15+次 📈中: 5-14次 📊低: 1-4次 📊近期: 近期有活动 💤静默: 近3个月无提交")
            print("✅: 近3个月活跃 ❌: 近3个月静默")
            print("\n🎯 建议: 优先将任务分配给✅且🔥📈级别的开发者，确保合并质量和效率")
        else:
            print("\n⚠️ 暂无贡献者数据，请先运行自动分配任务以分析贡献度")

    def mark_group_completed(self, group_name):
        """标记指定组为已完成"""
        plan_file = self.work_dir / "merge_plan.json"
        if not plan_file.exists():
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return False

        with open(plan_file, 'r', encoding='utf-8') as f:
            plan = json.load(f)

        # 找到对应组
        group_found = False
        for group in plan["groups"]:
            if group["name"] == group_name:
                group_found = True
                old_status = group.get("status", "pending")
                group["status"] = "completed"
                group["completed_at"] = datetime.now().isoformat()

                assignee = group.get("assignee", "未分配")
                file_count = group.get("file_count", len(group["files"]))

                print(f"✅ 组 '{group_name}' 已标记为完成")
                print(f"   负责人: {assignee}")
                print(f"   文件数: {file_count}")
                print(f"   状态变更: {old_status} → completed")
                break

        if not group_found:
            print(f"❌ 未找到组: {group_name}")
            return False

        # 保存更新
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)

        # 显示整体进度
        completed_count = sum(1 for g in plan["groups"] if g.get("status") == "completed")
        total_count = len(plan["groups"])
        print(f"📊 整体进度: {completed_count}/{total_count} 组已完成 ({completed_count/total_count*100:.1f}%)")

        return True

    def mark_assignee_completed(self, assignee_name):
        """标记指定负责人的所有任务为已完成"""
        plan_file = self.work_dir / "merge_plan.json"
        if not plan_file.exists():
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return False

        with open(plan_file, 'r', encoding='utf-8') as f:
            plan = json.load(f)

        # 找到负责人的所有任务
        assignee_groups = []
        for group in plan["groups"]:
            if group.get("assignee", "").lower() == assignee_name.lower():
                assignee_groups.append(group)

        if not assignee_groups:
            print(f"❌ 负责人 '{assignee_name}' 没有分配的任务")
            return False

        # 标记所有任务为完成
        completion_time = datetime.now().isoformat()
        completed_count = 0

        for group in assignee_groups:
            if group.get("status") != "completed":
                group["status"] = "completed"
                group["completed_at"] = completion_time
                completed_count += 1

        # 保存更新
        with open(plan_file, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)

        total_files = sum(g.get("file_count", len(g["files"])) for g in assignee_groups)

        print(f"✅ 负责人 '{assignee_name}' 的所有任务已标记完成")
        print(f"   完成组数: {completed_count}/{len(assignee_groups)}")
        print(f"   涉及文件: {total_files} 个")

        # 显示整体进度
        all_completed_count = sum(1 for g in plan["groups"] if g.get("status") == "completed")
        total_count = len(plan["groups"])
        print(f"📊 整体进度: {all_completed_count}/{total_count} 组已完成 ({all_completed_count/total_count*100:.1f}%)")

        return True

    def auto_check_remote_status(self):
        """自动检查远程分支状态，推断哪些组可能已完成"""
        plan_file = self.work_dir / "merge_plan.json"
        if not plan_file.exists():
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return False

        with open(plan_file, 'r', encoding='utf-8') as f:
            plan = json.load(f)

        print("🔍 正在检查远程分支状态...")

        # 更新远程分支信息
        self.run_git_command("git fetch --all")

        # 获取所有远程分支
        remote_branches_output = self.run_git_command("git branch -r")
        if not remote_branches_output:
            print("⚠️ 无法获取远程分支信息")
            return False

        remote_branches = set()
        for line in remote_branches_output.split('\n'):
            branch = line.strip()
            if branch and not branch.startswith('origin/HEAD'):
                remote_branches.add(branch.replace('origin/', ''))

        print(f"📡 发现 {len(remote_branches)} 个远程分支")

        # 检查每个组对应的远程分支
        potentially_completed = []
        confirmed_completed = []

        for group in plan["groups"]:
            if group.get("status") == "completed":
                continue  # 已经标记完成的跳过

            assignee = group.get("assignee")
            if not assignee:
                continue  # 未分配的跳过

            group_name = group["name"]

            # 生成可能的分支名
            possible_branch_names = [
                f"feat/merge-{group_name.replace('/', '-')}-{assignee.replace(' ', '-')}",
                f"feat/merge-batch-{assignee.replace(' ', '-')}"
            ]

            # 检查是否有对应的远程分支
            for branch_name in possible_branch_names:
                if any(branch_name in rb for rb in remote_branches):
                    potentially_completed.append({
                        "group": group,
                        "branch": branch_name,
                        "assignee": assignee
                    })
                    break

        if potentially_completed:
            print(f"\n🎯 发现 {len(potentially_completed)} 个可能已完成的组:")
            print("-" * 80)

            for item in potentially_completed:
                group = item["group"]
                branch = item["branch"]
                assignee = item["assignee"]
                file_count = group.get("file_count", len(group["files"]))

                print(f"组: {group['name']:<25} 负责人: {assignee:<15} 分支: {branch}")
                print(f"   文件数: {file_count}")

                # 询问是否标记为完成
                confirm = input(f"   是否标记为完成? (y/N): ").strip().lower()
                if confirm == 'y':
                    group["status"] = "completed"
                    group["completed_at"] = datetime.now().isoformat()
                    group["auto_detected"] = True
                    confirmed_completed.append(group['name'])
                    print(f"   ✅ 已标记完成")
                else:
                    print(f"   ⏭️ 跳过")
                print()

        # 保存更新
        if confirmed_completed:
            with open(plan_file, 'w', encoding='utf-8') as f:
                json.dump(plan, f, indent=2, ensure_ascii=False)

            print(f"📊 本次自动检查结果:")
            print(f"   自动标记完成: {len(confirmed_completed)} 个组")
            for group_name in confirmed_completed:
                print(f"   - {group_name}")

        # 显示整体进度
        all_completed_count = sum(1 for g in plan["groups"] if g.get("status") == "completed")
        total_count = len(plan["groups"])
        print(f"\n📈 整体进度: {all_completed_count}/{total_count} 组已完成 ({all_completed_count/total_count*100:.1f}%)")

        if potentially_completed and not confirmed_completed:
            print("\n💡 提示: 如果这些分支确实对应已完成的合并，建议手动标记完成")

        return True

def main():
    if len(sys.argv) < 3:
        print("使用方法: python git_merge_tool.py <source_branch> <target_branch> [max_files_per_group]")
        print("示例: python git_merge_tool.py feature/big-feature main 5")
        sys.exit(1)

    source_branch = sys.argv[1]
    target_branch = sys.argv[2]
    max_files_per_group = int(sys.argv[3]) if len(sys.argv) > 3 else 5

    tool = GitMergeTool(source_branch, target_branch, max_files_per_group=max_files_per_group)

    print("🚀 Git大分叉智能分步合并工具 (增强版)")
    print(f"源分支: {source_branch}")
    print(f"目标分支: {target_branch}")
    print(f"每组最大文件数: {max_files_per_group}")
    print()

    while True:
        print("\n📋 可用操作:")
        print("1. 分析分支分叉")
        print("2. 创建智能合并计划")
        print("3. 智能自动分配任务 (含活跃度过滤+备选方案)")
        print("4. 手动分配任务")
        print("5. 查看贡献者智能分析")
        print("6. 合并指定组")
        print("7. 搜索负责人任务")
        print("8. 合并指定负责人的所有任务")
        print("9. 检查状态")
        print("10. 查看分组详细信息")
        print("11. 查看分配原因分析")
        print("12. 完成状态管理 (标记完成/检查远程状态)")
        print("13. 完成最终合并")
        print("0. 退出")

        choice = input("\n请选择操作 (0-13): ").strip()

        if choice == '0':
            break
        elif choice == '1':
            tool.analyze_divergence()
        elif choice == '2':
            tool.create_merge_plan()
        elif choice == '3':
            print("🤖 智能自动分配模式 (活跃度过滤+备选方案)")
            exclude_input = input("请输入要排除的作者列表 (用逗号分隔，回车跳过): ").strip()
            exclude_authors = [name.strip() for name in exclude_input.split(',')] if exclude_input else []

            max_tasks_input = input("每人最大任务数 (默认3): ").strip()
            max_tasks = int(max_tasks_input) if max_tasks_input.isdigit() else 3

            fallback_input = input("启用备选分配方案? (Y/n): ").strip().lower()
            include_fallback = fallback_input != 'n'

            tool.auto_assign_tasks(exclude_authors, max_tasks, include_fallback)
        elif choice == '4':
            assignments = {}
            print("请输入任务分配 (格式: 组名=负责人，输入空行结束):")
            while True:
                line = input().strip()
                if not line:
                    break
                if '=' in line:
                    group, assignee = line.split('=', 1)
                    assignments[group.strip()] = assignee.strip()
            tool.assign_tasks(assignments)
        elif choice == '5':
            tool.show_contributor_analysis()
        elif choice == '6':
            group_name = input("请输入要合并的组名: ").strip()
            tool.merge_group(group_name)
        elif choice == '7':
            assignee_name = input("请输入负责人姓名: ").strip()
            tool.search_assignee_tasks(assignee_name)
        elif choice == '8':
            assignee_name = input("请输入要合并任务的负责人姓名: ").strip()
            tool.merge_assignee_tasks(assignee_name)
        elif choice == '9':
            tool.check_status()
        elif choice == '10':
            print("📋 查看分组详细信息:")
            print("a. 查看指定组详情")
            print("b. 交互式选择查看")
            print("c. 返回主菜单")

            sub_choice = input("请选择操作 (a-c): ").strip().lower()
            if sub_choice == 'a':
                group_name = input("请输入组名: ").strip()
                tool.view_group_details(group_name)
            elif sub_choice == 'b':
                tool.view_group_details()
            elif sub_choice == 'c':
                continue
        elif choice == '11':
            tool.show_assignment_reasons()
        elif choice == '12':
            print("📋 完成状态管理:")
            print("a. 标记组完成")
            print("b. 标记负责人所有任务完成")
            print("c. 自动检查远程分支状态")
            print("d. 返回主菜单")

            sub_choice = input("请选择操作 (a-d): ").strip().lower()
            if sub_choice == 'a':
                group_name = input("请输入已完成的组名: ").strip()
                tool.mark_group_completed(group_name)
            elif sub_choice == 'b':
                assignee_name = input("请输入负责人姓名: ").strip()
                tool.mark_assignee_completed(assignee_name)
            elif sub_choice == 'c':
                tool.auto_check_remote_status()
            elif sub_choice == 'd':
                continue
        elif choice == '13':
            tool.finalize_merge()

if __name__ == "__main__":
    main()
