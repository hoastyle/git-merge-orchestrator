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
```

### Testing
```bash
python run_tests.py                   # Interactive test menu
python run_tests.py --health         # Quick health check
python run_tests.py --full           # Complete test suite
python tests/comprehensive_test.py   # Direct comprehensive testing
python tests/config_test.py         # Configuration testing
python tests/test_deployment.py     # Deployment verification
```

## Architecture Overview

This is a Git merge orchestration tool built with a **DRY (Don't Repeat Yourself) architecture** and **dual processing modes**. The codebase follows a factory pattern with strategy inheritance for merge operations and supports both file-level and group-based processing.

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
   - **New**: File-level merge methods alongside group-based methods

2. **Performance-Optimized Dual Components**:
   - Basic vs Optimized versions of key modules (ContributorAnalyzer, TaskAssigner)
   - Optimized versions provide 60%+ performance improvement with 24-hour caching
   - Cache hit rates of 90%+ for large-scale operations
   - **New**: File-level caching and batch processing optimizations

3. **Enhanced UI System**: 6-category menu structure with dual-mode support
   - Quick Start Wizard, Project Management, Task Assignment, Merge Execution, System Management, Advanced Features
   - **New**: Mode-aware menus showing file-level or group-based options
   - **New**: File status tables, directory summaries, and workload distribution views

4. **Configuration Management**: Auto-saves branch and settings on first run
   - Persistent storage in `.merge_work/project_config.json`
   - 30-day expiry detection for configurations
   - **New**: Processing mode preference persistence

5. **Advanced File Management**:
   - **New**: Comprehensive ignore system (`.merge_ignore` file support)
   - **New**: Multi-dimensional file querying (path, assignee, status, directory)
   - **New**: Load balancing algorithms for file distribution
   - **New**: Real-time file status tracking and updates

### Key Modules Structure

- **Core Logic**: `core/` contains merge executors, git operations, contributor analysis, task assignment
  - **Enhanced**: `git_operations.py` with file-level branch creation methods
  - **Enhanced**: Merge executors with file-level script generation
  - **New**: `query_system.py` for advanced file searching

- **UI Components**: `ui/` handles display formatting and hierarchical menus
  - **Enhanced**: `display_helper.py` with file-level display methods
  - **Enhanced**: `menu_manager.py` with dual-mode support

- **Utilities**: `utils/` provides configuration, file operations, performance monitoring
  - **New**: `ignore_manager.py` for file filtering
  - **Enhanced**: `file_helper.py` with file-level plan management

- **Entry Points**: `main.py` (enhanced config support), `git_merge_orchestrator.py` (main controller)

### File Processing System

#### File-Level Mode (Default)
- Individual file tracking with status (pending, assigned, in_progress, completed)
- Per-file contributor analysis and intelligent assignment
- Load balancing algorithms to distribute workload evenly
- File-level merge script generation (single file or batch)
- Advanced querying: search by path, assignee, status, priority

#### Group-Based Mode (Legacy)
- Traditional directory-based file grouping (max 5 files per group)
- Group-level task assignment and status tracking
- Backward compatibility with existing workflows

#### Common Features
- Multi-dimensional scoring: Recent commits × 3 + historical commits × 1
- Activity filtering excludes contributors inactive for 3+ months
- Fallback allocation strategies: directory-level → root-level
- Intelligent ignore system with glob patterns, regex, and exact matching

### Testing Architecture

Comprehensive test suite organized into 7 categories:
- Configuration, Deployment, Performance, Merge Strategies, Integration, Error Handling
- Success rate targets: 95%+ (excellent), 80-94% (good)
- Performance targets: <10s (excellent), 10-30s (good)
- **New**: File-level processing mode testing coverage

## Configuration Constants (`config.py`)

Key defaults:
- `DEFAULT_MAX_FILES_PER_GROUP = 5` (group mode only)
- `DEFAULT_MAX_TASKS_PER_PERSON = 200`
- `DEFAULT_ACTIVE_MONTHS = 3`
- `CACHE_EXPIRY_HOURS = 24`
- `MAX_WORKER_THREADS = 4`

**New File-Level Constants**:
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
- Performance-critical components should provide optimized alternatives
- Rich emoji and formatted output for user experience

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

### File-Level Plan Structure
```json
{
  "processing_mode": "file_level",
  "files": [
    {
      "path": "src/example.py",
      "assignee": "developer",
      "status": "assigned",
      "priority": "normal",
      "assignment_reason": "主要贡献者",
      "contributors": {...}
    }
  ],
  "metadata": {...}
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

- **File-Level Mode**: Optimized for large repositories with many files
- **Caching**: 24-hour contributor analysis caching with 90%+ hit rates
- **Batch Operations**: Support for batch file processing to reduce overhead
- **Load Balancing**: Intelligent distribution algorithms to prevent contributor overload
- **Query Optimization**: Indexed searching for fast file lookups

@TODO.md
@Plan.md

# 其他
* 每次提交前，修改的代码部分需要进行格式化。如果是python，利用black进行格式化。
* 新的v2.2架构支持文件级处理，提供更精确的任务分配和进度跟踪
* 默认使用file_level模式，可通过参数切换到group_based模式以保持向后兼容性