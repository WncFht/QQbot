"""
基础数据模型
"""
from typing import Dict, Any, Optional
from datetime import datetime

class BaseModel:
    """基础数据模型类"""
    
    def __init__(self, **kwargs):
        """初始化模型
        
        Args:
            **kwargs: 模型字段值
        """
        self.id: Optional[int] = kwargs.get('id')
        self.created_at: datetime = kwargs.get('created_at', datetime.now())
        self.updated_at: datetime = kwargs.get('updated_at', datetime.now())
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 字典形式的数据
        """
        return {
            'id': self.id,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """从字典创建模型
        
        Args:
            data: 字典数据
            
        Returns:
            BaseModel: 模型实例
        """
        return cls(**data) 