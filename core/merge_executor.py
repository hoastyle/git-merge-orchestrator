"""
Git Merge Orchestrator - 修复后的合并执行器
使用真正的三路合并策略，产生标准冲突标记
"""

from datetime import datetime


class MergeExecutor:
    """修复后的合并执行器 - 真正三路合并版本"""

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
        print(f"  - 两边都修改(需要三路合并): {len(modified_in_both)} 个")
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

    def generate_true_three_way_merge_script(
        self, group_name, assignee, files, branch_name, source_branch, target_branch
    ):
        """生成真正的三路合并脚本，产生标准冲突标记"""

        # 分析文件修改情况
        analysis = self.analyze_file_modifications(files, source_branch, target_branch)

        missing_files = analysis["missing_files"]
        modified_only_in_source = analysis["modified_only_in_source"]
        modified_in_both = analysis["modified_in_both"]
        no_changes = analysis["no_changes"]
        merge_base = analysis["merge_base"]

        # 生成真正三路合并脚本
        script_content = f"""#!/bin/bash
# 真正三路合并脚本 - {group_name} (负责人: {assignee})
# 使用标准Git三路合并，产生标准冲突标记 <<<<<<< ======= >>>>>>>
# 文件数: {len(files)} (新增: {len(missing_files)}, 仅源修改: {len(modified_only_in_source)}, 需三路合并: {len(modified_in_both)})
# 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

set -e # 遇到错误立即退出

echo "🚀 开始真正三路合并组: {group_name}"
echo "👤 负责人: {assignee}"
echo "🌿 工作分支: {branch_name}"
echo "📁 总文件数: {len(files)}"
echo "📊 文件分类："
echo "  - 新增文件: {len(missing_files)} 个 (直接复制)"
echo "  - 仅源分支修改: {len(modified_only_in_source)} 个 (安全覆盖)"
echo "  - 需要三路合并: {len(modified_in_both)} 个 (使用git merge-file)"
echo "  - 无变化: {len(no_changes)} 个 (跳过)"
echo ""
echo "💡 重要说明：三路合并将产生标准冲突标记"
echo "   <<<<<<< HEAD       (当前分支内容)"
echo "   ======="
echo "   >>>>>>> {source_branch}  (源分支内容)"
echo ""

# 切换到工作分支
echo "📋 切换到工作分支..."
git checkout {branch_name}

# 获取merge-base
MERGE_BASE=$(git merge-base {source_branch} {target_branch} 2>/dev/null || echo "")
if [ -n "$MERGE_BASE" ]; then
    echo "🔍 找到分叉点: $MERGE_BASE"
else
    echo "⚠️ 无法确定分叉点，将使用两路合并策略"
    MERGE_BASE=""
fi
echo ""

merge_success=true
conflicts_found=false
total_processed=0

echo "🔄 开始标准三路合并处理..."
"""

        # 处理新增文件
        if missing_files:
            script_content += f"""
echo "🆕 处理新增文件 ({len(missing_files)}个) - 直接复制..."
"""
            for file in missing_files:
                script_content += f"""
echo "  [新增] {file}"
# 创建目录结构
mkdir -p "$(dirname "{file}")"
# 从源分支复制文件内容
if git show {source_branch}:"{file}" > "{file}" 2>/dev/null; then
    echo "    ✅ 新文件已复制到工作区"
    total_processed=$((total_processed + 1))
else
    echo "    ❌ 无法从源分支获取文件: {file}"
    merge_success=false
fi
"""

        # 处理仅源分支修改的文件
        if modified_only_in_source:
            script_content += f"""
echo ""
echo "📝 处理仅源分支修改的文件 ({len(modified_only_in_source)}个) - 安全覆盖..."
"""
            for file in modified_only_in_source:
                script_content += f"""
echo "  [覆盖] {file}"
if git show {source_branch}:"{file}" > "{file}" 2>/dev/null; then
    echo "    ✅ 文件已更新（目标分支无修改，安全覆盖）"
    total_processed=$((total_processed + 1))
else
    echo "    ❌ 无法从源分支获取文件: {file}"
    merge_success=false
fi
"""

        # 处理两边都修改的文件 - 真正的三路合并
        if modified_in_both:
            script_content += f"""
echo ""
echo "⚡ 处理需要三路合并的文件 ({len(modified_in_both)}个) - 产生标准冲突标记..."
"""
            for file in modified_in_both:
                script_content += f"""
echo "  [三路合并] {file}"

# 创建临时目录用于三路合并
TEMP_DIR=$(mktemp -d)
BASE_FILE="$TEMP_DIR/base"
CURRENT_FILE="$TEMP_DIR/current"
SOURCE_FILE="$TEMP_DIR/source"

# 获取三个版本的文件内容
if [ -n "$MERGE_BASE" ]; then
    # 有merge-base，使用真正的三路合并
    git show $MERGE_BASE:"{file}" > "$BASE_FILE" 2>/dev/null || echo "" > "$BASE_FILE"
    git show {target_branch}:"{file}" > "$CURRENT_FILE" 2>/dev/null || cp "{file}" "$CURRENT_FILE"
    git show {source_branch}:"{file}" > "$SOURCE_FILE" 2>/dev/null || echo "" > "$SOURCE_FILE"

    # 备份当前文件
    cp "{file}" "{file}.backup" 2>/dev/null || true

    # 使用git merge-file进行三路合并，设置正确的标签
    if git merge-file -L "HEAD" -L "merge-base" -L "{source_branch}" --marker-size=7 "$CURRENT_FILE" "$BASE_FILE" "$SOURCE_FILE" 2>/dev/null; then
        # 无冲突，直接复制结果
        cp "$CURRENT_FILE" "{file}"
        echo "    ✅ 三路合并成功，无冲突"
        total_processed=$((total_processed + 1))
    else
        # 有冲突，复制包含冲突标记的结果
        cp "$CURRENT_FILE" "{file}"
        echo "    ⚠️ 三路合并产生冲突，已标记在文件中"
        echo "    💡 冲突标记格式："
        echo "       <<<<<<< HEAD"
        echo "       当前分支的内容"
        echo "       ======="
        echo "       源分支的内容"
        echo "       >>>>>>> {source_branch}"
        conflicts_found=true
        total_processed=$((total_processed + 1))
    fi
else
    # 没有merge-base，使用两路合并
    echo "    ⚠️ 无分叉点，使用两路合并策略"

    # 创建包含冲突标记的合并结果，使用正确的分支标签
    echo "<<<<<<< HEAD" > "{file}.tmp"
    git show {target_branch}:"{file}" >> "{file}.tmp" 2>/dev/null || cat "{file}" >> "{file}.tmp"
    echo "=======" >> "{file}.tmp"
    git show {source_branch}:"{file}" >> "{file}.tmp" 2>/dev/null || echo "# 源分支版本获取失败" >> "{file}.tmp"
    echo ">>>>>>> {source_branch}" >> "{file}.tmp"

    mv "{file}.tmp" "{file}"
    echo "    ⚠️ 已创建手动合并模板（包含冲突标记）"
    conflicts_found=true
    total_processed=$((total_processed + 1))
fi

# 清理临时文件
rm -rf "$TEMP_DIR"
"""

        # 处理无变化的文件
        if no_changes:
            script_content += f"""
echo ""
echo "📋 跳过无变化的文件 ({len(no_changes)}个)..."
"""
            for file in no_changes:
                script_content += f'echo "  [跳过] {file} (两个分支中内容相同)"\n'

        # 添加最终处理逻辑
        script_content += f"""
echo ""
echo "📊 处理完成统计："
echo "  - 已处理文件: $total_processed 个"
echo "  - 总目标文件: {len(files)} 个"

# 显示当前工作区状态
echo ""
echo "📋 当前工作区状态："
git status --short

echo ""

if [ "$conflicts_found" = true ]; then
    echo "⚠️ 发现需要手动解决的冲突"
    echo ""
    echo "🎯 标准冲突解决流程："
    echo " 1. 打开VSCode: code ."
    echo " 2. 在Source Control面板查看Modified文件"
    echo " 3. 对于包含冲突标记的文件："
    echo "    - 查找 <<<<<<< HEAD 标记"
    echo "    - HEAD后面是当前分支({target_branch})的内容"
    echo "    - ======= 是分隔线"
    echo "    - >>>>>>> {source_branch} 前面是源分支的内容"
    echo " 4. 手动编辑，删除冲突标记，保留最终想要的内容"
    echo " 5. 保存文件后，在VSCode中点击+号添加到暂存区"
    echo ""
    echo "💡 VSCode冲突解决技巧："
    echo " - 使用内置的merge editor获得更好体验"
    echo " - 可以点击 'Accept Current Change' 或 'Accept Incoming Change'"
    echo " - 也可以点击 'Accept Both Changes' 然后手动调整"
    echo " - 推荐安装 GitLens 扩展增强Git功能"

elif [ "$merge_success" = true ]; then
    echo "✅ 智能三路合并完成! 所有文件均无冲突"
    echo ""
    echo "🎯 后续验证流程："
    echo " 1. 打开VSCode检查修改: code ."
    echo " 2. 在Source Control面板review所有变更"
    echo " 3. 运行测试验证合并结果: npm test 或 python -m pytest"
    echo " 4. 如果测试通过，批量添加文件: git add ."
    echo " 5. 或者选择性添加: git add <file1> <file2> ..."

else
    echo "❌ 合并过程中出现严重错误"
    merge_success=false
fi

if [ "$merge_success" = true ]; then
    echo ""
    echo "⏭️ 推荐后续操作："
    echo " 1. VSCode检查: code ."
    echo " 2. 查看所有差异: git diff"
    echo " 3. 运行完整测试套件"
    echo " 4. 添加已验证文件: git add <files...>"
    echo " 5. 检查暂存状态: git status"
    echo " 6. 提交更改: git commit -m 'Merge group: {group_name} ({len(files)} files) - resolved conflicts'"
    echo " 7. 推送分支: git push origin {branch_name}"
    echo ""
    echo "🔄 如需回滚某个文件: git checkout -- <文件名>"
    echo "🔄 如需完全重置: git reset --hard HEAD"

else
    echo ""
    echo "🛠️ 问题排查指南："
    echo " 1. 检查Git仓库状态: git status"
    echo " 2. 检查分支是否存在: git branch -a"
    echo " 3. 检查网络连接和权限"
    echo " 4. 如需重新开始: git reset --hard HEAD && git clean -fd"
    echo ""
    echo "📞 如遇到复杂问题，建议："
    echo " - 联系该组其他开发成员协助"
    echo " - 在团队群中分享具体错误信息"
    echo " - 考虑将大组拆分为更小的子组处理"
    exit 1
fi

echo ""
echo "💡 三路合并说明："
echo " - 这是Git的标准合并策略，最安全可靠"
echo " - 冲突标记是正常现象，表示两个分支对同一处做了不同修改"
echo " - 手动解决冲突后的代码质量通常比自动合并更高"
echo " - 解决冲突时要理解业务逻辑，不只是简单选择一边"
"""

        return script_content

    def generate_batch_true_merge_script(
        self,
        assignee,
        assignee_groups,
        all_files,
        batch_branch_name,
        source_branch,
        target_branch,
    ):
        """生成真正的批量三路合并脚本"""

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
# 真正三路合并批量脚本 - 负责人: {assignee}
# 使用标准Git三路合并，产生标准冲突标记
# 组数: {len(assignee_groups)} (文件总数: {len(all_files)})
# 文件分类: 新增{len(missing_files)}, 仅源修改{len(modified_only_in_source)}, 需三路合并{len(modified_in_both)}
# 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

