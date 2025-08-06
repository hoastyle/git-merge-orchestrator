# Git Merge Orchestrator 更新日志

## v2.2.0 - 文件级处理架构升级 (2024-08-06)

### 🎉 主要功能

#### 架构重构：从组模式到文件级处理
- **完全移除基于组的策略**，实现文件级精确分析和分配
- 新的数据结构支持 `processing_mode: "file_level"`
- 文件状态跟踪：`pending`, `assigned`, `in_progress`, `completed`
- 精确的文件级负载均衡算法

#### 高级查询系统
- **多维度查询功能**：按人员、文件、状态、目录查询
- **模糊匹配支持**：使用difflib和正则表达式实现智能匹配
- **反向查询**：根据条件反向查找相关项目
- **组合查询**：支持复杂的查询条件组合

#### 智能忽略系统
- 支持 `.merge_ignore` 配置文件
- 多种匹配模式：glob、regex、精确匹配、前缀、后缀
- 与 `.gitignore` 兼容的智能过滤
- 默认忽略规则涵盖常见开发文件类型

#### 默认策略优化
- **默认使用 legacy 策略**，提供更快的合并体验
- MergeExecutorFactory 默认模式改为 LEGACY_MODE
- 保持对 standard 策略的完整支持

#### UI/UX 系统升级
- **文件级视图**：状态概览、目录摘要、工作负载分配
- 新的表格配置：`file_status_overview`, `file_list`, `directory_summary`
- 文件级菜单和操作选项
- 改进的用户交互体验和反馈

### 🔧 技术改进

#### 核心组件升级
- `BaseMergeExecutor`: 新增文件级合并抽象方法
- `LegacyMergeExecutor`: 实现完整的文件级legacy合并策略
- `StandardMergeExecutor`: 实现完整的文件级standard合并策略
- `GitOperations`: 新增文件级分支操作和贡献者分析方法

#### 新增核心模块
- `core/query_system.py`: 高级查询系统实现
- `utils/ignore_manager.py`: 智能忽略规则管理器

#### 配置系统增强
- 新增文件级表格配置支持
- 扩展忽略规则配置：`DEFAULT_IGNORE_PATTERNS`, `IGNORE_RULE_TYPES`
- 处理模式偏好持久化

#### 数据结构优化
- 新的文件级计划结构设计
- 向后兼容现有组级数据结构
- 文件信息结构：`path`, `assignee`, `status`, `priority`, `assignment_reason`

### 🧪 测试基础设施

#### 完整的测试环境
- **git-merge-orchestrator-test** 独立测试目录
- 测试仓库创建工具：支持4种复杂度类型
- 8种预定义测试场景：合并冲突、文件级处理、负载均衡等
- 测试数据生成器和清理工具
- 详细的测试文档和最佳实践

#### 健康检查系统
- 模块导入验证 ✅
- 配置管理验证 ✅
- Git基础操作验证 ✅
- 合并策略验证 ✅

### 📚 文档更新

- **CLAUDE.md**: 完整的架构文档同步更新
- **TODO.md**: 任务完成状态和未来规划
- **测试文档**: 完整的测试使用指南
- **Plan.md**: 详细的优化方案和实施计划

### 🔄 兼容性

#### 向后兼容
- 支持现有配置文件格式
- `group_based` 模式作为fallback选项
- 现有脚本和工作流保持可用
- 自动化数据迁移处理

#### 新功能兼容
- 命令行参数保持兼容：`--processing-mode`, `--strategy`
- 配置文件自动升级机制
- 平滑的模式切换支持

### 🚀 性能优化

- 文件级处理减少不必要的分组开销
- 优化的查询算法，响应时间 < 2秒
- 智能缓存机制，24小时缓存过期
- 并行处理支持，最大4个工作线程

### 🔒 稳定性改进

- 完善的错误处理和边界条件检查
- 资源清理和内存管理优化
- 异常情况的优雅降级机制
- 详细的日志记录和调试信息

### 📦 代码质量

- **+1906 行代码增加**, **-49 行代码删除**
- 遵循 DRY (Don't Repeat Yourself) 架构原则
- 完整的类型注解和文档字符串
- Black 代码格式化一致性

---

## v2.1.x - 历史版本

### v2.1.0 - DRY架构重构
- 实现 DRY (Don't Repeat Yourself) 架构
- 合并执行器工厂模式
- 性能监控和优化

### v2.0.0 - 初始版本
- 基本的Git合并编排功能
- 组级文件处理
- Legacy 和 Standard 合并策略

---

## 🎯 升级指南

### 从 v2.1.x 升级到 v2.2.0

1. **自动升级**（推荐）：
   ```bash
   git pull origin master
   python main.py --update-config
   ```

2. **手动配置**：
   ```bash
   python main.py --processing-mode file_level
   python main.py --strategy legacy
   ```

3. **验证升级**：
   ```bash
   python run_tests.py --health
   ```

### 新用户快速开始

```bash
# 基本使用
python main.py source_branch target_branch

# 启用文件级处理
python main.py --processing-mode file_level source_branch target_branch

# 使用忽略规则
echo "*.log" > .merge_ignore
python main.py source_branch target_branch
```

---

**Git Merge Orchestrator v2.2.0 现已可用！** 🚀