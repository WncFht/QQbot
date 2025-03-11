"""
日志模块，用于提供日志功能
"""
import os
import logging
import logging.handlers
from typing import Dict, Optional

# 默认日志格式
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 日志级别映射
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

class LoggerManager:
    """日志管理器类，用于管理日志器"""
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化日志管理器"""
        # 避免重复初始化
        if self._initialized:
            return
        
        # 日志器字典，键为日志器名称，值为日志器对象
        self.loggers: Dict[str, logging.Logger] = {}
        
        self._initialized = True
    
    def get_logger(self, name: str, level: str = "INFO", log_dir: str = "logs",
                  console: bool = True, file: bool = True, max_bytes: int = 10485760,
                  backup_count: int = 5, log_format: str = DEFAULT_FORMAT) -> logging.Logger:
        """获取日志器
        
        Args:
            name: 日志器名称
            level: 日志级别
            log_dir: 日志目录
            console: 是否输出到控制台
            file: 是否输出到文件
            max_bytes: 日志文件最大字节数
            backup_count: 日志文件备份数量
            log_format: 日志格式
            
        Returns:
            logging.Logger: 日志器对象
        """
        # 检查是否已存在该名称的日志器
        if name in self.loggers:
            return self.loggers[name]
        
        # 创建日志器
        logger = logging.getLogger(name)
        
        # 设置日志级别
        log_level = LOG_LEVELS.get(level.upper(), logging.INFO)
        logger.setLevel(log_level)
        
        # 创建格式化器
        formatter = logging.Formatter(log_format)
        
        # 添加控制台处理器
        if console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # 添加文件处理器
        if file:
            # 确保日志目录存在
            os.makedirs(log_dir, exist_ok=True)
            
            # 创建文件处理器
            file_handler = logging.handlers.RotatingFileHandler(
                filename=os.path.join(log_dir, f"{name}.log"),
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # 保存日志器
        self.loggers[name] = logger
        
        return logger
    
    def setup_logger(self, name: str, level: str = "INFO", log_dir: str = "logs",
                    console: bool = True, file: bool = True, max_bytes: int = 10485760,
                    backup_count: int = 5, log_format: str = DEFAULT_FORMAT) -> logging.Logger:
        """设置日志器
        
        Args:
            name: 日志器名称
            level: 日志级别
            log_dir: 日志目录
            console: 是否输出到控制台
            file: 是否输出到文件
            max_bytes: 日志文件最大字节数
            backup_count: 日志文件备份数量
            log_format: 日志格式
            
        Returns:
            logging.Logger: 日志器对象
        """
        # 如果已存在该名称的日志器，先移除所有处理器
        if name in self.loggers:
            logger = self.loggers[name]
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
        
        # 创建日志器
        return self.get_logger(
            name=name,
            level=level,
            log_dir=log_dir,
            console=console,
            file=file,
            max_bytes=max_bytes,
            backup_count=backup_count,
            log_format=log_format
        )

# 创建全局日志管理器实例
logger_manager = LoggerManager()

def get_logger(name: str = "root", level: str = "INFO", log_dir: str = "logs",
              console: bool = True, file: bool = True) -> logging.Logger:
    """获取日志器
    
    Args:
        name: 日志器名称
        level: 日志级别
        log_dir: 日志目录
        console: 是否输出到控制台
        file: 是否输出到文件
        
    Returns:
        logging.Logger: 日志器对象
    """
    return logger_manager.get_logger(
        name=name,
        level=level,
        log_dir=log_dir,
        console=console,
        file=file
    )

def setup_logger(name: str = "root", level: str = "INFO", log_dir: str = "logs",
                console: bool = True, file: bool = True) -> logging.Logger:
    """设置日志器
    
    Args:
        name: 日志器名称
        level: 日志级别
        log_dir: 日志目录
        console: 是否输出到控制台
        file: 是否输出到文件
        
    Returns:
        logging.Logger: 日志器对象
    """
    return logger_manager.setup_logger(
        name=name,
        level=level,
        log_dir=log_dir,
        console=console,
        file=file
    ) 