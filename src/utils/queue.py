"""
消息队列模块
"""
import asyncio
import random
import time
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from ncatbot.core.element import MessageChain
from .logger import get_logger

logger = get_logger("message_queue")

class MessageQueue:
    """消息队列类，用于控制消息发送频率"""
    
    def __init__(self, min_interval: float = 1.0, max_interval: float = 3.0, 
                 max_queue_size: int = 100, retry_times: int = 3):
        """初始化消息队列
        
        Args:
            min_interval: 最小发送间隔（秒）
            max_interval: 最大发送间隔（秒）
            max_queue_size: 最大队列大小
            retry_times: 发送失败重试次数
        """
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.max_queue_size = max_queue_size
        self.retry_times = retry_times
        
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.running = False
        self.last_send_time = 0
        self.task: Optional[asyncio.Task] = None
    
    async def put(self, message: Union[str, MessageChain], target_id: Union[int, str], 
                 bot: Any, message_type: str = "group", priority: int = 0) -> bool:
        """将消息放入队列
        
        Args:
            message: 消息内容，可以是字符串或消息链
            target_id: 目标ID（群号或用户QQ号）
            bot: 机器人实例
            message_type: 消息类型（group/private）
            priority: 优先级，数字越小优先级越高
            
        Returns:
            bool: 是否成功放入队列
        """
        try:
            if self.queue.full():
                logger.warning(f"消息队列已满，丢弃消息: {message}")
                return False
            
            await self.queue.put((message, target_id, bot, message_type, priority))
            
            # 如果队列处理器未运行，启动它
            if not self.running:
                self.start()
            
            return True
        except Exception as e:
            logger.error(f"放入消息队列失败: {e}", exc_info=True)
            return False
    
    def start(self):
        """启动消息队列处理器"""
        if not self.running:
            self.running = True
            self.task = asyncio.create_task(self._process_queue())
            logger.info("消息队列处理器已启动")
    
    def stop(self):
        """停止消息队列处理器"""
        if self.running:
            self.running = False
            if self.task:
                self.task.cancel()
                self.task = None
            logger.info("消息队列处理器已停止")
    
    async def _process_queue(self):
        """处理消息队列"""
        try:
            while self.running:
                # 如果队列为空，等待一段时间
                if self.queue.empty():
                    await asyncio.sleep(0.1)
                    continue
                
                # 计算距离上次发送的时间
                now = time.time()
                elapsed = now - self.last_send_time
                
                # 如果时间间隔不够，等待
                if elapsed < self.min_interval:
                    await asyncio.sleep(self.min_interval - elapsed)
                
                # 获取队列中的消息
                try:
                    message, target_id, bot, message_type, priority = await self.queue.get()
                    
                    # 随机延迟，避免风控
                    delay = random.uniform(self.min_interval, self.max_interval)
                    await asyncio.sleep(delay)
                    
                    # 发送消息
                    success = await self._send_message(message, target_id, bot, message_type)
                    
                    # 更新最后发送时间
                    self.last_send_time = time.time()
                    
                    # 标记任务完成
                    self.queue.task_done()
                    
                    if not success:
                        logger.warning(f"发送消息失败: {message}")
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"处理消息队列异常: {e}", exc_info=True)
                    await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("消息队列处理器被取消")
        except Exception as e:
            logger.error(f"消息队列处理器异常: {e}", exc_info=True)
        finally:
            self.running = False
            logger.info("消息队列处理器已停止")
    
    async def _send_message(self, message: Union[str, MessageChain], target_id: Union[int, str], 
                           bot: Any, message_type: str) -> bool:
        """发送消息
        
        Args:
            message: 消息内容，可以是字符串或消息链
            target_id: 目标ID（群号或用户QQ号）
            bot: 机器人实例
            message_type: 消息类型（group/private）
            
        Returns:
            bool: 是否发送成功
        """
        for i in range(self.retry_times):
            try:
                if message_type == "group":
                    if isinstance(message, str):
                        await bot.api.post_group_msg(group_id=target_id, text=message)
                    else:
                        await bot.api.post_group_msg(group_id=target_id, rtf=message)
                else:
                    if isinstance(message, str):
                        await bot.api.post_private_msg(user_id=target_id, text=message)
                    else:
                        await bot.api.post_private_msg(user_id=target_id, rtf=message)
                
                return True
            except Exception as e:
                logger.error(f"发送消息失败 (尝试 {i+1}/{self.retry_times}): {e}", exc_info=True)
                await asyncio.sleep(1)
        
        return False

