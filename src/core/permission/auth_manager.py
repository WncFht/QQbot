"""
权限管理器模块
"""
import os
import json
import re
from typing import Dict, List, Union, Optional, Any, Callable
from ncatbot.utils.logger import get_log
from ncatbot.core.message import GroupMessage, PrivateMessage

from .permission import Permission, PermissionLevel

logger = get_log()

class AuthManager:
    """权限管理器类"""
    
    def __init__(self, permission_path: str = "data/permission.json"):
        """
        初始化权限管理器
        
        Args:
            permission_path: 权限配置文件路径
        """
        self.permission_path = permission_path
        self.permissions = {}
        self.command_permissions = {}
        self.plugin_permissions = {}
        self.default_permissions = {}
        self.superusers = []
        self.owner = ""
        
        # 确保权限文件目录存在
        os.makedirs(os.path.dirname(permission_path), exist_ok=True)
        
        # 加载权限配置
        self.load_permissions()
    
    def load_permissions(self) -> None:
        """从配置文件加载权限数据"""
        try:
            if os.path.exists(self.permission_path):
                with open(self.permission_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                    # 加载超级用户和拥有者
                    self.superusers = data.get("superusers", [])
                    self.owner = data.get("owner", "")
                    
                    # 加载用户权限
                    self.permissions = data.get("permissions", {})
                    
                    # 加载命令权限
                    self.command_permissions = data.get("command_permissions", {})
                    
                    # 加载插件权限
                    self.plugin_permissions = data.get("plugin_permissions", {})
                    
                    # 加载默认权限
                    self.default_permissions = data.get("default_permissions", {})
                    
                logger.info(f"已加载权限配置: {self.permission_path}")
            else:
                logger.warning(f"权限配置文件不存在，将创建默认配置: {self.permission_path}")
                self.create_default_permissions()
                self.save_permissions()
        except Exception as e:
            logger.error(f"加载权限配置失败: {e}")
            self.create_default_permissions()
    
    def create_default_permissions(self) -> None:
        """创建默认权限配置"""
        self.superusers = []
        self.owner = ""
        self.permissions = {}
        self.command_permissions = {}
        self.plugin_permissions = {}
        self.default_permissions = {
            "global": {
                "level": PermissionLevel.NORMAL.value
            }
        }
    
    def save_permissions(self) -> None:
        """保存权限配置到文件"""
        try:
            data = {
                "superusers": self.superusers,
                "owner": self.owner,
                "permissions": self.permissions,
                "command_permissions": self.command_permissions,
                "plugin_permissions": self.plugin_permissions,
                "default_permissions": self.default_permissions
            }
            
            with open(self.permission_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
            logger.info(f"已保存权限配置: {self.permission_path}")
        except Exception as e:
            logger.error(f"保存权限配置失败: {e}")
    
    def get_user_permission(self, user_id: str, group_id: Optional[str] = None) -> Permission:
        """
        获取用户权限
        
        Args:
            user_id: 用户ID
            group_id: 群ID，如果为None则获取全局权限
            
        Returns:
            Permission: 用户权限
        """
        # 检查是否为拥有者
        if user_id == self.owner:
            return Permission(PermissionLevel.OWNER)
        
        # 检查是否为超级管理员
        if user_id in self.superusers:
            return Permission(PermissionLevel.SUPER_ADMIN)
        
        # 获取用户在指定群的权限
        if group_id:
            # 检查群组用户权限
            group_permissions = self.permissions.get(group_id, {})
            if user_id in group_permissions:
                level_value = group_permissions[user_id].get("level", PermissionLevel.NORMAL.value)
                return Permission(PermissionLevel(level_value))
        
        # 获取用户全局权限
        global_permissions = self.permissions.get("global", {})
        if user_id in global_permissions:
            level_value = global_permissions[user_id].get("level", PermissionLevel.NORMAL.value)
            return Permission(PermissionLevel(level_value))
        
        # 返回默认权限
        default_level = self.default_permissions.get("global", {}).get("level", PermissionLevel.NORMAL.value)
        return Permission(PermissionLevel(default_level))
    
    def set_user_permission(self, user_id: str, level: Union[PermissionLevel, int], group_id: Optional[str] = None) -> bool:
        """
        设置用户权限
        
        Args:
            user_id: 用户ID
            level: 权限级别
            group_id: 群ID，如果为None则设置全局权限
            
        Returns:
            bool: 是否设置成功
        """
        try:
            # 转换权限级别
            if isinstance(level, PermissionLevel):
                level_value = level.value
            else:
                level_value = level
            
            # 设置用户在指定群的权限
            if group_id:
                if group_id not in self.permissions:
                    self.permissions[group_id] = {}
                
                self.permissions[group_id][user_id] = {"level": level_value}
            else:
                # 设置用户全局权限
                if "global" not in self.permissions:
                    self.permissions["global"] = {}
                
                self.permissions["global"][user_id] = {"level": level_value}
            
            # 保存权限配置
            self.save_permissions()
            return True
        except Exception as e:
            logger.error(f"设置用户权限失败: {e}")
            return False
    
    def check_command_permission(self, user_id: str, command: str, group_id: Optional[str] = None) -> bool:
        """
        检查用户是否有执行命令的权限
        
        Args:
            user_id: 用户ID
            command: 命令名称
            group_id: 群ID，如果为None则检查全局权限
            
        Returns:
            bool: 是否有权限
        """
        # 获取用户权限
        user_permission = self.get_user_permission(user_id, group_id)
        
        # 检查命令权限
        command_config = self.command_permissions.get(command, {})
        
        # 如果命令没有配置权限，则使用默认权限
        if not command_config:
            default_level = self.default_permissions.get("commands", {}).get(command, PermissionLevel.NORMAL.value)
            required_permission = Permission(PermissionLevel(default_level))
        else:
            # 检查群组命令权限
            if group_id and group_id in command_config:
                required_level = command_config[group_id].get("level", PermissionLevel.NORMAL.value)
                required_permission = Permission(PermissionLevel(required_level))
            else:
                # 检查全局命令权限
                required_level = command_config.get("global", {}).get("level", PermissionLevel.NORMAL.value)
                required_permission = Permission(PermissionLevel(required_level))
        
        return user_permission >= required_permission
    
    def set_command_permission(self, command: str, level: Union[PermissionLevel, int], group_id: Optional[str] = None) -> bool:
        """
        设置命令权限
        
        Args:
            command: 命令名称
            level: 权限级别
            group_id: 群ID，如果为None则设置全局权限
            
        Returns:
            bool: 是否设置成功
        """
        try:
            # 转换权限级别
            if isinstance(level, PermissionLevel):
                level_value = level.value
            else:
                level_value = level
            
            # 确保命令权限配置存在
            if command not in self.command_permissions:
                self.command_permissions[command] = {}
            
            # 设置命令在指定群的权限
            if group_id:
                self.command_permissions[command][group_id] = {"level": level_value}
            else:
                # 设置命令全局权限
                self.command_permissions[command]["global"] = {"level": level_value}
            
            # 保存权限配置
            self.save_permissions()
            return True
        except Exception as e:
            logger.error(f"设置命令权限失败: {e}")
            return False
    
    def check_plugin_permission(self, user_id: str, plugin_name: str, group_id: Optional[str] = None) -> bool:
        """
        检查用户是否有使用插件的权限
        
        Args:
            user_id: 用户ID
            plugin_name: 插件名称
            group_id: 群ID，如果为None则检查全局权限
            
        Returns:
            bool: 是否有权限
        """
        # 获取用户权限
        user_permission = self.get_user_permission(user_id, group_id)
        
        # 检查插件权限
        plugin_config = self.plugin_permissions.get(plugin_name, {})
        
        # 如果插件没有配置权限，则使用默认权限
        if not plugin_config:
            default_level = self.default_permissions.get("plugins", {}).get(plugin_name, PermissionLevel.NORMAL.value)
            required_permission = Permission(PermissionLevel(default_level))
        else:
            # 检查群组插件权限
            if group_id and group_id in plugin_config:
                required_level = plugin_config[group_id].get("level", PermissionLevel.NORMAL.value)
                required_permission = Permission(PermissionLevel(required_level))
            else:
                # 检查全局插件权限
                required_level = plugin_config.get("global", {}).get("level", PermissionLevel.NORMAL.value)
                required_permission = Permission(PermissionLevel(required_level))
        
        return user_permission >= required_permission
    
    def set_plugin_permission(self, plugin_name: str, level: Union[PermissionLevel, int], group_id: Optional[str] = None) -> bool:
        """
        设置插件权限
        
        Args:
            plugin_name: 插件名称
            level: 权限级别
            group_id: 群ID，如果为None则设置全局权限
            
        Returns:
            bool: 是否设置成功
        """
        try:
            # 转换权限级别
            if isinstance(level, PermissionLevel):
                level_value = level.value
            else:
                level_value = level
            
            # 确保插件权限配置存在
            if plugin_name not in self.plugin_permissions:
                self.plugin_permissions[plugin_name] = {}
            
            # 设置插件在指定群的权限
            if group_id:
                self.plugin_permissions[plugin_name][group_id] = {"level": level_value}
            else:
                # 设置插件全局权限
                self.plugin_permissions[plugin_name]["global"] = {"level": level_value}
            
            # 保存权限配置
            self.save_permissions()
            return True
        except Exception as e:
            logger.error(f"设置插件权限失败: {e}")
            return False
    
    def set_superusers(self, superusers: List[str]) -> bool:
        """
        设置超级用户列表
        
        Args:
            superusers: 超级用户ID列表
            
        Returns:
            bool: 是否设置成功
        """
        try:
            self.superusers = superusers
            self.save_permissions()
            return True
        except Exception as e:
            logger.error(f"设置超级用户失败: {e}")
            return False
    
    def set_owner(self, owner: str) -> bool:
        """
        设置拥有者
        
        Args:
            owner: 拥有者ID
            
        Returns:
            bool: 是否设置成功
        """
        try:
            self.owner = owner
            self.save_permissions()
            return True
        except Exception as e:
            logger.error(f"设置拥有者失败: {e}")
            return False
    
    def get_permission_decorator(self, required_level: Union[PermissionLevel, int, Permission]):
        """
        获取权限检查装饰器
        
        Args:
            required_level: 所需的权限级别
            
        Returns:
            Callable: 权限检查装饰器
        """
        def decorator(func):
            async def wrapper(msg: Union[GroupMessage, PrivateMessage], *args, **kwargs):
                # 检查权限
                has_permission = await Permission.check_permission(msg, required_level, self)
                
                if has_permission:
                    return await func(msg, *args, **kwargs)
                else:
                    # 权限不足，可以在这里添加回复逻辑
                    if hasattr(msg, 'reply'):
                        await msg.reply("权限不足，无法执行该操作")
                    return None
            
            return wrapper
        
        return decorator 