"""
NapcatBot 核心模块
提供机器人的核心功能，包括:
- 插件系统
- 事件系统
- 命令系统
- 权限系统
- 工具类
"""

# 工具类导出
from .utils import BaseComponent, catch_exceptions, log_execution_time

# 事件系统导出
from .event import EventBus, Event, EventHandler
from .event.types import (
    MessageEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
    NoticeEvent,
    RequestEvent
)

# 命令系统导出
from .command import (
    CommandManager,
    Command,
    CommandContext,
    CommandError,
    CommandParser
)

# 权限系统导出
from .auth import (
    AuthManager,
    PermissionLevel,
    PermissionError
)

# 插件系统导出
from .plugin import (
    Plugin,
    PluginManager,
    PluginError,
    PluginState
)

# 机器人核心导出
from .bot import Bot

__all__ = [
    # 工具类
    'BaseComponent',
    'catch_exceptions',
    'log_execution_time',
    
    # 事件系统
    'EventBus',
    'Event',
    'EventHandler',
    'MessageEvent',
    'GroupMessageEvent',
    'PrivateMessageEvent',
    'NoticeEvent',
    'RequestEvent',
    
    # 命令系统
    'CommandManager',
    'Command',
    'CommandContext',
    'CommandError',
    'CommandParser',
    
    # 权限系统
    'AuthManager',
    'PermissionLevel',
    'PermissionError',
    
    # 插件系统
    'Plugin',
    'PluginManager',
    'PluginError',
    'PluginState',
    
    # 机器人核心
    'Bot'
] 