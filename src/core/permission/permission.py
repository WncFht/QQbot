"""
权限定义模块
"""
from enum import Enum
from typing import Union, List, Dict, Any, Optional, Callable
from ncatbot.core.message import GroupMessage, PrivateMessage

class PermissionLevel(Enum):
    """权限级别枚举"""
    BANNED = -1      # 被禁止的用户
    NORMAL = 0       # 普通用户
    ADMIN = 1        # 管理员
    SUPER_ADMIN = 2  # 超级管理员
    OWNER = 3        # 拥有者

class Permission:
    """权限类"""
    
    def __init__(self, level: PermissionLevel = PermissionLevel.NORMAL):
        """初始化权限"""
        self.level = level
    
    def __str__(self) -> str:
        """返回权限级别的字符串表示"""
        return self.level.name
    
    def __repr__(self) -> str:
        """返回权限级别的字符串表示"""
        return f"Permission({self.level.name})"
    
    def __eq__(self, other) -> bool:
        """比较权限级别是否相等"""
        if isinstance(other, Permission):
            return self.level == other.level
        elif isinstance(other, PermissionLevel):
            return self.level == other
        elif isinstance(other, int):
            return self.level.value == other
        return False
    
    def __lt__(self, other) -> bool:
        """比较权限级别是否小于其他权限级别"""
        if isinstance(other, Permission):
            return self.level.value < other.level.value
        elif isinstance(other, PermissionLevel):
            return self.level.value < other.value
        elif isinstance(other, int):
            return self.level.value < other
        return False
    
    def __le__(self, other) -> bool:
        """比较权限级别是否小于等于其他权限级别"""
        if isinstance(other, Permission):
            return self.level.value <= other.level.value
        elif isinstance(other, PermissionLevel):
            return self.level.value <= other.value
        elif isinstance(other, int):
            return self.level.value <= other
        return False
    
    def __gt__(self, other) -> bool:
        """比较权限级别是否大于其他权限级别"""
        if isinstance(other, Permission):
            return self.level.value > other.level.value
        elif isinstance(other, PermissionLevel):
            return self.level.value > other.value
        elif isinstance(other, int):
            return self.level.value > other
        return False
    
    def __ge__(self, other) -> bool:
        """比较权限级别是否大于等于其他权限级别"""
        if isinstance(other, Permission):
            return self.level.value >= other.level.value
        elif isinstance(other, PermissionLevel):
            return self.level.value >= other.value
        elif isinstance(other, int):
            return self.level.value >= other
        return False
    
    @staticmethod
    async def check_permission(
        msg: Union[GroupMessage, PrivateMessage], 
        required_level: Union[PermissionLevel, int, 'Permission'],
        auth_manager: 'AuthManager'
    ) -> bool:
        """
        检查消息发送者是否有足够的权限
        
        Args:
            msg: 消息对象
            required_level: 所需的权限级别
            auth_manager: 权限管理器
            
        Returns:
            bool: 是否有足够的权限
        """
        # 私聊消息默认拥有普通用户权限
        if isinstance(msg, PrivateMessage):
            user_id = str(msg.user_id)
            user_permission = auth_manager.get_user_permission(user_id)
            
            # 将required_level转换为Permission对象进行比较
            if isinstance(required_level, PermissionLevel):
                required_permission = Permission(required_level)
            elif isinstance(required_level, int):
                required_permission = Permission(PermissionLevel(required_level))
            else:
                required_permission = required_level
                
            return user_permission >= required_permission
        
        # 群聊消息需要检查群权限和用户权限
        elif isinstance(msg, GroupMessage):
            group_id = str(msg.group_id)
            user_id = str(msg.user_id)
            
            # 检查用户在该群的权限
            user_permission = auth_manager.get_user_permission(user_id, group_id)
            
            # 将required_level转换为Permission对象进行比较
            if isinstance(required_level, PermissionLevel):
                required_permission = Permission(required_level)
            elif isinstance(required_level, int):
                required_permission = Permission(PermissionLevel(required_level))
            else:
                required_permission = required_level
                
            return user_permission >= required_permission
        
        return False 