"""
统计插件，用于统计群聊活跃度和消息数量
"""
from ncatbot.core.plugin import Plugin
from ncatbot.core.event import Event
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.core.element import MessageChain, Plain
from src.core import PermissionLevel, get_command_manager
from src.utils import Database, get_logger

class StatsPlugin(Plugin):
    """统计插件类"""
    
    def __init__(self):
        """初始化插件"""
        super().__init__()
        self.name = "stats"
        self.version = "1.0.0"
        self.description = "统计插件，用于统计群聊活跃度和消息数量"
        self.author = "NapcatBot"
        
        # 获取数据库实例
        self.db = Database()
        self.logger = get_logger("stats_plugin")
        
        # 注册命令
        cmd_mgr = get_command_manager()
        cmd_mgr.register_command(
            name="stats",
            handler=self.cmd_stats,
            permission=PermissionLevel.NORMAL,
            description="查看群聊统计信息",
            usage="/stats [天数=7]"
        )
        
        cmd_mgr.register_command(
            name="rank",
            handler=self.cmd_rank,
            permission=PermissionLevel.NORMAL,
            description="查看群聊发言排行",
            usage="/rank [天数=7] [数量=10]"
        )
        
        cmd_mgr.register_command(
            name="mystat",
            handler=self.cmd_mystat,
            permission=PermissionLevel.NORMAL,
            description="查看个人统计信息",
            usage="/mystat [天数=7]"
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
        """处理群消息事件，记录消息"""
        # 解析消息
        message_info = {
            "message_id": event.message_id,
            "group_id": event.group_id,
            "user_id": event.user_id,
            "message_type": "group",
            "content": str(event.message),
            "raw_message": event.raw_message,
            "time": event.time,
            "message_seq": event.message_seq,
            "message_data": str(event.message)
        }
        
        # 保存消息
        self.db.insert_message(message_info)
        
        # 更新群最后活跃时间
        self.db.update_group_last_active_time(event.group_id)
        
        # 更新成员最后发言时间
        self.db.update_member_last_sent_time(event.group_id, event.user_id)
    
    async def cmd_stats(self, event: Event, args: str):
        """处理 stats 命令，显示群聊统计信息"""
        if not isinstance(event, GroupMessage):
            await event.reply(MessageChain([Plain("该命令只能在群聊中使用")]))
            return
        
        # 解析参数
        try:
            days = int(args) if args else 7
            if days <= 0:
                days = 7
        except ValueError:
            days = 7
        
        # 获取群统计信息
        stats = self.db.get_group_stats(event.group_id, days)
        
        # 构建回复消息
        message = f"群 {event.group_id} 统计信息（{days}天）：\n"
        message += f"总消息数：{stats['total_messages']}\n"
        message += f"期间消息数：{stats['period_messages']}\n"
        message += f"发言人数：{stats['speakers_count']}\n"
        message += f"群成员数：{stats['members_count']}\n"
        message += f"活跃度：{stats['activity_rate']:.2%}"
        
        # 发送回复
        await event.reply(MessageChain([Plain(message)]))
    
    async def cmd_rank(self, event: Event, args: str):
        """处理 rank 命令，显示群聊发言排行"""
        if not isinstance(event, GroupMessage):
            await event.reply(MessageChain([Plain("该命令只能在群聊中使用")]))
            return
        
        # 解析参数
        args_list = args.split() if args else []
        try:
            days = int(args_list[0]) if len(args_list) > 0 else 7
            if days <= 0:
                days = 7
        except ValueError:
            days = 7
        
        try:
            limit = int(args_list[1]) if len(args_list) > 1 else 10
            if limit <= 0 or limit > 50:
                limit = 10
        except ValueError:
            limit = 10
        
        # 获取活跃用户
        active_users = self.db.get_active_users(event.group_id, days, limit)
        
        # 构建回复消息
        message = f"群 {event.group_id} 发言排行（{days}天）：\n"
        
        if not active_users:
            message += "暂无数据"
        else:
            for i, user in enumerate(active_users):
                user_name = user.get('card') or user.get('nickname') or str(user.get('user_id'))
                message += f"{i+1}. {user_name}: {user.get('message_count')} 条消息\n"
        
        # 发送回复
        await event.reply(MessageChain([Plain(message)]))
    
    async def cmd_mystat(self, event: Event, args: str):
        """处理 mystat 命令，显示个人统计信息"""
        # 解析参数
        try:
            days = int(args) if args else 7
            if days <= 0:
                days = 7
        except ValueError:
            days = 7
        
        user_id = event.user_id
        
        if isinstance(event, GroupMessage):
            group_id = event.group_id
            
            # 获取用户在该群的消息数量
            total_count = self.db.get_message_count(group_id, user_id)
            
            # 计算指定天数前的时间戳
            import time
            time_before = int(time.time()) - days * 86400
            
            # 获取用户在该群指定时间段内的消息
            period_messages = self.db.get_user_messages(group_id, user_id, 1000, 0)
            period_count = len([m for m in period_messages if m.get('time', 0) > time_before])
            
            # 获取群总消息数
            group_total = self.db.get_message_count(group_id)
            
            # 计算占比
            percentage = total_count / group_total if group_total > 0 else 0
            
            # 构建回复消息
            message = f"用户 {event.sender.card or event.sender.nickname} 在本群的统计信息：\n"
            message += f"总发言数：{total_count} 条\n"
            message += f"{days}天内发言数：{period_count} 条\n"
            message += f"占群消息比例：{percentage:.2%}"
        else:
            # 获取用户所有消息数量
            total_count = self.db.get_message_count(None, user_id)
            
            # 获取用户所在的群
            groups = self.db.get_user_groups(user_id)
            
            # 构建回复消息
            message = f"用户 {event.sender.nickname} 的统计信息：\n"
            message += f"总发言数：{total_count} 条\n"
            message += f"活跃群数：{len(groups)} 个"
        
        # 发送回复
        await event.reply(MessageChain([Plain(message)])) 