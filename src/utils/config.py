"""
配置管理模块，用于加载和管理配置文件
"""
import os
import json
import yaml
from typing import Any, Dict, List, Optional, Union
from .logger import get_logger

logger = get_logger("config")

class ConfigManager:
    """配置管理类，用于加载和管理配置文件"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_path: str = "config.json"):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        # 避免重复初始化
        if self._initialized:
            return
        
        self.config_path = config_path
        self.config = {}
        self._initialized = True
        
        # 加载配置文件
        self.load_config()
    
    def load_config(self) -> bool:
        """加载配置文件
        
        Returns:
            bool: 是否成功
        """
        try:
            if not os.path.exists(self.config_path):
                logger.warning(f"配置文件不存在: {self.config_path}")
                return False
            
            file_ext = os.path.splitext(self.config_path)[1].lower()
            
            if file_ext == '.json':
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            elif file_ext in ['.yaml', '.yml']:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config = yaml.safe_load(f)
            else:
                logger.error(f"不支持的配置文件格式: {file_ext}")
                return False
            
            logger.info(f"配置文件加载成功: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}", exc_info=True)
            return False
    
    def save_config(self) -> bool:
        """保存配置文件
        
        Returns:
            bool: 是否成功
        """
        try:
            file_ext = os.path.splitext(self.config_path)[1].lower()
            
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)
            
            if file_ext == '.json':
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.config, f, ensure_ascii=False, indent=4)
            elif file_ext in ['.yaml', '.yml']:
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self.config, f, allow_unicode=True)
            else:
                logger.error(f"不支持的配置文件格式: {file_ext}")
                return False
            
            logger.info(f"配置文件保存成功: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}", exc_info=True)
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项
        
        Args:
            key: 配置项键名，支持点号分隔的多级键名
            default: 默认值
            
        Returns:
            Any: 配置项值
        """
        try:
            # 处理多级键名
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            
            return value
        except Exception as e:
            logger.error(f"获取配置项失败: {key}, {e}", exc_info=True)
            return default
    
    def set(self, key: str, value: Any, auto_save: bool = True) -> bool:
        """设置配置项
        
        Args:
            key: 配置项键名，支持点号分隔的多级键名
            value: 配置项值
            auto_save: 是否自动保存配置文件
            
        Returns:
            bool: 是否成功
        """
        try:
            # 处理多级键名
            keys = key.split('.')
            config = self.config
            
            # 遍历除最后一个键以外的所有键
            for i, k in enumerate(keys[:-1]):
                if k not in config:
                    config[k] = {}
                elif not isinstance(config[k], dict):
                    # 如果当前键对应的值不是字典，则将其替换为字典
                    config[k] = {}
                
                config = config[k]
            
            # 设置最后一个键的值
            config[keys[-1]] = value
            
            # 自动保存
            if auto_save:
                return self.save_config()
            
            return True
        except Exception as e:
            logger.error(f"设置配置项失败: {key}, {e}", exc_info=True)
            return False
    
    def delete(self, key: str, auto_save: bool = True) -> bool:
        """删除配置项
        
        Args:
            key: 配置项键名，支持点号分隔的多级键名
            auto_save: 是否自动保存配置文件
            
        Returns:
            bool: 是否成功
        """
        try:
            # 处理多级键名
            keys = key.split('.')
            config = self.config
            
            # 遍历除最后一个键以外的所有键
            for i, k in enumerate(keys[:-1]):
                if k not in config or not isinstance(config[k], dict):
                    # 如果键不存在或者对应的值不是字典，则无法删除
                    return False
                
                config = config[k]
            
            # 删除最后一个键
            if keys[-1] in config:
                del config[keys[-1]]
                
                # 自动保存
                if auto_save:
                    return self.save_config()
                
                return True
            
            return False
        except Exception as e:
            logger.error(f"删除配置项失败: {key}, {e}", exc_info=True)
            return False
    
    def has(self, key: str) -> bool:
        """检查配置项是否存在
        
        Args:
            key: 配置项键名，支持点号分隔的多级键名
            
        Returns:
            bool: 是否存在
        """
        try:
            # 处理多级键名
            keys = key.split('.')
            value = self.config
            
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return False
            
            return True
        except Exception as e:
            logger.error(f"检查配置项是否存在失败: {key}, {e}", exc_info=True)
            return False
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置项
        
        Returns:
            Dict[str, Any]: 所有配置项
        """
        return self.config.copy()
    
    def reset(self) -> bool:
        """重置配置
        
        Returns:
            bool: 是否成功
        """
        try:
            self.config = {}
            return self.save_config()
        except Exception as e:
            logger.error(f"重置配置失败: {e}", exc_info=True)
            return False
    
    def merge(self, config: Dict[str, Any], auto_save: bool = True) -> bool:
        """合并配置
        
        Args:
            config: 要合并的配置
            auto_save: 是否自动保存配置文件
            
        Returns:
            bool: 是否成功
        """
        try:
            self._merge_dict(self.config, config)
            
            # 自动保存
            if auto_save:
                return self.save_config()
            
            return True
        except Exception as e:
            logger.error(f"合并配置失败: {e}", exc_info=True)
            return False
    
    def _merge_dict(self, target: Dict[str, Any], source: Dict[str, Any]):
        """合并字典
        
        Args:
            target: 目标字典
            source: 源字典
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # 如果两个值都是字典，则递归合并
                self._merge_dict(target[key], value)
            else:
                # 否则直接覆盖
                target[key] = value

# 创建全局配置管理器实例
config_manager = ConfigManager()

def get_config() -> ConfigManager:
    """获取配置管理器实例
    
    Returns:
        ConfigManager: 配置管理器实例
    """
    return config_manager 