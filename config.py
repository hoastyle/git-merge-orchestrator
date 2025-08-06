"""
Git Merge Orchestrator - 配置管理
负责管理全局配置常量和默认设置
"""

# 默认配置
DEFAULT_MAX_FILES_PER_GROUP = 5
DEFAULT_MAX_TASKS_PER_PERSON = 200
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
    "settings/",
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
