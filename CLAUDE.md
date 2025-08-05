# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Main application with auto-configuration
python main.py                        # Uses saved configuration from previous runs
python main.py [source_branch] [target_branch] [options]  # First run or manual override
python main.py --update-config        # Update saved configuration
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

This is a Git merge orchestration tool built with a **DRY (Don't Repeat Yourself) architecture** and dual merge strategy system. The codebase follows a factory pattern with strategy inheritance for merge operations.

### Core Architecture Components

1. **Strategy Pattern Implementation**:
   - `BaseMergeExecutor` (abstract base class) provides common functionality
   - `LegacyMergeExecutor` and `StandardMergeExecutor` inherit from base (~60% code reuse)
   - `MergeExecutorFactory` manages runtime strategy selection
   - Dual merge strategies: Legacy (fast override) and Standard (3-way merge)

2. **Performance-Optimized Dual Components**:
   - Basic vs Optimized versions of key modules (ContributorAnalyzer, TaskAssigner)
   - Optimized versions provide 60%+ performance improvement with 24-hour caching
   - Cache hit rates of 90%+ for large-scale operations

3. **Hierarchical UI System**: 6-category menu structure in `ui/menu_manager.py`
   - Quick Start Wizard, Project Management, Task Assignment, Merge Execution, System Management, Advanced Features

4. **Configuration Management**: Auto-saves branch and settings on first run
   - Persistent storage in `.merge_work/project_config.json`
   - 30-day expiry detection for configurations

### Key Modules Structure

- **Core Logic**: `core/` contains merge executors, git operations, contributor analysis, task assignment
- **UI Components**: `ui/` handles display formatting and hierarchical menus  
- **Utilities**: `utils/` provides configuration, file operations, performance monitoring
- **Entry Points**: `main.py` (enhanced config support), `git_merge_orchestrator.py` (main controller)

### File Management System

The tool intelligently groups files by directory structure (max 5 files per group) and assigns tasks based on contributor analysis:
- Multi-dimensional scoring: Recent commits × 3 + historical commits × 1
- Activity filtering excludes contributors inactive for 3+ months
- Fallback allocation strategies: directory-level → root-level

### Testing Architecture

Comprehensive test suite organized into 7 categories:
- Configuration, Deployment, Performance, Merge Strategies, Integration, Error Handling
- Success rate targets: 95%+ (excellent), 80-94% (good)
- Performance targets: <10s (excellent), 10-30s (good)

## Configuration Constants (`config.py`)

Key defaults:
- `DEFAULT_MAX_FILES_PER_GROUP = 5`
- `DEFAULT_MAX_TASKS_PER_PERSON = 200`
- `DEFAULT_ACTIVE_MONTHS = 3`
- `CACHE_EXPIRY_HOURS = 24`
- `MAX_WORKER_THREADS = 4`

## Development Guidelines

- Code uses Chinese comments and output messages
- Snake_case function naming convention
- All merge executors must inherit from `BaseMergeExecutor`
- New strategies registered via `MergeExecutorFactory`
- Performance-critical components should provide optimized alternatives
- Rich emoji and formatted output for user experience