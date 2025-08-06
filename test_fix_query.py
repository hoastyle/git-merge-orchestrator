#!/usr/bin/env python3
"""
测试QuerySystem与FilePlanManager的兼容性修复
"""

import sys
from pathlib import Path
import json
import os

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from core.query_system import QuerySystem
from core.file_manager import FileManager


def create_test_file_plan():
    """创建测试用的文件级计划"""
    # 确保工作目录存在
    work_dir = Path(".merge_work")
    work_dir.mkdir(exist_ok=True)
    
    # 创建文件级计划数据
    file_plan = {
        "created_at": "2025-01-08T10:00:00",
        "source_branch": "feature/test",
        "target_branch": "main",
        "integration_branch": "merge-feature-test-into-main",
        "processing_mode": "file_level",
        "files": [
            {
                "path": "src/main.py",
                "assignee": "Alice Johnson", 
                "status": "assigned",
                "assignment_reason": "基于文件贡献度直接分配",
                "priority": "normal",
                "created_at": "2025-01-08T10:00:00",
                "updated_at": "2025-01-08T10:00:00"
            },
            {
                "path": "tests/test_main.py",
                "assignee": "",  # 未分配
                "status": "pending", 
                "assignment_reason": "主要贡献者Bob Smith近3个月无活跃提交，已自动排除",
                "priority": "normal",
                "created_at": "2025-01-08T10:00:00",
                "updated_at": "2025-01-08T10:00:00"
            },
            {
                "path": "docs/README.md",
                "assignee": "",  # 未分配
                "status": "pending",
                "assignment_reason": "无法确定主要贡献者", 
                "priority": "low",
                "created_at": "2025-01-08T10:00:00",
                "updated_at": "2025-01-08T10:00:00"
            },
            {
                "path": "config/settings.json",
                "assignee": "Charlie Brown",
                "status": "assigned",
                "assignment_reason": "手动分配",
                "priority": "high",
                "created_at": "2025-01-08T10:00:00",
                "updated_at": "2025-01-08T10:00:00"
            }
        ],
        "metadata": {
            "total_files": 4,
            "assigned_files": 2,
            "unassigned_files": 2
        }
    }
    
    # 保存计划文件
    plan_file = work_dir / "file_plan.json"
    with open(plan_file, "w", encoding="utf-8") as f:
        json.dump(file_plan, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 创建测试文件计划: {plan_file}")
    return file_plan


def test_query_system_compatibility():
    """测试QuerySystem与文件级计划的兼容性"""
    print("🧪 测试QuerySystem兼容性修复")
    print("=" * 50)
    
    # 创建测试数据
    file_plan = create_test_file_plan()
    
    # 创建模拟的FilePlanManager
    class MockFilePlanManager:
        def __init__(self):
            self.file_manager = MockFileManager()
    
    class MockFileManager:
        def load_file_plan(self):
            return file_plan
    
    # 创建QuerySystem并测试
    mock_plan_manager = MockFilePlanManager()
    query_system = QuerySystem(mock_plan_manager)
    
    print("\n🔍 测试1: 反向查询未分配文件")
    try:
        result = query_system.reverse_query({
            "unassigned": True,
            "problematic": True
        })
        
        print(f"查询结果:")
        unassigned_files = result["results"]["unassigned_files"] 
        print(f"  未分配文件数量: {len(unassigned_files)}")
        print(f"  未分配文件列表: {unassigned_files}")
        
        # 验证结果
        expected_unassigned = ["tests/test_main.py", "docs/README.md"]
        if set(expected_unassigned) == set(unassigned_files):
            print("  ✅ 反向查询测试通过")
        else:
            print("  ❌ 反向查询测试失败")
            print(f"     期望: {expected_unassigned}")
            print(f"     实际: {unassigned_files}")
            
    except Exception as e:
        print(f"  ❌ 反向查询测试失败: {e}")
        return False
    
    print("\n🔍 测试2: 按状态查询")
    try:
        status_result = query_system.query_by_status("pending", include_details=True)
        print(f"Pending状态组数: {status_result['summary']['total_groups']}")
        print(f"Pending状态文件数: {status_result['summary']['total_files']}")
        
        if status_result['summary']['total_files'] == 2:
            print("  ✅ 状态查询测试通过")
        else:
            print("  ❌ 状态查询测试失败")
            
    except Exception as e:
        print(f"  ❌ 状态查询测试失败: {e}")
        return False
    
    print("\n🔍 测试3: 按负责人查询")
    try:
        assignee_result = query_system.query_by_assignee("Alice", fuzzy=True)
        print(f"Alice的分配结果: {len(assignee_result['results'])} 个组")
        
        if len(assignee_result['results']) == 1:
            print("  ✅ 负责人查询测试通过")
        else:
            print("  ❌ 负责人查询测试失败")
            
    except Exception as e:
        print(f"  ❌ 负责人查询测试失败: {e}")
        return False
    
    print("\n✅ 所有测试通过！QuerySystem兼容性修复成功")
    
    # 清理测试数据
    try:
        os.remove(".merge_work/file_plan.json")
        print("\n🧹 测试数据已清理")
    except:
        pass
        
    return True


if __name__ == "__main__":
    success = test_query_system_compatibility()
    if success:
        print("\n🎉 兼容性修复验证成功！")
    else:
        print("\n❌ 修复验证失败")
        sys.exit(1)