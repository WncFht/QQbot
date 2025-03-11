"""
数据库管理器模块
"""
import os
import sqlite3
import time
import threading
from typing import Dict, List, Optional, Tuple, Union, Any
from ncatbot.utils.logger import get_log

from .connection_pool import ConnectionPool

logger = get_log()

class DatabaseManager:
    """数据库管理器类"""
    
    def __init__(self, database_path: str, max_connections: int = 5):
        """
        初始化数据库管理器
        
        Args:
            database_path: 数据库文件路径
            max_connections: 最大连接数
        """
        self.database_path = database_path
        
        # 确保数据库目录存在
        dirname = os.path.dirname(database_path)
        if dirname:  # 只有当路径包含目录部分时才创建目录
            os.makedirs(dirname, exist_ok=True)
        
        # 创建连接池
        self.pool = ConnectionPool(database_path, max_connections)
        
        # 初始化数据库表
        self.init_tables()
        
        # 启动定时清理任务
        self.cleanup_timer = None
        self.start_cleanup_timer()
    
    def init_tables(self) -> None:
        """初始化数据库表"""
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            
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
            
            # 创建消息索引
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_messages_group_id ON messages (group_id)
            ''')
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages (user_id)
            ''')
            cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_messages_time ON messages (time)
            ''')
            
            # 创建日志表
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                level TEXT,
                name TEXT,
                message TEXT,
                filename TEXT,
                lineno INTEGER,
                funcName TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
            logger.info("数据库表初始化成功")
    
    def start_cleanup_timer(self) -> None:
        """启动定时清理任务"""
        def cleanup():
            self.pool.cleanup()
            # 每小时清理一次
            self.cleanup_timer = threading.Timer(3600, cleanup)
            self.cleanup_timer.daemon = True
            self.cleanup_timer.start()
        
        self.cleanup_timer = threading.Timer(3600, cleanup)
        self.cleanup_timer.daemon = True
        self.cleanup_timer.start()
    
    def stop_cleanup_timer(self) -> None:
        """停止定时清理任务"""
        if self.cleanup_timer:
            self.cleanup_timer.cancel()
            self.cleanup_timer = None
    
    def close(self) -> None:
        """关闭数据库管理器"""
        self.stop_cleanup_timer()
        self.pool.close_all()
    
    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        执行SQL语句
        
        Args:
            sql: SQL语句
            params: 参数
            
        Returns:
            sqlite3.Cursor: 游标
        """
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            conn.commit()
            return cursor
    
    def execute_many(self, sql: str, params_list: List[tuple]) -> sqlite3.Cursor:
        """
        执行多条SQL语句
        
        Args:
            sql: SQL语句
            params_list: 参数列表
            
        Returns:
            sqlite3.Cursor: 游标
        """
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.executemany(sql, params_list)
            conn.commit()
            return cursor
    
    def query(self, sql: str, params: tuple = ()) -> List[tuple]:
        """
        查询数据
        
        Args:
            sql: SQL语句
            params: 参数
            
        Returns:
            List[tuple]: 查询结果
        """
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchall()
    
    def query_one(self, sql: str, params: tuple = ()) -> Optional[tuple]:
        """
        查询单条数据
        
        Args:
            sql: SQL语句
            params: 参数
            
        Returns:
            Optional[tuple]: 查询结果
        """
        with self.pool.acquire() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchone()
    
    def transaction(self) -> ConnectionPool:
        """
        开始事务
        
        Returns:
            ConnectionPool: 连接池，用于上下文管理
        """
        return self.pool
    
    def backup(self, backup_path: str) -> bool:
        """
        备份数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 是否备份成功
        """
        try:
            # 确保备份目录存在
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            # 创建备份连接
            with sqlite3.connect(backup_path) as backup_conn:
                # 获取源数据库连接
                with self.pool.acquire() as conn:
                    # 执行备份
                    conn.conn.backup(backup_conn)
            
            logger.info(f"数据库备份成功: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return False
    
    def vacuum(self) -> bool:
        """
        压缩数据库
        
        Returns:
            bool: 是否压缩成功
        """
        try:
            with self.pool.acquire() as conn:
                conn.cursor().execute("VACUUM")
                conn.commit()
            
            logger.info("数据库压缩成功")
            return True
        except Exception as e:
            logger.error(f"数据库压缩失败: {e}")
            return False
    
    def optimize(self) -> bool:
        """
        优化数据库
        
        Returns:
            bool: 是否优化成功
        """
        try:
            with self.pool.acquire() as conn:
                # 分析数据库
                conn.cursor().execute("ANALYZE")
                # 重建索引
                conn.cursor().execute("REINDEX")
                conn.commit()
            
            logger.info("数据库优化成功")
            return True
        except Exception as e:
            logger.error(f"数据库优化失败: {e}")
            return False 