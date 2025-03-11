"""
群消息处理模块
"""
import asyncio
from ncatbot.utils.logger import get_log
from ncatbot.core.message import GroupMessage

logger = get_log()

class GroupMessageHandler:
    """群消息处理类"""
    
    def __init__(self, bot, message_queue, db_manager, auth_manager, target_groups):
        """
        初始化群消息处理器
        
        Args:
            bot: 机器人实例
            message_queue: 消息队列
            db_manager: 数据库管理器
            auth_manager: 权限管理器
            target_groups: 目标群列表
        """
        self.bot = bot
        self.message_queue = message_queue
        self.db_manager = db_manager
        self.auth_manager = auth_manager
        self.target_groups = target_groups
        self.group_info_cache = {}
        self.group_members_cache = {}
    
    async def handle(self, msg: GroupMessage):
        """处理群消息"""
        try:
            # 只处理目标群的消息
            if str(msg.group_id) in [str(group_id) for group_id in self.target_groups]:
                logger.info(f"收到群 {msg.group_id} 消息: {msg.raw_message[:30]}...")
                
                # 解析消息
                from ..utils.message_parser import MessageParser
                parsed_msg = MessageParser.parse_group_message(msg)
                
                if parsed_msg:
                    # 保存到数据库
                    self.db_manager.execute(
                        """
                        INSERT OR REPLACE INTO messages 
                        (message_id, group_id, user_id, message_type, content, raw_message, time, message_seq, message_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
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
                    )
        except Exception as e:
            logger.error(f"处理群消息失败: {e}")
    
    def register(self):
        """注册群消息处理函数"""
        @self.bot.group_event()
        async def on_group_message(msg: GroupMessage):
            await self.handle(msg)
    
    async def get_group_list(self):
        """获取群列表"""
        try:
            response = await self.bot.api.get_group_list()
            if response and "data" in response:
                groups = response["data"]
                logger.info(f"获取到 {len(groups)} 个群")
                return groups
            else:
                logger.error("获取群列表失败")
                return []
        except Exception as e:
            logger.error(f"获取群列表异常: {e}")
            return []
    
    async def get_group_info(self, group_id):
        """获取群信息"""
        try:
            response = await self.bot.api.get_group_info(group_id)
            if response and "data" in response:
                group_info = response["data"]
                logger.info(f"获取到群 {group_id} 信息: {group_info.get('group_name')}")
                
                # 保存群信息到数据库
                self.db_manager.execute(
                    """
                    INSERT OR REPLACE INTO group_info (group_id, group_name, member_count, last_update)
                    VALUES (?, ?, ?, datetime('now'))
                    """,
                    (
                        group_id,
                        group_info.get("group_name"),
                        group_info.get("member_count")
                    )
                )
                
                # 更新缓存
                self.group_info_cache[str(group_id)] = group_info
                
                return group_info
            else:
                logger.error(f"获取群 {group_id} 信息失败")
                return None
        except Exception as e:
            logger.error(f"获取群信息异常: {e}")
            return None
    
    async def get_group_member_list(self, group_id):
        """获取群成员列表"""
        try:
            response = await self.bot.api.get_group_member_list(group_id)
            if response and "data" in response:
                members = response["data"]
                logger.info(f"获取到群 {group_id} 成员 {len(members)} 人")
                
                # 保存群成员信息到数据库
                for member in members:
                    self.db_manager.execute(
                        """
                        INSERT OR REPLACE INTO group_members 
                        (group_id, user_id, nickname, card, role, join_time, last_update)
                        VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                        """,
                        (
                            group_id,
                            member.get("user_id"),
                            member.get("nickname"),
                            member.get("card"),
                            member.get("role"),
                            member.get("join_time")
                        )
                    )
                
                # 更新缓存
                self.group_members_cache[str(group_id)] = members
                
                return members
            else:
                logger.error(f"获取群 {group_id} 成员列表失败")
                return []
        except Exception as e:
            logger.error(f"获取群成员列表异常: {e}")
            return []
    
    async def update_group_info(self):
        """更新所有目标群的信息和成员列表"""
        for group_id in self.target_groups:
            await self.get_group_info(group_id)
            await self.get_group_member_list(group_id)
            await asyncio.sleep(1)  # 避免请求过快
    
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
                    
                    # 解析消息
                    from ..utils.message_parser import MessageParser
                    parsed_msg = MessageParser.parse_group_message(msg)
                    
                    if parsed_msg:
                        # 保存到数据库
                        self.db_manager.execute(
                            """
                            INSERT OR REPLACE INTO messages 
                            (message_id, group_id, user_id, message_type, content, raw_message, time, message_seq, message_data)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
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
                        )
                
                return messages
            else:
                logger.error(f"获取群 {group_id} 历史消息失败")
                return []
        except Exception as e:
            logger.error(f"获取群历史消息异常: {e}")
            return []
    
    async def fetch_history_messages(self):
        """获取所有目标群的历史消息"""
        for group_id in self.target_groups:
            # 获取最近的消息序号
            result = self.db_manager.query_one(
                """
                SELECT message_seq FROM messages 
                WHERE group_id = ? 
                ORDER BY time DESC LIMIT 1
                """,
                (group_id,)
            )
            
            message_seq = 0 if result is None else result[0]
            
            # 获取历史消息
            await self.get_group_msg_history(group_id, message_seq, 20)
            await asyncio.sleep(2)  # 避免请求过快 