"""
事件基类定义
"""
from typing import Any, Dict

class Event:
    """事件基类"""
    
    def __init__(self, event_type: str, **kwargs):
        """初始化事件
        
        Args:
            event_type: 事件类型
            **kwargs: 事件参数
        """
        self.type = event_type
        self.data = kwargs
    
    def __str__(self) -> str:
        """返回事件的字符串表示
        
        Returns:
            str: 事件的字符串表示
        """
        return f"Event(type={self.type}, data={self.data})"
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取事件参数
        
        Args:
            key: 参数键
            default: 默认值
            
        Returns:
            Any: 参数值
        """
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """设置事件参数
        
        Args:
            key: 参数键
            value: 参数值
        """
        self.data[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 事件字典
        """
        return {
            "type": self.type,
            "data": self.data
        } 