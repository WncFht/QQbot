"""
备份配置模型
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta

@dataclass
class BackupConfig:
    """备份配置模型"""
    backup_interval: int = 3600  # 默认备份间隔（秒）
    backup_dir: str = "data/backups"  # 备份目录
    max_backups: int = 10  # 最大保留备份数
    backup_name_format: str = "backup_%Y%m%d_%H%M%S.db"  # 备份文件名格式
    
    def get_backup_filename(self) -> str:
        """获取备份文件名
        
        Returns:
            str: 备份文件名
        """
        return datetime.now().strftime(self.backup_name_format)
    
    def should_backup(self, last_backup_time: Optional[float]) -> bool:
        """检查是否需要备份
        
        Args:
            last_backup_time: 上次备份时间戳
            
        Returns:
            bool: 是否需要备份
        """
        if last_backup_time is None:
            return True
            
        last_backup = datetime.fromtimestamp(last_backup_time)
        next_backup = last_backup + timedelta(seconds=self.backup_interval)
        return datetime.now() >= next_backup 