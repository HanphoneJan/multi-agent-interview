"""Config Loader 测试"""

import pytest
from unittest.mock import patch, mock_open

from app.agents.config import (
    ConfigLoader,
    get_scenario,
    get_all_scenarios,
    get_agent_config,
    get_all_agent_configs,
    reload_configs,
)


class TestConfigLoader:
    """测试 ConfigLoader 类"""

    def test_singleton_pattern(self):
        """测试单例模式"""
        loader1 = ConfigLoader()
        loader2 = ConfigLoader()

        assert loader1 is loader2

    @patch("builtins.open", mock_open(read_data="""
scenarios:
  test_scenario:
    name: "Test Scenario"
    description: "A test scenario"
"""))
    @patch("pathlib.Path.exists")
    def test_load_scenarios(self, mock_exists):
        """测试加载场景配置"""
        mock_exists.return_value = True

        # 创建新的 loader 实例以触发加载
        ConfigLoader._instance = None
        ConfigLoader._scenarios = None
        loader = ConfigLoader()

        scenarios = loader.get_all_scenarios()

        assert "test_scenario" in scenarios
        assert scenarios["test_scenario"]["name"] == "Test Scenario"

    @patch("builtins.open", mock_open(read_data="""
agents:
  test_agent:
    name: "Test Agent"
    role: "Tester"
"""))
    @patch("pathlib.Path.exists")
    def test_load_agents(self, mock_exists):
        """测试加载 Agent 配置"""
        mock_exists.return_value = True

        ConfigLoader._instance = None
        ConfigLoader._agents = None
        loader = ConfigLoader()

        agents = loader.get_all_agent_configs()

        assert "test_agent" in agents
        assert agents["test_agent"]["name"] == "Test Agent"

    def test_get_scenario(self):
        """测试获取单个场景"""
        ConfigLoader._instance = None
        loader = ConfigLoader()
        loader._scenarios = {
            "scenario1": {"name": "Scenario 1"},
            "scenario2": {"name": "Scenario 2"},
        }

        scenario = loader.get_scenario("scenario1")

        assert scenario == {"name": "Scenario 1"}

    def test_get_scenario_not_found(self):
        """测试获取不存在的场景"""
        ConfigLoader._instance = None
        loader = ConfigLoader()
        loader._scenarios = {}

        scenario = loader.get_scenario("nonexistent")

        assert scenario is None

    def test_get_agent_config(self):
        """测试获取 Agent 配置"""
        ConfigLoader._instance = None
        loader = ConfigLoader()
        loader._agents = {
            "agent1": {"name": "Agent 1"},
        }

        config = loader.get_agent_config("agent1")

        assert config == {"name": "Agent 1"}

    def test_get_scenario_names(self):
        """测试获取场景名称列表"""
        ConfigLoader._instance = None
        loader = ConfigLoader()
        loader._scenarios = {
            "scenario1": {},
            "scenario2": {},
        }

        names = loader.get_scenario_names()

        assert "scenario1" in names
        assert "scenario2" in names

    def test_get_agent_names(self):
        """测试获取 Agent 名称列表"""
        ConfigLoader._instance = None
        loader = ConfigLoader()
        loader._agents = {
            "agent1": {},
            "agent2": {},
        }

        names = loader.get_agent_names()

        assert "agent1" in names
        assert "agent2" in names


class TestConfigFunctions:
    """测试配置便捷函数"""

    def test_get_scenario_function(self):
        """测试 get_scenario 函数"""
        ConfigLoader._instance = None
        loader = ConfigLoader()
        loader._scenarios = {"test": {"name": "Test"}}

        scenario = get_scenario("test")

        assert scenario == {"name": "Test"}

    def test_get_all_scenarios_function(self):
        """测试 get_all_scenarios 函数"""
        ConfigLoader._instance = None
        loader = ConfigLoader()
        loader._scenarios = {"s1": {}, "s2": {}}

        scenarios = get_all_scenarios()

        assert len(scenarios) == 2

    def test_get_agent_config_function(self):
        """测试 get_agent_config 函数"""
        ConfigLoader._instance = None
        loader = ConfigLoader()
        loader._agents = {"agent1": {"role": "test"}}

        config = get_agent_config("agent1")

        assert config == {"role": "test"}

    def test_get_all_agent_configs_function(self):
        """测试 get_all_agent_configs 函数"""
        ConfigLoader._instance = None
        loader = ConfigLoader()
        loader._agents = {"a1": {}, "a2": {}}

        configs = get_all_agent_configs()

        assert len(configs) == 2

    def test_reload_configs(self):
        """测试 reload_configs 函数"""
        ConfigLoader._instance = None
        loader = ConfigLoader()
        loader._scenarios = {"old": {}}

        with patch.object(loader, "_load_configs") as mock_load:
            reload_configs()
            mock_load.assert_called_once()
