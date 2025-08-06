# Git Merge Orchestrator 测试指导文档

## 📋 测试目录概述

Git Merge Orchestrator 提供了一个独立的测试环境目录 `git-merge-orchestrator-test`，用于全面测试各种合并场景，确保工具在不同情况下的稳定性和正确性。

## 🏗️ 测试环境架构

### 目录结构
```
../git-merge-orchestrator-test/
├── README.md                            # 测试使用指南
├── test-scripts/                        # 测试工具脚本
│   ├── create_test_repo.py              # 测试仓库创建工具
│   ├── setup_scenarios.py              # 测试场景设置
│   ├── cleanup.py                       # 清理管理工具
│   └── test_data_generator.py           # 测试数据生成器
├── test-repos/                          # 测试仓库目录
├── test-data/                           # 测试数据
└── scenarios/                           # 测试场景配置
```

### 支持的仓库类型
1. **Simple** - 简单仓库（10-20个文件，2-3个贡献者）
2. **Complex** - 复杂仓库（50-100个文件，5-8个贡献者）
3. **Multi-branch** - 多分支仓库（多个feature分支）
4. **Large-scale** - 大规模仓库（500+文件，10+贡献者）

### 预定义测试场景
1. **merge-conflicts** - 合并冲突处理测试
2. **file-level-processing** - 文件级处理和分配测试
3. **load-balancing** - 负载均衡算法测试
4. **large-scale-performance** - 大规模性能压力测试
5. **multi-contributor** - 多专业团队协作测试
6. **complex-directory-structure** - 复杂深层目录结构测试
7. **branch-management** - 复杂分支管理测试
8. **ignore-rules** - 忽略规则功能测试

## 🚀 快速开始

### 步骤1：环境准备
```bash
# 确保您在主项目目录
cd /home/howie/Workspace/Project/tools/git-merge-orchestrator

# 切换到测试目录
cd ../git-merge-orchestrator-test

# 检查测试环境
ls -la
```

### 步骤2：查看可用场景
```bash
# 列出所有可用的测试场景
python test-scripts/setup_scenarios.py --list
```

### 步骤3：设置测试场景
```bash
# 设置单个场景
python test-scripts/setup_scenarios.py --scenario merge-conflicts

# 或设置所有场景（推荐首次使用）
python test-scripts/setup_scenarios.py --scenario all
```

## 📋 详细测试流程

### 1. 合并冲突测试

#### 场景设置
```bash
# 设置合并冲突测试场景
python test-scripts/setup_scenarios.py --scenario merge-conflicts
```

#### 执行测试
```bash
# 进入测试仓库
cd test-repos/merge-conflicts-test

# 查看仓库状态
git log --oneline --graph --all

# 运行合并编排工具
python ../../git-merge-orchestrator/main.py feature-1 master

# 按照界面提示进行操作：
# 1. 选择 "1. 快速开始向导" -> "a. 全流程引导"
# 2. 或者分步操作：分析分叉 -> 创建计划 -> 分配任务 -> 执行合并
```

#### 验证结果
```bash
# 检查生成的合并脚本
ls .merge_work/scripts/

# 检查分配结果
cat .merge_work/merge_plan.json

# 执行生成的合并脚本测试
bash .merge_work/scripts/group_*.sh

# 验证合并结果
git status
git diff
```

### 2. 文件级处理测试

#### 场景设置
```bash
python test-scripts/setup_scenarios.py --scenario file-level-processing
cd test-repos/file-level-test
```

#### 执行测试
```bash
# 使用文件级处理模式
python ../../git-merge-orchestrator/main.py --processing-mode file_level file-level-feature master

# 在主菜单中探索文件级功能：
# - "3. 任务分配" -> 查看文件级分配结果
# - "6. 高级功能" -> "a. 高级查询系统" -> 测试各种查询功能
```

#### 验证文件级功能
```bash
# 检查文件级计划结构
cat .merge_work/merge_plan.json | jq '.files'

# 测试查询功能（在主菜单中）
# - 按人员查询：查看某个开发者负责的所有文件
# - 按状态查询：查看 pending/assigned/completed 文件
# - 按目录查询：查看特定目录下的文件分配
```

### 3. 负载均衡测试

#### 场景设置
```bash
python test-scripts/setup_scenarios.py --scenario load-balancing
cd test-repos/load-balancing-test
```

#### 执行测试
```bash
python ../../git-merge-orchestrator/main.py load-test-feature master

# 重点观察：
# - 任务分配是否平衡
# - 重点贡献者是否分配了更多任务
# - 新手是否有适当的任务分配
```

#### 验证负载均衡
```bash
# 查看工作负载分配（在主菜单中）
# "2. 项目管理" -> "c. 检查项目状态" -> "c. 工作负载分配视图"

# 检查分配原因
# "2. 项目管理" -> "d. 查看分配原因分析"
```

### 4. 性能压力测试

#### 场景设置
```bash
python test-scripts/setup_scenarios.py --scenario large-scale-performance
cd test-repos/performance-test
```

