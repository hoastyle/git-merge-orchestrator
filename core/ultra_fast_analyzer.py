"""
Ultra Fast Contributor Analyzer
革命性性能优化：全局分析 + 智能推断
预期性能提升：10-100倍
"""

import subprocess
import json
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


class UltraFastAnalyzer:
    """超高速贡献者分析器"""
    
    def __init__(self, repo_path="."):
        self.repo_path = Path(repo_path)
        self.cache_file = self.repo_path / ".merge_work" / "ultra_cache.json"
        self.cache_expiry_hours = 6  # 6小时缓存过期
        
    def analyze_contributors_ultra_fast(self, file_list, months=6, force_incremental=False):
        """超高速分析 - 全局分析 + 智能推断 + 增量更新"""
        print(f"🚀 开始超高速分析 {len(file_list)} 个文件...")
        start_time = time.time()
        
        # 1. 检查是否可以使用增量更新
        if not force_incremental and self._should_use_incremental_update(file_list):
            return self._incremental_update_analysis(file_list, months)
        
        # 2. 检查缓存
        if self._is_cache_valid():
            print("⚡ 使用缓存数据，瞬间完成")
            cached_data = self._load_cache()
            return self._extract_file_results(cached_data, file_list)
        
        # 3. 全局分析 - 一次Git调用获取所有信息
        since_date = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
        global_data = self._global_analysis(since_date)
        
        # 4. 智能分配
        results = self._intelligent_assignment(global_data, file_list)
        
        # 5. 保存缓存
        self._save_cache(global_data)
        
        elapsed = time.time() - start_time
        print(f"⚡ 超高速分析完成: {elapsed:.3f}s (平均 {elapsed/len(file_list)*1000:.1f}ms/文件)")
        
        return results
    
    def _should_use_incremental_update(self, file_list):
        """判断是否应该使用增量更新"""
        if not self.cache_file.exists():
            return False
            
        try:
            cached_data = self._load_cache()
            cached_files = set(cached_data['file_contributors'].keys())
            
            # 如果超过80%的文件已在缓存中，且文件总数不少，使用增量更新
            overlap = len(set(file_list) & cached_files)
            overlap_ratio = overlap / len(file_list) if file_list else 0
            
            should_use = overlap_ratio > 0.8 and len(file_list) > 20
            if should_use:
                print(f"📊 增量更新条件满足：{overlap}/{len(file_list)} ({overlap_ratio*100:.1f}%) 文件已缓存")
            
            return should_use
        except:
            return False
    
    def _incremental_update_analysis(self, file_list, months):
        """增量更新分析 - 只分析变更的文件"""
        print("🔄 使用增量更新模式...")
        start_time = time.time()
        
        try:
            # 1. 加载现有缓存
            cached_data = self._load_cache()
            cached_files = set(cached_data['file_contributors'].keys())
            
            # 2. 识别需要更新的文件
            new_files = [f for f in file_list if f not in cached_files]
            changed_files = self._get_changed_files_since_cache(cached_data['timestamp'])
            
            files_to_update = list(set(new_files + changed_files))
            
            print(f"   📋 需要更新: {len(files_to_update)} 个文件 (新增: {len(new_files)}, 变更: {len(changed_files)})")
            
            if files_to_update:
                # 3. 只分析需要更新的文件
                since_date = (datetime.now() - timedelta(days=months * 30)).strftime("%Y-%m-%d")
                incremental_data = self._incremental_analysis(files_to_update, since_date)
                
                # 4. 合并到现有缓存
                cached_data['file_contributors'].update(incremental_data['file_contributors'])
                cached_data['author_activity'].update(incremental_data['author_activity'])
                cached_data['timestamp'] = time.time()
                
                # 5. 保存更新后的缓存
                self._save_cache(cached_data)
            
            # 6. 返回结果
            results = self._extract_file_results(cached_data, file_list)
            
            elapsed = time.time() - start_time
            print(f"⚡ 增量分析完成: {elapsed:.3f}s (更新了 {len(files_to_update)} 个文件)")
            
            return results
            
        except Exception as e:
            print(f"⚠️ 增量更新失败，回退到全量分析: {e}")
            return self.analyze_contributors_ultra_fast(file_list, months, force_incremental=True)
    
    def _get_changed_files_since_cache(self, cache_timestamp):
        """获取自缓存时间以来变更的文件"""
        try:
            # 转换时间戳为日期
            cache_date = datetime.fromtimestamp(cache_timestamp).strftime("%Y-%m-%d %H:%M:%S")
            
            # 获取自指定时间以来的变更文件
            cmd = f'git log --since="{cache_date}" --name-only --format="" | sort -u'
            result = subprocess.run(
                cmd, shell=True, cwd=self.repo_path,
                capture_output=True, text=True, check=False
            )
            
            if result.stdout:
                changed_files = [f.strip() for f in result.stdout.split('\n') if f.strip()]
                return changed_files
            else:
                return []
                
        except Exception as e:
            print(f"⚠️ 获取变更文件失败: {e}")
            return []
    
    def _incremental_analysis(self, file_list, since_date):
        """增量分析 - 只分析指定文件"""
        if not file_list:
            return {'file_contributors': {}, 'author_activity': {}}
        
        print(f"   🔍 增量分析 {len(file_list)} 个文件...")
        
        # 构建只针对这些文件的Git命令
        files_arg = " ".join([f'"{path}"' for path in file_list])
        cmd = f'git log --since="{since_date}" --format="COMMIT:%H|%an|%ct" --name-only -- {files_arg}'
        
        result = subprocess.run(
            cmd, shell=True, cwd=self.repo_path,
            capture_output=True, text=True, check=True
        )
        
        # 解析结果（使用与全局分析相同的逻辑）
        file_contributors = defaultdict(lambda: defaultdict(int))
        author_activity = defaultdict(int)
        
        lines = result.stdout.strip().split('\n')
        current_commit = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('COMMIT:'):
                parts = line[7:].split('|', 2)
                if len(parts) >= 2:
                    commit_hash, author = parts[0], parts[1]
                    current_commit = {'author': author}
                    author_activity[author] += 1
            elif current_commit and line and not line.startswith('COMMIT:'):
                if line in file_list:  # 只处理我们关心的文件
                    author = current_commit['author']
                    file_contributors[line][author] += 1
        
        return {
            'file_contributors': dict(file_contributors),
            'author_activity': dict(author_activity)
        }
    
    def _global_analysis(self, since_date):
        """一次性全局分析 - 核心优化"""
        print("📊 执行全局分析...")
        start = time.time()
        
        # 单个Git命令获取所有需要的信息
        cmd = f'git log --since="{since_date}" --format="COMMIT:%H|%an|%ct" --name-only'
        
        result = subprocess.run(
            cmd, shell=True, cwd=self.repo_path, 
            capture_output=True, text=True, check=True
        )
        
        print(f"   Git查询耗时: {time.time() - start:.3f}s")
        
        # 解析结果
        parse_start = time.time()
        commits = {}
        file_contributors = defaultdict(lambda: defaultdict(int))
        author_activity = defaultdict(int)
        
        lines = result.stdout.strip().split('\n')
        current_commit = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('COMMIT:'):
                # 解析提交信息: COMMIT:hash|author|timestamp
                parts = line[7:].split('|', 2)
                if len(parts) >= 2:
                    commit_hash, author = parts[0], parts[1]
                    timestamp = int(parts[2]) if len(parts) > 2 else int(time.time())
                    current_commit = {
                        'hash': commit_hash,
                        'author': author, 
                        'timestamp': timestamp
                    }
                    author_activity[author] += 1
            elif current_commit and line and not line.startswith('COMMIT:'):
                # 这是一个文件路径
                author = current_commit['author']
                file_contributors[line][author] += 1
        
        print(f"   数据解析耗时: {time.time() - parse_start:.3f}s")
        print(f"   发现 {len(file_contributors)} 个文件, {len(author_activity)} 个作者")
        
        return {
            'file_contributors': dict(file_contributors),
            'author_activity': dict(author_activity),
            'timestamp': time.time()
        }
    
    def _intelligent_assignment(self, global_data, file_list):
        """智能分配策略"""
        print("🧠 执行智能分配...")
        
        file_contributors = global_data['file_contributors']
        author_activity = global_data['author_activity']
        
        results = {}
        direct_hits = 0
        fallback_assignments = 0
        
        for file_path in file_list:
            if file_path in file_contributors:
                # 直接命中
                contributors = file_contributors[file_path]
                results[file_path] = contributors
                direct_hits += 1
            else:
                # 智能推断
                assigned = self._smart_fallback(file_path, file_contributors, author_activity)
                results[file_path] = assigned
                fallback_assignments += 1
        
        print(f"   直接命中: {direct_hits}, 智能推断: {fallback_assignments}")
        return results
    
    def _smart_fallback(self, file_path, file_contributors, author_activity):
        """增强的智能回退分配策略"""
        # 1. 精确目录匹配（包括父目录）
        dir_path = '/'.join(file_path.split('/')[:-1])
        if dir_path:
            # 尝试完全匹配的目录
            exact_dir_matches = defaultdict(int)
            for fp, contributors in file_contributors.items():
                fp_dir = '/'.join(fp.split('/')[:-1])
                if fp_dir == dir_path:
                    for author, count in contributors.items():
                        exact_dir_matches[author] += count * 3  # 完全匹配权重更高
            
            # 尝试父目录匹配
            parent_dir_matches = defaultdict(int)
            for fp, contributors in file_contributors.items():
                if fp.startswith(dir_path + '/'):
                    for author, count in contributors.items():
                        parent_dir_matches[author] += count
                        
            # 合并目录匹配结果
            combined_dir_matches = defaultdict(int)
            for author, count in exact_dir_matches.items():
                combined_dir_matches[author] += count
            for author, count in parent_dir_matches.items():
                combined_dir_matches[author] += count
                
            if combined_dir_matches:
                return dict(combined_dir_matches)
        
        # 2. 增强的扩展名匹配
        file_ext = file_path.split('.')[-1] if '.' in file_path else ''
        if file_ext:
            ext_matches = defaultdict(int)
            similar_ext_matches = defaultdict(int)
            
            # 相关扩展名组
            ext_groups = {
                'py': ['py', 'pyw', 'pyi'],
                'js': ['js', 'jsx', 'ts', 'tsx'], 
                'cpp': ['cpp', 'c', 'cc', 'cxx'],
                'h': ['h', 'hpp', 'hxx'],
                'md': ['md', 'txt', 'rst'],
                'json': ['json', 'yaml', 'yml'],
            }
            
            # 查找当前扩展名组
            current_group = [file_ext]
            for group_key, extensions in ext_groups.items():
                if file_ext in extensions:
                    current_group = extensions
                    break
            
            for fp, contributors in file_contributors.items():
                fp_ext = fp.split('.')[-1] if '.' in fp else ''
                if fp_ext == file_ext:
                    # 完全匹配扩展名
                    for author, count in contributors.items():
                        ext_matches[author] += count * 2
                elif fp_ext in current_group:
                    # 相关扩展名匹配
                    for author, count in contributors.items():
                        similar_ext_matches[author] += count
                        
            # 合并扩展名结果
            combined_ext_matches = defaultdict(int)
            for author, count in ext_matches.items():
                combined_ext_matches[author] += count
            for author, count in similar_ext_matches.items():
                combined_ext_matches[author] += count
                
            if combined_ext_matches:
                return dict(combined_ext_matches)
        
        # 3. 文件名模式匹配
        file_name = file_path.split('/')[-1].lower()
        name_matches = defaultdict(int)
        
        for fp, contributors in file_contributors.items():
            fp_name = fp.split('/')[-1].lower()
            
            # 检查相似的文件名模式
            similarity_score = 0
            if file_name.startswith(fp_name[:3]) or fp_name.startswith(file_name[:3]):
                similarity_score += 1
            
            # 检查关键词匹配
            keywords = ['test', 'main', 'config', 'utils', 'helper', 'core']
            for keyword in keywords:
                if keyword in file_name and keyword in fp_name:
                    similarity_score += 2
                    
            if similarity_score > 0:
                for author, count in contributors.items():
                    name_matches[author] += count * similarity_score
                    
        if name_matches:
            return dict(name_matches)
        
        # 4. 使用加权的全局活跃作者
        if author_activity:
            # 不只是最活跃的作者，而是按活跃度分配权重
            total_activity = sum(author_activity.values())
            weighted_authors = {}
            
            for author, activity in author_activity.items():
                # 按活跃度比例分配权重
                weight = max(1, int(activity * 5 / total_activity))
                weighted_authors[author] = weight
                
            return weighted_authors
        
        return {}
    
    def _extract_file_results(self, cached_data, file_list):
        """从缓存数据提取文件结果"""
        file_contributors = cached_data['file_contributors']
        author_activity = cached_data['author_activity']
        
        results = {}
        for file_path in file_list:
            if file_path in file_contributors:
                results[file_path] = file_contributors[file_path]
            else:
                results[file_path] = self._smart_fallback(
                    file_path, file_contributors, author_activity
                )
        return results
    
    def _is_cache_valid(self):
        """检查缓存是否有效"""
        if not self.cache_file.exists():
            return False
            
        try:
            with open(self.cache_file, 'r') as f:
                data = json.load(f)
            
            cache_time = data.get('timestamp', 0)
            age_hours = (time.time() - cache_time) / 3600
            
            return age_hours < self.cache_expiry_hours
        except:
            return False
    
    def _load_cache(self):
        """加载缓存数据"""
        with open(self.cache_file, 'r') as f:
            return json.load(f)
    
    def _save_cache(self, data):
        """保存缓存数据"""
        self.cache_file.parent.mkdir(exist_ok=True)
        with open(self.cache_file, 'w') as f:
            json.dump(data, f, indent=2)


