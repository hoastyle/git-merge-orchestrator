"""
Git Merge Orchestrator - 测试配置管理器
负责加载和管理统一测试配置
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TestModeConfig:
    """测试模式配置"""
    description: str
    timeout_seconds: int
    include_categories: List[str]
    parallel_execution: bool
    skip_long_running_tests: bool


@dataclass
class TestCategoryConfig:
    """测试类别配置"""
    description: str
    priority: str
    timeout_seconds: int
    retry_count: int
    tests: List[str]


@dataclass
class ScenarioConfig:
    """场景测试配置"""
    description: str
    main_test_category: str
    test_environment_scenarios: List[str]
    expected_duration_seconds: int


class TestConfigManager:
    """测试配置管理器"""
    
    def __init__(self, config_file_path: Optional[str] = None):
        """初始化配置管理器"""
        self.project_root = Path(__file__).parent.parent
        
        if config_file_path:
            self.config_file = Path(config_file_path)
        else:
            self.config_file = self.project_root / "test_config.json"
            
        self._config = None
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            else:
                # 使用默认配置
                self._config = self._get_default_config()
                print(f"⚠️ 配置文件不存在，使用默认配置: {self.config_file}")
        except Exception as e:
            print(f"❌ 加载配置失败: {e}")
            self._config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "test_modes": {
                "quick": {
                    "description": "快速测试模式",
                    "timeout_seconds": 30,
                    "include_categories": ["health"],
                    "parallel_execution": True,
                    "skip_long_running_tests": True
                },
                "full": {
                    "description": "完整测试套件",
                    "timeout_seconds": 900,
                    "include_categories": ["health", "integration", "performance"],
                    "parallel_execution": False,
                    "skip_long_running_tests": False
                }
            },
            "test_categories": {
                "health": {
                    "description": "健康检查测试",
                    "priority": "high",
                    "timeout_seconds": 60,
                    "retry_count": 1,
                    "tests": ["主项目健康检查", "环境检查"]
                }
            },
            "thresholds": {
                "success_rate": {
                    "excellent": 95.0,
                    "good": 80.0
                }
            }
        }
    
    def get_test_mode_config(self, mode: str) -> Optional[TestModeConfig]:
        """获取测试模式配置"""
        mode_data = self._config.get("test_modes", {}).get(mode)
        if not mode_data:
            return None
            
        return TestModeConfig(
            description=mode_data.get("description", ""),
            timeout_seconds=mode_data.get("timeout_seconds", 300),
            include_categories=mode_data.get("include_categories", []),
            parallel_execution=mode_data.get("parallel_execution", False),
            skip_long_running_tests=mode_data.get("skip_long_running_tests", False)
        )
    
    def get_test_category_config(self, category: str) -> Optional[TestCategoryConfig]:
        """获取测试类别配置"""
        category_data = self._config.get("test_categories", {}).get(category)
        if not category_data:
            return None
            
        return TestCategoryConfig(
            description=category_data.get("description", ""),
            priority=category_data.get("priority", "medium"),
            timeout_seconds=category_data.get("timeout_seconds", 300),
            retry_count=category_data.get("retry_count", 0),
            tests=category_data.get("tests", [])
        )
    
    def get_scenario_config(self, scenario: str) -> Optional[ScenarioConfig]:
        """获取场景配置"""
        scenario_data = self._config.get("scenario_definitions", {}).get(scenario)
        if not scenario_data:
            return None
            
        return ScenarioConfig(
            description=scenario_data.get("description", ""),
            main_test_category=scenario_data.get("main_test_category", ""),
            test_environment_scenarios=scenario_data.get("test_environment_scenarios", []),
            expected_duration_seconds=scenario_data.get("expected_duration_seconds", 300)
        )
    
    def get_available_test_modes(self) -> List[str]:
        """获取可用的测试模式列表"""
        return list(self._config.get("test_modes", {}).keys())
    
    def get_available_test_categories(self) -> List[str]:
        """获取可用的测试类别列表"""
        return list(self._config.get("test_categories", {}).keys())
    
    def get_available_scenarios(self) -> List[str]:
        """获取可用的场景列表"""
        return list(self._config.get("scenario_definitions", {}).keys())
    
    def get_success_rate_threshold(self, level: str = "good") -> float:
        """获取成功率阈值"""
        return self._config.get("thresholds", {}).get("success_rate", {}).get(level, 80.0)
    
    def get_timeout_for_mode(self, mode: str) -> int:
        """获取测试模式的超时时间"""
        mode_config = self.get_test_mode_config(mode)
        return mode_config.timeout_seconds if mode_config else 300
    
    def get_environment_config(self, env_name: str) -> Optional[Dict[str, Any]]:
        """获取环境配置"""
        return self._config.get("test_environments", {}).get(env_name)
    
    def should_retry_on_failure(self, category: str) -> Tuple[bool, int]:
        """检查是否应该重试失败的测试"""
        category_config = self.get_test_category_config(category)
        if category_config:
            return category_config.retry_count > 0, category_config.retry_count
        
        # 默认重试配置
        retry_config = self._config.get("thresholds", {}).get("retry", {})
        max_retries = retry_config.get("max_retries", 0)
        return max_retries > 0, max_retries
    
    def is_parallel_execution_enabled(self, mode: str) -> bool:
        """检查是否启用并行执行"""
        mode_config = self.get_test_mode_config(mode)
        return mode_config.parallel_execution if mode_config else False
    
    def should_skip_long_running_tests(self, mode: str) -> bool:
        """检查是否跳过长时间运行的测试"""
        mode_config = self.get_test_mode_config(mode)
        return mode_config.skip_long_running_tests if mode_config else False
    
    def get_reporting_config(self) -> Dict[str, Any]:
        """获取报告配置"""
        return self._config.get("reporting", {
            "formats": ["text"],
            "default_format": "text",
            "include_environment_info": True
        })
    
    def validate_config(self) -> List[str]:
        """验证配置文件的有效性"""
        issues = []
        
        # 检查必需的节
        required_sections = ["test_modes", "test_categories"]
        for section in required_sections:
            if section not in self._config:
                issues.append(f"缺少必需的配置节: {section}")
        
        # 检查测试模式配置
        test_modes = self._config.get("test_modes", {})
        for mode_name, mode_config in test_modes.items():
            if "include_categories" not in mode_config:
                issues.append(f"测试模式 '{mode_name}' 缺少 include_categories 配置")
            
            # 检查引用的类别是否存在
            categories = mode_config.get("include_categories", [])
            available_categories = self.get_available_test_categories()
            for category in categories:
                if category not in available_categories:
                    issues.append(f"测试模式 '{mode_name}' 引用了不存在的类别 '{category}'")
        
        # 检查超时时间的合理性
        for mode_name, mode_config in test_modes.items():
            timeout = mode_config.get("timeout_seconds", 0)
            if timeout <= 0:
                issues.append(f"测试模式 '{mode_name}' 的超时时间无效: {timeout}")
            elif timeout < 10:
                issues.append(f"测试模式 '{mode_name}' 的超时时间过短: {timeout}s")
        
        return issues
    
    def print_config_summary(self):
        """打印配置摘要"""
        print("📋 测试配置摘要")
        print("=" * 50)
        
        # 测试模式
        print(f"🎯 可用测试模式: {', '.join(self.get_available_test_modes())}")
        
        # 测试类别
        print(f"📁 可用测试类别: {', '.join(self.get_available_test_categories())}")
        
        # 场景
        scenarios = self.get_available_scenarios()
        if scenarios:
            print(f"🎬 可用测试场景: {', '.join(scenarios)}")
        
        # 成功率阈值
        thresholds = self._config.get("thresholds", {}).get("success_rate", {})
        print(f"📊 成功率阈值: 优秀 {thresholds.get('excellent', 95)}%, 良好 {thresholds.get('good', 80)}%")
        
        # 验证配置
        issues = self.validate_config()
        if issues:
            print(f"\n⚠️ 配置问题:")
            for issue in issues:
                print(f"   • {issue}")
        else:
            print(f"\n✅ 配置验证通过")
        
        print("=" * 50)


# 全局配置管理器实例
_test_config_manager = None

def get_test_config_manager() -> TestConfigManager:
    """获取全局测试配置管理器实例"""
    global _test_config_manager
    if _test_config_manager is None:
        _test_config_manager = TestConfigManager()
    return _test_config_manager


def main():
    """配置管理器测试函数"""
    config_mgr = TestConfigManager()
    config_mgr.print_config_summary()


if __name__ == "__main__":
    main()