#### 执行性能测试
```bash
# 使用 time 命令测量性能
time python ../../git-merge-orchestrator/main.py feature master

# 观察指标：
# - 总执行时间应 < 30秒
# - 内存使用合理
# - 缓存命中率 > 90%
```

#### 性能测试验证
```bash
# 测试缓存功能
python ../../git-merge-orchestrator/main.py feature master  # 第一次运行
python ../../git-merge-orchestrator/main.py feature master  # 第二次运行（应该更快）

# 查看缓存状态（在主菜单中）
# "5. 系统管理" -> "b. 缓存管理" -> "a. 查看缓存状态"
```

### 5. 忽略规则测试

#### 场景设置
```bash
python test-scripts/setup_scenarios.py --scenario ignore-rules
cd test-repos/ignore-rules-test
```

#### 执行忽略规则测试
```bash
# 查看忽略规则文件
cat .merge_ignore

# 运行合并工具
python ../../git-merge-orchestrator/main.py ignore-test master

# 验证忽略功能：
# - .pyc 文件应该被忽略
# - .log 文件应该被忽略
# - 重要的 .py 和 .md 文件应该被处理
```

### 6. 多贡献者协作测试

#### 场景设置
```bash
python test-scripts/setup_scenarios.py --scenario multi-contributor
cd test-repos/multi-contributor-test
```

#### 执行协作测试
```bash
python ../../git-merge-orchestrator/main.py multi-team-feature master

# 验证专业分工：
# - Frontend-Dev 是否分配前端文件
# - Backend-Dev 是否分配后端API文件
# - DevOps-Engineer 是否分配基础设施文件
```

## 🔍 高级测试技巧

### 1. 自定义测试仓库

#### 创建特定类型的测试仓库
```bash
# 创建自定义测试仓库
python test-scripts/create_test_repo.py \
    --name "custom-test" \
    --type "complex" \
    --contributors "Alice,Bob,Charlie" \
    --files 50 \
    --branches "feature-a,feature-b"
```

#### 参数说明
```bash
--name          # 仓库名称
--type          # 仓库类型: simple, complex, multi-branch, large-scale
--contributors  # 贡献者列表（逗号分隔）
--files         # 文件数量
--branches      # 分支列表（逗号分隔）
```

### 2. 批量测试脚本

#### 创建批量测试脚本
```bash
#!/bin/bash
# batch_test.sh - 批量测试脚本

echo "🚀 开始批量测试..."

# 测试场景列表
scenarios=("merge-conflicts" "file-level-processing" "load-balancing" "ignore-rules")

for scenario in "${scenarios[@]}"; do
    echo "📋 测试场景: $scenario"
    
    # 设置场景
    python test-scripts/setup_scenarios.py --scenario "$scenario"
    
    if [ $? -eq 0 ]; then
        echo "✅ 场景 $scenario 设置成功"
        
        # 进入测试仓库
        cd "test-repos/${scenario}-test"
        
        # 运行自动化测试
        # 这里可以添加具体的测试命令
        echo "🔄 运行 $scenario 测试..."
        
        # 返回测试目录
        cd ../../
        
        echo "✅ 场景 $scenario 测试完成"
    else
        echo "❌ 场景 $scenario 设置失败"
    fi
    
    echo "------------------------"
done

echo "🎉 批量测试完成"
```

#### 运行批量测试
```bash
chmod +x batch_test.sh
./batch_test.sh
```

### 3. 测试结果验证

#### 验证合并结果
```bash
#!/bin/bash
# verify_merge.sh - 合并结果验证脚本

test_repo=$1
if [ -z "$test_repo" ]; then
    echo "用法: $0 <test_repo_name>"
    exit 1
fi

cd "test-repos/$test_repo"

echo "📊 验证合并结果..."

# 检查合并计划是否生成
if [ -f ".merge_work/merge_plan.json" ]; then
    echo "✅ 合并计划已生成"
else
    echo "❌ 合并计划未生成"
    exit 1
fi

# 检查脚本是否生成
script_count=$(find .merge_work/scripts/ -name "*.sh" 2>/dev/null | wc -l)
if [ "$script_count" -gt 0 ]; then
    echo "✅ 生成了 $script_count 个合并脚本"
else
    echo "❌ 未生成合并脚本"
    exit 1
fi

# 检查文件级处理（如果适用）
if grep -q '"processing_mode": "file_level"' .merge_work/merge_plan.json 2>/dev/null; then
    file_count=$(jq '.files | length' .merge_work/merge_plan.json 2>/dev/null)
    echo "✅ 文件级处理模式：处理 $file_count 个文件"
else
    group_count=$(jq '.groups | length' .merge_work/merge_plan.json 2>/dev/null)
    echo "✅ 组级处理模式：处理 $group_count 个组"
fi

echo "📋 验证完成"
```

#### 使用验证脚本
```bash
chmod +x verify_merge.sh
./verify_merge.sh merge-conflicts-test
```

## 🧹 清理和维护

### 清理测试环境
```bash
# 清理特定测试仓库
python test-scripts/cleanup.py --repo "merge-conflicts-test"

# 清理所有测试仓库
python test-scripts/cleanup.py --all

# 保留场景配置，只清理仓库
python test-scripts/cleanup.py --repos-only
```

