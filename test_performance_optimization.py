#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能优化测试脚本 - 验证v2.3优化架构的性能提升
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.git_operations import GitOperations  
from core.enhanced_task_assigner import EnhancedTaskAssigner
from core.enhanced_contributor_analyzer import EnhancedContributorAnalyzer


def create_mock_plan_with_real_files(git_ops, num_files=100):
    """创建包含真实文件的模拟计划"""
    import subprocess
    import random
    
    try:
        # 获取Git仓库中的真实文件列表
        result = subprocess.run(['git', 'ls-files'], 
                              capture_output=True, text=True, cwd='.')
        if result.returncode != 0:
            raise Exception("无法获取Git文件列表")
        
        all_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
        
        # 过滤Python文件和其他代码文件
        code_files = [f for f in all_files if f.endswith(('.py', '.js', '.java', '.cpp', '.c', '.h'))]
        
        if len(code_files) < 10:
            # 如果代码文件不足，使用所有文件
            code_files = all_files
        
        # 随机选择文件（如果文件数量足够）
        selected_files = code_files[:num_files] if len(code_files) >= num_files else code_files * ((num_files // len(code_files)) + 1)
        selected_files = selected_files[:num_files]
        
        # 创建文件计划
        files = []
        for file_path in selected_files:
            files.append({
                'path': file_path,
                'status': 'pending', 
                'assignee': '',
                'assignment_reason': ''
            })
        
        return {
            'processing_mode': 'file_level',
            'files': files,
            'metadata': {
                'total_files': len(files),
                'real_files': len(code_files),
                'created': datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        print(f"⚠️ 无法创建真实文件计划: {e}")
        # 回退到使用实际存在的核心文件
        core_files = [
            'main.py',
            'core/git_operations.py',
            'core/enhanced_task_assigner.py',
            'core/enhanced_contributor_analyzer.py',
            'config.py',
            'git_merge_orchestrator.py'
        ]
        
        files = []
        for i, file_path in enumerate(core_files * (num_files // len(core_files) + 1)):
            if len(files) >= num_files:
                break
            files.append({
                'path': file_path,
                'status': 'pending',
                'assignee': '',
                'assignment_reason': ''
            })
        
        return {
            'processing_mode': 'file_level',
            'files': files[:num_files],
            'metadata': {
                'total_files': len(files[:num_files]),
                'created': datetime.now().isoformat(),
                'fallback': True
            }
        }


def test_performance_optimization():
    """测试性能优化效果"""
    print("🚀 开始性能优化测试...")
    print("=" * 60)
    
    try:
        # 初始化Git操作
        git_ops = GitOperations(".")
        print("✅ Git操作模块初始化完成")
        
        # 初始化增强任务分配器
        enhanced_assigner = EnhancedTaskAssigner(git_ops)
        
        # 检查增强功能是否启用
        if not enhanced_assigner.is_enhanced_enabled():
            print("❌ 增强功能未启用，请检查配置")
            return
        
        print(f"✅ 增强功能已启用")
        print(f"📊 测试配置:")
        print(f"  • 架构版本: v2.3 优化架构")
        print(f"  • 处理模式: file_level")
        print(f"  • 测试文件数: 100个文件")
        print()
        
        # 创建测试计划（使用真实文件）
        print("📝 创建测试计划...")
        test_plan = create_mock_plan_with_real_files(git_ops, 100)
        print(f"✅ 测试计划创建完成: {len(test_plan['files'])} 个文件")
        if 'real_files' in test_plan['metadata']:
            print(f"📁 仓库中代码文件总数: {test_plan['metadata']['real_files']}")
        if 'fallback' in test_plan['metadata']:
            print("⚠️ 使用核心文件回退模式")
        print()
        
        # 执行性能测试
        print("⚡ 开始增强任务分配性能测试...")
        start_time = time.time()
        
        success_count, failed_count, assignment_stats = enhanced_assigner.enhanced_auto_assign_tasks(
            test_plan,
            exclude_authors=[],
            max_tasks_per_person=50,
            enable_line_analysis=True,
            include_fallback=True
        )
        
        total_time = time.time() - start_time
        
        print()
        print("=" * 60)
        print("🎯 性能测试结果:")
        print(f"✅ 分配成功: {success_count} 个文件")
        print(f"❌ 分配失败: {failed_count} 个文件") 
        print(f"⏱️  总执行时间: {total_time:.2f}s")
        print(f"📊 平均处理时间: {(total_time / (success_count + failed_count)) * 1000:.1f}ms/文件")
        
        # 显示架构版本信息
        if 'architecture_version' in assignment_stats:
            print(f"🏗️  架构版本: {assignment_stats['architecture_version']}")
        
        # 显示性能分解
        if 'performance_breakdown' in assignment_stats:
            breakdown = assignment_stats['performance_breakdown']
            print(f"🔍 性能分解:")
            print(f"  • 分析阶段: {breakdown.get('analysis_time', 0):.2f}s")
            print(f"  • 决策计算: {breakdown.get('decision_time', 0):.2f}s")
            print(f"  • 负载均衡: {breakdown.get('assignment_time', 0):.2f}s")
            print(f"  • 结果应用: {breakdown.get('application_time', 0):.2f}s")
        
        # 性能评估
        print()
        print("📈 性能评估:")
        avg_time_ms = (total_time / (success_count + failed_count)) * 1000
        if avg_time_ms < 10:
            print(f"🏆 优秀: 平均处理时间 {avg_time_ms:.1f}ms/文件")
        elif avg_time_ms < 50:
            print(f"✅ 良好: 平均处理时间 {avg_time_ms:.1f}ms/文件")
        else:
            print(f"⚠️  需要改进: 平均处理时间 {avg_time_ms:.1f}ms/文件")
        
        # 检查日志文件
        print()
        print("📋 性能日志:")
        log_files = [
            '.merge_work/enhanced_performance_log.json',
            '.merge_work/enhanced_analysis_performance.json', 
            '.merge_work/decision_performance.json',
            '.merge_work/load_balance_performance.json'
        ]
        
        for log_file in log_files:
            if Path(log_file).exists():
                print(f"✅ {log_file} 已生成")
            else:
                print(f"❌ {log_file} 未生成")
        
        print()
        print("🎉 性能优化测试完成！")
        
        # 性能对比提示
        print()
        print("📊 性能对比参考:")
        print("  • 优化前 (v2.2): ~280-300ms/文件 (28.5s for 1000+ files)")
        print("  • 优化后 (v2.3): <50ms/文件 (预期90%+ 性能提升)")
        print("  • 目标性能: <10ms/文件 (优秀级别)")
        
    except Exception as e:
        print(f"❌ 测试执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_performance_optimization()