set -e # 遇到错误立即退出

echo "🚀 开始批量真正三路合并负责人 '{assignee}' 的所有任务"
echo "🌿 工作分支: {batch_branch_name}"
echo "📁 总文件数: {len(all_files)}"
echo "📊 文件分类："
echo "  - 新增文件: {len(missing_files)} 个 (直接复制)"
echo "  - 仅源分支修改: {len(modified_only_in_source)} 个 (安全覆盖)"
echo "  - 需要三路合并: {len(modified_in_both)} 个 (使用git merge-file)"
echo "  - 无变化: {len(no_changes)} 个 (跳过)"
echo "📋 包含组: {', '.join([g['name'] for g in assignee_groups])}"
echo ""
echo "💡 重要说明：对于冲突文件将产生标准冲突标记"
echo "   <<<<<<< HEAD       (当前分支内容)"
echo "   ======="
echo "   >>>>>>> {source_branch}  (源分支内容)"
echo ""

# 切换到工作分支
echo "📋 切换到工作分支..."
git checkout {batch_branch_name}

# 获取merge-base
MERGE_BASE=$(git merge-base {source_branch} {target_branch} 2>/dev/null || echo "")
if [ -n "$MERGE_BASE" ]; then
    echo "🔍 找到分叉点: $MERGE_BASE"
