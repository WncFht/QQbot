#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
NapcatBot 主程序入口文件
"""
import os
import sys
import asyncio
import signal
from ncatbot import NcatBot
from src.utils import get_logger, setup_logger, get_config
from src.core import get_plugin_manager, get_event_manager, get_command_manager

# 设置日志
setup_logger(level="INFO", log_dir="logs")
logger = get_logger("main")

# 获取配置
config = get_config()

# 获取管理器实例
plugin_manager = get_plugin_manager()
event_manager = get_event_manager()
command_manager = get_command_manager()

async def init_bot():
    """初始化机器人"""
    try:
        # 创建数据目录
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("plugins", exist_ok=True)
        
        # 加载插件
        plugin_manager.load_all_plugins()
        
        # 创建机器人实例
        bot = NcatBot(config_path="config.json")
        
        # 注册事件处理器
        @bot.on_message
        async def handle_message(event):
            # 先尝试作为命令处理
            command_result = await command_manager.handle_message(event)
            if command_result:
                return
            
            # 如果不是命令，则触发事件
            await event_manager.emit(event)
        
        # 启动机器人
        await bot.start()
        
        return bot
    except Exception as e:
        logger.error(f"初始化机器人失败: {e}", exc_info=True)
        return None

async def shutdown_bot(bot):
    """关闭机器人"""
    try:
        # 卸载所有插件
        plugin_manager.unload_all_plugins()
        
        # 关闭机器人
        if bot:
            await bot.stop()
        
        logger.info("机器人已关闭")
    except Exception as e:
        logger.error(f"关闭机器人失败: {e}", exc_info=True)

def signal_handler(sig, frame):
    """信号处理函数"""
    logger.info(f"接收到信号 {sig}，准备关闭...")
    if 'bot' in globals() and bot:
        asyncio.create_task(shutdown_bot(bot))
    else:
        sys.exit(0)

async def main():
    """主函数"""
    global bot
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 初始化机器人
    logger.info("正在启动 NapcatBot...")
    bot = await init_bot()
    
    if not bot:
        logger.error("启动失败")
        return
    
    logger.info("NapcatBot 已启动")
    
    try:
        # 保持运行
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("主循环被取消")
    finally:
        # 关闭机器人
        await shutdown_bot(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")
    except Exception as e:
        logger.error(f"程序异常: {e}", exc_info=True)
    finally:
        logger.info("程序已退出") 