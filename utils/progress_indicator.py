"""
Git Merge Orchestrator - 进度指示器工具
为长时间运行的操作提供用户友好的进度反馈
"""

import time
import sys
import threading
from typing import Optional, Callable, Any
from datetime import datetime


class ProgressIndicator:
    """进度指示器类 - 支持多种进度显示模式"""

    def __init__(self, message: str = "处理中", show_spinner: bool = True):
        self.message = message
        self.show_spinner = show_spinner
        self.is_running = False
        self.spinner_thread: Optional[threading.Thread] = None
        self.start_time: Optional[float] = None

        # 旋转字符
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spinner_index = 0

    def start(self):
        """开始显示进度指示器"""
        if self.is_running:
            return

        self.is_running = True
        self.start_time = time.time()

        if self.show_spinner:
            self.spinner_thread = threading.Thread(target=self._spin)
            self.spinner_thread.daemon = True
            self.spinner_thread.start()
        else:
            print(f"🚀 {self.message}...")

    def stop(
        self, success_message: Optional[str] = None, error_message: Optional[str] = None
    ):
        """停止进度指示器"""
        if not self.is_running:
            return

        self.is_running = False

        if self.spinner_thread and self.spinner_thread.is_alive():
            self.spinner_thread.join(timeout=0.1)

        # 清除旋转字符
        if self.show_spinner:
            sys.stdout.write("\r" + " " * (len(self.message) + 10) + "\r")
            sys.stdout.flush()

        # 显示结果消息
        elapsed_time = time.time() - self.start_time if self.start_time else 0

        if error_message:
            print(f"❌ {error_message} (耗时: {elapsed_time:.1f}秒)")
        elif success_message:
            print(f"✅ {success_message} (耗时: {elapsed_time:.1f}秒)")
        else:
            print(f"✅ {self.message}完成 (耗时: {elapsed_time:.1f}秒)")

    def _spin(self):
        """旋转动画循环"""
        while self.is_running:
            char = self.spinner_chars[self.spinner_index]
            elapsed = time.time() - self.start_time if self.start_time else 0

            # 显示旋转字符和经过时间
            display_text = f"\r{char} {self.message}... ({elapsed:.1f}s)"
            sys.stdout.write(display_text)
            sys.stdout.flush()

            self.spinner_index = (self.spinner_index + 1) % len(self.spinner_chars)
            time.sleep(0.1)

    def update_message(self, new_message: str):
        """更新进度消息"""
        self.message = new_message


class ProgressTracker:
    """进度跟踪器 - 支持分步骤和百分比进度"""

    def __init__(self, total_steps: int, description: str = "处理"):
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.start_time = time.time()
        self.step_messages = []

    def step(self, message: str = ""):
        """执行下一步"""
        self.current_step += 1

        # 计算进度百分比
        progress = (self.current_step / self.total_steps) * 100

        # 计算预计剩余时间
        elapsed = time.time() - self.start_time
        if self.current_step > 0:
            avg_time_per_step = elapsed / self.current_step
            remaining_steps = self.total_steps - self.current_step
            eta = avg_time_per_step * remaining_steps
        else:
            eta = 0

        # 显示进度
        progress_bar = self._create_progress_bar(progress)
        step_msg = f" - {message}" if message else ""

        print(
            f"📍 步骤 {self.current_step}/{self.total_steps}: {self.description} "
            f"{progress_bar} {progress:.0f}%{step_msg}"
        )

        if eta > 0 and self.current_step < self.total_steps:
            print(f"   ⏱️ 预计剩余时间: {eta:.1f}秒")

        # 记录步骤信息
        self.step_messages.append(
            {
                "step": self.current_step,
                "message": message,
                "timestamp": datetime.now(),
                "elapsed": elapsed,
            }
        )

    def _create_progress_bar(self, progress: float, width: int = 20) -> str:
        """创建进度条"""
        filled = int((progress / 100) * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"[{bar}]"

    def finish(self, success_message: str = ""):
        """完成进度跟踪"""
        total_time = time.time() - self.start_time
        final_message = success_message or f"{self.description}完成"
        print(f"✅ {final_message} (总耗时: {total_time:.1f}秒)")

        # 显示步骤总结
        if len(self.step_messages) > 1:
            print(f"📊 步骤耗时总结:")
            prev_elapsed = 0
            for step_info in self.step_messages:
                step_time = step_info["elapsed"] - prev_elapsed
                print(
                    f"   步骤{step_info['step']}: {step_time:.1f}s - {step_info['message']}"
                )
                prev_elapsed = step_info["elapsed"]


def with_progress(message: str = "处理中", show_spinner: bool = True):
    """装饰器：为函数添加进度指示器"""

    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs) -> Any:
            progress = ProgressIndicator(message, show_spinner)
            progress.start()

            try:
                result = func(*args, **kwargs)
                progress.stop(f"{message}完成")
                return result
            except Exception as e:
                progress.stop(error_message=f"{message}失败: {str(e)}")
                raise

        return wrapper

    return decorator


class StepProgress:
    """分步骤进度指示器 - 用于复杂的多步骤操作"""

    def __init__(self, steps: list, description: str = "执行"):
        self.steps = steps
        self.description = description
        self.current_index = 0
        self.tracker = ProgressTracker(len(steps), description)

    def next_step(self, custom_message: str = "") -> str:
        """进入下一步"""
        if self.current_index >= len(self.steps):
            return ""

        step_name = self.steps[self.current_index]
        message = custom_message or step_name

        self.tracker.step(message)
        self.current_index += 1

        return step_name

    def finish(self, message: str = ""):
        """完成所有步骤"""
        self.tracker.finish(message)


# 便捷函数
def show_progress(func: Callable, message: str = "处理中", *args, **kwargs) -> Any:
    """为单个函数调用显示进度"""
    progress = ProgressIndicator(message)
    progress.start()

    try:
        result = func(*args, **kwargs)
        progress.stop(f"{message}完成")
        return result
    except Exception as e:
        progress.stop(error_message=f"{message}失败: {str(e)}")
        raise


def run_with_steps(steps_and_functions: list, description: str = "执行任务") -> list:
    """
    运行多个步骤，每个步骤有自己的函数
    
    Args:
        steps_and_functions: [(step_name, function, args, kwargs), ...]
        description: 整体描述
        
    Returns:
        list: 每个步骤的执行结果
    """
    tracker = ProgressTracker(len(steps_and_functions), description)
    results = []

    for step_name, func, args, kwargs in steps_and_functions:
        try:
            tracker.step(step_name)
            result = func(*args, **kwargs)
            results.append(result)
        except Exception as e:
            print(f"❌ 步骤 '{step_name}' 执行失败: {str(e)}")
            raise

    tracker.finish(f"{description}全部完成")
    return results


if __name__ == "__main__":
    # 测试代码
    print("🧪 测试进度指示器...")

    # 测试1: 简单进度指示器
    progress = ProgressIndicator("测试操作")
    progress.start()
    time.sleep(2)
    progress.stop("测试完成")

    print()

    # 测试2: 进度跟踪器
    tracker = ProgressTracker(5, "多步骤测试")
    for i in range(5):
        time.sleep(0.5)
        tracker.step(f"执行步骤 {i+1}")
    tracker.finish("所有步骤完成")

    print()

    # 测试3: 装饰器
    @with_progress("装饰器测试")
    def test_function():
        time.sleep(1)
        return "成功"

    result = test_function()
    print(f"结果: {result}")
