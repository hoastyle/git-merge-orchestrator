"""
Git Merge Orchestrator - 扁平化菜单管理器
简化的1级菜单系统，提供直接访问所有核心功能
"""

from ui.display_helper import DisplayHelper
from ui.menu_commands import MenuCommands


class FlatMenuManager:
    """扁平化菜单管理器 - 1级菜单直接访问所有功能"""

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.commands = MenuCommands(orchestrator)

        # 核心功能菜单映射
        self.core_functions = {
            "1": ("🚀 快速全流程", self._quick_workflow),
            "2": ("🔍 分析分叉", self._analyze_divergence),
            "3": ("📋 创建计划", self._create_plan),
            "4": ("⚡ 自动分配", self._auto_assign),
            "5": ("📊 项目状态", self._check_status),
            "6": ("🔍 高级查询", self._advanced_query),
            "7": ("👤 搜索/分配任务", self._search_assign_tasks),
            "8": ("📄 合并指定文件", self._merge_file_or_group),
            "9": ("🎯 批量合并", self._batch_merge),
            "10": ("🎉 最终合并", self._finalize_merge),
            "11": ("⚙️ 系统设置", self._system_settings),
            "12": ("💡 帮助", self._show_help),
        }

        # 快捷键映射
        self.shortcuts = {
            "q": self._quit,
            "h": self._show_help,
            "s": self._check_status,
            "?": self._show_help,
        }

    def run_interactive_menu(self):
        """运行交互式扁平化菜单"""
        print("\n🎉 欢迎使用 Git Merge Orchestrator v2.2")
        print("💡 提示: 输入数字直接执行功能，输入 'q' 退出，'h' 查看帮助\n")

        while True:
            try:
                self._show_main_menu()
                choice = input("\n请选择功能 (1-12, q退出, h帮助): ").strip().lower()

                if not choice:
                    continue

                # 处理退出
                if choice in ["q", "quit", "exit", "0"]:
                    print("👋 感谢使用 Git Merge Orchestrator!")
                    break

                # 处理快捷键
                if choice in self.shortcuts:
                    self.shortcuts[choice]()
                    continue

                # 处理核心功能
                if choice in self.core_functions:
                    func_name, func = self.core_functions[choice]
                    print(f"\n▶️ 执行: {func_name}")
                    print("-" * 50)
                    func()
                else:
                    DisplayHelper.print_warning(f"无效选择: {choice}")
                    print("💡 输入 1-12 选择功能，或 'h' 查看帮助")

            except KeyboardInterrupt:
                print("\n\n👋 操作已取消，感谢使用!")
                break
            except Exception as e:
                DisplayHelper.print_error(f"操作出错: {e}")
                print("请重试或输入 'h' 查看帮助")

        print("\n程序已退出。")

    def _show_main_menu(self):
        """显示主菜单"""
        print("\n" + "=" * 60)
        print("🚀 Git Merge Orchestrator - 扁平化菜单")
        print("=" * 60)

        # 显示项目状态摘要
        self._show_project_summary()

        print(f"\n📋 核心功能 (输入数字直接执行):")

        # 显示简洁的单列布局
        functions_list = list(self.core_functions.items())
        for key, (name, _) in functions_list:
            # 为功能8动态调整显示名称
            if key == "8":
                if self._is_file_level_mode():
                    name = "📄 合并指定文件"
                else:
                    name = "📁 合并指定组"
            print(f"  {key:2}. {name}")
        print(f"💡 快捷键: q=退出, h=帮助, s=状态")

    def _show_project_summary(self):
        """显示项目状态摘要"""
        try:
            # 显示处理模式
            mode_info = self.orchestrator.get_processing_mode_info()
            print(f"🔧 模式: {mode_info['mode_name']}")

            # 显示分支信息
            print(
                f"🌿 {self.orchestrator.source_branch} → {self.orchestrator.target_branch}"
            )

            # 显示项目状态
            summary = self.orchestrator.get_plan_summary()
            if summary:
                strategy = summary["merge_strategy"]
                print(f"⚙️ 策略: {strategy['mode_name']}")

                if self.orchestrator.processing_mode == "file_level":
                    stats = summary.get("completion_stats", {})
                    if stats.get("total_files", 0) > 0:
                        progress = stats.get("completion_rate", 0)
                        print(
                            f"📊 进度: {stats['completed_files']}/{stats['total_files']} 文件 ({progress:.1f}%)"
                        )

                        # 智能建议
                        suggestion = self._get_smart_suggestion(stats)
                        if suggestion:
                            print(f"💡 建议: {suggestion}")
                else:
                    stats = summary.get("stats", {})
                    if stats.get("total_groups", 0) > 0:
                        progress = (
                            stats["completed_groups"] / stats["total_groups"] * 100
                        )
                        print(
                            f"📊 进度: {stats['completed_groups']}/{stats['total_groups']} 组 ({progress:.1f}%)"
                        )
            else:
                print("📊 状态: 尚未创建合并计划")
                print("💡 建议: 选择 1 (快速全流程) 或 3 (创建计划)")

        except Exception:
            print("📊 状态: 加载中...")

    def _get_smart_suggestion(self, stats):
        """获取智能建议"""
        if stats["assigned_files"] == 0:
            return "先执行自动分配 (选择 4)"
        elif stats["completed_files"] == 0:
            return "开始合并操作 (选择 8 或 9)"
        elif stats["completed_files"] < stats["total_files"]:
            return "继续完成剩余文件"
        else:
            return "执行最终合并 (选择 10)"

    # =================== 核心功能实现 ===================

    def _quick_workflow(self):
        """快速全流程"""
        self.commands.execute_quick_workflow()
        input("\n按回车键继续...")

    def _analyze_divergence(self):
        """分析分支分叉"""
        self.commands.execute_analyze_divergence()
        input("\n按回车键继续...")

    def _create_plan(self):
        """创建合并计划"""
        self.commands.execute_create_plan()
        input("\n按回车键继续...")

    def _auto_assign(self):
        """自动分配任务"""
        exclude_input = input("是否要排除特定人员？(输入姓名，多个用逗号分隔，直接回车跳过): ").strip()
        exclude_authors = (
            [name.strip() for name in exclude_input.split(",")]
            if exclude_input
            else None
        )

        self.commands.execute_auto_assign(exclude_authors)
        input("\n按回车键继续...")

    def _check_status(self):
        """检查项目状态"""
        self.commands.execute_check_status()
        input("\n按回车键继续...")

    def _advanced_query(self):
        """高级查询系统"""
        print("🔍 高级查询系统")
        print("1. 按负责人查询")
        print("2. 按文件路径查询")
        print("3. 按状态查询")
        print("4. 返回主菜单")

        choice = input("请选择查询类型 (1-4): ").strip()

        if choice == "1":
            assignee = input("请输入负责人姓名: ").strip()
            if assignee:
                self.orchestrator.search_files_by_assignee(assignee)
        elif choice == "2":
            if self.orchestrator.processing_mode == "file_level":
                directory = input("请输入目录路径: ").strip()
                if directory:
                    self.orchestrator.search_files_by_directory(directory)
            else:
                print("⚠️ 目录搜索功能仅在文件级模式下可用")
        elif choice == "3":
            print("状态类型: pending(待分配), assigned(已分配), in_progress(进行中), completed(已完成)")
            status = input("请输入状态: ").strip()
            if status:
                self._query_by_status(status)
        elif choice == "4":
            return
        else:
            DisplayHelper.print_warning("无效选择")

        input("\n按回车键继续...")

    def _query_by_status(self, status):
        """按状态查询文件"""
        # 标准化状态输入
        status_mapping = {
            "pending": "pending",
            "待分配": "pending",
            "assigned": "assigned",
            "已分配": "assigned",
            "in_progress": "in_progress",
            "进行中": "in_progress",
            "completed": "completed",
            "已完成": "completed",
        }

        normalized_status = status_mapping.get(status.lower(), status)

        if self.orchestrator.processing_mode == "file_level":
            # 文件级模式查询
            try:
                files = self.orchestrator.file_manager.get_files_by_status(
                    normalized_status
                )
                if files:
                    print(f"\n📊 状态为 '{status}' 的文件列表 ({len(files)} 个):")
                    print("-" * 50)

                    for i, file_info in enumerate(files[:20], 1):  # 最多显示20个
                        assignee = file_info.get("assignee", "未分配")
                        print(f"  {i:2d}. {file_info['path']}")
                        print(f"      👤 负责人: {assignee}")
                        if file_info.get("assignment_reason"):
                            print(
                                f"      📝 原因: {file_info['assignment_reason'][:40]}..."
                            )
                        print()

                    if len(files) > 20:
                        print(f"  ... 还有 {len(files) - 20} 个文件")

                    # 显示统计信息
                    assignee_stats = {}
                    for f in files:
                        assignee = f.get("assignee", "未分配")
                        assignee_stats[assignee] = assignee_stats.get(assignee, 0) + 1

                    print(f"\n👥 负责人分布:")
                    for assignee, count in sorted(
                        assignee_stats.items(), key=lambda x: x[1], reverse=True
                    ):
                        print(f"  {assignee}: {count} 个文件")

                else:
                    print(f"📭 未找到状态为 '{status}' 的文件")
            except Exception as e:
                print(f"❌ 查询失败: {e}")
        else:
            # 组模式查询
            print("⚠️ 按状态查询功能在文件级模式下效果最佳，当前为组模式")
            print("💡 建议使用功能5查看整体状态")

    def _search_assign_tasks(self):
        """搜索/分配任务"""
        print("👤 任务搜索与分配")
        print("1. 搜索负责人任务")
        print("2. 手动分配任务")
        print("3. 返回主菜单")

        choice = input("请选择操作 (1-3): ").strip()

        if choice == "1":
            assignee = input("请输入负责人姓名: ").strip()
            if assignee:
                self.orchestrator.search_assignee_tasks(assignee)
        elif choice == "2":
            if self.orchestrator.processing_mode == "file_level":
                file_path = input("请输入文件路径: ").strip()
                assignee = input("请输入负责人: ").strip()
                if file_path and assignee:
                    self.orchestrator.manual_assign_file(file_path, assignee)
            else:
                print("手动分配功能需要从传统菜单访问")
        elif choice == "3":
            return
        else:
            DisplayHelper.print_warning("无效选择")

        input("\n按回车键继续...")

    def _is_file_level_mode(self):
        """检查是否为文件级处理模式"""
        from pathlib import Path

        file_plan_path = Path(".merge_work/file_plan.json")
        return file_plan_path.exists()

    def _merge_file_or_group(self):
        """根据处理模式合并指定文件或组"""
        # 检查当前处理模式
        if self._is_file_level_mode():
            # 文件级模式：合并单个文件
            file_path = input("请输入要合并的文件路径: ").strip()
            if file_path:
                self.commands.execute_merge_file(file_path)
            else:
                print("❌ 文件路径不能为空")
        else:
            # 组模式：合并指定组
            group_name = input("请输入要合并的组名: ").strip()
            if group_name:
                self.commands.execute_merge_group(group_name)
            else:
                print("❌ 组名不能为空")
        input("\n按回车键继续...")

    def _batch_merge(self):
        """批量合并"""
        assignee = input("请输入负责人姓名: ").strip()
        if not assignee:
            # TODO: 显示负责人列表的功能
            print("💡 提示: 可以先使用功能7搜索现有负责人")
            assignee = input("请输入要批量合并的负责人姓名: ").strip()

        self.commands.execute_batch_merge(assignee)
        input("\n按回车键继续...")

    def _finalize_merge(self):
        """最终合并"""
        confirm = input("确定要执行最终合并吗？这将合并所有已完成的任务 (y/N): ").strip().lower()
        if confirm == "y":
            self.commands.execute_finalize_merge()
        else:
            print("❌ 最终合并已取消")
        input("\n按回车键继续...")

    def _system_settings(self):
        """系统设置"""
        while True:
            print("\n⚙️ 系统设置")
            print("-" * 30)
            print("a. 🔧 切换合并策略")
            print("b. 🚫 管理忽略规则")
            print("c. 📈 查看性能统计")
            print("d. 🗑️ 清理缓存")
            print("e. 🔄 切换处理模式")
            print("0. 返回主菜单")

            choice = input("\n请选择设置项 (a-e, 0): ").strip().lower()

            if choice == "a":
                if self.commands.switch_merge_strategy():
                    print("✅ 策略切换成功")
                else:
                    print("❌ 策略切换取消")
            elif choice == "b":
                print("🚫 忽略规则管理功能开发中，请手动编辑 .merge_ignore 文件")
            elif choice == "c":
                self.commands.show_performance_stats()
            elif choice == "d":
                self.commands.clean_cache()
            elif choice == "e":
                if self.commands.switch_processing_mode():
                    print("✅ 处理模式切换成功，请重新创建合并计划")
                else:
                    print("❌ 处理模式切换取消")
            elif choice == "0":
                break
            else:
                DisplayHelper.print_warning("无效选择")

            if choice != "0":
                input("\n按回车键继续...")

    def _show_help(self):
        """显示帮助信息"""
        self.commands.show_help()
        input("\n按回车键继续...")

    def _quit(self):
        """退出程序"""
        print("\n👋 感谢使用 Git Merge Orchestrator!")
        exit(0)
