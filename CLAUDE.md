# CLAUDE.md

@/home/howie/.claude/customize/CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Main application with auto-configuration
python main.py                        # Uses saved configuration from previous runs
python main.py [source_branch] [target_branch] [options]  # First run or manual override
python main.py --update-config        # Update saved configuration
python main.py --processing-mode file_level  # Use file-level processing (default)
python main.py --processing-mode group_based # Use traditional group-based mode

# v2.3 Performance Testing
python test_performance_optimization.py      # Performance optimization validation
python demo_enhanced_analysis.py            # Enhanced analysis feature demonstration
```

### Testing
```bash
python run_tests.py                   # Interactive test menu
python run_tests.py --health         # Quick health check
python run_tests.py --full           # Complete test suite
python tests/comprehensive_test.py   # Direct comprehensive testing
python tests/config_test.py         # Configuration testing
python tests/test_deployment.py     # Deployment verification

# v2.3 Enhanced Testing
python test_enhanced_analysis.py    # Enhanced analysis testing
python test_performance_optimization.py  # Performance testing
```

## Architecture Overview

This is a Git merge orchestration tool built with a **DRY (Don't Repeat Yourself) architecture**, **dual processing modes**, and **extreme performance optimization (v2.3)**. The codebase follows a factory pattern with strategy inheritance for merge operations and features revolutionary performance improvements.

### Major v2.3 Performance Architecture

1. **Extreme Performance Optimization**:
   - **99.6% Performance Improvement**: From 280ms/file to 1.2ms/file
   - **Batch Decision Pre-computation**: Revolutionary O(n²) to O(n) complexity reduction
   - **N+1 Query Elimination**: From 1,169 Git queries to 1 query
   - **Intelligent Load Balancing**: Multi-layer fallback with 100% assignment success rate

2. **Enhanced Analysis Engine**:
   - **Multi-dimensional Scoring**: Line weight, time decay, consistency scoring
   - **Batch Processing**: `EnhancedContributorAnalyzer` with batch operations
   - **Smart Filtering**: Adaptive filtering with automatic threshold adjustment
   - **Performance Monitoring**: 4 comprehensive performance logs

3. **v2.3 Core Components**:
   - `EnhancedContributorAnalyzer`: Multi-dimensional contributor analysis with batch processing
   - `EnhancedTaskAssigner`: Intelligent task assignment with load balancing
   - `compute_final_decision_batch()`: Batch decision pre-computation engine
   - `apply_load_balanced_assignment()`: Smart assignment with multi-layer fallback

### Major v2.2 Architecture Features

1. **Dual Processing Modes**:
   - **File-Level Processing** (default): Individual file tracking, assignment, and merging
   - **Group-Based Processing** (legacy): Traditional directory-based file grouping
   - Mode selection via `--processing-mode` parameter or configuration

2. **File-Level Architecture Components**:
   - Individual file status tracking (pending, assigned, in_progress, completed)
   - Per-file contributor analysis and assignment
   - File-level merge script generation
   - Advanced file filtering and querying system
   - Load balancing across contributors

### Core Architecture Components

1. **Strategy Pattern Implementation**:
   - `BaseMergeExecutor` (abstract base class) provides common functionality for both modes
   - `LegacyMergeExecutor` and `StandardMergeExecutor` inherit from base (~60% code reuse)
   - `MergeExecutorFactory` manages runtime strategy selection
   - Dual merge strategies: Legacy (fast override) and Standard (3-way merge)
   - **Enhanced**: File-level merge methods alongside group-based methods

2. **Performance-Optimized Components** (v2.3 Revolution):
   - **Enhanced vs Optimized vs Basic** versions of key modules
   - **Enhanced versions** (v2.3): 99.6% performance improvement with batch processing
   - **Optimized versions** (v2.1): 60%+ performance improvement with 24-hour caching
   - **Basic versions**: Original implementation for compatibility
   - Cache hit rates of 90%+ for large-scale operations
   - **Revolutionary**: Batch decision pre-computation and intelligent load balancing

3. **Enhanced UI System**: 6-category menu structure with dual-mode support
   - Quick Start Wizard, Project Management, Task Assignment, Merge Execution, System Management, Advanced Features
   - **Enhanced**: Mode-aware menus showing file-level or group-based options
   - **Enhanced**: File status tables, directory summaries, and workload distribution views
   - **v2.3 New**: Performance monitoring dashboards and real-time progress display

4. **Configuration Management**: Auto-saves branch and settings on first run
   - Persistent storage in `.merge_work/project_config.json`
   - 30-day expiry detection for configurations
   - **Enhanced**: Processing mode preference persistence
   - **v2.3 New**: Enhanced analysis configuration with 35+ parameters

5. **Advanced File Management**:
   - **Enhanced**: Comprehensive ignore system (`.merge_ignore` file support)
   - **Enhanced**: Multi-dimensional file querying (path, assignee, status, directory)
   - **Enhanced**: Load balancing algorithms for file distribution
   - **Enhanced**: Real-time file status tracking and updates
   - **v2.3 New**: Batch file processing with progress monitoring

### Key Modules Structure

- **Core Logic**: `core/` contains merge executors, git operations, contributor analysis, task assignment
  - **v2.3 New**: `enhanced_contributor_analyzer.py` - Multi-dimensional analysis engine
  - **v2.3 New**: `enhanced_task_assigner.py` - Intelligent assignment with load balancing
  - **Enhanced**: `git_operations.py` with enhanced Git log parsing and --numstat support
  - **Enhanced**: Merge executors with file-level script generation
  - **Enhanced**: `query_system.py` for advanced file searching

- **UI Components**: `ui/` handles display formatting and hierarchical menus
  - **Enhanced**: `display_helper.py` with file-level display methods
  - **Renamed**: `flat_menu_manager.py` (previously `menu_manager.py`) with dual-mode support

- **Utilities**: `utils/` provides configuration, file operations, performance monitoring
  - **Enhanced**: `ignore_manager.py` for file filtering
  - **Enhanced**: `file_helper.py` with file-level plan management
  - **Enhanced**: `performance_monitor.py` with detailed performance tracking

- **Entry Points**: `main.py` (enhanced config support), `git_merge_orchestrator.py` (main controller)

- **Testing and Validation**:
  - **v2.3 New**: `test_performance_optimization.py` - Performance validation suite
  - **v2.3 New**: `demo_enhanced_analysis.py` - Feature demonstration
  - **Enhanced**: `test_enhanced_analysis.py` - Enhanced analysis testing

### Enhanced Analysis System (v2.3)

#### Multi-dimensional Scoring Algorithm
```python
# Core scoring components
line_weight = logarithmic_scaling(total_changes)
time_weight = exp(-days_since_commit / half_life)
consistency_score = commits_regularity * bonus_factor
final_score = base_score * (1 + line_weight + time_weight + consistency_score)
```

#### Batch Processing Architecture
```python
# Traditional approach: O(n²)
for each_file:
    get_active_contributors()  # N+1 Query Problem
    calculate_best_assignee()  # Repeated computation