### 重新生成测试数据
```bash
# 重新生成所有测试场景
python test-scripts/cleanup.py --all
python test-scripts/setup_scenarios.py --scenario all
```

## 📊 测试报告和分析

### 生成测试报告
```bash
# 创建测试报告生成脚本
cat > generate_test_report.py << 'EOF'
#!/usr/bin/env python3
"""
测试报告生成工具
"""
import json
import os
from pathlib import Path
from datetime import datetime

def generate_report():
    """生成测试报告"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "test_scenarios": {},
        "summary": {}
    }
    
    scenarios_dir = Path("scenarios")
    if not scenarios_dir.exists():
        print("❌ 场景配置目录不存在")
        return
    
    total_scenarios = 0
    successful_setups = 0
    
    for scenario_file in scenarios_dir.glob("*.json"):
        scenario_name = scenario_file.stem
        try:
            with open(scenario_file) as f:
                scenario_data = json.load(f)
            
            # 检查对应的测试仓库是否存在
            repo_path = Path(f"test-repos/{scenario_name}-test")
            repo_exists = repo_path.exists() and repo_path.is_dir()
            
            report["test_scenarios"][scenario_name] = {
                "description": scenario_data.get("description", ""),
                "type": scenario_data.get("type", ""),
                "repo_exists": repo_exists,
                "setup_successful": repo_exists
            }
            
            total_scenarios += 1
            if repo_exists:
                successful_setups += 1
                
        except Exception as e:
            print(f"❌ 处理场景 {scenario_name} 时出错: {e}")
    
    report["summary"] = {
        "total_scenarios": total_scenarios,
        "successful_setups": successful_setups,
        "setup_success_rate": f"{successful_setups/total_scenarios*100:.1f}%" if total_scenarios > 0 else "0%"
    }
    
    # 保存报告
    with open("test_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 打印摘要
    print("📊 测试环境报告")
    print("=" * 50)
    print(f"总场景数: {total_scenarios}")
    print(f"成功设置: {successful_setups}")
    print(f"成功率: {report['summary']['setup_success_rate']}")
    print("=" * 50)
    
    for name, data in report["test_scenarios"].items():
        status = "✅" if data["setup_successful"] else "❌"
        print(f"{status} {name}: {data['description']}")

if __name__ == "__main__":
    generate_report()
EOF

chmod +x generate_test_report.py
python generate_test_report.py
```

## 🎯 最佳实践

### 1. 测试前准备
- 确保 Git 配置正确（user.name 和 user.email）
- 备份重要数据
- 关闭可能影响性能的应用程序

### 2. 测试执行建议
- 从简单场景开始，逐步测试复杂场景
- 每个场景测试后进行结果验证
- 记录遇到的问题和解决方案

### 3. 问题诊断
```bash
# 查看详细日志
export GIT_MERGE_DEBUG=1
python ../../git-merge-orchestrator/main.py feature master

# 健康检查
cd ../../git-merge-orchestrator
python run_tests.py --health
```

### 4. 持续集成建议
```bash
# CI/CD 流水线中的测试命令示例
#!/bin/bash
set -e

echo "🚀 CI测试开始..."

# 进入测试目录
cd git-merge-orchestrator-test

# 设置关键测试场景
python test-scripts/setup_scenarios.py --scenario merge-conflicts
python test-scripts/setup_scenarios.py --scenario file-level-processing

# 运行健康检查
cd ../git-merge-orchestrator
python run_tests.py --health

# 基础功能测试
cd ../git-merge-orchestrator-test/test-repos/merge-conflicts-test
timeout 60s python ../../git-merge-orchestrator/main.py feature-1 master --auto-mode

echo "✅ CI测试完成"
```

## 🆘 故障排除

### 常见问题

#### 1. 场景设置失败
```bash
# 问题：权限不足
sudo chown -R $USER:$USER ../git-merge-orchestrator-test

# 问题：Git配置缺失
git config --global user.name "Test User"
git config --global user.email "test@example.com"
```

#### 2. 测试仓库损坏
```bash
# 清理并重新创建
python test-scripts/cleanup.py --repo "damaged-repo-name"
python test-scripts/setup_scenarios.py --scenario "corresponding-scenario"
```

#### 3. 性能测试超时
```bash
# 减少测试规模
python test-scripts/create_test_repo.py \
    --name "small-performance-test" \
    --type "complex" \
    --files 50  # 减少文件数量
```

## 📞 支持和反馈

### 获取帮助
```bash
# 查看脚本帮助
python test-scripts/setup_scenarios.py --help
python test-scripts/create_test_repo.py --help
python test-scripts/cleanup.py --help

# 主程序帮助
cd ../git-merge-orchestrator
python main.py --help
```

### 报告问题
如果遇到问题，请提供：
1. 错误日志和堆栈跟踪
2. 使用的测试场景和命令
3. 系统环境信息
4. 期望的行为描述

---

**🎉 通过系统性的测试，确保 Git Merge Orchestrator 在各种场景下都能稳定可靠地工作！**

最后更新：2025-08-06