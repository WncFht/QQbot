"""
权限管理模块
"""
from enum import Enum
from typing import Dict, List, Optional, Union
from ncatbot.utils.logger import get_log

logger = get_log()

class PermissionLevel(Enum):
    """权限级别枚举"""
    BANNED = -1      # 黑名单
    NORMAL = 0       # 普通用户
    ADMIN = 1        # 管理员
    SUPER_ADMIN = 2  # 超级管理员
    OWNER = 3        # 拥有者

class AuthManager:
    """权限管理类"""
    
    def __init__(self, config_path: str = "auth_config.json"):
        """初始化权限管理器
        
        Args:
            config_path: 权限配置文件路径
        """
        self.config_path = config_path
        self.user_permissions: Dict[str, PermissionLevel] = {}
        self.command_permissions: Dict[str, PermissionLevel] = {}
        self.group_permissions: Dict[str, Dict[str, PermissionLevel]] = {}
        self.owner_id: Optional[str] = None
        self.super_admins: List[str] = []
        self.admins: List[str] = []
        self.banned_users: List[str] = []
        
        # 默认命令权限
        self.default_command_permissions = {
            "status": PermissionLevel.NORMAL,
            "backup": PermissionLevel.ADMIN,
            "update_group_info": PermissionLevel.ADMIN,
            "fetch_history": PermissionLevel.ADMIN,
            "analyze": PermissionLevel.NORMAL,
            "plugin_list": PermissionLevel.NORMAL,
            "permission": PermissionLevel.SUPER_ADMIN,
            "help": PermissionLevel.NORMAL
        }
        
        # 加载配置
        self.load_config()
    
    def load_config(self) -> bool:
        """加载权限配置
        
        Returns:
            bool: 是否加载成功
        """
        try:
            import json
            import os
            
            if not os.path.exists(self.config_path):
                logger.warning(f"权限配置文件 {self.config_path} 不存在，使用默认配置")
                self.command_permissions = self.default_command_permissions
                return False
            
            with open(self.config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # 加载用户权限
            if "owner" in config:
                self.owner_id = str(config["owner"])
            
            if "super_admins" in config:
                self.super_admins = [str(uid) for uid in config["super_admins"]]
            
            if "admins" in config:
                self.admins = [str(uid) for uid in config["admins"]]
            
            if "banned_users" in config:
                self.banned_users = [str(uid) for uid in config["banned_users"]]
            
            # 加载命令权限
            if "command_permissions" in config:
                for cmd, level in config["command_permissions"].items():
                    self.command_permissions[cmd] = PermissionLevel(level)
            else:
                self.command_permissions = self.default_command_permissions
            
            # 加载群组权限
            if "group_permissions" in config:
                for group_id, perms in config["group_permissions"].items():
                    self.group_permissions[str(group_id)] = {}
                    for user_id, level in perms.items():
                        self.group_permissions[str(group_id)][str(user_id)] = PermissionLevel(level)
            
            logger.info(f"权限配置加载成功: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"加载权限配置失败: {e}", exc_info=True)
            self.command_permissions = self.default_command_permissions
            return False
    
    def save_config(self) -> bool:
        """保存权限配置
        
        Returns:
            bool: 是否保存成功
        """
        try:
            import json
            import os
            
            config = {
                "owner": self.owner_id,
                "super_admins": self.super_admins,
                "admins": self.admins,
                "banned_users": self.banned_users,
                "command_permissions": {cmd: level.value for cmd, level in self.command_permissions.items()},
                "group_permissions": {
                    group_id: {user_id: level.value for user_id, level in perms.items()}
                    for group_id, perms in self.group_permissions.items()
                }
            }
            
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)
            
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            
            logger.info(f"权限配置保存成功: {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"保存权限配置失败: {e}", exc_info=True)
            return False
    
    def get_user_permission(self, user_id: Union[int, str]) -> PermissionLevel:
        """获取用户权限级别
        
        Args:
            user_id: 用户QQ号
            
        Returns:
            PermissionLevel: 用户权限级别
        """
        user_id = str(user_id)
        
        # 检查是否是拥有者
        if self.owner_id and user_id == self.owner_id:
            return PermissionLevel.OWNER
        
        # 检查是否是超级管理员
        if user_id in self.super_admins:
            return PermissionLevel.SUPER_ADMIN
        
        # 检查是否是管理员
        if user_id in self.admins:
            return PermissionLevel.ADMIN
        
        # 检查是否是黑名单用户
        if user_id in self.banned_users:
            return PermissionLevel.BANNED
        
        # 默认为普通用户
        return PermissionLevel.NORMAL
    
    def get_group_user_permission(self, group_id: Union[int, str], user_id: Union[int, str]) -> PermissionLevel:
        """获取用户在特定群组中的权限级别
        
        Args:
            group_id: 群号
            user_id: 用户QQ号
            
        Returns:
            PermissionLevel: 用户在群组中的权限级别
        """
        group_id = str(group_id)
        user_id = str(user_id)
        
        # 先检查全局权限
        global_perm = self.get_user_permission(user_id)
        if global_perm != PermissionLevel.NORMAL:
            return global_perm
        
        # 检查群组特定权限
        if group_id in self.group_permissions and user_id in self.group_permissions[group_id]:
            return self.group_permissions[group_id][user_id]
        
        # 默认为普通用户
        return PermissionLevel.NORMAL
    
    def get_command_permission(self, command: str) -> PermissionLevel:
        """获取命令所需的权限级别
        
        Args:
            command: 命令名称
            
        Returns:
            PermissionLevel: 命令所需的权限级别
        """
        if command in self.command_permissions:
            return self.command_permissions[command]
        
        # 默认为普通用户权限
        return PermissionLevel.NORMAL
    
    def check_command_permission(self, user_id: Union[int, str], command: str) -> bool:
        """检查用户是否有权限执行命令
        
        Args:
            user_id: 用户QQ号
            command: 命令名称
            
        Returns:
            bool: 是否有权限
        """
        user_perm = self.get_user_permission(user_id)
        cmd_perm = self.get_command_permission(command)
        
        # 黑名单用户无权执行任何命令
        if user_perm == PermissionLevel.BANNED:
            return False
        
        # 检查权限级别
        return user_perm.value >= cmd_perm.value
    
    def check_group_command_permission(self, group_id: Union[int, str], user_id: Union[int, str], command: str) -> bool:
        """检查用户是否有权限在特定群组中执行命令
        
        Args:
            group_id: 群号
            user_id: 用户QQ号
            command: 命令名称
            
        Returns:
            bool: 是否有权限
        """
        user_perm = self.get_group_user_permission(group_id, user_id)
        cmd_perm = self.get_command_permission(command)
        
        # 黑名单用户无权执行任何命令
        if user_perm == PermissionLevel.BANNED:
            return False
        
        # 检查权限级别
        return user_perm.value >= cmd_perm.value
    
    def set_user_permission(self, user_id: Union[int, str], level: PermissionLevel) -> bool:
        """设置用户权限级别
        
        Args:
            user_id: 用户QQ号
            level: 权限级别
            
        Returns:
            bool: 是否设置成功
        """
        user_id = str(user_id)
        
        # 根据权限级别更新相应列表
        if level == PermissionLevel.OWNER:
            self.owner_id = user_id
            # 从其他列表中移除
            if user_id in self.super_admins:
                self.super_admins.remove(user_id)
            if user_id in self.admins:
                self.admins.remove(user_id)
            if user_id in self.banned_users:
                self.banned_users.remove(user_id)
        elif level == PermissionLevel.SUPER_ADMIN:
            if user_id not in self.super_admins:
                self.super_admins.append(user_id)
            # 从其他列表中移除
            if user_id == self.owner_id:
                self.owner_id = None
            if user_id in self.admins:
                self.admins.remove(user_id)
            if user_id in self.banned_users:
                self.banned_users.remove(user_id)
        elif level == PermissionLevel.ADMIN:
            if user_id not in self.admins:
                self.admins.append(user_id)
            # 从其他列表中移除
            if user_id == self.owner_id:
                self.owner_id = None
            if user_id in self.super_admins:
                self.super_admins.remove(user_id)
            if user_id in self.banned_users:
                self.banned_users.remove(user_id)
        elif level == PermissionLevel.BANNED:
            if user_id not in self.banned_users:
                self.banned_users.append(user_id)
            # 从其他列表中移除
            if user_id == self.owner_id:
                self.owner_id = None
            if user_id in self.super_admins:
                self.super_admins.remove(user_id)
            if user_id in self.admins:
                self.admins.remove(user_id)
        elif level == PermissionLevel.NORMAL:
            # 从所有列表中移除
            if user_id == self.owner_id:
                self.owner_id = None
            if user_id in self.super_admins:
                self.super_admins.remove(user_id)
            if user_id in self.admins:
                self.admins.remove(user_id)
            if user_id in self.banned_users:
                self.banned_users.remove(user_id)
        
        # 保存配置
        return self.save_config()
    
    def set_group_user_permission(self, group_id: Union[int, str], user_id: Union[int, str], level: PermissionLevel) -> bool:
        """设置用户在特定群组中的权限级别
        
        Args:
            group_id: 群号
            user_id: 用户QQ号
            level: 权限级别
            
        Returns:
            bool: 是否设置成功
        """
        group_id = str(group_id)
        user_id = str(user_id)
        
        # 确保群组存在于权限配置中
        if group_id not in self.group_permissions:
            self.group_permissions[group_id] = {}
        
        # 设置权限
        if level == PermissionLevel.NORMAL:
            # 如果是普通用户，直接移除特定权限
            if user_id in self.group_permissions[group_id]:
                del self.group_permissions[group_id][user_id]
        else:
            self.group_permissions[group_id][user_id] = level
        
        # 保存配置
        return self.save_config()
    
    def set_command_permission(self, command: str, level: PermissionLevel) -> bool:
        """设置命令所需的权限级别
        
        Args:
            command: 命令名称
            level: 权限级别
            
        Returns:
            bool: 是否设置成功
        """
        self.command_permissions[command] = level
        
        # 保存配置
        return self.save_config() 