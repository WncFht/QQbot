"""
配置管理模块
提供配置的加载、保存和访问功能
"""
from .manager import ConfigManager

# 全局配置管理器实例
_config_manager = None

def get_config(config_path: str = "config.json"):
    """获取配置管理器实例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        ConfigManager: 配置管理器实例
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    return _config_manager

__all__ = ["get_config", "ConfigManager"] 