"""
群组数据模型
"""
from typing import Dict, Any, Optional, List
from datetime import datetime

from repositories.base.models import BaseModel

class Group(BaseModel):
    """群组模型类"""
    
    def __init__(self, **kwargs):
        """初始化群组模型
        
        Args:
            **kwargs: 模型字段值
        """
        super().__init__(**kwargs)
        self.group_id: str = kwargs.get('group_id', '')
        self.group_name: str = kwargs.get('group_name', '')
        self.member_count: int = kwargs.get('member_count', 0)
        self.max_member_count: int = kwargs.get('max_member_count', 0)
        self.owner_id: str = kwargs.get('owner_id', '')
        self.admin_list: List[str] = kwargs.get('admin_list', [])
        self.join_time: datetime = kwargs.get('join_time', datetime.now())
        self.last_active_time: datetime = kwargs.get('last_active_time', datetime.now())
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典形式的数据
        """
        data = super().to_dict()
        data.update({
            'group_id': self.group_id,
            'group_name': self.group_name,
            'member_count': self.member_count,
            'max_member_count': self.max_member_count,
            'owner_id': self.owner_id,
            'admin_list': self.admin_list,
            'join_time': self.join_time,
            'last_active_time': self.last_active_time
        })
        return data

class GroupMember(BaseModel):
    """群成员模型类"""
    
    def __init__(self, **kwargs):
        """初始化群成员模型
        
        Args:
            **kwargs: 模型字段值
        """
        super().__init__(**kwargs)
        self.group_id: str = kwargs.get('group_id', '')
        self.user_id: str = kwargs.get('user_id', '')
        self.nickname: str = kwargs.get('nickname', '')
        self.card: str = kwargs.get('card', '')  # 群名片
        self.role: str = kwargs.get('role', 'member')  # owner/admin/member
        self.join_time: datetime = kwargs.get('join_time', datetime.now())
        self.last_sent_time: datetime = kwargs.get('last_sent_time', datetime.now())
        self.level: int = kwargs.get('level', 0)
        self.title: str = kwargs.get('title', '')  # 专属头衔
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典形式的数据
        """
        data = super().to_dict()
        data.update({
            'group_id': self.group_id,
            'user_id': self.user_id,
            'nickname': self.nickname,
            'card': self.card,
            'role': self.role,
            'join_time': self.join_time,
            'last_sent_time': self.last_sent_time,
            'level': self.level,
            'title': self.title
        })
        return data 