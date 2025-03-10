"""
群组服务模块
"""
import asyncio
import time
from ncatbot.utils.logger import get_log

logger = get_log()

class GroupService:
    """群组服务类"""
    
    def __init__(self, bot, db, target_groups):
        """初始化群组服务"""
        self.bot = bot
        self.db = db
        self.target_groups = target_groups
        self.group_info_cache = {}
        self.group_members_cache = {}
    
    async def get_group_list(self):
        """获取群列表"""
        try:
            response = await self.bot.api.get_group_list()
            if response and "data" in response:
                groups = response["data"]
                logger.info(f"获取到 {len(groups)} 个群")
                return groups
            else:
                logger.error("获取群列表失败")
                return []
        except Exception as e:
            logger.error(f"获取群列表异常: {e}")
            return []
    
    async def get_group_info(self, group_id):
        """获取群信息"""
        try:
            response = await self.bot.api.get_group_info(group_id)
            if response and "data" in response:
                group_info = response["data"]
                logger.info(f"获取到群 {group_id} 信息: {group_info.get('group_name')}")
                
                # 保存群信息到数据库
                self.db.save_group_info(
                    group_id,
                    group_info.get("group_name"),
                    group_info.get("member_count")
                )
                
                # 更新缓存
                self.group_info_cache[str(group_id)] = group_info
                
                return group_info
            else:
                logger.error(f"获取群 {group_id} 信息失败")
                return None
        except Exception as e:
            logger.error(f"获取群信息异常: {e}")
            return None
    
    async def get_group_member_list(self, group_id):
        """获取群成员列表"""
        try:
            response = await self.bot.api.get_group_member_list(group_id)
            if response and "data" in response:
                members = response["data"]
                logger.info(f"获取到群 {group_id} 成员 {len(members)} 人")
                
                # 保存群成员信息到数据库
                for member in members:
                    self.db.save_group_member(
                        group_id,
                        member.get("user_id"),
                        member.get("nickname"),
                        member.get("card"),
                        member.get("role"),
                        member.get("join_time")
                    )
                
                # 更新缓存
                self.group_members_cache[str(group_id)] = members
                
                return members
            else:
                logger.error(f"获取群 {group_id} 成员列表失败")
                return []
        except Exception as e:
            logger.error(f"获取群成员列表异常: {e}")
            return []
    
    async def update_all_groups(self):
        """更新所有目标群的信息和成员列表"""
        for group_id in self.target_groups:
            await self.get_group_info(group_id)
            await self.get_group_member_list(group_id)
            await asyncio.sleep(1)  # 避免请求过快
    
    def update_group_info(self):
        """更新群信息（异步）"""
        import threading
        threading.Thread(target=self._update_group_info_thread).start()
    
    def _update_group_info_thread(self):
        """更新群信息的线程函数"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.update_all_groups())
        loop.close() 