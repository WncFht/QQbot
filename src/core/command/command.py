"""
命令类定义
"""
from typing import Callable, List
from ncatbot.core.auth import PermissionLevel

class Command:
    """命令类，表示一个命令"""
    
    def __init__(self, name: str, handler: Callable, 
                 permission: PermissionLevel = PermissionLevel.NORMAL,
                 description: str = "", usage: str = "", 
                 aliases: List[str] = None, **kwargs):
        """初始化命令
        
        Args:
            name: 命令名称
            handler: 命令处理函数
            permission: 命令权限等级
            description: 命令描述
            usage: 命令用法
            aliases: 命令别名列表
            **kwargs: 其他参数
        """
        self.name = name
        self.handler = handler
        self.permission = permission
        self.description = description
        self.usage = usage
        self.aliases = aliases or []
        self.kwargs = kwargs
    
    def __str__(self) -> str:
        """返回命令的字符串表示
        
        Returns:
            str: 命令的字符串表示
        """
        return f"Command(name={self.name}, permission={self.permission}, aliases={self.aliases})" 