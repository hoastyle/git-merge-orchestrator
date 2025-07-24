"""
Git Merge Orchestrator - 合并执行器 (改进版)
负责生成改进的合并脚本和执行合并操作
使用真正的三路合并策略，避免丢失目标分支的修改
"""

from datetime import datetime


class MergeExecutor:
    """合并执行器 - 使用改进的三路合并策略"""

    def __init__(self, git_ops, file_helper):
        self.git_ops = git_ops
        self.file_helper = file_helper

    def analyze_file_modifications(self, files, source_branch, target_branch):
        """分析文件的修改情况，为智能合并策略提供依据"""
        print("🔍 正在分析文件修改情况...")

        # 获取merge-base
        merge_base = self.git_ops.get_merge_base(source_branch, target_branch)
        if not merge_base:
            print("⚠️ 无法确定分叉点，使用简化分析策略")
            return self._simple_file_analysis(files, source_branch, target_branch)

        existing_files, missing_files = self.git_ops.check_file_existence(files, target_branch)

        # 详细分析已存在文件的修改情况
        modified_in_both = []
        modified_only_in_source = []
        no_changes = []

        for file in existing_files:
            # 检查源分支相对于merge-base是否有修改
            source_cmd = f"git diff --quiet {merge_base} {source_branch} -- \"{file}\""
            source_modified = self.git_ops.run_command(source_cmd) is None

            # 检查目标分支相对于merge-base是否有修改
            target_cmd = f"git diff --quiet {merge_base} {target_branch} -- \"{file}\""
            target_modified = self.git_ops.run_command(target_cmd) is None

            if source_modified and target_modified:
                modified_in_both.append(file)
            elif source_modified and not target_modified:
                modified_only_in_source.append(file)
            elif not source_modified and not target_modified:
                no_changes.append(file)
            # 如果只有target修改，源分支没修改，那这个文件不应该在变更列表中

        analysis_result = {
            'missing_files': missing_files,
            'modified_only_in_source': modified_only_in_source,
            'modified_in_both': modified_in_both,
            'no_changes': no_changes,
            'merge_base': merge_base
        }

        print(f"📊 文件修改分析结果:")
        print(f"  - 新增文件: {len(missing_files)} 个")
        print(f"  - 仅源分支修改: {len(modified_only_in_source)} 个")
        print(f"  - 两边都修改: {len(modified_in_both)} 个")
        print(f"  - 无变化: {len(no_changes)} 个")

        return analysis_result

    def _simple_file_analysis(self, files, source_branch, target_branch):
        """简化的文件分析策略（当无法确定merge-base时）"""
        existing_files, missing_files = self.git_ops.check_file_existence(files, target_branch)

        # 简化策略：假设所有已存在文件都可能有冲突
        return {
            'missing_files': missing_files,
            'modified_only_in_source': [],
            'modified_in_both': existing_files,  # 保守策略：都当作可能冲突处理
            'no_changes': [],
            'merge_base': None
        }

    def generate_smart_merge_script(self, group_name, assignee, files, branch_name, source_branch, target_branch):
        """生成改进的智能合并脚本，使用真正的三路合并策略"""

        # 分析文件修改情况
        analysis = self.analyze_file_modifications(files, source_branch, target_branch)

        missing_files = analysis['missing_files']
        modified_only_in_source = analysis['modified_only_in_source']
        modified_in_both = analysis['modified_in_both']
        no_changes = analysis['no_changes']
        merge_base = analysis['merge_base']

        # 生成改进的处理脚本
        script_content = f"""#!/bin/bash
# 改进的智能合并脚本 - {group_name} (负责人: {assignee})
# 使用真正的三路合并策略，避免丢失目标分支的修改
# 文件数: {len(files)} (新增: {len(missing_files)}, 仅源修改: {len(modified_only_in_source)}, 两边修改: {len(modified_in_both)})
# 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

set -e # 遇到错误立即退出

echo "🚀 开始改进的智能合并组: {group_name}"
echo "👤 负责人: {assignee}"
echo "🌿 工作分支: {branch_name}"
echo "📁 总文件数: {len(files)}"
echo "📊 文件分类："
echo "  - 新增文件: {len(missing_files)} 个"
echo "  - 仅源分支修改: {len(modified_only_in_source)} 个"
echo "  - 两边都修改: {len(modified_in_both)} 个"
echo "  - 无变化: {len(no_changes)} 个"
echo ""

# 切换到工作分支
echo "📋 切换到工作分支..."
git checkout {branch_name}
"""

        # 添加merge-base信息
        if merge_base:
            script_content += f"""
# 获取merge-base用于三路合并
MERGE_BASE="{merge_base}"
echo "🔍 分叉点: $MERGE_BASE"
echo ""
"""
        else:
            script_content += f"""
# 尝试获取merge-base
MERGE_BASE=$(git merge-base {source_branch} {target_branch} 2>/dev/null || echo "")
if [ -n "$MERGE_BASE" ]; then
    echo "🔍 分叉点: $MERGE_BASE"
else
    echo "⚠️ 无法确定分叉点，将使用保守的合并策略"
fi
echo ""
"""

        script_content += """
merge_success=true
conflicts_found=false

echo "🔄 开始智能三路合并..."
"""

        # 处理新增文件
        if missing_files:
            script_content += f"""
echo "🆕 处理新增文件 ({len(missing_files)}个)..."
"""
            for file in missing_files:
                script_content += f"""
echo "  处理新文件: {file}"
# 创建目录结构
mkdir -p "$(dirname "{file}")"
# 从源分支复制文件内容
if git show {source_branch}:"{file}" > "{file}" 2>/dev/null; then
    git add "{file}"
    echo "    ✅ 新文件 {file} 添加成功"
else
    echo "    ❌ 无法从源分支获取文件: {file}"
    merge_success=false
fi
"""

        # 处理仅源分支修改的文件
        if modified_only_in_source:
            script_content += f"""
echo "📝 处理仅源分支修改的文件 ({len(modified_only_in_source)}个)..."
"""
            for file in modified_only_in_source:
                script_content += f"""
echo "  合并文件: {file} (仅源分支有修改，安全替换)"
if git checkout {source_branch} -- "{file}"; then
    echo "    ✅ 文件 {file} 合并成功"
else
    echo "    ❌ 无法从源分支获取文件: {file}"
    merge_success=false
fi
"""

        # 处理两边都修改的文件
        if modified_in_both:
            script_content += f"""
echo "⚡ 处理两边都修改的文件 ({len(modified_in_both)}个) - 使用三路合并..."
"""
            for file in modified_in_both:
                script_content += f"""
echo "  三路合并文件: {file}"

# 尝试自动三路合并
if git checkout --merge {source_branch} -- "{file}" 2>/dev/null; then
    # 检查是否有冲突标记
    if grep -q "<<<<<<< " "{file}" 2>/dev/null; then
        echo "    ⚠️ 文件 {file} 存在合并冲突，需要手动解决"
        conflicts_found=true
        echo "    💡 冲突标记说明："
        echo "       <<<<<<< HEAD     (当前分支的内容)"
        echo "       =======          (分隔线)"
        echo "       >>>>>>> {source_branch}  (源分支的内容)"
        echo "    📝 请编辑文件解决冲突后运行: git add {file}"
    else
        echo "    ✅ 文件 {file} 自动合并成功"
        git add "{file}"
    fi
else
    echo "    ⚠️ 文件 {file} 自动合并失败，创建手动合并参考文件"

    # 创建参考文件用于手动合并
    if [ -n "$MERGE_BASE" ]; then
        git show $MERGE_BASE:"{file}" > "{file}.base" 2>/dev/null || echo "# 分叉点版本（文件可能不存在）" > "{file}.base"
    else
        echo "# 无法获取分叉点版本" > "{file}.base"
    fi

    git show {target_branch}:"{file}" > "{file}.target" 2>/dev/null || cp "{file}" "{file}.target"
    git show {source_branch}:"{file}" > "{file}.source" 2>/dev/null || echo "# 无法获取源分支版本" > "{file}.source"

    echo "    📁 已创建合并参考文件："
    echo "       - {file}.base   (分叉点版本)"
    echo "       - {file}.target (目标分支版本)"
    echo "       - {file}.source (源分支版本)"
    echo "    📝 请参考这些文件手动合并，完成后："
    echo "       1. 编辑 {file} 为最终版本"
    echo "       2. 删除临时文件: rm {file}.base {file}.target {file}.source"
    echo "       3. 添加文件: git add {file}"

    conflicts_found=true
fi
"""

        # 处理无变化的文件（理论上不应该在变更列表中，但为了完整性）
        if no_changes:
            script_content += f"""
echo "📋 跳过无变化的文件 ({len(no_changes)}个)..."
"""
            for file in no_changes:
                script_content += f'echo "  跳过: {file} (两个分支中内容相同)"\n'

        # 添加最终处理逻辑
        script_content += f"""
echo ""

if [ "$conflicts_found" = true ]; then
    echo "⚠️ 发现合并冲突，需要手动处理"
    echo ""
    echo "🔧 冲突解决步骤："
    echo " 1. 查看冲突文件列表: git status"
    echo " 2. 编辑有冲突标记的文件 (<<<<<<< ======= >>>>>>>)"
    echo " 3. 对于有.base/.target/.source参考文件的，参考这些文件进行合并"
    echo " 4. 解决冲突后运行: git add <文件名>"
    echo " 5. 删除临时参考文件: rm *.base *.target *.source"
    echo " 6. 检查所有文件都已添加: git status"
    echo " 7. 验证合并结果无误后继续后续步骤"
    echo ""
    echo "💡 合并建议："
    echo " - 仔细比较两个版本的差异"
    echo " - 保留两边有价值的修改"
    echo " - 测试合并后的代码是否正常工作"
    echo " - 如有疑问，联系相关文件的原作者"

elif [ "$merge_success" = true ]; then
    echo "✅ 智能三路合并完成!"
    echo ""
    echo "📊 合并状态:"
    git status --short
    echo ""
    echo "🔍 文件差异概览:"
    git diff --cached --stat 2>/dev/null || echo "(新文件无差异显示)"

else
    echo "❌ 合并过程中出现问题"
    merge_success=false
fi

if [ "$merge_success" = true ] && [ "$conflicts_found" = false ]; then
    echo ""
    echo "⏭️ 下一步操作："
    echo " 1. 检查合并结果: git diff --cached"
    echo " 2. 运行测试确保代码正常: npm test 或 python -m pytest 等"
    echo " 3. 提交更改: git commit -m 'Merge group: {group_name} ({len(files)} files)'"
    echo " 4. 推送分支: git push origin {branch_name}"
    echo ""
    echo "🔄 如需回滚: git reset --hard HEAD"

else
    echo ""
    echo "⏳ 需要手动处理冲突后再继续"
    echo ""
    echo "📊 当前状态:"
    git status
    echo ""
    echo "🔄 处理完冲突后的步骤："
    echo " 1. 确认所有冲突已解决: git status"
    echo " 2. 运行测试: npm test 或 python -m pytest 等"
    echo " 3. 提交: git commit -m 'Merge group: {group_name} (resolved conflicts)'"
    echo " 4. 推送: git push origin {branch_name}"
fi
"""

        return script_content

    def generate_batch_merge_script(self, assignee, assignee_groups, all_files, batch_branch_name,
                                  source_branch, target_branch):
        """生成改进的批量合并脚本"""

        # 分析所有文件的修改情况
        print(f"🔍 正在分析负责人 '{assignee}' 的所有文件...")
        analysis = self.analyze_file_modifications(all_files, source_branch, target_branch)

        missing_files = analysis['missing_files']
        modified_only_in_source = analysis['modified_only_in_source']
        modified_in_both = analysis['modified_in_both']
        no_changes = analysis['no_changes']

        script_content = f"""#!/bin/bash
# 改进的批量智能合并脚本 - 负责人: {assignee}
# 使用真正的三路合并策略，避免丢失目标分支的修改
# 组数: {len(assignee_groups)} (文件总数: {len(all_files)})
# 文件分类: 新增{len(missing_files)}, 仅源修改{len(modified_only_in_source)}, 两边修改{len(modified_in_both)}
# 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

set -e # 遇到错误立即退出

echo "🚀 开始批量智能合并负责人 '{assignee}' 的所有任务"
echo "🌿 工作分支: {batch_branch_name}"
echo "📁 总文件数: {len(all_files)}"
echo "📊 文件分类："
echo "  - 新增文件: {len(missing_files)} 个"
echo "  - 仅源分支修改: {len(modified_only_in_source)} 个"
echo "  - 两边都修改: {len(modified_in_both)} 个"
echo "  - 无变化: {len(no_changes)} 个"
echo "📋 包含组: {', '.join([g['name'] for g in assignee_groups])}"
echo ""

# 切换到工作分支
echo "📋 切换到工作分支..."
git checkout {batch_branch_name}

# 获取merge-base
MERGE_BASE=$(git merge-base {source_branch} {target_branch} 2>/dev/null || echo "")
if [ -n "$MERGE_BASE" ]; then
    echo "🔍 分叉点: $MERGE_BASE"
else
    echo "⚠️ 无法确定分叉点，将使用保守的合并策略"
fi

echo "📄 组别详情:"
{chr(10).join([f'echo "  组 {g["name"]}: {g.get("file_count", len(g["files"]))} 个文件"' for g in assignee_groups])}
echo ""

merge_success=true
conflicts_found=false

echo "🔄 开始批量智能三路合并..."
"""

        # 处理新增文件
        if missing_files:
            script_content += f"""
echo "🆕 处理新增文件 ({len(missing_files)}个)..."
"""
            for file in missing_files:
                script_content += f"""
echo "  处理新文件: {file}"
mkdir -p "$(dirname "{file}")"
if git show {source_branch}:"{file}" > "{file}" 2>/dev/null; then
    git add "{file}"
    echo "    ✅ 新文件 {file} 添加成功"
else
    echo "    ❌ 无法从源分支获取文件: {file}"
    merge_success=false
fi
"""

        # 处理仅源分支修改的文件
        if modified_only_in_source:
            script_content += f"""
echo "📝 处理仅源分支修改的文件 ({len(modified_only_in_source)}个)..."
"""
            for file in modified_only_in_source:
                script_content += f"""
echo "  合并文件: {file}"
if git checkout {source_branch} -- "{file}"; then
    echo "    ✅ 文件 {file} 合并成功"
else
    echo "    ❌ 无法从源分支获取文件: {file}"
    merge_success=false
fi
"""

        # 处理两边都修改的文件
        if modified_in_both:
            script_content += f"""
echo "⚡ 处理两边都修改的文件 ({len(modified_in_both)}个) - 使用三路合并..."
"""
            for file in modified_in_both:
                script_content += f"""
echo "  三路合并文件: {file}"
if git checkout --merge {source_branch} -- "{file}" 2>/dev/null; then
    if grep -q "<<<<<<< " "{file}" 2>/dev/null; then
        echo "    ⚠️ 文件 {file} 存在合并冲突"
        conflicts_found=true
    else
        echo "    ✅ 文件 {file} 自动合并成功"
        git add "{file}"
    fi
else
    echo "    ⚠️ 文件 {file} 需要手动处理"
    conflicts_found=true
fi
"""

        # 添加批量处理的最终逻辑
        script_content += f"""
echo ""

if [ "$conflicts_found" = true ]; then
    echo "⚠️ 批量合并中发现冲突，需要手动处理"
    echo ""
    echo "🔧 批量冲突解决步骤："
    echo " 1. 查看所有冲突文件: git status"
    echo " 2. 逐个编辑有冲突标记的文件"
    echo " 3. 解决冲突后逐个添加: git add <文件名>"
    echo " 4. 或者分组处理："
    echo "    - 先处理简单冲突"
    echo "    - 复杂冲突可以拆分到单独的组中处理"
    echo " 5. 全部解决后检查: git status"
    echo ""
    echo "💡 批量处理建议："
    echo " - 按组分类处理冲突，每个组的文件通常相关性较强"
    echo " - 优先处理自动合并成功的文件，先提交一部分"
    echo " - 复杂冲突可以联系对应组的其他开发者协助"

elif [ "$merge_success" = true ]; then
    echo "✅ 批量智能合并完成!"
    echo ""
    echo "📊 合并状态:"
    git status --short
    echo ""
    echo "🔍 文件差异概览:"
    git diff --cached --stat 2>/dev/null || echo "(新文件无差异显示)"

else
    echo "❌ 批量合并过程中出现问题"
    merge_success=false
fi

if [ "$merge_success" = true ] && [ "$conflicts_found" = false ]; then
    echo ""
    echo "⏭️ 下一步操作："
    echo " 1. 检查合并结果: git diff --cached"
    echo " 2. 运行完整测试套件确保代码正常"
    echo " 3. 提交更改: git commit -m 'Batch merge for {assignee}: {len(assignee_groups)} groups, {len(all_files)} files'"
    echo " 4. 推送分支: git push origin {batch_branch_name}"
    echo ""
    echo "🔄 如需回滚: git reset --hard HEAD"

else
    echo ""
    echo "⏳ 需要处理冲突或错误后再继续"
    echo ""
    echo "📊 当前状态:"
    git status
    echo ""
    echo "🛠️ 后续步骤："
    echo " 1. 解决所有冲突和错误"
    echo " 2. 确认状态: git status"
    echo " 3. 运行测试验证"
    echo " 4. 提交: git commit -m 'Batch merge for {assignee} (resolved conflicts)'"
    echo " 5. 推送: git push origin {batch_branch_name}"
    echo ""
    echo "💡 提示: 如果冲突太多，建议拆分为更小的组单独处理"
fi
"""

        return script_content

    def merge_group(self, group_name, source_branch, target_branch, integration_branch):
        """合并指定组的文件"""
        plan = self.file_helper.load_plan()
        if not plan:
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return False

        # 找到对应组
        group_info = self.file_helper.find_group_by_name(plan, group_name)
        if not group_info:
            print(f"❌ 未找到组: {group_name}")
            return False

        assignee = group_info["assignee"]
        if not assignee:
            print(f"❌ 组 {group_name} 尚未分配负责人")
            return False

        print(f"🎯 准备合并组: {group_name}")
        print(f"👤 负责人: {assignee}")
        print(f"📁 文件数: {group_info.get('file_count', len(group_info['files']))}")

        # 创建合并分支
        branch_name = self.git_ops.create_merge_branch(group_name, assignee, integration_branch)

        # 生成改进的智能合并脚本
        script_content = self.generate_smart_merge_script(
            group_name, assignee, group_info["files"], branch_name, source_branch, target_branch
        )

        script_file = self.file_helper.create_script_file(
            f"merge_{group_name.replace('/', '_')}", script_content
        )

        print(f"✅ 已生成改进的智能合并脚本: {script_file}")
        print(f"🎯 请执行: ./{script_file}")
        print(f"💡 该脚本使用三路合并策略，会自动处理冲突并提供详细指导")

        return True

    def merge_assignee_tasks(self, assignee_name, source_branch, target_branch, integration_branch):
        """合并指定负责人的所有任务"""
        plan = self.file_helper.load_plan()
        if not plan:
            print("❌ 合并计划文件不存在，请先运行创建合并计划")
            return False

        # 找到负责人的所有任务
        assignee_groups = self.file_helper.get_assignee_groups(plan, assignee_name)
        if not assignee_groups:
            print(f"❌ 负责人 '{assignee_name}' 没有分配的任务")
            return False

        total_files = sum(g.get('file_count', len(g['files'])) for g in assignee_groups)
        print(f"🎯 开始批量合并负责人 '{assignee_name}' 的所有任务...")
        print(f"📋 共 {len(assignee_groups)} 个组，总计 {total_files} 个文件")

        # 收集所有文件
        all_files = []
        for group in assignee_groups:
            all_files.extend(group["files"])

        if not all_files:
            print("❌ 没有找到需要合并的文件")
            return False

        # 创建统一的合并分支
        batch_branch_name = self.git_ops.create_batch_merge_branch(assignee_name, integration_branch)

        # 生成改进的智能批量合并脚本
        script_content = self.generate_batch_merge_script(
            assignee_name, assignee_groups, all_files, batch_branch_name, source_branch, target_branch
        )

        script_file = self.file_helper.create_script_file(
            f"merge_batch_{assignee_name.replace(' ', '_')}", script_content
        )

        print(f"✅ 已生成改进的智能批量合并脚本: {script_file}")
        print(f"🎯 请执行: ./{script_file}")
        print(f"💡 该脚本使用三路合并策略，自动分类处理不同类型的文件变更")

        return True

    def finalize_merge(self, integration_branch):
        """完成最终合并"""
        print("🎯 开始最终合并...")

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
                # 检查分支是否存在
                if self.git_ops.get_branch_exists(branch_name):
                    completed_branches.append((branch_name, group))

        if not completed_branches:
            print("⚠️ 没有找到已完成的合并分支")
            return False

        print(f"🔍 发现 {len(completed_branches)} 个已完成的分支:")
        total_files = 0
        for branch_name, group in completed_branches:
            file_count = group.get('file_count', len(group['files']))
            total_files += file_count
            print(f" - {branch_name} ({file_count} 文件)")

        print(f"📊 总计将合并 {total_files} 个文件")

        # 合并所有完成的分支
        all_success = True
        for branch_name, group in completed_branches:
            print(f"🔄 正在合并分支: {branch_name}")
            success = self.git_ops.merge_branch_to_integration(branch_name, group['name'], integration_branch)
            if success:
                print(f" ✅ 成功合并 {branch_name}")
            else:
                print(f" ❌ 合并 {branch_name} 时出现问题")
                all_success = False

        if all_success:
            print("🎉 最终合并完成!")
            print(f"📋 集成分支 {integration_branch} 已包含所有更改")
            print(f"🚀 建议操作:")
            print(f" 1. 验证合并结果: git log --oneline -10")
            print(f" 2. 运行完整测试套件")
            print(f" 3. 推送到远程: git push origin {integration_branch}")
            print(f" 4. 创建PR/MR合并到 {plan['target_branch']}")

        return all_success
