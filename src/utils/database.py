"""
数据库模块，用于管理数据库连接和操作
"""
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple, Union
from .logger import get_logger

logger = get_logger("database")

class Database:
    """数据库类，用于管理数据库连接和操作"""
    
    def __init__(self, db_path: str = "data/database.db"):
        """初始化数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化数据库连接
        self._init_connection()
        
        # 初始化数据库表
        self._init_tables()
    
    def _init_connection(self):
        """初始化数据库连接"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            # 启用外键约束
            self.conn.execute("PRAGMA foreign_keys = ON")
            # 设置行工厂，返回字典
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            logger.info(f"数据库连接成功: {self.db_path}")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}", exc_info=True)
            raise
    
    def _init_tables(self):
        """初始化数据库表"""
        try:
            # 创建群信息表
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_info (
                group_id INTEGER PRIMARY KEY,
                group_name TEXT,
                member_count INTEGER,
                max_member_count INTEGER,
                owner_id INTEGER,
                admin_count INTEGER,
                last_active_time INTEGER,
                join_time INTEGER,
                created_time INTEGER
            )
            """)
            
            # 创建群成员表
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER,
                user_id INTEGER,
                nickname TEXT,
                card TEXT,
                sex TEXT,
                age INTEGER,
                area TEXT,
                join_time INTEGER,
                last_sent_time INTEGER,
                level TEXT,
                role TEXT,
                unfriendly INTEGER DEFAULT 0,
                title TEXT,
                title_expire_time INTEGER,
                card_changeable INTEGER,
                shut_up_timestamp INTEGER,
                UNIQUE(group_id, user_id),
                FOREIGN KEY(group_id) REFERENCES group_info(group_id) ON DELETE CASCADE
            )
            """)
            
            # 创建消息表
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id TEXT PRIMARY KEY,
                group_id INTEGER,
                user_id INTEGER,
                message_type TEXT,
                content TEXT,
                raw_message TEXT,
                time INTEGER,
                message_seq INTEGER,
                message_data TEXT,
                FOREIGN KEY(group_id) REFERENCES group_info(group_id) ON DELETE CASCADE
            )
            """)
            
            # 创建索引
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_group_id ON messages(group_id)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id)")
            self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_time ON messages(time)")
            
            self.conn.commit()
            logger.info("数据库表初始化完成")
        except Exception as e:
            logger.error(f"数据库表初始化失败: {e}", exc_info=True)
            raise
    
    def close(self):
        """关闭数据库连接"""
        try:
            if self.conn:
                self.conn.close()
                logger.info("数据库连接已关闭")
        except Exception as e:
            logger.error(f"关闭数据库连接失败: {e}", exc_info=True)
    
    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """执行SQL语句
        
        Args:
            sql: SQL语句
            params: SQL参数
            
        Returns:
            sqlite3.Cursor: 游标对象
        """
        try:
            return self.cursor.execute(sql, params)
        except Exception as e:
            logger.error(f"执行SQL失败: {sql}, 参数: {params}, 错误: {e}", exc_info=True)
            raise
    
    def executemany(self, sql: str, params_list: List[tuple]) -> sqlite3.Cursor:
        """执行多条SQL语句
        
        Args:
            sql: SQL语句
            params_list: SQL参数列表
            
        Returns:
            sqlite3.Cursor: 游标对象
        """
        try:
            return self.cursor.executemany(sql, params_list)
        except Exception as e:
            logger.error(f"执行多条SQL失败: {sql}, 参数列表长度: {len(params_list)}, 错误: {e}", exc_info=True)
            raise
    
    def commit(self):
        """提交事务"""
        try:
            self.conn.commit()
        except Exception as e:
            logger.error(f"提交事务失败: {e}", exc_info=True)
            raise
    
    def rollback(self):
        """回滚事务"""
        try:
            self.conn.rollback()
        except Exception as e:
            logger.error(f"回滚事务失败: {e}", exc_info=True)
            raise
    
    def fetchone(self) -> Optional[Dict[str, Any]]:
        """获取一条记录
        
        Returns:
            Optional[Dict[str, Any]]: 记录字典，如果没有记录则返回None
        """
        try:
            row = self.cursor.fetchone()
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"获取一条记录失败: {e}", exc_info=True)
            return None
    
    def fetchall(self) -> List[Dict[str, Any]]:
        """获取所有记录
        
        Returns:
            List[Dict[str, Any]]: 记录字典列表
        """
        try:
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"获取所有记录失败: {e}", exc_info=True)
            return []
    
    def insert_group_info(self, group_info: Dict[str, Any]) -> bool:
        """插入群信息
        
        Args:
            group_info: 群信息字典
            
        Returns:
            bool: 是否成功
        """
        try:
            sql = """
            INSERT OR REPLACE INTO group_info (
                group_id, group_name, member_count, max_member_count, 
                owner_id, admin_count, last_active_time, join_time, created_time
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                group_info.get('group_id'),
                group_info.get('group_name'),
                group_info.get('member_count'),
                group_info.get('max_member_count'),
                group_info.get('owner_id'),
                group_info.get('admin_count'),
                group_info.get('last_active_time', int(time.time())),
                group_info.get('join_time'),
                group_info.get('created_time')
            )
            
            self.execute(sql, params)
            self.commit()
            return True
        except Exception as e:
            logger.error(f"插入群信息失败: {e}", exc_info=True)
            self.rollback()
            return False
    
    def insert_group_member(self, member_info: Dict[str, Any]) -> bool:
        """插入群成员信息
        
        Args:
            member_info: 群成员信息字典
            
        Returns:
            bool: 是否成功
        """
        try:
            sql = """
            INSERT OR REPLACE INTO group_members (
                group_id, user_id, nickname, card, sex, age, area, 
                join_time, last_sent_time, level, role, unfriendly, 
                title, title_expire_time, card_changeable, shut_up_timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                member_info.get('group_id'),
                member_info.get('user_id'),
                member_info.get('nickname'),
                member_info.get('card'),
                member_info.get('sex'),
                member_info.get('age'),
                member_info.get('area'),
                member_info.get('join_time'),
                member_info.get('last_sent_time', int(time.time())),
                member_info.get('level'),
                member_info.get('role'),
                member_info.get('unfriendly', 0),
                member_info.get('title'),
                member_info.get('title_expire_time'),
                member_info.get('card_changeable'),
                member_info.get('shut_up_timestamp')
            )
            
            self.execute(sql, params)
            self.commit()
            return True
        except Exception as e:
            logger.error(f"插入群成员信息失败: {e}", exc_info=True)
            self.rollback()
            return False
    
    def insert_message(self, message_info: Dict[str, Any]) -> bool:
        """插入消息
        
        Args:
            message_info: 消息信息字典
            
        Returns:
            bool: 是否成功
        """
        try:
            sql = """
            INSERT OR IGNORE INTO messages (
                message_id, group_id, user_id, message_type, 
                content, raw_message, time, message_seq, message_data
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                message_info.get('message_id'),
                message_info.get('group_id'),
                message_info.get('user_id'),
                message_info.get('message_type'),
                message_info.get('content'),
                message_info.get('raw_message'),
                message_info.get('time'),
                message_info.get('message_seq'),
                message_info.get('message_data')
            )
            
            self.execute(sql, params)
            self.commit()
            return True
        except Exception as e:
            logger.error(f"插入消息失败: {e}", exc_info=True)
            self.rollback()
            return False
    
    def get_group_info(self, group_id: int) -> Optional[Dict[str, Any]]:
        """获取群信息
        
        Args:
            group_id: 群号
            
        Returns:
            Optional[Dict[str, Any]]: 群信息字典，如果不存在则返回None
        """
        try:
            sql = "SELECT * FROM group_info WHERE group_id = ?"
            self.execute(sql, (group_id,))
            return self.fetchone()
        except Exception as e:
            logger.error(f"获取群信息失败: {e}", exc_info=True)
            return None
    
    def get_group_member(self, group_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """获取群成员信息
        
        Args:
            group_id: 群号
            user_id: QQ号
            
        Returns:
            Optional[Dict[str, Any]]: 群成员信息字典，如果不存在则返回None
        """
        try:
            sql = "SELECT * FROM group_members WHERE group_id = ? AND user_id = ?"
            self.execute(sql, (group_id, user_id))
            return self.fetchone()
        except Exception as e:
            logger.error(f"获取群成员信息失败: {e}", exc_info=True)
            return None
    
    def get_group_members(self, group_id: int) -> List[Dict[str, Any]]:
        """获取群所有成员信息
        
        Args:
            group_id: 群号
            
        Returns:
            List[Dict[str, Any]]: 群成员信息字典列表
        """
        try:
            sql = "SELECT * FROM group_members WHERE group_id = ?"
            self.execute(sql, (group_id,))
            return self.fetchall()
        except Exception as e:
            logger.error(f"获取群所有成员信息失败: {e}", exc_info=True)
            return []
    
    def get_user_groups(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户所在的所有群
        
        Args:
            user_id: QQ号
            
        Returns:
            List[Dict[str, Any]]: 群信息字典列表
        """
        try:
            sql = """
            SELECT g.* FROM group_info g
            INNER JOIN group_members m ON g.group_id = m.group_id
            WHERE m.user_id = ?
            """
            self.execute(sql, (user_id,))
            return self.fetchall()
        except Exception as e:
            logger.error(f"获取用户所在的所有群失败: {e}", exc_info=True)
            return []
    
    def get_messages(self, group_id: int, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取群消息
        
        Args:
            group_id: 群号
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            List[Dict[str, Any]]: 消息信息字典列表
        """
        try:
            sql = """
            SELECT * FROM messages 
            WHERE group_id = ? 
            ORDER BY time DESC 
            LIMIT ? OFFSET ?
            """
            self.execute(sql, (group_id, limit, offset))
            return self.fetchall()
        except Exception as e:
            logger.error(f"获取群消息失败: {e}", exc_info=True)
            return []
    
    def get_user_messages(self, group_id: int, user_id: int, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取用户在群中的消息
        
        Args:
            group_id: 群号
            user_id: QQ号
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            List[Dict[str, Any]]: 消息信息字典列表
        """
        try:
            sql = """
            SELECT * FROM messages 
            WHERE group_id = ? AND user_id = ? 
            ORDER BY time DESC 
            LIMIT ? OFFSET ?
            """
            self.execute(sql, (group_id, user_id, limit, offset))
            return self.fetchall()
        except Exception as e:
            logger.error(f"获取用户在群中的消息失败: {e}", exc_info=True)
            return []
    
    def search_messages(self, keyword: str, group_id: Optional[int] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """搜索消息
        
        Args:
            keyword: 关键词
            group_id: 群号，如果为None则搜索所有群
            limit: 限制数量
            
        Returns:
            List[Dict[str, Any]]: 消息信息字典列表
        """
        try:
            if group_id:
                sql = """
                SELECT * FROM messages 
                WHERE group_id = ? AND raw_message LIKE ? 
                ORDER BY time DESC 
                LIMIT ?
                """
                self.execute(sql, (group_id, f"%{keyword}%", limit))
            else:
                sql = """
                SELECT * FROM messages 
                WHERE raw_message LIKE ? 
                ORDER BY time DESC 
                LIMIT ?
                """
                self.execute(sql, (f"%{keyword}%", limit))
            
            return self.fetchall()
        except Exception as e:
            logger.error(f"搜索消息失败: {e}", exc_info=True)
            return []
    
    def update_group_last_active_time(self, group_id: int, active_time: Optional[int] = None) -> bool:
        """更新群最后活跃时间
        
        Args:
            group_id: 群号
            active_time: 活跃时间，如果为None则使用当前时间
            
        Returns:
            bool: 是否成功
        """
        try:
            if active_time is None:
                active_time = int(time.time())
            
            sql = "UPDATE group_info SET last_active_time = ? WHERE group_id = ?"
            self.execute(sql, (active_time, group_id))
            self.commit()
            return True
        except Exception as e:
            logger.error(f"更新群最后活跃时间失败: {e}", exc_info=True)
            self.rollback()
            return False
    
    def update_member_last_sent_time(self, group_id: int, user_id: int, sent_time: Optional[int] = None) -> bool:
        """更新成员最后发言时间
        
        Args:
            group_id: 群号
            user_id: QQ号
            sent_time: 发言时间，如果为None则使用当前时间
            
        Returns:
            bool: 是否成功
        """
        try:
            if sent_time is None:
                sent_time = int(time.time())
            
            sql = "UPDATE group_members SET last_sent_time = ? WHERE group_id = ? AND user_id = ?"
            self.execute(sql, (sent_time, group_id, user_id))
            self.commit()
            return True
        except Exception as e:
            logger.error(f"更新成员最后发言时间失败: {e}", exc_info=True)
            self.rollback()
            return False
    
    def delete_group(self, group_id: int) -> bool:
        """删除群信息
        
        Args:
            group_id: 群号
            
        Returns:
            bool: 是否成功
        """
        try:
            # 由于设置了外键约束，删除群信息会级联删除群成员和消息
            sql = "DELETE FROM group_info WHERE group_id = ?"
            self.execute(sql, (group_id,))
            self.commit()
            return True
        except Exception as e:
            logger.error(f"删除群信息失败: {e}", exc_info=True)
            self.rollback()
            return False
    
    def delete_group_member(self, group_id: int, user_id: int) -> bool:
        """删除群成员信息
        
        Args:
            group_id: 群号
            user_id: QQ号
            
        Returns:
            bool: 是否成功
        """
        try:
            sql = "DELETE FROM group_members WHERE group_id = ? AND user_id = ?"
            self.execute(sql, (group_id, user_id))
            self.commit()
            return True
        except Exception as e:
            logger.error(f"删除群成员信息失败: {e}", exc_info=True)
            self.rollback()
            return False
    
    def delete_messages_before(self, time_before: int, group_id: Optional[int] = None) -> bool:
        """删除指定时间之前的消息
        
        Args:
            time_before: 时间戳
            group_id: 群号，如果为None则删除所有群的消息
            
        Returns:
            bool: 是否成功
        """
        try:
            if group_id:
                sql = "DELETE FROM messages WHERE group_id = ? AND time < ?"
                self.execute(sql, (group_id, time_before))
            else:
                sql = "DELETE FROM messages WHERE time < ?"
                self.execute(sql, (time_before,))
            
            self.commit()
            return True
        except Exception as e:
            logger.error(f"删除指定时间之前的消息失败: {e}", exc_info=True)
            self.rollback()
            return False
    
    def get_message_count(self, group_id: Optional[int] = None, user_id: Optional[int] = None) -> int:
        """获取消息数量
        
        Args:
            group_id: 群号，如果为None则统计所有群
            user_id: QQ号，如果为None则统计所有用户
            
        Returns:
            int: 消息数量
        """
        try:
            if group_id and user_id:
                sql = "SELECT COUNT(*) as count FROM messages WHERE group_id = ? AND user_id = ?"
                self.execute(sql, (group_id, user_id))
            elif group_id:
                sql = "SELECT COUNT(*) as count FROM messages WHERE group_id = ?"
                self.execute(sql, (group_id,))
            elif user_id:
                sql = "SELECT COUNT(*) as count FROM messages WHERE user_id = ?"
                self.execute(sql, (user_id,))
            else:
                sql = "SELECT COUNT(*) as count FROM messages"
                self.execute(sql)
            
            result = self.fetchone()
            return result.get('count', 0) if result else 0
        except Exception as e:
            logger.error(f"获取消息数量失败: {e}", exc_info=True)
            return 0
    
    def get_active_users(self, group_id: int, days: int = 7, limit: int = 10) -> List[Dict[str, Any]]:
        """获取群内活跃用户
        
        Args:
            group_id: 群号
            days: 天数
            limit: 限制数量
            
        Returns:
            List[Dict[str, Any]]: 用户信息字典列表
        """
        try:
            # 计算指定天数前的时间戳
            time_before = int(time.time()) - days * 86400
            
            sql = """
            SELECT m.user_id, m.nickname, m.card, COUNT(*) as message_count 
            FROM messages msg
            INNER JOIN group_members m ON msg.group_id = m.group_id AND msg.user_id = m.user_id
            WHERE msg.group_id = ? AND msg.time > ?
            GROUP BY m.user_id
            ORDER BY message_count DESC
            LIMIT ?
            """
            
            self.execute(sql, (group_id, time_before, limit))
            return self.fetchall()
        except Exception as e:
            logger.error(f"获取群内活跃用户失败: {e}", exc_info=True)
            return []
    
    def get_group_stats(self, group_id: int, days: int = 7) -> Dict[str, Any]:
        """获取群统计信息
        
        Args:
            group_id: 群号
            days: 天数
            
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        try:
            # 计算指定天数前的时间戳
            time_before = int(time.time()) - days * 86400
            
            # 获取总消息数
            sql_total = "SELECT COUNT(*) as count FROM messages WHERE group_id = ?"
            self.execute(sql_total, (group_id,))
            total_result = self.fetchone()
            total_messages = total_result.get('count', 0) if total_result else 0
            
            # 获取指定时间段内的消息数
            sql_period = "SELECT COUNT(*) as count FROM messages WHERE group_id = ? AND time > ?"
            self.execute(sql_period, (group_id, time_before))
            period_result = self.fetchone()
            period_messages = period_result.get('count', 0) if period_result else 0
            
            # 获取发言人数
            sql_speakers = """
            SELECT COUNT(DISTINCT user_id) as count 
            FROM messages 
            WHERE group_id = ? AND time > ?
            """
            self.execute(sql_speakers, (group_id, time_before))
            speakers_result = self.fetchone()
            speakers_count = speakers_result.get('count', 0) if speakers_result else 0
            
            # 获取群成员数
            sql_members = "SELECT COUNT(*) as count FROM group_members WHERE group_id = ?"
            self.execute(sql_members, (group_id,))
            members_result = self.fetchone()
            members_count = members_result.get('count', 0) if members_result else 0
            
            # 计算活跃度
            activity_rate = speakers_count / members_count if members_count > 0 else 0
            
            return {
                'group_id': group_id,
                'total_messages': total_messages,
                'period_messages': period_messages,
                'speakers_count': speakers_count,
                'members_count': members_count,
                'activity_rate': activity_rate,
                'days': days
            }
        except Exception as e:
            logger.error(f"获取群统计信息失败: {e}", exc_info=True)
            return {
                'group_id': group_id,
                'total_messages': 0,
                'period_messages': 0,
                'speakers_count': 0,
                'members_count': 0,
                'activity_rate': 0,
                'days': days
            } 