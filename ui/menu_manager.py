"""
Git Merge Orchestrator - 优化的菜单管理器
将16个选项重新组织为分层菜单结构，提升用户体验
"""

from ui.display_helper import DisplayHelper
from typing import Optional, Callable, Dict, Any


class MenuManager:
    """菜单管理器 - 分层菜单设计"""

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.menu_stack = []  # 菜单历史栈
        self.current_menu = None

    def run_interactive_menu(self):
        """运行优化后的交互式菜单系统"""
        try:
            while True:
                self.show_main_menu()

                try:
                    choice = input("\n请选择功能分类 (0-6): ").strip()

                    if choice == "0":
                        print("👋 感谢使用Git Merge Orchestrator！")
                        break
                    elif choice == "1":
                        self._handle_quick_start_menu()
                    elif choice == "2":
                        self._handle_project_management_menu()
                    elif choice == "3":
                        self._handle_task_assignment_menu()
                    elif choice == "4":
                        self._handle_merge_execution_menu()
                    elif choice == "5":
                        self._handle_system_management_menu()
                    elif choice == "6":
                        self._handle_advanced_features_menu()
                    else:
                        DisplayHelper.print_warning("无效选择，请输入0-6之间的数字")

                except KeyboardInterrupt:
                    print("\n\n👋 用户中断，正在退出...")
                    break
                except Exception as e:
                    DisplayHelper.print_error(f"操作过程中出现错误: {e}")
                    print("请检查输入并重试，或选择其他操作")

        except KeyboardInterrupt:
            print("\n\n👋 用户中断，正在退出...")

    def show_main_menu(self):
        """显示主菜单"""
        print("\n" + "=" * 80)
        print("🚀 Git Merge Orchestrator 主菜单")
        print("=" * 80)

        # 显示项目状态摘要
        self._show_project_summary()

        print("\n📋 选择功能分类:")
        print("1. 🚀 快速开始向导 (新用户推荐)")
        print("2. 📊 项目管理 (计划、状态、分析)")
        print("3. 👥 任务分配 (分配、查看、搜索)")
        print("4. 🔄 执行合并 (组合并、批量合并)")
        print("5. ⚙️  系统管理 (策略、缓存、状态)")
        print("6. 🎯 高级功能 (详细分析、调试)")
        print("0. 退出")

    def _show_project_summary(self):
        """显示项目状态摘要"""
        try:
            # 显示处理模式信息
            mode_info = self.orchestrator.get_processing_mode_info()
            print(f"🔧 处理模式: {mode_info['mode_name']}")

            summary = self.orchestrator.get_plan_summary()
            if summary:
                strategy = summary["merge_strategy"]
                print(f"⚙️ 合并策略: {strategy['mode_name']}")

                if self.orchestrator.processing_mode == "file_level":
                    # 文件级模式显示
                    stats = summary.get("completion_stats", {})
                    if stats.get("total_files", 0) > 0:
                        print(
                            f"📊 项目状态: {stats['completed_files']}/{stats['total_files']} 文件已完成"
                        )
                        progress = stats.get("completion_rate", 0)
                        print(f"📈 完成进度: {progress:.1f}%")

                        # 显示下一步建议
                        if stats["assigned_files"] == 0:
                            print("💡 建议: 创建文件级计划后进行任务分配")
                        elif stats["completed_files"] == 0:
                            print("💡 建议: 开始处理分配的文件")
                        elif stats["completed_files"] < stats["total_files"]:
                            print("💡 建议: 继续完成剩余文件")
                        else:
                            print("💡 建议: 执行最终合并")
                    else:
                        print("📊 项目状态: 尚未创建文件级合并计划")
                else:
                    # 传统组模式显示
                    stats = summary.get("stats", {})
                    if stats.get("total_groups", 0) > 0:
                        print(
                            f"📊 项目状态: {stats['completed_groups']}/{stats['total_groups']} 组已完成"
                        )
                        progress = (
                            stats["completed_groups"] / stats["total_groups"] * 100
                        )
                        print(f"📈 完成进度: {progress:.1f}%")

                        # 显示下一步建议
                        if stats["assigned_groups"] == 0:
                            print("💡 建议: 创建计划后进行任务分配")
                        elif stats["completed_groups"] == 0:
                            print("💡 建议: 开始执行合并操作")
                        elif stats["completed_groups"] < stats["total_groups"]:
                            print("💡 建议: 继续合并剩余任务")
                        else:
                            print("💡 建议: 执行最终合并")
                    else:
                        print("📊 项目状态: 尚未创建合并计划")
            else:
                print("📊 项目状态: 尚未创建合并计划")
                print("💡 建议: 使用快速开始向导或创建合并计划")
        except Exception:
            print("📊 项目状态: 信息获取中...")

    # === 快速开始向导 ===

    def _handle_quick_start_menu(self):
        """处理快速开始向导"""
        while True:
            self._show_quick_start_menu()
            choice = input("\n请选择操作 (a-d): ").strip().lower()

            if choice == "a":
                self._execute_full_workflow()
            elif choice == "b":
                self._continue_existing_project()
            elif choice == "c":
                self._show_workflow_guide()
            elif choice == "d":
                break
            else:
                DisplayHelper.print_warning("无效选择，请输入a-d")

    def _show_quick_start_menu(self):
        """显示快速开始向导菜单"""
        print("\n🚀 快速开始向导")
        print("=" * 50)

        # 检测当前状态并提供建议
        plan = self.orchestrator.file_helper.load_plan()

        if not plan:
            print("💡 检测到：尚未创建合并计划")
            print("\n🎯 推荐操作：")
            print("a. 🔥 全流程引导 (分析→计划→分配→合并)")
            print("b. 📋 查看工作流程说明")
            print("c. 🎓 学习最佳实践")
            print("d. 返回主菜单")
        else:
            stats = self.orchestrator.file_helper.get_completion_stats(plan)
            if stats["assigned_groups"] == 0:
                print("💡 检测到：计划已创建，尚未分配任务")
                print("\n🎯 推荐操作：")
                print("a. ⚡ 自动分配任务")
                print("b. ✋ 手动分配任务")
                print("c. 📊 查看当前状态")
                print("d. 返回主菜单")
            elif stats["completed_groups"] < stats["total_groups"]:
                print("💡 检测到：任务已分配，进行中")
                print("\n🎯 推荐操作：")
                print("a. 🔄 继续合并操作")
                print("b. 📈 检查进度状态")
                print("c. ⚙️  管理任务状态")
                print("d. 返回主菜单")
            else:
                print("💡 检测到：所有任务已完成")
                print("\n🎯 推荐操作：")
                print("a. 🎉 执行最终合并")
                print("b. 📋 查看完成报告")
                print("c. 🆕 开始新项目")
                print("d. 返回主菜单")

    def _execute_full_workflow(self):
        """执行完整工作流程"""
        print("\n🚀 开始全流程引导模式...")

        # 1. 分析分支分叉
        print("\n📍 步骤 1/4: 分析分支分叉")
        if not self.orchestrator.analyze_divergence():
            DisplayHelper.print_error("分支分叉分析失败，请检查分支状态")
            return

        # 2. 创建合并计划
        print("\n📍 步骤 2/4: 创建智能合并计划")
        if not self.orchestrator.create_merge_plan():
            DisplayHelper.print_error("合并计划创建失败")
            return

        # 3. 自动分配任务
        print("\n📍 步骤 3/4: 智能自动分配任务")
        if not self.orchestrator.auto_assign_tasks():
            DisplayHelper.print_error("任务分配失败")
            return

        # 4. 显示下一步指导
        print("\n📍 步骤 4/4: 准备执行合并")
        print("✅ 全流程设置完成！")
        print("\n🎯 下一步操作:")
        print("1. 查看任务分配结果：主菜单 → 3. 任务分配 → d. 搜索负责人任务")
        print("2. 开始合并操作：主菜单 → 4. 执行合并")
        print("3. 查看详细状态：主菜单 → 2. 项目管理 → c. 检查项目状态")

        input("\n按回车键继续...")

    def _continue_existing_project(self):
        """继续现有项目"""
        plan = self.orchestrator.file_helper.load_plan()
        if not plan:
            DisplayHelper.print_warning("没有找到现有项目计划")
            return

        stats = self.orchestrator.file_helper.get_completion_stats(plan)
        print(f"\n📊 项目状态:")
        print(f"   总分组: {stats['total_groups']}")
        print(f"   已分配: {stats['assigned_groups']}")
        print(f"   已完成: {stats['completed_groups']}")

        # 根据状态提供建议
        if stats["assigned_groups"] == 0:
            print("\n💡 建议: 进行任务分配")
            if input("是否现在自动分配任务? (y/N): ").strip().lower() == "y":
                self.orchestrator.auto_assign_tasks()
        elif stats["completed_groups"] < stats["total_groups"]:
            print("\n💡 建议: 继续执行合并操作")
            print("可以使用主菜单 → 4. 执行合并 来继续")
        else:
            print("\n💡 建议: 执行最终合并")
            if input("是否现在执行最终合并? (y/N): ").strip().lower() == "y":
                self.orchestrator.finalize_merge()

    def _show_workflow_guide(self):
        """显示工作流程指导"""
        print("\n📖 Git Merge Orchestrator 工作流程指导")
        print("=" * 60)
        print("\n🔄 标准工作流程:")
        print("1. 📊 分析分支分叉 - 了解两个分支的差异情况")
        print("2. 📋 创建合并计划 - 智能分组文件，生成合并策略")
        print("3. 👥 分配任务 - 根据贡献度自动或手动分配负责人")
        print("4. 🔄 执行合并 - 按组或按负责人执行合并操作")
        print("5. ✅ 状态管理 - 跟踪进度，标记完成状态")
        print("6. 🎉 最终合并 - 将所有分支合并到集成分支")

        print("\n💡 最佳实践:")
        print("• 使用涡轮增压自动分配，提高效率")
        print("• 选择合适的合并策略 (Legacy快速 vs Standard安全)")
        print("• 定期检查进度状态，及时处理问题")
        print("• 利用交互式合并处理复杂冲突")

        print("\n🎯 新用户建议:")
        print("1. 首次使用选择 Legacy 策略，熟悉流程")
        print("2. 小团队或信任度高的项目使用 Legacy 模式")
        print("3. 大型项目或需要精确控制使用 Standard 模式")

        input("\n按回车键返回...")

    # === 项目管理 ===

    def _handle_project_management_menu(self):
        """处理项目管理菜单"""
        while True:
            self._show_project_management_menu()
            choice = input("\n请选择操作 (a-f): ").strip().lower()

            if choice == "a":
                self.orchestrator.analyze_divergence()
            elif choice == "b":
                self.orchestrator.create_merge_plan()
            elif choice == "c":
                self._handle_status_check_submenu()
            elif choice == "d":
                self.orchestrator.show_assignment_reasons()
            elif choice == "e":
                self._show_project_report()
            elif choice == "f":
                break
            else:
                DisplayHelper.print_warning("无效选择，请输入a-f")

    def _show_project_management_menu(self):
        """显示项目管理菜单"""
        print("\n📊 项目管理")
        print("=" * 40)
        print("a. 🔍 分析分支分叉")
        print("b. 📋 创建智能合并计划")
        print("c. 📈 检查项目状态")
        print("d. 📊 查看分配原因分析")
        print("e. 📄 生成项目报告")
        print("f. 返回主菜单")

    def _handle_status_check_submenu(self):
        """处理状态检查子菜单"""
        print("\n📊 检查状态选项:")
        print("a. 标准表格显示")
        print("b. 完整组名显示")
        print("c. 简要状态摘要")
        print("d. 返回上级菜单")

        sub_choice = input("请选择显示模式 (a-d): ").strip().lower()
        if sub_choice == "a":
            self.orchestrator.check_status(show_full_names=False)
        elif sub_choice == "b":
            self.orchestrator.check_status(show_full_names=True)
        elif sub_choice == "c":
            self._show_status_summary()
        elif sub_choice == "d":
            return
        else:
            DisplayHelper.print_warning("无效选择")

    def _show_status_summary(self):
        """显示状态摘要"""
        try:
            summary = self.orchestrator.get_plan_summary()
            if summary and summary.get("stats"):
                stats = summary["stats"]
                strategy = summary["merge_strategy"]

                print("\n📊 项目状态摘要")
                print("=" * 40)
                print(f"📁 总分组数: {stats['total_groups']}")
                print(f"📄 总文件数: {stats['total_files']}")
                print(
                    f"👥 已分配组: {stats['assigned_groups']} ({stats['assigned_files']} 文件)"
                )
                print(
                    f"✅ 已完成组: {stats['completed_groups']} ({stats['completed_files']} 文件)"
                )
                print(f"🔧 合并策略: {strategy['mode_name']}")

                if stats["total_groups"] > 0:
                    progress = stats["completed_groups"] / stats["total_groups"] * 100
                    print(f"📈 总体进度: {progress:.1f}%")

                    # 估算剩余工作
                    remaining_groups = stats["total_groups"] - stats["completed_groups"]
                    remaining_files = stats["total_files"] - stats["completed_files"]
                    print(f"⏳ 剩余工作: {remaining_groups} 组, {remaining_files} 文件")
            else:
                print("📊 尚未创建合并计划")
        except Exception as e:
            DisplayHelper.print_error(f"获取状态摘要失败: {e}")

    def _show_project_report(self):
        """生成项目报告"""
        print("\n📄 项目完整报告")
        print("=" * 60)

        # 基本信息
        print(f"🎯 源分支: {self.orchestrator.source_branch}")
        print(f"🎯 目标分支: {self.orchestrator.target_branch}")
        print(f"📁 仓库路径: {self.orchestrator.repo_path}")

        # 策略信息
        strategy_info = self.orchestrator.get_merge_strategy_info()
        print(f"🔧 合并策略: {strategy_info['mode_name']}")
        print(f"📝 策略描述: {strategy_info['description']}")

        # 项目状态
        self._show_status_summary()

        # 性能统计
        try:
            perf_stats = self.orchestrator.contributor_analyzer.get_performance_stats()
            print(f"\n⚡ 性能统计:")
            print(f"   缓存文件数: {perf_stats['cached_files']}")
            print(f"   缓存目录数: {perf_stats['cached_directories']}")
            print(f"   批量计算: {'✅' if perf_stats['batch_computed'] else '❌'}")
        except:
            print("\n⚡ 性能统计: 数据获取中...")

    # === 任务分配 ===

    def _handle_task_assignment_menu(self):
        """处理任务分配菜单"""
        while True:
            self._show_task_assignment_menu()

            if self.orchestrator.processing_mode == "file_level":
                valid_choices = "a-i"
                choice = input(f"\n请选择操作 ({valid_choices}): ").strip().lower()
            else:
                valid_choices = "a-f"
                choice = input(f"\n请选择操作 ({valid_choices}): ").strip().lower()

            if choice == "a":
                self._handle_auto_assign_submenu()
            elif choice == "b":
                self._handle_manual_assign_submenu()
            elif choice == "c":
                self.orchestrator.show_contributor_analysis()
            elif choice == "d":
                self._handle_search_assignee_submenu()
            elif choice == "e":
                break
            elif choice == "f":
                if self.orchestrator.processing_mode == "file_level":
                    self._handle_search_directory_submenu()
                else:
                    self.orchestrator.switch_processing_mode()
            elif choice == "g" and self.orchestrator.processing_mode == "file_level":
                self._handle_load_balancing_submenu()
            elif choice == "h" and self.orchestrator.processing_mode == "file_level":
                self._handle_file_detail_submenu()
            elif choice == "i" and self.orchestrator.processing_mode == "file_level":
                self.orchestrator.switch_processing_mode()
            else:
                DisplayHelper.print_warning(f"无效选择，请输入{valid_choices}")

    def _show_task_assignment_menu(self):
        """显示任务分配菜单"""
        mode_name = self.orchestrator.get_processing_mode_info()["mode_name"]
        print(f"\n👥 任务分配 - {mode_name}")
        print("=" * 40)
        print("a. 🚀 智能自动分配")
        print("b. ✋ 手动分配任务")
        print("c. 📊 查看贡献者分析")
        print("d. 🔍 搜索负责人任务")

        if self.orchestrator.processing_mode == "file_level":
            print("f. 📁 按目录搜索文件")
            print("g. ⚖️ 负载均衡")
            print("h. 📋 查看文件详情")
            print("i. 🔄 切换处理模式")
        else:
            print("f. 🔄 切换处理模式")

        print("e. 返回主菜单")

    def _handle_auto_assign_submenu(self):
        """处理自动分配子菜单"""
        if self.orchestrator.processing_mode == "file_level":
            print("🚀 文件级智能自动分配 (基于文件贡献度分析)")
        else:
            print("🤖 涡轮增压智能自动分配模式 (活跃度过滤+备选方案)")

        exclude_input = input("请输入要排除的作者列表 (用逗号分隔，回车跳过): ").strip()
        exclude_authors = (
            [name.strip() for name in exclude_input.split(",")] if exclude_input else []
        )

        if self.orchestrator.processing_mode == "file_level":
            max_tasks_input = input("每人最大文件数 (默认50): ").strip()
            max_tasks = int(max_tasks_input) if max_tasks_input.isdigit() else 50
        else:
            max_tasks_input = input("每人最大任务数 (默认3): ").strip()
            max_tasks = int(max_tasks_input) if max_tasks_input.isdigit() else 3

        fallback_input = input("启用备选分配方案? (Y/n): ").strip().lower()
        include_fallback = fallback_input != "n"

        self.orchestrator.auto_assign_tasks(
            exclude_authors, max_tasks, include_fallback
        )

    def _handle_manual_assign_submenu(self):
        """处理手动分配子菜单"""
        assignments = {}
        print("请输入任务分配 (格式: 组名=负责人，输入空行结束):")
        print("💡 提示: 可以先查看组列表，然后返回进行分配")

        show_groups = input("是否先查看组列表? (y/N): ").strip().lower()
        if show_groups == "y":
            self.orchestrator.view_group_details()
            print("\n现在请输入分配信息:")

        while True:
            line = input().strip()
            if not line:
                break
            if "=" in line:
                group, assignee = line.split("=", 1)
                assignments[group.strip()] = assignee.strip()

        if assignments:
            self.orchestrator.manual_assign_tasks(assignments)
        else:
            DisplayHelper.print_warning("未输入任何分配信息")

    # === 执行合并 ===

    def _handle_merge_execution_menu(self):
        """处理执行合并菜单"""
        while True:
            self._show_merge_execution_menu()
            choice = input("\n请选择操作 (a-e): ").strip().lower()

            if choice == "a":
                group_name = input("请输入要合并的组名: ").strip()
                if group_name:
                    self.orchestrator.merge_group(group_name)
                else:
                    DisplayHelper.print_warning("组名不能为空")
            elif choice == "b":
                assignee_name = input("请输入要合并任务的负责人姓名: ").strip()
                if assignee_name:
                    self.orchestrator.merge_assignee_tasks(assignee_name)
                else:
                    DisplayHelper.print_warning("负责人姓名不能为空")
            elif choice == "c":
                self._handle_interactive_merge_submenu()
            elif choice == "d":
                self.orchestrator.finalize_merge()
            elif choice == "e":
                break
            else:
                DisplayHelper.print_warning("无效选择，请输入a-e")

    def _show_merge_execution_menu(self):
        """显示执行合并菜单"""
        print("\n🔄 执行合并")
        print("=" * 40)
        print("a. 📁 合并指定组")
        print("b. 👤 合并指定负责人的所有任务")
        print("c. 🎯 交互式智能合并")
        print("d. 🎉 完成最终合并")
        print("e. 返回主菜单")

    def _handle_interactive_merge_submenu(self):
        """处理交互式合并子菜单"""
        print("🎯 交互式智能合并:")
        print("a. 交互式合并指定组")
        print("b. 交互式合并指定负责人的所有任务 (开发中)")
        print("c. 返回上级菜单")

        sub_choice = input("请选择操作 (a-c): ").strip().lower()
        if sub_choice == "a":
            group_name = input("请输入要交互式合并的组名: ").strip()
            if group_name:
                self.orchestrator.interactive_merge_group(group_name)
            else:
                DisplayHelper.print_warning("组名不能为空")

        elif sub_choice == "b":
            assignee_name = input("请输入负责人姓名: ").strip()
            if assignee_name:
                print("🔄 交互式批量合并功能开发中...")
                print("💡 建议：先使用单组交互式合并，积累经验后再批量处理")
                print("📋 您可以:")
                print("   1. 使用菜单3查看该负责人的所有任务")
                print("   2. 逐个使用交互式合并处理每个组")
                print("   3. 对于简单组，使用菜单4的自动合并")
            else:
                DisplayHelper.print_warning("负责人姓名不能为空")

        elif sub_choice == "c":
            return
        else:
            DisplayHelper.print_warning("无效选择")

    # === 系统管理 ===
    def _handle_system_management_menu(self):
        """处理系统管理菜单"""
        while True:
            self._show_system_management_menu()
            choice = input("\n请选择操作 (a-f): ").strip().lower()

            if choice == "a":
                self._handle_merge_strategy_submenu()
            elif choice == "b":
                self._handle_cache_management_submenu()
            elif choice == "c":
                self._handle_status_management_submenu()
            elif choice == "d":
                self._handle_ignore_rules_menu()
            elif choice == "e":
                self.orchestrator.view_group_details()
            elif choice == "f":
                break
            else:
                DisplayHelper.print_warning("无效选择，请输入a-f")

    def _show_system_management_menu(self):
        """显示系统管理菜单"""
        print("\n⚙️ 系统管理")
        print("=" * 40)
        print("a. 🔧 合并策略管理")
        print("b. ⚡ 缓存管理")
        print("c. ✅ 完成状态管理")
        print("d. 🚫 忽略规则管理")
        print("e. 📋 查看分组详细信息")
        print("f. 返回主菜单")

    def _handle_merge_strategy_submenu(self):
        """处理合并策略管理子菜单"""
        print("🔧 合并策略管理:")
        print("a. 查看当前策略状态")
        print("b. 切换合并策略")
        print("c. 策略对比说明")
        print("d. 返回上级菜单")

        sub_choice = input("请选择操作 (a-d): ").strip().lower()
        if sub_choice == "a":
            self.orchestrator.show_merge_strategy_status()

        elif sub_choice == "b":
            if self.orchestrator.switch_merge_strategy():
                print("💡 策略切换成功，后续合并操作将使用新策略")
            else:
                print("⚠️ 策略切换取消")

        elif sub_choice == "c":
            self._show_strategy_comparison()

        elif sub_choice == "d":
            return
        else:
            DisplayHelper.print_warning("无效选择")

    def _show_strategy_comparison(self):
        """显示策略对比"""
        print("📊 合并策略详细对比:")
        print("=" * 80)

        modes = self.orchestrator.merge_executor_factory.list_available_modes()
        for mode_info in modes:
            print(f"🔧 {mode_info['name']}")
            print(f"   描述: {mode_info['description']}")
            print(f"   优点: {', '.join(mode_info['pros'])}")
            print(f"   缺点: {', '.join(mode_info['cons'])}")
            print(f"   {mode_info['suitable']}")
            print()

        print("💡 选择建议:")
        print("   - 如果确信源分支内容正确，需要快速合并 → 选择Legacy模式")
        print("   - 如果需要精确控制，保证代码质量 → 选择Standard模式")
        print("   - 大型团队协作，多人修改同一文件 → 建议Standard模式")
        print("   - 小型团队，信任度高的合并 → 可以选择Legacy模式")

        print("\n🎯 使用场景:")
        print("   Legacy适合: 热修复、简单功能合并、紧急发布")
        print("   Standard适合: 大版本合并、复杂功能整合、多人协作")

    def _handle_cache_management_submenu(self):
        """处理缓存管理子菜单"""
        print("⚡ 缓存管理:")
        print("a. 查看缓存状态")
        print("b. 清理缓存")
        print("c. 强制重建缓存")
        print("d. 返回上级菜单")

        sub_choice = input("请选择操作 (a-d): ").strip().lower()
        if sub_choice == "a":
            stats = self.orchestrator.contributor_analyzer.get_performance_stats()
            print("📊 缓存状态:")
            print(f"   缓存文件数: {stats['cached_files']}")
            print(f"   缓存目录数: {stats['cached_directories']}")
            print(f"   缓存文件存在: {'✅' if stats['cache_file_exists'] else '❌'}")
            print(f"   批量计算状态: {'✅' if stats['batch_computed'] else '❌'}")

        elif sub_choice == "b":
            cache_file = self.orchestrator.contributor_analyzer.cache_file
            if cache_file.exists():
                cache_file.unlink()
                print("✅ 缓存已清理")
            else:
                print("ℹ️ 缓存文件不存在")

        elif sub_choice == "c":
            # 清理内存缓存，强制重新计算
            self.orchestrator.contributor_analyzer._file_contributors_cache = {}
            self.orchestrator.contributor_analyzer._directory_contributors_cache = {}
            self.orchestrator.contributor_analyzer._batch_computed = False
            print("✅ 缓存已重置，下次分析将重新计算")

        elif sub_choice == "d":
            return
        else:
            DisplayHelper.print_warning("无效选择")

    def _handle_status_management_submenu(self):
        """处理状态管理子菜单"""
        print("📋 完成状态管理:")
        print("a. 标记组完成")
        print("b. 标记负责人所有任务完成")
        print("c. 自动检查远程分支状态")
        print("d. 返回上级菜单")

        sub_choice = input("请选择操作 (a-d): ").strip().lower()
        if sub_choice == "a":
            group_name = input("请输入已完成的组名: ").strip()
            self.orchestrator.mark_group_completed(group_name)
        elif sub_choice == "b":
            assignee_name = input("请输入负责人姓名: ").strip()
            self.orchestrator.mark_assignee_completed(assignee_name)
        elif sub_choice == "c":
            self.orchestrator.auto_check_remote_status()
        elif sub_choice == "d":
            return
        else:
            DisplayHelper.print_warning("无效选择")

    # === 高级功能 ===

    def _handle_advanced_features_menu(self):
        """处理高级功能菜单"""
        while True:
            self._show_advanced_features_menu()
            choice = input("\n请选择操作 (a-f): ").strip().lower()

            if choice == "a":
                self.orchestrator.show_contributor_analysis()
            elif choice == "b":
                self._show_performance_report()
            elif choice == "c":
                self._handle_query_system_menu()
            elif choice == "d":
                self._handle_custom_script_generation()
            elif choice == "e":
                self._enter_debug_mode()
            elif choice == "f":
                break
            else:
                DisplayHelper.print_warning("无效选择，请输入a-f")

    def _show_advanced_features_menu(self):
        """显示高级功能菜单"""
        print("\n🎯 高级功能")
        print("=" * 40)
        print("a. 👥 详细贡献者分析")
        print("b. 📊 性能统计报告")
        print("c. 🔍 高级查询系统")
        print("d. 🛠️ 自定义脚本生成")
        print("e. 🐛 调试模式")
        print("f. 返回主菜单")

    def _show_performance_report(self):
        """显示性能报告"""
        print("\n📊 性能统计报告")
        print("=" * 50)

        try:
            # 贡献者分析性能
            perf_stats = self.orchestrator.contributor_analyzer.get_performance_stats()
            print("⚡ 贡献者分析性能:")
            print(f"   缓存文件数: {perf_stats['cached_files']}")
            print(f"   缓存目录数: {perf_stats['cached_directories']}")
            print(f"   批量计算: {'✅' if perf_stats['batch_computed'] else '❌'}")
            print(f"   缓存文件存在: {'✅' if perf_stats['cache_file_exists'] else '❌'}")

            # 项目统计
            summary = self.orchestrator.get_plan_summary()
            if summary and summary.get("stats"):
                stats = summary["stats"]
                print(f"\n📈 项目统计:")
                print(f"   总文件数: {stats['total_files']}")
                print(f"   总分组数: {stats['total_groups']}")
                print(
                    f"   平均每组文件数: {stats['total_files']/stats['total_groups']:.1f}"
                    if stats["total_groups"] > 0
                    else "   平均每组文件数: 0"
                )

                # 效率统计
                if stats["completed_groups"] > 0:
                    completion_rate = (
                        stats["completed_groups"] / stats["total_groups"] * 100
                    )
                    print(f"   完成率: {completion_rate:.1f}%")

            # Git仓库信息
            print(f"\n🗃️ 仓库信息:")
            print(f"   仓库路径: {self.orchestrator.repo_path}")
            print(f"   源分支: {self.orchestrator.source_branch}")
            print(f"   目标分支: {self.orchestrator.target_branch}")

        except Exception as e:
            DisplayHelper.print_error(f"获取性能报告失败: {e}")

    def _handle_custom_script_generation(self):
        """处理自定义脚本生成"""
        print("\n🛠️ 自定义脚本生成")
        print("=" * 40)
        print("a. 生成批量状态检查脚本")
        print("b. 生成团队通知脚本")
        print("c. 生成进度报告脚本")
        print("d. 返回上级菜单")

        choice = input("请选择要生成的脚本类型 (a-d): ").strip().lower()
        if choice == "a":
            print("🔄 批量状态检查脚本生成功能开发中...")
        elif choice == "b":
            print("🔄 团队通知脚本生成功能开发中...")
        elif choice == "c":
            print("🔄 进度报告脚本生成功能开发中...")
        elif choice == "d":
            return
        else:
            DisplayHelper.print_warning("无效选择")

    def _enter_debug_mode(self):
        """进入调试模式"""
        print("\n🐛 调试模式")
        print("=" * 40)
        print("⚠️ 调试模式提供底层系统信息，仅供开发者使用")

        confirm = input("确认进入调试模式? (y/N): ").strip().lower()
        if confirm != "y":
            return

        print("\n🔧 系统调试信息:")

        # Git状态
        print("📡 Git连接测试:")
        result = self.orchestrator.git_ops.run_command("git --version")
        print(f"   Git版本: {result if result else '获取失败'}")

        # 分支信息
        current_branch = self.orchestrator.git_ops.run_command(
            "git branch --show-current"
        )
        print(f"   当前分支: {current_branch if current_branch else '获取失败'}")

        # 文件系统
        print(f"\n💾 文件系统:")
        print(f"   工作目录: {self.orchestrator.file_helper.work_dir}")
        print(
            f"   工作目录存在: {'✅' if self.orchestrator.file_helper.work_dir.exists() else '❌'}"
        )
        print(
            f"   计划文件存在: {'✅' if self.orchestrator.file_helper.plan_file_path.exists() else '❌'}"
        )

        # 模块状态
        print(f"\n🧩 模块状态:")
        print(f"   贡献者分析器: {'✅' if self.orchestrator.contributor_analyzer else '❌'}")
        print(f"   任务分配器: {'✅' if self.orchestrator.task_assigner else '❌'}")
        print(f"   合并执行器工厂: {'✅' if self.orchestrator.merge_executor_factory else '❌'}")

        input("\n按回车键退出调试模式...")

    # === 忽略规则管理 ===
    def _handle_ignore_rules_menu(self):
        """处理忽略规则管理菜单"""
        while True:
            self._show_ignore_rules_menu()
            choice = input("\n请选择操作 (a-h): ").strip().lower()

            if choice == "a":
                self._show_ignore_rules_list()
            elif choice == "b":
                self._add_ignore_rule()
            elif choice == "c":
                self._remove_ignore_rule()
            elif choice == "d":
                self._toggle_ignore_rule()
            elif choice == "e":
                self._test_ignore_pattern()
            elif choice == "f":
                self._export_ignore_file()
            elif choice == "g":
                self._show_ignore_stats()
            elif choice == "h":
                break
            else:
                DisplayHelper.print_warning("无效选择，请输入a-h")

    def _show_ignore_rules_menu(self):
        """显示忽略规则管理菜单"""
        print("\n🚫 忽略规则管理")
        print("=" * 40)
        print("a. 📋 查看忽略规则列表")
        print("b. ➕ 添加忽略规则")
        print("c. ➖ 删除忽略规则")
        print("d. 🔄 切换规则启用状态")
        print("e. 🧪 测试忽略模式")
        print("f. 📤 导出到.merge_ignore文件")
        print("g. 📊 查看统计信息")
        print("h. 返回上级菜单")

    def _show_ignore_rules_list(self):
        """显示忽略规则列表"""
        print("\n📋 当前忽略规则列表:")
        print("=" * 80)

        rules = self.orchestrator.ignore_manager.list_rules()
        if not rules:
            print("暂无忽略规则")
            return

        # 按来源分组显示
        sources = ["default", "ignore_file", "config", "user_added"]
        source_names = {
            "default": "🔧 默认规则",
            "ignore_file": "📄 项目文件",
            "config": "⚙️ 配置文件",
            "user_added": "👤 用户添加",
        }

        for source in sources:
            source_rules = [r for r in rules if r.get("source") == source]
            if source_rules:
                print(f"\n{source_names.get(source, source)}:")
                print("-" * 60)

                for i, rule in enumerate(source_rules, 1):
                    status = "✅" if rule.get("enabled", True) else "❌"
                    pattern = rule["pattern"]
                    rule_type = rule["type"]
                    description = rule.get("description", "")

                    print(f"{i:2d}. {status} [{rule_type:5s}] {pattern}")
                    if description:
                        print(f"     💬 {description}")

    def _add_ignore_rule(self):
        """添加忽略规则"""
        print("\n➕ 添加新的忽略规则")
        print("=" * 40)

        from config import IGNORE_RULE_TYPES

        # 显示支持的规则类型
        print("支持的规则类型:")
        for rule_type, desc in IGNORE_RULE_TYPES.items():
            print(f"  {rule_type}: {desc}")

        try:
            pattern = input("\n请输入匹配模式: ").strip()
            if not pattern:
                DisplayHelper.print_warning("模式不能为空")
                return

            rule_type = input("请输入规则类型 (默认: glob): ").strip() or "glob"
            if rule_type not in IGNORE_RULE_TYPES:
                DisplayHelper.print_warning(f"不支持的规则类型: {rule_type}")
                return

            description = input("请输入规则描述 (可选): ").strip()

            # 添加规则
            if self.orchestrator.ignore_manager.add_rule(
                pattern, rule_type, description
            ):
                DisplayHelper.print_success(f"成功添加忽略规则: {pattern}")
            else:
                DisplayHelper.print_error("添加忽略规则失败")

        except KeyboardInterrupt:
            print("\n操作已取消")

    def _remove_ignore_rule(self):
        """删除忽略规则"""
        print("\n➖ 删除忽略规则")
        print("=" * 40)

        # 显示可删除的规则（排除默认规则）
        rules = self.orchestrator.ignore_manager.list_rules()
        removable_rules = [r for r in rules if r.get("source") not in ["default"]]

        if not removable_rules:
            print("没有可删除的规则（默认规则不能删除）")
            return

        print("可删除的规则:")
        for i, rule in enumerate(removable_rules, 1):
            status = "✅" if rule.get("enabled", True) else "❌"
            print(f"{i:2d}. {status} [{rule['type']:5s}] {rule['pattern']}")

        try:
            choice = input(f"\n请选择要删除的规则 (1-{len(removable_rules)}): ").strip()
            choice_idx = int(choice) - 1

            if 0 <= choice_idx < len(removable_rules):
                rule = removable_rules[choice_idx]
                pattern = rule["pattern"]
                rule_type = rule["type"]

                confirm = input(f"确认删除规则 '{pattern}' ? (y/N): ").strip().lower()
                if confirm == "y":
                    if self.orchestrator.ignore_manager.remove_rule(pattern, rule_type):
                        DisplayHelper.print_success(f"成功删除规则: {pattern}")
                    else:
                        DisplayHelper.print_error("删除规则失败")
                else:
                    print("删除操作已取消")
            else:
                DisplayHelper.print_warning("无效选择")

        except (ValueError, KeyboardInterrupt):
            print("操作已取消")

    def _toggle_ignore_rule(self):
        """切换规则启用状态"""
        print("\n🔄 切换规则启用状态")
        print("=" * 40)

        rules = self.orchestrator.ignore_manager.list_rules()
        if not rules:
            print("暂无忽略规则")
            return

        print("当前规则:")
        for i, rule in enumerate(rules, 1):
            status = "✅ 启用" if rule.get("enabled", True) else "❌ 禁用"
            print(f"{i:2d}. {status} [{rule['type']:5s}] {rule['pattern']}")

        try:
            choice = input(f"\n请选择要切换的规则 (1-{len(rules)}): ").strip()
            choice_idx = int(choice) - 1

            if 0 <= choice_idx < len(rules):
                rule = rules[choice_idx]
                pattern = rule["pattern"]
                rule_type = rule["type"]
                current_status = "启用" if rule.get("enabled", True) else "禁用"
                new_status = "禁用" if rule.get("enabled", True) else "启用"

                if self.orchestrator.ignore_manager.toggle_rule(pattern, rule_type):
                    DisplayHelper.print_success(
                        f"成功将规则 '{pattern}' 从{current_status}切换为{new_status}"
                    )
                else:
                    DisplayHelper.print_error("切换规则状态失败")
            else:
                DisplayHelper.print_warning("无效选择")

        except (ValueError, KeyboardInterrupt):
            print("操作已取消")

    def _test_ignore_pattern(self):
        """测试忽略模式"""
        print("\n🧪 测试忽略模式")
        print("=" * 40)

        from config import IGNORE_RULE_TYPES

        try:
            pattern = input("请输入要测试的模式: ").strip()
            if not pattern:
                DisplayHelper.print_warning("模式不能为空")
                return

            rule_type = input("请输入规则类型 (默认: glob): ").strip() or "glob"
            if rule_type not in IGNORE_RULE_TYPES:
                DisplayHelper.print_warning(f"不支持的规则类型: {rule_type}")
                return

            # 获取测试文件列表
            test_files_input = input("请输入测试文件列表 (用空格分隔): ").strip()
            if not test_files_input:
                # 使用默认测试文件
                test_files = [
                    "src/main.py",
                    "src/__pycache__/module.pyc",
                    "docs/README.md",
                    ".git/config",
                    "build/output.log",
                    "test.tmp",
                    ".DS_Store",
                    "node_modules/package/index.js",
                    "*.py",
                    "config.json",
                ]
                print("使用默认测试文件列表")
            else:
                test_files = test_files_input.split()

            # 执行测试
            result = self.orchestrator.ignore_manager.test_pattern(
                pattern, rule_type, test_files
            )

            print(f"\n测试结果:")
            print(f"模式: {result['pattern']}")
            print(f"类型: {result['type']}")
            print(f"匹配数量: {result['match_count']}/{result['total_count']}")

            if result["matched_files"]:
                print(f"\n✅ 匹配的文件 ({len(result['matched_files'])}个):")
                for file in result["matched_files"]:
                    print(f"  - {file}")

            if result["unmatched_files"]:
                print(f"\n❌ 未匹配的文件 ({len(result['unmatched_files'])}个):")
                for file in result["unmatched_files"]:
                    print(f"  - {file}")

        except KeyboardInterrupt:
            print("\n测试已取消")

    def _export_ignore_file(self):
        """导出到.merge_ignore文件"""
        print("\n📤 导出忽略规则到文件")
        print("=" * 40)

        file_path = input("请输入导出文件路径 (默认: .merge_ignore): ").strip()
        if not file_path:
            file_path = None  # 使用默认路径

        try:
            if self.orchestrator.ignore_manager.export_ignore_file(file_path):
                actual_path = file_path or ".merge_ignore"
                DisplayHelper.print_success(f"成功导出忽略规则到: {actual_path}")
            else:
                DisplayHelper.print_error("导出失败")
        except Exception as e:
            DisplayHelper.print_error(f"导出过程中出现错误: {e}")

    def _show_ignore_stats(self):
        """显示忽略规则统计信息"""
        print("\n📊 忽略规则统计信息")
        print("=" * 40)

        stats = self.orchestrator.ignore_manager.get_rule_stats()
        rules = self.orchestrator.ignore_manager.list_rules()

        print(f"总规则数: {stats['total_rules']}")
        print(f"启用规则数: {stats['enabled_rules']}")
        print(f"禁用规则数: {stats['total_rules'] - stats['enabled_rules']}")
        print(f"已过滤文件数: {stats.get('ignored_files', 0)}")
        print(f"最后更新: {stats.get('last_updated', '未知')}")

        # 按来源统计
        print(f"\n按来源统计:")
        sources = {}
        for rule in rules:
            source = rule.get("source", "unknown")
            sources[source] = sources.get(source, 0) + 1

        for source, count in sources.items():
            source_name = {
                "default": "默认规则",
                "ignore_file": "项目文件",
                "config": "配置文件",
                "user_added": "用户添加",
            }.get(source, source)
            print(f"  {source_name}: {count}")

        # 按类型统计
        print(f"\n按类型统计:")
        types = {}
        for rule in rules:
            rule_type = rule.get("type", "unknown")
            types[rule_type] = types.get(rule_type, 0) + 1

        for rule_type, count in types.items():
            print(f"  {rule_type}: {count}")

    # === 查询系统 ===
    def _handle_query_system_menu(self):
        """处理查询系统菜单"""
        while True:
            self._show_query_system_menu()
            choice = input("\n请选择查询类型 (a-g): ").strip().lower()

            if choice == "a":
                self._query_by_assignee()
            elif choice == "b":
                self._query_by_file()
            elif choice == "c":
                self._query_by_status()
            elif choice == "d":
                self._advanced_search()
            elif choice == "e":
                self._reverse_query()
            elif choice == "f":
                self._show_query_suggestions()
            elif choice == "g":
                break
            else:
                DisplayHelper.print_warning("无效选择，请输入a-g")

    def _show_query_system_menu(self):
        """显示查询系统菜单"""
        print("\n🔍 高级查询系统")
        print("=" * 40)
        print("a. 👤 按负责人查询")
        print("b. 📁 按文件模式查询")
        print("c. 📊 按状态查询")
        print("d. 🔧 高级组合查询")
        print("e. 🔄 反向查询")
        print("f. 💡 查询建议")
        print("g. 返回上级菜单")

    def _query_by_assignee(self):
        """按负责人查询"""
        print("\n👤 按负责人查询")
        print("=" * 40)

        try:
            name = input("请输入负责人姓名或姓名模式: ").strip()
            if not name:
                DisplayHelper.print_warning("姓名不能为空")
                return

            fuzzy = input("是否启用模糊匹配? (Y/n): ").strip().lower()
            fuzzy_enabled = fuzzy != "n"

            exact = input("是否要求精确匹配? (y/N): ").strip().lower()
            exact_match = exact == "y"

            print(f"\n🔍 查询中...")
            result = self.orchestrator.query_system.query_by_assignee(
                name, fuzzy_enabled, exact_match
            )

            self._display_query_result(result)

        except KeyboardInterrupt:
            print("\n查询已取消")

    def _query_by_file(self):
        """按文件模式查询"""
        print("\n📁 按文件模式查询")
        print("=" * 40)

        try:
            pattern = input("请输入文件路径模式 (支持通配符): ").strip()
            if not pattern:
                DisplayHelper.print_warning("文件模式不能为空")
                return

            fuzzy = input("是否启用模糊匹配? (Y/n): ").strip().lower()
            fuzzy_enabled = fuzzy != "n"

            regex = input("是否使用正则表达式? (y/N): ").strip().lower()
            regex_enabled = regex == "y"

            print(f"\n🔍 查询中...")
            result = self.orchestrator.query_system.query_by_file(
                pattern, fuzzy_enabled, regex_enabled
            )

            self._display_query_result(result)

        except KeyboardInterrupt:
            print("\n查询已取消")

    def _query_by_status(self):
        """按状态查询"""
        print("\n📊 按状态查询")
        print("=" * 40)

        print("可用状态:")
        print("  pending - 待处理")
        print("  in_progress - 进行中")
        print("  completed - 已完成")
        print("  conflict - 有冲突")

        try:
            status = input("\n请输入状态名称: ").strip()
            if not status:
                DisplayHelper.print_warning("状态不能为空")
                return

            details = input("是否包含详细信息? (Y/n): ").strip().lower()
            include_details = details != "n"

            print(f"\n🔍 查询中...")
            result = self.orchestrator.query_system.query_by_status(
                status, include_details
            )

            self._display_query_result(result)

        except KeyboardInterrupt:
            print("\n查询已取消")

    def _advanced_search(self):
        """高级组合查询"""
        print("\n🔧 高级组合查询")
        print("=" * 40)
        print("请设置查询条件 (留空跳过该条件):")

        try:
            criteria = {}

            assignee = input("负责人模式: ").strip()
            if assignee:
                criteria["assignee"] = assignee

            file_pattern = input("文件路径模式: ").strip()
            if file_pattern:
                criteria["file_pattern"] = file_pattern

            status = input("状态: ").strip()
            if status:
                criteria["status"] = status

            min_files = input("最小文件数: ").strip()
            if min_files and min_files.isdigit():
                criteria["min_files"] = int(min_files)

            max_files = input("最大文件数: ").strip()
            if max_files and max_files.isdigit():
                criteria["max_files"] = int(max_files)

            assignment_reason = input("分配原因模式: ").strip()
            if assignment_reason:
                criteria["assignment_reason"] = assignment_reason

            if not criteria:
                DisplayHelper.print_warning("未设置任何查询条件")
                return

            print(f"\n🔍 查询中...")
            result = self.orchestrator.query_system.advanced_search(criteria)

            self._display_query_result(result)

        except KeyboardInterrupt:
            print("\n查询已取消")

    def _reverse_query(self):
        """反向查询"""
        print("\n🔄 反向查询")
        print("=" * 40)
        print("请选择要查找的问题类型:")
        print("  1. 未分配的文件")
        print("  2. 工作量过重的负责人")
        print("  3. 空组")
        print("  4. 有问题的组")
        print("  5. 全部问题")

        try:
            choice = input("\n请选择 (1-5): ").strip()

            criteria = {}
            max_files = 10  # 默认最大文件数

            if choice == "1":
                criteria["unassigned"] = True
            elif choice == "2":
                criteria["overloaded"] = True
                max_input = input("设置最大文件数阈值 (默认10): ").strip()
                if max_input and max_input.isdigit():
                    max_files = int(max_input)
                criteria["max_files"] = max_files
            elif choice == "3":
                criteria["empty_groups"] = True
            elif choice == "4":
                criteria["problematic"] = True
            elif choice == "5":
                criteria.update(
                    {
                        "unassigned": True,
                        "overloaded": True,
                        "empty_groups": True,
                        "problematic": True,
                        "max_files": max_files,
                    }
                )
            else:
                DisplayHelper.print_warning("无效选择")
                return

            print(f"\n🔍 分析中...")
            result = self.orchestrator.query_system.reverse_query(criteria)

            self._display_reverse_query_result(result)

        except KeyboardInterrupt:
            print("\n查询已取消")

    def _show_query_suggestions(self):
        """显示查询建议"""
        print("\n💡 查询建议")
        print("=" * 40)

        try:
            partial = input("请输入部分查询内容: ").strip()
            if not partial:
                DisplayHelper.print_warning("查询内容不能为空")
                return

            suggestions = self.orchestrator.query_system.get_query_suggestions(partial)

            if suggestions:
                print(f"\n基于 '{partial}' 的查询建议:")
                for i, suggestion in enumerate(suggestions, 1):
                    print(f"{i:2d}. {suggestion}")
            else:
                print("没有找到相关建议")

        except KeyboardInterrupt:
            print("\n操作已取消")

    def _display_query_result(self, result: dict):
        """显示查询结果"""
        if not result.get("success", True):
            DisplayHelper.print_error(f"查询失败: {result.get('error', '未知错误')}")
            return

        query_type = result.get("query_type", "unknown")
        results = result.get("results", [])
        summary = result.get("summary", {})

        if not results:
            print("\n📭 没有找到匹配的结果")
            return

        print(f"\n✅ 查询完成 - {query_type}")
        print("=" * 60)

        # 显示摘要信息
        if summary:
            print("📊 查询摘要:")
            if "total_groups" in summary:
                print(f"  匹配组数: {summary['total_groups']}")
            if "total_files" in summary:
                print(f"  涉及文件: {summary['total_files']}")
            if "matched_assignees" in summary:
                assignees = summary["matched_assignees"]
                if isinstance(assignees, list):
                    print(f"  相关负责人: {', '.join(assignees) if assignees else '无'}")
            if "status_breakdown" in summary:
                print("  状态分布:")
                for status, count in summary["status_breakdown"].items():
                    print(f"    {status}: {count}")
            print()

        # 显示详细结果
        print("📋 详细结果:")
        for i, item in enumerate(results, 1):
            print(f"\n{i:2d}. 组名: {item.get('group_name', 'N/A')}")
            print(f"    负责人: {item.get('assignee', 'N/A')}")
            print(f"    状态: {item.get('status', 'N/A')}")

            if "file_count" in item:
                print(f"    文件数: {item['file_count']}")

            if "matched_files" in item:
                matched_files = item["matched_files"]
                print(f"    匹配文件 ({len(matched_files)}):")
                for file in matched_files[:5]:  # 只显示前5个
                    print(f"      - {file}")
                if len(matched_files) > 5:
                    print(f"      ... 还有 {len(matched_files) - 5} 个文件")

            if "assignment_reason" in item:
                reason = item["assignment_reason"]
                if reason:
                    print(f"    分配原因: {reason}")

        # 如果结果太多，提示用户
        if len(results) > 10:
            print(f"\n... 显示了前 10 个结果，共 {len(results)} 个结果")

    def _display_reverse_query_result(self, result: dict):
        """显示反向查询结果"""
        if not result.get("success", True):
            DisplayHelper.print_error(f"反向查询失败: {result.get('error', '未知错误')}")
            return

        results = result.get("results", {})
        summary = result.get("summary", {})

        print(f"\n🔄 反向查询结果")
        print("=" * 60)

        # 显示摘要
        issues_found = summary.get("issues_found", 0)
        if issues_found == 0:
            print("🎉 没有发现问题，项目状态良好！")
            return

        print(f"⚠️ 发现 {issues_found} 个问题")

        # 显示建议
        recommendations = summary.get("recommendations", [])
        if recommendations:
            print("\n💡 建议:")
            for i, rec in enumerate(recommendations, 1):
                print(f"{i:2d}. {rec}")

        # 显示详细结果
        if results.get("unassigned_files"):
            files = results["unassigned_files"]
            print(f"\n📂 未分配文件 ({len(files)}个):")
            for file in files[:10]:  # 只显示前10个
                print(f"  - {file}")
            if len(files) > 10:
                print(f"  ... 还有 {len(files) - 10} 个文件")

        if results.get("overloaded_assignees"):
            overloaded = results["overloaded_assignees"]
            print(f"\n👥 工作量过重的负责人 ({len(overloaded)}个):")
            for person in overloaded:
                ratio = person["overload_ratio"]
                print(
                    f"  - {person['assignee']}: {person['file_count']}个文件 "
                    f"({person['group_count']}个组) [负载: {ratio:.1f}x]"
                )

        if results.get("empty_groups"):
            empty = results["empty_groups"]
            print(f"\n📭 空组 ({len(empty)}个):")
            for group in empty:
                print(f"  - {group['group_name']} (负责人: {group['assignee']})")

        if results.get("problematic_groups"):
            problematic = results["problematic_groups"]
            print(f"\n⚠️ 有问题的组 ({len(problematic)}个):")
            for group in problematic:
                issues = group["issues"]
                issue_desc = {
                    "missing_assignee": "缺少负责人",
                    "no_files": "没有文件",
                    "invalid_status": "状态无效",
                }
                issues_list = []
                for issue in issues:
                    if issue:
                        desc = issue_desc.get(issue, issue)
                        if desc:
                            issues_list.append(desc)
                issues_text = ", ".join(issues_list)
                print(f"  - {group['group_name']}: {issues_text}")

    def _handle_search_assignee_submenu(self):
        """处理搜索负责人子菜单"""
        assignee_name = input("请输入负责人姓名: ").strip()
        if assignee_name:
            if self.orchestrator.processing_mode == "file_level":
                self.orchestrator.search_files_by_assignee(assignee_name)
            else:
                self.orchestrator.search_assignee_tasks(assignee_name)
        else:
            DisplayHelper.print_warning("负责人姓名不能为空")

    def _handle_search_directory_submenu(self):
        """处理搜索目录子菜单"""
        if self.orchestrator.processing_mode != "file_level":
            DisplayHelper.print_warning("目录搜索功能仅在文件级模式下可用")
            return

        directory_path = input("请输入目录路径: ").strip()
        if directory_path:
            self.orchestrator.search_files_by_directory(directory_path)
        else:
            DisplayHelper.print_warning("目录路径不能为空")

    def _handle_load_balancing_submenu(self):
        """处理负载均衡子菜单"""
        if self.orchestrator.processing_mode != "file_level":
            DisplayHelper.print_warning("负载均衡功能仅在文件级模式下可用")
            return

        print("⚖️ 文件级负载均衡")
        print("重新分配过载用户的文件到负载较轻的用户")

        max_tasks_input = input("每人最大文件数 (默认50): ").strip()
        max_tasks = int(max_tasks_input) if max_tasks_input.isdigit() else 50

        confirm = input(f"确定要执行负载均衡吗? (y/N): ").strip().lower()
        if confirm == "y":
            reassigned_count = self.orchestrator.balance_workload(max_tasks)
            if reassigned_count > 0:
                DisplayHelper.print_success(f"负载均衡完成，重新分配了 {reassigned_count} 个文件")
            else:
                DisplayHelper.print_info("当前负载分布合理，无需调整")
        else:
            DisplayHelper.print_info("已取消负载均衡操作")

    def _handle_file_detail_submenu(self):
        """处理文件详情查看子菜单"""
        if self.orchestrator.processing_mode != "file_level":
            DisplayHelper.print_warning("文件详情功能仅在文件级模式下可用")
            return

        file_path = input("请输入文件路径: ").strip()
        if file_path:
            file_info = self.orchestrator.file_manager.find_file_by_path(file_path)
            if file_info:
                DisplayHelper.display_file_detail(file_info)
            else:
                DisplayHelper.print_error(f"未找到文件: {file_path}")
        else:
            DisplayHelper.print_warning("文件路径不能为空")
