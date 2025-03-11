"""
消息队列模块
"""
import asyncio
import random
import time
from queue import PriorityQueue, Queue
from typing import Any, Dict, List, Optional, Tuple, Union
from ncatbot.utils.logger import get_log
from ncatbot.core.message import GroupMessage, PrivateMessage

logger = get_log()

class MessagePriority:
    """消息优先级"""
    HIGH = 0    # 高优先级
    NORMAL = 1  # 普通优先级
    LOW = 2     # 低优先级

class QueuedMessage:
    """队列中的消息"""
    
    def __init__(
        self, 
        message: Any, 
        target_id: Union[int, str], 
        bot: Any, 
        message_type: str = "group",
        priority: int = MessagePriority.NORMAL,
        retry_count: int = 0,
        max_retries: int = 3,
        delay: float = 0.0
    ):
        """
        初始化队列消息
        
        Args:
            message: 消息内容
            target_id: 目标ID（群号或用户ID）
            bot: 机器人实例
            message_type: 消息类型，"group"或"private"
            priority: 消息优先级
            retry_count: 当前重试次数
            max_retries: 最大重试次数
            delay: 延迟发送时间（秒）
        """
        self.message = message
        self.target_id = target_id
        self.bot = bot
        self.message_type = message_type
        self.priority = priority
        self.retry_count = retry_count
        self.max_retries = max_retries
        self.delay = delay
        self.create_time = time.time()
        self.scheduled_time = self.create_time + delay
    
    def __lt__(self, other):
        """比较优先级，用于优先级队列排序"""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.scheduled_time < other.scheduled_time

class MessageQueue:
    """消息队列类"""
    
    def __init__(self, rate_limit: float = 1.0, random_delay: bool = True):
        """
        初始化消息队列
        
        Args:
            rate_limit: 消息发送频率限制（秒/条）
            random_delay: 是否添加随机延迟
        """
        self.queue = PriorityQueue()
        self.rate_limit = rate_limit
        self.random_delay = random_delay
        self.last_send_time = 0.0
        self.running = False
        self.task = None
    
    def put(
        self, 
        message: Any, 
        target_id: Union[int, str], 
        bot: Any, 
        message_type: str = "group",
        priority: int = MessagePriority.NORMAL,
        delay: float = 0.0
    ) -> bool:
        """
        将消息放入队列
        
        Args:
            message: 消息内容
            target_id: 目标ID（群号或用户ID）
            bot: 机器人实例
            message_type: 消息类型，"group"或"private"
            priority: 消息优先级
            delay: 延迟发送时间（秒）
            
        Returns:
            bool: 是否成功放入队列
        """
        try:
            # 创建队列消息
            queued_message = QueuedMessage(
                message=message,
                target_id=target_id,
                bot=bot,
                message_type=message_type,
                priority=priority,
                delay=delay
            )
            
            # 放入队列
            self.queue.put(queued_message)
            logger.debug(f"消息已加入队列: {message_type} -> {target_id}")
            return True
        except Exception as e:
            logger.error(f"将消息放入队列失败: {e}")
            return False
    
    async def start(self):
        """启动消息队列处理"""
        if self.running:
            logger.warning("消息队列已经在运行中")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._process_queue())
        logger.info("消息队列处理已启动")
    
    async def stop(self):
        """停止消息队列处理"""
        if not self.running:
            logger.warning("消息队列未在运行")
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        logger.info("消息队列处理已停止")
    
    async def _process_queue(self):
        """处理消息队列"""
        while self.running:
            try:
                # 检查队列是否为空
                if self.queue.empty():
                    await asyncio.sleep(0.1)
                    continue
                
                # 获取当前时间
                current_time = time.time()
                
                # 检查是否需要限制发送频率
                if current_time - self.last_send_time < self.rate_limit:
                    await asyncio.sleep(0.1)
                    continue
                
                # 获取队列中的消息（不移除）
                queued_message = self.queue.queue[0]
                
                # 检查消息是否到达发送时间
                if queued_message.scheduled_time > current_time:
                    await asyncio.sleep(0.1)
                    continue
                
                # 移除队列中的消息
                queued_message = self.queue.get()
                
                # 发送消息
                success = await self._send_message(queued_message)
                
                # 更新最后发送时间
                self.last_send_time = time.time()
                
                # 如果发送失败且未达到最大重试次数，则重新放入队列
                if not success and queued_message.retry_count < queued_message.max_retries:
                    queued_message.retry_count += 1
                    queued_message.scheduled_time = time.time() + 2.0  # 延迟2秒后重试
                    self.queue.put(queued_message)
                    logger.warning(f"消息发送失败，将在2秒后重试 ({queued_message.retry_count}/{queued_message.max_retries})")
                
                # 添加随机延迟，避免消息发送过快
                if self.random_delay:
                    delay = self.rate_limit * (0.8 + 0.4 * random.random())  # 0.8~1.2倍的速率限制
                    await asyncio.sleep(delay)
                else:
                    await asyncio.sleep(self.rate_limit)
            
            except Exception as e:
                logger.error(f"处理消息队列时发生错误: {e}")
                await asyncio.sleep(1.0)
    
    async def _send_message(self, queued_message: QueuedMessage) -> bool:
        """
        发送消息
        
        Args:
            queued_message: 队列中的消息
            
        Returns:
            bool: 是否发送成功
        """
        try:
            # 根据消息类型发送消息
            if queued_message.message_type == "group":
                # 发送群消息
                response = await queued_message.bot.api.post_group_msg(
                    group_id=queued_message.target_id,
                    rtf=queued_message.message
                )
                logger.info(f"发送群消息: {queued_message.target_id}")
            elif queued_message.message_type == "private":
                # 发送私聊消息
                response = await queued_message.bot.api.post_private_msg(
                    user_id=queued_message.target_id,
                    rtf=queued_message.message
                )
                logger.info(f"发送私聊消息: {queued_message.target_id}")
            else:
                logger.error(f"未知的消息类型: {queued_message.message_type}")
                return False
            
            # 检查响应
            if response and response.get("status") == "ok":
                return True
            else:
                logger.warning(f"发送消息失败: {response}")
                return False
        
        except Exception as e:
            logger.error(f"发送消息时发生错误: {e}")
            return False 