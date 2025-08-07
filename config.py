"""
Git Merge Orchestrator - 配置管理
负责管理全局配置常量和默认设置
"""

# 默认配置
DEFAULT_MAX_FILES_PER_GROUP = 5
DEFAULT_MAX_TASKS_PER_PERSON = 1000
DEFAULT_ACTIVE_MONTHS = 3
DEFAULT_ANALYSIS_MONTHS = 12

# 分支命名模板
INTEGRATION_BRANCH_TEMPLATE = "integration-{source}-{target}"
MERGE_BRANCH_TEMPLATE = "feat/merge-{group}-{assignee}"
BATCH_BRANCH_TEMPLATE = "feat/merge-batch-{assignee}-{timestamp}"

# 工作目录
WORK_DIR_NAME = ".merge_work"
PLAN_FILE_NAME = "merge_plan.json"
IGNORE_FILE_NAME = ".merge_ignore"

# 显示配置
DEFAULT_FILE_DISPLAY_LIMIT = 20  # 默认文件显示数量限制
AUTO_DISPLAY_THRESHOLD = 20  # 自动显示阈值，超过此数量将提供选择菜单
ENABLE_INTERACTIVE_DISPLAY = True  # 启用交互式显示
AUTO_EXPORT_LARGE_LISTS = True  # 超过50个文件时自动建议导出
LARGE_LIST_THRESHOLD = 50  # 大列表阈值
EXPORT_SUBDIR = "file_lists"  # 导出文件的子目录名
PAGINATED_PAGE_SIZE = 20  # 分页显示时每页的文件数量

# 默认忽略规则配置
DEFAULT_IGNORE_PATTERNS = [
    # Python相关
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "__pycache__/",
    "*.egg-info/",
    ".pytest_cache/",
    ".coverage",
    ".tox/",
    "venv/",
    "env/",
    # 版本控制
    ".git/",
    ".svn/",
    ".hg/",
    ".bzr/",
    # IDE和编辑器
    ".vscode/",
    ".idea/",
    "*.swp",
    "*.swo",
    "*~",
    ".DS_Store",
    "Thumbs.db",
    # 构建和日志文件
    "build/",
    "dist/",
    "*.log",
    "*.tmp",
    "*.temp",
    "node_modules/",
    ".npm/",
    ".yarn/",
    # 文档和备份
    "*.bak",
    "*.backup",
    "*.orig",
    "*.rej",
    # 二进制文件
    "*.exe",
    "*.dll",
    "*.so",
    "*.dylib",
    "*.a",
    "*.lib",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.bmp",
    "*.ico",
    "*.pdf",
    "*.zip",
    "*.tar",
    "*.gz",
    "*.rar",
    "*.7z",
    # customize
    # "settings/",
]

# 忽略规则类型
IGNORE_RULE_TYPES = {
    "glob": "Glob模式匹配 (支持 *, ?, [])",
    "regex": "正则表达式匹配",
    "exact": "精确匹配",
    "prefix": "前缀匹配",
    "suffix": "后缀匹配",
}

# 分组类型
GROUP_TYPES = {
    "simple_group": "简单分组 - 文件数量较少，直接分组",
    "direct_files": "直接文件 - 目录下的直接文件",
    "subdir_group": "子目录分组 - 按子目录划分",
    "alpha_group": "字母分组 - 根目录文件按首字母分组",
    "batch_group": "批量分组 - 大量文件分批处理",
    "fallback_batch": "回退批量 - 分组失败后的简单批量处理",
}

# 分配原因分类
ASSIGNMENT_REASON_TYPES = {
    "直接分配": "基于文件贡献度直接分配",
    "负载均衡": "负载均衡分配",
    "备选分配": "备选目录分配",
    "手动分配": "手动分配",
    "无贡献者": "无法确定主要贡献者",
    "自动排除": "已自动排除",
    "任务满载": "已达最大任务数",
}

# 显示格式配置
TABLE_CONFIGS = {
    "status_overview": {
        "headers": ["组名", "文件数", "负责人", "状态", "分配类型", "推荐理由"],
        "widths": [45, 8, 20, 8, 12, 35],
        "aligns": ["left", "center", "left", "center", "left", "left"],
    },
    "group_list": {
        "headers": ["序号", "组名", "类型", "文件数", "负责人", "状态"],
        "widths": [6, 45, 18, 8, 20, 8],
        "aligns": ["center", "left", "left", "center", "left", "center"],
    },
    "contributor_ranking": {
        "headers": ["排名", "姓名", "近期", "历史", "得分", "活跃状态", "参与组", "分配组", "近期活跃"],
        "widths": [6, 25, 6, 6, 8, 10, 8, 8, 10],
        "aligns": [
            "center",
            "left",
            "center",
            "center",
            "center",
            "center",
            "center",
            "center",
            "center",
        ],
    },
    "assignment_reasons": {
        "headers": ["组名", "负责人", "文件数", "分配类型", "详细原因"],
        "widths": [45, 20, 8, 18, 45],
        "aligns": ["left", "left", "center", "left", "left"],
    },
    "assignee_tasks": {
        "headers": ["组名", "文件数", "状态", "类型", "分配原因"],
        "widths": [45, 8, 8, 18, 40],
        "aligns": ["left", "center", "center", "left", "left"],
    },
    # 文件级视图表格配置
    "file_status_overview": {
        "headers": ["文件路径", "目录", "负责人", "状态", "优先级", "分配原因"],
        "widths": [50, 25, 20, 8, 8, 35],
        "aligns": ["left", "left", "left", "center", "center", "left"],
    },
    "file_list": {
        "headers": ["序号", "文件路径", "扩展名", "负责人", "状态", "完成时间"],
        "widths": [6, 55, 8, 20, 8, 20],
        "aligns": ["center", "left", "center", "left", "center", "left"],
    },
    "directory_summary": {
        "headers": ["目录", "总文件", "已分配", "已完成", "完成率", "负责人数"],
        "widths": [40, 8, 8, 8, 10, 10],
        "aligns": ["left", "center", "center", "center", "center", "center"],
    },
    "workload_distribution": {
        "headers": ["负责人", "分配文件", "已完成", "待处理", "完成率", "最新分配"],
        "widths": [25, 10, 8, 8, 10, 20],
        "aligns": ["left", "center", "center", "center", "center", "left"],
    },
    "file_contributors": {
        "headers": ["文件路径", "主要贡献者", "得分", "近期提交", "历史提交", "活跃状态"],
        "widths": [45, 20, 8, 10, 10, 10],
        "aligns": ["left", "left", "center", "center", "center", "center"],
    },
}

