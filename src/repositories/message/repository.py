"""
消息仓储实现
"""
from typing import List, Optional, Dict, Any, TypeVar, Generic
from datetime import datetime

from repositories.base.repository import BaseRepository
from repositories.base.database import Database
from repositories.base.exceptions import RepositoryError
from .models import Message

T = TypeVar('T', bound=Message)

class MessageRepositoryError(RepositoryError):
    """消息仓储错误"""
    pass

class MessageRepository(BaseRepository[Message]):
    """消息仓储类"""
    
    def __init__(self, database: Database):
        """初始化消息仓储
        
        Args:
            database: 数据库实例
        """
        super().__init__(database)
        self._ensure_table()
        
    @property
    def table_name(self) -> str:
        """获取表名
        
        Returns:
            str: 表名
        """
        return 'messages'
        
    async def _ensure_table(self) -> None:
        """确保消息表存在"""
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                group_id TEXT,
                message_type TEXT NOT NULL,
                raw_message TEXT NOT NULL,
                message_seq TEXT,
                font INTEGER,
                sender_name TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
            """
            await self.db.connection.execute(sql)
        except Exception as e:
            raise MessageRepositoryError(f"创建消息表失败: {str(e)}")
        
    async def add_message(self, message: Message) -> bool:
        """添加消息记录
        
        Args:
            message: 消息模型
            
        Returns:
            bool: 是否添加成功
            
        Raises:
            MessageRepositoryError: 添加消息失败时抛出
        """
        try:
            return await self.create(message)
        except Exception as e:
            raise MessageRepositoryError(f"添加消息失败: {str(e)}")
        
    async def get_message(self, message_id: str) -> Optional[Message]:
        """获取消息记录
        
        Args:
            message_id: 消息ID
            
        Returns:
            Optional[Message]: 消息模型
            
        Raises:
            MessageRepositoryError: 获取消息失败时抛出
        """
        try:
            return await self.get_by_id('message_id', message_id)
        except Exception as e:
            raise MessageRepositoryError(f"获取消息失败: {str(e)}")
        
    async def get_user_messages(
        self,
        user_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Message]:
        """获取用户的消息记录
        
        Args:
            user_id: 用户ID
            limit: 限制条数
            offset: 偏移量
            
        Returns:
            List[Message]: 消息列表
            
        Raises:
            MessageRepositoryError: 获取消息失败时抛出
        """
        try:
            data = await self.db.select(
                self.table_name,
                {'user_id': user_id},
                order_by=[('created_at', True)],
                limit=limit,
                offset=offset
            )
            return [Message.from_dict(item) for item in data]
        except Exception as e:
            raise MessageRepositoryError(f"获取用户消息失败: {str(e)}")
        
    async def get_group_messages(
        self,
        group_id: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Message]:
        """获取群组的消息记录
        
        Args:
            group_id: 群组ID
            limit: 限制条数
            offset: 偏移量
            
        Returns:
            List[Message]: 消息列表
            
        Raises:
            MessageRepositoryError: 获取消息失败时抛出
        """
        try:
            data = await self.db.select(
                self.table_name,
                {'group_id': group_id},
                order_by=[('created_at', True)],
                limit=limit,
                offset=offset
            )
            return [Message.from_dict(item) for item in data]
        except Exception as e:
            raise MessageRepositoryError(f"获取群组消息失败: {str(e)}")
        
    async def delete_message(self, message_id: str) -> bool:
        """删除消息记录
        
        Args:
            message_id: 消息ID
            
        Returns:
            bool: 是否删除成功
            
        Raises:
            MessageRepositoryError: 删除消息失败时抛出
        """
        try:
            return await self.delete('message_id', message_id)
        except Exception as e:
            raise MessageRepositoryError(f"删除消息失败: {str(e)}")
        
    async def search_messages(
        self,
        keyword: str,
        message_type: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Message]:
        """搜索消息记录
        
        Args:
            keyword: 关键词
            message_type: 消息类型
            limit: 限制条数
            offset: 偏移量
            
        Returns:
            List[Message]: 消息列表
            
        Raises:
            MessageRepositoryError: 搜索消息失败时抛出
        """
        try:
            condition = {'raw_message__like': f'%{keyword}%'}
            if message_type:
                condition['message_type'] = message_type
                
            data = await self.db.select(
                self.table_name,
                condition,
                order_by=[('created_at', True)],
                limit=limit,
                offset=offset
            )
            return [Message.from_dict(item) for item in data]
        except Exception as e:
            raise MessageRepositoryError(f"搜索消息失败: {str(e)}") 