# v2.3 Optimized approach: O(n)
active_contributors = get_active_contributors_once()  # Single query
decisions = compute_final_decision_batch(files, active_contributors)  # Batch computation
assignments = apply_load_balanced_assignment(decisions)  # Smart allocation
```

#### Performance Monitoring System
```
v2.3 Performance Logs:
├── enhanced_performance_log.json      # Overall task assignment performance
├── enhanced_analysis_performance.json # Contributor analysis details
├── decision_performance.json          # Decision computation metrics
└── load_balance_performance.json      # Load balancing statistics
```

### File Processing System

#### File-Level Mode (Default)
- Individual file tracking with status (pending, assigned, in_progress, completed)
- Per-file contributor analysis with enhanced multi-dimensional scoring
- Batch decision pre-computation for optimal performance
- Load balancing algorithms with multi-layer fallback mechanism
- File-level merge script generation (single file or batch)
- Advanced querying: search by path, assignee, status, priority

#### Group-Based Mode (Legacy)
- Traditional directory-based file grouping (max 5 files per group)
- Group-level task assignment and status tracking
- Backward compatibility with existing workflows

#### Common Features
- **v2.3 Enhanced**: Multi-dimensional scoring with line weight, time decay, consistency
- **v2.3 Enhanced**: Batch processing for extreme performance
- **Enhanced**: Activity filtering excludes contributors inactive for 3+ months
- **Enhanced**: Fallback allocation strategies: directory-level → root-level
- **Enhanced**: Intelligent ignore system with glob patterns, regex, and exact matching

### Testing Architecture

Comprehensive test suite organized into multiple categories:
- Configuration, Deployment, Performance, Merge Strategies, Integration, Error Handling
- **v2.3 New**: Performance optimization testing (test_performance_optimization.py)
- **v2.3 New**: Enhanced analysis validation (test_enhanced_analysis.py)
- Success rate targets: 95%+ (excellent), 80-94% (good)
- Performance targets: <10ms/file (excellent), **v2.3 Achievement**: 1.2ms/file (超越目标8倍)
- **Enhanced**: File-level processing mode testing coverage

## Configuration Constants (`config.py`)

Key defaults:
- `DEFAULT_MAX_FILES_PER_GROUP = 5` (group mode only)
- `DEFAULT_MAX_TASKS_PER_PERSON = 1000` (increased from 200)
- `DEFAULT_ACTIVE_MONTHS = 3`
- `CACHE_EXPIRY_HOURS = 24`
- `MAX_WORKER_THREADS = 4`

**v2.3 Enhanced Analysis Configuration**:
```python
ENHANCED_CONTRIBUTOR_ANALYSIS = {
    # Core switches
    "enabled": True,
    "algorithm_version": "2.0",
    "assignment_algorithm": "comprehensive",

    # Multi-dimensional scoring
    "line_weight_enabled": True,
    "time_weight_enabled": True,
    "consistency_weight_enabled": True,

    # Performance optimization
    "cache_enabled": True,
    "parallel_processing": True,
    "max_parallel_files": 50,

    # 35+ configuration parameters for fine-tuning
}

