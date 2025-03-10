#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
QQ机器人主程序入口
"""
import os
import logging
from src.core import QQBot

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def main():
    """主程序入口"""
    # 创建必要的目录
    os.makedirs("plugins/analyzer", exist_ok=True)
    os.makedirs("data/backups", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # 创建并运行机器人
    bot = QQBot()
    bot.run()

if __name__ == "__main__":
    main() 