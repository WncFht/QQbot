"""
消息解析器模块，用于解析和处理QQ消息
"""
import re
import json
from typing import Dict, List, Optional, Union, Any, Tuple
from ncatbot.core.element import MessageChain, Plain, Image, At, Reply
from .logger import get_logger

logger = get_logger("message_parser")

class MessageParser:
    """消息解析器类，用于解析和处理QQ消息"""
    
    def __init__(self):
        """初始化消息解析器"""
        # 命令前缀，默认为 / 和 #
        self.command_prefixes = ['/', '#']
        # 命令正则表达式
        self.command_pattern = re.compile(r'^([/|#])(\w+)(?:\s+(.*))?$')
    
    def set_command_prefixes(self, prefixes: List[str]):
        """设置命令前缀
        
        Args:
            prefixes: 命令前缀列表
        """
        self.command_prefixes = prefixes
        prefix_str = '|'.join([re.escape(p) for p in prefixes])
        self.command_pattern = re.compile(f'^([{prefix_str}])(\\w+)(?:\\s+(.*))?$')
    
    def parse_command(self, message: str) -> Optional[Tuple[str, str]]:
        """解析命令
        
        Args:
            message: 消息文本
            
        Returns:
            Optional[Tuple[str, str]]: 命令名和参数，如果不是命令则返回None
        """
        try:
            # 检查是否是命令
            if not message or not message[0] in self.command_prefixes:
                return None
            
            # 解析命令
            match = self.command_pattern.match(message)
            if not match:
                return None
            
            command = match.group(2).lower()
            args = match.group(3) or ""
            
            return command, args.strip()
        except Exception as e:
            logger.error(f"解析命令失败: {e}", exc_info=True)
            return None
    
    def parse_args(self, args_str: str, expected_args: List[str] = None) -> Dict[str, str]:
        """解析命令参数
        
        Args:
            args_str: 参数字符串
            expected_args: 预期参数列表
            
        Returns:
            Dict[str, str]: 参数字典
        """
        result = {}
        
        try:
            # 如果没有预期参数，直接返回空字典
            if not expected_args:
                return result
            
            # 分割参数
            parts = args_str.split()
            
            # 处理位置参数
            for i, arg_name in enumerate(expected_args):
                if i < len(parts):
                    result[arg_name] = parts[i]
                else:
                    result[arg_name] = ""
            
            return result
        except Exception as e:
            logger.error(f"解析参数失败: {e}", exc_info=True)
            return result
    
    def parse_key_value_args(self, args_str: str) -> Dict[str, str]:
        """解析键值对参数
        
        Args:
            args_str: 参数字符串，格式为 "key1=value1 key2=value2"
            
        Returns:
            Dict[str, str]: 参数字典
        """
        result = {}
        
        try:
            # 分割参数
            parts = args_str.split()
            
            # 处理键值对参数
            for part in parts:
                if '=' in part:
                    key, value = part.split('=', 1)
                    result[key.strip()] = value.strip()
            
            return result
        except Exception as e:
            logger.error(f"解析键值对参数失败: {e}", exc_info=True)
            return result
    
    def extract_at_targets(self, message_chain: MessageChain) -> List[int]:
        """从消息链中提取@的目标
        
        Args:
            message_chain: 消息链
            
        Returns:
            List[int]: @的目标QQ号列表
        """
        targets = []
        
        try:
            for element in message_chain:
                if isinstance(element, At):
                    targets.append(element.target)
            
            return targets
        except Exception as e:
            logger.error(f"提取@目标失败: {e}", exc_info=True)
            return targets
    
    def extract_images(self, message_chain: MessageChain) -> List[str]:
        """从消息链中提取图片URL
        
        Args:
            message_chain: 消息链
            
        Returns:
            List[str]: 图片URL列表
        """
        images = []
        
        try:
            for element in message_chain:
                if isinstance(element, Image):
                    images.append(element.url)
            
            return images
        except Exception as e:
            logger.error(f"提取图片失败: {e}", exc_info=True)
            return images
    
    def extract_plain_text(self, message_chain: MessageChain) -> str:
        """从消息链中提取纯文本
        
        Args:
            message_chain: 消息链
            
        Returns:
            str: 纯文本内容
        """
        text = ""
        
        try:
            for element in message_chain:
                if isinstance(element, Plain):
                    text += element.text
            
            return text
        except Exception as e:
            logger.error(f"提取纯文本失败: {e}", exc_info=True)
            return text
    
    def build_message_chain(self, content: Union[str, List[Dict[str, Any]]]) -> MessageChain:
        """构建消息链
        
        Args:
            content: 消息内容，可以是字符串或消息元素列表
            
        Returns:
            MessageChain: 消息链
        """
        try:
            if isinstance(content, str):
                return MessageChain([Plain(content)])
            
            elements = []
            for item in content:
                element_type = item.get('type')
                if element_type == 'text':
                    elements.append(Plain(item.get('text', '')))
                elif element_type == 'image':
                    elements.append(Image(url=item.get('url', '')))
                elif element_type == 'at':
                    elements.append(At(target=item.get('target', 0)))
                elif element_type == 'reply':
                    elements.append(Reply(id=item.get('id', '')))
            
            return MessageChain(elements)
        except Exception as e:
            logger.error(f"构建消息链失败: {e}", exc_info=True)
            return MessageChain([Plain("消息构建失败")])
    
    def message_to_json(self, message_chain: MessageChain) -> str:
        """将消息链转换为JSON字符串
        
        Args:
            message_chain: 消息链
            
        Returns:
            str: JSON字符串
        """
        try:
            elements = []
            for element in message_chain:
                if isinstance(element, Plain):
                    elements.append({
                        'type': 'text',
                        'text': element.text
                    })
                elif isinstance(element, Image):
                    elements.append({
                        'type': 'image',
                        'url': element.url
                    })
                elif isinstance(element, At):
                    elements.append({
                        'type': 'at',
                        'target': element.target
                    })
                elif isinstance(element, Reply):
                    elements.append({
                        'type': 'reply',
                        'id': element.id
                    })
            
            return json.dumps(elements, ensure_ascii=False)
        except Exception as e:
            logger.error(f"消息转JSON失败: {e}", exc_info=True)
            return "[]"
    
    def json_to_message(self, json_str: str) -> MessageChain:
        """将JSON字符串转换为消息链
        
        Args:
            json_str: JSON字符串
            
        Returns:
            MessageChain: 消息链
        """
        try:
            elements = json.loads(json_str)
            return self.build_message_chain(elements)
        except Exception as e:
            logger.error(f"JSON转消息失败: {e}", exc_info=True)
            return MessageChain([Plain("消息解析失败")]) 