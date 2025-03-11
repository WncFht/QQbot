"""
私聊消息处理模块
"""
import asyncio
from datetime import datetime
from ncatbot.utils.logger import get_log
from ncatbot.core.message import PrivateMessage
from ncatbot.core.element import MessageChain, Text

from ..core.permission import Permission, PermissionLevel

logger = get_log()

class PrivateMessageHandler:
    """私聊消息处理类"""
    
    def __init__(self, bot, message_queue, request_queue, db_manager, auth_manager, target_groups):
        """
        初始化私聊消息处理器
        
        Args:
            bot: 机器人实例
            message_queue: 消息队列
            request_queue: 请求队列
            db_manager: 数据库管理器
            auth_manager: 权限管理器
            target_groups: 目标群列表
        """
        self.bot = bot
        self.message_queue = message_queue
        self.request_queue = request_queue
        self.db_manager = db_manager
        self.auth_manager = auth_manager
        self.target_groups = target_groups
    
    async def handle(self, msg: PrivateMessage):
        """处理私聊消息"""
        try:
            # 添加日志输出
            logger.info(f"收到私聊消息: {msg.raw_message} 来自: {msg.user_id}")
            
            # 检查是否为命令
            if msg.raw_message == "状态":
                logger.info(f"处理状态命令")
                await self._handle_status_command(msg)
            elif msg.raw_message == "备份":
                logger.info(f"处理备份命令")
                await self._handle_backup_command(msg)
            elif msg.raw_message == "更新群信息":
                logger.info(f"处理更新群信息命令")
                await self._handle_update_group_info_command(msg)
            elif msg.raw_message == "获取历史消息":
                logger.info(f"处理获取历史消息命令")
                await self._handle_fetch_history_command(msg)
            elif msg.raw_message.startswith("分析 "):
                logger.info(f"处理分析命令")
                await self._handle_analyze_command(msg)
            elif msg.raw_message == "插件列表":
                logger.info(f"处理插件列表命令")
                await self._handle_plugin_list_command(msg)
            elif msg.raw_message.startswith("权限 "):
                logger.info(f"处理权限命令")
                await self._handle_permission_command(msg)
            elif msg.raw_message == "帮助":
                logger.info(f"处理帮助命令")
                await self._handle_help_command(msg)
            else:
                # 保存普通私聊消息
                logger.info(f"保存普通私聊消息")
                from ..utils.message_parser import MessageParser
                parsed_msg = MessageParser.parse_private_message(msg)
                if parsed_msg:
                    # 保存到数据库
                    self.db_manager.execute(
                        """
                        INSERT OR REPLACE INTO messages 
                        (message_id, user_id, message_type, content, raw_message, time, message_seq, message_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            parsed_msg["message_id"],
                            parsed_msg["user_id"],
                            parsed_msg["message_type"],
                            parsed_msg["content"],
                            parsed_msg["raw_message"],
                            parsed_msg["time"],
                            parsed_msg.get("message_seq", ""),  # 添加message_seq字段，私聊消息可能没有此字段
                            parsed_msg["message_data"]
                        )
                    )
        except Exception as e:
            logger.error(f"处理私聊消息失败: {e}", exc_info=True)
            await msg.reply(f"处理命令失败: {e}")
    
    async def _handle_status_command(self, msg: PrivateMessage):
        """处理状态命令"""
        # 检查权限
        if not await self._check_permission(msg, "status"):
            return
        
        # 获取机器人状态信息
        group_count = len(self.target_groups)
        message_count = self.db_manager.query_one("SELECT COUNT(*) FROM messages")[0]
        
        # 移除对created_at字段的引用
        uptime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        status_text = f"机器人状态:\n"
        status_text += f"- 监听群数量: {group_count}\n"
        status_text += f"- 已保存消息数: {message_count}\n"
        status_text += f"- 当前时间: {uptime}"
        
        # 直接使用reply方法回复
        try:
            await msg.reply(text=status_text)
            logger.info(f"已回复状态信息")
        except Exception as e:
            logger.error(f"回复状态信息失败: {e}", exc_info=True)
            # 使用消息队列发送
            await self.message_queue.put(
                MessageChain([Text(status_text)]),
                msg.user_id,
                self.bot,
                message_type="private",
                priority=1
            )
    
    async def _handle_backup_command(self, msg: PrivateMessage):
        """处理备份命令"""
        # 检查权限
        if not await self._check_permission(msg, "backup"):
            return
        
        try:
            # 执行备份
            backup_path = f"data/backups/messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            if self.db_manager.backup(backup_path):
                try:
                    await msg.reply(text=f"数据库备份成功: {backup_path}")
                    logger.info(f"已回复备份成功信息")
                except Exception as e:
                    logger.error(f"回复备份成功信息失败: {e}", exc_info=True)
                    # 使用消息队列发送
                    await self.message_queue.put(
                        MessageChain([Text(f"数据库备份成功: {backup_path}")]),
                        msg.user_id,
                        self.bot,
                        message_type="private",
                        priority=1
                    )
            else:
                await msg.reply(text="数据库备份失败，请查看日志")
        except Exception as e:
            logger.error(f"执行备份命令失败: {e}", exc_info=True)
            await msg.reply(text=f"备份失败: {e}")
    
    async def _handle_update_group_info_command(self, msg: PrivateMessage):
        """处理更新群信息命令"""
        # 检查权限
        if not await self._check_permission(msg, "update_group_info"):
            return
        
        try:
            await msg.reply(text="群信息更新任务已启动，请稍候...")
            
            # 创建异步任务
            asyncio.create_task(self._update_group_info(msg))
        except Exception as e:
            logger.error(f"处理更新群信息命令失败: {e}", exc_info=True)
            await msg.reply(text=f"启动群信息更新任务失败: {e}")
    
    async def _update_group_info(self, msg: PrivateMessage):
        """更新群信息"""
        try:
            # 直接从主程序获取群信息
            for group_id in self.target_groups:
                # 获取群信息
                group_info = await self.bot.api.get_group_info(group_id=group_id)
                if group_info:
                    # 检查返回的数据格式
                    if isinstance(group_info, dict):
                        # 如果返回的是包含status和data的标准格式
                        if "status" in group_info and "data" in group_info and group_info["status"] == "ok":
                            group_data = group_info["data"]
                            # 更新数据库中的群信息
                            self.db_manager.execute(
                                "INSERT OR REPLACE INTO group_info (group_id, group_name, member_count, last_update) VALUES (?, ?, ?, datetime('now'))",
                                (group_id, group_data.get("group_name", "未知"), group_data.get("member_count", 0))
                            )
                            logger.info(f"更新群 {group_id} 信息: {group_data.get('group_name', '未知')}")
                        else:
                            # 直接使用返回的字典
                            self.db_manager.execute(
                                "INSERT OR REPLACE INTO group_info (group_id, group_name, member_count, last_update) VALUES (?, ?, ?, datetime('now'))",
                                (group_id, group_info.get("group_name", "未知"), group_info.get("member_count", 0))
                            )
                            logger.info(f"更新群 {group_id} 信息: {group_info.get('group_name', '未知')}")
                    else:
                        logger.warning(f"群信息格式不是字典: {group_info}")
                    
                    # 获取群成员列表
                    try:
                        members_response = await self.bot.api.get_group_member_list(group_id=group_id)
                        logger.debug(f"获取到群成员列表响应: {members_response}")
                        
                        # 提取成员列表
                        members = []
                        if isinstance(members_response, dict):
                            # 如果返回的是包含status和data的标准格式
                            if "status" in members_response and "data" in members_response and members_response["status"] == "ok":
                                members = members_response["data"]
                            else:
                                # 可能直接返回了成员列表
                                for key, value in members_response.items():
                                    if isinstance(value, list):
                                        members = value
                                        break
                        elif isinstance(members_response, list):
                            # 直接返回了成员列表
                            members = members_response
                        
                        if members:
                            # 更新数据库中的群成员信息
                            # 先删除旧的成员信息
                            self.db_manager.execute("DELETE FROM group_members WHERE group_id = ?", (group_id,))
                            
                            # 插入新的成员信息
                            for member in members:
                                if isinstance(member, dict):
                                    self.db_manager.execute(
                                        "INSERT INTO group_members (group_id, user_id, nickname, card, role, join_time, last_update) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
                                        (
                                            group_id,
                                            member.get("user_id", 0),
                                            member.get("nickname", ""),
                                            member.get("card", ""),
                                            member.get("role", "member"),
                                            member.get("join_time", 0)
                                        )
                                    )
                                else:
                                    # 如果成员数据不是字典，尝试解析
                                    logger.warning(f"群成员数据格式不是字典: {member}")
                                    # 简单处理：只保存用户ID
                                    try:
                                        user_id = int(member)
                                        self.db_manager.execute(
                                            "INSERT INTO group_members (group_id, user_id, nickname, card, role, join_time, last_update) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))",
                                            (group_id, user_id, "", "", "member", 0)
                                        )
                                    except (ValueError, TypeError):
                                        logger.error(f"无法解析群成员数据: {member}")
                            
                            logger.info(f"更新群 {group_id} 成员 {len(members)} 人")
                        else:
                            logger.warning(f"未能提取到群成员列表: {members_response}")
                    except Exception as e:
                        logger.error(f"获取群 {group_id} 成员列表失败: {e}", exc_info=True)
            
            try:
                await msg.reply(text="群信息更新完成")
                logger.info(f"已回复群信息更新完成")
            except Exception as e:
                logger.error(f"回复群信息更新完成失败: {e}", exc_info=True)
                # 使用消息队列发送
                await self.message_queue.put(
                    MessageChain([Text("群信息更新完成")]),
                    msg.user_id,
                    self.bot,
                    message_type="private",
                    priority=1
                )
        except Exception as e:
            logger.error(f"更新群信息失败: {e}", exc_info=True)
            try:
                await msg.reply(text=f"更新群信息失败: {e}")
            except Exception as e2:
                logger.error(f"回复失败: {e2}")
    
    async def _handle_fetch_history_command(self, msg: PrivateMessage):
        """处理获取历史消息命令"""
        # 检查权限
        if not await self._check_permission(msg, "fetch_history"):
            return
        
        try:
            await msg.reply(text="历史消息获取任务已启动，请稍候...")
            
            # 创建异步任务
            asyncio.create_task(self._fetch_history_messages(msg))
        except Exception as e:
            logger.error(f"处理获取历史消息命令失败: {e}", exc_info=True)
            await msg.reply(text=f"启动历史消息获取任务失败: {e}")
    
    async def _fetch_history_messages(self, msg: PrivateMessage):
        """获取历史消息"""
        try:
            # 直接获取历史消息
            for group_id in self.target_groups:
                try:
                    # 获取最新的消息序号
                    # 先查询数据库中最新的消息序号
                    last_seq = self.db_manager.query_one(
                        "SELECT MAX(message_seq) FROM messages WHERE group_id = ?",
                        (group_id,)
                    )
                    
                    # 如果没有消息，从0开始
                    message_seq = last_seq[0] if last_seq and last_seq[0] else 0
                    
                    # 获取历史消息，每次获取20条
                    count = 20
                    # 正序获取，从旧到新
                    reverse_order = False
                    
                    # 获取历史消息
                    try:
                        history_response = await self.bot.api.get_group_msg_history(
                            group_id=group_id,
                            message_seq=message_seq,
                            count=count,
                            reverse_order=reverse_order
                        )
                        
                        logger.debug(f"获取到历史消息响应: {history_response}")
                        
                        # 提取消息列表
                        messages = []
                        if isinstance(history_response, dict):
                            # 如果返回的是包含status和data的标准格式
                            if "status" in history_response and "data" in history_response and history_response["status"] == "ok":
                                if "messages" in history_response["data"]:
                                    messages = history_response["data"]["messages"]
                                else:
                                    messages = history_response["data"]
                            elif "messages" in history_response:
                                # 直接包含messages字段
                                messages = history_response["messages"]
                        elif isinstance(history_response, list):
                            # 直接返回了消息列表
                            messages = history_response
                        else:
                            logger.warning(f"无法识别的历史消息响应格式: {type(history_response)}")
                            await msg.reply(text=f"获取历史消息失败: 无法识别的响应格式")
                            return
                        
                        if not messages:
                            logger.info(f"未获取到历史消息，可能已经获取完毕")
                            await msg.reply(text=f"未获取到新的历史消息，可能已经获取完毕")
                            return
                            
                        # 保存消息到数据库
                        count = 0
                        for message in messages:
                            if not isinstance(message, dict):
                                logger.warning(f"消息格式不是字典: {message}")
                                continue
                                
                            # 检查消息是否已存在
                            message_id = message.get("message_id", "")
                            if not message_id:
                                logger.warning(f"消息缺少ID: {message}")
                                continue
                                
                            if not self.db_manager.query_one(
                                "SELECT 1 FROM messages WHERE message_id = ?",
                                (message_id,)
                            ):
                                # 保存消息
                                try:
                                    self.db_manager.execute(
                                        """
                                        INSERT INTO messages 
                                        (message_id, group_id, user_id, message_type, content, raw_message, time, message_seq, message_data) 
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """,
                                        (
                                            message_id,
                                            message.get("group_id", group_id),  # 使用参数中的group_id作为默认值
                                            message.get("user_id", 0),
                                            message.get("message_type", ""),
                                            message.get("content", "{}"),
                                            message.get("raw_message", ""),
                                            message.get("time", 0),
                                            message.get("message_seq", 0),
                                            str(message)
                                        )
                                    )
                                    count += 1
                                except Exception as e:
                                    logger.error(f"保存消息失败: {e}, 消息: {message}", exc_info=True)
                        
                        logger.info(f"获取到群 {group_id} 历史消息 {count} 条")
                    except Exception as e:
                        logger.error(f"获取群 {group_id} 历史消息失败: {e}", exc_info=True)
                except Exception as e:
                    logger.error(f"获取群 {group_id} 历史消息失败: {e}", exc_info=True)
            
            try:
                await msg.reply(text="历史消息获取完成")
                logger.info(f"已回复历史消息获取完成")
            except Exception as e:
                logger.error(f"回复历史消息获取完成失败: {e}", exc_info=True)
                # 使用消息队列发送
                await self.message_queue.put(
                    MessageChain([Text("历史消息获取完成")]),
                    msg.user_id,
                    self.bot,
                    message_type="private",
                    priority=1
                )
        except Exception as e:
            logger.error(f"获取历史消息失败: {e}", exc_info=True)
            try:
                await msg.reply(text=f"获取历史消息失败: {e}")
            except Exception as e2:
                logger.error(f"回复失败: {e2}")
    
    async def _handle_analyze_command(self, msg: PrivateMessage):
        """处理分析命令"""
        # 检查权限
        if not await self._check_permission(msg, "analyze"):
            return
        
        # 格式: 分析 群号 [天数]
        parts = msg.raw_message.split()
        if len(parts) >= 2:
            group_id = parts[1]
            days = int(parts[2]) if len(parts) > 2 else 7
            
            if group_id in [str(g) for g in self.target_groups]:
                try:
                    await msg.reply(text=f"正在分析群 {group_id} 最近 {days} 天的数据，请稍候...")
                    
                    # 获取分析器插件
                    analyzer = None
                    for plugin in self.bot.plugin_sys.plugins.values():
                        if hasattr(plugin, "name") and plugin.name == "MessageAnalyzer":
                            analyzer = plugin
                            break
                    
                    if analyzer:
                        # 设置数据库路径
                        analyzer.database_path = self.db_manager.database_path
                        if not analyzer.db_conn:
                            analyzer.connect()
                            
                        report = analyzer.generate_report(group_id, days)
                        
                        if "error" in report:
                            await msg.reply(text=f"分析失败: {report['error']}")
                        else:
                            # 生成简单的文本报告
                            text_report = self._format_report(report)
                            try:
                                await msg.reply(text=text_report)
                                logger.info(f"已回复分析报告")
                            except Exception as e:
                                logger.error(f"回复分析报告失败: {e}", exc_info=True)
                                # 使用消息队列发送
                                await self.message_queue.put(
                                    MessageChain([Text(text_report)]),
                                    msg.user_id,
                                    self.bot,
                                    message_type="private",
                                    priority=1
                                )
                    else:
                        await msg.reply(text="分析插件未加载，无法生成报告")
                except Exception as e:
                    logger.error(f"处理分析命令失败: {e}", exc_info=True)
                    await msg.reply(text=f"分析失败: {e}")
            else:
                await msg.reply(text=f"群 {group_id} 不在监听列表中")
        else:
            await msg.reply(text="格式错误，正确格式: 分析 群号 [天数]")
    
    def _format_report(self, report):
        """格式化分析报告为文本"""
        text = f"群 {report['group_name']}({report['group_id']}) 活跃度报告\n"
        text += f"统计周期: 最近 {report['days']} 天\n"
        text += f"成员数: {report['member_count']}\n"
        text += f"消息总数: {report['message_count']}\n\n"
        
        text += "活跃用户排行:\n"
        for i, user in enumerate(report['active_users'][:5], 1):
            text += f"{i}. {user['display_name']}({user['user_id']}): {user['message_count']}条消息\n"
        
        text += "\n每日消息数:\n"
        for day in report['daily_activity'][-7:]:  # 最近7天
            text += f"{day['date']}: {day['count']}条\n"
        
        text += "\n热门关键词:\n"
        for word, count in report['keywords'][:10]:  # 前10个关键词
            text += f"{word}: {count}次\n"
        
        text += f"\n报告生成时间: {report['generated_at']}"
        return text
    
    async def _handle_plugin_list_command(self, msg: PrivateMessage):
        """处理插件列表命令"""
        try:
            logger.info("获取插件列表")
            
            # 获取已加载的插件列表
            plugins_info = []
            for plugin in self.bot.plugin_sys.plugins.values():
                if hasattr(plugin, "name") and hasattr(plugin, "version"):
                    plugins_info.append(f"{plugin.name} v{plugin.version}")
                    logger.info(f"找到插件: {plugin.name} v{plugin.version}")
            
            if plugins_info:
                reply_text = f"已加载的插件:\n" + "\n".join(plugins_info)
            else:
                reply_text = "未加载任何插件"
            
            logger.info(f"发送插件列表: {reply_text}")
            
            try:
                await msg.reply(text=reply_text)
                logger.info(f"已回复插件列表")
            except Exception as e:
                logger.error(f"回复插件列表失败: {e}", exc_info=True)
                # 使用消息队列发送
                await self.message_queue.put(
                    MessageChain([Text(reply_text)]),
                    msg.user_id,
                    self.bot,
                    message_type="private",
                    priority=1
                )
            
        except Exception as e:
            logger.error(f"处理插件列表命令失败: {e}", exc_info=True)
            try:
                await msg.reply(text=f"处理插件列表命令失败: {e}")
            except Exception as e2:
                logger.error(f"回复失败: {e2}")
    
    async def _handle_permission_command(self, msg: PrivateMessage):
        """处理权限命令"""
        # 只有拥有者和超级管理员可以使用权限命令
        user_permission = self.auth_manager.get_user_permission(str(msg.user_id))
        if user_permission < Permission(PermissionLevel.SUPER_ADMIN):
            await msg.reply(text="权限不足，无法执行该操作")
            return
        
        # 格式: 权限 [设置/查看] [用户/命令/插件] [ID] [级别]
        parts = msg.raw_message.split()
        if len(parts) < 3:
            await msg.reply(text="格式错误，正确格式: 权限 [设置/查看] [用户/命令/插件] [ID] [级别]")
            return
        
        action = parts[1]  # 设置或查看
        target_type = parts[2]  # 用户、命令或插件
        
        if action == "查看":
            if target_type == "用户" and len(parts) >= 4:
                user_id = parts[3]
                permission = self.auth_manager.get_user_permission(user_id)
                await msg.reply(text=f"用户 {user_id} 的权限级别为: {permission}")
            elif target_type == "命令" and len(parts) >= 4:
                command = parts[3]
                await msg.reply(text=f"命令 {command} 的权限级别为: {self.auth_manager.command_permissions.get(command, '未设置')}")
            elif target_type == "插件" and len(parts) >= 4:
                plugin_name = parts[3]
                await msg.reply(text=f"插件 {plugin_name} 的权限级别为: {self.auth_manager.plugin_permissions.get(plugin_name, '未设置')}")
            else:
                await msg.reply(text="格式错误，正确格式: 权限 查看 [用户/命令/插件] [ID]")
        elif action == "设置":
            if len(parts) < 5:
                await msg.reply(text="格式错误，正确格式: 权限 设置 [用户/命令/插件] [ID] [级别]")
                return
            
            target_id = parts[3]
            level_str = parts[4].upper()
            
            try:
                level = PermissionLevel[level_str]
            except KeyError:
                await msg.reply(text=f"未知的权限级别: {level_str}，可用级别: {', '.join([l.name for l in PermissionLevel])}")
                return
            
            if target_type == "用户":
                if self.auth_manager.set_user_permission(target_id, level):
                    await msg.reply(text=f"已设置用户 {target_id} 的权限级别为: {level.name}")
                else:
                    await msg.reply(text=f"设置用户 {target_id} 的权限级别失败")
            elif target_type == "命令":
                if self.auth_manager.set_command_permission(target_id, level):
                    await msg.reply(text=f"已设置命令 {target_id} 的权限级别为: {level.name}")
                else:
                    await msg.reply(text=f"设置命令 {target_id} 的权限级别失败")
            elif target_type == "插件":
                if self.auth_manager.set_plugin_permission(target_id, level):
                    await msg.reply(text=f"已设置插件 {target_id} 的权限级别为: {level.name}")
                else:
                    await msg.reply(text=f"设置插件 {target_id} 的权限级别失败")
            else:
                await msg.reply(text=f"未知的目标类型: {target_type}，可用类型: 用户, 命令, 插件")
        else:
            await msg.reply(text=f"未知的操作: {action}，可用操作: 设置, 查看")
    
    async def _handle_help_command(self, msg: PrivateMessage):
        """处理帮助命令"""
        try:
            logger.info("生成帮助信息")
            
            help_text = "可用命令:\n"
            help_text += "- 状态: 查看机器人当前状态\n"
            help_text += "- 备份: 手动触发数据库备份\n"
            help_text += "- 更新群信息: 手动更新群信息和成员列表\n"
            help_text += "- 获取历史消息: 手动获取历史消息\n"
            help_text += "- 分析 群号 [天数]: 分析指定群的活跃度\n"
            help_text += "- 插件列表: 查看已加载的插件\n"
            help_text += "- 权限 [设置/查看] [用户/命令/插件] [ID] [级别]: 管理权限\n"
            help_text += "- 帮助: 显示此帮助信息"
            
            logger.info(f"发送帮助信息: {help_text}")
            
            try:
                await msg.reply(text=help_text)
                logger.info(f"已回复帮助信息")
            except Exception as e:
                logger.error(f"回复帮助信息失败: {e}", exc_info=True)
                # 使用消息队列发送
                await self.message_queue.put(
                    MessageChain([Text(help_text)]),
                    msg.user_id,
                    self.bot,
                    message_type="private",
                    priority=1
                )
            
        except Exception as e:
            logger.error(f"处理帮助命令失败: {e}", exc_info=True)
            try:
                await msg.reply(text=f"处理帮助命令失败: {e}")
            except Exception as e2:
                logger.error(f"回复失败: {e2}")
    
    async def _check_permission(self, msg: PrivateMessage, command: str) -> bool:
        """检查用户是否有执行命令的权限"""
        user_id = str(msg.user_id)
        
        logger.info(f"检查用户 {user_id} 是否有权限执行命令 {command}")
        
        try:
            has_permission = self.auth_manager.check_command_permission(user_id, command)
        except Exception as e:
            logger.warning(f"权限检查出错，默认允许: {e}")
            has_permission = True
        
        if not has_permission:
            logger.warning(f"用户 {user_id} 权限不足，无法执行命令 {command}")
            await msg.reply(text="权限不足，无法执行该操作")
        else:
            logger.info(f"用户 {user_id} 有权限执行命令 {command}")
        
        return has_permission
    
    def register(self):
        """注册私聊消息处理函数"""
        @self.bot.private_event()
        async def on_private_message(msg: PrivateMessage):
            await self.handle(msg) 