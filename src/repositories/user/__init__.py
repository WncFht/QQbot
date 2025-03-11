"""
用户仓储模块
"""
from .models import User, Friend
from .repository import UserRepository

__all__ = ['User', 'Friend', 'UserRepository'] 