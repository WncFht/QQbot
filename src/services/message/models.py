"""
消息服务数据模型
"""
from dataclasses import dataclass
from typing import Dict, Any
from datetime import datetime

@dataclass
class MessageModel:
    """消息数据模型"""
    message_id: str
    group_id: int
    user_id: int
    message_type: str
    content: str
    raw_message: str
    time: datetime
    message_seq: int
    message_data: Dict[str, Any]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageModel':
        """从字典创建消息模型"""
        return cls(
            message_id=data['message_id'],
            group_id=data['group_id'],
            user_id=data['user_id'],
            message_type=data['message_type'],
            content=data['content'],
            raw_message=data['raw_message'],
            time=datetime.fromtimestamp(data['time']),
            message_seq=data['message_seq'],
            message_data=data['message_data']
        )

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'message_id': self.message_id,
            'group_id': self.group_id,
            'user_id': self.user_id,
            'message_type': self.message_type,
            'content': self.content,
            'raw_message': self.raw_message,
            'time': int(self.time.timestamp()),
            'message_seq': self.message_seq,
            'message_data': self.message_data
        } 