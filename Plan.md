# Git Merge Orchestrator 完整优化计划与方案

## 项目背景
基于CLAUDE.md架构分析和TODO.md的5项具体需求，制定系统性优化方案，提升项目的功能完整性、可用性和维护性。

## 优化目标与方案

### 1. 测试目录管理优化
**目标**: 完善git-merge-orchestrator-test目录的功能和文档
**实施方案**:
- 在CLAUDE.md中添加测试目录使用说明和最佳实践
- 创建测试目录的README.md，包含测试场景、用例和自动化脚本
- 优化现有测试脚本，支持在测试目录中自动创建多种git仓库场景
- 添加测试数据生成工具，支持不同规模的仓库测试

### 2. 架构重构：完全移除组级策略
**目标**: 将基于组的策略完全替换成基于文件的分析、分配
**实施方案**:
- **配置层面**: 移除config.py中的GROUP_TYPES、TABLE_CONFIGS中的组相关配置
- **核心逻辑**: 重构file_helper.py，移除所有分组逻辑，改为纯文件级处理
- **任务分配**: 更新task_assigner和optimized_task_assigner，实现直接的文件级分配
- **显示系统**: 修改display_helper.py和menu_manager.py，从组视图改为文件列表视图
- **数据结构**: 更新plan_manager.py中的数据结构，移除group概念

### 3. 高级查询系统实现
**目标**: 提供完整的多维度查询功能，支持模糊匹配和反向查询
**实施方案**:
- **新增模块**: 创建`core/query_system.py`和`ui/query_interface.py`
- **查询功能**:
  - 按人员查询：`query_by_assignee(name, fuzzy=True)` - 负责的文件、合并状态、工作负载
  - 按文件查询：`query_by_file(pattern, fuzzy=True)` - 负责人、修改历史、合并状态
  - 按状态查询：`query_by_status(status)` - 待处理、进行中、已完成的文件
  - 反向查询：`reverse_query(criteria)` - 根据条件反向查找
- **模糊匹配**: 集成difflib和re模块，支持文件名、人员姓名的智能匹配
- **UI集成**: 在menu_manager.py中新增"查询分析"菜单类别

### 4. 默认策略调整
**目标**: 将系统默认策略改为legacy模式
**实施方案**:
- 修改`merge_executor_factory.py`中的默认模式从STANDARD_MODE改为LEGACY_MODE
- 更新配置文件和初始化逻辑
- 修改用户引导和帮助信息，强调legacy策略的优势
- 更新相关文档说明默认选择的原因

### 5. 文件/目录忽略功能 (新增)
**目标**: 允许指定ignore目录或者文件等
**实施方案**:
- **配置系统**: 在config.py中添加默认忽略规则配置
- **忽略规则引擎**: 创建`utils/ignore_manager.py`模块
  - 支持.gitignore风格的模式匹配
  - 支持正则表达式和glob模式
  - 支持目录级和文件级忽略
- **集成点**:
  - git_operations.py: 获取文件列表时应用忽略规则
  - file_helper.py: 文件处理时检查忽略状态
  - contributor_analyzer.py: 分析时排除忽略文件
- **用户界面**: 在menu_manager.py中添加忽略规则管理菜单
- **配置文件**: 支持项目级忽略配置文件`.merge_ignore`

### 6. CLAUDE.md全面同步更新
**目标**: 确保CLAUDE.md准确反映所有架构变更
**更新内容**:
- 移除所有分组相关的架构描述
- 添加文件级分析系统的详细说明
- 新增查询系统使用指南和API说明
- 添加忽略规则配置说明
- 更新配置常量列表，移除组相关配置
- 强调legacy策略为默认选择的优势
- 添加测试目录使用最佳实践

## 技术实施细节

### 忽略规则系统设计
```python
# utils/ignore_manager.py 核心功能
class IgnoreManager:
    def __init__(self):
        self.rules = []
        self.default_rules = [
            '*.pyc', '__pycache__/', '.git/', 
            '*.log', '*.tmp', '.DS_Store'
        ]
        self.load_ignore_rules()
    
    def should_ignore(self, file_path):
        """检查文件是否应该被忽略"""
        for rule in self.rules:
            if self._match_rule(file_path, rule):
                return True
        return False
    
    def add_rule(self, pattern, rule_type='glob'):
        """添加忽略规则"""
        self.rules.append({'pattern': pattern, 'type': rule_type})
    
    def load_ignore_rules(self):
        """从配置文件加载忽略规则"""
        # 加载.merge_ignore文件
        # 合并默认规则和自定义规则
```

