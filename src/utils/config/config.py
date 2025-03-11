"""
配置管理模块
"""
import json
import os
import logging
from ncatbot.utils.logger import get_log

logger = get_log()

class Config:
    """配置管理类"""
    
    def __init__(self, config_path="config.json"):
        """初始化配置"""
        self.config_path = config_path
        self.bot_uin = ""
        self.target_groups = []
        self.database_path = "messages.db"
        self.backup_interval = 3600
        self.history_fetch_interval = 1800
        self.ws_uri = "ws://localhost:3001"
        self.token = ""
        self.max_retries = 3
        
        self.load()
    
    def load(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    
                self.bot_uin = config_data.get("bot_uin", "")
                self.target_groups = config_data.get("target_groups", [])
                self.database_path = config_data.get("database_path", "messages.db")
                self.backup_interval = config_data.get("backup_interval", 3600)
                self.history_fetch_interval = config_data.get("history_fetch_interval", 1800)
                self.ws_uri = config_data.get("ws_uri", "ws://localhost:3001")
                self.token = config_data.get("token", "")
                self.max_retries = config_data.get("max_retries", 3)
                
                logger.info(f"配置加载成功: 目标群 {self.target_groups}")
                return True
            else:
                logger.warning(f"配置文件 {self.config_path} 不存在，使用默认配置")
                self.create_default_config()
                return False
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            return False
    
    def create_default_config(self):
        """创建默认配置文件"""
        try:
            default_config = {
                "bot_uin": "",
                "target_groups": [],
                "database_path": "messages.db",
                "backup_interval": 3600,
                "history_fetch_interval": 1800,
                "ws_uri": "ws://localhost:3001",
                "token": "",
                "max_retries": 3
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            logger.info(f"已创建默认配置文件 {self.config_path}，请修改后重新启动")
            return True
        except Exception as e:
            logger.error(f"创建默认配置文件失败: {e}")
            return False
    
    def save(self):
        """保存配置到文件"""
        try:
            config_data = {
                "bot_uin": self.bot_uin,
                "target_groups": self.target_groups,
                "database_path": self.database_path,
                "backup_interval": self.backup_interval,
                "history_fetch_interval": self.history_fetch_interval,
                "ws_uri": self.ws_uri,
                "token": self.token,
                "max_retries": self.max_retries
            }
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            logger.info(f"配置已保存到 {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            return False 