else
    echo "⚠️ 无法确定分叉点，将对冲突文件使用两路合并"
fi

echo "📄 组别详情:"
{chr(10).join([f'echo "  组 {g["name"]}: {g.get("file_count", len(g["files"]))} 个文件"' for g in assignee_groups])}
echo ""

merge_success=true
conflicts_found=false
total_processed=0
conflict_files=()

echo "🔄 开始批量标准三路合并..."
"""

        # 处理新增文件
        if missing_files:
            script_content += f"""
echo "🆕 批量处理新增文件 ({len(missing_files)}个)..."
"""
            for file in missing_files:
                script_content += f"""
echo "  [新增] {file}"
mkdir -p "$(dirname "{file}")"
if git show {source_branch}:"{file}" > "{file}" 2>/dev/null; then
    echo "    ✅ 新文件已复制"
    total_processed=$((total_processed + 1))
else
    echo "    ❌ 复制失败: {file}"
    merge_success=false
fi
"""

        # 处理仅源分支修改的文件
        if modified_only_in_source:
            script_content += f"""
echo ""
echo "📝 批量处理仅源分支修改的文件 ({len(modified_only_in_source)}个)..."
"""
            for file in modified_only_in_source:
                script_content += f"""
echo "  [覆盖] {file}"
if git show {source_branch}:"{file}" > "{file}" 2>/dev/null; then
    echo "    ✅ 安全覆盖完成"
    total_processed=$((total_processed + 1))
