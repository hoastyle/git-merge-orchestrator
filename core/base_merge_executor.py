"""
Git Merge Orchestrator - 抽象合并执行器基类
消除Standard和Legacy执行器的重复代码，实现DRY原则
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum


class MergeStrategy(Enum):
    """合并策略枚举"""

    LEGACY = "legacy"
    STANDARD = "standard"


class BaseMergeExecutor(ABC):
    """抽象合并执行器基类 - 提取公共逻辑"""

    def __init__(self, git_ops, file_helper, strategy: MergeStrategy):
        self.git_ops = git_ops
        self.file_helper = file_helper
        self.strategy = strategy

    def analyze_file_modifications(self, files, source_branch, target_branch):
        """分析文件的修改情况（公共逻辑）"""
        print(f"🔍 正在进行{self.get_strategy_name()}模式文件分析...")

        # 获取merge-base
        merge_base = self.git_ops.get_merge_base(source_branch, target_branch)
        if not merge_base:
            print("⚠️ 无法确定分叉点，使用简化分析策略")
            return self._simple_file_analysis(files, source_branch, target_branch)

        existing_files, missing_files = self.git_ops.check_file_existence(
            files, target_branch
        )

        # 详细分析已存在文件的修改情况
        modified_in_both = []
        modified_only_in_source = []
        no_changes = []

        for file in existing_files:
            # 检查源分支相对于merge-base是否有修改
            source_cmd = f'git diff --quiet {merge_base} {source_branch} -- "{file}"'
            source_result = self.git_ops.run_command_silent(source_cmd)
            source_modified = source_result is None

            # 检查目标分支相对于merge-base是否有修改
            target_cmd = f'git diff --quiet {merge_base} {target_branch} -- "{file}"'
            target_result = self.git_ops.run_command_silent(target_cmd)
            target_modified = target_result is None

            if source_modified and target_modified:
                modified_in_both.append(file)
            elif source_modified and not target_modified:
                modified_only_in_source.append(file)
            elif not source_modified and not target_modified:
                no_changes.append(file)

        analysis_result = {
            "missing_files": missing_files,
            "modified_only_in_source": modified_only_in_source,
            "modified_in_both": modified_in_both,
            "no_changes": no_changes,
            "merge_base": merge_base,
        }

        # 策略特定的分析结果描述
        self._print_analysis_result(analysis_result)
        return analysis_result

    def _simple_file_analysis(self, files, source_branch, target_branch):
        """简化的文件分析策略（公共逻辑）"""
        existing_files, missing_files = self.git_ops.check_file_existence(
            files, target_branch
        )

        return {
            "missing_files": missing_files,
            "modified_only_in_source": [],
            "modified_in_both": existing_files,
            "no_changes": [],
            "merge_base": None,
        }

    def merge_group(self, group_name, source_branch, target_branch, integration_branch):
        """合并指定组（模板方法）"""
        plan = self.file_helper.load_plan()
        if not plan:
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return False

        group_info = self.file_helper.find_group_by_name(plan, group_name)
        if not group_info:
            print(f"❌ 未找到组: {group_name}")
            return False

        assignee = group_info["assignee"]
        if not assignee:
            print(f"❌ 组 {group_name} 尚未分配负责人")
            return False

        print(f"🎯 准备使用{self.get_strategy_name()}模式合并组: {group_name}")
        print(f"👤 负责人: {assignee}")
        print(f"📁 文件数: {group_info.get('file_count', len(group_info['files']))}")
        print(f"💡 {self.get_strategy_description()}")

        # 创建合并分支
        branch_name = self.git_ops.create_merge_branch(
            group_name, assignee, integration_branch
        )

        # 策略特定的脚本生成
        script_content = self.generate_merge_script(
            group_name,
            assignee,
            group_info["files"],
            branch_name,
            source_branch,
            target_branch,
        )

        script_file = self.file_helper.create_script_file(
            f"{self.strategy.value}_merge_{group_name.replace('/', '_')}",
            script_content,
        )

        self._print_script_completion_message(script_file)
        return True

    def merge_assignee_tasks(
        self, assignee_name, source_branch, target_branch, integration_branch
    ):
        """批量合并指定负责人任务（模板方法）"""
        plan = self.file_helper.load_plan()
        if not plan:
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return False

        assignee_groups = self.file_helper.get_assignee_groups(plan, assignee_name)
        if not assignee_groups:
            print(f"❌ 负责人 '{assignee_name}' 没有分配的任务")
            return False

        total_files = sum(g.get("file_count", len(g["files"])) for g in assignee_groups)
        print(f"🎯 开始{self.get_strategy_name()}批量合并负责人 '{assignee_name}' 的所有任务...")
        print(f"📋 共 {len(assignee_groups)} 个组，总计 {total_files} 个文件")
        print(f"💡 {self.get_strategy_description()}")

        # 收集所有文件
        all_files = []
        for group in assignee_groups:
            all_files.extend(group["files"])

        if not all_files:
            print("❌ 没有找到需要合并的文件")
            return False

        # 创建批量合并分支
        batch_branch_name = self.git_ops.create_batch_merge_branch(
            assignee_name, integration_branch
        )

        # 策略特定的批量脚本生成
        script_content = self.generate_batch_merge_script(
            assignee_name,
            assignee_groups,
            all_files,
            batch_branch_name,
            source_branch,
            target_branch,
        )

        script_file = self.file_helper.create_script_file(
            f"{self.strategy.value}_merge_batch_{assignee_name.replace(' ', '_')}",
            script_content,
        )

        self._print_batch_script_completion_message(script_file)
        return True

    def finalize_merge(self, integration_branch):
        """完成最终合并（公共逻辑）"""
        print(f"🎯 开始{self.get_strategy_name()}模式最终合并...")

        plan = self.file_helper.load_plan()
        if not plan:
            print("❌ 合并计划文件不存在")
            return False

        # 切换到集成分支
        self.git_ops.run_command(f"git checkout {integration_branch}")

        # 检查哪些分支已完成
        completed_branches = []
        for group in plan["groups"]:
            if group["status"] == "completed" and group.get("assignee"):
                branch_name = f"feat/merge-{group['name'].replace('/', '-')}-{group['assignee'].replace(' ', '-')}"
                if self.git_ops.get_branch_exists(branch_name):
                    completed_branches.append((branch_name, group))

        if not completed_branches:
            print("⚠️ 没有找到已完成的合并分支")
            return False

        print(f"🔍 发现 {len(completed_branches)} 个已完成的分支:")
        total_files = 0
        for branch_name, group in completed_branches:
            file_count = group.get("file_count", len(group["files"]))
            total_files += file_count
            print(f" - {branch_name} ({file_count} 文件)")

        print(f"📊 总计将合并 {total_files} 个文件")

        # 合并所有完成的分支
        all_success = True
        for branch_name, group in completed_branches:
            print(f"🔄 正在合并分支: {branch_name}")
            success = self.git_ops.merge_branch_to_integration(
                branch_name, group["name"], integration_branch
            )
            if success:
                print(f" ✅ 成功合并 {branch_name}")
            else:
                print(f" ❌ 合并 {branch_name} 时出现问题")
                all_success = False

        if all_success:
            print(f"🎉 {self.get_strategy_name()}模式最终合并完成!")
            print(f"📋 集成分支 {integration_branch} 已包含所有更改")
            self._print_finalize_success_message(plan)

        return all_success

    # === 抽象方法：子类必须实现 ===

    @abstractmethod
    def generate_merge_script(
        self, group_name, assignee, files, branch_name, source_branch, target_branch
    ):
        """生成合并脚本（策略特定）"""
        pass

    @abstractmethod
    def generate_batch_merge_script(
        self,
        assignee,
        assignee_groups,
        all_files,
        batch_branch_name,
        source_branch,
        target_branch,
    ):
        """生成批量合并脚本（策略特定）"""
        pass

    @abstractmethod
    def get_strategy_name(self):
        """获取策略名称"""
        pass

    @abstractmethod
    def get_strategy_description(self):
        """获取策略描述"""
        pass

    @abstractmethod
    def _generate_strategy_specific_merge_logic(
        self, analysis, source_branch, target_branch
    ):
        """生成策略特定的合并逻辑（核心差异）"""
        pass

    # === 策略特定的辅助方法：子类可重写 ===

    def _print_analysis_result(self, analysis_result):
        """打印分析结果（可重写）"""
        missing_files = analysis_result["missing_files"]
        modified_only_in_source = analysis_result["modified_only_in_source"]
        modified_in_both = analysis_result["modified_in_both"]
        no_changes = analysis_result["no_changes"]

        print(f"📊 {self.get_strategy_name()}模式文件修改分析结果:")
        print(f"  - 新增文件: {len(missing_files)} 个")
        print(f"  - 仅源分支修改: {len(modified_only_in_source)} 个")
        print(f"  - 两边都修改: {len(modified_in_both)} 个")
        print(f"  - 无变化: {len(no_changes)} 个")

    def _print_script_completion_message(self, script_file):
        """打印脚本生成完成消息（可重写）"""
        print(f"✅ 已生成{self.get_strategy_name()}合并脚本: {script_file}")
        print(f"🎯 请执行: ./{script_file}")

    def _print_batch_script_completion_message(self, script_file):
        """打印批量脚本生成完成消息（可重写）"""
        print(f"✅ 已生成{self.get_strategy_name()}批量合并脚本: {script_file}")
        print(f"🎯 请执行: ./{script_file}")

    def _print_finalize_success_message(self, plan):
        """打印最终合并成功消息（可重写）"""
        print(f"🚀 建议操作:")
        print(f" 1. 验证合并结果: git log --oneline -10")
        print(f" 2. 运行完整测试套件")
        print(
            f" 3. 推送到远程: git push origin {plan.get('integration_branch', 'integration')}"
        )
        print(f" 4. 创建PR/MR合并到 {plan.get('target_branch', 'main')}")

    # === 公共辅助方法 ===

    def _generate_common_script_header(
        self, group_name, assignee, files, branch_name, script_type="单组"
    ):
        """生成脚本通用头部"""
        file_count = len(files)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return f"""#!/bin/bash
