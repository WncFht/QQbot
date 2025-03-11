"""
QQ机器人主模块
"""
import os
import time
import asyncio
import threading
from datetime import datetime
from ncatbot.core import BotClient
from ncatbot.utils.config import config as ncatbot_config
from ncatbot.utils.logger import get_log

from .config import Config
from .permission import AuthManager, Permission, PermissionLevel
from .queue import MessageQueue, RequestQueue
from .logging import setup_logger
from .database import DatabaseManager

from ..handlers import GroupMessageHandler, PrivateMessageHandler
from ..utils.message_parser import MessageParser

logger = get_log()

class QQBot:
    """QQ机器人主类"""
    
    def __init__(self, config_path="config.json"):
        """初始化QQ机器人"""
        # 设置日志系统
        self.logger = setup_logger(
            name="qqbot",
            level="INFO",
            log_dir="logs",
            console=True,
            file=True
        )
        
        self.logger.info("正在初始化QQ机器人...")
        
        # 加载配置
        self.config = Config(config_path)
        
        # 设置NcatBot配置
        ncatbot_config.set_bot_uin(self.config.bot_uin)
        ncatbot_config.set_ws_uri(self.config.ws_uri)
        ncatbot_config.set_token(self.config.token)
        
        self.logger.info(f"使用 WebSocket URI: {self.config.ws_uri}, Token: {self.config.token}")
        
        # 设置插件目录
        self.setup_plugins_dir()
        
        # 初始化NcatBot客户端
        self.bot = BotClient()
        
        # 初始化数据库
        self.db_manager = DatabaseManager(self.config.database_path)
        
        # 初始化权限系统
        self.auth_manager = AuthManager("data/permission.json")
        
        # 设置超级用户和拥有者
        if hasattr(self.config, 'superusers'):
            self.auth_manager.set_superusers(self.config.superusers)
        if hasattr(self.config, 'owner'):
            self.auth_manager.set_owner(self.config.owner)
        
        # 初始化消息队列
        self.message_queue = MessageQueue(rate_limit=1.0, random_delay=True)
        self.request_queue = RequestQueue(rate_limit=2.0, random_delay=True)
        
        # 初始化处理器
        self.group_handler = GroupMessageHandler(
            bot=self.bot,
            message_queue=self.message_queue,
            db_manager=self.db_manager,
            auth_manager=self.auth_manager,
            target_groups=self.config.target_groups
        )
        
        self.private_handler = PrivateMessageHandler(
            bot=self.bot,
            message_queue=self.message_queue,
            request_queue=self.request_queue,
            db_manager=self.db_manager,
            auth_manager=self.auth_manager,
            target_groups=self.config.target_groups
        )
        
        # 注册事件处理函数
        self.register_handlers()
        
        # 上次备份和历史消息获取时间
        self.last_backup_time = time.time()
        self.last_history_fetch_time = time.time()
        
        self.logger.info("QQ机器人初始化完成")
    
    def setup_plugins_dir(self):
        """设置插件目录"""
        try:
            # 确保插件目录存在
            os.makedirs("plugins", exist_ok=True)
            os.makedirs("plugins/analyzer", exist_ok=True)
            
            # 设置插件目录为当前工作目录下的 plugins 文件夹
            plugins_dir = os.path.abspath("plugins")
            
            # 设置环境变量
            os.environ["NCATBOT_PLUGINS_DIR"] = plugins_dir
            
            self.logger.info(f"插件目录设置为: {plugins_dir}")
        except Exception as e:
            self.logger.error(f"设置插件目录失败: {e}")
    
    def register_handlers(self):
        """注册事件处理函数"""
        self.group_handler.register()
        self.private_handler.register()
    
    async def start_services(self):
        """启动各项服务"""
        # 启动消息队列
        await self.message_queue.start()
        await self.request_queue.start()
        
        # 更新群信息
        await self.group_handler.update_group_info()
        
        # 获取历史消息
        await self.group_handler.fetch_history_messages()
    
    async def stop_services(self):
        """停止各项服务"""
        # 停止消息队列
        await self.message_queue.stop()
        await self.request_queue.stop()
    
    def _scheduled_tasks(self):
        """定时任务"""
        while True:
            try:
                current_time = time.time()
                
                # 定时备份数据库
                if current_time - self.last_backup_time >= self.config.backup_interval:
                    self.logger.info("执行定时数据库备份")
                    backup_path = f"data/backups/messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                    self.db_manager.backup(backup_path)
                    self.last_backup_time = time.time()
                
                # 定时获取历史消息
                if current_time - self.last_history_fetch_time >= self.config.history_fetch_interval:
                    self.logger.info("执行定时历史消息获取")
                    asyncio.run(self.group_handler.fetch_history_messages())
                    self.last_history_fetch_time = time.time()
                
                # 每小时更新一次群信息
                if current_time % 3600 < 10:  # 每小时的前10秒
                    self.logger.info("执行定时群信息更新")
                    asyncio.run(self.group_handler.update_group_info())
                
                # 每天优化一次数据库
                if current_time % 86400 < 10:  # 每天的前10秒
                    self.logger.info("执行定时数据库优化")
                    self.db_manager.optimize()
                
                time.sleep(10)
            except Exception as e:
                self.logger.error(f"定时任务执行失败: {e}")
                time.sleep(60)  # 出错后等待1分钟再继续
    
    def run(self):
        """运行机器人"""
        self.logger.info("QQ机器人启动中...")
        
        # 启动定时任务线程
        threading.Thread(target=self._scheduled_tasks, daemon=True).start()
        
        # 启动服务
        asyncio.run(self.start_services())
        
        retry_count = 0
        max_retries = self.config.max_retries
        
        while retry_count < max_retries:
            try:
                # 启动NcatBot，设置 reload=True 表示不要尝试启动 napcat 服务器
                self.bot.run(reload=True)
                break  # 如果正常退出，跳出循环
            except KeyboardInterrupt:
                self.logger.info("接收到退出信号，正在关闭...")
                break
            except Exception as e:
                retry_count += 1
                self.logger.error(f"运行过程中发生错误 (尝试 {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    self.logger.info(f"将在 10 秒后重试...")
                    time.sleep(10)
                else:
                    self.logger.error("达到最大重试次数，退出程序")
        
        # 停止服务
        asyncio.run(self.stop_services())
        
        # 关闭数据库
        self.db_manager.close()
        self.logger.info("QQ机器人已关闭") 