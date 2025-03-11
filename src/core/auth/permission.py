"""
权限级别定义
"""
from enum import Enum

class PermissionLevel(Enum):
    """权限级别枚举"""
    BANNED = -1      # 黑名单
    NORMAL = 0       # 普通用户
    ADMIN = 1        # 管理员
    SUPER_ADMIN = 2  # 超级管理员
    OWNER = 3        # 拥有者 