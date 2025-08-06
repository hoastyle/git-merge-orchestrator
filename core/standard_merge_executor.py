from .base_merge_executor import BaseMergeExecutor, MergeStrategy


class StandardMergeExecutor(BaseMergeExecutor):
    """Standard合并执行器 - 三路合并策略"""

    def __init__(self, git_ops, file_helper):
        super().__init__(git_ops, file_helper, MergeStrategy.STANDARD)

    def get_strategy_name(self):
        return "Standard"

    def get_strategy_description(self):
        return "标准Git三路合并，产生冲突标记 <<<<<<< ======= >>>>>>>"

    def generate_merge_script(
        self, group_name, assignee, files, branch_name, source_branch, target_branch
    ):
        """生成Standard合并脚本"""
        analysis = self.analyze_file_modifications(files, source_branch, target_branch)

        script_content = self._generate_common_script_header(
            group_name, assignee, files, branch_name
        )

        script_content += self._generate_merge_base_section(
            source_branch, target_branch
        )

        script_content += f"""
merge_success=true
conflicts_found=false
total_processed=0
conflict_files=()

echo "🔄 开始Standard三路合并处理..."
echo "💡 重要说明：三路合并将产生标准冲突标记"
echo "   <<<<<<< HEAD       (当前分支内容)"
echo "   ======="
echo "   >>>>>>> {source_branch}  (源分支内容)"
echo ""
"""

        script_content += self._generate_common_file_processing_sections(
            analysis, source_branch
        )
        script_content += self._generate_strategy_specific_merge_logic(
            analysis, source_branch, target_branch
        )

        # Standard特定的冲突处理说明
        script_content += """
echo ""
if [ "$conflicts_found" = true ]; then
    echo "⚠️ 发现需要手动解决的冲突"
    echo ""
    echo "🎯 标准冲突解决流程："
    echo " 1. 打开VSCode: code ."
    echo " 2. 在Source Control面板查看Modified文件"
    echo " 3. 对于包含冲突标记的文件："
    echo "    - 查找 <<<<<<< HEAD 标记"
    echo "    - HEAD后面是当前分支的内容"
    echo "    - ======= 是分隔线"
    echo "    - >>>>>>> 前面是源分支的内容"
    echo " 4. 手动编辑，删除冲突标记，保留最终想要的内容"
    echo " 5. 保存文件后，在VSCode中点击+号添加到暂存区"
    echo ""
    echo "💡 VSCode冲突解决技巧："
    echo " - 使用内置的merge editor获得更好体验"
    echo " - 可以点击 'Accept Current Change' 或 'Accept Incoming Change'"
    echo " - 也可以点击 'Accept Both Changes' 然后手动调整"
elif [ "$merge_success" = true ]; then
    echo "✅ Standard三路合并完成! 所有文件均无冲突"
    echo ""
    echo "🎯 后续验证流程："
    echo " 1. 打开VSCode检查修改: code ."
    echo " 2. 在Source Control面板review所有变更"
    echo " 3. 运行测试验证合并结果"
    echo " 4. 如果测试通过，批量添加文件: git add ."
else
    echo "❌ 合并过程中出现严重错误"
    merge_success=false
fi
"""

        script_content += self._generate_common_script_footer(
            group_name, len(files), branch_name
        )

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
        """生成Standard批量合并脚本"""
        analysis = self.analyze_file_modifications(
            all_files, source_branch, target_branch
        )

        script_content = self._generate_common_script_header(
            f"batch-{assignee}", assignee, all_files, batch_branch_name, "批量"
        )

        script_content += self._generate_merge_base_section(
            source_branch, target_branch
        )

        script_content += f"""
echo "📄 组别详情:"
{chr(10).join([f'echo "  组 {g["name"]}: {g.get("file_count", len(g["files"]))} 个文件"' for g in assignee_groups])}
echo ""

merge_success=true
conflicts_found=false
total_processed=0
conflict_files=()

echo "🔄 开始Standard批量三路合并..."
echo "💡 重要说明：对于冲突文件将产生标准冲突标记"
echo "   <<<<<<< HEAD       (当前分支内容)"
echo "   ======="
echo "   >>>>>>> {source_branch}  (源分支内容)"
echo ""
"""

        script_content += self._generate_common_file_processing_sections(
            analysis, source_branch
        )
        script_content += self._generate_strategy_specific_merge_logic(
            analysis, source_branch, target_branch
        )

        # Standard批量特定的冲突处理说明
        script_content += """
echo ""
if [ "${#conflict_files[@]}" -gt 0 ]; then
    echo "⚠️ 以下文件包含冲突标记，需要手动解决："
    for file in "${conflict_files[@]}"; do
        echo "  - $file"
    done
fi

echo ""

if [ "$conflicts_found" = true ]; then
    echo "⚠️ Standard批量合并中发现冲突文件"
    echo ""
    echo "🎯 批量冲突解决策略："
    echo " 1. 打开VSCode: code ."
    echo " 2. 在Source Control面板查看所有Modified文件"
    echo " 3. 优先处理无冲突文件（没有 <<<<<<< 标记的）"
    echo " 4. 将无冲突文件分批添加到暂存区"
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
    echo "✅ Standard批量三路合并完成! 所有文件均无冲突"
    echo ""
    echo "🎯 批量验证流程："
    echo " 1. 打开VSCode检查: code ."
    echo " 2. 在Source Control面板review所有变更"
    echo " 3. 按组检查修改内容"
    echo " 4. 运行完整测试套件验证合并结果"
    echo " 5. 如果测试通过，可以批量添加: git add ."
    echo " 6. 或者按组分批添加便于管理"
else
    echo "❌ 批量合并过程中出现严重错误"
    merge_success=false
fi
"""

        script_content += self._generate_common_batch_script_footer(
            assignee, len(assignee_groups), len(all_files), batch_branch_name
        )

        return script_content

    def _generate_strategy_specific_merge_logic(
        self, analysis, source_branch, target_branch
    ):
        """生成Standard特定的合并逻辑 - 真正的三路合并"""
        modified_in_both = analysis["modified_in_both"]

        if not modified_in_both:
            return ""

        script_logic = f"""
echo ""
echo "⚡ 处理需要三路合并的文件 ({len(modified_in_both)}个) - 产生标准冲突标记..."
"""

        for file in modified_in_both:
            script_logic += f"""
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
        conflict_files+=("{file}")
        total_processed=$((total_processed + 1))
    fi
else
    # 没有merge-base，使用两路合并，创建标准冲突标记
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
    conflict_files+=("{file}")
    total_processed=$((total_processed + 1))
fi

# 清理临时文件
rm -rf "$TEMP_DIR"
"""

        return script_logic

    def _print_analysis_result(self, analysis_result):
        """Standard特定的分析结果显示"""
        super()._print_analysis_result(analysis_result)
        modified_in_both = analysis_result["modified_in_both"]
        if modified_in_both:
            print(f"  💡 其中 {len(modified_in_both)} 个文件需要三路合并，可能产生冲突标记")

    def _print_script_completion_message(self, script_file):
        """Standard特定的完成消息"""
        super()._print_script_completion_message(script_file)
        print(f"💡 Standard模式: 使用Git标准三路合并策略")
        print(f"⚠️ 冲突文件将包含标准冲突标记 <<<<<<< ======= >>>>>>>")
        print(f"📝 请在VSCode中检查和解决冲突后手动提交")
        print(f"🛡️ 优势: 安全可靠，保留完整的合并历史")

    def _print_batch_script_completion_message(self, script_file):
        """Standard特定的批量完成消息"""
        super()._print_batch_script_completion_message(script_file)
        print(f"💡 Standard批量模式: 使用Git标准三路合并策略")
        print(f"⚠️ 冲突文件将包含标准冲突标记 <<<<<<< ======= >>>>>>>")
        print(f"📝 建议在VSCode中按组分批检查和解决冲突")
        print(f"🔄 可以分组提交，便于管理和问题回滚")

    def _get_strategy_footer_notes(self):
        """Standard策略特定的脚本结尾说明"""
        return """echo " - 这是Git的标准合并策略，最安全可靠"
echo " - 冲突标记是正常现象，表示两个分支对同一处做了不同修改"
echo " - 手动解决冲突后的代码质量通常比自动合并更高"
echo " - 解决冲突时要理解业务逻辑，不只是简单选择一边"
"""

    def _get_batch_strategy_footer_notes(self):
        """Standard批量策略特定的脚本结尾说明"""
        return """echo " - 分批验证比一次性处理更安全"
echo " - 冲突解决要理解业务逻辑，不只是技术层面"
echo " - 保持与原代码作者的沟通，特别是复杂冲突"
echo " - 详细测试合并结果，确保功能完整性"
echo " - 考虑在合并后创建临时分支备份"
"""

    # === 文件级合并方法实现 ===

    def generate_file_merge_script(
        self, file_info, branch_name, source_branch, target_branch
    ):
        """生成单个文件的Standard合并脚本"""
        file_path = file_info["path"]
        assignee = file_info.get("assignee", "未分配")

        analysis = self.analyze_file_modifications(
            [file_path], source_branch, target_branch
        )

        script_content = f"""#!/bin/bash
# Git Merge Orchestrator - 文件级Standard合并脚本
# 生成时间: {self._get_current_time()}
#
# 文件: {file_path}
# 负责人: {assignee}
# 分支: {branch_name}
# 策略: Standard (三路合并)

set -e  # 遇到错误立即退出

echo "🚀 开始文件级Standard合并处理"
echo "📄 目标文件: {file_path}"
echo "👤 负责人: {assignee}"
echo "🌿 工作分支: {branch_name}"
echo "💡 策略: Standard三路合并"
echo ""

"""

        script_content += self._generate_merge_base_section(
            source_branch, target_branch
        )

        script_content += f"""
merge_success=true
conflicts_found=false

echo "🔄 开始Standard三路合并处理..."
echo "💡 重要说明：三路合并将产生标准冲突标记"
echo "   <<<<<<< HEAD       (当前分支内容)"
echo "   ======="
echo "   >>>>>>> {source_branch}  (源分支内容)"
echo ""

"""

        # 文件特定的合并逻辑
        if file_path in analysis["modified_in_both"]:
            script_content += f"""
echo "⚡ 处理需要三路合并的文件: {file_path}"

# 创建临时目录用于三路合并
TEMP_DIR=$(mktemp -d)
BASE_FILE="$TEMP_DIR/base"
CURRENT_FILE="$TEMP_DIR/current"
SOURCE_FILE="$TEMP_DIR/source"

# 获取三个版本的文件内容
if [ -n "$MERGE_BASE" ]; then
    # 有merge-base，使用真正的三路合并
    git show $MERGE_BASE:"{file_path}" > "$BASE_FILE" 2>/dev/null || echo "" > "$BASE_FILE"
    git show {target_branch}:"{file_path}" > "$CURRENT_FILE" 2>/dev/null || cp "{file_path}" "$CURRENT_FILE"
    git show {source_branch}:"{file_path}" > "$SOURCE_FILE" 2>/dev/null || echo "" > "$SOURCE_FILE"

    # 备份当前文件
    cp "{file_path}" "{file_path}.backup" 2>/dev/null || true

    # 使用git merge-file进行三路合并
    if git merge-file -L "HEAD" -L "merge-base" -L "{source_branch}" --marker-size=7 "$CURRENT_FILE" "$BASE_FILE" "$SOURCE_FILE" 2>/dev/null; then
        # 无冲突，直接复制结果
        cp "$CURRENT_FILE" "{file_path}"
        echo "    ✅ 三路合并成功，无冲突"
    else
        # 有冲突，复制包含冲突标记的结果
        cp "$CURRENT_FILE" "{file_path}"
        echo "    ⚠️ 三路合并产生冲突，已标记在文件中"
        conflicts_found=true
    fi
else
    # 没有merge-base，使用两路合并，创建标准冲突标记
    echo "    ⚠️ 无分叉点，使用两路合并策略"
    
    echo "<<<<<<< HEAD" > "{file_path}.tmp"
    git show {target_branch}:"{file_path}" >> "{file_path}.tmp" 2>/dev/null || cat "{file_path}" >> "{file_path}.tmp"
    echo "=======" >> "{file_path}.tmp"
    git show {source_branch}:"{file_path}" >> "{file_path}.tmp" 2>/dev/null || echo "# 源分支版本获取失败" >> "{file_path}.tmp"
    echo ">>>>>>> {source_branch}" >> "{file_path}.tmp"

    mv "{file_path}.tmp" "{file_path}"
    echo "    ⚠️ 已创建手动合并模板（包含冲突标记）"
    conflicts_found=true
fi

# 清理临时文件
rm -rf "$TEMP_DIR"

"""
        elif file_path in analysis["only_in_source"]:
            script_content += f"""
echo "📥 处理源分支新增文件: {file_path}"
# 这是源分支新增的文件，直接复制
if git show {source_branch}:"{file_path}" > "{file_path}" 2>/dev/null; then
    echo "    ✅ 新文件已成功复制"
else
    echo "    ❌ 复制新文件失败"
    merge_success=false
fi

"""
        elif file_path in analysis["only_in_target"]:
            script_content += f"""
echo "📋 文件仅在目标分支存在: {file_path}"
echo "    ℹ️ 保持当前版本不变"

"""
        else:
            script_content += f"""
echo "📋 文件无需合并处理: {file_path}"
echo "    ℹ️ 源分支和目标分支版本相同"

"""

        # 结果处理
        script_content += f"""
echo ""
if [ "$conflicts_found" = true ]; then
    echo "⚠️ 文件包含冲突标记，需要手动解决"
    echo ""
    echo "🎯 冲突解决流程："
    echo " 1. 打开文件: code {file_path}"
    echo " 2. 查找冲突标记："
    echo "    - <<<<<<< HEAD (当前分支内容)"
    echo "    - ======= (分隔线)"
    echo "    - >>>>>>> {source_branch} (源分支内容)"
    echo " 3. 手动编辑，删除冲突标记，保留最终内容"
    echo " 4. 保存文件后添加到暂存区: git add {file_path}"
    echo ""
elif [ "$merge_success" = true ]; then
    echo "✅ 文件合并完成，无冲突!"
    echo ""
    echo "🎯 后续步骤："
    echo " 1. 检查文件内容: code {file_path}"
    echo " 2. 运行相关测试验证"
    echo " 3. 添加到暂存区: git add {file_path}"
else
    echo "❌ 文件合并失败"
    exit 1
fi

echo ""
echo "📝 合并完成信息："
echo "   文件: {file_path}"
echo "   负责人: {assignee}"
echo "   状态: $([ "$conflicts_found" = true ] && echo "需要手动解决冲突" || echo "合并成功")"
echo ""

"""

        script_content += self._get_file_strategy_footer_notes()

        return script_content

    def generate_file_batch_merge_script(
        self, assignee, file_list, batch_branch_name, source_branch, target_branch
    ):
        """生成文件批量Standard合并脚本"""
        file_paths = [f["path"] for f in file_list]
        analysis = self.analyze_file_modifications(
            file_paths, source_branch, target_branch
        )

        script_content = f"""#!/bin/bash
# Git Merge Orchestrator - 文件批量Standard合并脚本
# 生成时间: {self._get_current_time()}
#
# 负责人: {assignee}
# 文件数量: {len(file_list)}
# 分支: {batch_branch_name}
# 策略: Standard (三路合并)

set -e  # 遇到错误立即退出

echo "🚀 开始文件批量Standard合并处理"
echo "👤 负责人: {assignee}"
echo "📄 文件数量: {len(file_list)}"
echo "🌿 工作分支: {batch_branch_name}"
echo "💡 策略: Standard三路合并"
echo ""

echo "📋 待处理文件列表："
{chr(10).join([f'echo "  - {f["path"]} (状态: {f.get("status", "pending")})"' for f in file_list])}
echo ""

"""

        script_content += self._generate_merge_base_section(
            source_branch, target_branch
        )

        script_content += f"""
merge_success=true
conflicts_found=false
total_processed=0
conflict_files=()
success_files=()

echo "🔄 开始Standard批量三路合并..."
echo "💡 重要说明：对于冲突文件将产生标准冲突标记"
echo "   <<<<<<< HEAD       (当前分支内容)"  
echo "   ======="
echo "   >>>>>>> {source_branch}  (源分支内容)"
echo ""

"""

        # 批量处理每个文件
        for file_info in file_list:
            file_path = file_info["path"]
            script_content += f"""
echo "📄 处理文件: {file_path}"

"""

            if file_path in analysis["modified_in_both"]:
                script_content += f"""
# 创建临时目录用于三路合并
TEMP_DIR=$(mktemp -d)
BASE_FILE="$TEMP_DIR/base"
CURRENT_FILE="$TEMP_DIR/current"
SOURCE_FILE="$TEMP_DIR/source"

# 获取三个版本的文件内容
if [ -n "$MERGE_BASE" ]; then
    git show $MERGE_BASE:"{file_path}" > "$BASE_FILE" 2>/dev/null || echo "" > "$BASE_FILE"
    git show {target_branch}:"{file_path}" > "$CURRENT_FILE" 2>/dev/null || cp "{file_path}" "$CURRENT_FILE"
    git show {source_branch}:"{file_path}" > "$SOURCE_FILE" 2>/dev/null || echo "" > "$SOURCE_FILE"

    cp "{file_path}" "{file_path}.backup" 2>/dev/null || true

    if git merge-file -L "HEAD" -L "merge-base" -L "{source_branch}" --marker-size=7 "$CURRENT_FILE" "$BASE_FILE" "$SOURCE_FILE" 2>/dev/null; then
        cp "$CURRENT_FILE" "{file_path}"
        echo "  ✅ 三路合并成功，无冲突"
        success_files+=("{file_path}")
    else
        cp "$CURRENT_FILE" "{file_path}"
        echo "  ⚠️ 三路合并产生冲突，已标记在文件中"
        conflicts_found=true
        conflict_files+=("{file_path}")
    fi
else
    echo "  ⚠️ 无分叉点，使用两路合并策略"
    
    echo "<<<<<<< HEAD" > "{file_path}.tmp"
    git show {target_branch}:"{file_path}" >> "{file_path}.tmp" 2>/dev/null || cat "{file_path}" >> "{file_path}.tmp"
    echo "=======" >> "{file_path}.tmp"
    git show {source_branch}:"{file_path}" >> "{file_path}.tmp" 2>/dev/null || echo "# 源分支版本获取失败" >> "{file_path}.tmp"
    echo ">>>>>>> {source_branch}" >> "{file_path}.tmp"

    mv "{file_path}.tmp" "{file_path}"
    echo "  ⚠️ 已创建手动合并模板（包含冲突标记）"
    conflicts_found=true
    conflict_files+=("{file_path}")
fi

rm -rf "$TEMP_DIR"
total_processed=$((total_processed + 1))

"""
            elif file_path in analysis["only_in_source"]:
                script_content += f"""
echo "  📥 处理源分支新增文件"
if git show {source_branch}:"{file_path}" > "{file_path}" 2>/dev/null; then
    echo "  ✅ 新文件已成功复制"
    success_files+=("{file_path}")
else
    echo "  ❌ 复制新文件失败"
    merge_success=false
fi
total_processed=$((total_processed + 1))

"""
            else:
                script_content += f"""
echo "  📋 文件无需特殊处理"
success_files+=("{file_path}")
total_processed=$((total_processed + 1))

"""

        # 批量结果处理
        script_content += f"""
echo ""
echo "📊 批量合并结果统计："
echo "  总处理文件: $total_processed"
echo "  成功文件数: ${{#success_files[@]}}"
echo "  冲突文件数: ${{#conflict_files[@]}}"
echo ""

if [ "${{#conflict_files[@]}}" -gt 0 ]; then
    echo "⚠️ 以下文件包含冲突标记，需要手动解决："
    for file in "${{conflict_files[@]}}"; do
        echo "  - $file"
    done
    echo ""
fi

if [ "${{#success_files[@]}}" -gt 0 ]; then
    echo "✅ 以下文件合并成功，无冲突："
    for file in "${{success_files[@]}}"; do
        echo "  - $file"  
    done
    echo ""
fi

if [ "$conflicts_found" = true ]; then
    echo "🎯 批量冲突解决策略："
    echo " 1. 打开项目: code ."
    echo " 2. 在Source Control面板查看所有Modified文件"
    echo " 3. 优先处理无冲突文件（已成功合并的）"
    echo " 4. 将无冲突文件分批添加到暂存区"
    echo " 5. 逐个处理冲突文件："
    echo "    - 搜索 <<<<<<< HEAD 找到冲突位置"
    echo "    - 理解 ======= 上下两部分的区别"
    echo "    - 手动编辑保留正确内容，删除冲突标记"
    echo "    - 处理完一个文件就添加: git add <已解决文件>"
    echo " 6. 所有文件处理完后提交"
elif [ "$merge_success" = true ]; then
    echo "✅ 批量合并完成，所有文件均无冲突!"
    echo ""
    echo "🎯 批量验证流程："
    echo " 1. 打开项目检查: code ."
    echo " 2. 在Source Control面板review所有变更"
    echo " 3. 运行测试验证合并结果"
    echo " 4. 批量添加所有文件: git add ."
else
    echo "❌ 批量合并过程中出现严重错误"
    exit 1
fi

echo ""
echo "📝 批量合并完成信息："
echo "   负责人: {assignee}"
echo "   处理文件: $total_processed 个"
echo "   状态: $([ "$conflicts_found" = true ] && echo "部分文件需要手动解决冲突" || echo "全部合并成功")"
echo ""

"""

        script_content += self._get_file_batch_strategy_footer_notes()

        return script_content

    def _get_file_strategy_footer_notes(self):
        """文件级Standard策略特定的脚本结尾说明"""
        return """echo ""
echo "📋 Standard文件级合并说明："
echo " - 这是Git的标准合并策略，最安全可靠"
echo " - 冲突标记是正常现象，表示两个分支对同一处做了不同修改"
echo " - 手动解决冲突后的代码质量通常比自动合并更高"
echo " - 解决冲突时要理解业务逻辑，不只是简单选择一边"
echo " - 文件级处理让你可以专注于单个文件的合并质量"
echo ""
"""

    def _get_file_batch_strategy_footer_notes(self):
        """文件批量Standard策略特定的脚本结尾说明"""
        return """echo ""
echo "📋 Standard文件批量合并说明："
echo " - 批量处理提高效率，但保持文件级精确度"
echo " - 冲突解决要理解业务逻辑，不只是技术层面"
echo " - 保持与原代码作者的沟通，特别是复杂冲突"
echo " - 详细测试合并结果，确保功能完整性"
echo " - 可以分批提交，便于管理和问题回滚"
echo " - 优先处理无冲突文件，逐步解决复杂问题"
echo ""
"""

    def generate_file_batch_merge_script(
        self, assignee, assignee_files, batch_branch_name, source_branch, target_branch
    ):
        """生成Standard文件级批量合并脚本"""
        analysis = self.analyze_file_modifications(
            assignee_files, source_branch, target_branch
        )

        script_content = self._generate_common_script_header(
            f"file-batch-{assignee}",
            assignee,
            assignee_files,
            batch_branch_name,
            "文件级批量",
        )

        script_content += self._generate_merge_base_section(
            source_branch, target_branch
        )

        script_content += f"""
echo "📄 文件级批量处理详情:"
echo "  负责人: {assignee}"
echo "  文件数: {len(assignee_files)} 个"
echo ""

merge_success=true
conflicts_found=false
total_processed=0
conflict_files=()

echo "🔄 开始Standard文件级批量三路合并..."
echo "💡 重要说明：对于冲突文件将产生标准冲突标记"
echo "   <<<<<<< HEAD       (当前分支内容)"
echo "   ======="
echo "   >>>>>>> {source_branch}  (源分支内容)"
echo ""
"""

        script_content += self._generate_common_file_processing_sections(
            analysis, source_branch
        )
        script_content += self._generate_strategy_specific_merge_logic(
            analysis, source_branch, target_branch
        )

        # Standard批量特定的冲突处理说明
        script_content += """
echo ""
if [ "${#conflict_files[@]}" -gt 0 ]; then
    echo "⚠️ 以下文件包含冲突标记，需要手动解决："
    for file in "${conflict_files[@]}"; do
        echo "  - $file"
    done
fi

echo ""

if [ "$conflicts_found" = true ]; then
    echo "⚠️ Standard文件级批量合并中发现冲突文件"
    echo ""
    echo "🎯 文件级批量冲突解决策略："
    echo " 1. 打开VSCode: code ."
    echo " 2. 逐个处理冲突文件，专注单文件质量"
    echo " 3. 文件级处理的优势："
    echo "    - 每个文件独立处理，避免交叉影响"
    echo "    - 可以按文件功能分批解决冲突"
    echo "    - 更容易跟踪和回滚问题"
    echo " 4. 处理完一个文件就添加: git add <已解决文件>"
    echo " 5. 可以分文件提交，便于管理"
    echo ""
elif [ "$merge_success" = true ]; then
    echo "✅ Standard文件级批量三路合并完成! 所有文件均无冲突"
    echo ""
    echo "🎯 后续步骤："
    echo " 1. 检查合并结果: git status"
    echo " 2. 提交更改: git add -A && git commit -m 'Standard文件级批量合并完成'"
    echo " 3. 推送到远程: git push origin $batch_branch_name"
    echo ""
else
    echo "❌ Standard文件级批量合并过程中发现错误"
fi
"""

        script_content += self._generate_common_script_footer(
            f"file-batch-{assignee}", len(assignee_files), batch_branch_name
        )

        return script_content
