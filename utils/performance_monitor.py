"""
Git Merge Orchestrator - 性能监控模块
提供性能监控装饰器和统计功能
"""

import time
import functools
import logging
from datetime import datetime
from pathlib import Path

# 设置性能日志
performance_logger = logging.getLogger("performance")
performance_logger.setLevel(logging.INFO)

# 创建日志文件处理器
log_file = Path(".merge_work") / "performance.log"
log_file.parent.mkdir(exist_ok=True)

file_handler = logging.FileHandler(log_file)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
performance_logger.addHandler(file_handler)


def performance_monitor(operation_name=None):
    """性能监控装饰器

    使用方法:
    @performance_monitor("分析贡献者")
    def analyze_contributors(self):
        # 你的代码
        pass
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = operation_name or f"{func.__name__}"
            start_time = time.time()

            print(f"⏱️ 开始执行: {func_name}")

            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time

                # 控制台输出
                print(f"⚡ {func_name} 完成，耗时: {elapsed:.2f}秒")

                # 日志记录
                performance_logger.info(f"{func_name} - 耗时: {elapsed:.2f}秒")

                return result

            except Exception as e:
                elapsed = time.time() - start_time
                print(f"❌ {func_name} 执行失败，耗时: {elapsed:.2f}秒，错误: {e}")
                performance_logger.error(f"{func_name} - 失败: {elapsed:.2f}秒 - {str(e)}")
                raise

        return wrapper

    return decorator


def timing_context(operation_name):
    """计时上下文管理器

    使用方法:
    with timing_context("批量分析文件"):
        # 你的代码
        pass
    """

    class TimingContext:
        def __init__(self, name):
            self.name = name
            self.start_time = None

        def __enter__(self):
            self.start_time = time.time()
            print(f"⏱️ 开始: {self.name}")
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            elapsed = time.time() - self.start_time
            if exc_type is None:
                print(f"⚡ {self.name} 完成，耗时: {elapsed:.2f}秒")
                performance_logger.info(f"{self.name} - 耗时: {elapsed:.2f}秒")
            else:
                print(f"❌ {self.name} 失败，耗时: {elapsed:.2f}秒")
                performance_logger.error(f"{self.name} - 失败: {elapsed:.2f}秒")

    return TimingContext(operation_name)


class PerformanceStats:
    """性能统计收集器"""

    def __init__(self):
        self.stats = {}
        self.start_times = {}

    def start_operation(self, operation_name):
        """开始记录操作"""
        self.start_times[operation_name] = time.time()

    def end_operation(self, operation_name, additional_info=None):
        """结束记录操作"""
        if operation_name in self.start_times:
            elapsed = time.time() - self.start_times[operation_name]

            if operation_name not in self.stats:
                self.stats[operation_name] = []

            stats_entry = {"duration": elapsed, "timestamp": datetime.now().isoformat()}

            if additional_info:
                stats_entry.update(additional_info)

            self.stats[operation_name].append(stats_entry)
            del self.start_times[operation_name]

            return elapsed
        return None

    def get_summary(self):
        """获取性能摘要"""
        summary = {}
        for operation, records in self.stats.items():
            durations = [r["duration"] for r in records]
            summary[operation] = {
                "count": len(durations),
                "total_time": sum(durations),
                "avg_time": sum(durations) / len(durations),
                "min_time": min(durations),
                "max_time": max(durations),
            }
        return summary

    def print_summary(self):
        """打印性能摘要"""
        summary = self.get_summary()
        if not summary:
            print("📊 暂无性能数据")
            return

        print("\n📊 性能统计摘要:")
        print("-" * 60)

        for operation, stats in summary.items():
            print(f"🔍 {operation}:")
            print(f"   执行次数: {stats['count']}")
            print(f"   总耗时: {stats['total_time']:.2f}秒")
            print(f"   平均耗时: {stats['avg_time']:.2f}秒")
            print(f"   最快: {stats['min_time']:.2f}秒")
            print(f"   最慢: {stats['max_time']:.2f}秒")
            print()


# 全局性能统计实例
global_performance_stats = PerformanceStats()