# 性能测试函数
def performance_comparison_test():
    """性能对比测试"""
    from core.optimized_contributor_analyzer import OptimizedContributorAnalyzer
    from core.git_operations import GitOperations
    
    # 获取测试文件列表
    import glob
    test_files = glob.glob("**/*.py", recursive=True)[:50]  # 测试50个文件
    
    print(f"🧪 性能对比测试 - {len(test_files)} 个文件")
    
    # 1. 传统方法
    git_ops = GitOperations()
    traditional = OptimizedContributorAnalyzer(git_ops)
    
    print("\n📊 传统优化方法:")
    start = time.time()
    traditional_results = traditional.analyze_contributors_batch(test_files)
    traditional_time = time.time() - start
    print(f"传统方法耗时: {traditional_time:.3f}s")
    
    # 2. 超高速方法
    print("\n🚀 超高速方法:")
    ultra = UltraFastAnalyzer()
    start = time.time()
    ultra_results = ultra.analyze_contributors_ultra_fast(test_files)
    ultra_time = time.time() - start
    print(f"超高速方法耗时: {ultra_time:.3f}s")
    
    # 3. 性能对比
    if traditional_time > 0:
        speedup = traditional_time / ultra_time
        print(f"\n⚡ 性能提升: {speedup:.1f}倍")
        print(f"💡 效率对比: {traditional_time/len(test_files)*1000:.1f}ms vs {ultra_time/len(test_files)*1000:.1f}ms 每文件")


if __name__ == "__main__":
    performance_comparison_test()