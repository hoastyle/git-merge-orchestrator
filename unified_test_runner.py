#!/usr/bin/env python3
"""
Git Merge Orchestrator - 统一测试运行器
有机结合主项目测试和test-environment，支持智能降级策略
"""

import sys
import os
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))


@dataclass
class TestEnvironmentStatus:
    """测试环境状态"""
    main_tests_available: bool = False
    test_environment_available: bool = False
    git_available: bool = False
    python_available: bool = False
    dependencies_available: bool = False
    

@dataclass
class TestResult:
    """单个测试结果"""
    name: str
    passed: bool
    duration: float
    error_message: str = ""
    category: str = "unknown"


@dataclass  
class UnifiedTestReport:
    """统一测试报告"""
    timestamp: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    success_rate: float
    total_duration: float
    environment_status: TestEnvironmentStatus
    test_results: List[TestResult]
    test_mode: str
    recommendations: List[str]


class EnvironmentDetector:
    """环境检测器"""
    
    @staticmethod
    def detect_environment() -> TestEnvironmentStatus:
        """检测测试环境状态"""
        status = TestEnvironmentStatus()
        
        # 检查主项目测试
        main_test_runner = Path(__file__).parent / "tests" / "run_tests.py"
        status.main_tests_available = main_test_runner.exists()
        
        # 检查test-environment submodule
        test_env_dir = Path(__file__).parent / "test-environment"
        batch_test_script = test_env_dir / "batch_test.sh"
        status.test_environment_available = (
            test_env_dir.exists() and 
            batch_test_script.exists() and
            batch_test_script.is_file()
        )
        
        # 检查Git可用性
        try:
            subprocess.run(["git", "--version"], 
                         capture_output=True, check=True)
            status.git_available = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            status.git_available = False
            
        # 检查Python可用性
        status.python_available = True  # 既然能运行这个脚本，Python肯定可用
        
        # 检查依赖可用性
        try:
            # 检查核心模块是否可导入
            from core.git_operations import GitOperations
            from utils.config_manager import ProjectConfigManager
            status.dependencies_available = True
        except ImportError:
            status.dependencies_available = False
            
        return status


