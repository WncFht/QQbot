"""
消息数据模型
"""
from typing import Dict, Any, Optional
from datetime import datetime

from repositories.base.models import BaseModel

class Message(BaseModel):
    """消息模型类"""
    
    def __init__(self, **kwargs):
        """初始化消息模型
        
        Args:
            **kwargs: 模型字段值
        """
        super().__init__(**kwargs)
        self.message_id: str = kwargs.get('message_id', '')
        self.user_id: str = kwargs.get('user_id', '')
        self.group_id: Optional[str] = kwargs.get('group_id')
        self.message_type: str = kwargs.get('message_type', '')  # 'private' or 'group'
        self.raw_message: str = kwargs.get('raw_message', '')
        self.message_seq: Optional[str] = kwargs.get('message_seq')
        self.font: Optional[int] = kwargs.get('font')
        self.sender_name: str = kwargs.get('sender_name', '')
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典形式的数据
        """
        data = super().to_dict()
        data.update({
            'message_id': self.message_id,
            'user_id': self.user_id,
            'group_id': self.group_id,
            'message_type': self.message_type,
            'raw_message': self.raw_message,
            'message_seq': self.message_seq,
            'font': self.font,
            'sender_name': self.sender_name
        })
        return data 