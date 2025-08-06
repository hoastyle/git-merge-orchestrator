"""
Git Merge Orchestrator - 智能缓存管理器
实现LRU缓存和多层缓存策略以优化大型项目性能
"""

import json
import hashlib
import threading
from collections import OrderedDict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Union


class LRUCache:
    """LRU (Least Recently Used) 缓存实现"""

    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache = OrderedDict()
        self.lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            if key in self.cache:
                # 移动到最后（最近使用）
                self.cache.move_to_end(key)
                return self.cache[key]
            return None

    def put(self, key: str, value: Any) -> None:
        """设置缓存值"""
        with self.lock:
            if key in self.cache:
                # 更新现有值
                self.cache.move_to_end(key)
            elif len(self.cache) >= self.capacity:
                # 删除最久未使用的项
                self.cache.popitem(last=False)

            self.cache[key] = value

    def remove(self, key: str) -> bool:
        """移除缓存项"""
        with self.lock:
            return self.cache.pop(key, None) is not None

    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()

    def size(self) -> int:
        """获取缓存大小"""
        with self.lock:
            return len(self.cache)

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        with self.lock:
            return {
                "size": len(self.cache),
                "capacity": self.capacity,
                "usage_rate": len(self.cache) / self.capacity * 100,
            }


class SmartCacheManager:
    """智能缓存管理器 - 多层缓存策略"""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.cache_dir = self.repo_path / ".merge_work" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 多层缓存
        self.memory_cache = LRUCache(1000)  # 内存缓存
        self.file_cache_path = self.cache_dir / "persistent_cache.json"

        # 缓存统计
        self.stats = {
            "hits": 0,
            "misses": 0,
            "puts": 0,
            "memory_hits": 0,
            "file_hits": 0,
        }

        self.lock = threading.Lock()

    def _generate_cache_key(self, namespace: str, identifier: Union[str, Dict]) -> str:
        """生成缓存键"""
        if isinstance(identifier, dict):
            # 对字典进行序列化和哈希
            content = json.dumps(identifier, sort_keys=True)
        else:
            content = str(identifier)

        return f"{namespace}:{hashlib.md5(content.encode()).hexdigest()}"

    def get(
        self, namespace: str, identifier: Union[str, Dict], max_age_hours: int = 24
    ) -> Optional[Any]:
        """获取缓存数据"""
        cache_key = self._generate_cache_key(namespace, identifier)

        # 1. 检查内存缓存
        memory_result = self.memory_cache.get(cache_key)
        if memory_result is not None:
            cache_data, timestamp = memory_result
            if self._is_cache_valid(timestamp, max_age_hours):
                with self.lock:
                    self.stats["hits"] += 1
                    self.stats["memory_hits"] += 1
                return cache_data

        # 2. 检查文件缓存
        file_result = self._get_from_file_cache(cache_key)
        if file_result is not None:
            cache_data, timestamp = file_result
            if self._is_cache_valid(timestamp, max_age_hours):
                # 提升到内存缓存
                self.memory_cache.put(cache_key, (cache_data, timestamp))
                with self.lock:
                    self.stats["hits"] += 1
                    self.stats["file_hits"] += 1
                return cache_data

        # 缓存未命中
        with self.lock:
            self.stats["misses"] += 1
        return None

    def put(self, namespace: str, identifier: Union[str, Dict], data: Any) -> None:
        """存储缓存数据"""
        cache_key = self._generate_cache_key(namespace, identifier)
        timestamp = datetime.now().isoformat()

        # 存储到内存缓存
        self.memory_cache.put(cache_key, (data, timestamp))

        # 异步存储到文件缓存
        self._put_to_file_cache_async(cache_key, data, timestamp)

        with self.lock:
            self.stats["puts"] += 1

    def _is_cache_valid(self, timestamp: str, max_age_hours: int) -> bool:
        """检查缓存是否有效"""
        try:
            cached_time = datetime.fromisoformat(timestamp)
            age = datetime.now() - cached_time
            return age < timedelta(hours=max_age_hours)
        except:
            return False

    def _get_from_file_cache(self, cache_key: str) -> Optional[tuple]:
        """从文件缓存获取数据"""
        try:
            if not self.file_cache_path.exists():
                return None

            with open(self.file_cache_path, "r", encoding="utf-8") as f:
                file_cache = json.load(f)

            if cache_key in file_cache:
                cache_entry = file_cache[cache_key]
                return cache_entry["data"], cache_entry["timestamp"]

        except Exception as e:
            print(f"⚠️ 文件缓存读取失败: {e}")

        return None

    def _put_to_file_cache_async(
        self, cache_key: str, data: Any, timestamp: str
    ) -> None:
        """异步存储到文件缓存"""

        def save_to_file():
            try:
                # 读取现有缓存
                file_cache = {}
                if self.file_cache_path.exists():
                    with open(self.file_cache_path, "r", encoding="utf-8") as f:
                        file_cache = json.load(f)

                # 添加新缓存项
                file_cache[cache_key] = {"data": data, "timestamp": timestamp}

                # 限制文件缓存大小
                if len(file_cache) > 5000:
                    # 删除最旧的缓存项
                    sorted_items = sorted(
                        file_cache.items(), key=lambda x: x[1]["timestamp"]
                    )
                    # 保留最新的4000项
                    file_cache = dict(sorted_items[-4000:])

                # 写回文件
                with open(self.file_cache_path, "w", encoding="utf-8") as f:
                    json.dump(file_cache, f, ensure_ascii=False, indent=2)

            except Exception as e:
                print(f"⚠️ 文件缓存写入失败: {e}")

        # 使用线程异步执行
        import threading

        threading.Thread(target=save_to_file, daemon=True).start()

    def clear_expired(self, max_age_hours: int = 24) -> int:
        """清理过期缓存"""
        cleared_count = 0

        try:
            if not self.file_cache_path.exists():
                return 0

            with open(self.file_cache_path, "r", encoding="utf-8") as f:
                file_cache = json.load(f)

            # 过滤有效缓存
            valid_cache = {}
            for key, entry in file_cache.items():
                if self._is_cache_valid(entry["timestamp"], max_age_hours):
                    valid_cache[key] = entry
                else:
                    cleared_count += 1

            # 写回文件
            with open(self.file_cache_path, "w", encoding="utf-8") as f:
                json.dump(valid_cache, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"⚠️ 清理缓存失败: {e}")

        return cleared_count

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        memory_stats = self.memory_cache.get_stats()

        with self.lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (
                (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            )

            return {
                "total_requests": total_requests,
                "hit_rate": round(hit_rate, 2),
                "memory_cache": memory_stats,
                "stats": dict(self.stats),
            }

    def warm_up_cache(self, file_paths: list, contributor_analyzer) -> None:
        """预热缓存 - 预先计算常用数据"""
        print(f"🔥 开始缓存预热，处理 {len(file_paths)} 个文件...")

        # 分批预热，避免内存占用过大
        batch_size = 100
        warmed_count = 0

        for i in range(0, len(file_paths), batch_size):
            batch_files = file_paths[i : i + batch_size]

            # 预热文件贡献者缓存
            for file_path in batch_files:
                cache_key = f"file_contributors:{file_path}"
                if self.memory_cache.get(cache_key) is None:
                    try:
                        contributors = contributor_analyzer.get_file_contributors(
                            file_path
                        )
                        self.put("file_contributors", file_path, contributors)
                        warmed_count += 1
                    except Exception as e:
                        print(f"⚠️ 预热文件 {file_path} 失败: {e}")

            if i % (batch_size * 5) == 0:  # 每500个文件显示一次进度
                print(
                    f"  🔥 已预热 {min(i + batch_size, len(file_paths))}/{len(file_paths)} 个文件..."
                )

        print(f"✅ 缓存预热完成，成功预热 {warmed_count} 个文件")


# 全局缓存管理器实例
_cache_managers = {}


def get_cache_manager(repo_path: str) -> SmartCacheManager:
    """获取缓存管理器实例（单例模式）"""
    if repo_path not in _cache_managers:
        _cache_managers[repo_path] = SmartCacheManager(repo_path)
    return _cache_managers[repo_path]


if __name__ == "__main__":
    # 测试代码
    cache = SmartCacheManager(".")

    # 测试基本功能
    cache.put("test", "key1", {"data": "value1"})
    result = cache.get("test", "key1")
    print(f"缓存测试结果: {result}")

    # 显示统计信息
    stats = cache.get_stats()
    print(f"缓存统计: {stats}")
