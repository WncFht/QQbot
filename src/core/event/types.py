"""
事件类型定义模块
定义事件基类和常用事件类型
"""
from typing import Dict, Any, Optional

class Event:
    """事件基类"""
    
    def __init__(self, type: str, data: Any = None):
        """初始化事件
        
        Args:
            type: 事件类型
            data: 事件数据
        """
        self.type = type
        self.data = data if data is not None else {}
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            str: 事件信息
        """
        return f"Event(type={self.type}, data={self.data})"
    
    def __repr__(self) -> str:
        """表示形式
        
        Returns:
            str: 事件信息
        """
        return self.__str__()

# 官方事件类型
OFFICIAL_GROUP_MESSAGE_EVENT = "ncatbot.group_message_event"
OFFICIAL_PRIVATE_MESSAGE_EVENT = "ncatbot.private_message_event"
OFFICIAL_REQUEST_EVENT = "ncatbot.request_event"
OFFICIAL_NOTICE_EVENT = "ncatbot.notice_event"

# 自定义事件类型
GROUP_MESSAGE_EVENT = "group_message"
PRIVATE_MESSAGE_EVENT = "private_message"
GROUP_MEMBER_INCREASE_EVENT = "group_member_increase"
GROUP_MEMBER_DECREASE_EVENT = "group_member_decrease"
GROUP_ADMIN_CHANGE_EVENT = "group_admin_change"
GROUP_FILE_UPLOAD_EVENT = "group_file_upload"
GROUP_BAN_EVENT = "group_ban"
FRIEND_ADD_EVENT = "friend_add"
FRIEND_RECALL_EVENT = "friend_recall"
GROUP_RECALL_EVENT = "group_recall"
POKE_EVENT = "poke"
LUCKY_KING_EVENT = "lucky_king"
HONOR_EVENT = "honor"

class MessageEvent(Event):
    """消息事件基类"""
    
    def __init__(self, type: str, message_id: str, sender_id: str, content: str, raw_message: str, time: int, data: Dict[str, Any] = None):
        """初始化消息事件
        
        Args:
            type: 事件类型
            message_id: 消息ID
            sender_id: 发送者ID
            content: 消息内容
            raw_message: 原始消息
            time: 消息时间戳
            data: 其他数据
        """
        super().__init__(type, data or {})
        self.message_id = message_id
        self.sender_id = sender_id
        self.content = content
        self.raw_message = raw_message
        self.time = time
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            str: 消息事件信息
        """
        return f"MessageEvent(type={self.type}, message_id={self.message_id}, sender_id={self.sender_id}, content={self.content}, time={self.time})"

class GroupMessageEvent(MessageEvent):
    """群消息事件"""
    
    def __init__(self, message_id: str, group_id: str, sender_id: str, content: str, raw_message: str, time: int, data: Dict[str, Any] = None):
        """初始化群消息事件
        
        Args:
            message_id: 消息ID
            group_id: 群ID
            sender_id: 发送者ID
            content: 消息内容
            raw_message: 原始消息
            time: 消息时间戳
            data: 其他数据
        """
        super().__init__(GROUP_MESSAGE_EVENT, message_id, sender_id, content, raw_message, time, data)
        self.group_id = group_id
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            str: 群消息事件信息
        """
        return f"GroupMessageEvent(message_id={self.message_id}, group_id={self.group_id}, sender_id={self.sender_id}, content={self.content}, time={self.time})"

class PrivateMessageEvent(MessageEvent):
    """私聊消息事件"""
    
    def __init__(self, message_id: str, sender_id: str, content: str, raw_message: str, time: int, data: Dict[str, Any] = None):
        """初始化私聊消息事件
        
        Args:
            message_id: 消息ID
            sender_id: 发送者ID
            content: 消息内容
            raw_message: 原始消息
            time: 消息时间戳
            data: 其他数据
        """
        super().__init__(PRIVATE_MESSAGE_EVENT, message_id, sender_id, content, raw_message, time, data)
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            str: 私聊消息事件信息
        """
        return f"PrivateMessageEvent(message_id={self.message_id}, sender_id={self.sender_id}, content={self.content}, time={self.time})"

class GroupMemberEvent(Event):
    """群成员事件基类"""
    
    def __init__(self, type: str, group_id: str, user_id: str, operator_id: str = None, data: Dict[str, Any] = None):
        """初始化群成员事件
        
        Args:
            type: 事件类型
            group_id: 群ID
            user_id: 用户ID
            operator_id: 操作者ID
            data: 其他数据
        """
        super().__init__(type, data or {})
        self.group_id = group_id
        self.user_id = user_id
        self.operator_id = operator_id
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            str: 群成员事件信息
        """
        return f"GroupMemberEvent(type={self.type}, group_id={self.group_id}, user_id={self.user_id}, operator_id={self.operator_id})"

class GroupMemberIncreaseEvent(GroupMemberEvent):
    """群成员增加事件"""
    
    def __init__(self, group_id: str, user_id: str, operator_id: str = None, data: Dict[str, Any] = None):
        """初始化群成员增加事件
        
        Args:
            group_id: 群ID
            user_id: 用户ID
            operator_id: 操作者ID
            data: 其他数据
        """
        super().__init__(GROUP_MEMBER_INCREASE_EVENT, group_id, user_id, operator_id, data)
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            str: 群成员增加事件信息
        """
        return f"GroupMemberIncreaseEvent(group_id={self.group_id}, user_id={self.user_id}, operator_id={self.operator_id})"

class GroupMemberDecreaseEvent(GroupMemberEvent):
    """群成员减少事件"""
    
    def __init__(self, group_id: str, user_id: str, operator_id: str = None, data: Dict[str, Any] = None):
        """初始化群成员减少事件
        
        Args:
            group_id: 群ID
            user_id: 用户ID
            operator_id: 操作者ID
            data: 其他数据
        """
        super().__init__(GROUP_MEMBER_DECREASE_EVENT, group_id, user_id, operator_id, data)
    
    def __str__(self) -> str:
        """字符串表示
        
        Returns:
            str: 群成员减少事件信息
        """
        return f"GroupMemberDecreaseEvent(group_id={self.group_id}, user_id={self.user_id}, operator_id={self.operator_id})" 