# {self.get_strategy_name()}模式{script_type}合并脚本 - {group_name} (负责人: {assignee})
# 策略: {self.get_strategy_description()}
# 文件数: {file_count}
# 创建时间: {timestamp}

set -e # 遇到错误立即退出

echo "🚀 开始{self.get_strategy_name()}模式{script_type}合并: {group_name}"
echo "👤 负责人: {assignee}"
echo "🌿 工作分支: {branch_name}"
echo "📁 文件数: {file_count}"
echo "💡 策略说明: {self.get_strategy_description()}"
echo ""

# 切换到工作分支
echo "📋 切换到工作分支..."
git checkout {branch_name}
"""

    def _generate_merge_base_section(self, source_branch, target_branch):
        """生成merge-base检测部分"""
        return f"""
# 获取merge-base
MERGE_BASE=$(git merge-base {source_branch} {target_branch} 2>/dev/null || echo "")
if [ -n "$MERGE_BASE" ]; then
    echo "🔍 找到分叉点: $MERGE_BASE"
else
    echo "⚠️ 无法确定分叉点，将使用策略特定的合并方式"
fi
echo ""
"""

    def _generate_common_file_processing_sections(self, analysis, source_branch):
        """生成公共的文件处理部分"""
        missing_files = analysis["missing_files"]
        modified_only_in_source = analysis["modified_only_in_source"]
        no_changes = analysis["no_changes"]

        script_sections = []

        # 处理新增文件（所有策略相同）
        if missing_files:
            script_sections.append(
                f"""
