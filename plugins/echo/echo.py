"""
回声插件 - 简单的插件示例
"""
import json
from ncatbot.utils.logger import get_log
from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.plugin.event import EventBus
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.core.element import MessageChain, Text

logger = get_log()
bot = CompatibleEnrollment  # 兼容回调函数注册器

class EchoPlugin(BasePlugin):
    """回声插件类"""
    
    # 插件信息
    name = "EchoPlugin"
    version = "1.0.0"
    
    # 插件依赖 - 必须是字典类型
    dependencies = {}
    
    # 元数据
    meta_data = {
        "description": "简单的回声插件，用于演示插件开发",
        "author": "QQBot"
    }
    
    def __init__(self, event_bus=None, **kwargs):
        """初始化插件"""
        if event_bus is None:
            event_bus = EventBus()
        super().__init__(event_bus, **kwargs)
        
        # 命令前缀
        self.command_prefix = kwargs.get("command_prefix", "/echo ")
        
        # 注册事件处理函数
        self.register_handlers()
    
    def register_handlers(self):
        """注册事件处理函数"""
        # 注册群消息处理函数
        @bot.group_event()
        async def on_group_message(msg: GroupMessage):
            await self.handle_group_message(msg)
        
        # 注册私聊消息处理函数
        @bot.private_event()
        async def on_private_message(msg: PrivateMessage):
            await self.handle_private_message(msg)
    
    async def handle_group_message(self, msg: GroupMessage):
        """处理群消息"""
        try:
            # 检查是否是命令
            if not msg.raw_message.startswith(self.command_prefix):
                return
            
            # 提取命令内容
            content = msg.raw_message[len(self.command_prefix):].strip()
            if not content:
                await msg.reply(text="请输入要回声的内容")
                return
            
            # 回复消息
            await msg.reply(text=f"回声: {content}")
            logger.info(f"回声插件响应群 {msg.group_id} 用户 {msg.user_id} 的命令: {content}")
        except Exception as e:
            logger.error(f"处理群消息失败: {e}", exc_info=True)
    
    async def handle_private_message(self, msg: PrivateMessage):
        """处理私聊消息"""
        try:
            # 检查是否是命令
            if not msg.raw_message.startswith(self.command_prefix):
                return
            
            # 提取命令内容
            content = msg.raw_message[len(self.command_prefix):].strip()
            if not content:
                await msg.reply(text="请输入要回声的内容")
                return
            
            # 回复消息
            await msg.reply(text=f"回声: {content}")
            logger.info(f"回声插件响应用户 {msg.user_id} 的命令: {content}")
        except Exception as e:
            logger.error(f"处理私聊消息失败: {e}", exc_info=True)
    
    # 插件接口方法
    async def on_load(self):
        """插件加载时调用"""
        logger.info(f"回声插件已加载: {self.name} v{self.version}")
        return True
    
    async def on_unload(self):
        """插件卸载时调用"""
        logger.info("回声插件已卸载")
        return True 