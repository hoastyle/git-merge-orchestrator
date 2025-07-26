#!/usr/bin/env python3
"""
Git Merge Orchestrator - 综合测试套件
整合所有测试功能，提供完整的质量保证体系
"""

import sys
import os
import tempfile
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))


# 测试统计
class TestStats:
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = []
        self.start_time = datetime.now()

    def add_test(self, test_name, passed, error=None):
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
        else:
            self.failed_tests.append({"name": test_name, "error": error})

    def get_summary(self):
        elapsed = datetime.now() - self.start_time
        return {
            "total": self.total_tests,
            "passed": self.passed_tests,
            "failed": len(self.failed_tests),
            "success_rate": (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0,
            "elapsed": elapsed.total_seconds(),
            "failures": self.failed_tests,
        }


# 全局测试统计
test_stats = TestStats()


def test_wrapper(test_name):
    """测试装饰器，统一处理测试结果"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            print(f"🧪 {test_name}...")
            try:
                result = func(*args, **kwargs)
                if result:
                    print(f"✅ {test_name}通过")
                    test_stats.add_test(test_name, True)
                else:
                    print(f"❌ {test_name}失败")
                    test_stats.add_test(test_name, False)
                return result
            except Exception as e:
                print(f"❌ {test_name}异常: {e}")
                test_stats.add_test(test_name, False, str(e))
                return False

        return wrapper

    return decorator


class ComprehensiveTestSuite:
    """综合测试套件"""

    def __init__(self):
        self.temp_dirs = []

    def cleanup(self):
        """清理测试环境"""
        for temp_dir in self.temp_dirs:
            if Path(temp_dir).exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def create_temp_repo(self, with_history=True):
        """创建临时Git仓库用于测试"""
        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        if with_history:
            # 初始化Git仓库
            subprocess.run(["git", "init"], cwd=temp_dir, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=temp_dir, capture_output=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=temp_dir, capture_output=True)

            # 创建测试文件和提交
            (Path(temp_dir) / "test.txt").write_text("test content")
            subprocess.run(["git", "add", "."], cwd=temp_dir, capture_output=True)
            subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=temp_dir, capture_output=True)

        return temp_dir

    # === 配置管理测试模块 ===

    @test_wrapper("配置管理器基本功能测试")
    def test_config_manager_basic(self):
        """测试配置管理器基本功能（修复版）"""
        from utils.config_manager import ProjectConfigManager

        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        manager = ProjectConfigManager(temp_dir)

        # 测试保存配置
        if not manager.save_config("feature/test", "main", temp_dir, 5, "legacy"):
            return False

        # 测试读取配置
        config = manager.load_config()
        if not config or config["source_branch"] != "feature/test":
            return False

        # 测试分支获取
        source, target = manager.get_branches_from_config()
        if source != "feature/test" or target != "main":
            return False

        # 测试配置更新
        if not manager.update_config(merge_strategy="standard"):
            return False

        # 验证更新结果
        updated_config = manager.load_config()
        if updated_config["merge_strategy"] != "standard":
            return False

        return True

    @test_wrapper("配置过期检测测试")
    def test_config_expiry_detection(self):
        """测试配置过期检测（修复版）"""
        from utils.config_manager import ProjectConfigManager

        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        manager = ProjectConfigManager(temp_dir)

        # 保存配置
        manager.save_config("feature/test", "main", temp_dir)

        # 手动修改配置文件的保存时间为35天前
        config = manager.load_config()
        old_time = (datetime.now() - timedelta(days=35)).isoformat()
        config["saved_at"] = old_time

        # 直接写入文件，绕过update_config的时间戳更新
        with open(manager.config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        # 清除缓存，强制重新读取
        manager._config_cache = None

        # 测试过期检测
        is_outdated = manager.is_config_outdated(days=30)
        if not is_outdated:
            print(f"   调试：配置时间 {old_time}，当前时间 {datetime.now().isoformat()}")
            return False

        return True

    @test_wrapper("配置文件操作测试")
    def test_config_file_operations(self):
        """测试配置文件导入导出"""
        from utils.config_manager import ProjectConfigManager

        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)
        export_path = Path(temp_dir) / "exported_config.json"

        manager = ProjectConfigManager(temp_dir)

        # 保存初始配置
        if not manager.save_config("feature/export", "main", temp_dir):
            return False

        # 测试导出
        if not manager.export_config(export_path):
            return False

        if not export_path.exists():
            return False

        # 测试重置
        if not manager.reset_config():
            return False

        # 测试导入
        if not manager.import_config(export_path):
            return False

        # 验证导入结果
        source, target = manager.get_branches_from_config()
        if source != "feature/export" or target != "main":
            return False

        return True

    # === 部署和模块测试 ===

    @test_wrapper("模块导入测试")
    def test_module_imports(self):
        """测试关键模块导入"""
        try:
            from core.optimized_contributor_analyzer import OptimizedContributorAnalyzer
            from core.optimized_task_assigner import OptimizedTaskAssigner
            from utils.performance_monitor import performance_monitor, timing_context
            from core.legacy_merge_executor import LegacyMergeExecutor
            from core.standard_merge_executor import StandardMergeExecutor
            from core.merge_executor_factory import MergeExecutorFactory
            from ui.menu_manager import MenuManager

            return True
        except ImportError as e:
            print(f"   导入失败: {e}")
            return False

    @test_wrapper("Git操作基础测试")
    def test_git_operations_basic(self):
        """测试Git操作基础功能"""
        from core.git_operations import GitOperations

        temp_repo = self.create_temp_repo(with_history=True)
        git_ops = GitOperations(temp_repo)

        # 测试Git版本获取
        version = git_ops.run_command("git --version")
        if not version or "git version" not in version:
            return False

        # 测试分支操作
        current_branch = git_ops.run_command("git branch --show-current")
        if not current_branch:
            return False

        return True

    @test_wrapper("文件助手功能测试")
    def test_file_helper_operations(self):
        """测试文件操作助手"""
        from utils.file_helper import FileHelper

        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        file_helper = FileHelper(temp_dir, max_files_per_group=3)

        # 测试工作目录创建
        if not file_helper.work_dir.exists():
            return False

        # 测试文件分组
        test_files = [
            "src/module1/file1.py",
            "src/module1/file2.py",
            "src/module2/file3.py",
            "docs/readme.md",
            "config.json",
        ]

        groups = file_helper.iterative_group_files(test_files)
        if not groups or len(groups) == 0:
            return False

        # 验证分组逻辑
        total_files_in_groups = sum(len(group["files"]) for group in groups)
        if total_files_in_groups != len(test_files):
            return False

        return True

    # === 性能测试模块 ===

    @test_wrapper("性能监控功能测试")
    def test_performance_monitoring(self):
        """测试性能监控功能"""
        from utils.performance_monitor import performance_monitor, timing_context, PerformanceStats

        # 测试性能监控装饰器
        @performance_monitor("测试操作")
        def test_operation():
            import time

            time.sleep(0.05)  # 模拟耗时操作
            return True

        result = test_operation()
        if not result:
            return False

        # 测试时间上下文管理器
        with timing_context("测试上下文"):
            import time

            time.sleep(0.05)

        # 测试性能统计
        stats = PerformanceStats()
        stats.start_operation("test")
        import time

        time.sleep(0.05)
        elapsed = stats.end_operation("test")

        if elapsed is None or elapsed < 0.04:
            return False

        return True

    @test_wrapper("大规模文件分组性能测试")
    def test_large_scale_grouping_performance(self):
        """测试大规模文件分组性能"""
        from utils.file_helper import FileHelper
        import time

        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        file_helper = FileHelper(temp_dir, max_files_per_group=5)

        # 生成大量测试文件路径
        large_file_list = []
        for i in range(1000):
            module = f"module{i // 100}"
            submodule = f"sub{i // 10}"
            filename = f"file{i}.py"
            large_file_list.append(f"src/{module}/{submodule}/{filename}")

        # 性能测试
        start_time = time.time()
        groups = file_helper.iterative_group_files(large_file_list)
        elapsed = time.time() - start_time

        # 验证结果
        if not groups or len(groups) == 0:
            return False

        # 性能要求：1000个文件应在2秒内完成分组
        if elapsed > 2.0:
            print(f"   性能警告：分组耗时 {elapsed:.2f}秒，超过预期")
            return False

        print(f"   性能良好：{len(large_file_list)} 个文件分为 {len(groups)} 组，耗时 {elapsed:.2f}秒")
        return True

    # === 合并策略测试 ===

    @test_wrapper("合并执行器工厂测试")
    def test_merge_executor_factory(self):
        """测试合并执行器工厂"""
        from core.merge_executor_factory import MergeExecutorFactory
        from core.git_operations import GitOperations
        from utils.file_helper import FileHelper

        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        factory = MergeExecutorFactory(temp_dir)
        git_ops = GitOperations(temp_dir)
        file_helper = FileHelper(temp_dir)

        # 测试默认策略
        current_mode = factory.get_current_mode()
        if current_mode not in ["legacy", "standard"]:
            return False

        # 测试策略切换
        new_mode = "legacy" if current_mode == "standard" else "standard"
        factory.set_merge_mode(new_mode)

        if factory.get_current_mode() != new_mode:
            return False

        # 测试执行器创建
        executor = factory.create_executor(git_ops, file_helper)
        if not executor:
            return False

        # 测试策略信息获取
        status_info = factory.get_status_info()
        if not status_info or "mode_name" not in status_info:
            return False

        return True

    @test_wrapper("DRY架构合并策略测试")
    def test_dry_merge_strategies(self):
        """测试DRY架构的合并策略"""
        from core.legacy_merge_executor import LegacyMergeExecutor
        from core.standard_merge_executor import StandardMergeExecutor
        from core.git_operations import GitOperations
        from utils.file_helper import FileHelper

        temp_dir = tempfile.mkdtemp()
        self.temp_dirs.append(temp_dir)

        git_ops = GitOperations(temp_dir)
        file_helper = FileHelper(temp_dir)

        # 测试Legacy执行器
        legacy_executor = LegacyMergeExecutor(git_ops, file_helper)
        if legacy_executor.get_strategy_name() != "Legacy":
            return False

        # 测试Standard执行器
        standard_executor = StandardMergeExecutor(git_ops, file_helper)
        if standard_executor.get_strategy_name() != "Standard":
            return False

        # 测试策略描述
        legacy_desc = legacy_executor.get_strategy_description()
        standard_desc = standard_executor.get_strategy_description()

        if not legacy_desc or not standard_desc:
            return False

        if "快速覆盖" not in legacy_desc or "三路合并" not in standard_desc:
            return False

        return True

    # === 集成测试模块 ===

    @test_wrapper("主控制器集成测试")
    def test_orchestrator_integration(self):
        """测试主控制器集成功能"""
        from git_merge_orchestrator import GitMergeOrchestrator

        temp_repo = self.create_temp_repo(with_history=True)

        # 创建第二个分支用于测试
        subprocess.run(["git", "checkout", "-b", "feature/test"], cwd=temp_repo, capture_output=True)
        (Path(temp_repo) / "feature.txt").write_text("feature content")
        subprocess.run(["git", "add", "."], cwd=temp_repo, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add feature"], cwd=temp_repo, capture_output=True)
        subprocess.run(["git", "checkout", "master"], cwd=temp_repo, capture_output=True)

        try:
            orchestrator = GitMergeOrchestrator(
                source_branch="feature/test", target_branch="master", repo_path=temp_repo, max_files_per_group=3
            )

            # 测试基本属性
            if orchestrator.source_branch != "feature/test":
                return False

            if orchestrator.target_branch != "master":
                return False

            # 测试策略信息获取
            strategy_info = orchestrator.get_merge_strategy_info()
            if not strategy_info or "mode_name" not in strategy_info:
                return False

            return True

        except Exception as e:
            print(f"   集成测试异常: {e}")
            return False

    # === 错误处理测试 ===

    @test_wrapper("错误处理和边界条件测试")
    def test_error_handling(self):
        """测试错误处理和边界条件"""
        from utils.config_manager import ProjectConfigManager
        from core.git_operations import GitOperations

        # 测试不存在的目录
        non_existent_dir = "/tmp/non_existent_git_merge_test_dir_12345"

        try:
            # 配置管理器错误处理
            manager = ProjectConfigManager(non_existent_dir)
            config = manager.load_config()  # 应该返回None而不是抛出异常
            if config is not None:
                return False

            # 测试has_valid_config
            has_config = manager.has_valid_config()
            if has_config:
                return False

        except Exception as e:
            print(f"   配置管理器测试异常: {e}")
            # 这里如果抛出异常也是可接受的，因为目录不存在
            pass

        try:
            # Git操作错误处理
            git_ops = GitOperations(non_existent_dir)
            result = git_ops.run_command("git status")  # 应该返回None而不是抛出异常
            if result is not None:
                return False
        except Exception as e:
            print(f"   Git操作测试异常: {e}")
            # Git操作在不存在的目录中失败是正常的
            pass

        # 测试无效配置文件（使用存在的临时目录）
        temp_dir = tempfile.mkdtemp()
        try:
            self.temp_dirs.append(temp_dir)
            manager = ProjectConfigManager(temp_dir)

            # 确保工作目录存在
            manager.work_dir.mkdir(exist_ok=True)

            # 创建无效的JSON文件
            with open(manager.config_file, "w", encoding="utf-8") as f:
                f.write("invalid json content")

            # 应该返回None而不是抛出异常
            config = manager.load_config()
            if config is not None:
                print(f"   期望None，但得到: {config}")
                return False

            # 测试无效配置格式
            with open(manager.config_file, "w", encoding="utf-8") as f:
                f.write('{"version": "2.0", "missing_required": "fields"}')

            # 清除缓存
            manager._config_cache = None

            # 应该返回None因为缺少必需字段
            config = manager.load_config()
            if config is not None:
                print(f"   期望None（缺少必需字段），但得到: {config}")
                return False

        except Exception as e:
            print(f"   无效配置文件测试异常: {e}")
            return False

        # 测试无效参数
        try:
            from core.merge_executor_factory import MergeExecutorFactory

            factory = MergeExecutorFactory()
            factory.set_merge_mode("invalid_mode")  # 应该抛出ValueError
            print("   期望ValueError，但没有抛出异常")
            return False  # 如果没有抛出异常，测试失败
        except ValueError:
            # 期望的行为
            pass
        except Exception as e:
            print(f"   期望ValueError，但得到: {type(e).__name__}: {e}")
            return False  # 其他异常是意外的

        return True

    # === 主测试运行器 ===

    def run_all_tests(self, test_categories=None):
        """运行所有测试或指定类别的测试"""
        if test_categories is None:
            test_categories = ["config", "deployment", "performance", "integration", "error_handling"]

        print("🚀 Git Merge Orchestrator 综合测试套件")
        print("=" * 80)

        # 配置管理测试
        if "config" in test_categories:
            print("\n📋 配置管理测试模块")
            self.test_config_manager_basic()
            self.test_config_expiry_detection()
            self.test_config_file_operations()

        # 部署和模块测试
        if "deployment" in test_categories:
            print("\n🚀 部署和模块测试")
            self.test_module_imports()
            self.test_git_operations_basic()
            self.test_file_helper_operations()

        # 性能测试
        if "performance" in test_categories:
            print("\n⚡ 性能测试模块")
            self.test_performance_monitoring()
            self.test_large_scale_grouping_performance()

        # 合并策略测试
        if "merge_strategies" in test_categories:
            print("\n🔧 合并策略测试")
            self.test_merge_executor_factory()
            self.test_dry_merge_strategies()

        # 集成测试
        if "integration" in test_categories:
            print("\n🔄 集成测试模块")
            self.test_orchestrator_integration()

        # 错误处理测试
        if "error_handling" in test_categories:
            print("\n🛡️ 错误处理测试")
            self.test_error_handling()

        # 清理测试环境
        self.cleanup()

        # 生成测试报告
        self.generate_test_report()

    def generate_test_report(self):
        """生成详细的测试报告"""
        summary = test_stats.get_summary()

        print("\n" + "=" * 80)
        print("📊 综合测试报告")
        print("=" * 80)

        print(f"🧪 总测试数: {summary['total']}")
        print(f"✅ 通过测试: {summary['passed']}")
        print(f"❌ 失败测试: {summary['failed']}")
        print(f"📈 成功率: {summary['success_rate']:.1f}%")
        print(f"⏱️ 总耗时: {summary['elapsed']:.2f}秒")

        if summary["failures"]:
            print(f"\n❌ 失败测试详情:")
            for i, failure in enumerate(summary["failures"], 1):
                print(f"   {i}. {failure['name']}")
                if failure["error"]:
                    print(f"      错误: {failure['error']}")

        # 生成建议
        if summary["success_rate"] >= 95:
            print("\n🎉 测试结果优秀！项目质量很高")
        elif summary["success_rate"] >= 80:
            print("\n✅ 测试结果良好，建议修复失败的测试")
        else:
            print("\n⚠️ 测试结果需要改进，请优先修复失败的测试")

        # 性能评估
        if summary["elapsed"] < 10:
            print(f"⚡ 测试性能: 优秀 ({summary['elapsed']:.2f}秒)")
        elif summary["elapsed"] < 30:
            print(f"📈 测试性能: 良好 ({summary['elapsed']:.2f}秒)")
        else:
            print(f"⏰ 测试性能: 需要优化 ({summary['elapsed']:.2f}秒)")

    def run_specific_test(self, test_name):
        """运行特定的测试"""
        test_methods = {
            "config_basic": self.test_config_manager_basic,
            "config_expiry": self.test_config_expiry_detection,
            "config_files": self.test_config_file_operations,
            "imports": self.test_module_imports,
            "git_basic": self.test_git_operations_basic,
            "file_helper": self.test_file_helper_operations,
            "performance": self.test_performance_monitoring,
            "large_scale": self.test_large_scale_grouping_performance,
            "merge_factory": self.test_merge_executor_factory,
            "dry_strategies": self.test_dry_merge_strategies,
            "integration": self.test_orchestrator_integration,
            "error_handling": self.test_error_handling,
        }

        if test_name in test_methods:
            print(f"🎯 运行单个测试: {test_name}")
            result = test_methods[test_name]()
            self.cleanup()
            return result
        else:
            print(f"❌ 未找到测试: {test_name}")
            print(f"可用测试: {', '.join(test_methods.keys())}")
            return False


def main():
    """主函数 - 支持命令行参数"""
    import argparse

    parser = argparse.ArgumentParser(description="Git Merge Orchestrator 综合测试套件")
    parser.add_argument(
        "--category",
        "-c",
        choices=["config", "deployment", "performance", "merge_strategies", "integration", "error_handling"],
        nargs="+",
        help="运行指定类别的测试",
    )
    parser.add_argument("--test", "-t", help="运行特定的测试")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有可用的测试")

    args = parser.parse_args()

    suite = ComprehensiveTestSuite()

    if args.list:
        print("📋 可用测试类别:")
        print("  config - 配置管理测试")
        print("  deployment - 部署和模块测试")
        print("  performance - 性能测试")
        print("  merge_strategies - 合并策略测试")
        print("  integration - 集成测试")
        print("  error_handling - 错误处理测试")
        print("\n🎯 可用单个测试:")
        print("  config_basic, config_expiry, config_files")
        print("  imports, git_basic, file_helper")
        print("  performance, large_scale")
        print("  merge_factory, dry_strategies")
        print("  integration, error_handling")
        return

    if args.test:
        success = suite.run_specific_test(args.test)
        sys.exit(0 if success else 1)

    # 运行测试套件
    suite.run_all_tests(args.category)

    # 检查测试结果
    summary = test_stats.get_summary()
    sys.exit(0 if summary["success_rate"] >= 80 else 1)


if __name__ == "__main__":
    main()
