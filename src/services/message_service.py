"""
消息服务模块
"""
import asyncio
import threading
import time
from ncatbot.utils.logger import get_log
from utils.message_parser import MessageParser

logger = get_log()

class MessageService:
    """消息服务类"""
    
    def __init__(self, bot, db, target_groups):
        """初始化消息服务"""
        self.bot = bot
        self.db = db
        self.target_groups = target_groups
        self.message_queue = []
        self.queue_lock = threading.Lock()
        self.last_history_fetch_time = time.time()
    
    def save_message(self, message_data):
        """保存消息到队列"""
        try:
            # 将消息添加到队列
            with self.queue_lock:
                self.message_queue.append(message_data)
            
            # 如果队列长度超过10，立即处理
            if len(self.message_queue) >= 10:
                self.process_message_queue()
        except Exception as e:
            logger.error(f"保存消息失败: {e}")
    
    def process_message_queue(self):
        """处理消息队列"""
        try:
            with self.queue_lock:
                if not self.message_queue:
                    return
                
                messages_to_process = self.message_queue.copy()
                self.message_queue.clear()
            
            for msg in messages_to_process:
                # 使用消息解析器解析消息
                parsed_msg = MessageParser.parse_group_message(msg)
                if parsed_msg:
                    # 保存到数据库
                    self.db.save_message(
                        parsed_msg["message_id"],
                        parsed_msg["group_id"],
                        parsed_msg["user_id"],
                        parsed_msg["message_type"],
                        parsed_msg["content"],
                        parsed_msg["raw_message"],
                        parsed_msg["time"],
                        parsed_msg["message_seq"],
                        parsed_msg["message_data"]
                    )
            
            logger.info(f"已保存 {len(messages_to_process)} 条消息到数据库")
        except Exception as e:
            logger.error(f"处理消息队列失败: {e}")
    
    async def get_group_msg_history(self, group_id, message_seq=0, count=None):
        """获取群历史消息"""
        try:
            if count is None:
                count = 20  # 默认获取20条
            
            response = await self.bot.api.get_group_msg_history(
                group_id=group_id,
                message_seq=message_seq,
                count=count,
                reverse_order=False
            )
            
            if response and "data" in response and "messages" in response["data"]:
                messages = response["data"]["messages"]
                logger.info(f"获取到群 {group_id} 历史消息 {len(messages)} 条")
                
                # 保存历史消息
                for msg_data in messages:
                    # 构造消息对象
                    from ncatbot.core.message import GroupMessage
                    msg = GroupMessage(msg_data)
                    self.save_message(msg)
                
                return messages
            else:
                logger.error(f"获取群 {group_id} 历史消息失败")
                return []
        except Exception as e:
            logger.error(f"获取群历史消息异常: {e}")
            return []
    
    async def fetch_all_history(self):
        """获取所有目标群的历史消息"""
        for group_id in self.target_groups:
            # 获取最近的消息序号
            message_seq = self.db.get_latest_message_seq(group_id)
            
            # 获取历史消息
            await self.get_group_msg_history(group_id, message_seq, 20)
            await asyncio.sleep(2)  # 避免请求过快
        
        self.last_history_fetch_time = time.time()
    
    def fetch_history_messages(self):
        """获取历史消息（异步）"""
        threading.Thread(target=self._fetch_history_messages_thread).start()
    
    def _fetch_history_messages_thread(self):
        """获取历史消息的线程函数"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetch_all_history())
        loop.close()
    
    def format_report(self, report):
        """格式化分析报告为文本"""
        text = f"群 {report['group_name']}({report['group_id']}) 活跃度报告\n"
        text += f"统计周期: 最近 {report['days']} 天\n"
        text += f"成员数: {report['member_count']}\n"
        text += f"消息总数: {report['message_count']}\n\n"
        
        text += "活跃用户排行:\n"
        for i, user in enumerate(report['active_users'][:5], 1):
            text += f"{i}. {user['display_name']}({user['user_id']}): {user['message_count']}条消息\n"
        
        text += "\n每日消息数:\n"
        for day in report['daily_activity'][-7:]:  # 最近7天
            text += f"{day['date']}: {day['count']}条\n"
        
        text += "\n热门关键词:\n"
        for word, count in report['keywords'][:10]:  # 前10个关键词
            text += f"{word}: {count}次\n"
        
        text += f"\n报告生成时间: {report['generated_at']}"
        return text 