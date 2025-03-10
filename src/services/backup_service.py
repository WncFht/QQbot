"""
备份服务模块
"""
import time
from ncatbot.utils.logger import get_log

logger = get_log()

class BackupService:
    """备份服务类"""
    
    def __init__(self, db, backup_interval=3600):
        """初始化备份服务"""
        self.db = db
        self.backup_interval = backup_interval
        self.last_backup_time = time.time()
    
    def backup_database(self):
        """备份数据库"""
        try:
            # 使用数据库工具类进行备份
            if self.db.backup():
                logger.info("数据库备份成功")
            else:
                logger.error("数据库备份失败")
            
            self.last_backup_time = time.time()
            return True
        except Exception as e:
            logger.error(f"备份数据库失败: {e}")
            return False
    
    def check_backup_needed(self):
        """检查是否需要备份"""
        current_time = time.time()
        return current_time - self.last_backup_time >= self.backup_interval 