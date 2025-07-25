"""
Git Merge Orchestrator - 合并执行器 (工作区优先版)
负责生成改进的合并脚本和执行合并操作
使用真正的三路合并策略，所有结果保留在工作区，便于VSCode手动检查
"""

from datetime import datetime


class MergeExecutor:
    """合并执行器 - 工作区优先策略版本"""

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
            source_modified = source_result is None  # None表示有差异（非零退出码）

            # 检查目标分支相对于merge-base是否有修改
            target_cmd = f'git diff --quiet {merge_base} {target_branch} -- "{file}"'
            target_result = self.git_ops.run_command_silent(target_cmd)
            target_modified = target_result is None  # None表示有差异（非零退出码）

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

        print(f"📊 文件修改分析结果:")
        print(f"  - 新增文件: {len(missing_files)} 个")
        print(f"  - 仅源分支修改: {len(modified_only_in_source)} 个")
        print(f"  - 两边都修改: {len(modified_in_both)} 个")
        print(f"  - 无变化: {len(no_changes)} 个")

        return analysis_result

    def _simple_file_analysis(self, files, source_branch, target_branch):
        """简化的文件分析策略（当无法确定merge-base时）"""
        existing_files, missing_files = self.git_ops.check_file_existence(
            files, target_branch
        )

        # 简化策略：假设所有已存在文件都可能有冲突
        return {
            "missing_files": missing_files,
            "modified_only_in_source": [],
            "modified_in_both": existing_files,  # 保守策略：都当作可能冲突处理
            "no_changes": [],
            "merge_base": None,
        }

    def generate_smart_merge_script(
        self, group_name, assignee, files, branch_name, source_branch, target_branch
    ):
        """生成工作区优先的智能合并脚本，使用真正的三路合并策略"""

        # 分析文件修改情况
        analysis = self.analyze_file_modifications(files, source_branch, target_branch)

        missing_files = analysis["missing_files"]
        modified_only_in_source = analysis["modified_only_in_source"]
        modified_in_both = analysis["modified_in_both"]
        no_changes = analysis["no_changes"]
        merge_base = analysis["merge_base"]

        # 生成工作区优先的处理脚本
        script_content = f"""#!/bin/bash
# 工作区优先智能合并脚本 - {group_name} (负责人: {assignee})
# 使用三路合并策略，所有结果保留在工作区，便于VSCode手动检查
# 文件数: {len(files)} (新增: {len(missing_files)}, 仅源修改: {len(modified_only_in_source)}, 两边修改: {len(modified_in_both)})
# 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

set -e # 遇到错误立即退出

echo "🚀 开始工作区优先智能合并组: {group_name}"
echo "👤 负责人: {assignee}"
echo "🌿 工作分支: {branch_name}"
echo "📁 总文件数: {len(files)}"
echo "📊 文件分类："
echo "  - 新增文件: {len(missing_files)} 个"
echo "  - 仅源分支修改: {len(modified_only_in_source)} 个"
echo "  - 两边都修改: {len(modified_in_both)} 个"
echo "  - 无变化: {len(no_changes)} 个"
echo ""
echo "💡 策略说明：所有修改保留在工作区，便于VSCode检查后手动添加"
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

echo "🔄 开始三路合并到工作区..."
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
# 从源分支复制文件内容到工作区
if git show {source_branch}:"{file}" > "{file}" 2>/dev/null; then
    echo "    ✅ 新文件 {file} 已写入工作区"
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
echo "  获取文件: {file} (仅源分支有修改，安全覆盖)"
if git show {source_branch}:"{file}" > "{file}" 2>/dev/null; then
    echo "    ✅ 文件 {file} 已更新到工作区"
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

# 使用三路合并但保持结果在工作区
if git checkout --merge {source_branch} -- "{file}" 2>/dev/null; then
    # 立即将文件从暂存区移到工作区
    git reset HEAD -- "{file}" 2>/dev/null || true

    # 检查是否有冲突标记
    if grep -q "<<<<<<< " "{file}" 2>/dev/null; then
        echo "    ⚠️ 文件 {file} 存在合并冲突，已在工作区标记"
        conflicts_found=true
        echo "    💡 冲突标记说明："
        echo "       <<<<<<< HEAD     (当前分支的内容)"
        echo "       =======          (分隔线)"
        echo "       >>>>>>> {source_branch}  (源分支的内容)"
        echo "    📝 请在VSCode中编辑解决冲突"
    else
        echo "    ✅ 文件 {file} 自动合并成功，已在工作区"
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
    echo "    📝 请参考这些文件在VSCode中手动合并"

    conflicts_found=true
fi
"""

        # 处理无变化的文件
        if no_changes:
            script_content += f"""
echo "📋 跳过无变化的文件 ({len(no_changes)}个)..."
"""
            for file in no_changes:
                script_content += f'echo "  跳过: {file} (两个分支中内容相同)"\n'

        # 添加最终处理逻辑 - 工作区优先
        script_content += f"""
echo ""

# 显示工作区状态
echo "📊 当前工作区状态："
git status --short

echo ""

if [ "$conflicts_found" = true ]; then
    echo "⚠️ 发现合并冲突或需要手动处理的文件"
    echo ""
    echo "🎯 VSCode工作流程："
    echo " 1. 打开VSCode: code ."
    echo " 2. 查看Source Control面板，检查Modified文件"
    echo " 3. 逐个文件检查差异，解决冲突标记 (<<<<<<< ======= >>>>>>>)"
    echo " 4. 对于有.base/.target/.source参考文件的，参考进行手动合并"
    echo " 5. 检查完毕后删除临时参考文件: rm *.base *.target *.source"
    echo ""
    echo "📝 分阶段添加建议："
    echo " - 先添加简单无冲突文件: git add <简单文件>"
    echo " - 再逐个添加已解决冲突的文件: git add <已解决文件>"
    echo " - 检查暂存区状态: git status"

elif [ "$merge_success" = true ]; then
    echo "✅ 智能三路合并完成! 所有文件已在工作区"
    echo ""
    echo "🎯 VSCode检查流程："
    echo " 1. 打开VSCode: code ."
    echo " 2. 在Source Control面板查看所有Modified文件"
    echo " 3. 逐个文件review差异，确认修改正确"
    echo " 4. 满意的文件点击+号添加到暂存区"
    echo " 5. 或者使用命令批量添加: git add <文件列表>"

else
    echo "❌ 合并过程中出现问题"
    merge_success=false
fi

if [ "$merge_success" = true ]; then
    echo ""
    echo "⏭️ 推荐后续操作："
    echo " 1. VSCode检查: code ."
    echo " 2. 检查差异: git diff"
    echo " 3. 分批添加: git add <文件1> <文件2> ..."
    echo " 4. 检查暂存: git status"
    echo " 5. 运行测试: npm test 或 python -m pytest 等"
    echo " 6. 提交更改: git commit -m 'Merge group: {group_name} ({len(files)} files)'"
    echo " 7. 推送分支: git push origin {branch_name}"
    echo ""
    echo "🔄 如需重置: git checkout -- <文件名> 或 git reset --hard HEAD"

else
    echo ""
    echo "⏳ 需要手动处理问题后再继续"
    echo ""
    echo "📊 当前状态:"
    git status
    echo ""
    echo "🔄 处理完问题后的步骤："
    echo " 1. 解决所有问题"
    echo " 2. VSCode检查: code ."
    echo " 3. 确认修改: git status"
    echo " 4. 分批添加: git add <files>"
    echo " 5. 运行测试验证"
    echo " 6. 提交: git commit -m 'Merge group: {group_name} (resolved issues)'"
    echo " 7. 推送: git push origin {branch_name}"
fi

echo ""
echo "💡 小贴士："
echo " - 使用 'git diff' 查看工作区所有变更"
echo " - 使用 'git diff <文件名>' 查看特定文件变更"
echo " - 在VSCode中可以使用GitLens扩展获得更好的diff体验"
"""

        return script_content

    def generate_batch_merge_script(
        self,
        assignee,
        assignee_groups,
        all_files,
        batch_branch_name,
        source_branch,
        target_branch,
    ):
        """生成工作区优先的批量合并脚本"""

        # 分析所有文件的修改情况
        print(f"🔍 正在分析负责人 '{assignee}' 的所有文件...")
        analysis = self.analyze_file_modifications(
            all_files, source_branch, target_branch
        )

        missing_files = analysis["missing_files"]
        modified_only_in_source = analysis["modified_only_in_source"]
        modified_in_both = analysis["modified_in_both"]
        no_changes = analysis["no_changes"]

        script_content = f"""#!/bin/bash
# 工作区优先批量智能合并脚本 - 负责人: {assignee}
# 使用三路合并策略，所有结果保留在工作区，便于VSCode批量检查
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
echo "💡 策略说明：所有修改保留在工作区，便于VSCode批量检查后分阶段添加"
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

echo "🔄 开始批量智能三路合并到工作区..."
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
    echo "    ✅ 新文件 {file} 已写入工作区"
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
echo "  获取文件: {file}"
if git show {source_branch}:"{file}" > "{file}" 2>/dev/null; then
    echo "    ✅ 文件 {file} 已更新到工作区"
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
    git reset HEAD -- "{file}" 2>/dev/null || true

    if grep -q "<<<<<<< " "{file}" 2>/dev/null; then
        echo "    ⚠️ 文件 {file} 存在合并冲突，已在工作区标记"
        conflicts_found=true
    else
        echo "    ✅ 文件 {file} 自动合并成功，已在工作区"
    fi
else
    echo "    ⚠️ 文件 {file} 需要手动处理，已在工作区"
    conflicts_found=true
fi
"""

        # 添加批量处理的最终逻辑 - 工作区优先
        script_content += f"""
echo ""

# 显示工作区状态
echo "📊 当前工作区状态："
git status --short

echo ""

if [ "$conflicts_found" = true ]; then
    echo "⚠️ 批量合并中发现冲突，所有结果已在工作区"
    echo ""
    echo "🎯 VSCode批量处理流程："
    echo " 1. 打开VSCode: code ."
    echo " 2. 在Source Control面板查看所有Modified文件"
    echo " 3. 按组分类处理（文件名前缀可以帮助识别组别）："
    for group in assignee_groups:
        echo " 4. 按组处理可以逐个检查，每处理完一组就添加该组的文件"
        echo " 5. 对于有冲突标记的文件，在VSCode中逐个解决"
    echo " 6. 分批添加已检查的文件: git add <组1的文件...>"
    echo " 7. 继续处理下一组，重复此流程"
    echo ""
    echo "💡 批量处理建议："
    echo " - 按组分批处理，每个组的文件通常相关性较强"
    echo " - 优先处理无冲突的文件，建立信心"
    echo " - 复杂冲突可以联系该组的其他开发者协助"
    echo " - 使用VSCode的diff视图逐个对比修改"

elif [ "$merge_success" = true ]; then
    echo "✅ 批量智能合并完成! 所有文件已在工作区"
    echo ""
    echo "🎯 VSCode批量检查流程："
    echo " 1. 打开VSCode: code ."
    echo " 2. 在Source Control面板查看所有 {len(all_files)} 个Modified文件"
    echo " 3. 建议按组分批检查和添加："
{chr(10).join([f'    echo "    - 组 {g["name"]}: {g.get("file_count", len(g["files"]))} 个文件"' for g in assignee_groups])}
    echo " 4. 每检查完一组，就添加该组: git add <该组文件列表>"
    echo " 5. 定期检查暂存状态: git status"

else
    echo "❌ 批量合并过程中出现问题"
    merge_success=false
fi

if [ "$merge_success" = true ]; then
    echo ""
    echo "⏭️ 推荐批量后续操作："
    echo " 1. VSCode检查: code ."
    echo " 2. 查看所有变更: git diff"
    echo " 3. 按组分批添加文件（建议每组单独添加便于回滚）"
    echo " 4. 例如: git add {' '.join(assignee_groups[0]['files'][:3]) if assignee_groups else 'file1 file2 ...'}"
    echo " 5. 检查暂存: git status"
    echo " 6. 运行测试: npm test 或 python -m pytest 等"
    echo " 7. 可以分批提交: git commit -m 'Merge group: <组名>'"
    echo " 8. 或者最后统一提交: git commit -m 'Batch merge for {assignee}: {len(assignee_groups)} groups'"
    echo " 9. 推送分支: git push origin {batch_branch_name}"
    echo ""
    echo "🔄 如需重置某个文件: git checkout -- <文件名>"
    echo "🔄 如需重置所有: git reset --hard HEAD"

else
    echo ""
    echo "⏳ 需要处理问题后再继续"
    echo ""
    echo "📊 当前状态:"
    git status
    echo ""
    echo "🛠️ 后续步骤："
    echo " 1. 解决所有问题"
    echo " 2. VSCode检查: code ."
    echo " 3. 确认修改: git status"
    echo " 4. 按组分批添加: git add <组文件>"
    echo " 5. 运行测试验证"
    echo " 6. 提交: git commit -m 'Batch merge for {assignee} (resolved issues)'"
    echo " 7. 推送: git push origin {batch_branch_name}"
    echo ""
    echo "💡 提示: 如果文件太多，建议拆分为更小的组单独处理"
fi

echo ""
echo "💡 批量处理小贴士："
echo " - 使用 'git diff --name-only' 查看所有变更文件列表"
echo " - 使用 'git diff <组的文件...>' 查看特定组的变更"
echo " - 在VSCode中可以在Source Control面板中按文件夹分组查看"
echo " - 建议开启VSCode的GitLens扩展获得更好的批量diff体验"
echo " - 分批提交可以让历史更清晰，便于回滚特定组的修改"
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
        branch_name = self.git_ops.create_merge_branch(
            group_name, assignee, integration_branch
        )

        # 生成工作区优先的智能合并脚本
        script_content = self.generate_smart_merge_script(
            group_name,
            assignee,
            group_info["files"],
            branch_name,
            source_branch,
            target_branch,
        )

        script_file = self.file_helper.create_script_file(
            f"merge_{group_name.replace('/', '_')}", script_content
        )

        print(f"✅ 已生成工作区优先的智能合并脚本: {script_file}")
        print(f"🎯 请执行: ./{script_file}")
        print(f"💡 该脚本使用三路合并策略，结果保留在工作区便于VSCode检查")
        print(f"📝 完成后在VSCode中检查差异，满意后手动添加到暂存区")

        return True

    def merge_assignee_tasks(
        self, assignee_name, source_branch, target_branch, integration_branch
    ):
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

        total_files = sum(g.get("file_count", len(g["files"])) for g in assignee_groups)
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
        batch_branch_name = self.git_ops.create_batch_merge_branch(
            assignee_name, integration_branch
        )

        # 生成工作区优先的智能批量合并脚本
        script_content = self.generate_batch_merge_script(
            assignee_name,
            assignee_groups,
            all_files,
            batch_branch_name,
            source_branch,
            target_branch,
        )

        script_file = self.file_helper.create_script_file(
            f"merge_batch_{assignee_name.replace(' ', '_')}", script_content
        )

        print(f"✅ 已生成工作区优先的智能批量合并脚本: {script_file}")
        print(f"🎯 请执行: ./{script_file}")
        print(f"💡 该脚本使用三路合并策略，所有结果保留在工作区")
        print(f"📝 建议在VSCode中按组分批检查和添加文件")
        print(f"🔄 可以分组提交，便于管理和回滚")

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
            print("🎉 最终合并完成!")
            print(f"📋 集成分支 {integration_branch} 已包含所有更改")
            print(f"🚀 建议操作:")
            print(f" 1. 验证合并结果: git log --oneline -10")
            print(f" 2. 运行完整测试套件")
            print(f" 3. 推送到远程: git push origin {integration_branch}")
            print(f" 4. 创建PR/MR合并到 {plan['target_branch']}")

        return all_success
