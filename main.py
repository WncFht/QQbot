#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NapcatBot 主程序入口文件
"""
import os
import sys
import asyncio
import signal
import logging

from src.utils.logger import setup_logger, get_logger
from src.utils.config import get_config
from src.utils.database import init_database, close_all_connections, backup
from src.core import get_plugin_manager, get_event_manager, get_command_manager
from src.core.bot.bot import Bot

# 设置日志
setup_logger(level="INFO", log_dir="logs")
logger = get_logger("main")

# 获取配置
config = get_config()

# 获取管理器实例
plugin_manager = get_plugin_manager()
event_manager = get_event_manager()
command_manager = get_command_manager()

# 获取机器人实例
bot = Bot()

async def init():
    """初始化"""
    try:
        # 创建数据目录
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("plugins", exist_ok=True)
        
        # 初始化数据库
        init_database()
        
        # 加载插件
        await plugin_manager.load_all_plugins()
        
        # 初始化机器人
        await bot.init()
        
        logger.info("初始化完成")
        return True
    except Exception as e:
        logger.error(f"初始化失败: {e}", exc_info=True)
        return False

async def shutdown():
    """关闭"""
    try:
        # 卸载所有插件
        await plugin_manager.unload_all_plugins()
        
        # 停止机器人
        await bot.stop()
        
        # 备份数据库
        backup()
        
        # 关闭数据库连接
        close_all_connections()
        
        logger.info("关闭完成")
    except Exception as e:
        logger.error(f"关闭失败: {e}", exc_info=True)

def signal_handler(sig, frame):
    """信号处理函数"""
    logger.info(f"接收到信号 {sig}，准备关闭...")
    asyncio.create_task(shutdown())

async def main():
    """主函数"""
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 初始化
    logger.info("正在启动 NapcatBot...")
    if not await init():
        logger.error("启动失败")
        return
    
    # 启动机器人
    if not await bot.start():
        logger.error("启动机器人失败")
        await shutdown()
        return
    
    logger.info("NapcatBot 已启动")
    
    try:
        # 保持运行
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("主循环被取消")
    finally:
        # 关闭
        await shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常: {e}", exc_info=True)
    finally:
        logger.info("程序已退出") 