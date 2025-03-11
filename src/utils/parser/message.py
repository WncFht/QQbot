"""
消息解析器模块
用于解析和处理QQ消息
"""
import re
import json
from typing import Dict, List, Optional, Union, Any, Tuple
from ncatbot.core.element import MessageChain, Plain, Image, At, Reply
from ..logger import get_logger
from ..singleton import Singleton

logger = get_logger("message_parser")

class MessageParser(Singleton):
    """消息解析器类，用于解析和处理QQ消息"""
    
    def __init__(self):
        """初始化消息解析器"""
        # 避免重复初始化
        if hasattr(self, "_initialized") and self._initialized:
            return
            
        # 命令前缀，默认为 / 和 #
        self.command_prefixes = ['/', '#']
        
        # 命令正则表达式
        self._update_command_pattern()
        
        # 初始化标记
        self._initialized = True
    
    def _update_command_pattern(self):
        """更新命令正则表达式"""
        prefix_str = '|'.join([re.escape(p) for p in self.command_prefixes])
        self.command_pattern = re.compile(f'^([{prefix_str}])(\\w+)(?:\\s+(.*))?$')
    
    def set_command_prefixes(self, prefixes: List[str]):
        """设置命令前缀
        
        Args:
            prefixes: 命令前缀列表
        """
        self.command_prefixes = prefixes
        self._update_command_pattern()
    
    def parse_command(self, message: str) -> Optional[Tuple[str, str]]:
        """解析命令
        
        Args:
            message: 消息文本
            
        Returns:
            Optional[Tuple[str, str]]: (命令名, 参数) 元组，如果不是命令则返回 None
        """
        if not message:
            return None
            
        match = self.command_pattern.match(message)
        if match:
            prefix, command, args = match.groups()
            return command, args or ""
            
        return None
    
    def parse_args(self, args_str: str, expected_args: List[str] = None) -> Dict[str, str]:
        """解析命令参数
        
        Args:
            args_str: 参数字符串
            expected_args: 预期参数列表
            
        Returns:
            Dict[str, str]: 参数字典
        """
        args = {}
        
        if not args_str:
            return args
            
        # 如果没有预期参数，则按空格分割
        if not expected_args:
            parts = args_str.split()
            for i, part in enumerate(parts):
                args[str(i)] = part
            return args
        
        # 按预期参数解析
        parts = args_str.split(maxsplit=len(expected_args)-1)
        for i, arg_name in enumerate(expected_args):
            if i < len(parts):
                args[arg_name] = parts[i]
            else:
                args[arg_name] = ""
        
        return args
    
    def parse_key_value_args(self, args_str: str) -> Dict[str, str]:
        """解析键值对参数
        
        Args:
            args_str: 参数字符串，格式为 "key1=value1 key2=value2"
            
        Returns:
            Dict[str, str]: 参数字典
        """
        args = {}
        
        if not args_str:
            return args
            
        # 使用正则表达式匹配键值对
        pattern = re.compile(r'(\w+)=([^\s]+)')
        matches = pattern.finditer(args_str)
        
        for match in matches:
            key, value = match.groups()
            args[key] = value
        
        return args
    
    def extract_at_targets(self, message_chain: MessageChain) -> List[int]:
        """提取消息中的 @目标
        
        Args:
            message_chain: 消息链
            
        Returns:
            List[int]: @目标QQ号列表
        """
        targets = []
        
        for element in message_chain:
            if isinstance(element, At):
                try:
                    targets.append(int(element.target))
                except (ValueError, TypeError):
                    logger.warning(f"无效的 @目标: {element.target}")
        
        return targets
    
    def extract_images(self, message_chain: MessageChain) -> List[str]:
        """提取消息中的图片
        
        Args:
            message_chain: 消息链
            
        Returns:
            List[str]: 图片URL列表
        """
        images = []
        
        for element in message_chain:
            if isinstance(element, Image):
                if element.url:
                    images.append(element.url)
                elif element.path:
                    images.append(f"file://{element.path}")
        
        return images
    
    def extract_plain_text(self, message_chain: MessageChain) -> str:
        """提取消息中的纯文本
        
        Args:
            message_chain: 消息链
            
        Returns:
            str: 纯文本内容
        """
        text = []
        
        for element in message_chain:
            if isinstance(element, Plain):
                text.append(element.text)
        
        return "".join(text)
    
    def build_message_chain(self, content: Union[str, List[Dict[str, Any]]]) -> MessageChain:
        """构建消息链
        
        Args:
            content: 消息内容，可以是字符串或消息元素列表
            
        Returns:
            MessageChain: 消息链
        """
        if isinstance(content, str):
            return MessageChain([Plain(content)])
            
        elements = []
        for element_data in content:
            element_type = element_data.get("type")
            if element_type == "text":
                elements.append(Plain(element_data.get("text", "")))
            elif element_type == "image":
                elements.append(Image(
                    url=element_data.get("url"),
                    path=element_data.get("path")
                ))
            elif element_type == "at":
                elements.append(At(element_data.get("target")))
            elif element_type == "reply":
                elements.append(Reply(element_data.get("message_id")))
        
        return MessageChain(elements)
    
    def message_to_json(self, message_chain: MessageChain) -> str:
        """将消息链转换为 JSON 字符串
        
        Args:
            message_chain: 消息链
            
        Returns:
            str: JSON 字符串
        """
        elements = []
        
        for element in message_chain:
            if isinstance(element, Plain):
                elements.append({
                    "type": "text",
                    "text": element.text
                })
            elif isinstance(element, Image):
                element_data = {
                    "type": "image"
                }
                if element.url:
                    element_data["url"] = element.url
                if element.path:
                    element_data["path"] = element.path
                elements.append(element_data)
            elif isinstance(element, At):
                elements.append({
                    "type": "at",
                    "target": element.target
                })
            elif isinstance(element, Reply):
                elements.append({
                    "type": "reply",
                    "message_id": element.message_id
                })
        
        return json.dumps(elements, ensure_ascii=False)
    
    def json_to_message(self, json_str: str) -> MessageChain:
        """将 JSON 字符串转换为消息链
        
        Args:
            json_str: JSON 字符串
            
        Returns:
            MessageChain: 消息链
        """
        try:
            content = json.loads(json_str)
            return self.build_message_chain(content)
        except json.JSONDecodeError as e:
            logger.error(f"解析 JSON 失败: {e}")
            return MessageChain([Plain(json_str)])

# 创建全局消息解析器实例
parser = MessageParser()

# 导出常用函数和类
__all__ = ["MessageParser", "parser"] 