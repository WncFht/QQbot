"""
消息分析插件
"""
import sqlite3
import json
from datetime import datetime, timedelta
from ncatbot.utils.logger import get_log
from ncatbot.plugin import BasePlugin, CompatibleEnrollment
from ncatbot.plugin.event import EventBus

logger = get_log()
bot = CompatibleEnrollment  # 兼容回调函数注册器

class MessageAnalyzer(BasePlugin):
    """消息分析类"""
    
    # 插件信息
    name = "MessageAnalyzer"
    version = "1.0.0"
    
    # 插件依赖 - 必须是字典类型
    dependencies = {}
    
    # 元数据
    meta_data = {
        "description": "分析群消息活跃度和关键词统计",
        "author": "QQBot"
    }
    
    def __init__(self, event_bus=None, **kwargs):
        """初始化分析器"""
        if event_bus is None:
            event_bus = EventBus()
        super().__init__(event_bus, **kwargs)
        
        # 设置数据库路径
        self.database_path = kwargs.get("database_path", "messages.db")
        self.db_conn = None
        self.connect()
    
    def connect(self):
        """连接数据库"""
        try:
            self.db_conn = sqlite3.connect(self.database_path, check_same_thread=False)
            return True
        except Exception as e:
            logger.error(f"连接数据库失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.db_conn:
            self.db_conn.close()
            self.db_conn = None
    
    def get_active_users(self, group_id, days=7, limit=10):
        """获取群内活跃用户"""
        try:
            # 计算时间范围
            now = datetime.now()
            start_time = int((now - timedelta(days=days)).timestamp())
            
            cursor = self.db_conn.cursor()
            cursor.execute('''
            SELECT user_id, COUNT(*) as msg_count 
            FROM messages 
            WHERE group_id = ? AND time > ?
            GROUP BY user_id 
            ORDER BY msg_count DESC
            LIMIT ?
            ''', (group_id, start_time, limit))
            
            results = cursor.fetchall()
            
            # 获取用户昵称
            active_users = []
            for user_id, msg_count in results:
                cursor.execute('''
                SELECT nickname, card FROM group_members
                WHERE group_id = ? AND user_id = ?
                ''', (group_id, user_id))
                
                user_info = cursor.fetchone()
                if user_info:
                    nickname, card = user_info
                    display_name = card if card else nickname
                else:
                    display_name = f"用户{user_id}"
                
                active_users.append({
                    "user_id": user_id,
                    "display_name": display_name,
                    "message_count": msg_count
                })
            
            return active_users
        except Exception as e:
            logger.error(f"获取活跃用户失败: {e}")
            return []
    
    def get_keyword_stats(self, group_id, days=7, limit=20):
        """获取关键词统计"""
        try:
            # 计算时间范围
            now = datetime.now()
            start_time = int((now - timedelta(days=days)).timestamp())
            
            cursor = self.db_conn.cursor()
            cursor.execute('''
            SELECT raw_message FROM messages 
            WHERE group_id = ? AND time > ?
            ''', (group_id, start_time))
            
            messages = cursor.fetchall()
            
            # 简单的词频统计
            word_count = {}
            for msg in messages:
                if not msg[0]:
                    continue
                    
                # 简单分词（按空格分割）
                words = msg[0].split()
                for word in words:
                    if len(word) > 1:  # 忽略单字符
                        word_count[word] = word_count.get(word, 0) + 1
            
            # 排序并限制数量
            sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
            return sorted_words[:limit]
        except Exception as e:
            logger.error(f"获取关键词统计失败: {e}")
            return []
    
    def get_daily_activity(self, group_id, days=7):
        """获取每日活跃度"""
        try:
            # 计算时间范围
            now = datetime.now()
            start_time = int((now - timedelta(days=days)).timestamp())
            
            cursor = self.db_conn.cursor()
            cursor.execute('''
            SELECT time FROM messages 
            WHERE group_id = ? AND time > ?
            ''', (group_id, start_time))
            
            timestamps = cursor.fetchall()
            
            # 按天统计消息数量
            daily_counts = {}
            for ts in timestamps:
                day = datetime.fromtimestamp(ts[0]).strftime("%Y-%m-%d")
                daily_counts[day] = daily_counts.get(day, 0) + 1
            
            # 确保所有日期都有数据
            result = []
            for i in range(days):
                day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
                result.append({
                    "date": day,
                    "count": daily_counts.get(day, 0)
                })
            
            return sorted(result, key=lambda x: x["date"])
        except Exception as e:
            logger.error(f"获取每日活跃度失败: {e}")
            return []
    
    def generate_report(self, group_id, days=7):
        """生成群活跃度报告"""
        try:
            # 获取群信息
            cursor = self.db_conn.cursor()
            cursor.execute('SELECT group_name, member_count FROM group_info WHERE group_id = ?', (group_id,))
            group_info = cursor.fetchone()
            
            if not group_info:
                return {"error": "群信息不存在"}
            
            group_name, member_count = group_info
            
            # 获取消息总数
            cursor.execute('''
            SELECT COUNT(*) FROM messages 
            WHERE group_id = ? AND time > ?
            ''', (group_id, int((datetime.now() - timedelta(days=days)).timestamp())))
            
            message_count = cursor.fetchone()[0]
            
            # 获取活跃用户
            active_users = self.get_active_users(group_id, days)
            
            # 获取每日活跃度
            daily_activity = self.get_daily_activity(group_id, days)
            
            # 获取关键词统计
            keywords = self.get_keyword_stats(group_id, days)
            
            return {
                "group_id": group_id,
                "group_name": group_name,
                "member_count": member_count,
                "days": days,
                "message_count": message_count,
                "active_users": active_users,
                "daily_activity": daily_activity,
                "keywords": keywords,
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return {"error": str(e)}
    
    # 插件接口方法
    async def on_load(self):
        """插件加载时调用"""
        logger.info(f"消息分析插件已加载: {self.name} v{self.version}")
        return True
    
    async def on_unload(self):
        """插件卸载时调用"""
        self.close()
        logger.info("消息分析插件已卸载")
        return True
        
    def _init_(self):
        """初始化插件"""
        self.connect()
        
    def _close_(self):
        """关闭插件"""
        self.close() 