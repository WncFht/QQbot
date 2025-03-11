"""
机器人核心模块
负责初始化和管理机器人实例
"""
import os
import asyncio
from typing import Dict, List, Any, Optional, Callable

from ncatbot.core import BotClient
from ncatbot.utils.config import config as ncatbot_config

from ..event.bus import EventBus
from ..event.types import (
    Event,
    GroupMessageEvent,
    PrivateMessageEvent,
    GroupMemberIncreaseEvent,
    GroupMemberDecreaseEvent,
)

from src.utils.singleton import Singleton
from src.core.utils import BaseComponent, catch_exceptions, log_execution_time

class Bot(Singleton, BaseComponent):
    """机器人核心类"""
    
    def __init__(self, config_path: str = "config.json"):
        """初始化机器人
        
        Args:
            config_path: 配置文件路径
        """
        # 如果已经初始化过，则直接返回
        if hasattr(self, "initialized") and self.initialized:
            return
            
        # 初始化基类
        super().__init__("bot")
        
        # 加载配置
        from src.utils.config import get_config
        self.config = get_config(config_path)
        
        # 获取事件总线
        from ..event.bus import EventBus
        self.event_bus = EventBus()
        
        # 创建 NcatBot 客户端
        self.client = None
        
        # 标记为已初始化
        self.initialized = True
    
    @catch_exceptions
    async def init(self) -> bool:
        """初始化机器人"""
        # 创建数据目录
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("plugins", exist_ok=True)
        
        # 配置 NcatBot
        bot_uin = self.config.get("bot_uin")
        ws_uri = self.config.get("ws_uri")
        token = self.config.get("token")
        
        if not bot_uin:
            self.log_error("未配置机器人QQ号")
            return False
        
        if not ws_uri:
            self.log_error("未配置WebSocket URI")
            return False
        
        # 设置 NcatBot 配置
        ncatbot_config.set_bot_uin(bot_uin)
        ncatbot_config.set_ws_uri(ws_uri)
        ncatbot_config.set_token(token)
        
        # 创建 NcatBot 客户端
        self.client = BotClient()
        
        # 注册事件处理器
        @self.client.on_message
        async def handle_message(event):
            # 转换为自定义事件
            if event.message_type == "group":
                # 群消息
                custom_event = GroupMessageEvent(
                    message_id=event.message_id,
                    group_id=event.group_id,
                    sender_id=event.user_id,
                    content=event.message,
                    raw_message=event.raw_message,
                    time=event.time,
                    data=event.__dict__
                )
            else:
                # 私聊消息
                custom_event = PrivateMessageEvent(
                    message_id=event.message_id,
                    sender_id=event.user_id,
                    content=event.message,
                    raw_message=event.raw_message,
                    time=event.time,
                    data=event.__dict__
                )
            
            # 发布事件
            await self.event_bus.publish(custom_event)
        
        self.log_info("机器人初始化成功")
        return True
    
    @catch_exceptions
    @log_execution_time
    async def start(self) -> bool:
        """启动机器人"""
        if not self.client:
            if not await self.init():
                return False
        
        # 启动 NcatBot 客户端
        await self.client.start()
        
        self.log_info("机器人启动成功")
        return True
    
    @catch_exceptions
    async def stop(self) -> bool:
        """停止机器人"""
        if self.client:
            # 停止 NcatBot 客户端
            await self.client.stop()
        
        self.log_info("机器人停止成功")
        return True
    
    def get_api(self):
        """获取 API 接口
        
        Returns:
            BotAPI: API 接口
        """
        if not self.client:
            self.log_error("机器人未初始化")
            return None
        
        return self.client.api
    
    def on_message(self, handler: Callable):
        """注册消息处理器
        
        Args:
            handler: 消息处理器
            
        Returns:
            Callable: 处理器
        """
        if not self.client:
            self.log_error("机器人未初始化")
            return handler
        
        self.client.on_message(handler)
        return handler
    
    def on_event(self, event_type: str):
        """注册事件处理器装饰器
        
        Args:
            event_type: 事件类型
            
        Returns:
            Callable: 装饰器
        """
        def decorator(handler):
            self.event_bus.subscribe(event_type, handler)
            return handler
        return decorator
    
    def on_group_message(self, handler: Callable):
        """注册群消息处理器
        
        Args:
            handler: 群消息处理器
            
        Returns:
            Callable: 处理器
        """
        self.event_bus.subscribe("group_message", handler)
        return handler
    
    def on_private_message(self, handler: Callable):
        """注册私聊消息处理器
        
        Args:
            handler: 私聊消息处理器
            
        Returns:
            Callable: 处理器
        """
        self.event_bus.subscribe("private_message", handler)
        return handler 