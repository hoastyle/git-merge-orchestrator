"""
Git Merge Orchestrator - 增强贡献者分析模块（v2.3）
负责使用多维度权重算法分析文件和目录的贡献者
支持行数权重分析、时间衰减权重、一致性评分等高级功能
"""

from datetime import datetime, timedelta
from config import (
    ENHANCED_CONTRIBUTOR_ANALYSIS,
    ALGORITHM_CONFIGS,
    DEFAULT_ANALYSIS_MONTHS,
    DEFAULT_ACTIVE_MONTHS,
)


class EnhancedContributorAnalyzer:
    """增强贡献者分析器（支持多维度权重）"""

    def __init__(self, git_ops):
        self.git_ops = git_ops
        self._active_contributors_cache = None
        self._all_contributors_cache = None
        self.config = ENHANCED_CONTRIBUTOR_ANALYSIS

        # 检查功能是否启用
        self.enabled = self.config.get("enabled", True)

        if not self.enabled:
            print("⚠️  增强贡献者分析已禁用，将使用基础分析")

    def is_enabled(self):
        """检查增强分析是否启用"""
        return self.enabled

    def get_algorithm_config(self):
        """获取当前算法配置"""
        algorithm_type = self.config.get("assignment_algorithm", "comprehensive")
        return ALGORITHM_CONFIGS.get(algorithm_type, ALGORITHM_CONFIGS["comprehensive"])

    def analyze_file_contributors(
        self, filepath, months=None, enable_line_analysis=True
    ):
        """
        增强文件贡献者分析
        
        Args:
            filepath: 文件路径
            months: 分析时间范围（默认使用配置值）
            enable_line_analysis: 是否启用行数权重分析
            
        Returns:
            dict: 增强的贡献者信息
        """
        if not self.enabled:
            # 回退到基础分析
            return self._fallback_to_basic_analysis(filepath, months)

        months = months or self.config.get("analysis_months", DEFAULT_ANALYSIS_MONTHS)

        try:
            # 使用增强Git日志解析
            contributors = self.git_ops.get_enhanced_file_contributors(
                filepath, months, enable_line_analysis
            )

            # 应用活跃度过滤
            active_contributors = self._filter_active_contributors(contributors)

            # 应用最低分数阈值过滤
            filtered_contributors = self._apply_score_threshold(active_contributors)

            # 标准化分数
            normalized_contributors = self._normalize_scores(filtered_contributors)

            return normalized_contributors

        except Exception as e:
            print(f"增强分析失败: {e}")
            if self.config.get("fallback_to_simple", True):
                print("回退到基础分析...")
                return self._fallback_to_basic_analysis(filepath, months)
            return {}

    def analyze_contributors_batch(
        self, file_paths, months=None, enable_line_analysis=True
    ):
        """
        批量增强贡献者分析
        
        Args:
            file_paths: 文件路径列表
            months: 分析时间范围
            enable_line_analysis: 是否启用行数分析
            
        Returns:
            dict: {文件路径: 增强贡献者信息}
        """
        if not self.enabled:
            return self._fallback_to_basic_batch_analysis(file_paths, months)

        months = months or self.config.get("analysis_months", DEFAULT_ANALYSIS_MONTHS)

        try:
            from datetime import datetime
            
            # 阶段1: 使用增强批量Git日志解析
            git_parsing_start = datetime.now()
            batch_contributors = self.git_ops.get_enhanced_contributors_batch(
                file_paths, months, enable_line_analysis
            )
            git_parsing_time = (datetime.now() - git_parsing_start).total_seconds()
            print(f"⚡ Git日志解析完成: {git_parsing_time:.2f}s ({len(batch_contributors)} 个文件)")

            # 阶段2: 对每个文件的结果进行后处理
            post_processing_start = datetime.now()
            processed_results = {}
            file_count = len(batch_contributors)
            
            print(f"🧪 开始后处理: {file_count} 个文件...")
            
            # 优化: 一次性获取活跃贡献者列表（避免N+1查询问题）
            active_contributors_start = datetime.now()
            active_months = self.config.get("active_months", DEFAULT_ACTIVE_MONTHS)
            active_contributors_set = set(self.git_ops.get_active_contributors(active_months))
            active_contributors_time = (datetime.now() - active_contributors_start).total_seconds()
            print(f"⚡ 获取活跃贡献者列表: {active_contributors_time:.2f}s ({len(active_contributors_set)} 人)")
            
            # 详细的后处理统计
            filtering_time = active_contributors_time  # 包含一次性获取时间
            scoring_time = 0
            normalization_time = 0
            
            for i, (file_path, contributors) in enumerate(batch_contributors.items(), 1):
                # 应用活跃度过滤 - 使用预获取的活跃贡献者列表
                filter_start = datetime.now()
                active_contributors = self._filter_active_contributors_optimized(contributors, active_contributors_set)
                filtering_time += (datetime.now() - filter_start).total_seconds()

                # 应用分数阈值过滤
                score_start = datetime.now()
                filtered_contributors = self._apply_score_threshold(active_contributors)
                scoring_time += (datetime.now() - score_start).total_seconds()

                # 标准化分数
                norm_start = datetime.now()
                normalized_contributors = self._normalize_scores(filtered_contributors)
                normalization_time += (datetime.now() - norm_start).total_seconds()

                processed_results[file_path] = normalized_contributors
                
                # 进度显示（每10%显示一次）
                if i % max(1, file_count // 10) == 0 or i == file_count:
                    progress = (i / file_count) * 100
                    elapsed = (datetime.now() - post_processing_start).total_seconds()
                    print(f"🔄 后处理进度: {i}/{file_count} ({progress:.1f}%) - 用时 {elapsed:.1f}s")
            
            post_processing_time = (datetime.now() - post_processing_start).total_seconds()
            print(f"✅ 后处理完成: {post_processing_time:.2f}s")
            print(f"  • 活跃度过滤: {filtering_time:.2f}s")
            print(f"  • 分数过滤: {scoring_time:.2f}s")  
            print(f"  • 分数标准化: {normalization_time:.2f}s")
            
            # 保存详细性能记录
            self._save_analysis_performance_log({
                'git_parsing_time': git_parsing_time,
                'post_processing_time': post_processing_time,
                'filtering_time': filtering_time,
                'scoring_time': scoring_time,
                'normalization_time': normalization_time,
                'files_processed': file_count,
                'total_analysis_time': git_parsing_time + post_processing_time
            })

            return processed_results

        except Exception as e:
            print(f"批量增强分析失败: {e}")
            if self.config.get("fallback_to_simple", True):
                print("回退到基础批量分析...")
                return self._fallback_to_basic_batch_analysis(file_paths, months)
            return {}

    def get_contributor_ranking(self, contributors_dict):
        """
        获取贡献者排名
        
        Args:
            contributors_dict: 贡献者信息字典
            
        Returns:
            list: 排序后的贡献者列表 [(作者, 信息), ...]
        """
        if not contributors_dict:
            return []

        # 按增强分数排序
        sorted_contributors = sorted(
            contributors_dict.items(),
            key=lambda x: x[1].get("enhanced_score", x[1].get("score", 0)),
            reverse=True,
        )

        return sorted_contributors

    def get_best_assignee(self, contributors_dict, exclude_inactive=True):
        """
        获取最佳任务分配对象
        
        Args:
            contributors_dict: 贡献者信息字典
            exclude_inactive: 是否排除不活跃的贡献者
            
        Returns:
            tuple: (最佳作者, 作者信息, 推荐理由)
        """
        if not contributors_dict:
            return None, {}, "无贡献者信息"

        # 获取活跃贡献者
        if exclude_inactive:
            active_months = self.config.get("active_months", DEFAULT_ACTIVE_MONTHS)
            active_contributors = self.git_ops.get_active_contributors(active_months)

            # 过滤出活跃的贡献者
            filtered_contributors = {
                author: info
                for author, info in contributors_dict.items()
                if author in active_contributors
            }

            if not filtered_contributors:
                # 如果没有活跃贡献者，使用所有贡献者但添加警告
                filtered_contributors = contributors_dict
                warning_suffix = "（注意：该文件近期无活跃贡献者）"
            else:
                warning_suffix = ""
        else:
            filtered_contributors = contributors_dict
            warning_suffix = ""

        # 获取最高分贡献者
        ranking = self.get_contributor_ranking(filtered_contributors)
        if not ranking:
            return None, {}, "无可用贡献者"

        best_author, best_info = ranking[0]

        # 生成推荐理由
        reason = (
            self._generate_assignment_reason(best_author, best_info) + warning_suffix
        )

        return best_author, best_info, reason

    def _filter_active_contributors(self, contributors_dict):
        """过滤活跃贡献者"""
        if not contributors_dict:
            return {}

        active_months = self.config.get("active_months", DEFAULT_ACTIVE_MONTHS)
        active_contributors = self.git_ops.get_active_contributors(active_months)

        # 如果没有活跃贡献者，返回原始数据
        if not active_contributors:
            return contributors_dict

        # 过滤活跃贡献者
        filtered = {}
        for author, info in contributors_dict.items():
            if author in active_contributors:
                info["is_active"] = True
                filtered[author] = info
            else:
                # 标记为不活跃但保留数据
                info["is_active"] = False
                filtered[author] = info

        return filtered

    def _apply_score_threshold(self, contributors_dict):
        """应用最低分数阈值过滤"""
        if not contributors_dict:
            return {}

        min_threshold = self.config.get("minimum_score_threshold", 0.1)

        filtered = {}
        for author, info in contributors_dict.items():
            score = info.get("enhanced_score", info.get("score", 0))
            if score >= min_threshold:
                filtered[author] = info

        return filtered if filtered else contributors_dict  # 如果全部被过滤，返回原始数据

    def _apply_score_threshold_relaxed(self, contributors_dict):
        """应用更宽松的最低分数阈值过滤（用于批量决策）"""
        if not contributors_dict:
            return {}

        # 使用更宽松的阈值，确保有足够的候选人
        min_threshold = self.config.get("minimum_score_threshold", 0.1) * 0.5  # 降低50%
        
        # 如果所有贡献者的分数都很低，进一步放宽
        all_scores = [info.get("enhanced_score", info.get("score", 0)) for info in contributors_dict.values()]
        if all_scores and max(all_scores) < min_threshold:
            min_threshold = min(all_scores) * 0.8  # 使用最低分数的80%
            print(f"🔧 自动调整分数阈值为 {min_threshold:.3f} (原阈值过严)")

        filtered = {}
        for author, info in contributors_dict.items():
            score = info.get("enhanced_score", info.get("score", 0))
            if score >= min_threshold:
                filtered[author] = info

        return filtered if filtered else contributors_dict  # 如果全部被过滤，返回原始数据

    def _normalize_scores(self, contributors_dict):
        """标准化分数"""
        if not contributors_dict:
            return {}

        normalization_method = self.config.get("score_normalization", "min_max")

        # 提取所有分数
        scores = []
        for info in contributors_dict.values():
            score = info.get("enhanced_score", info.get("score", 0))
            scores.append(score)

        if not scores:
            return contributors_dict

        # 应用标准化
        if normalization_method == "min_max":
            min_score = min(scores)
            max_score = max(scores)
            score_range = max_score - min_score

            if score_range == 0:
                return contributors_dict  # 所有分数相同，无需标准化

            for author, info in contributors_dict.items():
                score = info.get("enhanced_score", info.get("score", 0))
                normalized_score = (score - min_score) / score_range
                info["normalized_score"] = normalized_score

        elif normalization_method == "z_score":
            import statistics

            try:
                mean_score = statistics.mean(scores)
                std_score = statistics.stdev(scores) if len(scores) > 1 else 1

                for author, info in contributors_dict.items():
                    score = info.get("enhanced_score", info.get("score", 0))
                    z_score = (score - mean_score) / std_score if std_score != 0 else 0
                    info["normalized_score"] = z_score
            except statistics.StatisticsError:
                # 回退到原始分数
                for author, info in contributors_dict.items():
                    info["normalized_score"] = info.get(
                        "enhanced_score", info.get("score", 0)
                    )

        elif normalization_method == "percentile":
            import statistics

            sorted_scores = sorted(scores)

            for author, info in contributors_dict.items():
                score = info.get("enhanced_score", info.get("score", 0))
                # 计算百分位数
                percentile = (sorted_scores.index(score) + 1) / len(sorted_scores)
                info["normalized_score"] = percentile

        return contributors_dict

    def _generate_assignment_reason(self, author, author_info):
        """生成分配推荐理由"""
        reasons = []

        # 提取关键信息
        recent_commits = author_info.get("recent_commits", 0)
        total_commits = author_info.get("total_commits", 0)
        total_changes = author_info.get("total_changes", 0)
        enhanced_score = author_info.get("enhanced_score", 0)

        # 分数详细信息
        score_breakdown = author_info.get("score_breakdown", {})

        # 基于提交数量的理由
        if recent_commits > 0:
            if recent_commits >= 5:
                reasons.append("高频近期贡献者")
            elif recent_commits >= 2:
                reasons.append("活跃贡献者")
            else:
                reasons.append("近期有贡献")

        # 基于行数变更的理由
        if total_changes > 0:
            if total_changes >= 1000:
                reasons.append("大规模代码变更经验")
            elif total_changes >= 100:
                reasons.append("中等规模变更经验")
            else:
                reasons.append("有代码变更经验")

        # 基于算法类型的特殊说明
        algorithm = self.config.get("assignment_algorithm", "comprehensive")
        if algorithm == "comprehensive":
            consistency_score = score_breakdown.get("consistency_score", 0)
            if consistency_score > 0.5:
                reasons.append("持续贡献模式")

        # 基于增强评分的总体评价
        if enhanced_score >= 5.0:
            reasons.append("综合评分优秀")
        elif enhanced_score >= 2.0:
            reasons.append("综合评分良好")

        # 生成最终理由
        if reasons:
            primary_reason = reasons[0]
            if len(reasons) > 1:
                return f"{primary_reason}，{', '.join(reasons[1:])}"
            return primary_reason

        return "基于贡献历史推荐"

    def _fallback_to_basic_analysis(self, filepath, months):
        """回退到基础分析"""
        from .contributor_analyzer import ContributorAnalyzer

        basic_analyzer = ContributorAnalyzer(self.git_ops)
        return basic_analyzer.analyze_file_contributors(filepath)

    def _fallback_to_basic_batch_analysis(self, file_paths, months):
        """回退到基础批量分析"""
        result = {}
        for file_path in file_paths:
            result[file_path] = self._fallback_to_basic_analysis(file_path, months)
        return result

    def compute_final_decision_batch(self, files_contributors_dict, active_contributors_set=None):
        """
        批量预计算所有文件的最优分配决策
        
        Args:
            files_contributors_dict: {文件路径: 贡献者信息} 字典
            active_contributors_set: 活跃贡献者集合（如果未提供将自动获取）
            
        Returns:
            dict: {文件路径: {'primary': (作者, 信息), 'alternatives': [...], 'reason': 理由}}
        """
        from datetime import datetime
        
        if not files_contributors_dict:
            return {}
            
        start_time = datetime.now()
        
        # 获取活跃贡献者集合（如果未提供）
        if active_contributors_set is None:
            active_months = self.config.get("active_months", DEFAULT_ACTIVE_MONTHS)
            active_contributors_set = set(self.git_ops.get_active_contributors(active_months))
        
        print(f"🎯 开始批量决策预计算: {len(files_contributors_dict)} 个文件...")
        
        decisions = {}
        processed_count = 0
        
        for file_path, contributors in files_contributors_dict.items():
            # 应用活跃度过滤（使用优化版本）
            filtered_contributors = self._filter_active_contributors_optimized(
                contributors, active_contributors_set
            )
            
            # 如果活跃度过滤后没有候选人，使用原始数据
            if not filtered_contributors:
                print(f"⚠️ 文件 {file_path} 无活跃贡献者，使用所有贡献者")
                filtered_contributors = contributors
            
            # 应用分数阈值过滤（使用更宽松的阈值）
            threshold_filtered = self._apply_score_threshold_relaxed(filtered_contributors)
            
            # 如果阈值过滤后没有候选人，使用过滤前的数据
            if not threshold_filtered:
                threshold_filtered = filtered_contributors
            
            # 标准化分数
            normalized_contributors = self._normalize_scores(threshold_filtered)
            
            # 获取排序后的候选人列表
            ranking = self.get_contributor_ranking(normalized_contributors)
            
            if ranking:
                primary_author, primary_info = ranking[0]
                alternatives = ranking[1:5]  # 保留前5个备选
                reason = self._generate_assignment_reason(primary_author, primary_info)
                
                decisions[file_path] = {
                    'primary': (primary_author, primary_info),
                    'alternatives': alternatives,
                    'reason': reason,
                    'all_candidates': len(ranking),
                    'active_candidates': len([r for r in ranking if r[1].get('is_active', True)])
                }
            else:
                decisions[file_path] = {
                    'primary': None,
                    'alternatives': [],
                    'reason': '无可用贡献者',
                    'all_candidates': 0,
                    'active_candidates': 0
                }
            
            processed_count += 1
            
            # 进度显示（每10%显示一次）
            if processed_count % max(1, len(files_contributors_dict) // 10) == 0:
                progress = (processed_count / len(files_contributors_dict)) * 100
                elapsed = (datetime.now() - start_time).total_seconds()
                print(f"🔄 决策计算进度: {processed_count}/{len(files_contributors_dict)} ({progress:.1f}%) - 用时 {elapsed:.1f}s")
        
        total_time = (datetime.now() - start_time).total_seconds()
        valid_decisions = len([d for d in decisions.values() if d['primary'] is not None])
        
        print(f"✅ 批量决策计算完成: {total_time:.2f}s")
        print(f"📊 决策统计: {valid_decisions}/{len(decisions)} 个文件有可分配对象 ({valid_decisions/len(decisions)*100:.1f}%)")
        
        # 保存决策计算性能日志
        self._save_decision_performance_log({
            'decision_calculation_time': total_time,
            'files_processed': len(files_contributors_dict),
            'valid_decisions': valid_decisions,
            'avg_decision_time_ms': (total_time / len(files_contributors_dict)) * 1000,
            'active_contributors_count': len(active_contributors_set)
        })
        
        return decisions

    def get_analysis_statistics(self, contributors_dict):
        """获取分析统计信息"""
        if not contributors_dict:
            return {}

        stats = {
            "total_contributors": len(contributors_dict),
            "active_contributors": 0,
            "avg_score": 0,
            "max_score": 0,
            "total_commits": 0,
            "total_changes": 0,
            "algorithm_used": self.config.get("assignment_algorithm", "comprehensive"),
        }

        scores = []
        for author, info in contributors_dict.items():
            if info.get("is_active", True):
                stats["active_contributors"] += 1

            score = info.get("enhanced_score", info.get("score", 0))
            scores.append(score)
            stats["max_score"] = max(stats["max_score"], score)
            stats["total_commits"] += info.get("total_commits", 0)
            stats["total_changes"] += info.get("total_changes", 0)

        if scores:
            stats["avg_score"] = sum(scores) / len(scores)

        return stats

    def export_detailed_analysis(self, filepath, contributors_dict, output_file=None):
        """导出详细分析结果"""
        if not self.config.get("export_analysis_results", False):
            return False

        import json
        from pathlib import Path

        # 准备导出数据
        export_data = {
            "file_path": filepath,
            "analysis_timestamp": datetime.now().isoformat(),
            "algorithm_config": self.get_algorithm_config(),
            "contributors": {},
        }

        # 处理贡献者数据
        for author, info in contributors_dict.items():
            export_data["contributors"][author] = {
                "basic_info": {
                    "total_commits": info.get("total_commits", 0),
                    "recent_commits": info.get("recent_commits", 0),
                    "total_changes": info.get("total_changes", 0),
                    "is_active": info.get("is_active", True),
                },
                "scoring": info.get("score_breakdown", {}),
                "final_scores": {
                    "enhanced_score": info.get("enhanced_score", 0),
                    "normalized_score": info.get("normalized_score", 0),
                },
            }

        # 确定输出文件名
        if not output_file:
            safe_filename = filepath.replace("/", "_").replace(" ", "_")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = (
                f".merge_work/analysis_export_{safe_filename}_{timestamp}.json"
            )

        # 创建输出目录
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            print(f"📊 详细分析结果已导出: {output_file}")
            return True

        except Exception as e:
            print(f"导出分析结果失败: {e}")
            return False

    def debug_analysis(self, filepath, contributors_dict):
        """调试分析过程（仅在调试模式下启用）"""
        if not self.config.get("debug_mode", False):
            return

        print(f"\n🔍 调试分析: {filepath}")
        print(f"算法类型: {self.config.get('assignment_algorithm', 'comprehensive')}")

        for author, info in contributors_dict.items():
            print(f"\n👤 {author}:")
            print(
                f"  基础信息: commits={info.get('total_commits', 0)}, changes={info.get('total_changes', 0)}"
            )

            if "score_breakdown" in info:
                breakdown = info["score_breakdown"]
                print(f"  评分详情:")
                for key, value in breakdown.items():
                    print(f"    {key}: {value:.3f}")

            enhanced_score = info.get("enhanced_score", 0)
            normalized_score = info.get("normalized_score", 0)
            print(
                f"  最终分数: enhanced={enhanced_score:.3f}, normalized={normalized_score:.3f}"
            )
            
    def _save_analysis_performance_log(self, perf_data):
        """保存分析性能详细日志"""
        try:
            import json
            from pathlib import Path
            from datetime import datetime
            
            # 设置日志文件路径
            if hasattr(self.git_ops, 'repo_path'):
                repo_path = Path(self.git_ops.repo_path)
            else:
                repo_path = Path(".")
                
            log_file = repo_path / ".merge_work" / "enhanced_analysis_performance.json"
            log_file.parent.mkdir(exist_ok=True)
            
            # 构建日志条目
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'component': 'EnhancedContributorAnalyzer',
                'version': '2.3',
                'detailed_breakdown': perf_data,
                'performance_insights': self._generate_analysis_insights(perf_data)
            }
            
            # 加载现有日志
            logs = []
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                except:
                    logs = []
            
            # 添加新日志
            logs.append(log_entry)
            
            # 保持最近30条记录
            if len(logs) > 30:
                logs = logs[-30:]
                
            # 写入文件
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ 保存分析性能日志失败: {e}")
    
    def _generate_analysis_insights(self, perf_data):
        """生成分析性能洞察"""
        insights = []
        
        total_time = perf_data.get('total_analysis_time', 0)
        git_time = perf_data.get('git_parsing_time', 0)
        post_time = perf_data.get('post_processing_time', 0)
        files_count = perf_data.get('files_processed', 0)
        
        # 分析时间分布
        if post_time > git_time:
            insights.append(f"后处理耗时较多 ({post_time:.1f}s vs {git_time:.1f}s Git解析)")
        
        # 检查单个细分阶段  
        filter_time = perf_data.get('filtering_time', 0)
        scoring_time = perf_data.get('scoring_time', 0)
        norm_time = perf_data.get('normalization_time', 0)
        
        if filter_time > post_time * 0.4:
            insights.append(f"活跃度过滤耗时较多 ({filter_time:.2f}s)")
        if scoring_time > post_time * 0.4:
            insights.append(f"分数过滤耗时较多 ({scoring_time:.2f}s)")
        if norm_time > post_time * 0.4:
            insights.append(f"分数标准化耗时较多 ({norm_time:.2f}s)")
            
        # 性能建议
        if total_time > 30:
            insights.append(f"分析总耗时较长 ({total_time:.1f}s), 可考虑缓存优化")
            
        avg_time_per_file = total_time / files_count * 1000 if files_count > 0 else 0
        if avg_time_per_file > 25:  # 25ms per file
            insights.append(f"平均文件分析时间较长 ({avg_time_per_file:.1f}ms)")
            
        if not insights:
            insights.append("分析性能表现良好")
            
        return insights
        
    def _filter_active_contributors_optimized(self, contributors_dict, active_contributors_set):
        """优化版活跃度过滤 - 使用预获取的活跃贡献者集合"""
        if not contributors_dict:
            return {}

        # 如果没有活跃贡献者，返回原始数据
        if not active_contributors_set:
            return contributors_dict

        # 使用预获取的集合进行快速过滤
        filtered = {}
        inactive_count = 0
        
        for author, info in contributors_dict.items():
            if author in active_contributors_set:
                info["is_active"] = True
                filtered[author] = info
            else:
                # 标记为不活跃
                info["is_active"] = False
                inactive_count += 1
                # 在批量决策中，如果活跃贡献者太少，包含不活跃的贡献者
                include_inactive = self.config.get("include_inactive", False)
                if include_inactive or len(filtered) < 2:  # 确保至少有一些候选人
                    filtered[author] = info

        # 如果过滤后候选人太少，包含所有贡献者
        if len(filtered) < max(1, len(contributors_dict) * 0.3):  # 至少保留30%的候选人
            print(f"🔧 活跃度过滤过严，保留所有 {len(contributors_dict)} 位贡献者 (活跃:{len(filtered)}, 不活跃:{inactive_count})")
            return contributors_dict

        return filtered
        
    def _save_decision_performance_log(self, perf_data):
        """保存决策计算性能详细日志"""
        try:
            import json
            from pathlib import Path
            from datetime import datetime
            
            # 设置日志文件路径
            if hasattr(self.git_ops, 'repo_path'):
                repo_path = Path(self.git_ops.repo_path)
            else:
                repo_path = Path(".")
                
            log_file = repo_path / ".merge_work" / "decision_performance.json"
            log_file.parent.mkdir(exist_ok=True)
            
            # 构建日志条目
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'component': 'EnhancedContributorAnalyzer.compute_final_decision_batch',
                'version': '2.3',
                'performance_data': perf_data,
                'efficiency_metrics': {
                    'decisions_per_second': perf_data.get('files_processed', 0) / max(perf_data.get('decision_calculation_time', 1), 0.001),
                    'avg_decision_time_ms': perf_data.get('avg_decision_time_ms', 0),
                    'success_rate': perf_data.get('valid_decisions', 0) / max(perf_data.get('files_processed', 1), 1) * 100
                }
            }
            
            # 加载现有日志
            logs = []
            if log_file.exists():
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                except:
                    logs = []
            
            # 添加新日志
            logs.append(log_entry)
            
            # 保持最近20条记录
            if len(logs) > 20:
                logs = logs[-20:]
                
            # 写入文件
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ 保存决策性能日志失败: {e}")
