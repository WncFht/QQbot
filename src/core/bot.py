"""
QQ机器人主模块
"""
import os
import time
import threading
import logging
from ncatbot.core import BotClient
from ncatbot.utils.config import config as ncatbot_config
from ncatbot.utils.logger import get_log

from .config import Config
from ..utils.database import Database
from ..services import GroupService, MessageService, BackupService
from ..handlers import GroupMessageHandler, PrivateMessageHandler

logger = get_log()

class QQBot:
    """QQ机器人主类"""
    
    def __init__(self, config_path="config.json"):
        """初始化QQ机器人"""
        # 加载配置
        self.config = Config(config_path)
        
        # 设置NcatBot配置
        ncatbot_config.set_bot_uin(self.config.bot_uin)
        ncatbot_config.set_ws_uri(self.config.ws_uri)
        ncatbot_config.set_token(self.config.token)
        
        logger.info(f"使用 WebSocket URI: {self.config.ws_uri}, Token: {self.config.token}")
        
        # 设置插件目录
        self.setup_plugins_dir()
        
        # 初始化NcatBot客户端
        self.bot = BotClient()
        
        # 初始化数据库
        self.db = Database(self.config.database_path)
        
        # 初始化服务
        self.group_service = GroupService(self.bot, self.db, self.config.target_groups)
        self.message_service = MessageService(self.bot, self.db, self.config.target_groups)
        self.backup_service = BackupService(self.db, self.config.backup_interval)
        
        # 初始化处理器
        self.group_handler = GroupMessageHandler(self.bot, self.message_service, self.config.target_groups)
        self.private_handler = PrivateMessageHandler(
            self.bot,
            self.message_service,
            self.backup_service,
            self.group_service,
            self.config.target_groups
        )
        
        # 注册事件处理函数
        self.register_handlers()
    
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
            
            logger.info(f"插件目录设置为: {plugins_dir}")
        except Exception as e:
            logger.error(f"设置插件目录失败: {e}")
    
    def register_handlers(self):
        """注册事件处理函数"""
        self.group_handler.register()
        self.private_handler.register()
    
    def _scheduled_tasks(self):
        """定时任务"""
        while True:
            try:
                current_time = time.time()
                
                # 定时备份数据库
                if self.backup_service.check_backup_needed():
                    logger.info("执行定时数据库备份")
                    self.backup_service.backup_database()
                
                # 定时获取历史消息
                if current_time - self.message_service.last_history_fetch_time >= self.config.history_fetch_interval:
                    logger.info("执行定时历史消息获取")
                    self.message_service.fetch_history_messages()
                
                # 每小时更新一次群信息
                if current_time % 3600 < 10:  # 每小时的前10秒
                    logger.info("执行定时群信息更新")
                    self.group_service.update_group_info()
                
                # 每10秒处理一次消息队列
                self.message_service.process_message_queue()
                
                time.sleep(10)
            except Exception as e:
                logger.error(f"定时任务执行失败: {e}")
                time.sleep(60)  # 出错后等待1分钟再继续
    
    def run(self):
        """运行机器人"""
        logger.info("QQ机器人启动中...")
        
        # 启动定时任务线程
        threading.Thread(target=self._scheduled_tasks, daemon=True).start()
        
        retry_count = 0
        max_retries = self.config.max_retries
        
        while retry_count < max_retries:
            try:
                # 启动NcatBot，设置 reload=True 表示不要尝试启动 napcat 服务器
                self.bot.run(reload=True)
                break  # 如果正常退出，跳出循环
            except KeyboardInterrupt:
                logger.info("接收到退出信号，正在关闭...")
                break
            except Exception as e:
                retry_count += 1
                logger.error(f"运行过程中发生错误 (尝试 {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    logger.info(f"将在 10 秒后重试...")
                    time.sleep(10)
                else:
                    logger.error("达到最大重试次数，退出程序")
        
        # 处理剩余消息并关闭数据库
        self.message_service.process_message_queue()
        self.db.close()
        logger.info("QQ机器人已关闭") 