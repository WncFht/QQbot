"""
群组服务数据模型
"""
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

@dataclass
class GroupModel:
    """群组数据模型"""
    group_id: int
    group_name: str
    member_count: int
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GroupModel':
        """从字典创建群组模型"""
        return cls(
            group_id=data['group_id'],
            group_name=data['group_name'],
            member_count=data['member_count']
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'group_id': self.group_id,
            'group_name': self.group_name,
            'member_count': self.member_count
        }

@dataclass
class GroupMemberModel:
    """群成员数据模型"""
    group_id: int
    user_id: int
    nickname: str
    card: Optional[str]
    role: str
    join_time: datetime
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GroupMemberModel':
        """从字典创建群成员模型"""
        return cls(
            group_id=data['group_id'],
            user_id=data['user_id'],
            nickname=data['nickname'],
            card=data.get('card'),  # 群名片可能为空
            role=data['role'],
            join_time=datetime.fromtimestamp(data['join_time'])
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'group_id': self.group_id,
            'user_id': self.user_id,
            'nickname': self.nickname,
            'card': self.card,
            'role': self.role,
            'join_time': int(self.join_time.timestamp())
        } 