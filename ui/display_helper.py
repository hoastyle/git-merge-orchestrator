"""
Git Merge Orchestrator - 显示格式化工具
负责用户界面显示、表格格式化和信息展示
"""

from collections import defaultdict
from config import TABLE_CONFIGS, ACTIVITY_LEVELS, ASSIGNMENT_REASON_TYPES


class DisplayHelper:
    """显示格式化助手类"""

    @staticmethod
    def get_display_width(text):
        """计算显示宽度，考虑中文字符"""
        width = 0
        for char in str(text):
            if ord(char) > 127:  # 中文字符
                width += 2
            else:  # 英文字符
                width += 1
        return width

    @staticmethod
    def format_table_cell(text, width, align="left"):
        """格式化表格单元格，确保对齐"""
        text_str = str(text)
        display_width = DisplayHelper.get_display_width(text_str)

        # 如果文本太长，智能截断
        if display_width > width:
            # 计算可以显示的字符数
            truncated_text = ""
            current_width = 0

            for char in text_str:
                char_width = 2 if ord(char) > 127 else 1
                if current_width + char_width + 3 > width:  # 保留3个字符给"..."
                    break
                truncated_text += char
                current_width += char_width

            # 添加省略号
            if width > 3:
                text_str = truncated_text + "..."
                display_width = DisplayHelper.get_display_width(text_str)
            else:
                text_str = text_str[:width]
                display_width = width

        padding = width - display_width

        if padding <= 0:
            return text_str

        if align == "left":
            return text_str + " " * padding
        elif align == "right":
            return " " * padding + text_str
        elif align == "center":
            left_pad = padding // 2
            right_pad = padding - left_pad
            return " " * left_pad + text_str + " " * right_pad

        return text_str

    @staticmethod
    def print_table_separator(widths):
        """打印表格分隔线"""
        total_width = sum(widths) + len(widths) - 1
        print("-" * total_width)

    @staticmethod
    def print_table_header(headers, widths, aligns=None):
        """打印表格标题行"""
        if aligns is None:
            aligns = ["left"] * len(headers)

        row = []
        for header, width, align in zip(headers, widths, aligns):
            row.append(DisplayHelper.format_table_cell(header, width, align))

        print(" ".join(row))
        DisplayHelper.print_table_separator(widths)

    @staticmethod
    def print_table_row(values, widths, aligns=None):
        """打印表格数据行"""
        if aligns is None:
            aligns = ["left"] * len(values)

        row = []
        for value, width, align in zip(values, widths, aligns):
            row.append(DisplayHelper.format_table_cell(value, width, align))

        print(" ".join(row))

    @staticmethod
    def auto_adjust_table_width(table_name, data_rows):
        """根据数据内容自动调整表格列宽"""
        if table_name not in TABLE_CONFIGS:
            return TABLE_CONFIGS.get(table_name, {})

        config = TABLE_CONFIGS[table_name].copy()
        headers = config["headers"]
        widths = config["widths"].copy()
        aligns = config["aligns"]

        # 计算每列的最大显示宽度
        max_widths = []
        for i, header in enumerate(headers):
            # 从标题开始
            max_width = DisplayHelper.get_display_width(header)

            # 检查数据行中的最大宽度
            for row in data_rows:
                if i < len(row):
                    cell_width = DisplayHelper.get_display_width(str(row[i]))
                    max_width = max(max_width, cell_width)

            max_widths.append(max_width)

        # 针对特定列进行智能调整（主要是组名列）
        if table_name == "status_overview" and len(max_widths) > 0:
            # 组名列（第0列）最少45个字符，最多65个字符
            max_widths[0] = max(45, min(65, max_widths[0] + 2))
        elif table_name == "group_list" and len(max_widths) > 1:
            # 组名列（第1列）
            max_widths[1] = max(45, min(65, max_widths[1] + 2))
        elif (
            table_name in ["assignment_reasons", "assignee_tasks"]
            and len(max_widths) > 0
        ):
            # 组名列（第0列）
            max_widths[0] = max(45, min(65, max_widths[0] + 2))

        # 使用调整后的宽度，但保持原来的最小宽度
        for i in range(len(widths)):
            if i < len(max_widths):
                widths[i] = max(widths[i], max_widths[i])

        return {"headers": headers, "widths": widths, "aligns": aligns}

    @staticmethod
    def print_table(table_name, data_rows, extra_info=None, auto_adjust=True):
        """打印预配置的表格"""
        if table_name not in TABLE_CONFIGS:
            print(f"❌ 未知的表格类型: {table_name}")
            return

        # 根据数据自动调整宽度
        if auto_adjust:
            config = DisplayHelper.auto_adjust_table_width(table_name, data_rows)
        else:
            config = TABLE_CONFIGS[table_name]

        headers = config["headers"]
        widths = config["widths"]
        aligns = config["aligns"]

        DisplayHelper.print_table_header(headers, widths, aligns)

        for row_data in data_rows:
            DisplayHelper.print_table_row(row_data, widths, aligns)

        DisplayHelper.print_table_separator(widths)

        if extra_info:
            print(extra_info)

    @staticmethod
    def get_activity_info(recent_commits, is_active):
        """获取活跃度信息"""
        if not is_active:
            return ACTIVITY_LEVELS["inactive"]

        for level_name, level_info in ACTIVITY_LEVELS.items():
            if level_name == "inactive":
                continue
            if recent_commits >= level_info["threshold"]:
                return level_info

        return ACTIVITY_LEVELS["recent"]

    @staticmethod
    def categorize_assignment_reason(reason):
        """将分配原因分类"""
        if not reason or reason == "未指定":
            return "未指定"

        for category, keyword in ASSIGNMENT_REASON_TYPES.items():
            if keyword in reason:
                return category

        return "其他"

    @staticmethod
    def format_assignment_summary(assignment_count, unassigned_groups):
        """格式化分配总结"""
        summary = "\n📊 自动分配总结:\n"
        summary += f"👥 任务分配:\n"

        for person, count in sorted(
            assignment_count.items(), key=lambda x: x[1], reverse=True
        ):
            summary += f" {person}: {count} 个任务\n"

        if unassigned_groups:
            summary += f"\n⚠️ 未分配的组 ({len(unassigned_groups)}个): "
            summary += ", ".join(unassigned_groups[:3])
            if len(unassigned_groups) > 3:
                summary += "..."

        return summary

    @staticmethod
    def format_workload_distribution(assignee_workload):
        """格式化负载分布"""
        if not assignee_workload:
            return ""

        distribution = "\n👥 负载分布:\n"
        sorted_workload = sorted(
            assignee_workload.items(), key=lambda x: x[1]["files"], reverse=True
        )

        for person, workload in sorted_workload:
            fallback_info = (
                f"(含{workload['fallback']}个备选)" if workload["fallback"] > 0 else ""
            )
            distribution += (
                f" {person}: {workload['completed']}/{workload['groups']} 组完成, "
            )
            distribution += f"{workload['files']} 个文件 {fallback_info}\n"

        return distribution.rstrip()

    @staticmethod
    def format_completion_stats(stats):
        """格式化完成统计"""
        if not stats:
            return "📈 进度统计: 数据不可用"

        assigned_groups = stats.get("assigned_groups", 0)
        total_groups = stats.get("total_groups", 0)
        assigned_files = stats.get("assigned_files", 0)
        total_files = stats.get("total_files", 0)
        completed_groups = stats.get("completed_groups", 0)

        completion_info = f"📈 进度统计: {assigned_groups}/{total_groups} 组已分配 "
        completion_info += f"({assigned_files}/{total_files} 文件), "
        completion_info += f"{completed_groups}/{total_groups} 组已完成"
        return completion_info

    @staticmethod
    def display_group_detail(group, file_helper):
        """显示单个组的详细信息"""
        print("\n" + "=" * 100)
        print(f"📁 组详细信息: {group['name']}")
        print("=" * 100)

        # 基本信息
        print(f"📊 基本信息:")
        print(f"   组名: {group['name']}")
        group_type_desc = file_helper.get_group_type_description(
            group.get("group_type", "unknown")
        )
        print(f"   类型: {group.get('group_type', 'unknown')} ({group_type_desc})")
        print(f"   文件数: {group.get('file_count', len(group['files']))} 个")
        print(f"   负责人: {group.get('assignee', '未分配')}")

        status = group.get("status", "pending")
        status_text = {"completed": "✅ 已完成", "pending": "⏳ 待分配"}.get(
            status, "🔄 进行中" if group.get("assignee") else "⏳ 待分配"
        )
        print(f"   状态: {status_text}")

        # 分配原因
        assignment_reason = group.get("assignment_reason", "未指定")
        if assignment_reason:
            print(f"   分配原因: {assignment_reason}")

        # 备选分配信息
        fallback_reason = group.get("fallback_reason", "")
        if fallback_reason:
            print(f"   备选原因: {fallback_reason}")

        # 文件列表
        print(f"\n📄 包含文件列表:")
        files = group.get("files", [])
        for i, file_path in enumerate(files, 1):
            print(f"   {i:2d}. {file_path}")

        # 贡献者分析
        contributors = group.get("contributors", {})
        if contributors:
            print(f"\n👥 贡献者分析 (基于一年内活跃度):")

            contrib_data = []
            sorted_contributors = sorted(
                contributors.items(),
                key=lambda x: x[1]["score"] if isinstance(x[1], dict) else x[1],
                reverse=True,
            )

            for i, (author, stats) in enumerate(sorted_contributors[:10], 1):
                if isinstance(stats, dict):
                    recent = stats.get("recent_commits", 0)
                    total = stats.get("total_commits", 0)
                    score = stats.get("score", 0)
                    file_count = stats.get("file_count", 0)
                    row_data = [
                        str(i),
                        author,
                        str(recent),
                        str(total),
                        str(score),
                        str(file_count),
                    ]
                else:
                    row_data = [str(i), author, "N/A", str(stats), str(stats), "N/A"]

                contrib_data.append(row_data)

            DisplayHelper.print_table(
                "contributor_ranking", contrib_data[: len(contrib_data)]
            )

            if len(sorted_contributors) > 10:
                print(f"   ... 还有 {len(sorted_contributors) - 10} 位贡献者")

        # 备注信息
        notes = group.get("notes", "")
        if notes:
            print(f"\n📝 备注: {notes}")

        print("=" * 100)

    @staticmethod
    def show_menu():
        """显示主菜单"""
        print("\n📋 可用操作:")
        print("1. 分析分支分叉")
        print("2. 创建智能合并计划")
        print("3. 智能自动分配任务 (含活跃度过滤+备选方案)")
        print("4. 手动分配任务")
        print("5. 查看贡献者智能分析")
        print("6. 合并指定组")
        print("7. 搜索负责人任务")
        print("8. 合并指定负责人的所有任务")
        print("9. 检查状态 (可选择显示模式)")
        print("10. 查看分组详细信息")
        print("11. 查看分配原因分析")
        print("12. 完成状态管理 (标记完成/检查远程状态)")
        print("13. 完成最终合并")
        print("0. 退出")

    @staticmethod
    def print_section_header(title):
        """打印区块标题"""
        print(f"\n{'='*80}")
        print(f"{title}")
        print(f"{'='*80}")

    @staticmethod
    def print_success(message):
        """打印成功信息"""
        print(f"✅ {message}")

    @staticmethod
    def print_warning(message):
        """打印警告信息"""
        print(f"⚠️ {message}")

    @staticmethod
    def print_error(message):
        """打印错误信息"""
        print(f"❌ {message}")

    @staticmethod
    def print_info(message):
        """打印信息"""
        print(f"ℹ️ {message}")

    @staticmethod
    def format_file_completion_stats(stats):
        """格式化文件级完成统计"""
        if not stats:
            return "📈 文件进度统计: 数据不可用"

        total_files = stats.get("total_files", 0)
        assigned_files = stats.get("assigned_files", 0)
        completed_files = stats.get("completed_files", 0)
        pending_files = stats.get("pending_files", 0)
        in_progress_files = stats.get("in_progress_files", 0)

        completion_rate = stats.get("completion_rate", 0)
        assignment_rate = stats.get("assignment_rate", 0)

        completion_info = f"📈 文件进度统计: {total_files} 个文件 | "
        completion_info += f"已分配: {assigned_files} ({assignment_rate:.1f}%) | "
        completion_info += f"已完成: {completed_files} ({completion_rate:.1f}%) | "
        completion_info += f"待处理: {pending_files} | 进行中: {in_progress_files}"

        return completion_info

    @staticmethod
    def format_file_workload_distribution(workload):
        """格式化文件级负载分布"""
        if not workload:
            return ""

        distribution = "\n👥 文件级负载分布:\n"
        sorted_workload = sorted(
            workload.items(), key=lambda x: x[1]["assigned"], reverse=True
        )

        for person, load_info in sorted_workload:
            assigned = load_info["assigned"]
            completed = load_info["completed"]
            pending = load_info["pending"]
            completion_rate = (completed / assigned * 100) if assigned > 0 else 0

            distribution += f" {person}: {assigned} 个文件 | "
            distribution += (
                f"完成: {completed} | 待处理: {pending} | 完成率: {completion_rate:.1f}%\n"
            )

        return distribution.rstrip()

    @staticmethod
    def display_file_detail(file_info):
        """显示单个文件的详细信息"""
        print("\n" + "=" * 100)
        print(f"📄 文件详细信息: {file_info['path']}")
        print("=" * 100)

        # 基本信息
        print(f"📊 基本信息:")
        print(f"   文件路径: {file_info['path']}")
        print(f"   目录: {file_info['directory']}")
        print(f"   文件名: {file_info['filename']}")
        print(f"   扩展名: {file_info['extension'] or '无'}")
        print(f"   负责人: {file_info.get('assignee', '未分配')}")

        # 状态信息
        status = file_info.get("status", "pending")
        status_icons = {
            "pending": "⏳ 待处理",
            "assigned": "📋 已分配",
            "in_progress": "🔄 进行中",
            "completed": "✅ 已完成",
        }
        status_text = status_icons.get(status, f"❓ {status}")
        print(f"   状态: {status_text}")

        # 优先级
        priority = file_info.get("priority", "normal")
        priority_icons = {"high": "🔥 高", "normal": "📊 普通", "low": "📉 低"}
        priority_text = priority_icons.get(priority, f"❓ {priority}")
        print(f"   优先级: {priority_text}")

        # 时间信息
        if file_info.get("assigned_at"):
            print(f"   分配时间: {file_info['assigned_at']}")
        if file_info.get("completed_at"):
            print(f"   完成时间: {file_info['completed_at']}")

        # 分配原因
        assignment_reason = file_info.get("assignment_reason", "")
        if assignment_reason:
            print(f"   分配原因: {assignment_reason}")

        # 备注
        notes = file_info.get("notes", "")
        if notes:
            print(f"   备注: {notes}")

        # 贡献者分析
        contributors = file_info.get("contributors", {})
        if contributors:
            print(f"\n👥 文件贡献者分析:")

            sorted_contributors = sorted(
                contributors.items(),
                key=lambda x: x[1]["score"] if isinstance(x[1], dict) else x[1],
                reverse=True,
            )

            for i, (author, stats) in enumerate(sorted_contributors[:5], 1):
                if isinstance(stats, dict):
                    recent = stats.get("recent_commits", 0)
                    total = stats.get("total_commits", 0)
                    score = stats.get("score", 0)
                    print(f"   {i}. {author}: 得分 {score} (近期: {recent}, 历史: {total})")
                else:
                    print(f"   {i}. {author}: 历史提交 {stats}")

        print("=" * 100)

    @staticmethod
    def print_file_status_table(files, max_files=50):
        """打印文件状态表格"""
        if not files:
            print("📋 没有找到文件")
            return

        # 限制显示数量
        display_files = files[:max_files]

        table_data = []
        for i, file_info in enumerate(display_files, 1):
            # 状态图标
            status_icons = {
                "pending": "⏳",
                "assigned": "📋",
                "in_progress": "🔄",
                "completed": "✅",
            }
            status_icon = status_icons.get(file_info["status"], "❓")

            # 优先级图标
            priority_icons = {"high": "🔥", "normal": "📊", "low": "📉"}
            priority_icon = priority_icons.get(file_info.get("priority", "normal"), "📊")

            # 截断文件路径和分配原因以适应表格宽度
            file_path = file_info["path"]
            if len(file_path) > 45:
                file_path = file_path[:42] + "..."

            assignment_reason = file_info.get("assignment_reason", "")
            if len(assignment_reason) > 30:
                assignment_reason = assignment_reason[:27] + "..."

            table_data.append(
                [
                    str(i),
                    file_path,
                    file_info["directory"][:20]
                    if len(file_info["directory"]) > 20
                    else file_info["directory"],
                    file_info.get("assignee", "未分配")[:15],
                    status_icon,
                    priority_icon,
                    assignment_reason,
                ]
            )

        # 使用自定义表格配置
        DisplayHelper.print_table("file_status_overview", table_data)

        if len(files) > max_files:
            print(f"\n💡 显示了前 {max_files} 个文件，总共 {len(files)} 个文件")

    @staticmethod
    def print_directory_summary_table(directory_summary):
        """打印目录汇总表格"""
        if not directory_summary:
            print("📁 没有目录数据")
            return

        table_data = []
        sorted_dirs = sorted(
            directory_summary.items(), key=lambda x: x[1]["total_files"], reverse=True
        )

        for directory, stats in sorted_dirs:
            total = stats["total_files"]
            assigned = stats["assigned_files"]
            completed = stats["completed_files"]
            assignees = stats["assignees"]

            completion_rate = (completed / total * 100) if total > 0 else 0

            # 截断长目录名
            dir_display = directory
            if len(directory) > 35:
                dir_display = directory[:32] + "..."

            table_data.append(
                [
                    dir_display,
                    str(total),
                    str(assigned),
                    str(completed),
                    f"{completion_rate:.1f}%",
                    str(len(assignees)),
                ]
            )

        DisplayHelper.print_table("directory_summary", table_data)

    @staticmethod
    def print_workload_table(workload):
        """打印工作负载分布表格"""
        if not workload:
            print("👥 没有工作负载数据")
            return

        table_data = []
        sorted_workload = sorted(
            workload.items(), key=lambda x: x[1]["assigned"], reverse=True
        )

        for assignee, load_info in sorted_workload:
            assigned = load_info["assigned"]
            completed = load_info["completed"]
            pending = load_info["pending"]
            completion_rate = (completed / assigned * 100) if assigned > 0 else 0

            # 获取最新分配的文件时间
            latest_assignment = ""
            if load_info["files"]:
                latest_file = max(
                    load_info["files"],
                    key=lambda x: x.get("assigned_at", ""),
                    default={},
                )
                latest_assignment = latest_file.get("assigned_at", "")[:16]  # 只显示日期时间部分

            table_data.append(
                [
                    assignee[:20],  # 限制姓名长度
                    str(assigned),
                    str(completed),
                    str(pending),
                    f"{completion_rate:.1f}%",
                    latest_assignment,
                ]
            )

        DisplayHelper.print_table("workload_distribution", table_data)
