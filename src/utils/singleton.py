"""
单例模式基类
提供统一的单例模式实现
"""
from typing import Dict, Type, TypeVar, Any

T = TypeVar('T')

class Singleton:
    """单例基类
    
    继承此类的子类将自动成为单例类
    """
    
    _instances: Dict[Type, Any] = {}
    
    def __new__(cls, *args, **kwargs):
        """创建或获取单例实例
        
        Returns:
            cls: 单例实例
        """
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__new__(cls)
        return cls._instances[cls]
    
    @classmethod
    def get_instance(cls: Type[T], *args, **kwargs) -> T:
        """获取单例实例
        
        Returns:
            T: 单例实例
        """
        if cls not in cls._instances:
            cls._instances[cls] = cls(*args, **kwargs)
        return cls._instances[cls]
    
    @classmethod
    def has_instance(cls) -> bool:
        """检查是否已创建单例实例
        
        Returns:
            bool: 是否已创建单例实例
        """
        return cls in cls._instances
    
    @classmethod
    def clear_instance(cls) -> None:
        """清除单例实例
        """
        if cls in cls._instances:
            del cls._instances[cls]
    
    @classmethod
    def clear_all_instances(cls) -> None:
        """清除所有单例实例
        """
        cls._instances.clear() 