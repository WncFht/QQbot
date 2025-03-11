"""
统计插件，用于统计群聊活跃度和消息数量
"""
from typing import Optional, List, Dict, Any
import time
import sqlite3
from pathlib import Path

from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.core.element import MessageChain, Text

bot = CompatibleEnrollment  # 兼容回调函数注册器

class StatsPlugin(BasePlugin):
    """统计插件类"""
    name = "stats"  # 插件名称（必写）
    version = "1.0.0"  # 插件版本（必写）
    description = "统计插件，用于统计群聊活跃度和消息数量"
    author = "NapcatBot"
    
    def __init__(self):
        """初始化插件"""
        super().__init__()
        self.db_path = Path("data") / self.name / "stats.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 创建消息表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    group_id TEXT,
                    user_id TEXT,
                    message_type TEXT,
                    content TEXT,
                    raw_message TEXT,
                    time INTEGER,
                    message_seq TEXT,
                    message_data TEXT
                )
            """)
            # 创建群组表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    group_id TEXT PRIMARY KEY,
                    last_active_time INTEGER
                )
            """)
            # 创建成员表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS members (
                    group_id TEXT,
                    user_id TEXT,
                    last_sent_time INTEGER,
                    PRIMARY KEY (group_id, user_id)
                )
            """)
            conn.commit()
    
    def _insert_message(self, message_info: Dict[str, Any]):
        """插入消息记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO messages 
                (message_id, group_id, user_id, message_type, content, raw_message, time, message_seq, message_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    message_info["message_id"],
                    message_info["group_id"],
                    message_info["user_id"],
                    message_info["message_type"],
                    message_info["content"],
                    message_info["raw_message"],
                    message_info["time"],
                    message_info["message_seq"],
                    message_info["message_data"]
                )
            )
            conn.commit()
    
    def _update_group_activity(self, group_id: str):
        """更新群组活跃时间"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO groups (group_id, last_active_time) VALUES (?, ?)",
                (group_id, int(time.time()))
            )
            conn.commit()
    
    def _update_member_activity(self, group_id: str, user_id: str):
        """更新成员活跃时间"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO members (group_id, user_id, last_sent_time) VALUES (?, ?, ?)",
                (group_id, user_id, int(time.time()))
            )
            conn.commit()
    
    def _get_group_stats(self, group_id: str, days: int) -> Dict[str, Any]:
        """获取群组统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            time_before = int(time.time()) - days * 86400
            
            # 获取总消息数
            cursor.execute(
                "SELECT COUNT(*) FROM messages WHERE group_id = ?",
                (group_id,)
            )
            total_messages = cursor.fetchone()[0]
            
            # 获取时间段内消息数
            cursor.execute(
                "SELECT COUNT(*) FROM messages WHERE group_id = ? AND time > ?",
                (group_id, time_before)
            )
            period_messages = cursor.fetchone()[0]
            
            # 获取发言人数
            cursor.execute(
                "SELECT COUNT(DISTINCT user_id) FROM messages WHERE group_id = ? AND time > ?",
                (group_id, time_before)
            )
            speakers_count = cursor.fetchone()[0]
            
            # 获取群成员数
            cursor.execute(
                "SELECT COUNT(DISTINCT user_id) FROM members WHERE group_id = ?",
                (group_id,)
            )
            members_count = cursor.fetchone()[0] or 1  # 避免除以0
            
            return {
                "total_messages": total_messages,
                "period_messages": period_messages,
                "speakers_count": speakers_count,
                "members_count": members_count,
                "activity_rate": speakers_count / members_count
            }
    
    def _get_active_users(self, group_id: str, days: int, limit: int) -> List[Dict[str, Any]]:
        """获取活跃用户排行"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            time_before = int(time.time()) - days * 86400
            
            cursor.execute(
                """
                SELECT user_id, COUNT(*) as count
                FROM messages 
                WHERE group_id = ? AND time > ?
                GROUP BY user_id
                ORDER BY count DESC
                LIMIT ?
                """,
                (group_id, time_before, limit)
            )
            
            return [
                {"user_id": row[0], "message_count": row[1]}
                for row in cursor.fetchall()
            ]
    
    def _get_user_stats(self, group_id: Optional[str], user_id: str, days: int) -> Dict[str, Any]:
        """获取用户统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            time_before = int(time.time()) - days * 86400
            
            if group_id:
                # 获取用户在指定群的消息数
                cursor.execute(
                    "SELECT COUNT(*) FROM messages WHERE group_id = ? AND user_id = ?",
                    (group_id, user_id)
                )
                total_count = cursor.fetchone()[0]
                
                # 获取时间段内消息数
                cursor.execute(
                    "SELECT COUNT(*) FROM messages WHERE group_id = ? AND user_id = ? AND time > ?",
                    (group_id, user_id, time_before)
                )
                period_count = cursor.fetchone()[0]
                
                # 获取群总消息数
                cursor.execute(
                    "SELECT COUNT(*) FROM messages WHERE group_id = ?",
                    (group_id,)
                )
                group_total = cursor.fetchone()[0] or 1  # 避免除以0
                
                return {
                    "total_count": total_count,
                    "period_count": period_count,
                    "percentage": total_count / group_total
                }
            else:
                # 获取用户所有消息数
                cursor.execute(
                    "SELECT COUNT(*) FROM messages WHERE user_id = ?",
                    (user_id,)
                )
                total_count = cursor.fetchone()[0]
                
                # 获取用户活跃群数
                cursor.execute(
                    "SELECT COUNT(DISTINCT group_id) FROM messages WHERE user_id = ?",
                    (user_id,)
                )
                active_groups = cursor.fetchone()[0]
                
                return {
                    "total_count": total_count,
                    "active_groups": active_groups
                }
    
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
        """处理群消息事件，记录消息"""
        try:
            # 解析消息
            message_info = {
                "message_id": msg.message_id,
                "group_id": msg.group_id,
                "user_id": msg.user_id,
                "message_type": "group",
                "content": str(msg.message),
                "raw_message": msg.raw_message,
                "time": int(time.time()),
                "message_seq": msg.message_seq,
                "message_data": str(msg.message)
            }
            
            # 保存消息
            self._insert_message(message_info)
            
            # 更新群和成员活跃时间
            self._update_group_activity(msg.group_id)
            self._update_member_activity(msg.group_id, msg.user_id)
            
            # 处理命令
            if msg.raw_message.startswith("/stats"):
                await self._handle_stats_cmd(msg)
            elif msg.raw_message.startswith("/rank"):
                await self._handle_rank_cmd(msg)
            elif msg.raw_message.startswith("/mystat"):
                await self._handle_mystat_cmd(msg)
        except Exception as e:
            self.logger.error(f"处理群消息失败: {e}", exc_info=True)
    
    async def _handle_stats_cmd(self, msg: GroupMessage):
        """处理 stats 命令"""
        try:
            # 解析参数
            args = msg.raw_message.split(" ", 1)
            days = int(args[1]) if len(args) > 1 else 7
            if days <= 0:
                days = 7
        except ValueError:
            days = 7
        
        # 获取统计信息
        stats = self._get_group_stats(msg.group_id, days)
        
        # 构建回复消息
        message = (
            f"群 {msg.group_id} 统计信息（{days}天）：\n"
            f"总消息数：{stats['total_messages']}\n"
            f"期间消息数：{stats['period_messages']}\n"
            f"发言人数：{stats['speakers_count']}\n"
            f"群成员数：{stats['members_count']}\n"
            f"活跃度：{stats['activity_rate']:.2%}"
        )
        
        # 发送回复
        await msg.reply(text=message)
    
    async def _handle_rank_cmd(self, msg: GroupMessage):
        """处理 rank 命令"""
        try:
            # 解析参数
            args = msg.raw_message.split()
            days = int(args[1]) if len(args) > 1 else 7
            limit = int(args[2]) if len(args) > 2 else 10
            
            if days <= 0:
                days = 7
            if limit <= 0 or limit > 50:
                limit = 10
        except (ValueError, IndexError):
            days = 7
            limit = 10
        
        # 获取活跃用户
        active_users = self._get_active_users(msg.group_id, days, limit)
        
        # 构建回复消息
        message = f"群 {msg.group_id} 发言排行（{days}天）：\n"
        
        if not active_users:
            message += "暂无数据"
        else:
            for i, user in enumerate(active_users):
                message += f"{i+1}. {user['user_id']}: {user['message_count']} 条消息\n"
        
        # 发送回复
        await msg.reply(text=message)
    
    async def _handle_mystat_cmd(self, msg: GroupMessage | PrivateMessage):
        """处理 mystat 命令"""
        try:
            # 解析参数
            args = msg.raw_message.split(" ", 1)
            days = int(args[1]) if len(args) > 1 else 7
            if days <= 0:
                days = 7
        except ValueError:
            days = 7
        
        # 获取统计信息
        if isinstance(msg, GroupMessage):
            stats = self._get_user_stats(msg.group_id, msg.user_id, days)
            message = (
                f"用户 {msg.sender.card or msg.sender.nickname} 在本群的统计信息：\n"
                f"总发言数：{stats['total_count']} 条\n"
                f"{days}天内发言数：{stats['period_count']} 条\n"
                f"占群消息比例：{stats['percentage']:.2%}"
            )
        else:
            stats = self._get_user_stats(None, msg.user_id, days)
            message = (
                f"用户 {msg.sender.nickname} 的统计信息：\n"
                f"总发言数：{stats['total_count']} 条\n"
                f"活跃群数：{stats['active_groups']} 个"
            )
        
        # 发送回复
        await msg.reply(text=message) 