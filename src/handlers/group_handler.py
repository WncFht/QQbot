"""
群消息处理模块
"""
from ncatbot.utils.logger import get_log
from ncatbot.core.message import GroupMessage

logger = get_log()

class GroupMessageHandler:
    """群消息处理类"""
    
    def __init__(self, bot, message_service, target_groups):
        """初始化群消息处理器"""
        self.bot = bot
        self.message_service = message_service
        self.target_groups = target_groups
    
    async def handle(self, msg: GroupMessage):
        """处理群消息"""
        try:
            # 只处理目标群的消息
            if str(msg.group_id) in [str(group_id) for group_id in self.target_groups]:
                logger.info(f"收到群 {msg.group_id} 消息: {msg.raw_message[:30]}...")
                self.message_service.save_message(msg)
        except Exception as e:
            logger.error(f"处理群消息失败: {e}")
    
    def register(self):
        """注册群消息处理函数"""
        @self.bot.group_event()
        async def on_group_message(msg: GroupMessage):
            await self.handle(msg) 