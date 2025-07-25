#!/usr/bin/env python3
"""
Git Merge Orchestrator - 主入口文件（优化版）
提供命令行界面和优化的分层菜单系统，支持Legacy和Standard两种合并策略
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from git_merge_orchestrator import GitMergeOrchestrator
from ui.display_helper import DisplayHelper
from ui.menu_manager import MenuManager  # 新的菜单管理器


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="Git大分叉智能分步合并工具 - 多人协作版（优化菜单+DRY架构）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python main.py feature/big-feature main
  python main.py feature/big-feature main --max-files 8
  python main.py feature/big-feature main --repo /path/to/repo

新版本特性:
  • 🚀 优化菜单结构 - 6个主分类，减少选择焦虑
  • ⚡ DRY架构重构 - 消除代码重复，提升维护性
  • 🎯 快速开始向导 - 引导新用户完成全流程
  • 📊 智能状态感知 - 根据当前进度提供操作建议
  • 🔧 策略管理优化 - 更清晰的Legacy/Standard对比

核心功能:
  • 智能文件分组 - 按目录结构自动分组，每组最多5个文件
  • 贡献者分析 - 基于Git历史分析文件贡献者和活跃度
  • 自动任务分配 - 优先分配给近期活跃且熟悉相关文件的开发者
  • 双合并策略 - Legacy快速覆盖 vs Standard三路合并
  • 批量操作支持 - 支持按负责人批量合并和状态管理
  • 进度跟踪 - 完整的任务状态跟踪和远程分支检测

菜单结构:
  1. 🚀 快速开始向导 - 新用户推荐，全流程引导
  2. 📊 项目管理 - 计划创建、状态检查、分析报告
  3. 👥 任务分配 - 自动分配、手动分配、查看分析
  4. 🔄 执行合并 - 组合并、批量合并、交互式合并
  5. ⚙️ 系统管理 - 策略选择、缓存管理、状态管理
  6. 🎯 高级功能 - 详细分析、性能统计、调试模式
        """,
    )

    parser.add_argument("source_branch", help="源分支名称")
    parser.add_argument("target_branch", help="目标分支名称")
    parser.add_argument("--max-files", type=int, default=5, help="每组最大文件数 (默认: 5)")
    parser.add_argument("--repo", default=".", help="Git仓库路径 (默认: 当前目录)")
    parser.add_argument(
        "--strategy",
        choices=["legacy", "standard"],
        help="合并策略 (legacy: 快速覆盖, standard: 三路合并)",
    )
    parser.add_argument(
        "--version", action="version", version="Git Merge Orchestrator 2.2 (优化版)"
    )

    return parser.parse_args()


def show_welcome_banner(orchestrator):
    """显示欢迎横幅"""
    print("🚀 Git大分叉智能分步合并工具 (优化增强版)")
    print("=" * 80)
    print(f"源分支: {orchestrator.source_branch}")
    print(f"目标分支: {orchestrator.target_branch}")
    print(f"每组最大文件数: {orchestrator.max_files_per_group}")
    print(f"工作目录: {orchestrator.repo_path}")

    # 显示当前合并策略
    strategy_info = orchestrator.get_merge_strategy_info()
    print(f"🔧 当前合并策略: {strategy_info['mode_name']}")
    print(f"📝 策略说明: {strategy_info['description']}")

    # 显示版本特性
    print("\n🆕 本版本特性:")
    print("   • 🎯 优化菜单: 6个主分类，降低选择复杂度")
    print("   • ⚡ DRY重构: 消除代码重复，提升维护性")
    print("   • 🚀 快速向导: 新用户友好的全流程引导")
    print("   • 📊 智能感知: 基于当前状态的操作建议")

    # 显示计划摘要（如果存在）
    try:
        summary = orchestrator.get_plan_summary()
        if summary and summary.get("stats"):
            stats = summary["stats"]
            print(f"\n📊 当前计划状态:")
            print(f"   总分组: {stats.get('total_groups', 0)} 个")
            print(f"   总文件: {stats.get('total_files', 0)} 个")
            print(
                f"   已分配: {stats.get('assigned_groups', 0)} 组 ({stats.get('assigned_files', 0)} 文件)"
            )
            print(
                f"   已完成: {stats.get('completed_groups', 0)} 组 ({stats.get('completed_files', 0)} 文件)"
            )
            if summary.get("integration_branch"):
                print(f"   集成分支: {summary['integration_branch']}")

            # 智能建议
            if stats['total_groups'] == 0:
                print("💡 建议: 使用快速开始向导创建合并计划")
            elif stats['assigned_groups'] == 0:
                print("💡 建议: 使用涡轮增压自动分配任务")
            elif stats['completed_groups'] < stats['total_groups']:
                print("💡 建议: 继续执行合并操作")
            else:
                print("💡 建议: 执行最终合并完成项目")
    except Exception as e:
        # 如果获取摘要失败，不影响主程序运行
        pass

    print("=" * 80)


