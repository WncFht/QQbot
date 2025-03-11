"""
仓储层异常定义
"""
from typing import Optional

class RepositoryError(Exception):
    """仓储层基础异常"""
    
    def __init__(self, message: str, cause: Optional[Exception] = None):
        """初始化异常
        
        Args:
            message: 错误信息
            cause: 导致此异常的原始异常
        """
        super().__init__(message)
        self.message = message
        self.cause = cause
        
    def __str__(self) -> str:
        """获取异常字符串表示
        
        Returns:
            str: 异常字符串
        """
        if self.cause:
            return f"{self.message} (原因: {str(self.cause)})"
        return self.message

class DatabaseError(RepositoryError):
    """数据库操作异常"""
    pass

class ValidationError(RepositoryError):
    """数据验证异常"""
    pass

class NotFoundError(RepositoryError):
    """记录未找到异常"""
    pass

class DuplicateError(RepositoryError):
    """记录重复异常"""
    pass

class TransactionError(RepositoryError):
    """事务操作异常"""
    pass

class ConnectionError(RepositoryError):
    """数据库连接异常"""
    pass 