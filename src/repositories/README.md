# Repositories 仓储层

仓储层提供数据访问和持久化功能，是应用程序与数据库之间的抽象层。

## 目录结构

```
repositories/
├── base/           # 基础类
│   ├── models.py   # 基础模型
│   ├── repository.py # 基础仓储
│   ├── database.py # 数据库操作
│   └── exceptions.py # 异常定义
├── message/        # 消息相关
├── user/          # 用户相关
└── group/         # 群组相关
```

## 设计原则

1. **分层架构**
   - 基础设施与业务逻辑分离
   - 使用依赖注入管理数据库连接
   - 遵循单一职责原则

2. **错误处理**
   - 使用自定义异常层级
   - 提供详细的错误信息
   - 保留异常上下文

3. **并发控制**
   - 使用事务确保数据一致性
   - 实现乐观锁机制（TODO）
   - 处理并发访问冲突（TODO）

4. **性能优化**
   - 支持分页查询
   - 实现缓存机制（TODO）
   - 优化批量操作（TODO）

## 基础类

### BaseModel

所有模型的基类，提供基本的数据模型功能。

```python
class BaseModel:
    def __init__(self, **kwargs):
        self.id: Optional[int]
        self.created_at: datetime
        self.updated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """从字典创建模型"""
```

### BaseRepository

所有仓储的基类，提供基本的 CRUD 操作。

```python
class BaseRepository(Generic[T], ABC):
    async def create(self, model: T) -> bool:
        """创建记录"""
    
    async def update(self, id_field: str, model: T) -> bool:
        """更新记录"""
    
    async def delete(self, id_field: str, id_value: Any) -> bool:
        """删除记录"""
    
    async def get_by_id(self, id_field: str, id_value: Any) -> Optional[T]:
        """根据ID获取记录"""
    
    async def get_all(self, condition: Optional[Dict[str, Any]] = None) -> List[T]:
        """获取所有记录"""
```

## 业务仓储

### MessageRepository

提供消息相关的数据访问功能。

```python
class MessageRepository(BaseRepository[Message]):
    async def get_group_messages(
        self,
        group_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Message]:
        """获取群消息"""
    
    async def get_private_messages(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Message]:
        """获取私聊消息"""
```

### UserRepository

提供用户相关的数据访问功能。

```python
class UserRepository(BaseRepository[User]):
    async def get_user_by_qq(self, qq: str) -> Optional[User]:
        """根据QQ号获取用户"""
    
    async def get_group_members(self, group_id: str) -> List[User]:
        """获取群成员"""
```

### GroupRepository

提供群组相关的数据访问功能。

```python
class GroupRepository(BaseRepository[Group]):
    async def get_user_groups(self, user_id: str) -> List[Group]:
        """获取用户所在的群"""
    
    async def get_group_info(self, group_id: str) -> Optional[Group]:
        """获取群信息"""
```

## 最佳实践

### 1. 数据验证
- 在创建/更新记录前验证数据完整性
- 检查必填字段
- 验证数据类型和格式
- 实现业务规则验证

### 2. 错误处理
- 使用适当的异常类型
- 提供详细的错误信息
- 记录异常堆栈
- 保持异常的上下文信息

### 3. 性能优化
- 使用适当的索引
- 实现查询缓存
- 批量处理大量数据
- 优化 N+1 查询问题

### 4. 并发控制
- 使用事务保证一致性
- 实现乐观锁机制
- 处理并发冲突
- 避免长事务

### 5. 可观测性
- 记录详细的操作日志
- 实现性能监控
- 添加操作审计
- 提供调试信息

## 待改进项

1. **缓存机制**
   - 实现缓存层
   - 定义缓存策略
   - 处理缓存失效

2. **数据验证**
   - 添加输入验证
   - 实现业务规则检查
   - 提供验证错误信息

3. **并发控制**
   - 添加乐观锁
   - 实现并发控制
   - 处理死锁情况

4. **性能优化**
   - 添加批量操作接口
   - 优化查询性能
   - 实现预加载

5. **监控审计**
   - 添加性能监控
   - 实现操作审计
   - 完善日志记录

## 使用示例

```python
# 创建仓储实例
message_repo = MessageRepository(database)
user_repo = UserRepository(database)
group_repo = GroupRepository(database)

# 获取群消息
messages = await message_repo.get_group_messages(
    "123456789",
    limit=100,
    offset=0
)

# 获取用户信息
user = await user_repo.get_user_by_qq("987654321")

# 获取群信息
group = await group_repo.get_group_info("123456789")
```

## 注意事项

1. 所有数据库操作都是异步的，需要使用 `await` 调用
2. 错误处理已在基类中实现，子类可以根据需要重写
3. 建议使用类型注解以获得更好的IDE支持
4. 数据库连接由外部注入，仓储类不负责管理连接生命周期
5. 大量数据操作时注意使用分页和批量接口
6. 注意处理并发访问和事务隔离级别
7. 关注性能监控和日志记录 