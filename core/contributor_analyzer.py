"""
Git Merge Orchestrator - 贡献者分析模块
负责分析文件和目录的贡献者，评估活跃度和推荐分配
"""

from datetime import datetime, timedelta
from config import SCORING_WEIGHTS, DEFAULT_ANALYSIS_MONTHS, DEFAULT_ACTIVE_MONTHS


class ContributorAnalyzer:
    """贡献者分析器"""

    def __init__(self, git_ops):
        self.git_ops = git_ops
        self._active_contributors_cache = None
        self._all_contributors_cache = None

    def get_active_contributors(self, months=DEFAULT_ACTIVE_MONTHS):
        """获取近N个月有提交的活跃贡献者列表"""
        if self._active_contributors_cache is not None:
            return self._active_contributors_cache

        print(f"🔍 正在分析近{months}个月的活跃贡献者...")
        active_contributors = self.git_ops.get_active_contributors(months)

        self._active_contributors_cache = active_contributors
        print(f"📊 发现 {len(active_contributors)} 位近{months}个月活跃的贡献者")
        return active_contributors

    def get_all_contributors(self):
        """获取所有历史贡献者"""
        if self._all_contributors_cache is not None:
            return self._all_contributors_cache

        all_contributors = self.git_ops.get_all_contributors_global()
        self._all_contributors_cache = all_contributors
        return all_contributors

    def analyze_file_contributors(self, filepath, include_recent=True):
        """分析文件的主要贡献者（重点关注一年内的贡献）"""
        try:
            contributors = {}

            # 获取一年内的贡献统计 (重点)
            if include_recent:
                one_year_ago = (datetime.now() - timedelta(days=DEFAULT_ANALYSIS_MONTHS * 30)).strftime('%Y-%m-%d')
                recent_contributors = self.git_ops.get_contributors_since(filepath, one_year_ago)

                for author, count in recent_contributors.items():
                    contributors[author] = {
                        'total_commits': count,
                        'recent_commits': count,
                        'score': count * SCORING_WEIGHTS['recent_commits']
                    }

            # 获取总体贡献统计 (补充)
            all_contributors = self.git_ops.get_all_contributors(filepath)

            for author, count in all_contributors.items():
                if author in contributors:
                    contributors[author]['total_commits'] = count
                    contributors[author]['score'] = (contributors[author]['recent_commits'] *
                                                   SCORING_WEIGHTS['recent_commits'] +
                                                   count * SCORING_WEIGHTS['total_commits'])
                else:
                    contributors[author] = {
                        'total_commits': count,
                        'recent_commits': 0,
                        'score': count * SCORING_WEIGHTS['total_commits']
                    }

            return contributors
        except Exception as e:
            print(f"分析文件 {filepath} 时出错: {e}")
            return {}

    def analyze_directory_contributors(self, directory_path, include_recent=True):
        """分析目录级别的主要贡献者"""
        return self.git_ops.get_directory_contributors(directory_path, include_recent)

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

    def get_contributor_activity_level(self, author, recent_commits, active_contributors):
        """获取贡献者活跃度等级"""
        if author not in active_contributors:
            return 'inactive'

        if recent_commits >= 15:
            return 'high'
        elif recent_commits >= 5:
            return 'medium'
        elif recent_commits >= 1:
            return 'low'
        else:
            return 'recent'

    def calculate_global_contributor_stats(self, plan):
        """计算全局贡献者统计"""
        all_contributors_global = {}

        for group in plan["groups"]:
            contributors = group.get('contributors', {})
            for author, stats in contributors.items():
                if author not in all_contributors_global:
                    all_contributors_global[author] = {
                        'total_commits': 0,
                        'recent_commits': 0,
                        'score': 0,
                        'groups_contributed': 0,
                        'groups_assigned': [],
                        'is_active': author in self.get_active_contributors()
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
                    assignee_workload[assignee] = {"groups": 0, "files": 0, "completed": 0, "fallback": 0}
                assignee_workload[assignee]["groups"] += 1
                assignee_workload[assignee]["files"] += group.get("file_count", len(group.get("files", [])))
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
            assignment_reason = group.get('assignment_reason', '未指定')
            reason_type = DisplayHelper.categorize_assignment_reason(assignment_reason)

            if reason_type not in reason_stats:
                reason_stats[reason_type] = []
            reason_stats[reason_type].append(group)

        return reason_stats