echo "🆕 处理新增文件 ({len(missing_files)}个) - 直接复制..."
"""
            )
            for file in missing_files:
                script_sections.append(
                    f"""
echo "  [新增] {file}"
mkdir -p "$(dirname "{file}")"
if git show {source_branch}:"{file}" > "{file}" 2>/dev/null; then
    echo "    ✅ 新文件已复制到工作区"
    total_processed=$((total_processed + 1))
else
    echo "    ❌ 无法从源分支获取文件: {file}"
    merge_success=false
fi
"""
                )

        # 处理仅源分支修改的文件（所有策略相同）
        if modified_only_in_source:
            script_sections.append(
                f"""
echo ""
echo "📝 处理仅源分支修改的文件 ({len(modified_only_in_source)}个) - 安全覆盖..."
"""
            )
            for file in modified_only_in_source:
                script_sections.append(
                    f"""
echo "  [覆盖] {file}"
if git show {source_branch}:"{file}" > "{file}" 2>/dev/null; then
    echo "    ✅ 文件已更新（目标分支无修改，安全覆盖）"
    total_processed=$((total_processed + 1))
else
    echo "    ❌ 无法从源分支获取文件: {file}"
    merge_success=false
fi
"""
                )

        # 处理无变化的文件（所有策略相同）
        if no_changes:
            script_sections.append(
                f"""