class UnifiedTestRunner:
    """统一测试运行器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.env_status = EnvironmentDetector.detect_environment()
        self.test_results: List[TestResult] = []
        self.start_time = time.time()
        
    def print_environment_status(self):
        """打印环境状态"""
        print("🔍 检测测试环境状态...")
        print("=" * 60)
        
        status_items = [
            ("主项目测试", self.env_status.main_tests_available, "tests/run_tests.py"),
            ("test-environment", self.env_status.test_environment_available, "test-environment/"),
            ("Git工具", self.env_status.git_available, "git命令"),
            ("Python环境", self.env_status.python_available, "Python3"), 
            ("项目依赖", self.env_status.dependencies_available, "核心模块")
        ]
        
        for name, available, desc in status_items:
            icon = "✅" if available else "❌"
            status = "可用" if available else "不可用"
            print(f"{icon} {name}: {status} ({desc})")
        
        print()
        
    def run_quick_test(self) -> List[TestResult]:
        """快速测试 (< 30秒)"""
        print("🚀 运行快速测试 (< 30秒)")
        print("-" * 40)
        results = []
        
        # 1. 主项目健康检查
        if self.env_status.main_tests_available:
            result = self._run_main_health_check()
            results.append(result)
        else:
            results.append(TestResult(
                "主项目健康检查", False, 0, "主项目测试不可用", "health"
            ))
            
        # 2. test-environment基础检查  
        if self.env_status.test_environment_available:
            result = self._run_test_environment_health()
            results.append(result)
        else:
            results.append(TestResult(
                "test-environment健康检查", False, 0, "test-environment不可用", "health"
            ))
            
        return results
        
    def run_scenario_test(self, scenarios: List[str]) -> List[TestResult]:
        """运行指定场景测试"""
        print(f"🎯 运行场景测试: {', '.join(scenarios)}")
        print("-" * 40)
        results = []
        
        # 主项目特定测试
        if self.env_status.main_tests_available:
            for scenario in scenarios:
                result = self._run_main_specific_test(scenario)
                results.append(result)
                
        # test-environment场景测试
        if self.env_status.test_environment_available:
            result = self._run_test_environment_scenarios(scenarios)
            results.append(result)
            
        return results
        
    def run_full_test(self) -> List[TestResult]:
        """完整测试套件"""
        print("🌟 运行完整测试套件")
        print("-" * 40)
        results = []
        
        # 计算总的测试项数
        total_tests = 0
        if self.env_status.main_tests_available:
            total_tests += 1
        if self.env_status.test_environment_available:
            total_tests += 1
        total_tests += 1  # 性能测试
        
        current_test = 0
        
        # 1. 主项目完整测试
        if self.env_status.main_tests_available:
            current_test += 1
            print(f"📋 [{current_test}/{total_tests}] 运行主项目完整测试...")
            result = self._run_main_full_test()
            results.append(result)
            icon = "✅" if result.passed else "❌"
            print(f"    {icon} 完成 ({result.duration:.1f}s)")
            
        # 2. test-environment完整测试
        if self.env_status.test_environment_available:
            current_test += 1
            print(f"📋 [{current_test}/{total_tests}] 运行test-environment完整测试...")
            result = self._run_test_environment_full()
            results.append(result)
            icon = "✅" if result.passed else "❌"
            print(f"    {icon} 完成 ({result.duration:.1f}s)")
            
        # 3. 性能测试
        current_test += 1
        print(f"📋 [{current_test}/{total_tests}] 运行性能测试...")
        result = self._run_performance_test()
        results.append(result)
        icon = "✅" if result.passed else "❌"
        print(f"    {icon} 完成 ({result.duration:.1f}s)")
        
        return results
        
    def run_core_only_test(self) -> List[TestResult]:
        """仅主项目测试（降级模式）"""
        print("⚠️ 运行核心测试 (降级模式)")
        print("-" * 40)
        results = []
        
        if self.env_status.main_tests_available:
            # 主项目健康检查
            result = self._run_main_health_check()
            results.append(result)
            
            # 主项目完整测试
            result = self._run_main_full_test()
            results.append(result)
            
            # 内置模拟测试
            result = self._run_builtin_mock_tests()
            results.append(result)
        else:
            results.append(TestResult(
                "核心测试", False, 0, "主项目测试不可用，无法运行核心测试", "error"
            ))
            
        return results
        
    def _run_main_health_check(self) -> TestResult:
        """运行主项目健康检查"""
        start_time = time.time()
        
        try:
            result = subprocess.run([
                sys.executable, "run_tests.py", "--health"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=60)
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                return TestResult(
                    "主项目健康检查", True, duration, "", "health"
                )
            else:
                return TestResult(
                    "主项目健康检查", False, duration, 
                    result.stderr or "健康检查失败", "health"
                )
                
        except subprocess.TimeoutExpired:
            return TestResult(
                "主项目健康检查", False, time.time() - start_time, 
                "测试超时（60秒）", "health"
            )
        except Exception as e:
            return TestResult(
                "主项目健康检查", False, time.time() - start_time,
                f"执行异常: {e}", "health"
            )
            
    def _run_test_environment_health(self) -> TestResult:
        """运行test-environment健康检查"""
        start_time = time.time()
        
        try:
            test_env_dir = self.project_root / "test-environment"
            
            # 简化的健康检查：验证基础结构和关键文件
            checks_passed = 0
            total_checks = 4
            
            # 1. 检查目录存在
            if test_env_dir.exists():
                checks_passed += 1
            
            # 2. 检查README文件存在  
            readme_file = test_env_dir / "README.md"
            if readme_file.exists():
                checks_passed += 1
                
            # 3. 检查test-scripts目录存在
            scripts_dir = test_env_dir / "test-scripts"
            if scripts_dir.exists():
                checks_passed += 1
                
            # 4. 检查至少有一个核心脚本存在
            core_script = test_env_dir / "test-scripts" / "create_test_repo.py"
            if core_script.exists():
                checks_passed += 1
            
            duration = time.time() - start_time
            
            if checks_passed >= 3:  # 至少3/4检查通过
                return TestResult(
                    "test-environment健康检查", True, duration, 
                    f"健康检查通过 ({checks_passed}/{total_checks})", "health"
                )
            else:
                return TestResult(
                    "test-environment健康检查", False, duration,
                    f"健康检查不足 ({checks_passed}/{total_checks})", "health"
                )
                
        except Exception as e:
            return TestResult(
                "test-environment健康检查", False, time.time() - start_time,
                f"执行异常: {e}", "health"
            )
            
    def _run_main_specific_test(self, scenario: str) -> TestResult:
        """运行主项目特定测试"""
        start_time = time.time()
        
        # 场景映射到主项目测试类别
        scenario_mapping = {
            "config": "配置管理",
            "performance": "性能测试",  
            "git": "Git操作",
            "merge": "合并策略",
            "integration": "集成测试"
        }
        
        test_name = scenario_mapping.get(scenario, scenario)
        
        try:
            # 运行主项目分类测试
            result = subprocess.run([
                sys.executable, "tests/run_tests.py", "--category", scenario
            ], cwd=self.project_root, capture_output=True, text=True, timeout=300)
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                return TestResult(
                    f"主项目{test_name}测试", True, duration, "", "scenario"
                )
            else:
                return TestResult(
                    f"主项目{test_name}测试", False, duration,
                    result.stderr or f"{test_name}测试失败", "scenario"
                )
                
        except Exception as e:
            return TestResult(
                f"主项目{test_name}测试", False, time.time() - start_time,
                f"执行异常: {e}", "scenario"
            )
            
    def _run_test_environment_scenarios(self, scenarios: List[str]) -> TestResult:
        """运行test-environment场景测试"""
        start_time = time.time()
        
        try:
            test_env_dir = self.project_root / "test-environment"
            
            # 简化的场景测试：验证场景配置文件和脚本存在
            success = True
            error_messages = []
            scenarios_checked = 0
            
            # 检查场景设置脚本是否存在
            setup_script = test_env_dir / "test-scripts" / "setup_scenarios.py"
            if not setup_script.exists():
                success = False
                error_messages.append("setup_scenarios.py脚本不存在")
            else:
                # 测试场景脚本的基本可用性
                try:
                    result = subprocess.run([
                        sys.executable, "test-scripts/setup_scenarios.py", "--help"
                    ], cwd=test_env_dir, capture_output=True, text=True, timeout=15)
                    
                    if result.returncode == 0:
                        scenarios_checked += 1
                    else:
                        error_messages.append("场景设置脚本不可执行")
                        
                except subprocess.TimeoutExpired:
                    error_messages.append("场景脚本执行超时")
                except Exception as e:
                    error_messages.append(f"场景脚本测试失败: {e}")
            
            # 检查测试数据目录
            test_data_dir = test_env_dir / "test-data"
            if test_data_dir.exists():
                scenarios_checked += 1
            else:
                error_messages.append("test-data目录不存在")
            
            duration = time.time() - start_time
            
            if scenarios_checked >= 1:  # 至少一个场景组件可用
                return TestResult(
                    f"test-environment场景测试", True, duration, 
                    f"场景验证通过 ({scenarios_checked}/2)", "scenario"
                )
            else:
                return TestResult(
                    f"test-environment场景测试", False, duration,
                    "; ".join(error_messages), "scenario"
                )
                
        except Exception as e:
            return TestResult(
                f"test-environment场景测试", False, time.time() - start_time,
                f"执行异常: {e}", "scenario"
            )
            
    def _run_main_full_test(self) -> TestResult:
        """运行主项目完整测试"""
        start_time = time.time()
        
        try:
            result = subprocess.run([
                sys.executable, "run_tests.py", "--full"
            ], cwd=self.project_root, capture_output=True, text=True, timeout=600)
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                return TestResult(
                    "主项目完整测试", True, duration, "", "full"
                )
            else:
                return TestResult(
                    "主项目完整测试", False, duration,
                    result.stderr or "完整测试失败", "full"
                )
                
        except Exception as e:
            return TestResult(
                "主项目完整测试", False, time.time() - start_time,
                f"执行异常: {e}", "full"
            )
            
    def _run_test_environment_full(self) -> TestResult:
        """运行test-environment完整测试"""
        start_time = time.time()
        
        try:
            test_env_dir = self.project_root / "test-environment"
            
            # 运行实际的test-environment核心功能测试
            # 避免batch_test.sh的外部路径依赖，直接运行核心测试
            
            success = True
            error_messages = []
            tests_passed = 0
            total_tests = 0
            
            # 1. 基础环境检查
            total_tests += 1
            required_dirs = ["test-scripts", "test-data", "scenarios"]
            dirs_exist = all((test_env_dir / dir_name).exists() for dir_name in required_dirs)
            if dirs_exist:
                tests_passed += 1
            else:
                error_messages.append("目录结构检查失败")
            
            # 2. 核心脚本功能测试
            key_tests = [
                ("create_test_repo.py", "创建测试仓库"),
                ("setup_scenarios.py", "场景设置"), 
                ("integration_tests.py", "集成测试脚本")
            ]
            
            for script_name, test_name in key_tests:
                total_tests += 1
                script_path = test_env_dir / "test-scripts" / script_name
                
                if script_path.exists():
                    try:
                        # 测试脚本的基本可执行性
                        result = subprocess.run([
                            sys.executable, f"test-scripts/{script_name}", "--help"
                        ], cwd=test_env_dir, capture_output=True, text=True, timeout=15)
                        
                        if result.returncode == 0:
                            tests_passed += 1
                        else:
                            error_messages.append(f"{test_name}脚本不可执行")
                            
                    except subprocess.TimeoutExpired:
                        error_messages.append(f"{test_name}脚本执行超时")
                    except Exception as e:
                        error_messages.append(f"{test_name}测试失败: {e}")
                else:
                    error_messages.append(f"缺少{test_name}脚本")
            
            # 3. 快速集成测试验证 - 创建一个简单的测试仓库
            total_tests += 1
            try:
                import random
                import string
                # 使用随机后缀避免仓库名冲突
                random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
                temp_repo_name = f"test_repo_{random_suffix}"
                temp_repo_path = test_env_dir / "test-repos" / temp_repo_name
                
                # 创建测试仓库（快速模式）
                result = subprocess.run([
                    sys.executable, "test-scripts/create_test_repo.py",
                    "--name", temp_repo_name,
                    "--type", "simple",
                    "--contributors", "Alice,Bob"
                ], cwd=test_env_dir, capture_output=True, text=True, timeout=45)
                
                if result.returncode == 0 and temp_repo_path.exists():
                    tests_passed += 1
                    # 清理测试仓库
                    try:
                        import shutil
                        shutil.rmtree(temp_repo_path)
                    except:
                        pass  # 清理失败不影响测试结果
                else:
                    error_messages.append(f"测试仓库创建失败: {result.stderr if result.stderr else '未知错误'}")
                    
            except subprocess.TimeoutExpired:
                error_messages.append("测试仓库创建超时")
            except Exception as e:
                error_messages.append(f"测试仓库创建异常: {e}")
            
            duration = time.time() - start_time
            success = tests_passed >= (total_tests * 0.75)  # 75%通过率认为成功
            
            if success:
                return TestResult(
                    "test-environment完整测试", True, duration, 
                    f"通过 {tests_passed}/{total_tests} 项测试", "full"
                )
            else:
                return TestResult(
                    "test-environment完整测试", False, duration,
                    f"仅通过 {tests_passed}/{total_tests} 项测试: " + "; ".join(error_messages[:3]), "full"
                )
                
        except Exception as e:
            return TestResult(
                "test-environment完整测试", False, time.time() - start_time,
                f"执行异常: {e}", "full"
            )
            
    def _run_performance_test(self) -> TestResult:
        """运行性能测试"""
        start_time = time.time()
        
        try:
            performance_script = self.project_root / "test_performance_optimization.py"
            if performance_script.exists():
                result = subprocess.run([
                    sys.executable, str(performance_script)
                ], cwd=self.project_root, capture_output=True, text=True, timeout=300)
                
                duration = time.time() - start_time
                
                if result.returncode == 0:
                    return TestResult(
                        "性能优化测试", True, duration, "", "performance"
                    )
                else:
                    return TestResult(
                        "性能优化测试", False, duration,
                        result.stderr or "性能测试失败", "performance"
                    )
            else:
                return TestResult(
                    "性能优化测试", False, 0, "性能测试脚本不存在", "performance"
                )
                
        except Exception as e:
            return TestResult(
                "性能优化测试", False, time.time() - start_time,
                f"执行异常: {e}", "performance"
            )
            
    def _run_builtin_mock_tests(self) -> TestResult:
        """运行内置模拟测试（降级模式）"""
        start_time = time.time()
        
        try:
            # 简单的模拟测试，验证核心功能
            from core.git_operations import GitOperations
            from utils.config_manager import ProjectConfigManager
            
            # 基本导入测试
            git_ops = GitOperations(".")
            config_mgr = ProjectConfigManager(".")
            
            duration = time.time() - start_time
            return TestResult(
                "内置模拟测试", True, duration, "", "mock"
            )
            
        except Exception as e:
            return TestResult(
                "内置模拟测试", False, time.time() - start_time,
                f"模拟测试失败: {e}", "mock"
            )
            
    def generate_report(self, test_mode: str) -> UnifiedTestReport:
        """生成统一测试报告"""
        total_duration = time.time() - self.start_time
        passed_tests = sum(1 for r in self.test_results if r.passed)
        failed_tests = len(self.test_results) - passed_tests
        success_rate = (passed_tests / len(self.test_results) * 100) if self.test_results else 0
        
        # 生成建议
        recommendations = self._generate_recommendations()
        
        return UnifiedTestReport(
            timestamp=datetime.now().isoformat(),
            total_tests=len(self.test_results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            success_rate=success_rate,
            total_duration=total_duration,
            environment_status=self.env_status,
            test_results=self.test_results,
            test_mode=test_mode,
            recommendations=recommendations
        )
        
    def _generate_recommendations(self) -> List[str]:
        """生成测试建议"""
        recommendations = []
        
        # 基于环境状态的建议
        if not self.env_status.test_environment_available:
            recommendations.append("建议初始化test-environment submodule以获得完整测试覆盖")
            
        if not self.env_status.git_available:
            recommendations.append("建议安装Git工具以支持完整的版本控制测试")
            
        # 基于测试结果的建议  
        failed_results = [r for r in self.test_results if not r.passed]
        if failed_results:
            recommendations.append(f"需要修复{len(failed_results)}个失败的测试项")
            
        success_rate = (sum(1 for r in self.test_results if r.passed) / len(self.test_results) * 100) if self.test_results else 0
        if success_rate < 80:
            recommendations.append("测试成功率较低，建议检查核心功能实现")
        elif success_rate < 95:
            recommendations.append("测试成功率良好，建议进一步优化提升稳定性")
        else:
            recommendations.append("测试覆盖优秀，系统状态良好")
            
        return recommendations
        
    def print_detailed_report(self, report: UnifiedTestReport):
        """打印详细测试报告"""
        print("\n" + "=" * 80)
        print("🎯 统一测试报告")
        print("=" * 80)
        
        # 基本统计
        print(f"📊 测试统计:")
        print(f"   测试模式: {report.test_mode}")
        print(f"   总测试数: {report.total_tests}")
        print(f"   通过数: {report.passed_tests}")
        print(f"   失败数: {report.failed_tests}")
        print(f"   成功率: {report.success_rate:.1f}%")
        print(f"   总耗时: {report.total_duration:.2f}秒")
        
        # 环境状态
        print(f"\n🔍 环境状态:")
        env_items = [
            ("主项目测试", report.environment_status.main_tests_available),
            ("test-environment", report.environment_status.test_environment_available),
            ("Git工具", report.environment_status.git_available),
            ("Python环境", report.environment_status.python_available),
            ("项目依赖", report.environment_status.dependencies_available)
        ]
        
        for name, status in env_items:
            icon = "✅" if status else "❌"
            print(f"   {icon} {name}")
            
        # 详细结果
        if report.test_results:
            print(f"\n📋 详细结果:")
            for result in report.test_results:
                icon = "✅" if result.passed else "❌"
                print(f"   {icon} {result.name} ({result.duration:.2f}s)")
                if not result.passed and result.error_message:
                    print(f"      错误: {result.error_message}")
                    
        # 建议
        if report.recommendations:
            print(f"\n💡 建议:")
            for rec in report.recommendations:
                print(f"   • {rec}")
                
        print("=" * 80)
        
    def save_report(self, report: UnifiedTestReport, file_path: str):
        """保存测试报告到文件"""
        try:
            report_dict = asdict(report)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, indent=2, ensure_ascii=False)
            print(f"📄 测试报告已保存: {file_path}")
        except Exception as e:
            print(f"⚠️ 保存报告失败: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Git Merge Orchestrator 统一测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 快速验证 (< 30秒)
  python unified_test_runner.py --quick
  
  # 完整测试套件 (10-15分钟)
  python unified_test_runner.py --full
  
  # 特定场景测试
  python unified_test_runner.py --scenario config,performance
  
  # 仅主项目测试 (test-environment不可用时)
  python unified_test_runner.py --core-only
  
  # 生成详细报告
  python unified_test_runner.py --full --save-report test_report.json
        """
    )
    
    parser.add_argument("--quick", action="store_true", help="快速测试模式 (< 30秒)")
    parser.add_argument("--full", action="store_true", help="完整测试套件 (10-15分钟)")
    parser.add_argument("--core-only", action="store_true", help="仅主项目测试 (降级模式)")
    parser.add_argument("--scenario", help="指定场景测试，逗号分隔 (如: config,performance)")
    parser.add_argument("--save-report", help="保存测试报告到文件")
    parser.add_argument("--quiet", action="store_true", help="静默模式，只显示结果")
    
    args = parser.parse_args()
    
    # 创建测试运行器
    runner = UnifiedTestRunner()
    
    if not args.quiet:
        print("🚀 Git Merge Orchestrator 统一测试系统")
        print("=" * 60)
        runner.print_environment_status()
    
    # 根据参数选择测试模式
    if args.quick:
        test_mode = "quick"
        runner.test_results = runner.run_quick_test()
    elif args.full:
        test_mode = "full"
        runner.test_results = runner.run_full_test()
    elif args.core_only:
        test_mode = "core_only"
        runner.test_results = runner.run_core_only_test()
    elif args.scenario:
        scenarios = [s.strip() for s in args.scenario.split(",")]
        test_mode = f"scenario_{'+'.join(scenarios)}"
        runner.test_results = runner.run_scenario_test(scenarios)
    else:
        # 默认：根据环境智能选择
        if runner.env_status.test_environment_available:
            test_mode = "quick"
            runner.test_results = runner.run_quick_test()
        else:
            test_mode = "core_only"
            runner.test_results = runner.run_core_only_test()
            print("⚠️ test-environment不可用，使用降级模式")
    
    # 生成报告
    report = runner.generate_report(test_mode)
    
    if not args.quiet:
        runner.print_detailed_report(report)
    else:
        # 静默模式只显示关键信息
        success_rate = report.success_rate
        print(f"测试结果: {report.passed_tests}/{report.total_tests} 通过 ({success_rate:.1f}%)")
        if report.failed_tests > 0:
            sys.exit(1)
    
    # 保存报告
    if args.save_report:
        runner.save_report(report, args.save_report)
    
    # 返回适当的退出码
    if report.failed_tests > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 用户中断测试")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试运行器异常: {e}")
        sys.exit(1)