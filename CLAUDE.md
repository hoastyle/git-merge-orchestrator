# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 原则
1. 除非必须用英文如翻译，否则用中文回复问题。
2. 每个TODO完成后生成commit。

## 常用开发命令

### 测试
```bash
# 快速健康检查（首次设置推荐）
python run_tests.py --health

# 运行完整测试套件
python run_tests.py --full

# 交互式测试菜单
python run_tests.py

# 测试特定模块
python tests/comprehensive_test.py --category config
python tests/config_test.py
python tests/test_deployment.py

# 测试包入口点
python -m tests
```

### 运行应用程序
```bash
# 首次运行配置
python main.py feature/big-feature main

# 后续运行（使用保存的配置）
python main.py

# 自定义配置
python main.py source-branch target-branch --max-files 8 --strategy standard

# 配置管理
python main.py --show-config
python main.py --reset-config
python main.py --update-config
```

### 代码质量
本项目不使用传统的代码检查工具。代码质量通过以下方式维护：
- 95%+ 成功率目标的综合测试套件
- 性能监控和优化
- 通过 DRY 架构原则进行代码审查

## 项目架构

### 高级架构
这是一个 **Git 合并编排器** - 用于管理大型仓库中复杂分支合并的智能工具。项目使用 **DRY（不重复）架构**，结合**工厂模式和策略模式**进行合并执行。

### 核心架构模式
- **工厂模式**: `MergeExecutorFactory` 根据策略创建相应的合并执行器
- **策略模式**: 两种合并策略（Legacy 和 Standard）共享基类
- **DRY 架构**: `BaseMergeExecutor` 消除策略间的代码重复
- **模板方法**: 通用工作流程配合策略特定实现

### 关键组件

#### 主要入口点
- `main.py`: 增强的主入口，包含配置管理和交互菜单
- `git_merge_orchestrator.py`: 协调所有组件的主控制器
- `run_tests.py`: 测试运行器入口点（重定向到 tests/run_tests.py）

#### 核心业务逻辑 (`core/`)
- **Git 操作**: `git_operations.py` - 所有 Git 命令交互
- **贡献者分析**:
  - `contributor_analyzer.py` - 基础贡献者分析
  - `optimized_contributor_analyzer.py` - 带缓存的性能优化版本
- **任务分配**:
  - `task_assigner.py` - 基础任务分配逻辑
  - `optimized_task_assigner.py` - 负载均衡和性能优化增强版
- **合并执行**（DRY 架构）:
  - `base_merge_executor.py` - 包含通用合并逻辑的抽象基类
  - `legacy_merge_executor.py` - 快速覆盖策略实现
  - `standard_merge_executor.py` - 标准三路合并策略实现
  - `merge_executor_factory.py` - 创建合并执行器的工厂
- **计划管理**: `plan_manager.py` - 合并计划创建和管理

#### 用户界面 (`ui/`)
- `display_helper.py` - 格式化、表格显示、进度指示器
- `menu_manager.py` - 分层菜单系统（6个主类别）

#### 工具类 (`utils/`)
- `file_helper.py` - 文件操作、分组逻辑、脚本生成
- `config_manager.py` - 项目配置持久化和管理
- `performance_monitor.py` - 性能跟踪和优化监控

### 合并策略（DRY 架构）

#### 策略选择
系统通过统一接口支持两种合并策略：

1. **Legacy 模式** (`legacy`): 快速覆盖策略
   - 源分支直接覆盖文件
   - 不生成冲突标记
   - 适用于：热修复、紧急发布、小团队

2. **Standard 模式** (`standard`): 标准三路合并
   - Git 标准合并行为，包含冲突标记
   - 需要手动冲突解决
   - 适用于：大型项目、协作开发

#### DRY 实现优势
- 通过 `BaseMergeExecutor` 在策略间实现 **60% 代码复用**
- 所有合并操作的统一接口
- 易于添加新合并策略
- 简化测试和维护

### 配置系统
- **自动配置保存**: 首次运行保存分支和设置
- **无参数执行**: 后续运行使用保存的配置
- **配置优先级**: 命令行 > 配置文件 > 交互输入
- **配置文件**: `.merge_work/project_config.json`

### 性能优化
- **涡轮增压任务分配**: 通过缓存提升 60%+ 性能
- **24小时持久缓存**: 贡献者分析缓存系统
- **并行批处理**: 大型仓库的多线程分析
- **性能监控**: 完整的性能统计和调试

### 文件结构原则
```
git-merge-orchestrator/
├── main.py                    # 带配置管理的增强入口点
├── git_merge_orchestrator.py  # 主控制器
├── config.py                  # 全局配置常量
├── core/                      # 核心业务逻辑
│   ├── *_analyzer.py         # 贡献者分析（基础 + 优化版）
│   ├── *_assigner.py         # 任务分配（基础 + 优化版）
│   ├── base_merge_executor.py # DRY 架构基类
│   ├── *_merge_executor.py   # 策略实现
│   └── merge_executor_factory.py # 策略创建工厂
├── ui/                       # 用户界面组件
├── utils/                    # 工具模块
└── tests/                    # 综合测试框架
```

## 开发指南

### 代码规范
- **中文注释和输出**: 所有面向用户的文本和注释使用中文
- **Snake_case 函数**: 遵循 Python 命名规范
- **丰富的错误处理**: 全面的错误处理和用户友好的消息
- **Emoji 格式化**: 广泛使用 emoji 增强用户体验
- **DRY 原则**: 避免代码重复，使用基类和工厂

### 新功能特性

