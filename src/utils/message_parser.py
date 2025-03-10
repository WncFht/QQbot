"""
消息解析工具类
"""
import json
from ncatbot.utils.logger import get_log
from ncatbot.core.message import GroupMessage, PrivateMessage

logger = get_log()

class MessageParser:
    """消息解析类"""
    
    @staticmethod
    def parse_group_message(msg: GroupMessage):
        """解析群消息"""
        try:
            # 提取基本信息
            message_id = msg.message_id
            group_id = msg.group_id
            user_id = msg.user_id
            message_type = msg.message_type
            raw_message = msg.raw_message
            time_stamp = msg.time
            message_seq = msg.message_seq
            
            # 提取消息内容
            content = json.dumps(msg.message, ensure_ascii=False)
            
            # 构造完整消息数据
            message_data = {
                "message_id": message_id,
                "group_id": group_id,
                "user_id": user_id,
                "message_type": message_type,
                "raw_message": raw_message,
                "time": time_stamp,
                "message_seq": message_seq,
                "message": msg.message,
                "sender": {
                    "user_id": msg.sender.user_id,
                    "nickname": msg.sender.nickname,
                    "card": msg.sender.card
                }
            }
            
            # 转换为JSON字符串
            message_data_json = json.dumps(message_data, ensure_ascii=False, default=str)
            
            return {
                "message_id": message_id,
                "group_id": group_id,
                "user_id": user_id,
                "message_type": message_type,
                "content": content,
                "raw_message": raw_message,
                "time": time_stamp,
                "message_seq": message_seq,
                "message_data": message_data_json
            }
        except Exception as e:
            logger.error(f"解析群消息失败: {e}")
            return None
    
    @staticmethod
    def extract_text(message):
        """从消息中提取纯文本内容"""
        try:
            if isinstance(message, list):
                text_parts = []
                for item in message:
                    if item.get("type") == "text":
                        text_parts.append(item.get("data", {}).get("text", ""))
                return "".join(text_parts)
            return ""
        except Exception as e:
            logger.error(f"提取消息文本失败: {e}")
            return ""
    
    @staticmethod
    def has_image(message):
        """检查消息是否包含图片"""
        try:
            if isinstance(message, list):
                for item in message:
                    if item.get("type") == "image":
                        return True
            return False
        except Exception as e:
            logger.error(f"检查消息图片失败: {e}")
            return False
    
    @staticmethod
    def get_at_targets(message):
        """获取消息中@的目标"""
        try:
            targets = []
            if isinstance(message, list):
                for item in message:
                    if item.get("type") == "at":
                        target = item.get("data", {}).get("qq")
                        if target:
                            targets.append(target)
            return targets
        except Exception as e:
            logger.error(f"获取@目标失败: {e}")
            return []
    
    @staticmethod
    def parse_private_message(msg: PrivateMessage):
        """解析私聊消息"""
        try:
            # 提取基本信息
            message_id = msg.message_id
            user_id = msg.user_id
            message_type = msg.message_type
            raw_message = msg.raw_message
            time_stamp = msg.time
            
            # 提取消息内容
            content = json.dumps(msg.message, ensure_ascii=False)
            
            # 构造完整消息数据
            message_data = {
                "message_id": message_id,
                "user_id": user_id,
                "message_type": message_type,
                "raw_message": raw_message,
                "time": time_stamp,
                "message": msg.message,
                "sender": {
                    "user_id": msg.sender.user_id,
                    "nickname": msg.sender.nickname
                }
            }
            
            # 转换为JSON字符串
            message_data_json = json.dumps(message_data, ensure_ascii=False, default=str)
            
            return {
                "message_id": message_id,
                "user_id": user_id,
                "message_type": message_type,
                "content": content,
                "raw_message": raw_message,
                "time": time_stamp,
                "message_data": message_data_json
            }
        except Exception as e:
            logger.error(f"解析私聊消息失败: {e}")
            return None 