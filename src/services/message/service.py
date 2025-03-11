"""
消息服务实现
"""
import asyncio
import time
from typing import List, Optional
from datetime import datetime

from utils.logger import get_logger
from utils.message_parser import MessageParser
from .models import MessageModel

logger = get_logger(__name__)

class MessageService:
    """消息服务类"""
    
    def __init__(self, bot, message_repository, target_groups):
        """初始化消息服务
        
        Args:
            bot: 机器人实例
            message_repository: 消息仓储实例
            target_groups: 目标群组列表
        """
        self.bot = bot
        self.message_repository = message_repository
        self.target_groups = target_groups
        self.last_history_fetch_time = time.time()

    async def save_message(self, message_data: dict) -> bool:
        """保存消息
        
        Args:
            message_data: 消息数据字典
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 解析消息数据
            parsed_msg = MessageParser.parse_group_message(message_data)
            if not parsed_msg:
                return False
                
            # 创建消息模型
            message = MessageModel.from_dict(parsed_msg)
            
            # 保存到仓储
            await self.message_repository.save(message)
            logger.info(f"消息已保存: {message.message_id}")
            return True
            
        except Exception as e:
            logger.error(f"保存消息失败: {e}")
            return False

    async def get_group_messages(
        self,
        group_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[MessageModel]:
        """获取群组消息
        
        Args:
            group_id: 群组ID
            start_time: 开始时间
            end_time: 结束时间
            limit: 限制条数
            
        Returns:
            List[MessageModel]: 消息列表
        """
        try:
            return await self.message_repository.get_by_group(
                group_id,
                start_time,
                end_time,
                limit
            )
        except Exception as e:
            logger.error(f"获取群组消息失败: {e}")
            return []

    async def get_group_msg_history(
        self,
        group_id: int,
        message_seq: int = 0,
        count: Optional[int] = None
    ) -> List[dict]:
        """获取群历史消息
        
        Args:
            group_id: 群组ID
            message_seq: 消息序号
            count: 获取数量
            
        Returns:
            List[dict]: 历史消息列表
        """
        try:
            if count is None:
                count = 20

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
                    await self.save_message(msg_data)
                
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
            latest_message = await self.message_repository.get_latest_message(group_id)
            message_seq = latest_message.message_seq if latest_message else 0
            
            # 获取历史消息
            await self.get_group_msg_history(group_id, message_seq, 20)
            await asyncio.sleep(2)  # 避免请求过快
        
        self.last_history_fetch_time = time.time()

    def format_report(self, report: dict) -> str:
        """格式化分析报告为文本
        
        Args:
            report: 报告数据字典
            
        Returns:
            str: 格式化后的报告文本
        """
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