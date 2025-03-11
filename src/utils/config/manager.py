"""
配置管理模块
提供配置的加载、保存和访问功能
"""
import os
import json
import yaml
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from ..singleton import Singleton
from ..logger import get_logger

logger = get_logger("config")

class ConfigManager(Singleton):
    """配置管理类，用于加载和管理配置文件"""
    
    def __init__(self, config_path: str = "config.json"):
        """初始化配置管理器
        
        Args:
            config_path: 配置文件路径
        """
        # 避免重复初始化
        if hasattr(self, "_initialized") and self._initialized:
            return
            
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        
        # 配置变更回调函数
        # 键为配置键，值为回调函数列表
        self.change_callbacks: Dict[str, List[Callable]] = {}
        
        # 加载配置文件
        self.load()
        
        # 初始化标记
        self._initialized = True
    
    def load(self) -> bool:
        """加载配置文件
        
        Returns:
            bool: 是否加载成功
        """
        try:
            # 如果配置文件不存在，则创建默认配置
            if not os.path.exists(self.config_path):
                self.config = self._get_default_config()
                self.save()
                return True
            
            # 根据文件扩展名选择加载方式
            ext = os.path.splitext(self.config_path)[1].lower()
            if ext == ".json":
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = json.load(f)
            elif ext in [".yml", ".yaml"]:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config = yaml.safe_load(f)
            else:
                logger.error(f"不支持的配置文件格式: {ext}")
                return False
            
            logger.info(f"加载配置文件成功: {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return False
    
    def save(self) -> bool:
        """保存配置文件
        
        Returns:
            bool: 是否保存成功
        """
        try:
            # 确保配置目录存在
            os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)
            
            # 根据文件扩展名选择保存方式
            ext = os.path.splitext(self.config_path)[1].lower()
            if ext == ".json":
                with open(self.config_path, "w", encoding="utf-8") as f:
                    json.dump(self.config, f, indent=4, ensure_ascii=False)
            elif ext in [".yml", ".yaml"]:
                with open(self.config_path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(self.config, f, allow_unicode=True)
            else:
                logger.error(f"不支持的配置文件格式: {ext}")
                return False
            
            logger.info(f"保存配置文件成功: {self.config_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的多级键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        try:
            value = self.config
            for k in key.split("."):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """设置配置值
        
        Args:
            key: 配置键，支持点号分隔的多级键
            value: 配置值
            
        Returns:
            bool: 是否设置成功
        """
        try:
            keys = key.split(".")
            target = self.config
            
            # 遍历到倒数第二级键
            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                elif not isinstance(target[k], dict):
                    target[k] = {}
                target = target[k]
            
            # 获取旧值
            old_value = target.get(keys[-1])
            
            # 设置新值
            target[keys[-1]] = value
            
            # 调用变更回调
            self._call_change_callbacks(key, old_value, value)
            
            return True
            
        except Exception as e:
            logger.error(f"设置配置值失败: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除配置项
        
        Args:
            key: 配置键，支持点号分隔的多级键
            
        Returns:
            bool: 是否删除成功
        """
        try:
            keys = key.split(".")
            target = self.config
            
            # 遍历到倒数第二级键
            for k in keys[:-1]:
                if k not in target:
                    return False
                target = target[k]
                if not isinstance(target, dict):
                    return False
            
            # 获取旧值
            old_value = target.get(keys[-1])
            
            # 删除配置项
            if keys[-1] in target:
                del target[keys[-1]]
                
                # 调用变更回调
                self._call_change_callbacks(key, old_value, None)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"删除配置项失败: {e}")
            return False
    
    def has(self, key: str) -> bool:
        """检查配置项是否存在
        
        Args:
            key: 配置键，支持点号分隔的多级键
            
        Returns:
            bool: 是否存在
        """
        try:
            value = self.config
            for k in key.split("."):
                value = value[k]
            return True
        except (KeyError, TypeError):
            return False
    
    def get_int(self, key: str, default: int = 0) -> int:
        """获取整数配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            int: 配置值
        """
        value = self.get(key, default)
        try:
            return int(value)
        except (TypeError, ValueError):
            return default
    
    def get_float(self, key: str, default: float = 0.0) -> float:
        """获取浮点数配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            float: 配置值
        """
        value = self.get(key, default)
        try:
            return float(value)
        except (TypeError, ValueError):
            return default
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """获取布尔配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            bool: 配置值
        """
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ["true", "yes", "1", "on"]
        return bool(value)
    
    def get_str(self, key: str, default: str = "") -> str:
        """获取字符串配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            str: 配置值
        """
        value = self.get(key, default)
        return str(value)
    
    def get_list(self, key: str, default: List = None) -> List:
        """获取列表配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            List: 配置值
        """
        if default is None:
            default = []
        value = self.get(key, default)
        return list(value) if isinstance(value, (list, tuple)) else default
    
    def get_dict(self, key: str, default: Dict = None) -> Dict:
        """获取字典配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            Dict: 配置值
        """
        if default is None:
            default = {}
        value = self.get(key, default)
        return dict(value) if isinstance(value, dict) else default
    
    def on_change(self, key: str):
        """配置变更装饰器
        
        Args:
            key: 配置键
            
        Returns:
            Callable: 装饰器
        """
        def decorator(callback):
            if key not in self.change_callbacks:
                self.change_callbacks[key] = []
            self.change_callbacks[key].append(callback)
            return callback
        return decorator
    
    def _call_change_callbacks(self, key: str, old_value: Any, new_value: Any):
        """调用配置变更回调函数
        
        Args:
            key: 配置键
            old_value: 旧值
            new_value: 新值
        """
        # 调用完整键的回调
        if key in self.change_callbacks:
            for callback in self.change_callbacks[key]:
                try:
                    callback(old_value, new_value)
                except Exception as e:
                    logger.error(f"调用配置变更回调失败: {e}")
        
        # 调用父级键的回调
        parts = key.split(".")
        for i in range(len(parts) - 1):
            parent_key = ".".join(parts[:i+1])
            if parent_key in self.change_callbacks:
                for callback in self.change_callbacks[parent_key]:
                    try:
                        callback(old_value, new_value)
                    except Exception as e:
                        logger.error(f"调用配置变更回调失败: {e}")
    
    def _get_default_config(self) -> Dict:
        """获取默认配置
        
        Returns:
            Dict: 默认配置
        """
        return {
            "bot": {
                "name": "NapcatBot",
                "version": "1.0.0",
                "description": "一个基于 NapcatBot 框架的 QQ 机器人"
            },
            "log": {
                "level": "INFO",
                "dir": "logs",
                "max_size": 10485760,  # 10MB
                "backup_count": 5
            },
            "database": {
                "path": "data/database.db"
            },
            "plugins": {
                "dir": "plugins",
                "disabled": []
            }
        }

# 创建全局配置管理器实例
config = ConfigManager()

# 导出常用函数和类
__all__ = ["ConfigManager", "config"] 