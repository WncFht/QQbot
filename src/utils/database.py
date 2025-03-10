"""
数据库操作工具类
"""
import sqlite3
import json
import os
import time
from datetime import datetime
import shutil
from ncatbot.utils.logger import get_log

logger = get_log()

class Database:
    """数据库操作类"""
    
    def __init__(self, database_path="messages.db"):
        """初始化数据库连接"""
        self.database_path = database_path
        self.db_conn = None
        self.connect()
        self.init_tables()
    
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
    
    def init_tables(self):
        """初始化数据库表"""
        try:
            cursor = self.db_conn.cursor()
            
            # 创建群信息表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_info (
                group_id TEXT PRIMARY KEY,
                group_name TEXT,
                member_count INTEGER,
                last_update TEXT
            )
            ''')
            
            # 创建群成员表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_members (
                group_id TEXT,
                user_id TEXT,
                nickname TEXT,
                card TEXT,
                role TEXT,
                join_time INTEGER,
                last_update TEXT,
                PRIMARY KEY (group_id, user_id)
            )
            ''')
            
            # 创建消息表
            cursor.execute('''
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
            ''')
            
            self.db_conn.commit()
            logger.info("数据库表初始化成功")
            return True
        except Exception as e:
            logger.error(f"初始化数据库表失败: {e}")
            return False
    
    def save_group_info(self, group_id, group_name, member_count):
        """保存群信息"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            INSERT OR REPLACE INTO group_info (group_id, group_name, member_count, last_update)
            VALUES (?, ?, ?, ?)
            ''', (
                group_id,
                group_name,
                member_count,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            self.db_conn.commit()
            return True
        except Exception as e:
            logger.error(f"保存群信息失败: {e}")
            return False
    
    def save_group_member(self, group_id, user_id, nickname, card, role, join_time):
        """保存群成员信息"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            INSERT OR REPLACE INTO group_members 
            (group_id, user_id, nickname, card, role, join_time, last_update)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                group_id,
                user_id,
                nickname,
                card,
                role,
                join_time,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            self.db_conn.commit()
            return True
        except Exception as e:
            logger.error(f"保存群成员信息失败: {e}")
            return False
    
    def save_message(self, message_id, group_id, user_id, message_type, content, raw_message, time_stamp, message_seq, message_data):
        """保存消息"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            INSERT OR REPLACE INTO messages 
            (message_id, group_id, user_id, message_type, content, raw_message, time, message_seq, message_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message_id,
                group_id,
                user_id,
                message_type,
                content,
                raw_message,
                time_stamp,
                message_seq,
                message_data
            ))
            self.db_conn.commit()
            return True
        except Exception as e:
            logger.error(f"保存消息失败: {e}")
            return False
    
    def get_latest_message_seq(self, group_id):
        """获取最新的消息序号"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            SELECT message_seq FROM messages 
            WHERE group_id = ? 
            ORDER BY time DESC LIMIT 1
            ''', (group_id,))
            
            result = cursor.fetchone()
            return 0 if result is None else result[0]
        except Exception as e:
            logger.error(f"获取最新消息序号失败: {e}")
            return 0
    
    def backup(self, max_backups=5):
        """备份数据库"""
        try:
            # 创建备份目录
            backup_dir = "data/backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            # 创建备份文件名
            backup_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{os.path.splitext(os.path.basename(self.database_path))[0]}_{backup_time}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # 关闭当前连接
            self.close()
            
            # 复制数据库文件
            shutil.copy2(self.database_path, backup_path)
            
            # 重新连接数据库
            self.connect()
            
            logger.info(f"数据库备份成功: {backup_path}")
            
            # 清理旧备份（保留最近几个）
            backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
            backup_files.sort(reverse=True)
            
            for old_backup in backup_files[max_backups:]:
                try:
                    os.remove(os.path.join(backup_dir, old_backup))
                    logger.info(f"删除旧备份: {old_backup}")
                except Exception as e:
                    logger.error(f"删除旧备份失败: {e}")
            
            return True
        except Exception as e:
            logger.error(f"备份数据库失败: {e}")
            # 确保数据库连接正常
            if not self.db_conn:
                self.connect()
            return False
    
    def get_group_info(self, group_id):
        """获取群信息"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            SELECT group_id, group_name, member_count, last_update 
            FROM group_info 
            WHERE group_id = ?
            ''', (group_id,))
            
            result = cursor.fetchone()
            if result:
                return {
                    "group_id": result[0],
                    "group_name": result[1],
                    "member_count": result[2],
                    "last_update": result[3]
                }
            return None
        except Exception as e:
            logger.error(f"获取群信息失败: {e}")
            return None
    
    def get_group_members(self, group_id):
        """获取群成员列表"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            SELECT user_id, nickname, card, role, join_time, last_update 
            FROM group_members 
            WHERE group_id = ?
            ''', (group_id,))
            
            members = []
            for row in cursor.fetchall():
                members.append({
                    "user_id": row[0],
                    "nickname": row[1],
                    "card": row[2],
                    "role": row[3],
                    "join_time": row[4],
                    "last_update": row[5]
                })
            return members
        except Exception as e:
            logger.error(f"获取群成员列表失败: {e}")
            return [] 