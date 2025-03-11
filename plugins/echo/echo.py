"""
回声插件 - 简单的插件示例
"""
from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.core.element import MessageChain, Text

bot = CompatibleEnrollment  # 兼容回调函数注册器

class EchoPlugin(BasePlugin):
    """回声插件类"""
    
    name = "echo"  # 插件名称（必写）
    version = "1.0.0"  # 插件版本（必写）
    description = "简单的回声插件，用于演示插件开发"
    author = "NapcatBot"
    
    # 插件依赖
    dependencies = {}
    
    def __init__(self):
        """初始化插件"""
        super().__init__()
        # 命令前缀
        self.command_prefix = "/echo "
    
    async def on_load(self):
        """插件加载时执行的操作"""
        self.logger.info(f"插件 {self.name} v{self.version} 已加载")
        return True
    
    async def on_unload(self):
        """插件卸载时执行的操作"""
        self.logger.info(f"插件 {self.name} 已卸载")
        return True
    
    @bot.group_event()
    async def on_group_message(self, msg: GroupMessage):
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
            self.logger.info(f"回声插件响应群 {msg.group_id} 用户 {msg.user_id} 的命令: {content}")
        except Exception as e:
            self.logger.error(f"处理群消息失败: {e}", exc_info=True)
    
    @bot.private_event()
    async def on_private_message(self, msg: PrivateMessage):
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
            self.logger.info(f"回声插件响应用户 {msg.user_id} 的命令: {content}")
        except Exception as e:
            self.logger.error(f"处理私聊消息失败: {e}", exc_info=True) 