class RequestQueue:
    """请求队列类，用于控制API请求频率"""
    
    def __init__(self, min_interval: float = 1.0, max_interval: float = 3.0, 
                 max_queue_size: int = 100, retry_times: int = 3):
        """初始化请求队列
        
        Args:
            min_interval: 最小请求间隔（秒）
            max_interval: 最大请求间隔（秒）
            max_queue_size: 最大队列大小
            retry_times: 请求失败重试次数
        """
        self.min_interval = min_interval
        self.max_interval = max_interval
        self.max_queue_size = max_queue_size
        self.retry_times = retry_times
        
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.running = False
        self.last_request_time = 0
        self.task: Optional[asyncio.Task] = None
    
    async def put(self, func: Callable, *args, **kwargs) -> asyncio.Future:
        """将请求放入队列
        
        Args:
            func: 要执行的异步函数
            *args: 函数参数
            **kwargs: 函数关键字参数
            
        Returns:
            asyncio.Future: 请求结果的Future对象
        """
        future = asyncio.get_event_loop().create_future()
        
        try:
            if self.queue.full():
                logger.warning(f"请求队列已满，丢弃请求: {func.__name__}")
                future.set_exception(RuntimeError("请求队列已满"))
                return future
            
            await self.queue.put((func, args, kwargs, future))
            
            # 如果队列处理器未运行，启动它
            if not self.running:
                self.start()
            
            return future
        except Exception as e:
            logger.error(f"放入请求队列失败: {e}", exc_info=True)
            future.set_exception(e)
            return future
    
    def start(self):
        """启动请求队列处理器"""
        if not self.running:
            self.running = True
            self.task = asyncio.create_task(self._process_queue())
            logger.info("请求队列处理器已启动")
    
    def stop(self):
        """停止请求队列处理器"""
        if self.running:
            self.running = False
            if self.task:
                self.task.cancel()
                self.task = None
            logger.info("请求队列处理器已停止")
    
    async def _process_queue(self):
        """处理请求队列"""
        try:
            while self.running:
                # 如果队列为空，等待一段时间
                if self.queue.empty():
                    await asyncio.sleep(0.1)
                    continue
                
                # 计算距离上次请求的时间
                now = time.time()
                elapsed = now - self.last_request_time
                
                # 如果时间间隔不够，等待
                if elapsed < self.min_interval:
                    await asyncio.sleep(self.min_interval - elapsed)
                
                # 获取队列中的请求
                try:
                    func, args, kwargs, future = await self.queue.get()
                    
                    # 随机延迟，避免风控
                    delay = random.uniform(self.min_interval, self.max_interval)
                    await asyncio.sleep(delay)
                    
                    # 执行请求
                    result = await self._execute_request(func, args, kwargs, future)
                    
                    # 更新最后请求时间
                    self.last_request_time = time.time()
                    
                    # 标记任务完成
                    self.queue.task_done()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"处理请求队列异常: {e}", exc_info=True)
                    await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("请求队列处理器被取消")
        except Exception as e:
            logger.error(f"请求队列处理器异常: {e}", exc_info=True)
        finally:
            self.running = False
            logger.info("请求队列处理器已停止")
    
    async def _execute_request(self, func: Callable, args: Tuple, kwargs: Dict, 
                              future: asyncio.Future) -> Any:
        """执行请求
        
        Args:
            func: 要执行的异步函数
            args: 函数参数
            kwargs: 函数关键字参数
            future: 请求结果的Future对象
            
        Returns:
            Any: 请求结果
        """
        for i in range(self.retry_times):
            try:
                result = await func(*args, **kwargs)
                future.set_result(result)
                return result
            except Exception as e:
                logger.error(f"执行请求失败 (尝试 {i+1}/{self.retry_times}): {e}", exc_info=True)
                if i == self.retry_times - 1:
                    future.set_exception(e)
                await asyncio.sleep(1)
        
        return None 