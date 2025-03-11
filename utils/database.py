"""
数据库操作工具类
"""
import sqlite3
import json
import os
import time
import threading
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
        self._lock = threading.RLock()  # 添加线程锁以支持并发操作
        self.connect()
        self.init_tables()
    
    def connect(self):
        """连接数据库"""
        try:
            with self._lock:
                self.db_conn = sqlite3.connect(self.database_path, check_same_thread=False)
                # 启用外键约束
                self.db_conn.execute("PRAGMA foreign_keys = ON")
                # 设置行工厂，使查询结果可以通过列名访问
                self.db_conn.row_factory = sqlite3.Row
                return True
        except Exception as e:
            logger.error(f"连接数据库失败: {e}", exc_info=True)
            return False
    
    def close(self):
        """关闭数据库连接"""
        with self._lock:
            if self.db_conn:
                self.db_conn.close()
                self.db_conn = None
    
    def init_tables(self):
        """初始化数据库表"""
        try:
            with self._lock:
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
                    message_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                ''')
                
                # 创建索引以提高查询性能
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_group_id ON messages(group_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_time ON messages(time)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_message_seq ON messages(message_seq)')
                
                self.db_conn.commit()
                logger.info("数据库表初始化成功")
                return True
        except Exception as e:
            logger.error(f"初始化数据库表失败: {e}", exc_info=True)
            return False
    
    def execute(self, sql, params=None, commit=True):
        """执行SQL语句"""
        try:
            with self._lock:
                if not self.db_conn:
                    self.connect()
                
                cursor = self.db_conn.cursor()
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                if commit:
                    self.db_conn.commit()
                
                return cursor
        except Exception as e:
            logger.error(f"执行SQL失败: {sql}, 参数: {params}, 错误: {e}", exc_info=True)
            if commit:
                self.db_conn.rollback()
            return None
    
    def executemany(self, sql, params_list, commit=True):
        """批量执行SQL语句"""
        try:
            with self._lock:
                if not self.db_conn:
                    self.connect()
                
                cursor = self.db_conn.cursor()
                cursor.executemany(sql, params_list)
                
                if commit:
                    self.db_conn.commit()
                
                return cursor
        except Exception as e:
            logger.error(f"批量执行SQL失败: {sql}, 错误: {e}", exc_info=True)
            if commit:
                self.db_conn.rollback()
            return None
    
    def query(self, sql, params=None):
        """查询数据"""
        cursor = self.execute(sql, params, commit=False)
        if cursor:
            return cursor.fetchall()
        return []
    
    def query_one(self, sql, params=None):
        """查询单条数据"""
        cursor = self.execute(sql, params, commit=False)
        if cursor:
            return cursor.fetchone()
        return None
    
    def transaction(self):
        """开始事务"""
        return DatabaseTransaction(self)
    
    def save_group_info(self, group_id, group_name, member_count):
        """保存群信息"""
        try:
            self.execute('''
            INSERT OR REPLACE INTO group_info (group_id, group_name, member_count, last_update)
            VALUES (?, ?, ?, ?)
            ''', (
                group_id,
                group_name,
                member_count,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            return True
        except Exception as e:
            logger.error(f"保存群信息失败: {e}", exc_info=True)
            return False
    
    def save_group_member(self, group_id, user_id, nickname, card, role, join_time):
        """保存群成员信息"""
        try:
            self.execute('''
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
            return True
        except Exception as e:
            logger.error(f"保存群成员信息失败: {e}", exc_info=True)
            return False
    
    def save_message(self, message_id, group_id, user_id, message_type, content, raw_message, time_stamp, message_seq, message_data):
        """保存消息"""
        try:
            self.execute('''
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
            return True
        except Exception as e:
            logger.error(f"保存消息失败: {e}", exc_info=True)
            return False
    
    def get_latest_message_seq(self, group_id):
        """获取最新的消息序号"""
        try:
            result = self.query_one('''
            SELECT message_seq FROM messages 
            WHERE group_id = ? 
            ORDER BY time DESC LIMIT 1
            ''', (group_id,))
            
            if result and result[0]:
                try:
                    return int(result[0])
                except (ValueError, TypeError):
                    return 0
            return 0
        except Exception as e:
            logger.error(f"获取最新消息序号失败: {e}", exc_info=True)
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
            backup_files = [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) 
                           if f.startswith(os.path.splitext(os.path.basename(self.database_path))[0]) 
                           and f.endswith('.db')]
            backup_files.sort(reverse=True)
            
            for old_backup in backup_files[max_backups:]:
                try:
                    os.remove(old_backup)
                    logger.info(f"删除旧备份: {old_backup}")
                except Exception as e:
                    logger.error(f"删除旧备份失败: {e}", exc_info=True)
            
            return True
        except Exception as e:
            logger.error(f"备份数据库失败: {e}", exc_info=True)
            # 确保数据库连接正常
            if not self.db_conn:
                self.connect()
            return False

class DatabaseTransaction:
    """数据库事务类"""
    
    def __init__(self, database):
        self.database = database
        self.conn = database.db_conn
        self.is_active = False
    
    def __enter__(self):
        with self.database._lock:
            if not self.database.db_conn:
                self.database.connect()
            self.conn = self.database.db_conn
            self.is_active = True
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        with self.database._lock:
            if exc_type is not None:
                # 发生异常，回滚事务
                if self.is_active and self.conn:
                    self.conn.rollback()
                    logger.warning(f"事务回滚: {exc_val}")
            else:
                # 没有异常，提交事务
                if self.is_active and self.conn:
                    self.conn.commit()
            self.is_active = False
        return False  # 不抑制异常
    
    def commit(self):
        """提交事务"""
        with self.database._lock:
            if self.is_active and self.conn:
                self.conn.commit()
                self.is_active = False
    
    def rollback(self):
        """回滚事务"""
        with self.database._lock:
            if self.is_active and self.conn:
                self.conn.rollback()
                self.is_active = False 