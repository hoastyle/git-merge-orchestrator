"""
Git Merge Orchestrator - 项目配置管理器
负责自动保存和加载项目配置，支持无参数运行
"""

import json
import os
from pathlib import Path
from datetime import datetime
from config import WORK_DIR_NAME


class ProjectConfigManager:
    """项目配置管理器"""

    CONFIG_FILE_NAME = "project_config.json"
    CONFIG_VERSION = "2.0"

    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path)
        self.work_dir = self.repo_path / WORK_DIR_NAME
        self.config_file = self.work_dir / self.CONFIG_FILE_NAME
        self._config_cache = None

    def load_config(self):
        """加载项目配置"""
        if self._config_cache is not None:
            return self._config_cache

        if not self.config_file.exists():
            return None

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            # 验证配置版本和必要字段
            if not self._validate_config(config):
                print("⚠️ 配置文件格式不正确，将忽略现有配置")
                return None

            self._config_cache = config
            return config

        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️ 读取配置文件失败: {e}")
            return None

    def save_config(self, source_branch, target_branch, repo_path=".", max_files_per_group=5, merge_strategy=None):
        """保存项目配置"""
        # 确保工作目录存在
        self.work_dir.mkdir(exist_ok=True)

        # 加载现有合并策略（如果存在）
        if merge_strategy is None:
            try:
                from core.merge_executor_factory import MergeExecutorFactory

                factory = MergeExecutorFactory(repo_path)
                merge_strategy = factory.get_current_mode()
            except:
                merge_strategy = "standard"

        config = {
            "version": self.CONFIG_VERSION,
            "saved_at": datetime.now().isoformat(),
            "source_branch": source_branch,
            "target_branch": target_branch,
            "repo_path": str(repo_path),
            "max_files_per_group": max_files_per_group,
            "merge_strategy": merge_strategy,
        }

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self._config_cache = config
            print(f"✅ 项目配置已保存到: {self.config_file}")
            return True

        except IOError as e:
            print(f"❌ 保存配置文件失败: {e}")
            return False

    def get_config_value(self, key, default=None):
        """获取配置值"""
        config = self.load_config()
        if config:
            return config.get(key, default)
        return default

    def has_valid_config(self):
        """检查是否有有效的配置文件"""
        config = self.load_config()
        return config is not None and self._validate_config(config)

    def get_branches_from_config(self):
        """从配置获取分支信息"""
        config = self.load_config()
        if config:
            return config.get("source_branch"), config.get("target_branch")
        return None, None

    def update_config(self, preserve_timestamp=False, **kwargs):
        """更新配置中的特定字段

        Args:
            preserve_timestamp: 是否保留原始时间戳（用于测试）
            **kwargs: 要更新的配置字段
        """
        config = self.load_config()
        if not config:
            print("❌ 没有现有配置可以更新")
            return False

        # 更新字段
        for key, value in kwargs.items():
            if key in config:
                config[key] = value

        # 只有在不需要保留时间戳时才更新
        if not preserve_timestamp:
            config["saved_at"] = datetime.now().isoformat()

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self._config_cache = config
            print(f"✅ 配置已更新")
            return True

        except IOError as e:
            print(f"❌ 更新配置失败: {e}")
            return False

    def show_current_config(self):
        """显示当前配置"""
        config = self.load_config()
        if not config:
            print("📋 当前没有保存的项目配置")
            return

        print("📋 当前项目配置:")
        print("=" * 50)
        print(f"📁 仓库路径: {config.get('repo_path', '.')}")
        print(f"🌿 源分支: {config.get('source_branch', 'N/A')}")
        print(f"🎯 目标分支: {config.get('target_branch', 'N/A')}")
        print(f"📦 每组最大文件数: {config.get('max_files_per_group', 5)}")
        print(f"🔧 合并策略: {config.get('merge_strategy', 'standard')}")
        print(f"💾 保存时间: {config.get('saved_at', 'N/A')}")
        print(f"📝 配置版本: {config.get('version', 'N/A')}")

    def reset_config(self):
        """重置配置（删除配置文件）"""
        if self.config_file.exists():
            try:
                self.config_file.unlink()
                self._config_cache = None
                print("✅ 项目配置已重置")
                return True
            except OSError as e:
                print(f"❌ 重置配置失败: {e}")
                return False
        else:
            print("ℹ️ 没有找到配置文件")
            return True

    def _validate_config(self, config):
        """验证配置文件格式"""
        if not isinstance(config, dict):
            return False

        required_fields = ["source_branch", "target_branch", "version"]
        for field in required_fields:
            if field not in config:
                return False

        # 检查版本兼容性
        config_version = config.get("version", "1.0")
        if config_version not in ["1.0", "2.0"]:
            return False

        return True

    def export_config(self, export_path):
        """导出配置到指定路径"""
        config = self.load_config()
        if not config:
            print("❌ 没有配置可以导出")
            return False

        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)

            with open(export_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            print(f"✅ 配置已导出到: {export_file}")
            return True

        except IOError as e:
            print(f"❌ 导出配置失败: {e}")
            return False

    def import_config(self, import_path):
        """从指定路径导入配置"""
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                print(f"❌ 导入文件不存在: {import_path}")
                return False

            with open(import_file, "r", encoding="utf-8") as f:
                config = json.load(f)

            if not self._validate_config(config):
                print("❌ 导入的配置文件格式不正确")
                return False

            # 更新保存时间
            config["saved_at"] = datetime.now().isoformat()

            # 确保工作目录存在
            self.work_dir.mkdir(exist_ok=True)

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self._config_cache = config
            print(f"✅ 配置已从 {import_path} 导入")
            return True

        except (json.JSONDecodeError, IOError) as e:
            print(f"❌ 导入配置失败: {e}")
            return False

    def get_config_file_path(self):
        """获取配置文件路径"""
        return str(self.config_file)

    def is_config_outdated(self, days=30):
        """检查配置是否过期"""
        config = self.load_config()
        if not config or "saved_at" not in config:
            return False

        try:
            saved_time = datetime.fromisoformat(config["saved_at"])
            age_days = (datetime.now() - saved_time).days
            return age_days > days
        except:
            return False
