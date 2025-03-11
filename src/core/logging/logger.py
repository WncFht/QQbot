"""
日志系统模块
"""
import os
import sys
import logging
import time
from datetime import datetime, timedelta
from logging.handlers import TimedRotatingFileHandler
from typing import Dict, Optional, Union, List

# 日志级别映射
LOG_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

# 日志保留时间（天）
LOG_RETENTION = {
    "DEBUG": 5,      # 调试日志保留5天
    "INFO": 30,      # 普通日志保留30天
    "WARNING": 60,   # 警告日志保留60天
    "ERROR": 90      # 错误日志保留90天
}

# 日志格式
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DETAILED_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"

# 日志实例缓存
_loggers: Dict[str, logging.Logger] = {}

class CustomFilter(logging.Filter):
    """自定义日志过滤器"""
    
    def __init__(self, name: str = "", exclude_modules: List[str] = None):
        """
        初始化过滤器
        
        Args:
            name: 过滤器名称
            exclude_modules: 要排除的模块列表
        """
        super().__init__(name)
        self.exclude_modules = exclude_modules or []
    
    def filter(self, record):
        """过滤日志记录"""
        # 排除指定模块的日志
        if any(record.name.startswith(module) for module in self.exclude_modules):
            return False
        
        return True

class DatabaseLogHandler(logging.Handler):
    """数据库日志处理器"""
    
    def __init__(self, db_conn, level=logging.NOTSET):
        """
        初始化数据库日志处理器
        
        Args:
            db_conn: 数据库连接
            level: 日志级别
        """
        super().__init__(level)
        self.db_conn = db_conn
        
        # 创建日志表
        cursor = self.db_conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            level TEXT,
            name TEXT,
            message TEXT,
            filename TEXT,
            lineno INTEGER,
            funcName TEXT
        )
        ''')
        self.db_conn.commit()
    
    def emit(self, record):
        """将日志记录写入数据库"""
        try:
            cursor = self.db_conn.cursor()
            cursor.execute('''
            INSERT INTO logs (timestamp, level, name, message, filename, lineno, funcName)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
                record.levelname,
                record.name,
                record.getMessage(),
                record.filename,
                record.lineno,
                record.funcName
            ))
            self.db_conn.commit()
        except Exception as e:
            print(f"Error writing log to database: {e}")

def setup_logger(
    name: str = "qqbot",
    level: Union[str, int] = "INFO",
    log_dir: str = "logs",
    console: bool = True,
    file: bool = True,
    db_conn = None,
    format_str: str = None,
    exclude_modules: List[str] = None
) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        log_dir: 日志目录
        console: 是否输出到控制台
        file: 是否输出到文件
        db_conn: 数据库连接，用于记录日志到数据库
        format_str: 日志格式字符串
        exclude_modules: 要排除的模块列表
        
    Returns:
        logging.Logger: 日志记录器
    """
    # 如果已经创建过该名称的日志记录器，则直接返回
    if name in _loggers:
        return _loggers[name]
    
    # 创建日志记录器
    logger = logging.getLogger(name)
    
    # 设置日志级别
    if isinstance(level, str):
        level = LOG_LEVELS.get(level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # 添加自定义过滤器
    logger.addFilter(CustomFilter(name, exclude_modules))
    
    # 设置日志格式
    if format_str is None:
        format_str = DETAILED_LOG_FORMAT if level <= logging.DEBUG else DEFAULT_LOG_FORMAT
    formatter = logging.Formatter(format_str)
    
    # 添加控制台处理器
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # 添加文件处理器
    if file:
        # 确保日志目录存在
        os.makedirs(log_dir, exist_ok=True)
        
        # 为不同级别的日志创建不同的文件处理器
        for level_name, level_value in LOG_LEVELS.items():
            if level_value >= level:
                # 创建日志子目录
                level_dir = os.path.join(log_dir, level_name.lower())
                os.makedirs(level_dir, exist_ok=True)
                
                # 创建按天轮转的文件处理器
                file_handler = TimedRotatingFileHandler(
                    filename=os.path.join(level_dir, f"{name}.log"),
                    when="midnight",
                    interval=1,
                    backupCount=LOG_RETENTION.get(level_name, 30)
                )
                file_handler.setLevel(level_value)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
    
    # 添加数据库处理器
    if db_conn:
        db_handler = DatabaseLogHandler(db_conn, level)
        db_handler.setFormatter(formatter)
        logger.addHandler(db_handler)
    
    # 缓存日志记录器
    _loggers[name] = logger
    
    return logger

def get_logger(name: str = "qqbot") -> logging.Logger:
    """
    获取日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器
    """
    # 如果已经创建过该名称的日志记录器，则直接返回
    if name in _loggers:
        return _loggers[name]
    
    # 否则创建一个新的日志记录器
    return setup_logger(name) 