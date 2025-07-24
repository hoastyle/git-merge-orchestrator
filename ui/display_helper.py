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
    def format_table_cell(text, width, align='left'):
        """格式化表格单元格，确保对齐"""
        text_str = str(text)
        display_width = DisplayHelper.get_display_width(text_str)
        padding = width - display_width

        if padding <= 0:
            return text_str[:width]

        if align == 'left':
            return text_str + ' ' * padding
        elif align == 'right':
            return ' ' * padding + text_str
        elif align == 'center':
            left_pad = padding // 2
            right_pad = padding - left_pad
            return ' ' * left_pad + text_str + ' ' * right_pad

        return text_str

    @staticmethod
    def print_table_separator(widths):
        """打印表格分隔线"""
        total_width = sum(widths) + len(widths) - 1
        print('-' * total_width)

    @staticmethod
    def print_table_header(headers, widths, aligns=None):
        """打印表格标题行"""
        if aligns is None:
            aligns = ['left'] * len(headers)

        row = []
        for header, width, align in zip(headers, widths, aligns):
            row.append(DisplayHelper.format_table_cell(header, width, align))

        print(' '.join(row))
        DisplayHelper.print_table_separator(widths)

    @staticmethod
    def print_table_row(values, widths, aligns=None):
        """打印表格数据行"""
        if aligns is None:
            aligns = ['left'] * len(values)

        row = []
        for value, width, align in zip(values, widths, aligns):
            row.append(DisplayHelper.format_table_cell(value, width, align))

        print(' '.join(row))

    @staticmethod
    def print_table(table_name, data_rows, extra_info=None):
        """打印预配置的表格"""
        if table_name not in TABLE_CONFIGS:
            print(f"❌ 未知的表格类型: {table_name}")
            return

        config = TABLE_CONFIGS[table_name]
        headers = config['headers']
        widths = config['widths']
        aligns = config['aligns']

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
            return ACTIVITY_LEVELS['inactive']

        for level_name, level_info in ACTIVITY_LEVELS.items():
            if level_name == 'inactive':
                continue
            if recent_commits >= level_info['threshold']:
                return level_info

        return ACTIVITY_LEVELS['recent']

    @staticmethod
    def categorize_assignment_reason(reason):
        """将分配原因分类"""
        if not reason or reason == '未指定':
            return '未指定'

        for category, keyword in ASSIGNMENT_REASON_TYPES.items():
            if keyword in reason:
                return category

        return '其他'

    @staticmethod
    def format_assignment_summary(assignment_count, unassigned_groups):
        """格式化分配总结"""
        summary = "\n📊 自动分配总结:\n"
        summary += f"👥 任务分配:\n"

        for person, count in sorted(assignment_count.items(), key=lambda x: x[1], reverse=True):
            summary += f" {person}: {count} 个任务\n"

        if unassigned_groups:
            summary += f"\n⚠️ 未分配的组 ({len(unassigned_groups)}个): "
            summary += ', '.join(unassigned_groups[:3])
            if len(unassigned_groups) > 3:
                summary += "..."

        return summary

    @staticmethod
    def format_workload_distribution(assignee_workload):
        """格式化负载分布"""
        if not assignee_workload:
            return ""

        distribution = "\n👥 负载分布:\n"
        sorted_workload = sorted(assignee_workload.items(),
                               key=lambda x: x[1]["files"], reverse=True)

        for person, workload in sorted_workload:
            fallback_info = f"(含{workload['fallback']}个备选)" if workload['fallback'] > 0 else ""
            distribution += f" {person}: {workload['completed']}/{workload['groups']} 组完成, "
            distribution += f"{workload['files']} 个文件 {fallback_info}\n"

        return distribution.rstrip()

    @staticmethod
    def format_completion_stats(stats):
        """格式化完成统计"""
        if not stats:
            return "📈 进度统计: 数据不可用"

        assigned_groups = stats.get('assigned_groups', 0)
        total_groups = stats.get('total_groups', 0)
        assigned_files = stats.get('assigned_files', 0)
        total_files = stats.get('total_files', 0)
        completed_groups = stats.get('completed_groups', 0)

        completion_info = f"📈 进度统计: {assigned_groups}/{total_groups} 组已分配 "
        completion_info += f"({assigned_files}/{total_files} 文件), "
        completion_info += f"{completed_groups}/{total_groups} 组已完成"
        return completion_info

    @staticmethod
    def display_group_detail(group, file_helper):
        """显示单个组的详细信息"""
        print("\n" + "="*100)
        print(f"📁 组详细信息: {group['name']}")
        print("="*100)

        # 基本信息
        print(f"📊 基本信息:")
        print(f"   组名: {group['name']}")
        group_type_desc = file_helper.get_group_type_description(group.get('group_type', 'unknown'))
        print(f"   类型: {group.get('group_type', 'unknown')} ({group_type_desc})")
        print(f"   文件数: {group.get('file_count', len(group['files']))} 个")
        print(f"   负责人: {group.get('assignee', '未分配')}")

        status = group.get('status', 'pending')
        status_text = {'completed': '✅ 已完成', 'pending': '⏳ 待分配'}.get(
            status, '🔄 进行中' if group.get('assignee') else '⏳ 待分配'
        )
        print(f"   状态: {status_text}")

        # 分配原因
        assignment_reason = group.get('assignment_reason', '未指定')
        if assignment_reason:
            print(f"   分配原因: {assignment_reason}")

        # 备选分配信息
        fallback_reason = group.get('fallback_reason', '')
        if fallback_reason:
            print(f"   备选原因: {fallback_reason}")

        # 文件列表
        print(f"\n📄 包含文件列表:")
        files = group.get('files', [])
        for i, file_path in enumerate(files, 1):
            print(f"   {i:2d}. {file_path}")

        # 贡献者分析
        contributors = group.get('contributors', {})
        if contributors:
            print(f"\n👥 贡献者分析 (基于一年内活跃度):")

            contrib_data = []
            sorted_contributors = sorted(contributors.items(),
                                       key=lambda x: x[1]['score'] if isinstance(x[1], dict) else x[1],
                                       reverse=True)

            for i, (author, stats) in enumerate(sorted_contributors[:10], 1):
                if isinstance(stats, dict):
                    recent = stats.get('recent_commits', 0)
                    total = stats.get('total_commits', 0)
                    score = stats.get('score', 0)
                    file_count = stats.get('file_count', 0)
                    row_data = [str(i), author, str(recent), str(total), str(score), str(file_count)]
                else:
                    row_data = [str(i), author, 'N/A', str(stats), str(stats), 'N/A']

                contrib_data.append(row_data)

            DisplayHelper.print_table('contributor_ranking', contrib_data[:len(contrib_data)])

            if len(sorted_contributors) > 10:
                print(f"   ... 还有 {len(sorted_contributors) - 10} 位贡献者")

        # 备注信息
        notes = group.get('notes', '')
        if notes:
            print(f"\n📝 备注: {notes}")

        print("="*100)

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
        print("9. 检查状态")
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