"""
消息解析工具类
"""
import json
import re
from typing import Dict, List, Optional, Union, Any
from ncatbot.utils.logger import get_log
from ncatbot.core.message import GroupMessage, PrivateMessage

logger = get_log()

class MessageParser:
    """消息解析类"""
    
    @staticmethod
    def parse_group_message(msg: GroupMessage) -> Optional[Dict[str, Any]]:
        """解析群消息
        
        Args:
            msg: 群消息对象
            
        Returns:
            解析后的消息字典，解析失败返回None
        """
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
            logger.error(f"解析群消息失败: {e}", exc_info=True)
            return None
    
    @staticmethod
    def parse_private_message(msg: PrivateMessage) -> Optional[Dict[str, Any]]:
        """解析私聊消息
        
        Args:
            msg: 私聊消息对象
            
        Returns:
            解析后的消息字典，解析失败返回None
        """
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
                "group_id": None,
                "user_id": user_id,
                "message_type": message_type,
                "content": content,
                "raw_message": raw_message,
                "time": time_stamp,
                "message_seq": None,
                "message_data": message_data_json
            }
        except Exception as e:
            logger.error(f"解析私聊消息失败: {e}", exc_info=True)
            return None
    
    @staticmethod
    def extract_text(message: Union[List[Dict[str, Any]], Dict[str, Any], str]) -> str:
        """从消息中提取纯文本内容
        
        Args:
            message: 消息对象，可以是列表、字典或字符串
            
        Returns:
            提取的文本内容
        """
        try:
            if isinstance(message, str):
                try:
                    # 尝试解析JSON字符串
                    message_obj = json.loads(message)
                    return MessageParser.extract_text(message_obj)
                except json.JSONDecodeError:
                    # 如果不是JSON，直接返回字符串
                    return message
            
            if isinstance(message, list):
                text_parts = []
                for item in message:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_parts.append(item.get("data", {}).get("text", ""))
                return "".join(text_parts)
            
            if isinstance(message, dict):
                if "message" in message:
                    return MessageParser.extract_text(message["message"])
                if "raw_message" in message:
                    return message["raw_message"]
                
            return ""
        except Exception as e:
            logger.error(f"提取消息文本失败: {e}", exc_info=True)
            return ""
    
    @staticmethod
    def has_image(message: Union[List[Dict[str, Any]], Dict[str, Any], str]) -> bool:
        """检查消息是否包含图片
        
        Args:
            message: 消息对象，可以是列表、字典或字符串
            
        Returns:
            是否包含图片
        """
        try:
            if isinstance(message, str):
                try:
                    # 尝试解析JSON字符串
                    message_obj = json.loads(message)
                    return MessageParser.has_image(message_obj)
                except json.JSONDecodeError:
                    # 如果不是JSON，检查是否包含图片标记
                    return "[CQ:image" in message
            
            if isinstance(message, list):
                for item in message:
                    if isinstance(item, dict) and item.get("type") == "image":
                        return True
            
            if isinstance(message, dict):
                if "message" in message:
                    return MessageParser.has_image(message["message"])
                
            return False
        except Exception as e:
            logger.error(f"检查消息图片失败: {e}", exc_info=True)
            return False
    
    @staticmethod
    def get_at_targets(message: Union[List[Dict[str, Any]], Dict[str, Any], str]) -> List[str]:
        """获取消息中@的目标
        
        Args:
            message: 消息对象，可以是列表、字典或字符串
            
        Returns:
            @的目标QQ号列表
        """
        try:
            targets = []
            
            if isinstance(message, str):
                try:
                    # 尝试解析JSON字符串
                    message_obj = json.loads(message)
                    return MessageParser.get_at_targets(message_obj)
                except json.JSONDecodeError:
                    # 如果不是JSON，使用正则表达式提取@目标
                    at_pattern = r"\[CQ:at,qq=(\d+)\]"
                    targets.extend(re.findall(at_pattern, message))
                    return targets
            
            if isinstance(message, list):
                for item in message:
                    if isinstance(item, dict) and item.get("type") == "at":
                        target = item.get("data", {}).get("qq")
                        if target:
                            targets.append(target)
            
            if isinstance(message, dict):
                if "message" in message:
                    return MessageParser.get_at_targets(message["message"])
                
            return targets
        except Exception as e:
            logger.error(f"获取@目标失败: {e}", exc_info=True)
            return []
    
    @staticmethod
    def get_image_urls(message: Union[List[Dict[str, Any]], Dict[str, Any], str]) -> List[str]:
        """获取消息中的图片URL列表
        
        Args:
            message: 消息对象，可以是列表、字典或字符串
            
        Returns:
            图片URL列表
        """
        try:
            urls = []
            
            if isinstance(message, str):
                try:
                    # 尝试解析JSON字符串
                    message_obj = json.loads(message)
                    return MessageParser.get_image_urls(message_obj)
                except json.JSONDecodeError:
                    # 如果不是JSON，使用正则表达式提取图片URL
                    image_pattern = r"\[CQ:image,.*?url=([^,\]]+)"
                    urls.extend(re.findall(image_pattern, message))
                    return urls
            
            if isinstance(message, list):
                for item in message:
                    if isinstance(item, dict) and item.get("type") == "image":
                        url = item.get("data", {}).get("url")
                        if url:
                            urls.append(url)
            
            if isinstance(message, dict):
                if "message" in message:
                    return MessageParser.get_image_urls(message["message"])
                
            return urls
        except Exception as e:
            logger.error(f"获取图片URL失败: {e}", exc_info=True)
            return []
    
    @staticmethod
    def is_command(message: str, command_prefix: str = "/") -> bool:
        """检查消息是否是命令
        
        Args:
            message: 消息文本
            command_prefix: 命令前缀，默认为"/"
            
        Returns:
            是否是命令
        """
        try:
            message = message.strip()
            return message.startswith(command_prefix)
        except Exception as e:
            logger.error(f"检查命令失败: {e}", exc_info=True)
            return False
    
    @staticmethod
    def parse_command(message: str, command_prefix: str = "/") -> tuple:
        """解析命令和参数
        
        Args:
            message: 消息文本
            command_prefix: 命令前缀，默认为"/"
            
        Returns:
            (命令, 参数列表)元组
        """
        try:
            message = message.strip()
            if not message.startswith(command_prefix):
                return "", []
            
            # 移除命令前缀
            command_text = message[len(command_prefix):]
            
            # 分割命令和参数
            parts = command_text.split()
            if not parts:
                return "", []
            
            command = parts[0].lower()
            args = parts[1:]
            
            return command, args
        except Exception as e:
            logger.error(f"解析命令失败: {e}", exc_info=True)
            return "", [] 