"""
Git Merge Orchestrator - 通用显示工具
处理大量文件列表的智能显示、分页、导出功能
"""

import json
from datetime import datetime
from pathlib import Path
from enum import Enum
from typing import List, Dict, Any, Optional


class DisplayMode(Enum):
    """显示模式枚举"""

    SUMMARY = "summary"  # 摘要模式：前10+后10+统计
    PAGINATED = "paginated"  # 分页模式：逐页浏览
    ALL = "all"  # 全部显示
    EXPORT = "export"  # 导出到文件
    STATS_ONLY = "stats_only"  # 仅统计信息


class FileListDisplayer:
    """文件列表显示器 - 智能处理大量文件显示"""

    def __init__(self, work_dir: Path = None):
        self.work_dir = work_dir or Path(".merge_work")
        self.export_dir = self.work_dir / "file_lists"
        self.export_dir.mkdir(exist_ok=True)

    def display_file_list(
        self,
        files: List[Dict[str, Any]],
        title: str = "文件列表",
        context: str = None,
        auto_threshold: int = 20,
    ) -> None:
        """
        智能显示文件列表
        
        Args:
            files: 文件信息列表
            title: 显示标题
            context: 上下文信息（如负责人姓名）
            auto_threshold: 自动显示阈值，超过此数量将提供选择菜单
        """
        total_count = len(files)

        print(f"\n📊 {title} ({total_count} 个):")
        if context:
            print(f"👤 {context}")
        print("-" * 60)

        # 小于阈值直接显示全部
        if total_count <= auto_threshold:
            self._display_all_files(files)
            return

        # 大于阈值提供选择菜单
        self._show_display_options(files, title, context)

    def _show_display_options(
        self, files: List[Dict[str, Any]], title: str, context: str = None
    ) -> None:
        """显示选择菜单"""
        print(f"\n📄 发现{len(files)}个文件，选择显示方式:")
        print("1. 📋 查看摘要 (前10 + 后10 + 统计)")
        print("2. 📖 分页浏览 (每页20个)")
        print("3. 📄 显示全部")
        print("4. 💾 导出到文件")
        print("5. 📊 仅显示统计信息")

        while True:
            try:
                choice = input("请选择 (1-5): ").strip()

                if choice == "1":
                    self._display_summary(files)
                    break
                elif choice == "2":
                    self._display_paginated(files)
                    break
                elif choice == "3":
                    self._display_all_files(files)
                    break
                elif choice == "4":
                    export_path = self._export_to_file(files, title, context)
                    print(f"✅ 文件列表已导出到: {export_path}")
                    # 显示摘要
                    self._display_summary(files)
                    break
                elif choice == "5":
                    self._display_statistics_only(files)
                    break
                else:
                    print("❌ 无效选择，请输入1-5")
            except (KeyboardInterrupt, EOFError):
                print("\n⏭️ 跳过显示")
                break

    def _display_summary(self, files: List[Dict[str, Any]]) -> None:
        """显示摘要：前10+后10+统计"""
        total = len(files)

        if total <= 20:
            self._display_all_files(files)
            return

        print(f"\n📋 文件摘要显示:")

        # 显示前10个
        print(f"\n🔼 前10个文件:")
        for i, file_info in enumerate(files[:10], 1):
            self._display_single_file(i, file_info)

        # 显示省略信息
        if total > 20:
            print(f"\n⏹️ 中间省略 {total - 20} 个文件")

        # 显示后10个
        if total > 10:
            print(f"\n🔽 后10个文件:")
            start_idx = max(10, total - 10)
            for i, file_info in enumerate(files[start_idx:], start_idx + 1):
                self._display_single_file(i, file_info)

        # 显示详细统计
        self._display_statistics(files)

    def _display_paginated(
        self, files: List[Dict[str, Any]], page_size: int = 20
    ) -> None:
        """分页显示文件列表"""
        total = len(files)
        total_pages = (total + page_size - 1) // page_size
        current_page = 1

        while True:
            start_idx = (current_page - 1) * page_size
            end_idx = min(start_idx + page_size, total)
            current_files = files[start_idx:end_idx]

            print(
                f"\n📖 第 {current_page}/{total_pages} 页 (第{start_idx + 1}-{end_idx}个，共{total}个):"
            )
            print("-" * 50)

            for i, file_info in enumerate(current_files, start_idx + 1):
                self._display_single_file(i, file_info)

            # 分页控制
            if current_page < total_pages:
                print(f"\n🔄 分页控制:")
                choice = (
                    input("继续查看? (回车=下一页, p=上一页, q=退出, all=显示全部): ").strip().lower()
                )

                if choice == "q":
                    break
                elif choice == "p" and current_page > 1:
                    current_page -= 1
                elif choice == "all":
                    self._display_all_files(files[end_idx:])
                    break
                else:
                    current_page += 1
            else:
                print(f"\n✅ 已显示全部 {total} 个文件")
                break

    def _display_all_files(self, files: List[Dict[str, Any]]) -> None:
        """显示所有文件"""
        print(f"\n📄 完整文件列表:")

        for i, file_info in enumerate(files, 1):
            self._display_single_file(i, file_info)

        self._display_statistics(files)

    def _display_single_file(self, index: int, file_info: Dict[str, Any]) -> None:
        """显示单个文件信息"""
        # 状态图标
        status_icon = {
            "pending": "⏳",
            "assigned": "📋",
            "in_progress": "🔄",
            "completed": "✅",
        }.get(file_info.get("status", "unknown"), "❓")

        # 基本信息
        path = file_info.get("path", "Unknown")
        assignee = file_info.get("assignee", "未分配")

        print(f"  {index:3d}. {status_icon} {path}")

        # 负责人信息
        if assignee != "未分配":
            print(f"       👤 负责人: {assignee}")

        # 分配原因
        reason = file_info.get("assignment_reason", "")
        if reason:
            # 限制原因显示长度，避免过长
            max_reason_length = 60
            if len(reason) > max_reason_length:
                reason = reason[:max_reason_length] + "..."
            print(f"       📝 原因: {reason}")

        # 其他信息
        if file_info.get("priority"):
            print(f"       ⭐ 优先级: {file_info['priority']}")

        if file_info.get("completed_at"):
            print(f"       ⏰ 完成时间: {file_info['completed_at']}")

    def _display_statistics(self, files: List[Dict[str, Any]]) -> None:
        """显示详细统计信息"""
        if not files:
            return

        print(f"\n📊 详细统计信息:")

        # 状态统计
        status_stats = {}
        assignee_stats = {}
        directory_stats = {}

        for file_info in files:
            # 状态统计
            status = file_info.get("status", "unknown")
            status_stats[status] = status_stats.get(status, 0) + 1

            # 负责人统计
            assignee = file_info.get("assignee", "未分配")
            assignee_stats[assignee] = assignee_stats.get(assignee, 0) + 1

            # 目录统计
            path = file_info.get("path", "")
            if "/" in path:
                directory = "/".join(path.split("/")[:-1])
            else:
                directory = "根目录"
            directory_stats[directory] = directory_stats.get(directory, 0) + 1

        # 显示状态分布
        print("📈 状态分布:")
        status_names = {
            "pending": "待处理",
            "assigned": "已分配",
            "in_progress": "进行中",
            "completed": "已完成",
        }
        for status, count in sorted(
            status_stats.items(), key=lambda x: x[1], reverse=True
        ):
            status_display = status_names.get(status, status)
            percentage = (count / len(files)) * 100
            print(f"  {status_display}: {count} 个 ({percentage:.1f}%)")

        # 显示负责人分布
        print("\n👥 负责人分布:")
        for assignee, count in sorted(
            assignee_stats.items(), key=lambda x: x[1], reverse=True
        )[:10]:
            percentage = (count / len(files)) * 100
            print(f"  {assignee}: {count} 个文件 ({percentage:.1f}%)")
        if len(assignee_stats) > 10:
            print(f"  ... 还有 {len(assignee_stats) - 10} 位负责人")

        # 显示目录分布
        print("\n📁 目录分布:")
        for directory, count in sorted(
            directory_stats.items(), key=lambda x: x[1], reverse=True
        )[:10]:
            percentage = (count / len(files)) * 100
            print(f"  {directory}: {count} 个文件 ({percentage:.1f}%)")
        if len(directory_stats) > 10:
            print(f"  ... 还有 {len(directory_stats) - 10} 个目录")

    def _display_statistics_only(self, files: List[Dict[str, Any]]) -> None:
        """仅显示统计信息"""
        print(f"\n📊 统计信息摘要:")
        print(f"总文件数: {len(files)}")
        self._display_statistics(files)

    def _export_to_file(
        self, files: List[Dict[str, Any]], title: str, context: str = None
    ) -> str:
        """导出文件列表到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 生成文件名
        if context:
            safe_context = "".join(
                c if c.isalnum() or c in ".-_" else "_" for c in context
            )
            filename = f"{safe_context}_{timestamp}.txt"
        else:
            filename = f"file_list_{timestamp}.txt"

        export_path = self.export_dir / filename

        with open(export_path, "w", encoding="utf-8") as f:
            # 文件头
            f.write(f"Git Merge Orchestrator - 文件列表导出\n")
            f.write(f"=" * 60 + "\n")
            f.write(f"标题: {title}\n")
            if context:
                f.write(f"上下文: {context}\n")
            f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"总文件数: {len(files)}\n")
            f.write(f"=" * 60 + "\n\n")

            # 详细文件列表
            for i, file_info in enumerate(files, 1):
                f.write(f"{i:4d}. {file_info.get('path', 'Unknown')}\n")
                f.write(f"      状态: {file_info.get('status', 'unknown')}\n")

                assignee = file_info.get("assignee")
                if assignee:
                    f.write(f"      负责人: {assignee}\n")

                reason = file_info.get("assignment_reason")
                if reason:
                    f.write(f"      分配原因: {reason}\n")

                priority = file_info.get("priority")
                if priority:
                    f.write(f"      优先级: {priority}\n")

                completed_at = file_info.get("completed_at")
                if completed_at:
                    f.write(f"      完成时间: {completed_at}\n")

                f.write("\n")

            # 统计信息
            f.write("\n" + "=" * 60 + "\n")
            f.write("统计信息\n")
            f.write("=" * 60 + "\n")

            # 这里可以添加统计信息的文本版本
            # 状态统计
            status_stats = {}
            assignee_stats = {}

            for file_info in files:
                status = file_info.get("status", "unknown")
                status_stats[status] = status_stats.get(status, 0) + 1

                assignee = file_info.get("assignee", "未分配")
                assignee_stats[assignee] = assignee_stats.get(assignee, 0) + 1

            f.write("\n状态分布:\n")
            for status, count in sorted(
                status_stats.items(), key=lambda x: x[1], reverse=True
            ):
                percentage = (count / len(files)) * 100
                f.write(f"  {status}: {count} 个 ({percentage:.1f}%)\n")

            f.write("\n负责人分布:\n")
            for assignee, count in sorted(
                assignee_stats.items(), key=lambda x: x[1], reverse=True
            ):
                percentage = (count / len(files)) * 100
                f.write(f"  {assignee}: {count} 个文件 ({percentage:.1f}%)\n")

        return str(export_path)


# 便捷函数
def display_files_interactive(
    files: List[Dict[str, Any]],
    title: str = "文件列表",
    context: str = None,
    work_dir: Path = None,
) -> None:
    """便捷函数：交互式显示文件列表"""
    displayer = FileListDisplayer(work_dir)
    displayer.display_file_list(files, title, context)
