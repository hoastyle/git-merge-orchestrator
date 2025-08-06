#!/usr/bin/env python3
"""
全面的忽略规则测试
验证新的精确匹配和通配符匹配逻辑
"""

import sys
from pathlib import Path
import tempfile
import os
import shutil

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from utils.ignore_manager import IgnoreManager


class ComprehensiveIgnoreTest:
    """全面的忽略规则测试类"""

    def __init__(self):
        self.test_results = []
        self.temp_dir = None

    def setup_test_environment(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp(prefix="ignore_test_")
        print(f"🏗️ 测试环境: {self.temp_dir}")

        # 创建测试目录结构
        test_structure = {
            "settings/config.json": "file",
            "settings/database.conf": "file",
            "settings/local/dev.conf": "file",
            "app/settings/production.json": "file",
            "app/config/settings.json": "file",
            "src/main.py": "file",
            "src/utils/helper.py": "file",
            "README.md": "file",
            "config.py": "file",
            "settings.json": "file",  # 同名文件，不应该被忽略
            "settings": "file",  # 同名文件（无扩展名）
            "test/settings/unit.py": "file",
            "docs/settings/api.md": "file",
            "build/": "dir",
            "dist/": "dir",
            "node_modules/": "dir",
            "logs/debug.log": "file",
            "temp/cache.tmp": "file",
        }

        for path, item_type in test_structure.items():
            full_path = Path(self.temp_dir) / path
            if item_type == "dir":
                full_path.mkdir(parents=True, exist_ok=True)
                # 创建一个子文件让目录不为空
                (full_path / ".gitkeep").touch()
            else:
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.touch()

        print(f"✅ 测试环境创建完成")

    def cleanup_test_environment(self):
        """清理测试环境"""
        if self.temp_dir and Path(self.temp_dir).exists():
            shutil.rmtree(self.temp_dir)
            print(f"🧹 测试环境已清理")

    def run_all_tests(self):
        """运行所有测试"""
        self.setup_test_environment()

        try:
            print("\n" + "=" * 60)
            print("🧪 开始全面忽略规则测试")
            print("=" * 60)

            # 测试1: 精确目录匹配
            self.test_exact_directory_matching()

            # 测试2: 通配符目录匹配
            self.test_wildcard_directory_matching()

            # 测试3: 文件/目录冲突处理
            self.test_file_directory_conflicts()

            # 测试4: 文件模式匹配
            self.test_file_pattern_matching()

            # 测试5: 混合规则优先级
            self.test_mixed_rules_priority()

            # 测试6: 边缘情况
            self.test_edge_cases()

            # 显示测试结果
            self.display_test_results()

        finally:
            self.cleanup_test_environment()

    def test_exact_directory_matching(self):
        """测试精确目录匹配"""
        print(f"\n📁 测试1: 精确目录匹配")

        # 创建只有settings/规则的忽略管理器
        ignore_manager = IgnoreManager(self.temp_dir)
        ignore_manager.rules = [
            {"pattern": "settings/", "type": "glob", "enabled": True, "source": "test"}
        ]
        ignore_manager._compile_rules()

        test_cases = [
            # 应该被忽略的
            ("settings/config.json", True, "根目录settings下的文件"),
            ("settings/database.conf", True, "根目录settings下的文件"),
            ("settings/local/dev.conf", True, "根目录settings下的子目录文件"),
            # 不应该被忽略的
            ("app/settings/production.json", False, "嵌套的settings目录"),
            ("test/settings/unit.py", False, "嵌套的settings目录"),
            ("docs/settings/api.md", False, "嵌套的settings目录"),
            ("settings.json", False, "同名文件"),
            ("settings", False, "同名文件（无扩展名）"),
            ("app/config/settings.json", False, "不在settings目录下"),
        ]

        self._run_test_cases(ignore_manager, test_cases, "精确目录匹配")

    def test_wildcard_directory_matching(self):
        """测试通配符目录匹配"""
        print(f"\n🌟 测试2: 通配符目录匹配")

        # 创建有**/settings/规则的忽略管理器
        ignore_manager = IgnoreManager(self.temp_dir)
        ignore_manager.rules = [
            {
                "pattern": "**/settings/",
                "type": "glob",
                "enabled": True,
                "source": "test",
            }
        ]
        ignore_manager._compile_rules()

        test_cases = [
            # 应该被忽略的
            ("settings/config.json", True, "根目录settings"),
            ("app/settings/production.json", True, "嵌套的settings目录"),
            ("test/settings/unit.py", True, "嵌套的settings目录"),
            ("docs/settings/api.md", True, "嵌套的settings目录"),
            # 不应该被忽略的
            ("settings.json", False, "同名文件"),
            ("settings", False, "同名文件（无扩展名）"),
            ("app/config/settings.json", False, "不在settings目录下"),
        ]

        self._run_test_cases(ignore_manager, test_cases, "通配符目录匹配")

    def test_file_directory_conflicts(self):
        """测试文件/目录冲突处理"""
        print(f"\n⚖️ 测试3: 文件/目录冲突处理")

        # 分别测试单独的规则
        print("  📋 子测试3a: 只有目录规则")
        ignore_manager_dir = IgnoreManager(self.temp_dir)
        ignore_manager_dir.rules = [
            {"pattern": "settings/", "type": "glob", "enabled": True, "source": "test"}
        ]
        ignore_manager_dir._compile_rules()

        # 子测试：只有目录规则时，settings文件不应该被忽略
        settings_ignored_by_dir_rule = ignore_manager_dir.should_ignore("settings")
        print(f"    settings 被目录规则忽略: {settings_ignored_by_dir_rule}")

        print("  📋 子测试3b: 只有文件规则")
        ignore_manager_file = IgnoreManager(self.temp_dir)
        ignore_manager_file.rules = [
            {"pattern": "settings", "type": "glob", "enabled": True, "source": "test"}
        ]
        ignore_manager_file._compile_rules()

        settings_ignored_by_file_rule = ignore_manager_file.should_ignore("settings")
        print(f"    settings 被文件规则忽略: {settings_ignored_by_file_rule}")

        print("  📋 子测试3c: 同时有两个规则")
        ignore_manager = IgnoreManager(self.temp_dir)
        ignore_manager.rules = [
            {
                "pattern": "settings/",  # 目录模式
                "type": "glob",
                "enabled": True,
                "source": "test",
            },
            {
                "pattern": "settings",  # 文件模式
                "type": "glob",
                "enabled": True,
                "source": "test",
            },
        ]
        ignore_manager._compile_rules()

        test_cases = [
            # 目录模式匹配
            ("settings/config.json", True, "目录下的文件"),
            # 文件模式匹配
            ("settings", True, "同名文件"),
            ("settings.json", False, "包含settings但不完全匹配"),
        ]

        self._run_test_cases(ignore_manager, test_cases, "文件/目录冲突")

    def test_file_pattern_matching(self):
        """测试文件模式匹配"""
        print(f"\n📄 测试4: 文件模式匹配")

        ignore_manager = IgnoreManager(self.temp_dir)
        ignore_manager.rules = [
            {"pattern": "*.log", "type": "glob", "enabled": True, "source": "test"},
            {"pattern": "*.tmp", "type": "glob", "enabled": True, "source": "test"},
            {"pattern": "build/", "type": "glob", "enabled": True, "source": "test"},
        ]
        ignore_manager._compile_rules()

        test_cases = [
            # 文件扩展名匹配
            ("logs/debug.log", True, ".log文件"),
            ("temp/cache.tmp", True, ".tmp文件"),
            # 目录匹配
            ("build/", True, "build目录"),
            # 不匹配的
            ("logs/debug.txt", False, ".txt文件"),
            ("src/main.py", False, ".py文件"),
        ]

        self._run_test_cases(ignore_manager, test_cases, "文件模式匹配")

    def test_mixed_rules_priority(self):
        """测试混合规则优先级"""
        print(f"\n🎭 测试5: 混合规则优先级")

        ignore_manager = IgnoreManager(self.temp_dir)
        ignore_manager.rules = [
            {"pattern": "settings/", "type": "glob", "enabled": True, "source": "test"},
            {"pattern": "*.json", "type": "glob", "enabled": True, "source": "test"},
            {
                "pattern": "**/production.json",
                "type": "glob",
                "enabled": True,
                "source": "test",
            },
        ]
        ignore_manager._compile_rules()

        test_cases = [
            # 多重匹配情况
            ("settings/config.json", True, "同时匹配目录和文件扩展名"),
            ("app/settings/production.json", True, "匹配文件路径模式"),
            ("config.py", False, "不匹配任何规则"),
        ]

        self._run_test_cases(ignore_manager, test_cases, "混合规则优先级")

    def test_edge_cases(self):
        """测试边缘情况"""
        print(f"\n🎪 测试6: 边缘情况")

        ignore_manager = IgnoreManager(self.temp_dir)
        ignore_manager.rules = [
            {"pattern": "settings/", "type": "glob", "enabled": True, "source": "test"},
            {"pattern": "", "type": "glob", "enabled": True, "source": "test"},  # 空模式
            {"pattern": "/", "type": "glob", "enabled": True, "source": "test"},  # 根目录
        ]
        ignore_manager._compile_rules()

        test_cases = [
            # 边缘情况
            ("", False, "空路径"),
            ("settings/", True, "目录本身"),
            ("settings", False, "文件名"),
            ("SETTINGS/config.json", False, "大小写敏感"),
        ]

        self._run_test_cases(ignore_manager, test_cases, "边缘情况")

    def _run_test_cases(self, ignore_manager, test_cases, test_name):
        """运行测试用例"""
        passed = 0
        failed = 0

        for file_path, expected_ignored, description in test_cases:
            actual_ignored = ignore_manager.should_ignore(file_path)

            if actual_ignored == expected_ignored:
                status = "✅"
                passed += 1
            else:
                status = "❌"
                failed += 1

            print(f"  {status} {file_path:<35} - {description}")
            if actual_ignored != expected_ignored:
                print(
                    f"      期望: {'忽略' if expected_ignored else '保留'}, "
                    f"实际: {'忽略' if actual_ignored else '保留'}"
                )

        # 记录测试结果
        self.test_results.append(
            {
                "name": test_name,
                "passed": passed,
                "failed": failed,
                "total": len(test_cases),
            }
        )

        print(f"  📊 {test_name}: {passed}/{len(test_cases)} 通过")

    def display_test_results(self):
        """显示测试结果总结"""
        print("\n" + "=" * 60)
        print("📊 测试结果总结")
        print("=" * 60)

        total_passed = 0
        total_failed = 0
        total_tests = 0

        for result in self.test_results:
            total_passed += result["passed"]
            total_failed += result["failed"]
            total_tests += result["total"]

            percentage = (result["passed"] / result["total"]) * 100
            status = "✅" if result["failed"] == 0 else "⚠️"

            print(
                f"{status} {result['name']:<25} {result['passed']:>2}/{result['total']:<2} "
                f"({percentage:5.1f}%)"
            )

        overall_percentage = (total_passed / total_tests) * 100
        overall_status = "🎉" if total_failed == 0 else "🔧"

        print("-" * 60)
        print(
            f"{overall_status} 总计: {total_passed}/{total_tests} 通过 "
            f"({overall_percentage:.1f}%)"
        )

        if total_failed == 0:
            print("🎉 所有测试通过！忽略规则工作正常。")
        else:
            print(f"🔧 有 {total_failed} 个测试失败，需要进一步调试。")

        return total_failed == 0


def main():
    """主函数"""
    print("🚀 启动全面忽略规则测试...")

    tester = ComprehensiveIgnoreTest()
    success = tester.run_all_tests()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
