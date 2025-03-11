"""
示例插件的主要实现
"""
from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.core.element import MessageChain, Text
from ncatbot.core.event import Event

bot = CompatibleEnrollment  # 兼容回调函数注册器

class ExamplePlugin(BasePlugin):
    """示例插件类"""
    name = "example"  # 插件名称（必写）
    version = "1.0.0"  # 插件版本（必写）
    description = "示例插件，展示插件开发的基本结构"
    author = "NapcatBot"
    
    async def on_load(self):
        """插件加载时执行的操作"""
        self.logger.info(f"插件 {self.name} v{self.version} 已加载")
        
        # 初始化数据
        if "count" not in self.data:
            self.data["count"] = 0
    
    async def on_unload(self):
        """插件卸载时执行的操作"""
        self.logger.info(f"插件 {self.name} 已卸载")
        return True
    
    @bot.group_event()
    async def on_group_message(self, msg: GroupMessage):
        """处理群消息事件"""
        if msg.raw_message.startswith("/hello"):
            await self._handle_hello(msg)
        elif msg.raw_message.startswith("/echo"):
            await self._handle_echo(msg)
    
    @bot.private_event()
    async def on_private_message(self, msg: PrivateMessage):
        """处理私聊消息事件"""
        if msg.raw_message.startswith("/hello"):
            await self._handle_hello(msg)
        elif msg.raw_message.startswith("/echo"):
            await self._handle_echo(msg)
    
    async def _handle_hello(self, msg: GroupMessage | PrivateMessage):
        """处理 hello 命令"""
        # 获取参数
        args = msg.raw_message.split(" ", 1)
        name = args[1] if len(args) > 1 else None
        
        # 获取发送者信息
        sender_name = msg.sender.card or msg.sender.nickname if hasattr(msg, 'sender') else "陌生人"
        
        # 构建消息
        if name:
            message = f"你好，{name}！我是 NapcatBot。"
        else:
            message = f"你好，{sender_name}！我是 NapcatBot。"
        
        # 发送回复
        await msg.reply(text=message)
        
        # 更新计数
        self.data["count"] += 1
    
    async def _handle_echo(self, msg: GroupMessage | PrivateMessage):
        """处理 echo 命令"""
        args = msg.raw_message.split(" ", 1)
        if len(args) <= 1:
            await msg.reply(text="请输入要回显的内容")
            return
        
        # 发送回复
        await msg.reply(text=args[1])
        
        # 更新计数
        self.data["count"] += 1 