# 活跃度等级配置
ACTIVITY_LEVELS = {
    "high": {"threshold": 15, "icon": "🔥", "name": "高"},
    "medium": {"threshold": 5, "icon": "📈", "name": "中"},
    "low": {"threshold": 1, "icon": "📊", "name": "低"},
    "recent": {"threshold": 0, "icon": "📊", "name": "近期"},
    "inactive": {"threshold": -1, "icon": "💤", "name": "静默"},
}

# 评分权重配置
SCORING_WEIGHTS = {"recent_commits": 3, "total_commits": 1}  # 一年内提交权重  # 历史提交权重

# 性能优化配置
CACHE_EXPIRY_HOURS = 24  # 缓存过期时间（小时）
MAX_WORKER_THREADS = 4  # 最大并行线程数
BATCH_SIZE_THRESHOLD = 10  # 启用批量处理的最小文件数
ENABLE_PERFORMANCE_MONITORING = True  # 是否启用性能监控

# 增强贡献者分析配置 (v2.3新增)
ENHANCED_CONTRIBUTOR_ANALYSIS = {
    # 核心开关
    "enabled": True,
    "algorithm_version": "2.0",
    "fallback_to_simple": True,  # 失败时回退到简单算法
    # 基础评分配置
    "base_commit_score": 1.0,
    "analysis_months": 12,
    "active_months": 3,
    # 时间衰减权重配置
    "time_weight_enabled": True,
    "time_half_life_days": 180,  # 半衰期6个月，近期贡献权重更高
    "time_weight_factor": 0.4,  # 时间权重影响因子
    # 行数变更权重配置
    "line_weight_enabled": True,
    "line_weight_factor": 0.3,  # 行数权重影响因子
    "small_change_threshold": 10,  # 小变更阈值(行数)
    "medium_change_threshold": 100,  # 中变更阈值(行数)
    "large_change_threshold": 1000,  # 大变更阈值(行数)
    "max_line_weight_multiplier": 3.0,  # 最大行数权重倍数
    # 权重计算算法配置
    "line_weight_algorithm": "logarithmic",  # logarithmic, linear, sigmoid
    "magnitude_scaling": {
        "linear_factor": 0.01,  # 线性增长因子
        "log_base": 10,  # 对数底数
        "sigmoid_steepness": 0.1,  # sigmoid陡峭度
    },
    # 一致性权重配置
    "consistency_weight_enabled": True,
    "consistency_bonus_factor": 0.2,  # 持续贡献奖励因子
    "min_commits_for_consistency": 3,  # 计算一致性的最小提交数
    # 文件关联权重配置
    "file_relationship_weight_enabled": True,
    "related_file_bonus": 0.1,  # 相关文件贡献奖励
    "directory_coherence_bonus": 0.15,  # 目录连贯性奖励
    # 提交质量评估配置
    "commit_quality_weight_enabled": False,  # 暂时禁用，未来功能
    "commit_message_analysis": False,  # 提交消息分析
    "merge_commit_penalty": 0.1,  # 合并提交权重减少
    # 分配决策配置
    "assignment_algorithm": "comprehensive",  # simple, weighted, comprehensive
    "score_normalization": "min_max",  # min_max, z_score, percentile
    "minimum_score_threshold": 0.1,  # 最低分数阈值
    # 缓存和性能配置
    "cache_enabled": True,
    "cache_expiry_hours": 24,
    "parallel_processing": True,
    "max_parallel_files": 50,
    # 调试和日志配置
    "debug_mode": False,
    "detailed_breakdown": False,
    "log_scoring_details": False,
    "export_analysis_results": False,
    # 异常处理配置
    "handle_renamed_files": True,
    "ignore_merge_commits": False,
    "handle_large_refactors": True,
    "max_single_commit_lines": 10000,  # 单次提交最大行数限制
}

# 算法类型配置
ALGORITHM_CONFIGS = {
    "simple": {
        "use_time_weight": False,
        "use_line_weight": False,
        "use_consistency_weight": False,
    },
    "weighted": {
        "use_time_weight": True,
        "use_line_weight": True,
        "use_consistency_weight": False,
    },
    "comprehensive": {
        "use_time_weight": True,
        "use_line_weight": True,
        "use_consistency_weight": True,
        "use_file_relationship": True,
    },
}
