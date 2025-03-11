"""
命令管理器模块
负责命令的注册和处理
"""
from typing import Dict, List, Optional, Callable, Any, Union
import re
from src.utils.singleton import Singleton
from src.core.utils import BaseComponent, catch_exceptions, log_execution_time
from src.core.auth import AuthManager
from .command import Command, CommandContext

class CommandManager(Singleton, BaseComponent):
    """命令管理器类"""
    
    def __init__(self):
        """初始化命令管理器"""
        # 避免重复初始化
        if hasattr(self, "_initialized") and self._initialized:
            return
            
        # 初始化基类
        super().__init__("command_manager")
        
        # 命令字典
        self.commands: Dict[str, Command] = {}
        
        # 命令别名字典
        self.aliases: Dict[str, str] = {}
        
        # 命令前缀
        self.prefix = "/"
        
        # 权限管理器
        self.auth_manager = AuthManager()
        
        self._initialized = True
    
    @catch_exceptions
    def register_command(self, command: Command) -> bool:
        """注册命令
        
        Args:
            command: 命令对象
            
        Returns:
            bool: 是否注册成功
        """
        # 检查命令名是否已存在
        if command.name in self.commands:
            self.log_warning(f"命令 {command.name} 已存在")
            return False
        
        # 检查命令别名是否已存在
        for alias in command.aliases:
            if alias in self.aliases:
                self.log_warning(f"命令别名 {alias} 已存在")
                return False
        
        # 注册命令
        self.commands[command.name] = command
        
        # 注册命令别名
        for alias in command.aliases:
            self.aliases[alias] = command.name
        
        self.log_info(f"注册命令 {command.name} 成功")
        return True
    
    @catch_exceptions
    def unregister_command(self, name: str) -> bool:
        """注销命令
        
        Args:
            name: 命令名称
            
        Returns:
            bool: 是否注销成功
        """
        # 检查命令是否存在
        if name not in self.commands:
            self.log_warning(f"命令 {name} 不存在")
            return False
        
        # 获取命令对象
        command = self.commands[name]
        
        # 移除命令别名
        for alias in command.aliases:
            if alias in self.aliases:
                del self.aliases[alias]
        
        # 移除命令
        del self.commands[name]
        
        self.log_info(f"注销命令 {name} 成功")
        return True
    
    def get_command(self, name: str) -> Optional[Command]:
        """获取命令对象
        
        Args:
            name: 命令名称或别名
            
        Returns:
            Optional[Command]: 命令对象，如果不存在则返回 None
        """
        # 检查是否是命令别名
        if name in self.aliases:
            name = self.aliases[name]
        
        # 返回命令对象
        return self.commands.get(name)
    
    @catch_exceptions
    def handle_message(self, context: CommandContext) -> bool:
        """处理消息
        
        Args:
            context: 命令上下文
            
        Returns:
            bool: 是否处理成功
        """
        # 检查消息是否以命令前缀开头
        if not context.message.startswith(self.prefix):
            return False
        
        # 解析命令名称和参数
        parts = context.message[len(self.prefix):].strip().split(maxsplit=1)
        if not parts:
            return False
        
        name = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # 获取命令对象
        command = self.get_command(name)
        if not command:
            self.log_warning(f"命令 {name} 不存在")
            return False
        
        # 检查权限
        if not self.auth_manager.check_command_permission(context.user_id, command.name):
            self.log_warning(f"用户 {context.user_id} 没有执行命令 {command.name} 的权限")
            return False
        
        # 解析命令参数
        try:
            parsed_args = command.parse_args(args)
        except Exception as e:
            self.log_error(f"解析命令 {command.name} 参数失败: {e}")
            return False
        
        # 执行命令
        try:
            result = command.execute(context, **parsed_args)
            self.log_info(f"执行命令 {command.name} 成功")
            return result
        except Exception as e:
            self.log_error(f"执行命令 {command.name} 失败: {e}")
            return False
    
    def get_commands(self) -> List[Command]:
        """获取所有命令列表
        
        Returns:
            List[Command]: 命令列表
        """
        return list(self.commands.values())
    
    def get_command_help(self, name: str) -> Optional[str]:
        """获取命令帮助信息
        
        Args:
            name: 命令名称或别名
            
        Returns:
            Optional[str]: 命令帮助信息，如果命令不存在则返回 None
        """
        command = self.get_command(name)
        if not command:
            return None
        
        # 生成帮助信息
        help_text = f"命令: {command.name}\n"
        if command.aliases:
            help_text += f"别名: {', '.join(command.aliases)}\n"
        help_text += f"描述: {command.description}\n"
        help_text += f"用法: {self.prefix}{command.name} {command.usage}\n"
        if command.examples:
            help_text += "示例:\n"
            for example in command.examples:
                help_text += f"  {self.prefix}{command.name} {example}\n"
        
        return help_text
    
    def get_all_commands_help(self) -> str:
        """获取所有命令的帮助信息
        
        Returns:
            str: 所有命令的帮助信息
        """
        help_text = "可用命令列表:\n\n"
        
        # 按名称排序命令
        commands = sorted(self.commands.values(), key=lambda x: x.name)
        
        for command in commands:
            help_text += f"{self.prefix}{command.name}"
            if command.aliases:
                help_text += f" ({', '.join(command.aliases)})"
            help_text += f": {command.description}\n"
        
        help_text += f"\n使用 {self.prefix}help <命令名> 获取详细帮助信息"
        return help_text
    
    @catch_exceptions
    def set_prefix(self, prefix: str) -> bool:
        """设置命令前缀
        
        Args:
            prefix: 命令前缀
            
        Returns:
            bool: 是否设置成功
        """
        if not prefix:
            self.log_warning("命令前缀不能为空")
            return False
        
        self.prefix = prefix
        self.log_info(f"设置命令前缀为 {prefix} 成功")
        return True 