def validate_environment(orchestrator):
    """验证运行环境"""
    # 检查是否在Git仓库中
    git_dir = orchestrator.repo_path / ".git"
    if not git_dir.exists():
        DisplayHelper.print_error("当前目录不是Git仓库")
        return False

    # 检查分支是否存在
    result = orchestrator.git_ops.run_command(
        f"git rev-parse --verify {orchestrator.source_branch}"
    )
    if result is None:
        DisplayHelper.print_error(f"源分支 '{orchestrator.source_branch}' 不存在")
        return False

    result = orchestrator.git_ops.run_command(
        f"git rev-parse --verify {orchestrator.target_branch}"
    )
    if result is None:
        DisplayHelper.print_error(f"目标分支 '{orchestrator.target_branch}' 不存在")
        return False

    return True


def main():
    """主函数"""
    try:
        # 解析命令行参数
        args = parse_arguments()

        # 创建主控制器
        orchestrator = GitMergeOrchestrator(
            source_branch=args.source_branch,
            target_branch=args.target_branch,
            repo_path=args.repo,
            max_files_per_group=args.max_files,
        )

        # 设置命令行指定的策略
        if args.strategy:
            strategy_map = {"legacy": "legacy", "standard": "standard"}
            if orchestrator.set_merge_strategy(strategy_map[args.strategy]):
                print(f"✅ 已设置合并策略为: {args.strategy}")
            else:
                print(f"⚠️ 设置合并策略失败，使用默认策略")

        # 验证环境
        if not validate_environment(orchestrator):
            sys.exit(1)

        # 显示欢迎信息
        show_welcome_banner(orchestrator)

        # 运行优化后的交互式菜单
        menu_manager = MenuManager(orchestrator)
        menu_manager.run_interactive_menu()

    except KeyboardInterrupt:
        print("\n\n👋 用户中断，正在退出...")
        sys.exit(0)
    except Exception as e:
        DisplayHelper.print_error(f"程序运行出现错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


# === 更新后的工厂类 ===

"""
更新 core/merge_executor_factory.py
"""

from pathlib import Path
import json
from config import WORK_DIR_NAME


class MergeExecutorFactory:
    """合并执行器工厂类 - 支持DRY优化后的执行器"""

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
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self._current_mode = config.get('merge_strategy', self.STANDARD_MODE)
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
            'merge_strategy': mode,
            'updated_at': datetime.now().isoformat(),
            'version': '2.2-optimized'
        }

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 保存合并策略配置失败: {e}")

    def create_executor(self, git_ops, file_helper):
        """创建合并执行器实例 - 使用DRY优化后的执行器"""
        mode = self.get_current_mode()

        if mode == self.LEGACY_MODE:
            # 导入DRY优化后的Legacy执行器
            from core.legacy_merge_executor_optimized import LegacyMergeExecutor
            return LegacyMergeExecutor(git_ops, file_helper)
        else:
            # 导入DRY优化后的Standard执行器
            from core.standard_merge_executor_optimized import StandardMergeExecutor
            return StandardMergeExecutor(git_ops, file_helper)

    def get_mode_description(self, mode=None):
        """获取模式描述 - 增强版本"""
        if mode is None:
            mode = self.get_current_mode()

        descriptions = {
            self.LEGACY_MODE: {
                'name': 'Legacy模式',
                'description': '快速覆盖策略，源分支内容直接覆盖目标分支',
                'pros': ['速度快', '操作简单', '适合信任源分支的场景', '无需手动解决冲突'],
                'cons': ['无冲突标记', '可能丢失目标分支修改', '需要人工验证结果'],
                'suitable': '适合：热修复、紧急发布、小团队高信任度项目',
                'use_cases': ['紧急bug修复', '配置文件更新', '文档同步', '版本号更新']
            },
            self.STANDARD_MODE: {
                'name': 'Standard模式',
                'description': '标准Git三路合并，产生标准冲突标记',
                'pros': ['标准Git流程', '产生冲突标记', '支持手动解决冲突', '更安全可靠'],
                'cons': ['需要手动处理冲突', '操作稍复杂', '耗时较长'],
                'suitable': '适合：大型项目、多人协作、需要精确控制的场景',
                'use_cases': ['功能分支合并', '版本发布', '代码重构', '多人协作开发']
            }
        }

        return descriptions.get(mode, {})

    def list_available_modes(self):
        """列出所有可用模式 - 增强版本"""
        return [
            {
                'mode': self.LEGACY_MODE,
                **self.get_mode_description(self.LEGACY_MODE)
            },
            {
                'mode': self.STANDARD_MODE,
                **self.get_mode_description(self.STANDARD_MODE)
            }
        ]

    def switch_mode_interactive(self):
        """交互式切换模式 - 增强版本"""
        current_mode = self.get_current_mode()
        modes = self.list_available_modes()

        print("🔧 合并策略选择 (DRY优化版)")
        print("=" * 80)

        for i, mode_info in enumerate(modes, 1):
            current_indicator = " ← 当前模式" if mode_info['mode'] == current_mode else ""
            print(f"{i}. {mode_info['name']}{current_indicator}")
            print(f"   描述: {mode_info['description']}")
            print(f"   优点: {', '.join(mode_info['pros'])}")
            print(f"   缺点: {', '.join(mode_info['cons'])}")
            print(f"   {mode_info['suitable']}")
            print(f"   典型场景: {', '.join(mode_info['use_cases'])}")
            print()

        # 提供更详细的选择指导
        print("💡 选择指导:")
        print("   📊 项目规模: 小项目(<10人) → Legacy, 大项目(>10人) → Standard")
        print("   🕒 时间要求: 紧急发布 → Legacy, 常规开发 → Standard")
        print("   🤝 团队信任: 高信任度 → Legacy, 需要审查 → Standard")
        print("   🔧 技术复杂度: 简单修改 → Legacy, 复杂功能 → Standard")
        print()

        try:
            choice = input("请选择合并策略 (1-2): ").strip()
            choice_idx = int(choice) - 1

            if 0 <= choice_idx < len(modes):
                selected_mode = modes[choice_idx]['mode']
                if selected_mode == current_mode:
                    print(f"✅ 已经是 {modes[choice_idx]['name']} 模式")
                else:
                    self.set_merge_mode(selected_mode)
                    print(f"✅ 已切换到 {modes[choice_idx]['name']} 模式")
                    print(f"💡 后续的合并操作将使用新策略")
                    print(f"🔄 策略差异: DRY架构确保两种策略的基础行为一致")
                return True
            else:
                print("❌ 无效选择")
                return False

        except ValueError:
            print("❌ 请输入有效数字")
            return False

    def get_status_info(self):
        """获取当前状态信息 - 增强版本"""
        mode = self.get_current_mode()
        mode_info = self.get_mode_description(mode)

        return {
            'current_mode': mode,
            'mode_name': mode_info.get('name', 'Unknown'),
            'description': mode_info.get('description', ''),
            'config_file': str(self.config_file),
            'config_exists': self.config_file.exists(),
            'architecture': 'DRY-Optimized',
            'version': '2.2-optimized'
        }

    def get_architecture_info(self):
        """获取架构信息"""
        return {
            'architecture': 'DRY-Optimized',
            'base_class': 'BaseMergeExecutor',
            'code_reuse': '~60%',
            'maintainability': 'Enhanced',
            'extensibility': 'High',
            'benefits': [
                '消除重复代码',
                '统一接口规范',
                '易于添加新策略',
                '提升代码质量',
                '简化测试维护'
            ]
        }
