"""
回声插件 - 简单的插件示例
"""
from .echo import EchoPlugin

# 导出插件类，用于 NcatBot 插件系统
__all__ = ["EchoPlugin"]

# 初始化插件实例
def init_plugin(event_bus, **kwargs):
    """初始化插件
    
    Args:
        event_bus: 事件总线
        **kwargs: 其他参数
        
    Returns:
        EchoPlugin: 插件实例
    """
    return EchoPlugin(event_bus=event_bus, **kwargs) 