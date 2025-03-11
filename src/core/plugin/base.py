"""
插件基类定义
"""
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from src.core.utils import BaseComponent, catch_exceptions, log_execution_time

class Plugin(ABC, BaseComponent):
    """插件基类"""
    
    def __init__(self):
        """初始化插件"""
        self.name = self.__class__.__name__
        super().__init__(self.name)
        
        self.description = ""
        self.version = "1.0.0"
        self.author = ""
        self.dependencies = {}
        self.config = {}
        self.enabled = True
    
    @abstractmethod
    @catch_exceptions
    async def on_load(self) -> bool:
        """插件加载时调用
        
        Returns:
            bool: 是否加载成功
        """
        self.log_info(f"插件 {self.name} 正在加载")
        return True
    
    @abstractmethod
    @catch_exceptions
    async def on_unload(self) -> bool:
        """插件卸载时调用
        
        Returns:
            bool: 是否卸载成功
        """
        self.log_info(f"插件 {self.name} 正在卸载")
        return True
    
    @catch_exceptions
    async def on_enable(self) -> bool:
        """插件启用时调用
        
        Returns:
            bool: 是否启用成功
        """
        self.enabled = True
        self.log_info(f"插件 {self.name} 已启用")
        return True
    
    @catch_exceptions
    async def on_disable(self) -> bool:
        """插件禁用时调用
        
        Returns:
            bool: 是否禁用成功
        """
        self.enabled = False
        self.log_info(f"插件 {self.name} 已禁用")
        return True
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置项
        
        Args:
            key: 配置项键
            default: 默认值
            
        Returns:
            Any: 配置项值
        """
        value = self.config.get(key, default)
        self.log_debug(f"获取配置项 {key}={value}")
        return value
    
    def set_config(self, key: str, value: Any) -> None:
        """设置配置项
        
        Args:
            key: 配置项键
            value: 配置项值
        """
        self.config[key] = value
        self.log_debug(f"设置配置项 {key}={value}")
    
    def get_dependency_version(self, name: str) -> Optional[str]:
        """获取依赖版本
        
        Args:
            name: 依赖名称
            
        Returns:
            Optional[str]: 依赖版本
        """
        return self.dependencies.get(name)
    
    def add_dependency(self, name: str, version: str) -> None:
        """添加依赖
        
        Args:
            name: 依赖名称
            version: 依赖版本
        """
        self.dependencies[name] = version
        self.log_debug(f"添加依赖 {name}={version}")
    
    def get_info(self) -> Dict[str, Any]:
        """获取插件信息
        
        Returns:
            Dict[str, Any]: 插件信息
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "dependencies": self.dependencies,
            "enabled": self.enabled
        } 