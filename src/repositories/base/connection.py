"""
数据库连接池实现
"""
import asyncio
import aiosqlite
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from utils.logger import get_logger

logger = get_logger(__name__)

class DatabaseConnection:
    """数据库连接类"""
    
    def __init__(self, database_path: str):
        """初始化数据库连接
        
        Args:
            database_path: 数据库文件路径
        """
        self.database_path = database_path
        self.connection: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()
    
    async def connect(self):
        """建立数据库连接"""
        if not self.connection:
            try:
                self.connection = await aiosqlite.connect(self.database_path)
                await self.connection.execute("PRAGMA foreign_keys = ON")
                logger.info(f"数据库连接成功: {self.database_path}")
            except Exception as e:
                logger.error(f"数据库连接失败: {e}")
                raise
    
    async def disconnect(self):
        """关闭数据库连接"""
        if self.connection:
            await self.connection.close()
            self.connection = None
            logger.info("数据库连接已关闭")
    
    async def execute(self, sql: str, parameters: tuple = ()) -> bool:
        """执行SQL语句
        
        Args:
            sql: SQL语句
            parameters: SQL参数
            
        Returns:
            bool: 是否执行成功
        """
        async with self._lock:
            try:
                await self.connect()
                async with self.connection.execute(sql, parameters) as cursor:
                    await self.connection.commit()
                return True
            except Exception as e:
                logger.error(f"SQL执行失败: {sql}, 参数: {parameters}, 错误: {e}")
                return False
    
    async def execute_many(self, sql: str, parameters: List[tuple]) -> bool:
        """执行多条SQL语句
        
        Args:
            sql: SQL语句
            parameters: SQL参数列表
            
        Returns:
            bool: 是否执行成功
        """
        async with self._lock:
            try:
                await self.connect()
                async with self.connection.executemany(sql, parameters) as cursor:
                    await self.connection.commit()
                return True
            except Exception as e:
                logger.error(f"批量SQL执行失败: {sql}, 参数: {parameters}, 错误: {e}")
                return False
    
    async def fetch_one(self, sql: str, parameters: tuple = ()) -> Optional[Dict[str, Any]]:
        """查询单条记录
        
        Args:
            sql: SQL语句
            parameters: SQL参数
            
        Returns:
            Optional[Dict[str, Any]]: 查询结果
        """
        async with self._lock:
            try:
                await self.connect()
                async with self.connection.execute(sql, parameters) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        columns = [column[0] for column in cursor.description]
                        return dict(zip(columns, row))
                return None
            except Exception as e:
                logger.error(f"查询失败: {sql}, 参数: {parameters}, 错误: {e}")
                return None
    
    async def fetch_all(self, sql: str, parameters: tuple = ()) -> List[Dict[str, Any]]:
        """查询多条记录
        
        Args:
            sql: SQL语句
            parameters: SQL参数
            
        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """
        async with self._lock:
            try:
                await self.connect()
                async with self.connection.execute(sql, parameters) as cursor:
                    rows = await cursor.fetchall()
                    if rows:
                        columns = [column[0] for column in cursor.description]
                        return [dict(zip(columns, row)) for row in rows]
                return []
            except Exception as e:
                logger.error(f"查询失败: {sql}, 参数: {parameters}, 错误: {e}")
                return []
    
    async def backup(self, backup_path: str) -> bool:
        """备份数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 是否备份成功
        """
        async with self._lock:
            try:
                await self.connect()
                # SQLite的backup需要使用同步API
                self.connection._conn.backup(backup_path)
                logger.info(f"数据库备份成功: {backup_path}")
                return True
            except Exception as e:
                logger.error(f"数据库备份失败: {e}")
                return False
    
    async def restore(self, backup_path: str) -> bool:
        """从备份恢复数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 是否恢复成功
        """
        async with self._lock:
            try:
                # 关闭当前连接
                await self.disconnect()
                
                # 使用备份文件替换当前数据库文件
                import shutil
                shutil.copy2(backup_path, self.database_path)
                
                # 重新连接数据库
                await self.connect()
                
                logger.info(f"数据库恢复成功: {backup_path}")
                return True
            except Exception as e:
                logger.error(f"数据库恢复失败: {e}")
                return False 