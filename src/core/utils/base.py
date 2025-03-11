"""
基础工具类，提供通用的日志记录和错误处理功能
"""
import logging
import functools
import traceback
from typing import Any, Callable, TypeVar, ParamSpec, Awaitable, Optional
from datetime import datetime

# 类型变量定义
T = TypeVar('T')
P = ParamSpec('P')

class BaseComponent:
    """基础组件类，提供通用的日志和错误处理功能"""
    
    def __init__(self, name: str):
        """初始化基础组件
        
        Args:
            name: 组件名称，用于日志标识
        """
        self.name = name
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """配置日志记录器"""
        handler = logging.FileHandler(f"logs/{self.name}.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录信息日志
        
        Args:
            message: 日志消息
            *args: 格式化参数
            **kwargs: 关键字参数
        """
        self.logger.info(message, *args, **kwargs)
    
    def log_error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录错误日志
        
        Args:
            message: 错误消息
            *args: 格式化参数
            **kwargs: 关键字参数
        """
        self.logger.error(message, *args, **kwargs)
    
    def log_warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录警告日志
        
        Args:
            message: 警告消息
            *args: 格式化参数
            **kwargs: 关键字参数
        """
        self.logger.warning(message, *args, **kwargs)
    
    def log_debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """记录调试日志
        
        Args:
            message: 调试消息
            *args: 格式化参数
            **kwargs: 关键字参数
        """
        self.logger.debug(message, *args, **kwargs)

def catch_exceptions(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[Optional[T]]]:
    """异步函数异常捕获装饰器
    
    Args:
        func: 需要装饰的异步函数
        
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> Optional[T]:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # 获取第一个参数（通常是self）的logger
            logger = getattr(args[0], 'logger', logging.getLogger(__name__))
            logger.error(
                f"Error in {func.__name__}: {str(e)}\n"
                f"Traceback:\n{traceback.format_exc()}"
            )
            return None
    return wrapper

def log_execution_time(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    """记录异步函数执行时间的装饰器
    
    Args:
        func: 需要装饰的异步函数
        
    Returns:
        装饰后的函数
    """
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        start_time = datetime.now()
        result = await func(*args, **kwargs)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 获取第一个参数（通常是self）的logger
        logger = getattr(args[0], 'logger', logging.getLogger(__name__))
        logger.debug(
            f"{func.__name__} executed in {duration:.3f} seconds"
        )
        return result
    return wrapper 