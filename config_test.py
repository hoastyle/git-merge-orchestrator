#!/usr/bin/env python3
"""
Git Merge Orchestrator - 配置管理功能测试（修复版）
修复过期检测测试，确保所有功能正常工作
"""

import sys
import tempfile
import json
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))


def test_config_manager_comprehensive():
    """全面的配置管理器测试（修复版）"""
    print("🚀 Git Merge Orchestrator 配置管理功能测试（修复版）")
    print("=" * 70)

    passed_tests = 0
    total_tests = 0

    def run_test(test_name, test_func):
        nonlocal passed_tests, total_tests
        total_tests += 1
        print(f"\n🧪 测试{total_tests}: {test_name}...")
        try:
            if test_func():
                print(f"✅ {test_name}通过")
                passed_tests += 1
                return True
            else:
                print(f"❌ {test_name}失败")
                return False
        except Exception as e:
            print(f"❌ {test_name}异常: {e}")
            return False

    # 测试1: 基本配置管理功能
    def test_basic_config():
        from utils.config_manager import ProjectConfigManager

        temp_dir = tempfile.mkdtemp()
        try:
            manager = ProjectConfigManager(temp_dir)

            # 测试保存配置
            if not manager.save_config("feature/test", "main", temp_dir, 5, "legacy"):
                return False

            # 测试配置存在检查
            if not manager.has_valid_config():
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
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # 测试2: 配置过期检测（修复版）
    def test_config_expiry_fixed():
        from utils.config_manager import ProjectConfigManager

        temp_dir = tempfile.mkdtemp()
        try:
            manager = ProjectConfigManager(temp_dir)

            # 保存初始配置
            if not manager.save_config("feature/test", "main", temp_dir):
                return False

            # 手动创建过期配置
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
                print(f"   调试信息: 配置时间={old_time}, 当前时间={datetime.now().isoformat()}")

                # 尝试重新读取配置
                fresh_config = manager.load_config()
                print(f"   重新读取的配置时间: {fresh_config.get('saved_at', 'N/A')}")

                return False

            # 测试非过期配置
            manager.save_config("feature/test", "main", temp_dir)  # 保存新配置
            is_not_outdated = not manager.is_config_outdated(days=30)

            return is_not_outdated

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # 测试3: 配置文件操作
    def test_config_file_operations():
        from utils.config_manager import ProjectConfigManager

        temp_dir = tempfile.mkdtemp()
        try:
            manager = ProjectConfigManager(temp_dir)
            export_path = Path(temp_dir) / "exported_config.json"

            # 保存配置
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

            # 验证重置
            if manager.has_valid_config():
                return False

            # 测试导入
            if not manager.import_config(export_path):
                return False

            # 验证导入
            source, target = manager.get_branches_from_config()
            if source != "feature/export" or target != "main":
                return False

            return True

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # 测试4: 边界情况和错误处理
    def test_edge_cases():
        from utils.config_manager import ProjectConfigManager

        # 测试不存在的目录
        non_existent_dir = "/tmp/non_existent_test_dir_12345"
        manager = ProjectConfigManager(non_existent_dir)

        # 应该返回None而不是抛出异常
        config = manager.load_config()
        if config is not None:
            return False

        if manager.has_valid_config():
            return False

        # 测试无效配置文件
        temp_dir = tempfile.mkdtemp()
        try:
            manager = ProjectConfigManager(temp_dir)

            # 确保工作目录存在
            manager.work_dir.mkdir(exist_ok=True)

            # 创建无效的JSON文件
            with open(manager.config_file, "w", encoding="utf-8") as f:
                f.write("invalid json content")

            # 应该返回None而不是抛出异常
            config = manager.load_config()
            if config is not None:
                return False

            # 测试无效配置格式
            with open(manager.config_file, "w", encoding="utf-8") as f:
                f.write('{"invalid": "config", "missing": "required_fields"}')

            # 清除缓存
            manager._config_cache = None

            # 应该返回None因为缺少必需字段
            config = manager.load_config()
            if config is not None:
                return False

            return True

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # 运行所有测试
    run_test("配置管理器基本功能", test_basic_config)
    run_test("配置过期检测（修复版）", test_config_expiry_fixed)
    run_test("配置文件操作", test_config_file_operations)
    run_test("边界情况和错误处理", test_edge_cases)

    # 生成测试报告
    print(f"\n{'='*70}")
    print(f"📊 配置管理测试结果: {passed_tests}/{total_tests} 项测试通过")

    if passed_tests == total_tests:
        print("🎉 所有配置管理功能测试通过！")
        print("💡 配置增强版本已准备就绪，支持:")
        print("   • 自动配置保存和读取")
        print("   • 配置过期检测")
        print("   • 配置导入导出")
        print("   • 完善的错误处理")
        return True
    else:
        print("⚠️ 部分测试失败，请检查实现")
        return False


def main():
    """主函数"""
    try:
        success = test_config_manager_comprehensive()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ 测试运行出错: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
