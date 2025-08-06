from .base_merge_executor import BaseMergeExecutor, MergeStrategy


class LegacyMergeExecutor(BaseMergeExecutor):
    """Legacy合并执行器 - 快速覆盖策略"""

    def __init__(self, git_ops, file_helper):
        super().__init__(git_ops, file_helper, MergeStrategy.LEGACY)

    def get_strategy_name(self):
        return "Legacy"

    def get_strategy_description(self):
        return "快速覆盖策略，源分支内容直接覆盖目标分支，无冲突标记"

    def generate_merge_script(self, group_name, assignee, files, branch_name, source_branch, target_branch):
        """生成Legacy合并脚本"""
        # 分析文件修改情况
        analysis = self.analyze_file_modifications(files, source_branch, target_branch)

        # 生成脚本头部
        script_content = self._generate_common_script_header(group_name, assignee, files, branch_name)

        # 添加merge-base检测
        script_content += self._generate_merge_base_section(source_branch, target_branch)

        # 添加变量初始化
        script_content += """
merge_success=true
conflicts_found=false
total_processed=0

echo "🔄 开始Legacy快速覆盖处理..."
"""

        # 添加公共文件处理部分
        script_content += self._generate_common_file_processing_sections(analysis, source_branch)

        # Legacy特定的冲突文件处理
        script_content += self._generate_strategy_specific_merge_logic(analysis, source_branch, target_branch)

        # 添加通用结尾
        script_content += self._generate_common_script_footer(group_name, len(files), branch_name)

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
        """生成Legacy批量合并脚本"""
        analysis = self.analyze_file_modifications(all_files, source_branch, target_branch)

        script_content = self._generate_common_script_header(
            f"batch-{assignee}", assignee, all_files, batch_branch_name, "批量"
        )

        script_content += self._generate_merge_base_section(source_branch, target_branch)

        # 添加组别详情
        script_content += f"""
echo "📄 组别详情:"
{chr(10).join([f'echo "  组 {g["name"]}: {g.get("file_count", len(g["files"]))} 个文件"' for g in assignee_groups])}
echo ""

merge_success=true
conflicts_found=false
total_processed=0

echo "🔄 开始Legacy批量快速覆盖处理..."
"""

        script_content += self._generate_common_file_processing_sections(analysis, source_branch)
        script_content += self._generate_strategy_specific_merge_logic(analysis, source_branch, target_branch)
        script_content += self._generate_common_batch_script_footer(
            assignee, len(assignee_groups), len(all_files), batch_branch_name
        )

        return script_content

    def _generate_strategy_specific_merge_logic(self, analysis, source_branch, target_branch):
        """生成Legacy特定的合并逻辑 - 直接覆盖冲突文件"""
        modified_in_both = analysis["modified_in_both"]

        if not modified_in_both:
            return ""

        script_logic = f"""
echo ""
echo "⚡ 处理两边都修改的文件 ({len(modified_in_both)}个) - Legacy快速覆盖..."
"""

        for file in modified_in_both:
            script_logic += f"""
echo "  [快速覆盖] {file}"
if git show {source_branch}:"{file}" > "{file}" 2>/dev/null; then
    echo "    ✅ Legacy快速覆盖完成（源分支版本优先）"
    total_processed=$((total_processed + 1))
else
    echo "    ❌ 无法从源分支获取文件: {file}"
    merge_success=false
fi
"""

        return script_logic

    def _print_analysis_result(self, analysis_result):
        """Legacy特定的分析结果显示"""
        super()._print_analysis_result(analysis_result)
        modified_in_both = analysis_result["modified_in_both"]
        if modified_in_both:
            print(f"  💡 其中 {len(modified_in_both)} 个文件将使用源分支版本快速覆盖")

    def _print_script_completion_message(self, script_file):
        """Legacy特定的完成消息"""
        super()._print_script_completion_message(script_file)
        print(f"💡 Legacy模式: 使用快速覆盖策略，无冲突标记")
        print(f"📝 适合: 确定源分支内容正确的场景")
        print(f"⚡ 优势: 执行速度快，操作简单")

    def _print_batch_script_completion_message(self, script_file):
        """Legacy特定的批量完成消息"""
        super()._print_batch_script_completion_message(script_file)
        print(f"💡 Legacy批量模式: 所有冲突文件使用源分支版本覆盖")
        print(f"📝 建议: 执行前确认源分支内容的正确性")
        print(f"⚡ 适合: 热修复、紧急发布等快速合并场景")

    def _get_strategy_footer_notes(self):
        """Legacy策略特定的脚本结尾说明"""
        return """echo " - 这是快速覆盖策略，冲突文件直接使用源分支版本"
echo " - 适合确定源分支内容正确的场景"
echo " - 执行速度快，但需要人工验证合并结果"
echo " - 如需精确控制，可切换到Standard模式"
"""

    def _get_batch_strategy_footer_notes(self):
        """Legacy批量策略特定的脚本结尾说明"""
        return """echo " - 批量快速覆盖比手动解决冲突更高效"
echo " - 适合小团队或高信任度的项目"
echo " - 建议在合并后运行完整测试套件"
echo " - 如发现问题，可以使用git reset回滚后重新处理"
"""

    # === 文件级处理方法实现 ===

    def generate_file_merge_script(self, file_path, assignee, branch_name, source_branch, target_branch):
        """生成Legacy单文件合并脚本"""
        # 分析单个文件的修改情况
        analysis = self.analyze_file_modifications([file_path], source_branch, target_branch)
        
        # 生成脚本头部
        script_content = self._generate_file_script_header(file_path, assignee, branch_name)
        
        # 添加merge-base检测
        script_content += self._generate_merge_base_section(source_branch, target_branch)
        
        # 添加变量初始化
        script_content += f"""
merge_success=true

echo "🔄 开始Legacy快速覆盖单文件处理: {file_path}..."
echo "💡 策略说明: 源分支内容直接覆盖，无冲突标记"
echo ""
"""
        
        # 生成文件特定的处理逻辑
        script_content += self._generate_file_processing_logic(file_path, analysis, source_branch, target_branch)
        
        # 添加通用结尾
        script_content += self._generate_file_script_footer(file_path, branch_name)
        
        return script_content

    def generate_file_batch_merge_script(
        self,
        assignee,
        assignee_files, 
        batch_branch_name,
        source_branch,
        target_branch,
    ):
        """生成Legacy文件批量合并脚本"""
        # 获取文件路径列表
        file_paths = [f['path'] for f in assignee_files]
        analysis = self.analyze_file_modifications(file_paths, source_branch, target_branch)
        
        script_content = self._generate_file_script_header(
            f"batch-{len(file_paths)}-files", assignee, batch_branch_name, "文件批量"
        )
        
        script_content += self._generate_merge_base_section(source_branch, target_branch)
        
        # 添加文件详情
        script_content += f"""
echo "📄 文件详情:"
{chr(10).join([f'echo "  文件: {f["path"]} (负责人: {f.get("assignee", "未分配")})"' for f in assignee_files])}
echo ""

batch_success=true
successful_files=0
failed_files=0

echo "🔄 开始Legacy文件批量快速覆盖处理..."
echo "💡 策略说明: 所有冲突文件使用源分支版本覆盖"
echo ""
"""
        
        # 逐个处理每个文件
        for file_info in assignee_files:
            file_path = file_info['path']
            script_content += self._generate_single_file_processing_logic(
                file_path, analysis, source_branch, target_branch
            )
        
        script_content += self._generate_file_batch_script_footer(
            assignee, len(assignee_files), batch_branch_name
        )
        
        return script_content

    def _generate_file_processing_logic(self, file_path, analysis, source_branch, target_branch):
        """生成单文件处理逻辑"""
        missing_files = analysis["missing_files"]
        modified_only_in_source = analysis["modified_only_in_source"] 
        modified_in_both = analysis["modified_in_both"]
        no_changes = analysis["no_changes"]
        
        script_logic = ""
        
        if file_path in missing_files:
            script_logic += f"""
echo "🆕 处理新增文件: {file_path}"
mkdir -p "$(dirname "{file_path}")"
if git show {source_branch}:"{file_path}" > "{file_path}" 2>/dev/null; then
    echo "    ✅ 新文件已复制到工作区"
else
    echo "    ❌ 无法从源分支获取文件: {file_path}"
    merge_success=false
fi
"""
        elif file_path in modified_only_in_source:
            script_logic += f"""
echo "📝 处理仅源分支修改的文件: {file_path}"
if git show {source_branch}:"{file_path}" > "{file_path}" 2>/dev/null; then
    echo "    ✅ 文件已更新（目标分支无修改，安全覆盖）"
else
    echo "    ❌ 无法从源分支获取文件: {file_path}"
    merge_success=false
fi
"""
        elif file_path in modified_in_both:
            script_logic += f"""
echo "⚡ 处理两边都修改的文件: {file_path} - Legacy快速覆盖"
if git show {source_branch}:"{file_path}" > "{file_path}" 2>/dev/null; then
    echo "    ✅ Legacy快速覆盖完成（源分支版本优先）"
else
    echo "    ❌ 无法从源分支获取文件: {file_path}"
    merge_success=false
fi
"""
        elif file_path in no_changes:
            script_logic += f"""
echo "📋 跳过无变化的文件: {file_path} (两个分支中内容相同)"
"""
        
        return script_logic

    def _generate_single_file_processing_logic(self, file_path, analysis, source_branch, target_branch):
        """生成批量处理中单个文件的处理逻辑"""
        missing_files = analysis["missing_files"]
        modified_only_in_source = analysis["modified_only_in_source"]
        modified_in_both = analysis["modified_in_both"]
        no_changes = analysis["no_changes"]
        
        script_logic = f"""
echo "📄 处理文件: {file_path}"
"""
        
        if file_path in missing_files:
            script_logic += f"""
echo "  [新增] {file_path}"
mkdir -p "$(dirname "{file_path}")"
if git show {source_branch}:"{file_path}" > "{file_path}" 2>/dev/null; then
    echo "    ✅ 新文件已复制到工作区"
    successful_files=$((successful_files + 1))
else
    echo "    ❌ 无法从源分支获取文件: {file_path}"
    failed_files=$((failed_files + 1))
    batch_success=false
fi
"""
        elif file_path in modified_only_in_source:
            script_logic += f"""
echo "  [安全覆盖] {file_path}"
if git show {source_branch}:"{file_path}" > "{file_path}" 2>/dev/null; then
    echo "    ✅ 文件已更新（目标分支无修改）"
    successful_files=$((successful_files + 1))
else
    echo "    ❌ 无法从源分支获取文件: {file_path}"
    failed_files=$((failed_files + 1))
    batch_success=false
fi
"""
        elif file_path in modified_in_both:
            script_logic += f"""
echo "  [快速覆盖] {file_path}"
if git show {source_branch}:"{file_path}" > "{file_path}" 2>/dev/null; then
    echo "    ✅ Legacy快速覆盖完成（源分支版本优先）"
    successful_files=$((successful_files + 1))
else
    echo "    ❌ 无法从源分支获取文件: {file_path}"
    failed_files=$((failed_files + 1))
    batch_success=false
fi
"""
        elif file_path in no_changes:
            script_logic += f"""
echo "  [跳过] {file_path} (两个分支中内容相同)"
successful_files=$((successful_files + 1))
"""
        
        script_logic += "\necho \"\"\n"
        return script_logic

    def _print_file_script_completion_message(self, script_file, file_path):
        """Legacy特定的单文件完成消息"""
        super()._print_file_script_completion_message(script_file, file_path)
        print(f"💡 Legacy单文件模式: 使用快速覆盖策略，无冲突标记")
        print(f"📝 适合: 确定源分支内容正确的单文件快速合并")
        print(f"⚡ 优势: 处理速度极快，操作简单")

    def _print_file_batch_script_completion_message(self, script_file, assignee_files):
        """Legacy特定的文件批量完成消息"""
        super()._print_file_batch_script_completion_message(script_file, assignee_files)
        print(f"💡 Legacy文件批量模式: 所有冲突文件使用源分支版本覆盖")
        print(f"📝 建议: 执行前确认所有源分支文件内容的正确性")
        print(f"⚡ 适合: 批量文件快速处理和紧急发布场景")

    def _get_file_strategy_footer_notes(self):
        """Legacy文件级策略特定的脚本结尾说明"""
        return """echo " - 这是单文件快速覆盖策略，直接使用源分支版本"
echo " - 适合确定源分支文件内容正确的场景"
echo " - 执行速度极快，但需要人工验证文件内容"
echo " - 如需精确控制，可切换到Standard模式"
"""

    def _get_file_batch_strategy_footer_notes(self):
        """Legacy文件批量策略特定的脚本结尾说明"""
        return """echo " - 文件批量快速覆盖比逐个解决冲突更高效"
echo " - 适合同一负责人的相关文件批量处理"
echo " - 建议按文件类型或目录分组验证结果"
echo " - 如发现问题，可以针对性回滚特定文件"
"""