echo ""
echo "📋 跳过无变化的文件 ({len(no_changes)}个)..."
"""
            )
            for file in no_changes:
                script_sections.append(f'echo "  [跳过] {file} (两个分支中内容相同)"\n')

        return "\n".join(script_sections)

    def _generate_common_script_footer(self, group_name, file_count, branch_name):
        """生成脚本通用结尾"""
        return f"""
echo ""
echo "📊 处理完成统计："
echo "  - 已处理文件: $total_processed 个"
echo "  - 总目标文件: {file_count} 个"

# 显示当前工作区状态
echo ""
echo "📋 当前工作区状态："
git status --short

echo ""

if [ "$merge_success" = true ]; then
    echo "⏭️ 推荐后续操作："
    echo " 1. 检查修改: git diff"
    echo " 2. 运行测试: npm test 或 python -m pytest"
    echo " 3. 添加文件: git add <files...>"
    echo " 4. 检查暂存: git status"
    echo " 5. 提交更改: git commit -m '{self.get_strategy_name()} merge group: {group_name} ({file_count} files)'"
    echo " 6. 推送分支: git push origin {branch_name}"
    echo ""
    echo "🔄 如需回滚: git checkout -- <文件名> 或 git reset --hard HEAD"
else
    echo "🛠️ 问题排查指南："
    echo " 1. 检查Git仓库状态: git status"
    echo " 2. 检查分支是否存在: git branch -a"
    echo " 3. 如需重新开始: git reset --hard HEAD && git clean -fd"
    exit 1
fi

echo ""
echo "💡 {self.get_strategy_name()}模式说明："
{self._get_strategy_footer_notes()}
"""

    def _generate_common_batch_script_footer(
        self, assignee, group_count, file_count, branch_name
    ):
        """生成批量脚本通用结尾"""
        return f"""
echo ""
echo "📊 批量处理完成统计："
echo "  - 已处理文件: $total_processed 个"
echo "  - 总目标文件: {file_count} 个"

echo ""
git status --short

echo ""

if [ "$merge_success" = true ]; then
    echo "⏭️ 推荐批量后续操作："
    echo " 1. 检查所有修改: git diff"
    echo " 2. 运行完整测试: npm test 或 python -m pytest"
    echo " 3. 选择添加策略："
    echo "    a) 按组分批添加 (推荐)"
    echo "    b) 全部添加: git add ."
    echo " 4. 检查暂存状态: git status"
    echo " 5. 提交: git commit -m '{self.get_strategy_name()} batch merge for {assignee}: {group_count} groups, {file_count} files'"
    echo " 6. 推送分支: git push origin {branch_name}"
    echo ""
    echo "🔄 回滚选项："
    echo " - 回滚单个文件: git checkout -- <文件名>"
    echo " - 完全重置: git reset --hard HEAD"
else
    echo "🛠️ 批量处理问题排查："
    echo " 1. 检查文件权限和磁盘空间"
    echo " 2. 验证分支完整性: git fsck"
    echo " 3. 考虑分批处理减少复杂度"
    exit 1
fi

echo ""
echo "💡 {self.get_strategy_name()}批量处理最佳实践："
{self._get_batch_strategy_footer_notes()}
"""

    @abstractmethod
    def _get_strategy_footer_notes(self):
        """获取策略特定的脚本结尾说明"""
        pass

    @abstractmethod
    def _get_batch_strategy_footer_notes(self):
        """获取批量策略特定的脚本结尾说明"""
        pass
