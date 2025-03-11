"""
用户仓储实现
"""
from typing import List, Optional, Dict, Any, TypeVar, Generic
from datetime import datetime

from repositories.base.repository import BaseRepository
from repositories.base.database import Database
from repositories.base.exceptions import RepositoryError
from .models import User, Friend

T = TypeVar('T', bound=User)
F = TypeVar('F', bound=Friend)

class UserRepositoryError(RepositoryError):
    """用户仓储错误"""
    pass

class UserRepository(BaseRepository[User]):
    """用户仓储类"""
    
    def __init__(self, database: Database):
        """初始化用户仓储
        
        Args:
            database: 数据库实例
        """
        super().__init__(database)
        self._ensure_tables()
        
    @property
    def table_name(self) -> str:
        """获取用户表名
        
        Returns:
            str: 表名
        """
        return 'users'
        
    @property
    def friend_table_name(self) -> str:
        """获取好友表名
        
        Returns:
            str: 表名
        """
        return 'friends'
        
    async def _ensure_tables(self) -> None:
        """确保用户相关表存在"""
        try:
            # 创建用户表
            user_sql = """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL UNIQUE,
                nickname TEXT NOT NULL,
                sex TEXT NOT NULL,
                age INTEGER NOT NULL,
                level INTEGER NOT NULL,
                login_days INTEGER NOT NULL,
                avatar TEXT NOT NULL,
                status TEXT NOT NULL,
                personal_note TEXT NOT NULL,
                last_active_time TIMESTAMP NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
            """
            await self.db.connection.execute(user_sql)
            
            # 创建好友关系表
            friend_sql = """
            CREATE TABLE IF NOT EXISTS friends (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                friend_id TEXT NOT NULL,
                remark TEXT NOT NULL,
                source TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                category_name TEXT NOT NULL,
                is_blocked BOOLEAN NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                UNIQUE(user_id, friend_id)
            )
            """
            await self.db.connection.execute(friend_sql)
        except Exception as e:
            raise UserRepositoryError(f"创建用户相关表失败: {str(e)}")
        
    async def add_user(self, user: User) -> bool:
        """添加用户
        
        Args:
            user: 用户模型
            
        Returns:
            bool: 是否添加成功
            
        Raises:
            UserRepositoryError: 添加用户失败时抛出
        """
        try:
            return await self.create(user)
        except Exception as e:
            raise UserRepositoryError(f"添加用户失败: {str(e)}")
        
    async def get_user(self, user_id: str) -> Optional[User]:
        """获取用户信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[User]: 用户模型
            
        Raises:
            UserRepositoryError: 获取用户失败时抛出
        """
        try:
            return await self.get_by_id('user_id', user_id)
        except Exception as e:
            raise UserRepositoryError(f"获取用户失败: {str(e)}")
        
    async def update_user(self, user: User) -> bool:
        """更新用户信息
        
        Args:
            user: 用户模型
            
        Returns:
            bool: 是否更新成功
            
        Raises:
            UserRepositoryError: 更新用户失败时抛出
        """
        try:
            return await self.update('user_id', user)
        except Exception as e:
            raise UserRepositoryError(f"更新用户失败: {str(e)}")
        
    async def delete_user(self, user_id: str) -> bool:
        """删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否删除成功
            
        Raises:
            UserRepositoryError: 删除用户失败时抛出
        """
        try:
            async with self.db.transaction():
                # 删除好友关系
                await self.db.delete(self.friend_table_name, {'user_id': user_id})
                await self.db.delete(self.friend_table_name, {'friend_id': user_id})
                # 删除用户
                return await self.delete('user_id', user_id)
        except Exception as e:
            raise UserRepositoryError(f"删除用户失败: {str(e)}")
        
    async def add_friend(self, friend: Friend) -> bool:
        """添加好友关系
        
        Args:
            friend: 好友关系模型
            
        Returns:
            bool: 是否添加成功
            
        Raises:
            UserRepositoryError: 添加好友失败时抛出
        """
        try:
            return await self.db.insert(self.friend_table_name, friend.to_dict())
        except Exception as e:
            raise UserRepositoryError(f"添加好友失败: {str(e)}")
        
    async def get_friend(self, user_id: str, friend_id: str) -> Optional[Friend]:
        """获取好友关系
        
        Args:
            user_id: 用户ID
            friend_id: 好友ID
            
        Returns:
            Optional[Friend]: 好友关系模型
            
        Raises:
            UserRepositoryError: 获取好友失败时抛出
        """
        try:
            data = await self.db.select_one(
                self.friend_table_name,
                {'user_id': user_id, 'friend_id': friend_id}
            )
            return Friend.from_dict(data) if data else None
        except Exception as e:
            raise UserRepositoryError(f"获取好友失败: {str(e)}")
        
    async def update_friend(self, friend: Friend) -> bool:
        """更新好友关系
        
        Args:
            friend: 好友关系模型
            
        Returns:
            bool: 是否更新成功
            
        Raises:
            UserRepositoryError: 更新好友失败时抛出
        """
        try:
            return await self.db.update(
                self.friend_table_name,
                friend.to_dict(),
                {'user_id': friend.user_id, 'friend_id': friend.friend_id}
            )
        except Exception as e:
            raise UserRepositoryError(f"更新好友失败: {str(e)}")
        
    async def delete_friend(self, user_id: str, friend_id: str) -> bool:
        """删除好友关系
        
        Args:
            user_id: 用户ID
            friend_id: 好友ID
            
        Returns:
            bool: 是否删除成功
            
        Raises:
            UserRepositoryError: 删除好友失败时抛出
        """
        try:
            return await self.db.delete(
                self.friend_table_name,
                {'user_id': user_id, 'friend_id': friend_id}
            )
        except Exception as e:
            raise UserRepositoryError(f"删除好友失败: {str(e)}")
        
    async def get_friends(
        self,
        user_id: str,
        category_id: Optional[int] = None
    ) -> List[Friend]:
        """获取好友列表
        
        Args:
            user_id: 用户ID
            category_id: 分组ID
            
        Returns:
            List[Friend]: 好友关系列表
            
        Raises:
            UserRepositoryError: 获取好友列表失败时抛出
        """
        try:
            condition = {'user_id': user_id}
            if category_id is not None:
                condition['category_id'] = category_id
                
            data = await self.db.select(
                self.friend_table_name,
                condition,
                order_by=[('created_at', False)]
            )
            return [Friend.from_dict(item) for item in data]
        except Exception as e:
            raise UserRepositoryError(f"获取好友列表失败: {str(e)}")
        
    async def get_blocked_friends(self, user_id: str) -> List[Friend]:
        """获取黑名单列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Friend]: 好友关系列表
            
        Raises:
            UserRepositoryError: 获取黑名单列表失败时抛出
        """
        try:
            data = await self.db.select(
                self.friend_table_name,
                {'user_id': user_id, 'is_blocked': True},
                order_by=[('created_at', False)]
            )
            return [Friend.from_dict(item) for item in data]
        except Exception as e:
            raise UserRepositoryError(f"获取黑名单列表失败: {str(e)}")
        
    async def search_users(
        self,
        keyword: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[User]:
        """搜索用户
        
        Args:
            keyword: 关键词
            limit: 限制条数
            offset: 偏移量
            
        Returns:
            List[User]: 用户列表
            
        Raises:
            UserRepositoryError: 搜索用户失败时抛出
        """
        try:
            condition = {
                'nickname__like': f'%{keyword}%'
            }
            
            data = await self.db.select(
                self.table_name,
                condition,
                order_by=[('created_at', True)],
                limit=limit,
                offset=offset
            )
            return [User.from_dict(item) for item in data]
        except Exception as e:
            raise UserRepositoryError(f"搜索用户失败: {str(e)}") 