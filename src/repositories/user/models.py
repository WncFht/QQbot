"""
用户数据模型
"""
from typing import Dict, Any, Optional, List
from datetime import datetime

from repositories.base.models import BaseModel

class User(BaseModel):
    """用户模型类"""
    
    def __init__(self, **kwargs):
        """初始化用户模型
        
        Args:
            **kwargs: 模型字段值
        """
        super().__init__(**kwargs)
        self.user_id: str = kwargs.get('user_id', '')
        self.nickname: str = kwargs.get('nickname', '')
        self.sex: str = kwargs.get('sex', 'unknown')  # male/female/unknown
        self.age: int = kwargs.get('age', 0)
        self.level: int = kwargs.get('level', 0)
        self.login_days: int = kwargs.get('login_days', 0)
        self.avatar: str = kwargs.get('avatar', '')
        self.status: str = kwargs.get('status', 'offline')  # online/offline/hidden
        self.personal_note: str = kwargs.get('personal_note', '')
        self.last_active_time: datetime = kwargs.get('last_active_time', datetime.now())
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典形式的数据
        """
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'nickname': self.nickname,
            'sex': self.sex,
            'age': self.age,
            'level': self.level,
            'login_days': self.login_days,
            'avatar': self.avatar,
            'status': self.status,
            'personal_note': self.personal_note,
            'last_active_time': self.last_active_time
        })
        return data

class Friend(BaseModel):
    """好友关系模型类"""
    
    def __init__(self, **kwargs):
        """初始化好友关系模型
        
        Args:
            **kwargs: 模型字段值
        """
        super().__init__(**kwargs)
        self.user_id: str = kwargs.get('user_id', '')
        self.friend_id: str = kwargs.get('friend_id', '')
        self.remark: str = kwargs.get('remark', '')
        self.source: str = kwargs.get('source', '')  # 来源
        self.category_id: int = kwargs.get('category_id', 0)  # 分组ID
        self.category_name: str = kwargs.get('category_name', '默认分组')
        self.is_blocked: bool = kwargs.get('is_blocked', False)
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典形式的数据
        """
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'friend_id': self.friend_id,
            'remark': self.remark,
            'source': self.source,
            'category_id': self.category_id,
            'category_name': self.category_name,
            'is_blocked': self.is_blocked
        })
        return data 