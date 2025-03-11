"""
群组仓储实现
"""
from typing import List, Optional, Dict, Any, TypeVar, Generic
from datetime import datetime

from repositories.base.repository import BaseRepository
from repositories.base.database import Database
from repositories.base.exceptions import RepositoryError
from .models import Group, GroupMember

T = TypeVar('T', bound=Group)
M = TypeVar('M', bound=GroupMember)

class GroupRepositoryError(RepositoryError):
    """群组仓储错误"""
    pass

class GroupRepository(BaseRepository[Group]):
    """群组仓储类"""
    
    def __init__(self, database: Database):
        """初始化群组仓储
        
        Args:
            database: 数据库实例
        """
        super().__init__(database)
        self._ensure_tables()
        
    @property
    def table_name(self) -> str:
        """获取群组表名
        
        Returns:
            str: 表名
        """
        return 'groups'
        
    @property
    def member_table_name(self) -> str:
        """获取群成员表名
        
        Returns:
            str: 表名
        """
        return 'group_members'
        
    async def _ensure_tables(self) -> None:
        """确保群组相关表存在"""
        try:
            # 创建群组表
            group_sql = """
            CREATE TABLE IF NOT EXISTS groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL UNIQUE,
                group_name TEXT NOT NULL,
                member_count INTEGER NOT NULL,
                max_member_count INTEGER NOT NULL,
                owner_id TEXT NOT NULL,
                admin_list TEXT NOT NULL,
                join_time TIMESTAMP NOT NULL,
                last_active_time TIMESTAMP NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
            """
            await self.db.connection.execute(group_sql)
            
            # 创建群成员表
            member_sql = """
            CREATE TABLE IF NOT EXISTS group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                nickname TEXT NOT NULL,
                card TEXT NOT NULL,
                role TEXT NOT NULL,
                join_time TIMESTAMP NOT NULL,
                last_sent_time TIMESTAMP NOT NULL,
                level INTEGER NOT NULL,
                title TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                UNIQUE(group_id, user_id)
            )
            """
            await self.db.connection.execute(member_sql)
        except Exception as e:
            raise GroupRepositoryError(f"创建群组相关表失败: {str(e)}")
        
    async def add_group(self, group: Group) -> bool:
        """添加群组
        
        Args:
            group: 群组模型
            
        Returns:
            bool: 是否添加成功
            
        Raises:
            GroupRepositoryError: 添加群组失败时抛出
        """
        try:
            data = group.to_dict()
            data['admin_list'] = ','.join(group.admin_list)  # 转换列表为字符串
            return await self.db.insert(self.table_name, data)
        except Exception as e:
            raise GroupRepositoryError(f"添加群组失败: {str(e)}")
        
    async def get_group(self, group_id: str) -> Optional[Group]:
        """获取群组信息
        
        Args:
            group_id: 群组ID
            
        Returns:
            Optional[Group]: 群组模型
            
        Raises:
            GroupRepositoryError: 获取群组失败时抛出
        """
        try:
            data = await self.db.select_one(self.table_name, {'group_id': group_id})
            if data:
                data['admin_list'] = data['admin_list'].split(',')  # 转换字符串为列表
                return Group.from_dict(data)
            return None
        except Exception as e:
            raise GroupRepositoryError(f"获取群组失败: {str(e)}")
        
    async def update_group(self, group: Group) -> bool:
        """更新群组信息
        
        Args:
            group: 群组模型
            
        Returns:
            bool: 是否更新成功
            
        Raises:
            GroupRepositoryError: 更新群组失败时抛出
        """
        try:
            data = group.to_dict()
            data['admin_list'] = ','.join(group.admin_list)
            return await self.db.update(
                self.table_name,
                data,
                {'group_id': group.group_id}
            )
        except Exception as e:
            raise GroupRepositoryError(f"更新群组失败: {str(e)}")
        
    async def delete_group(self, group_id: str) -> bool:
        """删除群组
        
        Args:
            group_id: 群组ID
            
        Returns:
            bool: 是否删除成功
            
        Raises:
            GroupRepositoryError: 删除群组失败时抛出
        """
        try:
            async with self.db.transaction():
                # 删除群组成员
                await self.db.delete(self.member_table_name, {'group_id': group_id})
                # 删除群组
                return await self.delete('group_id', group_id)
        except Exception as e:
            raise GroupRepositoryError(f"删除群组失败: {str(e)}")
        
    async def add_member(self, member: GroupMember) -> bool:
        """添加群成员
        
        Args:
            member: 群成员模型
            
        Returns:
            bool: 是否添加成功
            
        Raises:
            GroupRepositoryError: 添加群成员失败时抛出
        """
        try:
            return await self.db.insert(self.member_table_name, member.to_dict())
        except Exception as e:
            raise GroupRepositoryError(f"添加群成员失败: {str(e)}")
        
    async def get_member(self, group_id: str, user_id: str) -> Optional[GroupMember]:
        """获取群成员信息
        
        Args:
            group_id: 群组ID
            user_id: 用户ID
            
        Returns:
            Optional[GroupMember]: 群成员模型
            
        Raises:
            GroupRepositoryError: 获取群成员失败时抛出
        """
        try:
            data = await self.db.select_one(
                self.member_table_name,
                {'group_id': group_id, 'user_id': user_id}
            )
            return GroupMember.from_dict(data) if data else None
        except Exception as e:
            raise GroupRepositoryError(f"获取群成员失败: {str(e)}")
        
    async def update_member(self, member: GroupMember) -> bool:
        """更新群成员信息
        
        Args:
            member: 群成员模型
            
        Returns:
            bool: 是否更新成功
            
        Raises:
            GroupRepositoryError: 更新群成员失败时抛出
        """
        try:
            return await self.db.update(
                self.member_table_name,
                member.to_dict(),
                {'group_id': member.group_id, 'user_id': member.user_id}
            )
        except Exception as e:
            raise GroupRepositoryError(f"更新群成员失败: {str(e)}")
        
    async def delete_member(self, group_id: str, user_id: str) -> bool:
        """删除群成员
        
        Args:
            group_id: 群组ID
            user_id: 用户ID
            
        Returns:
            bool: 是否删除成功
            
        Raises:
            GroupRepositoryError: 删除群成员失败时抛出
        """
        try:
            return await self.db.delete(
                self.member_table_name,
                {'group_id': group_id, 'user_id': user_id}
            )
        except Exception as e:
            raise GroupRepositoryError(f"删除群成员失败: {str(e)}")
        
    async def get_group_members(
        self,
        group_id: str,
        role: Optional[str] = None
    ) -> List[GroupMember]:
        """获取群成员列表
        
        Args:
            group_id: 群组ID
            role: 成员角色
            
        Returns:
            List[GroupMember]: 群成员列表
            
        Raises:
            GroupRepositoryError: 获取群成员列表失败时抛出
        """
        try:
            condition = {'group_id': group_id}
            if role:
                condition['role'] = role
                
            data = await self.db.select(
                self.member_table_name,
                condition,
                order_by=[('join_time', False)]
            )
            return [GroupMember.from_dict(item) for item in data]
        except Exception as e:
            raise GroupRepositoryError(f"获取群成员列表失败: {str(e)}")
        
    async def get_user_groups(self, user_id: str) -> List[Group]:
        """获取用户加入的群组列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            List[Group]: 群组列表
            
        Raises:
            GroupRepositoryError: 获取用户群组列表失败时抛出
        """
        try:
            # 先获取用户加入的群组ID
            member_data = await self.db.select(
                self.member_table_name,
                {'user_id': user_id},
                fields=['group_id']
            )
            
            if not member_data:
                return []
                
            # 获取群组详细信息
            group_ids = [item['group_id'] for item in member_data]
            group_data = await self.db.select(
                self.table_name,
                {'group_id__in': group_ids}
            )
            
            return [Group.from_dict(item) for item in group_data]
        except Exception as e:
            raise GroupRepositoryError(f"获取用户群组列表失败: {str(e)}") 