else
    echo "    ❌ 覆盖失败: {file}"
    merge_success=false
fi
"""

        # 处理两边都修改的文件 - 批量三路合并
        if modified_in_both:
            script_content += f"""
echo ""
echo "⚡ 批量处理需要三路合并的文件 ({len(modified_in_both)}个)..."
"""
            for file in modified_in_both:
                script_content += f"""
echo "  [三路合并] {file}"

TEMP_DIR=$(mktemp -d)
BASE_FILE="$TEMP_DIR/base"
CURRENT_FILE="$TEMP_DIR/current"
SOURCE_FILE="$TEMP_DIR/source"

if [ -n "$MERGE_BASE" ]; then
    git show $MERGE_BASE:"{file}" > "$BASE_FILE" 2>/dev/null || echo "" > "$BASE_FILE"
    git show {target_branch}:"{file}" > "$CURRENT_FILE" 2>/dev/null || cp "{file}" "$CURRENT_FILE"
    git show {source_branch}:"{file}" > "$SOURCE_FILE" 2>/dev/null || echo "" > "$SOURCE_FILE"

    if git merge-file -L "HEAD" -L "merge-base" -L "{source_branch}" --marker-size=7 "$CURRENT_FILE" "$BASE_FILE" "$SOURCE_FILE" 2>/dev/null; then
        cp "$CURRENT_FILE" "{file}"
        echo "    ✅ 三路合并成功"
        total_processed=$((total_processed + 1))
    else
        cp "$CURRENT_FILE" "{file}"
        echo "    ⚠️ 发现冲突，已标记"
        conflicts_found=true
        conflict_files+=("{file}")
        total_processed=$((total_processed + 1))
    fi
