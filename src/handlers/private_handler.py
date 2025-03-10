"""
私聊消息处理模块
"""
from ncatbot.utils.logger import get_log
from ncatbot.core.message import PrivateMessage

logger = get_log()

class PrivateMessageHandler:
    """私聊消息处理类"""
    
    def __init__(self, bot, message_service, backup_service, group_service, target_groups):
        """初始化私聊消息处理器"""
        self.bot = bot
        self.message_service = message_service
        self.backup_service = backup_service
        self.group_service = group_service
        self.target_groups = target_groups
    
    async def handle(self, msg: PrivateMessage):
        """处理私聊消息"""
        try:
            if msg.raw_message == "状态":
                await msg.reply(text=f"机器人正在监听 {len(self.target_groups)} 个群")
            elif msg.raw_message == "备份":
                self.backup_service.backup_database()
                await msg.reply(text="数据库备份完成")
            elif msg.raw_message == "更新群信息":
                self.group_service.update_group_info()
                await msg.reply(text="群信息更新任务已启动")
            elif msg.raw_message == "获取历史消息":
                self.message_service.fetch_history_messages()
                await msg.reply(text="历史消息获取任务已启动")
            elif msg.raw_message.startswith("分析 "):
                await self._handle_analyze_command(msg)
            elif msg.raw_message == "插件列表":
                await self._handle_plugin_list_command(msg)
        except Exception as e:
            logger.error(f"处理私聊消息失败: {e}")
            await msg.reply(text=f"处理命令失败: {e}")
    
    async def _handle_analyze_command(self, msg: PrivateMessage):
        """处理分析命令"""
        # 格式: 分析 群号 [天数]
        parts = msg.raw_message.split()
        if len(parts) >= 2:
            group_id = parts[1]
            days = int(parts[2]) if len(parts) > 2 else 7
            
            if group_id in [str(g) for g in self.target_groups]:
                await msg.reply(text=f"正在分析群 {group_id} 最近 {days} 天的数据，请稍候...")
                
                # 获取分析器插件
                analyzer = None
                for plugin in self.bot.plugin_sys.plugins.values():
                    if hasattr(plugin, "name") and plugin.name == "MessageAnalyzer":
                        analyzer = plugin
                        break
                
                if analyzer:
                    # 设置数据库路径
                    analyzer.database_path = self.message_service.db.database_path
                    if not analyzer.db_conn:
                        analyzer.connect()
                        
                    report = analyzer.generate_report(group_id, days)
                    
                    if "error" in report:
                        await msg.reply(text=f"分析失败: {report['error']}")
                    else:
                        # 生成简单的文本报告
                        text_report = self.message_service.format_report(report)
                        await msg.reply(text=text_report)
                else:
                    await msg.reply(text="分析插件未加载，无法生成报告")
            else:
                await msg.reply(text=f"群 {group_id} 不在监听列表中")
        else:
            await msg.reply(text="格式错误，正确格式: 分析 群号 [天数]")
    
    async def _handle_plugin_list_command(self, msg: PrivateMessage):
        """处理插件列表命令"""
        plugins_info = []
        for plugin in self.bot.plugin_sys.plugins.values():
            if hasattr(plugin, "name") and hasattr(plugin, "version"):
                plugins_info.append(f"{plugin.name} v{plugin.version}")
        
        if plugins_info:
            await msg.reply(text=f"已加载的插件:\n" + "\n".join(plugins_info))
        else:
            await msg.reply(text="未加载任何插件")
    
    def register(self):
        """注册私聊消息处理函数"""
        @self.bot.private_event()
        async def on_private_message(msg: PrivateMessage):
            await self.handle(msg) 