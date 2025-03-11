"""
命令管理模块，用于注册和处理命令
"""
import asyncio
import re
import inspect
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from ncatbot.core.event import Event
from ncatbot.core.message import GroupMessage, PrivateMessage
from src.utils.logger import get_logger
from src.utils.message_parser import MessageParser
from src.utils.config import get_config
from .auth import PermissionLevel, AuthManager

logger = get_logger("command_manager")
config = get_config()
auth_manager = AuthManager()
message_parser = MessageParser()

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

class CommandManager:
    """命令管理类，用于注册和处理命令"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(CommandManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化命令管理器"""
        # 避免重复初始化
        if self._initialized:
            return
        
        # 命令字典，键为命令名称，值为命令对象
        self.commands: Dict[str, Command] = {}
        # 命令别名字典，键为别名，值为命令名称
        self.aliases: Dict[str, str] = {}
        # 命令前缀列表
        self.prefixes: List[str] = ['/', '#']
        
        self._initialized = True
        
        # 从配置中加载命令前缀
        prefixes = config.get("commands.prefixes", ['/', '#'])
        if isinstance(prefixes, list):
            self.set_prefixes(prefixes)
    
    def set_prefixes(self, prefixes: List[str]):
        """设置命令前缀
        
        Args:
            prefixes: 命令前缀列表
        """
        self.prefixes = prefixes
        message_parser.set_command_prefixes(prefixes)
        logger.info(f"设置命令前缀: {prefixes}")
    
    def register_command(self, name: str, handler: Callable, 
                        permission: PermissionLevel = PermissionLevel.NORMAL,
                        description: str = "", usage: str = "", 
                        aliases: List[str] = None, **kwargs) -> bool:
        """注册命令
        
        Args:
            name: 命令名称
            handler: 命令处理函数
            permission: 命令权限等级
            description: 命令描述
            usage: 命令用法
            aliases: 命令别名列表
            **kwargs: 其他参数
            
        Returns:
            bool: 是否成功
        """
        try:
            # 检查命令是否已注册
            if name in self.commands:
                logger.warning(f"命令已注册: {name}")
                return False
            
            # 检查别名是否已被使用
            if aliases:
                for alias in aliases:
                    if alias in self.aliases:
                        logger.warning(f"命令别名已被使用: {alias}")
                        return False
            
            # 创建命令对象
            command = Command(
                name=name,
                handler=handler,
                permission=permission,
                description=description,
                usage=usage,
                aliases=aliases or [],
                **kwargs
            )
            
            # 注册命令
            self.commands[name] = command
            
            # 注册别名
            if aliases:
                for alias in aliases:
                    self.aliases[alias] = name
            
            logger.info(f"注册命令成功: {command}")
            return True
        except Exception as e:
            logger.error(f"注册命令失败: {name}, {e}", exc_info=True)
            return False
    
    def unregister_command(self, name: str) -> bool:
        """注销命令
        
        Args:
            name: 命令名称
            
        Returns:
            bool: 是否成功
        """
        try:
            # 检查命令是否已注册
            if name not in self.commands:
                logger.warning(f"命令未注册: {name}")
                return False
            
            # 获取命令对象
            command = self.commands[name]
            
            # 注销别名
            for alias in command.aliases:
                if alias in self.aliases:
                    del self.aliases[alias]
            
            # 注销命令
            del self.commands[name]
            
            logger.info(f"注销命令成功: {name}")
            return True
        except Exception as e:
            logger.error(f"注销命令失败: {name}, {e}", exc_info=True)
            return False
    
    def get_command(self, name: str) -> Optional[Command]:
        """获取命令
        
        Args:
            name: 命令名称或别名
            
        Returns:
            Optional[Command]: 命令对象，如果不存在则返回None
        """
        try:
            # 检查是否是别名
            if name in self.aliases:
                name = self.aliases[name]
            
            # 返回命令对象
            return self.commands.get(name)
        except Exception as e:
            logger.error(f"获取命令失败: {name}, {e}", exc_info=True)
            return None
    
    def get_all_commands(self) -> Dict[str, Command]:
        """获取所有命令
        
        Returns:
            Dict[str, Command]: 命令字典，键为命令名称，值为命令对象
        """
        return self.commands.copy()
    
    def get_commands_by_permission(self, permission: PermissionLevel) -> Dict[str, Command]:
        """获取指定权限等级的命令
        
        Args:
            permission: 权限等级
            
        Returns:
            Dict[str, Command]: 命令字典，键为命令名称，值为命令对象
        """
        try:
            result = {}
            for name, command in self.commands.items():
                if command.permission <= permission:
                    result[name] = command
            return result
        except Exception as e:
            logger.error(f"获取指定权限等级的命令失败: {permission}, {e}", exc_info=True)
            return {}
    
    async def handle_message(self, event: Event) -> bool:
        """处理消息事件
        
        Args:
            event: 消息事件
            
        Returns:
            bool: 是否成功处理
        """
        try:
            # 检查事件类型
            if not isinstance(event, (GroupMessage, PrivateMessage)):
                return False
            
            # 获取消息文本
            message_text = event.raw_message
            
            # 解析命令
            command_result = message_parser.parse_command(message_text)
            if not command_result:
                return False
            
            command_name, args_text = command_result
            
            # 获取命令对象
            command = self.get_command(command_name)
            if not command:
                logger.debug(f"命令不存在: {command_name}")
                return False
            
            # 检查权限
            user_id = event.user_id
            group_id = getattr(event, 'group_id', None)
            
            if not auth_manager.check_command_permission(user_id, command.name, group_id):
                logger.warning(f"用户权限不足: {user_id}, 命令: {command.name}")
                return False
            
            # 调用命令处理函数
            await self._call_async_or_sync(command.handler, event, args_text, **command.kwargs)
            
            logger.info(f"处理命令成功: {command.name}, 用户: {user_id}, 参数: {args_text}")
            return True
        except Exception as e:
            logger.error(f"处理消息事件失败: {e}", exc_info=True)
            return False
    
    async def _call_async_or_sync(self, func: Callable, *args, **kwargs) -> Any:
        """调用异步或同步函数
        
        Args:
            func: 函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 函数返回值
        """
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

# 创建全局命令管理器实例
command_manager = CommandManager()

def get_command_manager() -> CommandManager:
    """获取命令管理器实例
    
    Returns:
        CommandManager: 命令管理器实例
    """
    return command_manager 