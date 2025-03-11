"""
数据库管理实现
"""
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from utils.logger import get_logger
from .connection import DatabaseConnection

logger = get_logger(__name__)

class Database:
    """数据库管理类"""
    
    def __init__(self, database_path: str):
        """初始化数据库管理器
        
        Args:
            database_path: 数据库文件路径
        """
        self.connection = DatabaseConnection(database_path)
        self.logger = logger
    
    async def insert(self, table: str, data: Dict[str, Any]) -> bool:
        """插入数据
        
        Args:
            table: 表名
            data: 数据字典
            
        Returns:
            bool: 是否插入成功
        """
        fields = list(data.keys())
        values = list(data.values())
        placeholders = ["?" for _ in fields]
        
        sql = f"INSERT INTO {table} ({','.join(fields)}) VALUES ({','.join(placeholders)})"
        return await self.connection.execute(sql, tuple(values))
    
    async def update(self, table: str, data: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """更新数据
        
        Args:
            table: 表名
            data: 更新数据
            condition: 更新条件
            
        Returns:
            bool: 是否更新成功
        """
        set_fields = [f"{k}=?" for k in data.keys()]
        where_fields = [f"{k}=?" for k in condition.keys()]
        
        sql = f"UPDATE {table} SET {','.join(set_fields)} WHERE {' AND '.join(where_fields)}"
        parameters = tuple(list(data.values()) + list(condition.values()))
        
        return await self.connection.execute(sql, parameters)
    
    async def delete(self, table: str, condition: Dict[str, Any]) -> bool:
        """删除数据
        
        Args:
            table: 表名
            condition: 删除条件
            
        Returns:
            bool: 是否删除成功
        """
        where_fields = [f"{k}=?" for k in condition.keys()]
        
        sql = f"DELETE FROM {table} WHERE {' AND '.join(where_fields)}"
        parameters = tuple(condition.values())
        
        return await self.connection.execute(sql, parameters)
    
    async def select_one(
        self,
        table: str,
        condition: Optional[Dict[str, Any]] = None,
        fields: Optional[List[str]] = None,
        order_by: Optional[List[Tuple[str, bool]]] = None
    ) -> Optional[Dict[str, Any]]:
        """查询单条记录
        
        Args:
            table: 表名
            condition: 查询条件
            fields: 查询字段
            order_by: 排序条件，元组(字段名, 是否降序)
            
        Returns:
            Optional[Dict[str, Any]]: 查询结果
        """
        field_str = "*" if not fields else ",".join(fields)
        sql = f"SELECT {field_str} FROM {table}"
        parameters = []
        
        if condition:
            where_fields = []
            for k, v in condition.items():
                if "__" in k:
                    field, op = k.split("__")
                    if op == "gt":
                        where_fields.append(f"{field} > ?")
                    elif op == "gte":
                        where_fields.append(f"{field} >= ?")
                    elif op == "lt":
                        where_fields.append(f"{field} < ?")
                    elif op == "lte":
                        where_fields.append(f"{field} <= ?")
                    elif op == "like":
                        where_fields.append(f"{field} LIKE ?")
                    elif op == "in":
                        placeholders = ",".join(["?" for _ in v])
                        where_fields.append(f"{field} IN ({placeholders})")
                        parameters.extend(v)
                        continue
                else:
                    where_fields.append(f"{k}=?")
                parameters.append(v)
            
            if where_fields:
                sql += f" WHERE {' AND '.join(where_fields)}"
        
        if order_by:
            order_fields = [f"{field} {'DESC' if desc else 'ASC'}" 
                          for field, desc in order_by]
            sql += f" ORDER BY {','.join(order_fields)}"
        
        return await self.connection.fetch_one(sql, tuple(parameters))
    
    async def select(
        self,
        table: str,
        condition: Optional[Dict[str, Any]] = None,
        fields: Optional[List[str]] = None,
        order_by: Optional[List[Tuple[str, bool]]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """查询多条记录
        
        Args:
            table: 表名
            condition: 查询条件
            fields: 查询字段
            order_by: 排序条件，元组(字段名, 是否降序)
            limit: 限制条数
            offset: 偏移量
            
        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """
        field_str = "*" if not fields else ",".join(fields)
        sql = f"SELECT {field_str} FROM {table}"
        parameters = []
        
        if condition:
            where_fields = []
            for k, v in condition.items():
                if "__" in k:
                    field, op = k.split("__")
                    if op == "gt":
                        where_fields.append(f"{field} > ?")
                    elif op == "gte":
                        where_fields.append(f"{field} >= ?")
                    elif op == "lt":
                        where_fields.append(f"{field} < ?")
                    elif op == "lte":
                        where_fields.append(f"{field} <= ?")
                    elif op == "like":
                        where_fields.append(f"{field} LIKE ?")
                    elif op == "in":
                        placeholders = ",".join(["?" for _ in v])
                        where_fields.append(f"{field} IN ({placeholders})")
                        parameters.extend(v)
                        continue
                else:
                    where_fields.append(f"{k}=?")
                parameters.append(v)
            
            if where_fields:
                sql += f" WHERE {' AND '.join(where_fields)}"
        
        if order_by:
            order_fields = [f"{field} {'DESC' if desc else 'ASC'}" 
                          for field, desc in order_by]
            sql += f" ORDER BY {','.join(order_fields)}"
        
        if limit is not None:
            sql += f" LIMIT {limit}"
            
        if offset is not None:
            sql += f" OFFSET {offset}"
        
        return await self.connection.fetch_all(sql, tuple(parameters))
    
    async def backup(self, backup_path: str) -> bool:
        """备份数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 是否备份成功
        """
        return await self.connection.backup(backup_path)
    
    async def restore(self, backup_path: str) -> bool:
        """从备份恢复数据库
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            bool: 是否恢复成功
        """
        return await self.connection.restore(backup_path) 