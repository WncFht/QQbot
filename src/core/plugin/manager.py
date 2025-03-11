"""
插件管理器模块
负责加载、卸载和管理插件
"""
import os
import sys
import importlib
import logging
import asyncio
from typing import Dict, List, Any, Optional, Type

from .base import BasePlugin
from ..event.bus import EventBus

class PluginManager:
    """插件管理器类"""
    
    def __init__(self):
        """初始化插件管理器"""
        # 获取事件总线
        from ..event.bus import EventBus
        self.event_bus = EventBus()
        
        # 插件目录
        self.plugins_dir = "plugins"
        
        # 已加载的插件
        self.plugins: Dict[str, BasePlugin] = {}
        
        # 禁用的插件
        self.disabled_plugins: List[str] = []
        
        # 设置日志
        self.logger = logging.getLogger("plugin_manager")
        
        # 从配置中加载禁用的插件列表
        self._load_disabled_plugins()
    
    def _load_disabled_plugins(self):
        """从配置中加载禁用的插件列表"""
        try:
            from src.utils.config import get_config
            config = get_config()
            self.disabled_plugins = config.get("plugins.disabled", [])
        except Exception as e:
            self.logger.error(f"加载禁用插件列表失败: {e}")
            self.disabled_plugins = []
    
    async def load_plugin(self, plugin_name: str) -> bool:
        """加载单个插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否加载成功
        """
        # 检查插件是否已加载
        if plugin_name in self.plugins:
            self.logger.warning(f"插件 {plugin_name} 已经加载")
            return False
        
        # 检查插件是否被禁用
        if plugin_name in self.disabled_plugins:
            self.logger.info(f"插件 {plugin_name} 已被禁用，跳过加载")
            return False
        
        # 检查插件目录是否存在
        plugin_path = os.path.join(self.plugins_dir, plugin_name)
        if not os.path.exists(plugin_path) or not os.path.isdir(plugin_path):
            self.logger.error(f"插件目录 {plugin_path} 不存在")
            return False
        
        # 检查插件入口文件是否存在
        init_file = os.path.join(plugin_path, "__init__.py")
        if not os.path.exists(init_file):
            self.logger.error(f"插件入口文件 {init_file} 不存在")
            return False
        
        try:
            # 导入插件模块
            module_name = f"{self.plugins_dir}.{plugin_name}"
            if module_name in sys.modules:
                module = importlib.reload(sys.modules[module_name])
            else:
                module = importlib.import_module(module_name)
            
            # 查找插件类
            plugin_class = None
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr != BasePlugin:
                    plugin_class = attr
                    break
            
            if not plugin_class:
                self.logger.error(f"在插件 {plugin_name} 中找不到继承自 BasePlugin 的类")
                return False
            
            # 创建插件实例
            plugin = plugin_class(event_bus=self.event_bus)
            
            # 检查插件依赖
            for dep_name, dep_version in plugin.dependencies.items():
                if dep_name not in self.plugins:
                    self.logger.error(f"插件 {plugin_name} 依赖的插件 {dep_name} 未加载")
                    return False
                # TODO: 检查版本兼容性
            
            # 调用插件加载方法
            if hasattr(plugin, "on_load"):
                result = await plugin.on_load()
                if not result:
                    self.logger.error(f"插件 {plugin_name} 加载失败")
                    return False
            
            # 将插件添加到已加载插件字典
            self.plugins[plugin_name] = plugin
            
            # 如果插件未被禁用，则启用插件
            if plugin_name not in self.disabled_plugins:
                await self.enable_plugin(plugin_name)
            
            self.logger.info(f"插件 {plugin_name} 加载成功")
            return True
        
        except Exception as e:
            self.logger.error(f"加载插件 {plugin_name} 时发生错误: {e}", exc_info=True)
            return False
    
    async def unload_plugin(self, plugin_name: str) -> bool:
        """卸载单个插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否卸载成功
        """
        # 检查插件是否已加载
        if plugin_name not in self.plugins:
            self.logger.warning(f"插件 {plugin_name} 未加载")
            return False
        
        try:
            # 获取插件实例
            plugin = self.plugins[plugin_name]
            
            # 如果插件已启用，则先禁用插件
            if plugin.enabled:
                await self.disable_plugin(plugin_name)
            
            # 调用插件卸载方法
            if hasattr(plugin, "on_unload"):
                result = await plugin.on_unload()
                if not result:
                    self.logger.error(f"插件 {plugin_name} 卸载失败")
                    return False
            
            # 从已加载插件字典中移除插件
            del self.plugins[plugin_name]
            
            self.logger.info(f"插件 {plugin_name} 卸载成功")
            return True
        
        except Exception as e:
            self.logger.error(f"卸载插件 {plugin_name} 时发生错误: {e}", exc_info=True)
            return False
    
    async def enable_plugin(self, plugin_name: str) -> bool:
        """启用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否启用成功
        """
        # 检查插件是否已加载
        if plugin_name not in self.plugins:
            self.logger.warning(f"插件 {plugin_name} 未加载")
            return False
        
        # 获取插件实例
        plugin = self.plugins[plugin_name]
        
        # 检查插件是否已启用
        if plugin.enabled:
            self.logger.warning(f"插件 {plugin_name} 已经启用")
            return True
        
        try:
            # 调用插件启用方法
            if hasattr(plugin, "on_enable"):
                result = await plugin.on_enable()
                if not result:
                    self.logger.error(f"插件 {plugin_name} 启用失败")
                    return False
            
            # 从禁用插件列表中移除
            if plugin_name in self.disabled_plugins:
                self.disabled_plugins.remove(plugin_name)
                # 更新配置
                from src.utils.config import get_config
                config = get_config()
                config.set("plugins.disabled", self.disabled_plugins)
            
            self.logger.info(f"插件 {plugin_name} 启用成功")
            return True
        
        except Exception as e:
            self.logger.error(f"启用插件 {plugin_name} 时发生错误: {e}", exc_info=True)
            return False
    
    async def disable_plugin(self, plugin_name: str) -> bool:
        """禁用插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否禁用成功
        """
        # 检查插件是否已加载
        if plugin_name not in self.plugins:
            self.logger.warning(f"插件 {plugin_name} 未加载")
            return False
        
        # 获取插件实例
        plugin = self.plugins[plugin_name]
        
        # 检查插件是否已禁用
        if not plugin.enabled:
            self.logger.warning(f"插件 {plugin_name} 已经禁用")
            return True
        
        try:
            # 调用插件禁用方法
            if hasattr(plugin, "on_disable"):
                result = await plugin.on_disable()
                if not result:
                    self.logger.error(f"插件 {plugin_name} 禁用失败")
                    return False
            
            # 添加到禁用插件列表
            if plugin_name not in self.disabled_plugins:
                self.disabled_plugins.append(plugin_name)
                # 更新配置
                from src.utils.config import get_config
                config = get_config()
                config.set("plugins.disabled", self.disabled_plugins)
            
            self.logger.info(f"插件 {plugin_name} 禁用成功")
            return True
        
        except Exception as e:
            self.logger.error(f"禁用插件 {plugin_name} 时发生错误: {e}", exc_info=True)
            return False
    
    async def reload_plugin(self, plugin_name: str) -> bool:
        """重新加载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 是否重新加载成功
        """
        # 先卸载插件
        if plugin_name in self.plugins:
            if not await self.unload_plugin(plugin_name):
                return False
        
        # 再加载插件
        return await self.load_plugin(plugin_name)
    
    async def load_all_plugins(self) -> bool:
        """加载所有插件
        
        Returns:
            bool: 是否全部加载成功
        """
        # 检查插件目录是否存在
        if not os.path.exists(self.plugins_dir):
            self.logger.error(f"插件目录 {self.plugins_dir} 不存在")
            return False
        
        # 获取所有插件目录
        plugin_dirs = []
        for item in os.listdir(self.plugins_dir):
            item_path = os.path.join(self.plugins_dir, item)
            if os.path.isdir(item_path) and os.path.exists(os.path.join(item_path, "__init__.py")):
                plugin_dirs.append(item)
        
        # 加载所有插件
        success_count = 0
        for plugin_name in plugin_dirs:
            if await self.load_plugin(plugin_name):
                success_count += 1
        
        self.logger.info(f"共加载 {success_count}/{len(plugin_dirs)} 个插件")
        return success_count == len(plugin_dirs)
    
    async def unload_all_plugins(self) -> bool:
        """卸载所有插件
        
        Returns:
            bool: 是否全部卸载成功
        """
        # 获取所有已加载的插件
        plugin_names = list(self.plugins.keys())
        
        # 卸载所有插件
        success_count = 0
        for plugin_name in plugin_names:
            if await self.unload_plugin(plugin_name):
                success_count += 1
        
        self.logger.info(f"共卸载 {success_count}/{len(plugin_names)} 个插件")
        return success_count == len(plugin_names)
    
    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """获取插件实例
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            Optional[BasePlugin]: 插件实例，如果不存在则返回 None
        """
        return self.plugins.get(plugin_name)
    
    def get_all_plugins(self) -> Dict[str, BasePlugin]:
        """获取所有已加载的插件
        
        Returns:
            Dict[str, BasePlugin]: 插件名称到插件实例的映射
        """
        return self.plugins.copy()
    
    def get_enabled_plugins(self) -> Dict[str, BasePlugin]:
        """获取所有已启用的插件
        
        Returns:
            Dict[str, BasePlugin]: 插件名称到插件实例的映射
        """
        return {name: plugin for name, plugin in self.plugins.items() if plugin.enabled}
    
    def get_disabled_plugins(self) -> Dict[str, BasePlugin]:
        """获取所有已禁用的插件
        
        Returns:
            Dict[str, BasePlugin]: 插件名称到插件实例的映射
        """
        return {name: plugin for name, plugin in self.plugins.items() if not plugin.enabled} 