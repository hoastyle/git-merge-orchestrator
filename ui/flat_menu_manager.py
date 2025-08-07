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
            "10": ("🏁 标记完成", self._mark_completion),
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
            
            # 显示增强分析状态
            if hasattr(self.orchestrator, 'use_enhanced_analysis'):
                analysis_status = "🚀 增强" if self.orchestrator.use_enhanced_analysis else "🔧 基础"
                print(f"🧠 分析: {analysis_status}")

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
                analysis_hint = "增强智能分析" if getattr(self.orchestrator, 'use_enhanced_analysis', False) else "基础分析"
                print(f"💡 建议: 选择 1 (快速全流程) 或 3 (创建计划) - 将使用{analysis_hint}")

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
                    from utils.display_utils import display_files_interactive

                    # 使用新的交互式显示功能
                    title = f"状态为 '{status}' 的文件"
                    context = f"状态: {status} ({len(files)} 个文件)"

                    display_files_interactive(
                        files,
                        title=title,
                        context=context,
                        work_dir=self.orchestrator.file_helper.work_dir,
                    )
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

    def _execute_finalize_merge(self):
        """执行最终合并（在系统设置中）"""
        confirm = input("确定要执行最终合并吗？这将合并所有已完成的任务 (y/N): ").strip().lower()
        if confirm == "y":
            self.commands.execute_finalize_merge()
        else:
            print("❌ 最终合并已取消")

    def _mark_completion(self):
        """标记完成 - 独立的完成标记菜单"""
        # 检查是否为文件级模式
        if not self._is_file_level_mode():
            print("❌ 完成标记功能仅在文件级模式下可用")
            print("💡 请先创建文件级合并计划")
            input("\n按回车键继续...")
            return

        self._show_completion_menu()

    def _show_completion_menu(self):
        """显示完成标记菜单"""
        while True:
            print("\n🏁 标记完成")
            print("=" * 50)

            # 显示当前状态概览
            try:
                stats = self.orchestrator.file_manager.get_completion_stats()
                print(f"📊 任务概览:")
                print(f"  总文件数: {stats['total_files']}")
                print(
                    f"  已完成: {stats['completed_files']} ({stats['completion_rate']:.1f}%)"
                )
                print(f"  待处理: {stats['pending_files']}")
                print(f"  进行中: {stats['in_progress_files']}")
            except Exception as e:
                print(f"⚠️ 无法获取状态信息: {e}")

            print(f"\n📝 标记选项:")
            print("1. 🎯 标记单个文件完成")
            print("2. 📋 标记负责人的所有任务完成")
            print("3. 📁 标记整个目录完成")
            print("4. 🔍 查看完成详情")
            print("5. 🌐 自动检测远程分支状态")
            print("6. 📊 查看团队整体进度")
            print("0. 返回主菜单")

            choice = input("\n请选择 (1-6, 0): ").strip()

            if choice == "1":
                self._mark_single_file()
            elif choice == "2":
                self._mark_assignee_tasks()
            elif choice == "3":
                self._mark_directory_tasks()
            elif choice == "4":
                self._view_completion_details()
            elif choice == "5":
                self._auto_detect_remote_status()
            elif choice == "6":
                self._view_team_progress()
            elif choice == "0":
                break
            else:
                print("❌ 无效选择，请输入0-6")

            if choice != "0":
                input("\n按回车键继续...")

    def _mark_single_file(self):
        """标记单个文件完成"""
        file_path = input("请输入要标记完成的文件路径: ").strip()
        if not file_path:
            print("❌ 文件路径不能为空")
            return

        notes = input("请输入完成备注 (可选): ").strip()

        success = self.orchestrator.mark_file_completed(file_path, notes)
        if success:
            print(f"✅ 文件 '{file_path}' 已标记为完成")

    def _mark_assignee_tasks(self):
        """标记负责人的所有任务完成"""
        assignee = input("请输入负责人姓名: ").strip()
        if not assignee:
            print("❌ 负责人姓名不能为空")
            return

        # 先显示该负责人的任务概览
        try:
            files = self.orchestrator.file_manager.get_files_by_assignee(assignee)
            if not files:
                print(f"❌ 负责人 '{assignee}' 没有分配的任务")
                return

            pending_files = [f for f in files if f["status"] != "completed"]
            completed_files = [f for f in files if f["status"] == "completed"]

            print(f"\n📊 负责人 '{assignee}' 任务概览:")
            print(f"  总文件数: {len(files)}")
            print(f"  已完成: {len(completed_files)}")
            print(f"  待完成: {len(pending_files)}")

            if len(pending_files) == 0:
                print("✅ 该负责人的所有任务已完成")
                return

            confirm = (
                input(
                    f"\n确定要标记 '{assignee}' 的所有 {len(pending_files)} 个待完成任务为已完成吗? (y/N): "
                )
                .strip()
                .lower()
            )
            if confirm == "y":
                success = self.orchestrator.mark_assignee_completed(assignee)
                if success:
                    print(f"✅ 负责人 '{assignee}' 的所有任务已标记完成")
            else:
                print("❌ 操作已取消")

        except Exception as e:
            print(f"❌ 操作失败: {e}")

    def _mark_directory_tasks(self):
        """标记整个目录完成"""
        directory = input("请输入目录路径: ").strip()
        if not directory:
            print("❌ 目录路径不能为空")
            return

        success = self.orchestrator.mark_directory_completed(directory)
        if success:
            print(f"✅ 目录 '{directory}' 的所有文件已标记完成")

    def _view_completion_details(self):
        """查看完成详情"""
        try:
            stats = self.orchestrator.file_manager.get_completion_stats()
            workload = self.orchestrator.file_manager.get_workload_distribution()

            print(f"\n📈 详细完成统计:")
            print(f"  总文件数: {stats['total_files']}")
            print(
                f"  已完成: {stats['completed_files']} ({stats['completion_rate']:.1f}%)"
            )
            print(f"  已分配: {stats['assigned_files']} ({stats['assignment_rate']:.1f}%)")
            print(f"  待处理: {stats['pending_files']}")
            print(f"  进行中: {stats['in_progress_files']}")

            if workload:
                print(f"\n👥 负责人完成情况:")
                sorted_workload = sorted(
                    workload.items(), key=lambda x: x[1]["completed"], reverse=True
                )

                for assignee, load_info in sorted_workload[:10]:
                    assigned = load_info["assigned"]
                    completed = load_info["completed"]
                    pending = load_info["pending"]
                    completion_rate = (
                        (completed / assigned * 100) if assigned > 0 else 0
                    )

                    print(
                        f"  {assignee}: {completed}/{assigned} 完成 ({completion_rate:.1f}%)"
                    )

        except Exception as e:
            print(f"❌ 获取详情失败: {e}")

    def _auto_detect_remote_status(self):
        """自动检测远程分支状态"""
        print("🔍 正在检查远程分支状态...")
        success = self.orchestrator.auto_check_remote_status()
        if success:
            print("✅ 远程分支状态检查完成")
        else:
            print("❌ 远程分支状态检查失败")

    def _view_team_progress(self):
        """查看团队整体进度"""
        self.commands.execute_check_status()

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
            print("f. 🎉 执行最终合并")
            print("0. 返回主菜单")

            choice = input("\n请选择设置项 (a-f, 0): ").strip().lower()

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
            elif choice == "f":
                self._execute_finalize_merge()
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
