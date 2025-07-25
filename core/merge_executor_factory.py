"""
Git Merge Orchestrator - 合并执行器工厂
支持Legacy和Standard两种合并策略
"""

from pathlib import Path
import json
from config import WORK_DIR_NAME


class MergeExecutorFactory:
    """合并执行器工厂类"""

    LEGACY_MODE = "legacy"
    STANDARD_MODE = "standard"

    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path)
        self.config_file = self.repo_path / WORK_DIR_NAME / "merge_strategy.json"
        self._current_mode = None

    def get_current_mode(self):
        """获取当前合并策略模式"""
        if self._current_mode is not None:
            return self._current_mode

        # 从配置文件读取
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    self._current_mode = config.get(
                        "merge_strategy", self.STANDARD_MODE
                    )
            except:
                self._current_mode = self.STANDARD_MODE
        else:
            self._current_mode = self.STANDARD_MODE

        return self._current_mode

    def set_merge_mode(self, mode):
        """设置合并策略模式"""
        if mode not in [self.LEGACY_MODE, self.STANDARD_MODE]:
            raise ValueError(f"Invalid merge mode: {mode}")

        self._current_mode = mode

        # 保存到配置文件
        self.config_file.parent.mkdir(exist_ok=True)
        config = {
            "merge_strategy": mode,
            "updated_at": Path(__file__)
            .parent.parent.joinpath("utils", "file_helper.py")
            .stat()
            .st_mtime
            if Path(__file__).parent.parent.joinpath("utils", "file_helper.py").exists()
            else 0,
        }

        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 保存合并策略配置失败: {e}")

    def create_executor(self, git_ops, file_helper):
        """创建合并执行器实例"""
        mode = self.get_current_mode()

        if mode == self.LEGACY_MODE:
            from core.legacy_merge_executor import LegacyMergeExecutor

            return LegacyMergeExecutor(git_ops, file_helper)
        else:
            from core.standard_merge_executor import StandardMergeExecutor

            return StandardMergeExecutor(git_ops, file_helper)

    def get_mode_description(self, mode=None):
        """获取模式描述"""
        if mode is None:
            mode = self.get_current_mode()

        descriptions = {
            self.LEGACY_MODE: {
                "name": "Legacy模式",
                "description": "快速覆盖策略，直接使用源分支内容覆盖目标分支",
                "pros": ["速度快", "操作简单", "适合信任源分支的场景"],
                "cons": ["无冲突标记", "无法手动解决冲突", "可能丢失目标分支修改"],
                "suitable": "适合：确定源分支内容正确，不需要精细控制的场景",
            },
            self.STANDARD_MODE: {
                "name": "Standard模式",
                "description": "标准Git三路合并，产生标准冲突标记",
                "pros": ["标准Git流程", "产生冲突标记", "支持手动解决冲突", "更安全"],
                "cons": ["需要手动处理冲突", "操作稍复杂"],
                "suitable": "适合：需要精确控制合并结果，保证代码质量的场景",
            },
        }

        return descriptions.get(mode, {})

    def list_available_modes(self):
        """列出所有可用模式"""
        return [
            {"mode": self.LEGACY_MODE, **self.get_mode_description(self.LEGACY_MODE)},
            {
                "mode": self.STANDARD_MODE,
                **self.get_mode_description(self.STANDARD_MODE),
            },
        ]

    def switch_mode_interactive(self):
        """交互式切换模式"""
        current_mode = self.get_current_mode()
        modes = self.list_available_modes()

        print("🔧 合并策略选择")
        print("=" * 80)

        for i, mode_info in enumerate(modes, 1):
            current_indicator = " ← 当前模式" if mode_info["mode"] == current_mode else ""
            print(f"{i}. {mode_info['name']}{current_indicator}")
            print(f"   描述: {mode_info['description']}")
            print(f"   优点: {', '.join(mode_info['pros'])}")
            print(f"   缺点: {', '.join(mode_info['cons'])}")
            print(f"   {mode_info['suitable']}")
            print()

        try:
            choice = input("请选择合并策略 (1-2): ").strip()
            choice_idx = int(choice) - 1

            if 0 <= choice_idx < len(modes):
                selected_mode = modes[choice_idx]["mode"]
                if selected_mode == current_mode:
                    print(f"✅ 已经是 {modes[choice_idx]['name']} 模式")
                else:
                    self.set_merge_mode(selected_mode)
                    print(f"✅ 已切换到 {modes[choice_idx]['name']} 模式")
                    print(f"💡 后续的合并操作将使用新策略")
                return True
            else:
                print("❌ 无效选择")
                return False

        except ValueError:
            print("❌ 请输入有效数字")
            return False

    def get_status_info(self):
        """获取当前状态信息"""
        mode = self.get_current_mode()
        mode_info = self.get_mode_description(mode)

        return {
            "current_mode": mode,
            "mode_name": mode_info.get("name", "Unknown"),
            "description": mode_info.get("description", ""),
            "config_file": str(self.config_file),
            "config_exists": self.config_file.exists(),
        }
