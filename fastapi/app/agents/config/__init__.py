"""Agent 配置模块

提供 YAML 配置的加载和管理功能。
"""

import os
import yaml
from typing import Any
from pathlib import Path

from app.utils.log_helper import get_logger

logger = get_logger("agents.config")

# 配置文件路径
CONFIG_DIR = Path(__file__).parent
SCENARIOS_FILE = CONFIG_DIR / "scenarios.yaml"
AGENTS_FILE = CONFIG_DIR / "agents.yaml"


class ConfigLoader:
    """配置加载器

    负责加载和管理 YAML 配置文件。
    """

    _instance = None
    _scenarios: dict[str, Any] | None = None
    _agents: dict[str, Any] | None = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._scenarios is None:
            self._load_configs()

    def _load_configs(self) -> None:
        """加载所有配置文件"""
        try:
            if SCENARIOS_FILE.exists():
                with open(SCENARIOS_FILE, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    self._scenarios = data.get("scenarios", {})
                logger.info(f"Loaded scenarios config: {len(self._scenarios)} scenarios")
            else:
                logger.warning(f"Scenarios config file not found: {SCENARIOS_FILE}")
                self._scenarios = {}

            if AGENTS_FILE.exists():
                with open(AGENTS_FILE, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    self._agents = data.get("agents", {})
                logger.info(f"Loaded agents config: {len(self._agents)} agents")
            else:
                logger.warning(f"Agents config file not found: {AGENTS_FILE}")
                self._agents = {}

        except Exception as e:
            logger.error(f"Failed to load configs: {e}")
            self._scenarios = {}
            self._agents = {}

    def get_scenario(self, scenario_id: str) -> dict[str, Any] | None:
        """获取指定场景配置

        Args:
            scenario_id: 场景 ID

        Returns:
            场景配置字典，如果不存在返回 None
        """
        return self._scenarios.get(scenario_id)

    def get_all_scenarios(self) -> dict[str, Any]:
        """获取所有场景配置

        Returns:
            所有场景配置字典
        """
        return self._scenarios.copy()

    def get_agent_config(self, agent_id: str) -> dict[str, Any] | None:
        """获取指定 Agent 配置

        Args:
            agent_id: Agent ID

        Returns:
            Agent 配置字典，如果不存在返回 None
        """
        return self._agents.get(agent_id)

    def get_all_agent_configs(self) -> dict[str, Any]:
        """获取所有 Agent 配置

        Returns:
            所有 Agent 配置字典
        """
        return self._agents.copy()

    def get_scenario_names(self) -> list[str]:
        """获取所有场景名称列表

        Returns:
            场景 ID 列表
        """
        return list(self._scenarios.keys())

    def get_agent_names(self) -> list[str]:
        """获取所有 Agent 名称列表

        Returns:
            Agent ID 列表
        """
        return list(self._agents.keys())

    def reload(self) -> None:
        """重新加载配置"""
        self._load_configs()


# 全局配置加载器实例
_config_loader: ConfigLoader | None = None


def get_config_loader() -> ConfigLoader:
    """获取配置加载器实例"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def get_scenario(scenario_id: str) -> dict[str, Any] | None:
    """获取指定场景配置（便捷函数）"""
    return get_config_loader().get_scenario(scenario_id)


def get_all_scenarios() -> dict[str, Any]:
    """获取所有场景配置（便捷函数）"""
    return get_config_loader().get_all_scenarios()


def get_agent_config(agent_id: str) -> dict[str, Any] | None:
    """获取指定 Agent 配置（便捷函数）"""
    return get_config_loader().get_agent_config(agent_id)


def get_all_agent_configs() -> dict[str, Any]:
    """获取所有 Agent 配置（便捷函数）"""
    return get_config_loader().get_all_agent_configs()


def reload_configs() -> None:
    """重新加载所有配置"""
    get_config_loader().reload()


__all__ = [
    "ConfigLoader",
    "get_config_loader",
    "get_scenario",
    "get_all_scenarios",
    "get_agent_config",
    "get_all_agent_configs",
    "reload_configs",
]