### 查询系统设计
```python
# core/query_system.py 核心功能
class QuerySystem:
    def __init__(self, plan_manager):
        self.plan_manager = plan_manager
        
    def query_by_assignee(self, name, fuzzy=True):
        """按负责人查询文件和状态"""
        # 返回该负责人的所有文件、状态、工作负载统计
        
    def query_by_file(self, pattern, fuzzy=True):
        """按文件名模式查询"""
        # 支持glob模式和正则表达式
        
    def query_by_status(self, status):
        """按合并状态查询"""
        # pending, in_progress, completed, conflict
        
    def advanced_search(self, criteria):
        """高级组合查询"""
        # 支持多条件组合查询
        
    def reverse_query(self, criteria):
        """反向查询 - 根据结果查找满足条件的记录"""
        # 例如：查找所有未分配负责人的文件
```

### 文件级处理架构
```python
# 移除分组后的数据结构
FileTask = {
    'file_path': str,
    'assignee': str, 
    'status': str,
    'merge_strategy': str,
    'conflicts': list,
    'commit_history': list,
    'assignment_reason': str
}

# 替代原有的GroupTask结构
```

## 实施时间线

### 阶段1: 基础功能优化 (优先级：高)
1. **默认策略调整** - 1天
   - 修改merge_executor_factory.py默认值
   - 更新相关配置和文档

2. **忽略功能实现** - 3天
   - 创建ignore_manager.py模块
   - 集成到现有文件处理流程
   - 添加配置界面和文件支持

### 阶段2: 功能增强 (优先级：中)
3. **查询系统实现** - 5天
   - 设计查询API和数据结构
   - 实现各类查询功能
   - 创建用户界面集成

### 阶段3: 架构重构 (优先级：中)
4. **移除分组逻辑** - 7天
   - 重构核心数据结构
   - 更新所有相关模块
   - 全面测试和验证

### 阶段4: 完善优化 (优先级：低)
5. **测试目录功能** - 2天
   - 完善测试环境
   - 添加文档和示例

6. **文档更新** - 2天
   - 同步CLAUDE.md内容
   - 验证文档准确性

## 风险评估与应对

### 主要风险
1. **架构重构风险**: 移除分组逻辑可能影响现有功能
   - **应对**: 分步实施，保留兼容模式，充分测试

2. **性能影响**: 文件级处理可能影响大仓库性能
   - **应对**: 优化算法，使用缓存，并行处理

3. **用户体验变化**: 界面和操作流程的改变
   - **应对**: 保持核心操作不变，渐进式改进

### 回滚计划
- 每个阶段完成后创建代码快照
- 关键功能保留向后兼容接口
- 提供配置开关支持新旧模式切换

## 验证标准

### 功能验证
- [ ] 所有现有功能正常工作
- [ ] 新增忽略功能正确过滤文件
- [ ] 查询系统返回准确结果
- [ ] 文件级分配逻辑正确
- [ ] 默认legacy策略生效

### 性能验证
- [ ] 文件级处理性能不低于原组级处理
- [ ] 大仓库(1000+文件)处理时间<30秒
- [ ] 查询响应时间<2秒
- [ ] 内存占用不超过原有2倍

### 兼容性验证
- [ ] 现有配置文件可正常加载
- [ ] 历史数据可正常迁移
- [ ] 测试用例全部通过
- [ ] 不同操作系统兼容性

### 用户体验验证
- [ ] 界面操作直观易懂
- [ ] 错误信息清晰有用
- [ ] 帮助文档完整准确
- [ ] 新手引导流畅

## 预期效果

### 架构优化
- **代码简化**: 移除不必要的分组抽象，代码行数减少15-20%
- **维护性**: 统一的文件级处理逻辑，降低维护复杂度
- **扩展性**: 更灵活的架构支持未来功能扩展

### 功能增强
- **查询能力**: 强大的多维度查询，提升用户工作效率
- **忽略功能**: 智能过滤不相关文件，减少干扰
- **策略优化**: 默认legacy模式提供更快的合并体验

### 开发体验
- **测试环境**: 完善的测试目录支持各种场景验证
- **文档同步**: CLAUDE.md与代码实现100%一致
- **调试便利**: 详细的查询和分析工具

### 性能提升
- **处理速度**: 文件级处理减少不必要的分组开销
- **内存优化**: 简化的数据结构降低内存占用
- **响应时间**: 优化的查询算法提升交互响应速度

## 后续发展规划

### 短期目标 (1-2月)
- 完成所有优化项目实施
- 收集用户反馈，调整优化策略
- 发布稳定版本

### 中期目标 (3-6月)  
- 基于用户反馈进一步优化
- 添加更多高级功能
- 集成到CI/CD流程

### 长期目标 (6月+)
- 开发Web界面版本
- 支持分布式大型项目
- 与其他开发工具生态集成