else
    echo "<<<<<<< HEAD" > "{file}.tmp"
    git show {target_branch}:"{file}" >> "{file}.tmp" 2>/dev/null || cat "{file}" >> "{file}.tmp"
    echo "=======" >> "{file}.tmp"
    git show {source_branch}:"{file}" >> "{file}.tmp" 2>/dev/null || echo "# 源分支版本获取失败" >> "{file}.tmp"
    echo ">>>>>>> {source_branch}" >> "{file}.tmp"

    mv "{file}.tmp" "{file}"
    echo "    ⚠️ 创建冲突标记"
    conflicts_found=true
    conflict_files+=("{file}")
    total_processed=$((total_processed + 1))
fi

rm -rf "$TEMP_DIR"
"""

        # 添加批量处理的最终逻辑
        script_content += f"""
echo ""
echo "📊 批量处理完成统计："
echo "  - 已处理文件: $total_processed 个"
echo "  - 总目标文件: {len(all_files)} 个"
echo "  - 冲突文件数: ${{#conflict_files[@]}} 个"

if [ "${{#conflict_files[@]}}" -gt 0 ]; then
    echo ""
    echo "⚠️ 以下文件包含冲突标记，需要手动解决："
    for file in "${{conflict_files[@]}}"; do
        echo "  - $file"
    done
fi

echo ""
git status --short

echo ""

if [ "$conflicts_found" = true ]; then
    echo "⚠️ 批量合并中发现 ${{#conflict_files[@]}} 个冲突文件"
    echo ""
    echo "🎯 批量冲突解决策略："
    echo " 1. 打开VSCode: code ."
    echo " 2. 在Source Control面板查看所有Modified文件"
    echo " 3. 优先处理无冲突文件（没有 <<<<<<< 标记的）"
    echo " 4. 将无冲突文件分批添加到暂存区: git add <无冲突文件...>"
    echo " 5. 逐个处理冲突文件："
    echo "    - 搜索 <<<<<<< HEAD 找到冲突位置"
    echo "    - 理解 ======= 上下两部分的区别"
    echo "    - 手动编辑保留正确内容，删除冲突标记"
    echo "    - 处理完一个文件就添加: git add <已解决文件>"
    echo " 6. 所有文件处理完后提交"
    echo ""
    echo "💡 批量处理建议："
    echo " - 按组分批处理，每个组的文件相关性较强"
    echo " - 复杂冲突可以创建issue联系原作者"
    echo " - 可以分多次提交，每解决一组就提交一次"

elif [ "$merge_success" = true ]; then
    echo "✅ 批量三路合并完成! 所有 {len(all_files)} 个文件均无冲突"
    echo ""
    echo "🎯 批量验证流程："
    echo " 1. 打开VSCode检查: code ."
    echo " 2. 在Source Control面板review所有变更"
    echo " 3. 按组检查修改内容（建议按以下顺序）："
{chr(10).join([f'    echo "    - 组 {g["name"]}: {g.get("file_count", len(g["files"]))} 个文件"' for g in assignee_groups])}
    echo " 4. 运行完整测试套件验证合并结果"
    echo " 5. 如果测试通过，可以批量添加: git add ."
    echo " 6. 或者按组分批添加便于管理"

else
    echo "❌ 批量合并过程中出现严重错误"
    merge_success=false
fi