#### 文件级分配系统
- **启用方式**: 在 `config.py` 中设置 `ASSIGNMENT_STRATEGY["file_level_assignment"] = True`
- **工作原理**: 分析组内每个文件的贡献者，选择最合适的负责人
- **回退机制**: 如果文件级分配失败，自动回退到组级分配
- **详细信息**: 保存文件级分配详情到 `group["file_assignments"]`

#### 增强评分算法
- **启用方式**: 在 `config.py` 中设置 `ASSIGNMENT_STRATEGY["enhanced_scoring"] = True`
- **评分公式**: `提交数权重 + 修改行数权重 + 新增行数权重`
- **权重配置**: 在 `SCORING_WEIGHTS` 中自定义各项权重
- **代码行统计**: 使用 `git log --numstat` 获取详细的代码变更统计

#### 多维度查询系统
- **文件查询**: 支持简单匹配、通配符、正则表达式
- **目录查询**: 支持递归和非递归查询
- **负责人查询**: 支持精确匹配和模糊匹配
- **交互式搜索**: 提供智能建议和自动补全
- **查询结果**: 支持表格、摘要、详细三种显示格式

#### 优化菜单架构
- **2层菜单**: 将原来的3层菜单简化为最多2层
- **6个主类别**: 快速开始、项目管理、任务分配、智能查询、执行合并、系统设置
- **直接操作**: 减少子菜单层次，提高操作效率
- **上下文感知**: 根据项目状态提供智能建议

### 使用新功能

#### 启用文件级分配
```python
# 在 config.py 中修改
ASSIGNMENT_STRATEGY = {
    "file_level_assignment": True,     # 启用文件级分配
    "fallback_to_group": True,         # 启用回退到组级分配
    "enhanced_scoring": True,          # 启用增强评分算法
    "line_stats_weight": 0.3,          # 代码行数权重比例
}
```

#### 使用智能查询
```bash
# 通过菜单
python main.py
# 选择 4. 智能查询

# 文件查询示例
查询: *.py
模式: glob

# 目录查询示例
目录: src/core
递归: 是

# 负责人查询示例
姓名: 张三
模糊匹配: 是
```

#### 查看文件级分配结果
- 在任务分配后，组信息会包含 `file_assignments` 字段
- 可以通过智能查询查看具体文件的负责人
- 分配原因会显示文件级分配的详细信息

### 配置选项

#### 评分权重配置
```python
SCORING_WEIGHTS = {
    "recent_commits": 3,           # 一年内提交权重
    "total_commits": 1,            # 历史提交权重
    "recent_modified_lines": 2,    # 一年内修改行数权重
    "total_modified_lines": 0.5,   # 历史修改行数权重
    "recent_added_lines": 1.5,     # 一年内新增行数权重
    "total_added_lines": 0.3,      # 历史新增行数权重
}
```

#### 分配策略配置
```python
ASSIGNMENT_STRATEGY = {
    "file_level_assignment": True,   # 启用文件级分配
    "fallback_to_group": True,       # 文件级分配失败时回退到组级分配
    "enhanced_scoring": True,        # 启用增强评分算法（包含行数统计）
    "line_stats_weight": 0.3,       # 代码行数在评分中的权重比例
}
```

### 性能优化

#### 缓存机制
- **文件贡献者缓存**: 24小时持久化缓存
- **目录贡献者缓存**: 内存缓存，提高查询速度
- **批量分析**: 对大型项目使用并行分析
- **增量更新**: 只重新分析变更的文件

#### 最佳实践
- 首次使用建议运行健康检查：`python run_tests.py --health`
- 大型项目建议启用文件级分配和增强评分
- 定期清理缓存以获取最新的贡献者信息
- 使用交互式查询功能提高工作效率

### 添加新合并策略
扩展合并策略系统时：

1. **继承 `BaseMergeExecutor`**: 所有策略必须扩展基类
2. **实现抽象方法**:
   - `generate_merge_script()`
   - `generate_batch_merge_script()`
   - `get_strategy_name()`
   - `get_strategy_description()`
   - `_generate_strategy_specific_merge_logic()`
3. **在工厂中注册**: 将新策略添加到 `MergeExecutorFactory`
4. **添加配置**: 更新配置常量和文档
5. **添加测试**: 为新策略包含全面测试

### 性能考虑
- **使用优化版本**: 优先使用 `OptimizedContributorAnalyzer` 和 `OptimizedTaskAssigner`
- **监控缓存效率**: 通过性能监控检查缓存命中率
- **批量操作**: 对 10+ 文件的操作使用批处理
- **线程限制**: 遵守 `MAX_WORKER_THREADS = 4` 配置

### 测试策略
项目使用综合测试框架：
- 所有测试套件 **95%+ 成功率目标**
- **多类别测试**: config、deployment、performance、merge_strategies、integration、error_handling
- **性能基准测试**: 大规模测试（1000+ 文件）
- **健康检查**: 核心功能的快速验证

### 配置管理最佳实践
- **自动配置保存**: 系统在首次成功运行后自动保存配置
- **配置验证**: 验证配置格式和过期（30天警告）
- **优先级处理**: 命令行参数覆盖保存的配置
- **重置能力**: 提供简单的配置重置功能

### 代码库工作流程
1. **从测试开始**: 首先运行健康检查：`python run_tests.py --health`
2. **使用主入口**: 始终使用 `python main.py` 作为应用程序入口
3. **检查配置**: 使用 `python main.py --show-config` 查看当前设置
4. **遵循 DRY 原则**: 扩展基类而不是重复代码
5. **充分测试**: 提交更改前使用综合测试套件

此架构通过 DRY 原则和综合测试，为大规模协作开发实现智能 Git 合并编排，同时保持代码质量。
