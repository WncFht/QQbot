"""
事件总线模块
负责事件的发布和订阅
"""
import re
import asyncio
from typing import Dict, List, Callable, Any, Optional, Pattern, Union

from src.utils.singleton import Singleton
from src.core.utils import BaseComponent, catch_exceptions, log_execution_time
from .types import Event

# 事件处理器类型
EventHandler = Callable[[Event], Any]

class EventBus(Singleton, BaseComponent):
    """事件总线类"""
    
    def __init__(self):
        """初始化事件总线"""
        # 如果已经初始化过，则直接返回
        if hasattr(self, "initialized") and self.initialized:
            return
            
        # 初始化基类
        super().__init__("event_bus")
        
        # 事件处理器字典
        self.handlers: Dict[str, List[EventHandler]] = {}
        
        # 正则表达式处理器字典
        self.regex_handlers: Dict[Pattern, List[EventHandler]] = {}
        
        # 标记为已初始化
        self.initialized = True
    
    @catch_exceptions
    def subscribe(self, event_type: str, handler: EventHandler) -> bool:
        """订阅事件
        
        Args:
            event_type: 事件类型，支持正则表达式（以 re: 开头）
            handler: 事件处理器
            
        Returns:
            bool: 是否订阅成功
        """
        # 检查是否为正则表达式
        if event_type.startswith("re:"):
            pattern_str = event_type[3:]
            pattern = re.compile(pattern_str)
            
            # 添加到正则表达式处理器字典
            if pattern not in self.regex_handlers:
                self.regex_handlers[pattern] = []
            
            # 检查处理器是否已存在
            if handler not in self.regex_handlers[pattern]:
                self.regex_handlers[pattern].append(handler)
                self.log_debug(f"订阅正则事件 {pattern_str} 成功")
                return True
            else:
                self.log_warning(f"处理器已订阅正则事件 {pattern_str}")
                return False
        else:
            # 添加到事件处理器字典
            if event_type not in self.handlers:
                self.handlers[event_type] = []
            
            # 检查处理器是否已存在
            if handler not in self.handlers[event_type]:
                self.handlers[event_type].append(handler)
                self.log_debug(f"订阅事件 {event_type} 成功")
                return True
            else:
                self.log_warning(f"处理器已订阅事件 {event_type}")
                return False

    @catch_exceptions
    def unsubscribe(self, event_type: str, handler: EventHandler) -> bool:
        """取消订阅事件
        
        Args:
            event_type: 事件类型，支持正则表达式（以 re: 开头）
            handler: 事件处理器
            
        Returns:
            bool: 是否取消订阅成功
        """
        # 检查是否为正则表达式
        if event_type.startswith("re:"):
            pattern_str = event_type[3:]
            pattern = re.compile(pattern_str)
            
            # 检查正则表达式是否存在
            if pattern not in self.regex_handlers:
                self.log_warning(f"正则事件 {pattern_str} 未订阅")
                return False
            
            # 检查处理器是否存在
            if handler not in self.regex_handlers[pattern]:
                self.log_warning(f"处理器未订阅正则事件 {pattern_str}")
                return False
            
            # 移除处理器
            self.regex_handlers[pattern].remove(handler)
            
            # 如果处理器列表为空，则移除正则表达式
            if not self.regex_handlers[pattern]:
                del self.regex_handlers[pattern]
            
            self.log_debug(f"取消订阅正则事件 {pattern_str} 成功")
            return True
        else:
            # 检查事件类型是否存在
            if event_type not in self.handlers:
                self.log_warning(f"事件 {event_type} 未订阅")
                return False
            
            # 检查处理器是否存在
            if handler not in self.handlers[event_type]:
                self.log_warning(f"处理器未订阅事件 {event_type}")
                return False
            
            # 移除处理器
            self.handlers[event_type].remove(handler)
            
            # 如果处理器列表为空，则移除事件类型
            if not self.handlers[event_type]:
                del self.handlers[event_type]
            
            self.log_debug(f"取消订阅事件 {event_type} 成功")
            return True

    @catch_exceptions
    @log_execution_time
    async def publish(self, event: Union[Event, str], data: Any = None) -> List[Any]:
        """发布事件
        
        Args:
            event: 事件对象或事件类型
            data: 事件数据，当 event 为事件类型时使用
            
        Returns:
            List[Any]: 处理器返回值列表
        """
        # 如果 event 是字符串，则创建事件对象
        if isinstance(event, str):
            from .types import Event
            event = Event(event, data)
        
        event_type = event.type
        results = []
        
        # 调用事件处理器
        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                try:
                    result = handler(event)
                    if asyncio.iscoroutine(result):
                        result = await result
                    results.append(result)
                except Exception as e:
                    self.log_error(f"处理事件 {event_type} 时发生错误: {e}", exc_info=True)
        
        # 调用正则表达式处理器
        for pattern, handlers in self.regex_handlers.items():
            if pattern.match(event_type):
                for handler in handlers:
                    try:
                        result = handler(event)
                        if asyncio.iscoroutine(result):
                            result = await result
                        results.append(result)
                    except Exception as e:
                        self.log_error(f"处理正则事件 {pattern.pattern} 时发生错误: {e}", exc_info=True)
        
        return results
    
    def publish_sync(self, event: Union[Event, str], data: Any = None) -> List[Any]:
        """同步发布事件
        
        Args:
            event: 事件对象或事件类型
            data: 事件数据，当 event 为事件类型时使用
            
        Returns:
            List[Any]: 处理器返回值列表
        """
        # 如果 event 是字符串，则创建事件对象
        if isinstance(event, str):
            from .types import Event
            event = Event(event, data)
        
        event_type = event.type
        results = []
        
        try:
            # 调用事件处理器
            if event_type in self.handlers:
                for handler in self.handlers[event_type]:
                    try:
                        result = handler(event)
                        if asyncio.iscoroutine(result):
                            self.log_warning(f"处理器 {handler.__name__} 返回了协程，但使用了同步发布")
                            continue
                        results.append(result)
                    except Exception as e:
                        self.log_error(f"处理事件 {event_type} 时发生错误: {e}", exc_info=True)
            
            # 调用正则表达式处理器
            for pattern, handlers in self.regex_handlers.items():
                if pattern.match(event_type):
                    for handler in handlers:
                        try:
                            result = handler(event)
                            if asyncio.iscoroutine(result):
                                self.log_warning(f"处理器 {handler.__name__} 返回了协程，但使用了同步发布")
                                continue
                            results.append(result)
                        except Exception as e:
                            self.log_error(f"处理正则事件 {pattern.pattern} 时发生错误: {e}", exc_info=True)
            
            return results
        
        except Exception as e:
            self.log_error(f"同步发布事件 {event_type} 失败: {e}", exc_info=True)
            return []
    
    async def publish_async(self, event: Union[Event, str], data: Any = None) -> None:
        """异步发布事件（不等待结果）
        
        Args:
            event: 事件对象或事件类型
            data: 事件数据，当 event 为事件类型时使用
        """
        # 创建任务
        asyncio.create_task(self.publish(event, data))
    
    def clear(self) -> None:
        """清空所有事件处理器"""
        self.handlers.clear()
        self.regex_handlers.clear()
        self.log_debug("清空所有事件处理器成功")
    
    def get_handler_count(self, event_type: str = None) -> int:
        """获取事件处理器数量
        
        Args:
            event_type: 事件类型，如果为 None 则返回所有处理器数量
            
        Returns:
            int: 处理器数量
        """
        if event_type is None:
            # 计算所有处理器数量
            count = sum(len(handlers) for handlers in self.handlers.values())
            count += sum(len(handlers) for handlers in self.regex_handlers.values())
            return count
        elif event_type.startswith("re:"):
            # 计算正则表达式处理器数量
            pattern_str = event_type[3:]
            pattern = re.compile(pattern_str)
            return len(self.regex_handlers.get(pattern, []))
        else:
            # 计算事件类型处理器数量
            return len(self.handlers.get(event_type, []))
    
    def emit(self, event_type: str, data: Any = None) -> None:
        """发布事件（同步）
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        self.publish_sync(event_type, data)
    
    async def emit_async(self, event_type: str, data: Any = None) -> List[Any]:
        """发布事件（异步）
        
        Args:
            event_type: 事件类型
            data: 事件数据
            
        Returns:
            List[Any]: 处理器返回值列表
        """
        return await self.publish(event_type, data) 