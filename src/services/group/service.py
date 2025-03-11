"""
群组服务实现
"""
import asyncio
from typing import List, Optional, Dict

from utils.logger import get_logger
from .models import GroupModel, GroupMemberModel

logger = get_logger(__name__)

class GroupService:
    """群组服务类"""
    
    def __init__(self, bot, group_repository, target_groups):
        """初始化群组服务
        
        Args:
            bot: 机器人实例
            group_repository: 群组仓储实例
            target_groups: 目标群组列表
        """
        self.bot = bot
        self.group_repository = group_repository
        self.target_groups = target_groups
        self._group_info_cache: Dict[str, GroupModel] = {}
        self._group_members_cache: Dict[str, List[GroupMemberModel]] = {}
    
    async def get_group_list(self) -> List[GroupModel]:
        """获取群列表
        
        Returns:
            List[GroupModel]: 群组列表
        """
        try:
            response = await self.bot.api.get_group_list()
            if response and "data" in response:
                groups = response["data"]
                logger.info(f"获取到 {len(groups)} 个群")
                
                # 转换为模型对象
                return [GroupModel.from_dict(group) for group in groups]
            else:
                logger.error("获取群列表失败")
                return []
        except Exception as e:
            logger.error(f"获取群列表异常: {e}")
            return []
    
    async def get_group_info(self, group_id: int) -> Optional[GroupModel]:
        """获取群信息
        
        Args:
            group_id: 群组ID
            
        Returns:
            Optional[GroupModel]: 群组信息，如果获取失败则返回None
        """
        try:
            # 先检查缓存
            cache_key = str(group_id)
            if cache_key in self._group_info_cache:
                return self._group_info_cache[cache_key]
            
            response = await self.bot.api.get_group_info(group_id)
            if response and "data" in response:
                group_info = response["data"]
                logger.info(f"获取到群 {group_id} 信息: {group_info.get('group_name')}")
                
                # 创建群组模型
                group_model = GroupModel.from_dict(group_info)
                
                # 保存到仓储
                await self.group_repository.save_group(group_model)
                
                # 更新缓存
                self._group_info_cache[cache_key] = group_model
                
                return group_model
            else:
                logger.error(f"获取群 {group_id} 信息失败")
                return None
        except Exception as e:
            logger.error(f"获取群信息异常: {e}")
            return None
    
    async def get_group_member_list(self, group_id: int) -> List[GroupMemberModel]:
        """获取群成员列表
        
        Args:
            group_id: 群组ID
            
        Returns:
            List[GroupMemberModel]: 群成员列表
        """
        try:
            # 先检查缓存
            cache_key = str(group_id)
            if cache_key in self._group_members_cache:
                return self._group_members_cache[cache_key]
            
            response = await self.bot.api.get_group_member_list(group_id)
            if response and "data" in response:
                members = response["data"]
                logger.info(f"获取到群 {group_id} 成员 {len(members)} 人")
                
                # 转换为模型对象
                member_models = []
                for member in members:
                    member['group_id'] = group_id  # 添加群组ID
                    member_model = GroupMemberModel.from_dict(member)
                    member_models.append(member_model)
                    
                    # 保存到仓储
                    await self.group_repository.save_member(member_model)
                
                # 更新缓存
                self._group_members_cache[cache_key] = member_models
                
                return member_models
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
    
    def clear_cache(self):
        """清除缓存"""
        self._group_info_cache.clear()
        self._group_members_cache.clear()
        logger.info("群组服务缓存已清除")