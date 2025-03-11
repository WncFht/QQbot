"""
基础仓储实现
"""
from typing import TypeVar, Generic, List, Optional, Dict, Any
from abc import ABC, abstractmethod

from utils.database import Database
from .models import BaseModel

T = TypeVar('T', bound=BaseModel)

class BaseRepository(Generic[T], ABC):
    """基础仓储类"""
    
    def __init__(self, database: Database):
        """初始化仓储
        
        Args:
            database: 数据库实例
        """
        self.db = database
        self.table_name: str = self.get_table_name()
    
    @abstractmethod
    def get_table_name(self) -> str:
        """获取表名
        
        Returns:
            str: 数据库表名
        """
        raise NotImplementedError
    
    async def create(self, model: T) -> bool:
        """创建记录
        
        Args:
            model: 数据模型
            
        Returns:
            bool: 是否创建成功
        """
        try:
            data = model.to_dict()
            return await self.db.insert(self.table_name, data)
        except Exception as e:
            self.db.logger.error(f"创建记录失败: {e}")
            return False
    
    async def update(self, id_field: str, model: T) -> bool:
        """更新记录
        
        Args:
            id_field: ID字段名
            model: 数据模型
            
        Returns:
            bool: 是否更新成功
        """
        try:
            data = model.to_dict()
            condition = {id_field: data[id_field]}
            return await self.db.update(self.table_name, data, condition)
        except Exception as e:
            self.db.logger.error(f"更新记录失败: {e}")
            return False
    
    async def delete(self, id_field: str, id_value: Any) -> bool:
        """删除记录
        
        Args:
            id_field: ID字段名
            id_value: ID值
            
        Returns:
            bool: 是否删除成功
        """
        try:
            condition = {id_field: id_value}
            return await self.db.delete(self.table_name, condition)
        except Exception as e:
            self.db.logger.error(f"删除记录失败: {e}")
            return False
    
    async def get_by_id(self, id_field: str, id_value: Any) -> Optional[T]:
        """根据ID获取记录
        
        Args:
            id_field: ID字段名
            id_value: ID值
            
        Returns:
            Optional[T]: 数据模型，如果不存在则返回None
        """
        try:
            condition = {id_field: id_value}
            result = await self.db.select_one(self.table_name, condition)
            if result:
                return self._create_model(result)
            return None
        except Exception as e:
            self.db.logger.error(f"获取记录失败: {e}")
            return None
    
    async def get_all(self, condition: Optional[Dict[str, Any]] = None) -> List[T]:
        """获取所有记录
        
        Args:
            condition: 查询条件
            
        Returns:
            List[T]: 数据模型列表
        """
        try:
            results = await self.db.select(self.table_name, condition)
            return [self._create_model(result) for result in results]
        except Exception as e:
            self.db.logger.error(f"获取所有记录失败: {e}")
            return []
    
    @abstractmethod
    def _create_model(self, data: Dict[str, Any]) -> T:
        """从数据字典创建模型
        
        Args:
            data: 数据字典
            
        Returns:
            T: 数据模型
        """
        raise NotImplementedError