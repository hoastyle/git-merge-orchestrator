#!/usr/bin/env python3
"""
测试未分配文件查询功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from utils.file_helper import FileHelper
from core.query_system import QuerySystem


def test_unassigned_query():
    """测试未分配文件查询功能"""
    print("🧪 测试未分配文件查询功能")
    print("=" * 50)

    # 创建测试计划数据
    test_plan = {
        "source_branch": "feature/test",
        "target_branch": "main", 
        "groups": [
            {
                "name": "group_1",
                "files": ["src/main.py", "src/utils.py"],
                "assignee": "Alice Johnson",
                "status": "assigned",
                "assignment_reason": "基于文件贡献度直接分配"
            },
            {
                "name": "group_2",
                "files": ["tests/test_main.py", "tests/test_utils.py"], 
                "assignee": "",  # 未分配
                "status": "pending",
                "assignment_reason": "主要贡献者Bob Smith近3个月无活跃提交，已自动排除"
            },
            {
                "name": "group_3",
                "files": ["docs/README.md"],
                "assignee": "",  # 未分配
                "status": "pending", 
                "assignment_reason": "无法确定主要贡献者"
            },
            {
                "name": "group_4",
                "files": ["config/settings.json"],
                "assignee": "Charlie Brown",
                "status": "assigned",
                "assignment_reason": "手动分配"
            }
        ]
    }

    # 保存测试计划
    file_helper = FileHelper(".")
    file_helper.save_plan(test_plan)

    # 创建查询系统
    query_system = QuerySystem(file_helper)

    # 测试1: 反向查询未分配文件
    print("\n🔍 测试1: 查询未分配文件")
    result = query_system.reverse_query({
        "unassigned": True,
        "problematic": True
    })
    
    print(f"查询结果:")
    unassigned_files = result["results"]["unassigned_files"]
    print(f"  未分配文件数量: {len(unassigned_files)}")
    print(f"  未分配文件列表: {unassigned_files}")
    
    problematic_groups = result["results"]["problematic_groups"]
    print(f"  有问题的组数量: {len(problematic_groups)}")
    
    # 测试2: 按状态查询
    print("\n🔍 测试2: 按状态查询 (pending)")
    status_result = query_system.query_by_status("pending", include_details=True)
    print(f"Pending状态组数: {status_result['summary']['total_groups']}")
    print(f"Pending状态文件数: {status_result['summary']['total_files']}")
    
    # 测试3: 按负责人查询
    print("\n🔍 测试3: 按负责人查询")
    assignee_result = query_system.query_by_assignee("Alice", fuzzy=True)
    print(f"Alice的分配结果: {len(assignee_result['results'])} 个组")
    
    # 验证结果
    expected_unassigned = ["tests/test_main.py", "tests/test_utils.py", "docs/README.md"]
    actual_unassigned = unassigned_files
    
    if set(expected_unassigned) == set(actual_unassigned):
        print("\n✅ 测试通过: 未分配文件查询结果正确")
    else:
        print("\n❌ 测试失败: 查询结果不匹配")
        print(f"   期望: {expected_unassigned}")
        print(f"   实际: {actual_unassigned}")
    
    # 清理测试数据
    try:
        import os
        os.remove(".merge_work/merge_plan.json")
        print("\n🧹 测试数据已清理")
    except:
        pass


if __name__ == "__main__":
    test_unassigned_query()