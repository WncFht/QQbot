"""
插件管理模块，用于加载和管理插件
"""
import os
import sys
import importlib
import inspect
import pkgutil
from typing import Any, Dict, List, Optional, Set, Type, Union
from ncatbot.core.plugin import Plugin
from src.utils.logger import get_logger
from src.utils.config import get_config

logger = get_logger("plugin_manager")
config = get_config()

class PluginManager:
    """插件管理类，用于加载和管理插件"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(PluginManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, plugin_dir: str = "plugins"):
        """初始化插件管理器
        
        Args:
            plugin_dir: 插件目录
        """
        # 避免重复初始化
        if self._initialized:
            return
        
        self.plugin_dir = plugin_dir
        self.plugins: Dict[str, Plugin] = {}
        self.plugin_classes: Dict[str, Type[Plugin]] = {}
        self.disabled_plugins: Set[str] = set()
        self._initialized = True
        
        # 从配置中加载禁用的插件列表
        disabled = config.get("plugins.disabled", [])
        if isinstance(disabled, list):
            self.disabled_plugins = set(disabled)
    
    def discover_plugins(self) -> List[str]:
        """发现插件
        
        Returns:
            List[str]: 插件名称列表
        """
        try:
            # 确保插件目录存在
            if not os.path.exists(self.plugin_dir):
                os.makedirs(self.plugin_dir)
                logger.info(f"创建插件目录: {self.plugin_dir}")
                return []
            
            # 将插件目录添加到系统路径
            if self.plugin_dir not in sys.path:
                sys.path.insert(0, os.path.abspath(self.plugin_dir))
            
            # 发现插件
            plugin_names = []
            for _, name, is_pkg in pkgutil.iter_modules([self.plugin_dir]):
                if is_pkg:
                    plugin_names.append(name)
            
            logger.info(f"发现插件: {plugin_names}")
            return plugin_names
        except Exception as e:
            logger.error(f"发现插件失败: {e}", exc_info=True)
            return []
    
    def load_plugin(self, plugin_name: str) -> bool:
        """加载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否成功
        """
        try:
            # 检查插件是否已加载
            if plugin_name in self.plugins:
                logger.warning(f"插件已加载: {plugin_name}")
                return True
            
            # 检查插件是否被禁用
            if plugin_name in self.disabled_plugins:
                logger.warning(f"插件已禁用: {plugin_name}")
                return False
            
            # 导入插件模块
            module = importlib.import_module(plugin_name)
            
            # 查找插件类
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, Plugin) and 
                    obj is not Plugin):
                    plugin_class = obj
                    break
            
            if plugin_class is None:
                logger.error(f"插件类未找到: {plugin_name}")
                return False
            
            # 实例化插件
            plugin = plugin_class()
            
            # 保存插件实例和类
            self.plugins[plugin_name] = plugin
            self.plugin_classes[plugin_name] = plugin_class
            
            logger.info(f"插件加载成功: {plugin_name}")
            return True
        except Exception as e:
            logger.error(f"加载插件失败: {plugin_name}, {e}", exc_info=True)
            return False
    
    def load_all_plugins(self) -> Dict[str, bool]:
        """加载所有插件
        
        Returns:
            Dict[str, bool]: 插件加载结果，键为插件名称，值为是否成功
        """
        try:
            # 发现插件
            plugin_names = self.discover_plugins()
            
            # 加载插件
            results = {}
            for name in plugin_names:
                results[name] = self.load_plugin(name)
            
            logger.info(f"加载所有插件完成: {results}")
            return results
        except Exception as e:
            logger.error(f"加载所有插件失败: {e}", exc_info=True)
            return {}
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否成功
        """
        try:
            # 检查插件是否已加载
            if plugin_name not in self.plugins:
                logger.warning(f"插件未加载: {plugin_name}")
                return False
            
            # 获取插件实例
            plugin = self.plugins[plugin_name]
            
            # 调用插件的卸载方法
            if hasattr(plugin, 'on_unload') and callable(getattr(plugin, 'on_unload')):
                plugin.on_unload()
            
            # 移除插件
            del self.plugins[plugin_name]
            del self.plugin_classes[plugin_name]
            
            # 尝试卸载模块
            if plugin_name in sys.modules:
                del sys.modules[plugin_name]
            
            logger.info(f"插件卸载成功: {plugin_name}")
            return True
        except Exception as e:
            logger.error(f"卸载插件失败: {plugin_name}, {e}", exc_info=True)
            return False
    
    def unload_all_plugins(self) -> Dict[str, bool]:
        """卸载所有插件
        
        Returns:
            Dict[str, bool]: 插件卸载结果，键为插件名称，值为是否成功
        """
        try:
            # 获取所有已加载的插件
            plugin_names = list(self.plugins.keys())
            
            # 卸载插件
            results = {}
            for name in plugin_names:
                results[name] = self.unload_plugin(name)
            
            logger.info(f"卸载所有插件完成: {results}")
            return results
        except Exception as e:
            logger.error(f"卸载所有插件失败: {e}", exc_info=True)
            return {}
    
    def reload_plugin(self, plugin_name: str) -> bool:
        """重新加载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否成功
        """
        try:
            # 卸载插件
            if plugin_name in self.plugins:
                if not self.unload_plugin(plugin_name):
                    return False
            
            # 重新加载模块
            if plugin_name in sys.modules:
                importlib.reload(sys.modules[plugin_name])
            
            # 加载插件
            return self.load_plugin(plugin_name)
        except Exception as e:
            logger.error(f"重新加载插件失败: {plugin_name}, {e}", exc_info=True)
            return False
    
    def reload_all_plugins(self) -> Dict[str, bool]:
        """重新加载所有插件
        
        Returns:
            Dict[str, bool]: 插件重新加载结果，键为插件名称，值为是否成功
        """
        try:
            # 获取所有已加载的插件
            plugin_names = list(self.plugins.keys())
            
            # 卸载所有插件
            self.unload_all_plugins()
            
            # 加载所有插件
            results = {}
            for name in plugin_names:
                results[name] = self.load_plugin(name)
            
            # 发现新插件
            discovered = self.discover_plugins()
            for name in discovered:
                if name not in results:
                    results[name] = self.load_plugin(name)
            
            logger.info(f"重新加载所有插件完成: {results}")
            return results
        except Exception as e:
            logger.error(f"重新加载所有插件失败: {e}", exc_info=True)
            return {}
    
    def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否成功
        """
        try:
            # 检查插件是否已启用
            if plugin_name not in self.disabled_plugins:
                logger.warning(f"插件已启用: {plugin_name}")
                return True
            
            # 从禁用列表中移除
            self.disabled_plugins.remove(plugin_name)
            
            # 更新配置
            config.set("plugins.disabled", list(self.disabled_plugins))
            
            # 加载插件
            result = self.load_plugin(plugin_name)
            
            logger.info(f"插件启用成功: {plugin_name}")
            return result
        except Exception as e:
            logger.error(f"启用插件失败: {plugin_name}, {e}", exc_info=True)
            return False
    
    def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否成功
        """
        try:
            # 检查插件是否已禁用
            if plugin_name in self.disabled_plugins:
                logger.warning(f"插件已禁用: {plugin_name}")
                return True
            
            # 卸载插件
            if plugin_name in self.plugins:
                if not self.unload_plugin(plugin_name):
                    return False
            
            # 添加到禁用列表
            self.disabled_plugins.add(plugin_name)
            
            # 更新配置
            config.set("plugins.disabled", list(self.disabled_plugins))
            
            logger.info(f"插件禁用成功: {plugin_name}")
            return True
        except Exception as e:
            logger.error(f"禁用插件失败: {plugin_name}, {e}", exc_info=True)
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """获取插件实例
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[Plugin]: 插件实例，如果不存在则返回None
        """
        return self.plugins.get(plugin_name)
    
    def get_plugin_class(self, plugin_name: str) -> Optional[Type[Plugin]]:
        """获取插件类
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[Type[Plugin]]: 插件类，如果不存在则返回None
        """
        return self.plugin_classes.get(plugin_name)
    
    def get_all_plugins(self) -> Dict[str, Plugin]:
        """获取所有插件实例
        
        Returns:
            Dict[str, Plugin]: 插件实例字典，键为插件名称，值为插件实例
        """
        return self.plugins.copy()
    
    def get_all_plugin_classes(self) -> Dict[str, Type[Plugin]]:
        """获取所有插件类
        
        Returns:
            Dict[str, Type[Plugin]]: 插件类字典，键为插件名称，值为插件类
        """
        return self.plugin_classes.copy()
    
    def get_disabled_plugins(self) -> Set[str]:
        """获取禁用的插件列表
        
        Returns:
            Set[str]: 禁用的插件名称集合
        """
        return self.disabled_plugins.copy()
    
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """检查插件是否已加载
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否已加载
        """
        return plugin_name in self.plugins
    
    def is_plugin_disabled(self, plugin_name: str) -> bool:
        """检查插件是否已禁用
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否已禁用
        """
        return plugin_name in self.disabled_plugins
    
    def call_plugin_method(self, plugin_name: str, method_name: str, *args, **kwargs) -> Any:
        """调用插件方法
        
        Args:
            plugin_name: 插件名称
            method_name: 方法名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 方法返回值
        """
        try:
            # 获取插件实例
            plugin = self.get_plugin(plugin_name)
            if plugin is None:
                logger.error(f"插件未加载: {plugin_name}")
                return None
            
            # 检查方法是否存在
            if not hasattr(plugin, method_name) or not callable(getattr(plugin, method_name)):
                logger.error(f"插件方法不存在: {plugin_name}.{method_name}")
                return None
            
            # 调用方法
            method = getattr(plugin, method_name)
            return method(*args, **kwargs)
        except Exception as e:
            logger.error(f"调用插件方法失败: {plugin_name}.{method_name}, {e}", exc_info=True)
            return None
    
    def call_all_plugin_method(self, method_name: str, *args, **kwargs) -> Dict[str, Any]:
        """调用所有插件的方法
        
        Args:
            method_name: 方法名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Dict[str, Any]: 方法返回值字典，键为插件名称，值为方法返回值
        """
        try:
            results = {}
            for name, plugin in self.plugins.items():
                # 检查方法是否存在
                if hasattr(plugin, method_name) and callable(getattr(plugin, method_name)):
                    try:
                        method = getattr(plugin, method_name)
                        results[name] = method(*args, **kwargs)
                    except Exception as e:
                        logger.error(f"调用插件方法失败: {name}.{method_name}, {e}", exc_info=True)
                        results[name] = None
            
            return results
        except Exception as e:
            logger.error(f"调用所有插件方法失败: {method_name}, {e}", exc_info=True)
            return {}

# 创建全局插件管理器实例
plugin_manager = PluginManager()

def get_plugin_manager() -> PluginManager:
    """获取插件管理器实例
    
    Returns:
        PluginManager: 插件管理器实例
    """
    return plugin_manager 