class StandardMergeExecutor(BaseMergeExecutor):
    """Standard合并执行器 - 三路合并策略"""

    def __init__(self, git_ops, file_helper):
        super().__init__(git_ops, file_helper, MergeStrategy.STANDARD)

    def get_strategy_name(self):
        return "Standard"

    def get_strategy_description(self):
        return "标准Git三路合并，产生冲突标记 <<<<<<< ======= >>>>>>>"

    def generate_merge_script(self, group_name, assignee, files, branch_name, source_branch, target_branch):
        """生成Standard合并脚本"""
        analysis = self.analyze_file_modifications(files, source_branch, target_branch)

        script_content = self._generate_common_script_header(group_name, assignee, files, branch_name)

        script_content += self._generate_merge_base_section(source_branch, target_branch)

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

        script_content += self._generate_common_file_processing_sections(analysis, source_branch)
        script_content += self._generate_strategy_specific_merge_logic(analysis, source_branch, target_branch)

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

        script_content += self._generate_common_script_footer(group_name, len(files), branch_name)

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
        analysis = self.analyze_file_modifications(all_files, source_branch, target_branch)

        script_content = self._generate_common_script_header(
            f"batch-{assignee}", assignee, all_files, batch_branch_name, "批量"
        )

        script_content += self._generate_merge_base_section(source_branch, target_branch)

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

        script_content += self._generate_common_file_processing_sections(analysis, source_branch)
        script_content += self._generate_strategy_specific_merge_logic(analysis, source_branch, target_branch)

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

    def _generate_strategy_specific_merge_logic(self, analysis, source_branch, target_branch):
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

    # === Standard策略文件级处理方法实现 ===

    def generate_file_merge_script(self, file_path, assignee, branch_name, source_branch, target_branch):
        """生成Standard单文件合并脚本"""
        analysis = self.analyze_file_modifications([file_path], source_branch, target_branch)
        
        script_content = self._generate_file_script_header(file_path, assignee, branch_name)
        script_content += self._generate_merge_base_section(source_branch, target_branch)
        
        script_content += f"""
merge_success=true
conflicts_found=false

echo "🔄 开始Standard三路合并单文件处理: {file_path}..."
echo "💡 重要说明：三路合并将产生标准冲突标记"
echo "   <<<<<<< HEAD       (当前分支内容)"
echo "   ======="
echo "   >>>>>>> {source_branch}  (源分支内容)"
echo ""
"""
        
        script_content += self._generate_standard_file_processing_logic(
            file_path, analysis, source_branch, target_branch
        )
        
        # Standard特定的冲突处理说明
        script_content += f"""
echo ""
if [ "$conflicts_found" = true ]; then
    echo "⚠️ 文件 {file_path} 包含冲突标记，需要手动解决"
    echo ""
    echo "🎯 标准冲突解决流程："
    echo " 1. 打开文件编辑器: code {file_path} 或 vim {file_path}"
    echo " 2. 查找 <<<<<<< HEAD 标记"
    echo " 3. HEAD后面是当前分支的内容"
    echo " 4. ======= 是分隔线"
    echo " 5. >>>>>>> 前面是源分支的内容"
    echo " 6. 手动编辑，删除冲突标记，保留最终想要的内容"
    echo " 7. 保存文件"
    echo ""
    echo "💡 VSCode冲突解决技巧："
    echo " - 可以点击 'Accept Current Change' 或 'Accept Incoming Change'"
    echo " - 也可以点击 'Accept Both Changes' 然后手动调整"
elif [ "$merge_success" = true ]; then
    echo "✅ Standard三路合并完成! 文件无冲突"
    echo ""
    echo "🎯 后续验证流程："
    echo " 1. 检查文件内容: cat {file_path} 或 code {file_path}"
    echo " 2. 验证功能正确性"
    echo " 3. 运行相关测试"
else
    echo "❌ 文件合并过程中出现严重错误"
    merge_success=false
fi
"""
        
        script_content += self._generate_file_script_footer(file_path, branch_name)
        return script_content

    def generate_file_batch_merge_script(
        self,
        assignee,
        assignee_files,
        batch_branch_name,
        source_branch,
        target_branch,
    ):
        """生成Standard文件批量合并脚本"""
        file_paths = [f['path'] for f in assignee_files]
        analysis = self.analyze_file_modifications(file_paths, source_branch, target_branch)
        
        script_content = self._generate_file_script_header(
            f"batch-{len(file_paths)}-files", assignee, batch_branch_name, "文件批量"
        )
        
        script_content += self._generate_merge_base_section(source_branch, target_branch)
        
        script_content += f"""
echo "📄 文件详情:"
{chr(10).join([f'echo "  文件: {f["path"]} (负责人: {f.get("assignee", "未分配")})"' for f in assignee_files])}
echo ""

batch_success=true
conflicts_found=false
successful_files=0
failed_files=0
conflict_files=()

echo "🔄 开始Standard文件批量三路合并..."
echo "💡 重要说明：对于冲突文件将产生标准冲突标记"
echo "   <<<<<<< HEAD       (当前分支内容)"
echo "   ======="
echo "   >>>>>>> {source_branch}  (源分支内容)"
echo ""
"""
        
        # 逐个处理每个文件
        for file_info in assignee_files:
            file_path = file_info['path']
            script_content += self._generate_standard_single_file_processing_logic(
                file_path, analysis, source_branch, target_branch
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
    echo "⚠️ Standard文件批量合并中发现冲突文件"
    echo ""
    echo "🎯 批量冲突解决策略："
    echo " 1. 按文件类型分组处理（相关文件一起处理）"
    echo " 2. 优先处理无冲突文件（没有 <<<<<<< 标记的）"
    echo " 3. 将无冲突文件分批添加到暂存区"
    echo " 4. 逐个处理冲突文件："
    echo "    - 打开文件: code <文件路径>"
    echo "    - 搜索 <<<<<<< HEAD 找到冲突位置"
    echo "    - 理解 ======= 上下两部分的区别"
    echo "    - 手动编辑保留正确内容，删除冲突标记"
    echo "    - 处理完一个文件就添加: git add <已解决文件>"
    echo " 5. 所有文件处理完后提交"
elif [ "$batch_success" = true ]; then
    echo "✅ Standard文件批量三路合并完成! 所有文件均无冲突"
    echo ""
    echo "🎯 批量验证流程："
    echo " 1. 按文件类型检查修改内容"
    echo " 2. 验证关键文件的功能正确性"
    echo " 3. 运行完整测试套件验证合并结果"
    echo " 4. 按类型或功能分批添加文件"
else
    echo "❌ 文件批量合并过程中出现严重错误"
    batch_success=false
fi
"""
        
        script_content += self._generate_file_batch_script_footer(
            assignee, len(assignee_files), batch_branch_name
        )
        
        return script_content

    def _generate_standard_file_processing_logic(self, file_path, analysis, source_branch, target_branch):
        """生成Standard单文件处理逻辑"""
        missing_files = analysis["missing_files"]
        modified_only_in_source = analysis["modified_only_in_source"]
        modified_in_both = analysis["modified_in_both"]
        no_changes = analysis["no_changes"]
        
        script_logic = ""
        
        if file_path in missing_files:
            script_logic += f"""
echo "🆕 处理新增文件: {file_path}"
mkdir -p "$(dirname "{file_path}")"
if git show {source_branch}:"{file_path}" > "{file_path}" 2>/dev/null; then
    echo "    ✅ 新文件已复制到工作区"
else
    echo "    ❌ 无法从源分支获取文件: {file_path}"
    merge_success=false
fi
"""
        elif file_path in modified_only_in_source:
            script_logic += f"""
echo "📝 处理仅源分支修改的文件: {file_path}"
if git show {source_branch}:"{file_path}" > "{file_path}" 2>/dev/null; then
    echo "    ✅ 文件已更新（目标分支无修改，安全覆盖）"
else
    echo "    ❌ 无法从源分支获取文件: {file_path}"
    merge_success=false
fi
"""
        elif file_path in modified_in_both:
            script_logic += f"""
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

    # 使用git merge-file进行三路合并，设置正确的标签
    if git merge-file -L "HEAD" -L "merge-base" -L "{source_branch}" --marker-size=7 "$CURRENT_FILE" "$BASE_FILE" "$SOURCE_FILE" 2>/dev/null; then
        # 无冲突，直接复制结果
        cp "$CURRENT_FILE" "{file_path}"
        echo "    ✅ 三路合并成功，无冲突"
    else
        # 有冲突，复制包含冲突标记的结果
        cp "$CURRENT_FILE" "{file_path}"
        echo "    ⚠️ 三路合并产生冲突，已标记在文件中"
        echo "    💡 冲突标记格式："
        echo "       <<<<<<< HEAD"
        echo "       当前分支的内容"
        echo "       ======="
        echo "       源分支的内容"
        echo "       >>>>>>> {source_branch}"
        conflicts_found=true
    fi
else
    # 没有merge-base，使用两路合并，创建标准冲突标记
    echo "    ⚠️ 无分叉点，使用两路合并策略"

    # 创建包含冲突标记的合并结果，使用正确的分支标签
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
        elif file_path in no_changes:
            script_logic += f"""
echo "📋 跳过无变化的文件: {file_path} (两个分支中内容相同)"
"""
        
        return script_logic

    def _generate_standard_single_file_processing_logic(self, file_path, analysis, source_branch, target_branch):
        """生成Standard批量处理中单个文件的处理逻辑"""
        missing_files = analysis["missing_files"]
        modified_only_in_source = analysis["modified_only_in_source"]
        modified_in_both = analysis["modified_in_both"]
        no_changes = analysis["no_changes"]
        
        script_logic = f"""
echo "📄 处理文件: {file_path}"
"""
        
        if file_path in missing_files:
            script_logic += f"""
echo "  [新增] {file_path}"
mkdir -p "$(dirname "{file_path}")"
if git show {source_branch}:"{file_path}" > "{file_path}" 2>/dev/null; then
    echo "    ✅ 新文件已复制到工作区"
    successful_files=$((successful_files + 1))
else
    echo "    ❌ 无法从源分支获取文件: {file_path}"
    failed_files=$((failed_files + 1))
    batch_success=false
fi
"""
        elif file_path in modified_only_in_source:
            script_logic += f"""
echo "  [安全覆盖] {file_path}"
if git show {source_branch}:"{file_path}" > "{file_path}" 2>/dev/null; then
    echo "    ✅ 文件已更新（目标分支无修改）"
    successful_files=$((successful_files + 1))
else
    echo "    ❌ 无法从源分支获取文件: {file_path}"
    failed_files=$((failed_files + 1))
    batch_success=false
fi
"""
        elif file_path in modified_in_both:
            script_logic += f"""
echo "  [三路合并] {file_path}"

# 三路合并处理逻辑（简化版）
TEMP_DIR=$(mktemp -d)
BASE_FILE="$TEMP_DIR/base"
CURRENT_FILE="$TEMP_DIR/current"
SOURCE_FILE="$TEMP_DIR/source"

if [ -n "$MERGE_BASE" ]; then
    git show $MERGE_BASE:"{file_path}" > "$BASE_FILE" 2>/dev/null || echo "" > "$BASE_FILE"
    git show {target_branch}:"{file_path}" > "$CURRENT_FILE" 2>/dev/null || cp "{file_path}" "$CURRENT_FILE"
    git show {source_branch}:"{file_path}" > "$SOURCE_FILE" 2>/dev/null || echo "" > "$SOURCE_FILE"
    
    if git merge-file -L "HEAD" -L "merge-base" -L "{source_branch}" --marker-size=7 "$CURRENT_FILE" "$BASE_FILE" "$SOURCE_FILE" 2>/dev/null; then
        cp "$CURRENT_FILE" "{file_path}"
        echo "    ✅ 三路合并成功，无冲突"
        successful_files=$((successful_files + 1))
    else
        cp "$CURRENT_FILE" "{file_path}"
        echo "    ⚠️ 三路合并产生冲突，已标记在文件中"
        conflicts_found=true
        conflict_files+=("{file_path}")
        successful_files=$((successful_files + 1))
    fi
else
    echo "<<<<<<< HEAD" > "{file_path}.tmp"
    git show {target_branch}:"{file_path}" >> "{file_path}.tmp" 2>/dev/null || cat "{file_path}" >> "{file_path}.tmp"
    echo "=======" >> "{file_path}.tmp"
    git show {source_branch}:"{file_path}" >> "{file_path}.tmp" 2>/dev/null || echo "# 源分支版本获取失败" >> "{file_path}.tmp"
    echo ">>>>>>> {source_branch}" >> "{file_path}.tmp"
    
    mv "{file_path}.tmp" "{file_path}"
    echo "    ⚠️ 已创建手动合并模板（包含冲突标记）"
    conflicts_found=true
    conflict_files+=("{file_path}")
    successful_files=$((successful_files + 1))
fi

rm -rf "$TEMP_DIR"
"""
        elif file_path in no_changes:
            script_logic += f"""
echo "  [跳过] {file_path} (两个分支中内容相同)"
successful_files=$((successful_files + 1))
"""
        
        script_logic += "\necho \"\"\n"
        return script_logic

    def _print_file_script_completion_message(self, script_file, file_path):
        """Standard特定的单文件完成消息"""
        super()._print_file_script_completion_message(script_file, file_path)
        print(f"💡 Standard单文件模式: 使用Git标准三路合并策略")
        print(f"⚠️ 冲突文件将包含标准冲突标记 <<<<<<< ======= >>>>>>>")
        print(f"📝 请在编辑器中检查和解决冲突后手动提交")
        print(f"🛡️ 优势: 安全可靠，保留完整的合并历史")

    def _print_file_batch_script_completion_message(self, script_file, assignee_files):
        """Standard特定的文件批量完成消息"""
        super()._print_file_batch_script_completion_message(script_file, assignee_files)
        print(f"💡 Standard文件批量模式: 使用Git标准三路合并策略")
        print(f"⚠️ 冲突文件将包含标准冲突标记 <<<<<<< ======= >>>>>>>")
        print(f"📝 建议在编辑器中按类型分批检查和解决冲突")
        print(f"🔄 可以分类型提交，便于管理和问题回滚")

    def _get_file_strategy_footer_notes(self):
        """Standard文件级策略特定的脚本结尾说明"""
        return """echo " - 这是Git的标准文件合并策略，最安全可靠"
echo " - 冲突标记是正常现象，表示两个分支对同一处做了不同修改"
echo " - 手动解决冲突后的代码质量通常比自动合并更高"
echo " - 解决冲突时要理解业务逻辑，不只是简单选择一边"
"""

    def _get_file_batch_strategy_footer_notes(self):
        """Standard文件批量策略特定的脚本结尾说明"""
        return """echo " - 文件批量三路合并需要细致的冲突解决"
echo " - 建议按文件功能或类型分组处理冲突"
echo " - 保持与原代码作者的沟通，特别是复杂冲突"
echo " - 详细测试每类文件的合并结果，确保功能完整性"
echo " - 考虑在合并后创建临时分支备份重要文件"
"""