ALGORITHM_CONFIGS = {
    "simple": {"use_time_weight": False, "use_line_weight": False},
    "weighted": {"use_time_weight": True, "use_line_weight": True},
    "comprehensive": {"use_time_weight": True, "use_line_weight": True, "use_consistency_weight": True}
}
```

**File-Level Constants**:
- Table configurations for file status overview, directory summary, workload distribution
- File status icons and priority mappings
- File-level display formatting parameters

**Enhanced Ignore System**:
- `DEFAULT_IGNORE_PATTERNS`: Comprehensive list of patterns for common development files
- `IGNORE_RULE_TYPES`: Support for glob, regex, exact, prefix, and suffix matching

## Development Guidelines

- Code uses Chinese comments and output messages
- Snake_case function naming convention
- All merge executors must inherit from `BaseMergeExecutor`
- New strategies registered via `MergeExecutorFactory`
- Performance-critical components should provide enhanced alternatives (v2.3)
- Rich emoji and formatted output for user experience

### v2.3 Enhanced Development Guidelines

- **Performance First**: Always consider batch processing opportunities
- **Enhanced Analysis**: Use `EnhancedContributorAnalyzer` for new features
- **Intelligent Assignment**: Implement multi-layer fallback mechanisms
- **Performance Monitoring**: Add detailed performance logging for critical operations
- **Adaptive Filtering**: Design filters that automatically adjust thresholds
- **Batch Operations**: Prefer batch operations over individual processing

### File-Level Development Guidelines

- **File Status Management**: Use standardized status values (pending, assigned, in_progress, completed)
- **Contributor Analysis**: Always consider both recent and historical contributions
- **Load Balancing**: Implement fair distribution algorithms when assigning files
- **Query System**: Support flexible searching across multiple dimensions
- **Ignore System**: Respect user-defined ignore patterns for file filtering
- **UI Consistency**: Maintain consistent display formats between file-level and group-based modes

### Merge Executor Extensions

When extending merge executors for new strategies:
1. Inherit from `BaseMergeExecutor`
2. Implement both group-level and file-level methods:
   - `generate_merge_script()` and `generate_file_merge_script()`
   - `generate_batch_merge_script()` and `generate_file_batch_merge_script()`
3. Provide strategy-specific footer notes for both modes
4. Register new strategies in `MergeExecutorFactory`

### Processing Mode Compatibility

Code should support both processing modes:
- Check `processing_mode` in plan data structure
- Handle both `files` array (file-level) and `groups` array (group-based)
- Provide fallback behavior for legacy data structures
- Test functionality in both modes

## Data Structure Evolution

### v2.3 Enhanced Analysis Structure
```json
{
  "enhanced_analysis": {
    "algorithm_version": "2.0",
    "multi_dimensional_scoring": {
      "line_weight": 0.3,
      "time_decay": 0.4,
      "consistency_bonus": 0.2
    },
    "performance_metrics": {
      "analysis_time": 0.12,
      "decision_time": 0.0007,
      "assignment_time": 0.0004
    }
  }
}
```

### File-Level Plan Structure
```json
{
  "processing_mode": "file_level",
  "architecture_version": "2.3_optimized",
  "files": [
    {
      "path": "src/example.py",
      "assignee": "developer",
      "status": "assigned",
      "priority": "normal",
      "assignment_reason": "主要贡献者 (综合评分优秀)",
      "enhanced_score": 5.2,
      "contributors": {
        "developer": {
          "enhanced_score": 5.2,
          "score_breakdown": {
            "base_score": 3.0,
            "line_weight": 1.2,
            "time_weight": 0.8,
            "consistency_score": 0.2
          }
        }
      }
    }
  ],
  "metadata": {
    "performance_stats": {
      "total_time": 0.12,
      "avg_time_per_file": 1.2
    }
  }
}
```

### Group-Based Plan Structure (Legacy)
```json
{
  "processing_mode": "group_based",
  "groups": [
    {
      "name": "src/",
      "files": ["src/example.py", "src/utils.py"],
      "assignee": "developer",
      "status": "pending"
    }
  ],
  "metadata": {...}
}
```

## Performance Considerations

### v2.3 Performance Revolution
- **Extreme Performance**: 1.2ms/file processing (超越10ms目标8倍)
- **Batch Processing**: All major operations use batch processing for optimal performance
- **Smart Caching**: Multi-level caching with 24-hour contributor analysis caching
- **Load Balancing**: Intelligent distribution algorithms prevent contributor overload
- **Query Optimization**: Batch decision pre-computation eliminates N+1 queries
- **Performance Monitoring**: Real-time performance tracking with automated insights

### Previous Performance Features
- **File-Level Mode**: Optimized for large repositories with many files
- **Caching**: 24-hour contributor analysis caching with 90%+ hit rates
- **Query Optimization**: Indexed searching for fast file lookups

@TODO.md

# 开发规范

## 代码格式化
* 每次提交前，修改的代码部分需要进行格式化
* Python代码使用black进行格式化：`black <file_path>`
* 保持代码风格一致性

## v2.3架构要点
* 默认使用增强分析系统，提供极致的性能和精确度
* 批量处理优先：所有主要操作都应考虑批量处理机会
* 智能容错：实现多层回退机制确保高成功率
* 性能监控：为关键操作添加详细的性能日志记录
* 重点使用comprehensive分配算法作为默认选择

## v2.2架构要点
* 默认使用file_level处理模式，提供更精确的任务分配和进度跟踪
* 可通过参数切换到group_based模式以保持向后兼容性
* 所有新功能都应同时支持两种处理模式
* 重点使用legacy合并策略作为默认选择

## 测试要求
* 使用`python run_tests.py`进行测试
* 重要功能变更需要进行健康检查：`python run_tests.py --health`
* 性能相关变更需要运行：`python test_performance_optimization.py`
* 利用test-environment子模块进行完整测试

## 项目状态
**版本**: v2.3 (生产就绪)
**更新**: 2025-08-07
**状态**: ✅ 开发完成，性能优化完成，所有TODO项目已实现
**性能**: 1.2ms/文件 (99.6%性能提升)
