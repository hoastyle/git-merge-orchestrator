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
            summary = self.orchestrator.get_plan_summary()
            if summary and summary.get("stats"):
                stats = summary["stats"]
                strategy = summary["merge_strategy"]

                print(f"📊 项目状态: {stats['completed_groups']}/{stats['total_groups']} 组已完成")
                print(f"🔧 当前策略: {strategy['mode_name']}")

                if stats["total_groups"] > 0:
                    progress = stats["completed_groups"] / stats["total_groups"] * 100
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
                print(f"👥 已分配组: {stats['assigned_groups']} ({stats['assigned_files']} 文件)")
                print(f"✅ 已完成组: {stats['completed_groups']} ({stats['completed_files']} 文件)")
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
            choice = input("\n请选择操作 (a-e): ").strip().lower()

            if choice == "a":
                self._handle_auto_assign_submenu()
            elif choice == "b":
                self._handle_manual_assign_submenu()
            elif choice == "c":
                self.orchestrator.show_contributor_analysis()
            elif choice == "d":
                assignee_name = input("请输入负责人姓名: ").strip()
                if assignee_name:
                    self.orchestrator.search_assignee_tasks(assignee_name)
                else:
                    DisplayHelper.print_warning("负责人姓名不能为空")
            elif choice == "e":
                break
            else:
                DisplayHelper.print_warning("无效选择，请输入a-e")

    def _show_task_assignment_menu(self):
        """显示任务分配菜单"""
        print("\n👥 任务分配")
        print("=" * 40)
        print("a. 🚀 涡轮增压自动分配")
        print("b. ✋ 手动分配任务")
        print("c. 📊 查看贡献者分析")
        print("d. 🔍 搜索负责人任务")
        print("e. 返回主菜单")

    def _handle_auto_assign_submenu(self):
        """处理自动分配子菜单"""
        print("🤖 涡轮增压智能自动分配模式 (活跃度过滤+修改行数综合评分+备选方案)")
        print("💡 新评分算法: 近期提交×2 + 近期行数×0.1 + 历史提交×1 + 历史行数×0.05")

        exclude_input = input("请输入要排除的作者列表 (用逗号分隔，回车跳过): ").strip()
        exclude_authors = [name.strip() for name in exclude_input.split(",")] if exclude_input else []

        max_tasks_input = input("每人最大任务数 (默认3): ").strip()
        max_tasks = int(max_tasks_input) if max_tasks_input.isdigit() else 3

        fallback_input = input("启用备选分配方案? (Y/n): ").strip().lower()
        include_fallback = fallback_input != "n"

        self.orchestrator.auto_assign_tasks(exclude_authors, max_tasks, include_fallback)

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
                self._handle_config_management_submenu()
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
        print("d. 📋 查看分组详细信息")
        print("e. 返回主菜单")

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
            choice = input("\n请选择操作 (a-e): ").strip().lower()

            if choice == "a":
                self.orchestrator.show_contributor_analysis()
            elif choice == "b":
                self._show_performance_report()
            elif choice == "c":
                self._handle_custom_script_generation()
            elif choice == "d":
                self._enter_debug_mode()
            elif choice == "e":
                break
            else:
                DisplayHelper.print_warning("无效选择，请输入a-e")

    def _show_advanced_features_menu(self):
        """显示高级功能菜单"""
        print("\n🎯 高级功能")
        print("=" * 40)
        print("a. 👥 详细贡献者分析")
        print("b. 📊 性能统计报告")
        print("c. 🛠️ 自定义脚本生成")
        print("d. 🐛 调试模式")
        print("e. 返回主菜单")

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
                    completion_rate = stats["completed_groups"] / stats["total_groups"] * 100
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
        current_branch = self.orchestrator.git_ops.run_command("git branch --show-current")
        print(f"   当前分支: {current_branch if current_branch else '获取失败'}")

        # 文件系统
        print(f"\n💾 文件系统:")
        print(f"   工作目录: {self.orchestrator.file_helper.work_dir}")
        print(f"   工作目录存在: {'✅' if self.orchestrator.file_helper.work_dir.exists() else '❌'}")
        print(f"   计划文件存在: {'✅' if self.orchestrator.file_helper.plan_file_path.exists() else '❌'}")

        # 模块状态
        print(f"\n🧩 模块状态:")
        print(f"   贡献者分析器: {'✅' if self.orchestrator.contributor_analyzer else '❌'}")
        print(f"   任务分配器: {'✅' if self.orchestrator.task_assigner else '❌'}")
        print(f"   合并执行器工厂: {'✅' if self.orchestrator.merge_executor_factory else '❌'}")

        input("\n按回车键退出调试模式...")
