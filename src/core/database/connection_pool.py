"""
数据库连接池模块
"""
import sqlite3
import threading
import time
from queue import Queue, Empty
from typing import Dict, List, Optional, Tuple, Union, Any
from ncatbot.utils.logger import get_log

logger = get_log()

class Connection:
    """数据库连接包装类"""
    
    def __init__(self, conn: sqlite3.Connection, pool: 'ConnectionPool'):
        """
        初始化连接
        
        Args:
            conn: SQLite连接
            pool: 连接池
        """
        self.conn = conn
        self.pool = pool
        self.in_use = False
        self.last_used = time.time()
    
    def cursor(self) -> sqlite3.Cursor:
        """获取游标"""
        return self.conn.cursor()
    
    def commit(self) -> None:
        """提交事务"""
        self.conn.commit()
    
    def rollback(self) -> None:
        """回滚事务"""
        self.conn.rollback()
    
    def close(self) -> None:
        """关闭连接（归还到连接池）"""
        self.in_use = False
        self.last_used = time.time()
        self.pool.release(self)
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        if exc_type is not None:
            # 发生异常，回滚事务
            self.rollback()
        else:
            # 正常退出，提交事务
            self.commit()
        
        # 释放连接
        self.close()

class ConnectionPool:
    """数据库连接池"""
    
    def __init__(self, database_path: str, max_connections: int = 5, timeout: int = 30):
        """
        初始化连接池
        
        Args:
            database_path: 数据库文件路径
            max_connections: 最大连接数
            timeout: 连接超时时间（秒）
        """
        self.database_path = database_path
        self.max_connections = max_connections
        self.timeout = timeout
        self.connections: List[Connection] = []
        self.lock = threading.RLock()
        self.connection_count = 0
    
    def _create_connection(self) -> Connection:
        """创建新的数据库连接"""
        try:
            conn = sqlite3.connect(self.database_path, check_same_thread=False)
            # 启用外键约束
            conn.execute("PRAGMA foreign_keys = ON")
            # 启用WAL模式，提高并发性能
            conn.execute("PRAGMA journal_mode = WAL")
            # 设置同步模式，提高写入性能
            conn.execute("PRAGMA synchronous = NORMAL")
            
            connection = Connection(conn, self)
            self.connection_count += 1
            logger.debug(f"创建新的数据库连接，当前连接数: {self.connection_count}")
            return connection
        except Exception as e:
            logger.error(f"创建数据库连接失败: {e}")
            raise
    
    def acquire(self) -> Connection:
        """
        获取一个数据库连接
        
        Returns:
            Connection: 数据库连接
        """
        with self.lock:
            # 查找可用的连接
            for connection in self.connections:
                if not connection.in_use:
                    connection.in_use = True
                    return connection
            
            # 如果没有可用连接且未达到最大连接数，则创建新连接
            if self.connection_count < self.max_connections:
                connection = self._create_connection()
                connection.in_use = True
                self.connections.append(connection)
                return connection
            
            # 如果已达到最大连接数，则等待连接释放
            logger.warning(f"已达到最大连接数 {self.max_connections}，等待连接释放")
        
        # 在锁外等待，避免死锁
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            with self.lock:
                for connection in self.connections:
                    if not connection.in_use:
                        connection.in_use = True
                        return connection
            
            # 短暂休眠，避免CPU占用过高
            time.sleep(0.1)
        
        # 超时，抛出异常
        raise TimeoutError(f"获取数据库连接超时，当前连接数: {self.connection_count}")
    
    def release(self, connection: Connection) -> None:
        """
        释放连接
        
        Args:
            connection: 要释放的连接
        """
        with self.lock:
            if connection in self.connections:
                connection.in_use = False
                connection.last_used = time.time()
    
    def close_all(self) -> None:
        """关闭所有连接"""
        with self.lock:
            for connection in self.connections:
                try:
                    connection.conn.close()
                except Exception as e:
                    logger.error(f"关闭数据库连接失败: {e}")
            
            self.connections.clear()
            self.connection_count = 0
            logger.info("已关闭所有数据库连接")
    
    def cleanup(self, max_idle_time: int = 300) -> None:
        """
        清理空闲连接
        
        Args:
            max_idle_time: 最大空闲时间（秒）
        """
        current_time = time.time()
        with self.lock:
            # 找出空闲时间超过阈值的连接
            idle_connections = [
                conn for conn in self.connections
                if not conn.in_use and current_time - conn.last_used > max_idle_time
            ]
            
            # 关闭空闲连接
            for connection in idle_connections:
                try:
                    connection.conn.close()
                    self.connections.remove(connection)
                    self.connection_count -= 1
                except Exception as e:
                    logger.error(f"关闭空闲连接失败: {e}")
            
            if idle_connections:
                logger.debug(f"已清理 {len(idle_connections)} 个空闲连接，当前连接数: {self.connection_count}")
    
    def __enter__(self) -> Connection:
        """上下文管理器入口"""
        return self.acquire()
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器出口"""
        if exc_type is not None:
            # 发生异常，回滚事务
            self.connections[-1].rollback()
        else:
            # 正常退出，提交事务
            self.connections[-1].commit()
        
        # 释放连接
        self.connections[-1].close() 