if [ "$merge_success" = true ]; then
    echo ""
    echo "⏭️ 推荐批量后续操作："
    echo " 1. VSCode全面检查: code ."
    echo " 2. 查看全部差异: git diff"
    echo " 3. 运行完整测试: npm test 或 python -m pytest"
    echo " 4. 选择添加策略："
    echo "    a) 按组分批添加: git add <组1文件...> (推荐)"
    echo "    b) 全部添加: git add . (需要确保所有修改都正确)"
    echo " 5. 检查暂存状态: git status"
    echo " 6. 提交选择："
    echo "    a) 分组提交: git commit -m 'Merge group: <组名>'"
    echo "    b) 统一提交: git commit -m 'Batch merge for {assignee}: {len(assignee_groups)} groups, {len(all_files)} files'"
    echo " 7. 推送分支: git push origin {batch_branch_name}"
    echo ""
    echo "🔄 回滚选项："
    echo " - 回滚单个文件: git checkout -- <文件名>"
    echo " - 完全重置: git reset --hard HEAD"

else
    echo ""
    echo "🛠️ 批量处理问题排查："
    echo " 1. 检查文件权限和磁盘空间"
    echo " 2. 验证分支完整性: git fsck"
    echo " 3. 检查网络连接状态"
    echo " 4. 考虑分批处理减少复杂度"
    echo ""
    echo "📞 建议求助方式："
    echo " - 在团队群中分享错误日志"
    echo " - 联系熟悉相关代码的团队成员"
    echo " - 考虑将大批量拆分为多个小组单独处理"
    exit 1
fi

echo ""
echo "💡 批量三路合并最佳实践："
echo " - 分批验证比一次性处理更安全"
echo " - 冲突解决要理解业务逻辑，不只是技术层面"
echo " - 保持与原代码作者的沟通，特别是复杂冲突"
echo " - 详细测试合并结果，确保功能完整性"
echo " - 考虑在合并后创建临时分支备份"
"""

        return script_content

    def merge_group(self, group_name, source_branch, target_branch, integration_branch):
        """合并指定组的文件 - 使用真正三路合并"""
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

        print(f"🎯 准备使用真正三路合并处理组: {group_name}")
        print(f"👤 负责人: {assignee}")
        print(f"📁 文件数: {group_info.get('file_count', len(group_info['files']))}")

        # 创建合并分支
        branch_name = self.git_ops.create_merge_branch(
            group_name, assignee, integration_branch
        )

        # 生成真正的三路合并脚本
        script_content = self.generate_true_three_way_merge_script(
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

        print(f"✅ 已生成真正三路合并脚本: {script_file}")
        print(f"🎯 请执行: ./{script_file}")
        print(f"💡 该脚本使用Git标准三路合并策略")
        print(f"⚠️ 冲突文件将包含标准冲突标记 <<<<<<< ======= >>>>>>>")
        print(f"📝 请在VSCode中检查和解决冲突后手动提交")

        return True

    def merge_assignee_tasks(
        self, assignee_name, source_branch, target_branch, integration_branch
    ):
        """批量合并指定负责人的所有任务 - 使用真正三路合并"""
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
        print(f"🎯 开始批量真正三路合并负责人 '{assignee_name}' 的所有任务...")
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

        # 生成真正的批量三路合并脚本
        script_content = self.generate_batch_true_merge_script(
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

        print(f"✅ 已生成真正的批量三路合并脚本: {script_file}")
        print(f"🎯 请执行: ./{script_file}")
        print(f"💡 该脚本使用Git标准三路合并策略")
        print(f"⚠️ 冲突文件将包含标准冲突标记 <<<<<<< ======= >>>>>>>")
        print(f"📝 建议在VSCode中按组分批检查和解决冲突")
        print(f"🔄 可以分组提交，便于管理和问题回滚")

        return True

    def finalize_merge(self, integration_branch):
        """完成最终合并 - 保持不变"""
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
