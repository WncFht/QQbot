"""
消息分析插件
"""
from .analyzer import MessageAnalyzer

# 导出插件类，用于 NcatBot 插件系统
__all__ = ["MessageAnalyzer"]

# 设置数据库路径
database_path = "messages.db"

# 初始化插件实例
def init_plugin(event_bus, **kwargs):
    return MessageAnalyzer(event_bus=event_bus, database_path=database_path, **kwargs) 