"""
备份服务实现
"""
import os
import glob
import time
import shutil
from pathlib import Path
from typing import List, Optional

from utils.logger import get_logger
from .models import BackupConfig

logger = get_logger(__name__)

class BackupService:
    """备份服务类"""
    
    def __init__(self, database, config: Optional[BackupConfig] = None):
        """初始化备份服务
        
        Args:
            database: 数据库实例
            config: 备份配置，如果为None则使用默认配置
        """
        self.database = database
        self.config = config or BackupConfig()
        self.last_backup_time: Optional[float] = None
        
        # 确保备份目录存在
        os.makedirs(self.config.backup_dir, exist_ok=True)
    
    async def backup(self) -> bool:
        """执行数据库备份
        
        Returns:
            bool: 备份是否成功
        """
        try:
            # 获取备份文件路径
            backup_path = os.path.join(
                self.config.backup_dir,
                self.config.get_backup_filename()
            )
            
            # 执行备份
            if await self.database.backup(backup_path):
                logger.info(f"数据库备份成功: {backup_path}")
                self.last_backup_time = time.time()
                
                # 清理旧备份
                await self._cleanup_old_backups()
                return True
            else:
                logger.error("数据库备份失败")
                return False
                
        except Exception as e:
            logger.error(f"执行备份失败: {e}")
            return False
    
    async def _cleanup_old_backups(self):
        """清理旧的备份文件"""
        try:
            # 获取所有备份文件
            pattern = os.path.join(self.config.backup_dir, "backup_*.db")
            backup_files = glob.glob(pattern)
            
            # 按修改时间排序
            backup_files.sort(key=os.path.getmtime, reverse=True)
            
            # 删除超出限制的旧备份
            if len(backup_files) > self.config.max_backups:
                for old_backup in backup_files[self.config.max_backups:]:
                    try:
                        os.remove(old_backup)
                        logger.info(f"删除旧备份: {old_backup}")
                    except Exception as e:
                        logger.error(f"删除旧备份失败: {e}")
        
        except Exception as e:
            logger.error(f"清理旧备份失败: {e}")
    
    def should_backup(self) -> bool:
        """检查是否需要执行备份
        
        Returns:
            bool: 是否需要备份
        """
        return self.config.should_backup(self.last_backup_time)
    
    async def restore(self, backup_file: str) -> bool:
        """从备份文件恢复数据库
        
        Args:
            backup_file: 备份文件名或路径
            
        Returns:
            bool: 恢复是否成功
        """
        try:
            # 如果只提供文件名，添加备份目录路径
            if not os.path.dirname(backup_file):
                backup_file = os.path.join(self.config.backup_dir, backup_file)
            
            # 检查备份文件是否存在
            if not os.path.exists(backup_file):
                logger.error(f"备份文件不存在: {backup_file}")
                return False
            
            # 执行恢复
            if await self.database.restore(backup_file):
                logger.info(f"数据库恢复成功: {backup_file}")
                return True
            else:
                logger.error("数据库恢复失败")
                return False
                
        except Exception as e:
            logger.error(f"执行恢复失败: {e}")
            return False
    
    def list_backups(self) -> List[str]:
        """获取所有备份文件列表
        
        Returns:
            List[str]: 备份文件名列表，按时间倒序排序
        """
        try:
            pattern = os.path.join(self.config.backup_dir, "backup_*.db")
            backup_files = glob.glob(pattern)
            
            # 按修改时间排序（最新的在前）
            backup_files.sort(key=os.path.getmtime, reverse=True)
            
            # 只返回文件名
            return [os.path.basename(f) for f in backup_files]
            
        except Exception as e:
            logger.error(f"获取备份列表失败: {e}")
            return [] 