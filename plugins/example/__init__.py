"""
示例插件，展示插件开发的基本结构
"""
from .plugin import ExamplePlugin

__all__ = ["ExamplePlugin"]

from ncatbot.core.plugin import Plugin
from ncatbot.core.event import Event
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.core.element import MessageChain, Plain
from src.core import PermissionLevel, get_command_manager

class ExamplePlugin(Plugin):
    """示例插件类"""
    
    def __init__(self):
        """初始化插件"""
        super().__init__()
        self.name = "example"
        self.version = "1.0.0"
        self.description = "示例插件，展示插件开发的基本结构"
        self.author = "NapcatBot"
        
        # 注册命令
        cmd_mgr = get_command_manager()
        cmd_mgr.register_command(
            name="hello",
            handler=self.cmd_hello,
            permission=PermissionLevel.NORMAL,
            description="打招呼命令",
            usage="/hello [名字]",
            aliases=["hi"]
        )
        
        cmd_mgr.register_command(
            name="echo",
            handler=self.cmd_echo,
            permission=PermissionLevel.NORMAL,
            description="回显命令",
            usage="/echo <内容>"
        )
        
        self.logger.info(f"插件 {self.name} v{self.version} 已加载")
    
    async def on_enable(self):
        """插件启用时调用"""
        self.logger.info(f"插件 {self.name} 已启用")
        return True
    
    async def on_disable(self):
        """插件禁用时调用"""
        self.logger.info(f"插件 {self.name} 已禁用")
        return True
    
    async def on_group_message(self, event: GroupMessage):
        """处理群消息事件"""
        # 这里可以处理所有群消息
        pass
    
    async def on_private_message(self, event: PrivateMessage):
        """处理私聊消息事件"""
        # 这里可以处理所有私聊消息
        pass
    
    async def cmd_hello(self, event: Event, args: str):
        """处理 hello 命令"""
        # 获取发送者信息
        sender_name = event.sender.card or event.sender.nickname
        
        # 处理参数
        if args:
            name = args
            message = f"你好，{name}！我是 NapcatBot。"
        else:
            message = f"你好，{sender_name}！我是 NapcatBot。"
        
        # 构建回复消息
        reply = MessageChain([Plain(message)])
        
        # 发送回复
        if isinstance(event, GroupMessage):
            await event.reply(reply)
        else:
            await event.reply(reply)
    
    async def cmd_echo(self, event: Event, args: str):
        """处理 echo 命令"""
        if not args:
            await event.reply(MessageChain([Plain("请输入要回显的内容")]))
            return
        
        # 构建回复消息
        reply = MessageChain([Plain(args)])
        
        # 发送回复
        await event.reply(reply) 