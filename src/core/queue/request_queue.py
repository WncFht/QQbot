"""
请求队列模块
"""
import asyncio
import random
import time
from queue import PriorityQueue
from typing import Any, Dict, List, Optional, Tuple, Union
from ncatbot.utils.logger import get_log

logger = get_log()

class RequestPriority:
    """请求优先级"""
    HIGH = 0    # 高优先级
    NORMAL = 1  # 普通优先级
    LOW = 2     # 低优先级

class QueuedRequest:
    """队列中的请求"""
    
    def __init__(
        self, 
        bot: Any, 
        flag: str,
        sub_type: str,
        approve: bool,
        reason: str = "",
        priority: int = RequestPriority.NORMAL,
        retry_count: int = 0,
        max_retries: int = 3,
        delay: float = 0.0
    ):
        """
        初始化队列请求
        
        Args:
            bot: 机器人实例
            flag: 请求标识
            sub_type: 请求子类型
            approve: 是否同意请求
            reason: 拒绝理由
            priority: 请求优先级
            retry_count: 当前重试次数
            max_retries: 最大重试次数
            delay: 延迟处理时间（秒）
        """
        self.bot = bot
        self.flag = flag
        self.sub_type = sub_type
        self.approve = approve
        self.reason = reason
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

class RequestQueue:
    """请求队列类"""
    
    def __init__(self, rate_limit: float = 2.0, random_delay: bool = True):
        """
        初始化请求队列
        
        Args:
            rate_limit: 请求处理频率限制（秒/条）
            random_delay: 是否添加随机延迟
        """
        self.queue = PriorityQueue()
        self.rate_limit = rate_limit
        self.random_delay = random_delay
        self.last_process_time = 0.0
        self.running = False
        self.task = None
    
    def put(
        self, 
        bot: Any, 
        flag: str,
        sub_type: str,
        approve: bool,
        reason: str = "",
        priority: int = RequestPriority.NORMAL,
        delay: float = 0.0
    ) -> bool:
        """
        将请求放入队列
        
        Args:
            bot: 机器人实例
            flag: 请求标识
            sub_type: 请求子类型
            approve: 是否同意请求
            reason: 拒绝理由
            priority: 请求优先级
            delay: 延迟处理时间（秒）
            
        Returns:
            bool: 是否成功放入队列
        """
        try:
            # 创建队列请求
            queued_request = QueuedRequest(
                bot=bot,
                flag=flag,
                sub_type=sub_type,
                approve=approve,
                reason=reason,
                priority=priority,
                delay=delay
            )
            
            # 放入队列
            self.queue.put(queued_request)
            logger.debug(f"请求已加入队列: {sub_type} -> {flag}")
            return True
        except Exception as e:
            logger.error(f"将请求放入队列失败: {e}")
            return False
    
    async def start(self):
        """启动请求队列处理"""
        if self.running:
            logger.warning("请求队列已经在运行中")
            return
        
        self.running = True
        self.task = asyncio.create_task(self._process_queue())
        logger.info("请求队列处理已启动")
    
    async def stop(self):
        """停止请求队列处理"""
        if not self.running:
            logger.warning("请求队列未在运行")
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        logger.info("请求队列处理已停止")
    
    async def _process_queue(self):
        """处理请求队列"""
        while self.running:
            try:
                # 检查队列是否为空
                if self.queue.empty():
                    await asyncio.sleep(0.1)
                    continue
                
                # 获取当前时间
                current_time = time.time()
                
                # 检查是否需要限制处理频率
                if current_time - self.last_process_time < self.rate_limit:
                    await asyncio.sleep(0.1)
                    continue
                
                # 获取队列中的请求（不移除）
                queued_request = self.queue.queue[0]
                
                # 检查请求是否到达处理时间
                if queued_request.scheduled_time > current_time:
                    await asyncio.sleep(0.1)
                    continue
                
                # 移除队列中的请求
                queued_request = self.queue.get()
                
                # 处理请求
                success = await self._process_request(queued_request)
                
                # 更新最后处理时间
                self.last_process_time = time.time()
                
                # 如果处理失败且未达到最大重试次数，则重新放入队列
                if not success and queued_request.retry_count < queued_request.max_retries:
                    queued_request.retry_count += 1
                    queued_request.scheduled_time = time.time() + 2.0  # 延迟2秒后重试
                    self.queue.put(queued_request)
                    logger.warning(f"请求处理失败，将在2秒后重试 ({queued_request.retry_count}/{queued_request.max_retries})")
                
                # 添加随机延迟，避免请求处理过快
                if self.random_delay:
                    delay = self.rate_limit * (0.8 + 0.4 * random.random())  # 0.8~1.2倍的速率限制
                    await asyncio.sleep(delay)
                else:
                    await asyncio.sleep(self.rate_limit)
            
            except Exception as e:
                logger.error(f"处理请求队列时发生错误: {e}")
                await asyncio.sleep(1.0)
    
    async def _process_request(self, queued_request: QueuedRequest) -> bool:
        """
        处理请求
        
        Args:
            queued_request: 队列中的请求
            
        Returns:
            bool: 是否处理成功
        """
        try:
            # 根据请求类型处理请求
            if queued_request.sub_type == "friend":
                # 处理好友请求
                if queued_request.approve:
                    response = await queued_request.bot.api.set_friend_add_request(
                        flag=queued_request.flag,
                        approve=True,
                        remark=""
                    )
                    logger.info(f"已同意好友请求: {queued_request.flag}")
                else:
                    response = await queued_request.bot.api.set_friend_add_request(
                        flag=queued_request.flag,
                        approve=False,
                        remark=""
                    )
                    logger.info(f"已拒绝好友请求: {queued_request.flag}")
            elif queued_request.sub_type in ["add", "invite"]:
                # 处理群请求
                if queued_request.approve:
                    response = await queued_request.bot.api.set_group_add_request(
                        flag=queued_request.flag,
                        sub_type=queued_request.sub_type,
                        approve=True,
                        reason=""
                    )
                    logger.info(f"已同意群请求: {queued_request.flag}")
                else:
                    response = await queued_request.bot.api.set_group_add_request(
                        flag=queued_request.flag,
                        sub_type=queued_request.sub_type,
                        approve=False,
                        reason=queued_request.reason
                    )
                    logger.info(f"已拒绝群请求: {queued_request.flag}")
            else:
                logger.error(f"未知的请求类型: {queued_request.sub_type}")
                return False
            
            # 检查响应
            if response and response.get("status") == "ok":
                return True
            else:
                logger.warning(f"处理请求失败: {response}")
                return False
        
        except Exception as e:
            logger.error(f"处理请求时发生错误: {e}")
            return False 