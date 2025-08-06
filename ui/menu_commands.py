"""
Git Merge Orchestrator - 菜单命令执行器
包含所有菜单功能的具体实现，从菜单管理器中分离出来
"""

from ui.display_helper import DisplayHelper


class MenuCommands:
    """菜单命令执行器 - 处理具体的功能执行"""

    def __init__(self, orchestrator):
        self.orchestrator = orchestrator

    def execute_quick_workflow(self):
        """执行快速全流程"""
        print("🚀 启动全流程引导模式")
        print(f"📋 处理模式: {self.orchestrator.processing_mode}")
        print(f"🌿 源分支: {self.orchestrator.source_branch}")
        print(f"🎯 目标分支: {self.orchestrator.target_branch}")

        steps = ["分析分支分叉", "创建智能合并计划", "智能自动分配任务", "准备执行合并"]

        try:
            # 步骤 1: 分析分支分叉
            print(f"\n📋 步骤 1/4: {steps[0]}")
            result = self.orchestrator.analyze_divergence()
            if not result:
                DisplayHelper.print_error("分支分叉分析失败")
                return False
            print("   ✅ 分支分叉分析完成")

            # 步骤 2: 创建合并计划
            print(f"\n📋 步骤 2/4: {steps[1]}")
            plan = self.orchestrator.create_merge_plan()
            if not plan:
                DisplayHelper.print_error("合并计划创建失败")
                return False

            if self.orchestrator.processing_mode == "file_level":
                file_count = len(plan.get("files", []))
                print(f"   ✅ 文件级合并计划创建完成，包含 {file_count} 个文件")
            else:
                group_count = len(plan.get("groups", []))
                print(f"   ✅ 组级合并计划创建完成，包含 {group_count} 个分组")

            # 步骤 3: 自动分配任务
            print(f"\n📋 步骤 3/4: {steps[2]}")
            assignment_result = self.orchestrator.auto_assign_tasks()
            if not assignment_result:
                DisplayHelper.print_error("任务分配失败")
                return False
            print("   ✅ 任务分配完成")

            # 步骤 4: 完成指导
            print(f"\n📋 步骤 4/4: {steps[3]}")
            print("🎉 全流程设置完成！系统已准备就绪")
            print("\n🎯 下一步建议:")
            print("• 查看项目状态了解分配情况")
            print("• 开始按组合并或批量合并")
            print("• 最后执行最终合并完成项目")

            return True

        except Exception as e:
            DisplayHelper.print_error(f"全流程执行出错: {str(e)}")
            return False

    def execute_analyze_divergence(self):
        """执行分支分叉分析"""
        print("🔍 正在分析分支分叉...")
        result = self.orchestrator.analyze_divergence()
        if result:
            print("✅ 分支分叉分析完成")
            print(f"📊 发现 {result.get('total_files', 0)} 个文件变更")
            print(f"🎯 集成分支: {result.get('integration_branch', 'N/A')}")
            return True
        else:
            DisplayHelper.print_error("分支分叉分析失败")
            return False

    def execute_create_plan(self):
        """执行创建合并计划"""
        print("📋 正在创建智能合并计划...")
        plan = self.orchestrator.create_merge_plan()
        if plan:
            if self.orchestrator.processing_mode == "file_level":
                file_count = len(plan.get("files", []))
                print(f"✅ 文件级合并计划创建完成")
                print(f"📁 包含 {file_count} 个文件")
                print(f"🔧 处理模式: 文件级精确处理")
            else:
                group_count = len(plan.get("groups", []))
                total_files = sum(
                    len(group.get("files", [])) for group in plan.get("groups", [])
                )
                print(f"✅ 组级合并计划创建完成")
                print(f"📁 包含 {group_count} 个分组，总计 {total_files} 个文件")
                print(f"🔧 处理模式: 传统组级处理")
            return True
        else:
            DisplayHelper.print_error("合并计划创建失败")
            return False

    def execute_auto_assign(self, exclude_authors=None):
        """执行自动分配任务"""
        print("⚡ 启动智能自动分配...")

        if exclude_authors:
            print(f"🚫 排除人员: {', '.join(exclude_authors)}")

        result = self.orchestrator.auto_assign_tasks(exclude_authors=exclude_authors)
        if result:
            print("✅ 智能自动分配完成")

            if self.orchestrator.processing_mode == "file_level":
                if hasattr(result, "get"):
                    assigned_count = result.get("assigned_count", 0)
                    print(f"📊 已分配 {assigned_count} 个文件")
            else:
                # 传统模式的分配结果显示
                active_contributors = result.get("active_contributors", [])
                assignment_count = result.get("assignment_count", {})
                print(f"👥 活跃贡献者: {len(active_contributors)} 位")
                print(f"📋 分配详情: {sum(assignment_count.values())} 个任务已分配")

            return True
        else:
            DisplayHelper.print_error("任务分配失败")
            return False

    def execute_check_status(self):
        """执行状态检查"""
        print("📊 正在检查项目状态...")
        self.orchestrator.check_status()
        return True

    def execute_merge_group(self, group_name):
        """执行组合并"""
        if not group_name:
            DisplayHelper.print_error("组名不能为空")
            return False

        print(f"📁 正在为组 '{group_name}' 生成合并脚本...")
        success = self.orchestrator.merge_group(group_name)
        if success:
            print("✅ 组合并脚本已生成")
            print("💡 请查看生成的脚本文件并执行")
            return True
        else:
            DisplayHelper.print_error(f"组 '{group_name}' 合并失败")
            return False

    def execute_batch_merge(self, assignee_name):
        """执行批量合并"""
        if not assignee_name:
            DisplayHelper.print_error("负责人姓名不能为空")
            return False

        print(f"👤 正在为负责人 '{assignee_name}' 生成批量合并脚本...")
        success = self.orchestrator.merge_assignee_tasks(assignee_name)
        if success:
            print("✅ 批量合并脚本已生成")
            print("💡 请查看生成的脚本文件并执行")
            return True
        else:
            DisplayHelper.print_error(f"负责人 '{assignee_name}' 的任务批量合并失败")
            return False

    def execute_merge_file(self, file_path):
        """执行单个文件合并"""
        if not file_path:
            DisplayHelper.print_error("文件路径不能为空")
            return False

        print(f"📄 正在为文件 '{file_path}' 生成合并脚本...")
        success = self.orchestrator.merge_file(file_path)
        if success:
            print("✅ 文件合并脚本已生成")
            print("💡 请查看生成的脚本文件并执行")
            return True
        else:
            DisplayHelper.print_error(f"文件 '{file_path}' 合并失败")
            return False

    def execute_finalize_merge(self):
        """执行最终合并"""
        print("🎉 正在执行最终合并...")
        success = self.orchestrator.finalize_merge()
        if success:
            print("✅ 最终合并完成！")
            print("🎊 项目合并任务全部完成")
            return True
        else:
            DisplayHelper.print_error("最终合并失败")
            return False

    def execute_search_assignee_tasks(self, assignee_name):
        """搜索负责人任务"""
        if not assignee_name:
            DisplayHelper.print_error("负责人姓名不能为空")
            return False

        print(f"🔍 正在搜索负责人 '{assignee_name}' 的任务...")
        result = self.orchestrator.search_assignee_tasks(assignee_name)
        if result:
            print(f"✅ 找到 {len(result)} 个任务")
            return True
        else:
            print(f"ℹ️ 负责人 '{assignee_name}' 暂无分配的任务")
            return False

    def execute_search_files_by_directory(self, directory_path):
        """按目录搜索文件"""
        if not directory_path:
            DisplayHelper.print_error("目录路径不能为空")
            return False

        if self.orchestrator.processing_mode != "file_level":
            DisplayHelper.print_error("目录搜索功能仅在文件级模式下可用")
            return False

        print(f"📁 正在搜索目录 '{directory_path}' 下的文件...")
        result = self.orchestrator.search_files_by_directory(directory_path)
        if result:
            print(f"✅ 找到 {len(result)} 个文件")
            return True
        else:
            print(f"ℹ️ 目录 '{directory_path}' 下暂无文件")
            return False

    def execute_manual_assign_file(self, file_path, assignee):
        """手动分配文件"""
        if not file_path or not assignee:
            DisplayHelper.print_error("文件路径和负责人都不能为空")
            return False

        if self.orchestrator.processing_mode != "file_level":
            DisplayHelper.print_error("文件级手动分配功能仅在文件级模式下可用")
            return False

        print(f"👤 正在将文件 '{file_path}' 分配给 '{assignee}'...")
        success = self.orchestrator.manual_assign_file(file_path, assignee)
        if success:
            print("✅ 文件分配成功")
            return True
        else:
            DisplayHelper.print_error("文件分配失败")
            return False

    def show_system_info(self):
        """显示系统信息"""
        print("⚙️ 系统信息:")
        print(f"   处理模式: {self.orchestrator.processing_mode}")
        print(f"   源分支: {self.orchestrator.source_branch}")
        print(f"   目标分支: {self.orchestrator.target_branch}")
        print(f"   工作目录: {self.orchestrator.repo_path}")

        # 合并策略信息
        strategy_info = self.orchestrator.get_merge_strategy_info()
        print(f"   合并策略: {strategy_info['mode_name']}")

        # 处理模式信息
        mode_info = self.orchestrator.get_processing_mode_info()
        print(f"   模式描述: {mode_info['description']}")

    def show_performance_stats(self):
        """显示性能统计"""
        try:
            stats = self.orchestrator.contributor_analyzer.get_performance_stats()
            print("📈 性能统计:")
            print(f"   缓存文件数: {stats['cached_files']}")
            print(f"   缓存目录数: {stats['cached_directories']}")
            print(f"   批量计算: {'✅' if stats['batch_computed'] else '❌'}")
            print(f"   缓存文件存在: {'✅' if stats['cache_file_exists'] else '❌'}")
            return True
        except Exception as e:
            DisplayHelper.print_error(f"获取性能统计失败: {e}")
            return False

    def clean_cache(self):
        """清理缓存"""
        try:
            cache_file = self.orchestrator.contributor_analyzer.cache_file
            if cache_file.exists():
                cache_file.unlink()
                print("✅ 缓存已清理")
                return True
            else:
                print("ℹ️ 缓存文件不存在")
                return True
        except Exception as e:
            DisplayHelper.print_error(f"清理缓存失败: {e}")
            return False

    def switch_merge_strategy(self):
        """切换合并策略"""
        return self.orchestrator.switch_merge_strategy()

    def switch_processing_mode(self):
        """切换处理模式"""
        return self.orchestrator.switch_processing_mode()

    def show_help(self):
        """显示帮助信息"""
        print("\n💡 Git Merge Orchestrator 使用帮助")
        print("=" * 60)
        print("🚀 核心流程:")
        print("  1. 快速全流程 - 新手推荐，一键完成分析→计划→分配")
        print("  2-4. 手动执行各步骤 - 高级用户精确控制")
        print("  5. 查看状态 - 随时了解项目进度")
        print("  8-10. 执行合并 - 完成实际的代码合并")
        print()
        print("🎯 最佳实践:")
        print("  • 首次使用选择 1 (快速全流程)")
        print("  • 定期使用 5 查看项目状态")
        print("  • 小组合并用 8，大批量用 9")
        print("  • 最后使用 10 完成最终合并")
        print()
        print("⌨️  快捷键:")
        print("  q - 退出程序")
        print("  h - 显示帮助")
        print("  s - 快速查看状态")
        print("  直接输入数字 - 执行对应功能")
        print()
        print("🔧 系统配置:")
        print("  • 默认使用文件级处理模式 (更精确)")
        print("  • 默认使用Legacy合并策略 (更快速)")
        print("  • 可在设置中切换模式和策略")
        print()
        print("📝 使用技巧:")
        print("  • 扁平化菜单设计，1级操作更高效")
        print("  • 配置会自动保存，后续运行无需参数")
        print("  • 支持中断恢复，随时可以继续之前的工作")
        return True
