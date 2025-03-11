"""
仓储层包
提供数据访问和持久化功能
"""
from .base import BaseRepository, BaseModel
from .message import MessageRepository
from .user import UserRepository
from .group import GroupRepository

__all__ = [
    'BaseRepository',
    'BaseModel',
    'MessageRepository',
    'UserRepository',
    'GroupRepository'
] 