#!/usr/bin/env python3
"""
Git Merge Orchestrator - 性能测试脚本
测试优化后的批量处理和缓存系统性能
"""

import sys
import time
from pathlib import Path
import tempfile
import os
import subprocess

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from core.git_operations import GitOperations
from core.optimized_contributor_analyzer import OptimizedContributorAnalyzer
from utils.smart_cache import SmartCacheManager


def create_test_repo():
    """创建测试仓库"""
    temp_dir = tempfile.mkdtemp(prefix="perf_test_")
    os.chdir(temp_dir)

    # 初始化Git仓库
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)

    # 创建测试文件
    test_files = []
    for i in range(100):  # 创建100个测试文件
        dir_name = f"dir_{i // 10}"
        os.makedirs(dir_name, exist_ok=True)

        file_path = f"{dir_name}/file_{i}.py"
        with open(file_path, "w") as f:
            f.write(
                f"""# Test file {i}
def test_function_{i}():
    '''Test function {i}'''
    return {i}

class TestClass{i}:
    '''Test class {i}'''
    def method(self):
        return {i}
"""
            )
        test_files.append(file_path)

    # 创建多个提交来模拟历史
    authors = ["Alice", "Bob", "Charlie", "David", "Eve"]

    for commit_idx in range(20):  # 创建20个提交
        # 随机修改一些文件
        import random

        files_to_modify = random.sample(test_files, min(20, len(test_files)))

        for file_path in files_to_modify:
            with open(file_path, "a") as f:
                f.write(f"\n# Commit {commit_idx} modification\n")

        subprocess.run(["git", "add", "."], check=True)

        author = random.choice(authors)
        subprocess.run(
            [
                "git",
                "-c",
                f"user.name={author}",
                "-c",
                f"user.email={author.lower()}@example.com",
                "commit",
                "-m",
                f"Commit {commit_idx} by {author}",
            ],
            check=True,
            capture_output=True,
        )

    print(f"✅ 测试仓库创建完成: {temp_dir}")
    return temp_dir, test_files


def test_batch_processing_performance():
    """测试批量处理性能"""
    print("\n🚀 开始性能测试...")

    # 创建测试仓库
    repo_path, test_files = create_test_repo()

    try:
        git_ops = GitOperations(repo_path)
        analyzer = OptimizedContributorAnalyzer(git_ops)

        print(f"📊 测试文件数量: {len(test_files)}")

        # 测试1: 传统单文件处理
        print("\n🔍 测试1: 传统单文件处理")
        start_time = time.time()

        traditional_results = {}
        for i, file_path in enumerate(test_files[:20]):  # 只测试前20个文件
            contributors = git_ops.get_all_contributors(file_path)
            traditional_results[file_path] = contributors
            if i % 5 == 0:
                print(f"  处理进度: {i+1}/20")

        traditional_time = time.time() - start_time
        print(f"✅ 传统方法完成，耗时: {traditional_time:.2f}秒")

        # 测试2: 批量处理
        print("\n⚡ 测试2: 批量处理")
        start_time = time.time()

        batch_results = git_ops.get_contributors_batch(test_files[:20])

        batch_time = time.time() - start_time
        print(f"✅ 批量方法完成，耗时: {batch_time:.2f}秒")

        # 性能对比
        if batch_time > 0:
            speedup = traditional_time / batch_time
            print(f"\n📈 性能对比:")
            print(f"  传统方法: {traditional_time:.2f}秒")
            print(f"  批量方法: {batch_time:.2f}秒")
            print(f"  性能提升: {speedup:.2f}x")

            if speedup > 1.5:
                print("🎉 批量处理性能优化显著！")
            else:
                print("⚠️ 批量处理优化效果有限")

        # 测试3: 智能缓存效果
        print("\n🧠 测试3: 智能缓存效果")
        cache_manager = SmartCacheManager(repo_path)

        # 第一次访问（缓存未命中）
        start_time = time.time()
        for file_path in test_files[:10]:
            result = cache_manager.get("test_contributors", file_path)
            if result is None:
                contributors = git_ops.get_all_contributors(file_path)
                cache_manager.put("test_contributors", file_path, contributors)

        first_access_time = time.time() - start_time

        # 第二次访问（缓存命中）
        start_time = time.time()
        cached_hits = 0
        for file_path in test_files[:10]:
            result = cache_manager.get("test_contributors", file_path)
            if result is not None:
                cached_hits += 1

        second_access_time = time.time() - start_time

        print(f"  第一次访问（建立缓存）: {first_access_time:.2f}秒")
        print(f"  第二次访问（缓存命中）: {second_access_time:.2f}秒")
        print(f"  缓存命中率: {cached_hits}/10 ({cached_hits*10}%)")

        if cached_hits > 0:
            cache_speedup = first_access_time / max(second_access_time, 0.001)
            print(f"  缓存加速比: {cache_speedup:.2f}x")

        # 显示缓存统计
        stats = cache_manager.get_stats()
        print(f"\n📊 缓存统计: {stats}")

        # 测试4: 大批量处理
        if len(test_files) >= 50:
            print("\n🏭 测试4: 大批量处理（50个文件）")
            start_time = time.time()

            large_batch_results = git_ops.get_contributors_batch_optimized(
                test_files[:50], max_commits=100
            )

            large_batch_time = time.time() - start_time
            print(f"✅ 大批量处理完成，耗时: {large_batch_time:.2f}秒")
            print(f"  平均每文件: {large_batch_time/50:.3f}秒")

    except Exception as e:
        print(f"❌ 性能测试出错: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # 清理测试环境
        os.chdir("/")
        import shutil

        try:
            shutil.rmtree(repo_path)
            print(f"🧹 测试环境已清理: {repo_path}")
        except:
            print(f"⚠️ 清理测试环境失败: {repo_path}")


def main():
    """主函数"""
    print("🔬 Git Merge Orchestrator 性能测试")
    print("=" * 50)

    test_batch_processing_performance()

    print("\n" + "=" * 50)
    print("✅ 性能测试完成")


if __name__ == "__main__":
    main()
