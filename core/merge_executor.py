"""
Git Merge Orchestrator - 合并执行器
负责生成合并脚本和执行合并操作
"""

from datetime import datetime


class MergeExecutor:
    """合并执行器"""

    def __init__(self, git_ops, file_helper):
        self.git_ops = git_ops
        self.file_helper = file_helper

    def generate_smart_merge_script(self, group_name, assignee, files, branch_name, source_branch, target_branch):
        """生成智能合并脚本，处理新文件和已存在文件"""
        # 检查文件存在性
        existing_files, missing_files = self.git_ops.check_file_existence(files, target_branch)

        print(f"📊 文件分析:")
        print(f"  - 已存在文件: {len(existing_files)} 个")
        print(f"  - 新增文件: {len(missing_files)} 个")

        # 生成处理脚本
        script_content = f"""#!/bin/bash
# 智能合并脚本 - {group_name} (负责人: {assignee})
# 文件数: {len(files)} (已存在: {len(existing_files)}, 新增: {len(missing_files)})
# 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

set -e # 遇到错误立即退出

echo "🚀 开始智能合并组: {group_name}"
echo "👤 负责人: {assignee}"
echo "🌿 工作分支: {branch_name}"
echo "📁 总文件数: {len(files)}"
echo "📊 已存在文件: {len(existing_files)}"
echo "📊 新增文件: {len(missing_files)}"
echo ""

# 切换到工作分支
echo "📋 切换到工作分支..."
git checkout {branch_name}

echo "📄 文件详情:"
"""

        if existing_files:
            script_content += f"""
echo "✅ 已存在文件 ({len(existing_files)}个):"
{chr(10).join([f'echo "  - {file}"' for file in existing_files])}
"""

        if missing_files:
            script_content += f"""
echo "🆕 新增文件 ({len(missing_files)}个):"
{chr(10).join([f'echo "  - {file}"' for file in missing_files])}
"""

        script_content += f"""
echo ""

# 智能合并策略
merge_success=true

echo "🔄 开始智能选择性合并..."
"""

        # 处理已存在文件
        if existing_files:
            script_content += f"""
echo "📝 处理已存在文件..."
if git checkout {source_branch} -- {' '.join([f'"{f}"' for f in existing_files])}; then
    echo "✅ 已存在文件合并成功"
else
    echo "⚠️ 已存在文件合并时出现问题"
    merge_success=false
fi
"""

        # 处理新增文件
        if missing_files:
            script_content += f"""
echo "🆕 处理新增文件..."
"""
            for file in missing_files:
                script_content += f"""
echo "  处理新文件: {file}"
# 创建目录结构
mkdir -p "$(dirname "{file}")"
# 从源分支复制文件内容
if git show {source_branch}:{file} > "{file}" 2>/dev/null; then
    git add "{file}"
    echo "    ✅ 新文件 {file} 添加成功"
else
    echo "    ❌ 无法从源分支获取文件: {file}"
    merge_success=false
fi
"""

        script_content += f"""
echo ""

if [ "$merge_success" = true ]; then
    echo "✅ 智能合并完成!"
    echo ""
    echo "📊 合并状态:"
    git status --short
    echo ""
    echo "🔍 文件差异概览:"
    git diff --cached --stat 2>/dev/null || echo "(新文件无差异显示)"
    echo ""
    echo "⏭️ 下一步操作："
    echo " 1. 检查合并结果: git diff --cached"
    echo " 2. 检查新文件内容: git diff --no-index /dev/null <文件名>"
    echo " 3. 提交更改: git commit -m 'Merge group: {group_name} ({len(files)} files)'"
    echo " 4. 推送分支: git push origin {branch_name}"
    echo ""
    echo "🔄 如需回滚: git reset --hard HEAD"
else
    echo "❌ 智能合并过程中出现问题"
    echo "🔧 可能的问题和解决方案："
    echo " 1. 文件在源分支中不存在 - 请检查分支和文件路径"
    echo " 2. 权限问题 - 请检查文件和目录权限"
    echo " 3. 路径问题 - 请检查文件路径是否正确"
    echo ""
    echo "📊 当前状态:"
    git status
    echo ""
    echo "🛠️ 手动处理步骤："
    echo " 1. 检查具体错误: 查看上方错误信息"
    echo " 2. 手动复制问题文件: cp source/path target/path"
    echo " 3. 添加文件: git add <files>"
    echo " 4. 提交: git commit -m 'Manual merge: {group_name}'"
    exit 1
fi
"""

        return script_content

    def generate_batch_merge_script(self, assignee, assignee_groups, all_files, batch_branch_name,
                                  source_branch, target_branch):
        """生成批量合并脚本"""
        # 检查文件存在性
        existing_files, missing_files = self.git_ops.check_file_existence(all_files, target_branch)

        print(f"📊 批量合并文件分析:")
        print(f"  - 已存在文件: {len(existing_files)} 个")
        print(f"  - 新增文件: {len(missing_files)} 个")

        script_content = f"""#!/bin/bash
# 批量智能合并脚本 - 负责人: {assignee}
# 组数: {len(assignee_groups)} (文件总数: {len(all_files)}, 已存在: {len(existing_files)}, 新增: {len(missing_files)})
# 创建时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

set -e # 遇到错误立即退出

echo "🚀 开始批量智能合并负责人 '{assignee}' 的所有任务"
echo "🌿 工作分支: {batch_branch_name}"
echo "📁 总文件数: {len(all_files)}"
echo "📊 已存在文件: {len(existing_files)}"
echo "📊 新增文件: {len(missing_files)}"
echo "📋 包含组: {', '.join([g['name'] for g in assignee_groups])}"
echo ""

# 切换到工作分支
echo "📋 切换到工作分支..."
git checkout {batch_branch_name}

echo "📄 组别详情:"
{chr(10).join([f'echo "  组 {g["name"]}: {g.get("file_count", len(g["files"]))} 个文件"' for g in assignee_groups])}
echo ""

# 智能合并策略
merge_success=true

echo "🔄 开始批量智能选择性合并..."
"""

        # 处理已存在文件
        if existing_files:
            script_content += f"""
echo "📝 处理已存在文件 ({len(existing_files)}个)..."
if git checkout {source_branch} -- {' '.join([f'"{f}"' for f in existing_files])}; then
    echo "✅ 已存在文件批量合并成功"
else
    echo "⚠️ 部分已存在文件合并时出现问题"
    merge_success=false
fi
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
if git show {source_branch}:{file} > "{file}" 2>/dev/null; then
    git add "{file}"
    echo "    ✅ 新文件 {file} 添加成功"
else
    echo "    ❌ 无法从源分支获取文件: {file}"
    merge_success=false
fi
"""

        script_content += f"""
echo ""

if [ "$merge_success" = true ]; then
    echo "✅ 批量智能合并完成!"
    echo ""
    echo "📊 合并状态:"
    git status --short
    echo ""
    echo "🔍 文件差异概览:"
    git diff --cached --stat 2>/dev/null || echo "(新文件无差异显示)"
    echo ""
    echo "⏭️ 下一步操作："
    echo " 1. 检查合并结果: git diff --cached"
    echo " 2. 检查新文件内容 (如有): git diff --no-index /dev/null <文件名>"
    echo " 3. 提交更改: git commit -m 'Batch merge for {assignee}: {len(assignee_groups)} groups, {len(all_files)} files'"
    echo " 4. 推送分支: git push origin {batch_branch_name}"
    echo ""
    echo "🔄 如需回滚: git reset --hard HEAD"
else
    echo "❌ 批量智能合并过程中出现问题"
    echo ""
    echo "🔧 可能的问题和解决方案："
    echo " 1. 某些文件在源分支中不存在 - 请检查文件路径和分支"
    echo " 2. 权限问题 - 请检查文件和目录权限"
    echo " 3. 路径冲突 - 请检查文件路径是否正确"
    echo ""
    echo "📊 当前状态:"
    git status
    echo ""
    echo "🛠️ 手动处理步骤："
    echo " 1. 检查具体错误信息 (见上方输出)"
    echo " 2. 对于问题文件，手动复制: cp source_branch_checkout/path target/path"
    echo " 3. 添加文件: git add <files>"
    echo " 4. 提交: git commit -m 'Manual batch merge for {assignee}'"
    echo ""
    echo "💡 提示: 你可以分组处理，先处理成功的文件，再单独处理问题文件"
    exit 1
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

        # 创建合并分支
        branch_name = self.git_ops.create_merge_branch(group_name, assignee, integration_branch)

        # 生成智能合并脚本
        script_content = self.generate_smart_merge_script(
            group_name, assignee, group_info["files"], branch_name, source_branch, target_branch
        )

        script_file = self.file_helper.create_script_file(
            f"merge_{group_name.replace('/', '_')}", script_content
        )

        print(f"✅ 已生成智能合并脚本: {script_file}")
        print(f"🎯 请执行: ./{script_file}")

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

        print(f"🎯 开始批量合并负责人 '{assignee_name}' 的所有任务...")
        print(f"📋 共 {len(assignee_groups)} 个组，总计 {sum(g.get('file_count', len(g['files'])) for g in assignee_groups)} 个文件")

        # 收集所有文件
        all_files = []
        for group in assignee_groups:
            all_files.extend(group["files"])

        if not all_files:
            print("❌ 没有找到需要合并的文件")
            return False

        # 创建统一的合并分支
        batch_branch_name = self.git_ops.create_batch_merge_branch(assignee_name, integration_branch)

        # 生成智能批量合并脚本
        script_content = self.generate_batch_merge_script(
            assignee_name, assignee_groups, all_files, batch_branch_name, source_branch, target_branch
        )

        script_file = self.file_helper.create_script_file(
            f"merge_batch_{assignee_name.replace(' ', '_')}", script_content
        )

        print(f"✅ 已生成智能批量合并脚本: {script_file}")
        print(f"🎯 请执行: ./{script_file}")

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
            print(f" 2. 推送到远程: git push origin {integration_branch}")
            print(f" 3. 创建PR/MR合并到 {plan['target_branch']}")

        return all_success