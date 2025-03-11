"""
事件管理器实现
"""
import asyncio
import inspect
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union
from src.utils.logger import get_logger
from src.utils.singleton import Singleton
from .event import Event

logger = get_logger("event_manager")

class EventManager(Singleton):
    """事件管理类，用于处理和分发事件"""
    
    def __init__(self):
        """初始化事件管理器"""
        # 避免重复初始化
        if hasattr(self, "_initialized") and self._initialized:
            return
        
        # 事件处理器字典，键为事件类型，值为处理器列表
        self.handlers: Dict[str, List[Tuple[Callable, Dict[str, Any]]]] = {}
        # 事件过滤器字典，键为事件类型，值为过滤器列表
        self.filters: Dict[str, List[Tuple[Callable, Dict[str, Any]]]] = {}
        # 事件拦截器字典，键为事件类型，值为拦截器列表
        self.interceptors: Dict[str, List[Tuple[Callable, Dict[str, Any]]]] = {}
        # 全局事件处理器列表
        self.global_handlers: List[Tuple[Callable, Dict[str, Any]]] = []
        # 全局事件过滤器列表
        self.global_filters: List[Tuple[Callable, Dict[str, Any]]] = []
        # 全局事件拦截器列表
        self.global_interceptors: List[Tuple[Callable, Dict[str, Any]]] = []
        
        self._initialized = True
    
    def register_handler(self, event_type: str, handler: Callable, **kwargs) -> bool:
        """注册事件处理器
        
        Args:
            event_type: 事件类型
            handler: 处理器函数
            **kwargs: 处理器参数
            
        Returns:
            bool: 是否成功
        """
        try:
            if event_type not in self.handlers:
                self.handlers[event_type] = []
            
            # 检查处理器是否已注册
            for h, _ in self.handlers[event_type]:
                if h == handler:
                    logger.warning(f"事件处理器已注册: {event_type}, {handler.__name__}")
                    return False
            
            self.handlers[event_type].append((handler, kwargs))
            logger.info(f"注册事件处理器成功: {event_type}, {handler.__name__}")
            return True
        except Exception as e:
            logger.error(f"注册事件处理器失败: {event_type}, {handler.__name__}, {e}", exc_info=True)
            return False
    
    def unregister_handler(self, event_type: str, handler: Callable) -> bool:
        """注销事件处理器
        
        Args:
            event_type: 事件类型
            handler: 处理器函数
            
        Returns:
            bool: 是否成功
        """
        try:
            if event_type not in self.handlers:
                logger.warning(f"事件类型不存在: {event_type}")
                return False
            
            # 查找处理器
            for i, (h, _) in enumerate(self.handlers[event_type]):
                if h == handler:
                    self.handlers[event_type].pop(i)
                    logger.info(f"注销事件处理器成功: {event_type}, {handler.__name__}")
                    return True
            
            logger.warning(f"事件处理器未注册: {event_type}, {handler.__name__}")
            return False
        except Exception as e:
            logger.error(f"注销事件处理器失败: {event_type}, {handler.__name__}, {e}", exc_info=True)
            return False
    
    def register_filter(self, event_type: str, filter_func: Callable, **kwargs) -> bool:
        """注册事件过滤器
        
        Args:
            event_type: 事件类型
            filter_func: 过滤器函数
            **kwargs: 过滤器参数
            
        Returns:
            bool: 是否成功
        """
        try:
            if event_type not in self.filters:
                self.filters[event_type] = []
            
            # 检查过滤器是否已注册
            for f, _ in self.filters[event_type]:
                if f == filter_func:
                    logger.warning(f"事件过滤器已注册: {event_type}, {filter_func.__name__}")
                    return False
            
            self.filters[event_type].append((filter_func, kwargs))
            logger.info(f"注册事件过滤器成功: {event_type}, {filter_func.__name__}")
            return True
        except Exception as e:
            logger.error(f"注册事件过滤器失败: {event_type}, {filter_func.__name__}, {e}", exc_info=True)
            return False
    
    def unregister_filter(self, event_type: str, filter_func: Callable) -> bool:
        """注销事件过滤器
        
        Args:
            event_type: 事件类型
            filter_func: 过滤器函数
            
        Returns:
            bool: 是否成功
        """
        try:
            if event_type not in self.filters:
                logger.warning(f"事件类型不存在: {event_type}")
                return False
            
            # 查找过滤器
            for i, (f, _) in enumerate(self.filters[event_type]):
                if f == filter_func:
                    self.filters[event_type].pop(i)
                    logger.info(f"注销事件过滤器成功: {event_type}, {filter_func.__name__}")
                    return True
            
            logger.warning(f"事件过滤器未注册: {event_type}, {filter_func.__name__}")
            return False
        except Exception as e:
            logger.error(f"注销事件过滤器失败: {event_type}, {filter_func.__name__}, {e}", exc_info=True)
            return False
    
    def register_interceptor(self, event_type: str, interceptor: Callable, **kwargs) -> bool:
        """注册事件拦截器
        
        Args:
            event_type: 事件类型
            interceptor: 拦截器函数
            **kwargs: 拦截器参数
            
        Returns:
            bool: 是否成功
        """
        try:
            if event_type not in self.interceptors:
                self.interceptors[event_type] = []
            
            # 检查拦截器是否已注册
            for i, _ in self.interceptors[event_type]:
                if i == interceptor:
                    logger.warning(f"事件拦截器已注册: {event_type}, {interceptor.__name__}")
                    return False
            
            self.interceptors[event_type].append((interceptor, kwargs))
            logger.info(f"注册事件拦截器成功: {event_type}, {interceptor.__name__}")
            return True
        except Exception as e:
            logger.error(f"注册事件拦截器失败: {event_type}, {interceptor.__name__}, {e}", exc_info=True)
            return False
    
    def unregister_interceptor(self, event_type: str, interceptor: Callable) -> bool:
        """注销事件拦截器
        
        Args:
            event_type: 事件类型
            interceptor: 拦截器函数
            
        Returns:
            bool: 是否成功
        """
        try:
            if event_type not in self.interceptors:
                logger.warning(f"事件类型不存在: {event_type}")
                return False
            
            # 查找拦截器
            for i, (inter, _) in enumerate(self.interceptors[event_type]):
                if inter == interceptor:
                    self.interceptors[event_type].pop(i)
                    logger.info(f"注销事件拦截器成功: {event_type}, {interceptor.__name__}")
                    return True
            
            logger.warning(f"事件拦截器未注册: {event_type}, {interceptor.__name__}")
            return False
        except Exception as e:
            logger.error(f"注销事件拦截器失败: {event_type}, {interceptor.__name__}, {e}", exc_info=True)
            return False
    
    def register_global_handler(self, handler: Callable, **kwargs) -> bool:
        """注册全局事件处理器
        
        Args:
            handler: 处理器函数
            **kwargs: 处理器参数
            
        Returns:
            bool: 是否成功
        """
        try:
            # 检查处理器是否已注册
            for h, _ in self.global_handlers:
                if h == handler:
                    logger.warning(f"全局事件处理器已注册: {handler.__name__}")
                    return False
            
            self.global_handlers.append((handler, kwargs))
            logger.info(f"注册全局事件处理器成功: {handler.__name__}")
            return True
        except Exception as e:
            logger.error(f"注册全局事件处理器失败: {handler.__name__}, {e}", exc_info=True)
            return False
    
    def unregister_global_handler(self, handler: Callable) -> bool:
        """注销全局事件处理器
        
        Args:
            handler: 处理器函数
            
        Returns:
            bool: 是否成功
        """
        try:
            # 查找处理器
            for i, (h, _) in enumerate(self.global_handlers):
                if h == handler:
                    self.global_handlers.pop(i)
                    logger.info(f"注销全局事件处理器成功: {handler.__name__}")
                    return True
            
            logger.warning(f"全局事件处理器未注册: {handler.__name__}")
            return False
        except Exception as e:
            logger.error(f"注销全局事件处理器失败: {handler.__name__}, {e}", exc_info=True)
            return False
    
    def register_global_filter(self, filter_func: Callable, **kwargs) -> bool:
        """注册全局事件过滤器
        
        Args:
            filter_func: 过滤器函数
            **kwargs: 过滤器参数
            
        Returns:
            bool: 是否成功
        """
        try:
            # 检查过滤器是否已注册
            for f, _ in self.global_filters:
                if f == filter_func:
                    logger.warning(f"全局事件过滤器已注册: {filter_func.__name__}")
                    return False
            
            self.global_filters.append((filter_func, kwargs))
            logger.info(f"注册全局事件过滤器成功: {filter_func.__name__}")
            return True
        except Exception as e:
            logger.error(f"注册全局事件过滤器失败: {filter_func.__name__}, {e}", exc_info=True)
            return False
    
    def unregister_global_filter(self, filter_func: Callable) -> bool:
        """注销全局事件过滤器
        
        Args:
            filter_func: 过滤器函数
            
        Returns:
            bool: 是否成功
        """
        try:
            # 查找过滤器
            for i, (f, _) in enumerate(self.global_filters):
                if f == filter_func:
                    self.global_filters.pop(i)
                    logger.info(f"注销全局事件过滤器成功: {filter_func.__name__}")
                    return True
            
            logger.warning(f"全局事件过滤器未注册: {filter_func.__name__}")
            return False
        except Exception as e:
            logger.error(f"注销全局事件过滤器失败: {filter_func.__name__}, {e}", exc_info=True)
            return False
    
    def register_global_interceptor(self, interceptor: Callable, **kwargs) -> bool:
        """注册全局事件拦截器
        
        Args:
            interceptor: 拦截器函数
            **kwargs: 拦截器参数
            
        Returns:
            bool: 是否成功
        """
        try:
            # 检查拦截器是否已注册
            for i, _ in self.global_interceptors:
                if i == interceptor:
                    logger.warning(f"全局事件拦截器已注册: {interceptor.__name__}")
                    return False
            
            self.global_interceptors.append((interceptor, kwargs))
            logger.info(f"注册全局事件拦截器成功: {interceptor.__name__}")
            return True
        except Exception as e:
            logger.error(f"注册全局事件拦截器失败: {interceptor.__name__}, {e}", exc_info=True)
            return False
    
    def unregister_global_interceptor(self, interceptor: Callable) -> bool:
        """注销全局事件拦截器
        
        Args:
            interceptor: 拦截器函数
            
        Returns:
            bool: 是否成功
        """
        try:
            # 查找拦截器
            for i, (inter, _) in enumerate(self.global_interceptors):
                if inter == interceptor:
                    self.global_interceptors.pop(i)
                    logger.info(f"注销全局事件拦截器成功: {interceptor.__name__}")
                    return True
            
            logger.warning(f"全局事件拦截器未注册: {interceptor.__name__}")
            return False
        except Exception as e:
            logger.error(f"注销全局事件拦截器失败: {interceptor.__name__}, {e}", exc_info=True)
            return False
    
    async def emit(self, event: Event) -> bool:
        """发送事件
        
        Args:
            event: 事件对象
            
        Returns:
            bool: 是否成功
        """
        try:
            # 运行全局拦截器
            for interceptor, kwargs in self.global_interceptors:
                if not await self._call_async_or_sync(interceptor, event, **kwargs):
                    logger.debug(f"事件被全局拦截器拦截: {event.type}")
                    return False
            
            # 运行事件拦截器
            if event.type in self.interceptors:
                for interceptor, kwargs in self.interceptors[event.type]:
                    if not await self._call_async_or_sync(interceptor, event, **kwargs):
                        logger.debug(f"事件被拦截器拦截: {event.type}")
                        return False
            
            # 运行全局过滤器
            for filter_func, kwargs in self.global_filters:
                if not await self._call_async_or_sync(filter_func, event, **kwargs):
                    logger.debug(f"事件被全局过滤器过滤: {event.type}")
                    return False
            
            # 运行事件过滤器
            if event.type in self.filters:
                for filter_func, kwargs in self.filters[event.type]:
                    if not await self._call_async_or_sync(filter_func, event, **kwargs):
                        logger.debug(f"事件被过滤器过滤: {event.type}")
                        return False
            
            # 运行全局处理器
            for handler, kwargs in self.global_handlers:
                try:
                    await self._call_async_or_sync(handler, event, **kwargs)
                except Exception as e:
                    logger.error(f"全局事件处理器执行失败: {handler.__name__}, {e}", exc_info=True)
            
            # 运行事件处理器
            if event.type in self.handlers:
                for handler, kwargs in self.handlers[event.type]:
                    try:
                        await self._call_async_or_sync(handler, event, **kwargs)
                    except Exception as e:
                        logger.error(f"事件处理器执行失败: {handler.__name__}, {e}", exc_info=True)
            
            return True
        except Exception as e:
            logger.error(f"事件处理失败: {event.type}, {e}", exc_info=True)
            return False
    
    async def _call_async_or_sync(self, func: Callable, *args, **kwargs) -> Any:
        """调用异步或同步函数
        
        Args:
            func: 要调用的函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            Any: 函数返回值
        """
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs) 