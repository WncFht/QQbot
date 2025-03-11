# Core 核心模块

核心模块是 NapcatBot 的中枢系统，提供了机器人运行所需的基础设施和核心功能。

## 目录结构

```
core/
├── auth/           # 权限系统
│   ├── manager.py  # 权限管理器
│   └── permission.py # 权限定义
├── bot/            # 机器人核心
│   └── bot.py      # 机器人实现
├── command/        # 命令系统
│   ├── command.py  # 命令定义
│   └── manager.py  # 命令管理器
├── event/          # 事件系统
│   ├── bus.py      # 事件总线
│   ├── event.py    # 事件定义
│   ├── manager.py  # 事件管理器
│   └── types.py    # 事件类型
├── plugin/         # 插件系统
│   ├── base.py     # 插件基类
│   └── manager.py  # 插件管理器
└── queue/          # 消息队列
    ├── message_queue.py  # 消息队列
    └── request_queue.py  # 请求队列
```

## 核心组件

### 1. 权限系统 (auth)

权限系统负责管理和控制用户对机器人功能的访问权限。

**主要功能：**
- 权限等级管理
- 用户权限验证
- 命令权限控制
- 群组权限管理

**设计特点：**
- 基于角色的访问控制（RBAC）
- 支持权限继承
- 灵活的权限规则配置
- 实时权限更新

### 2. 机器人核心 (bot)

机器人核心模块负责协调各个子系统的工作，是整个框架的中枢。

**主要功能：**
- 生命周期管理
- 系统初始化
- 消息处理
- 异常处理

**设计特点：**
- 异步架构
- 模块化设计
- 可扩展接口
- 优雅关闭

### 3. 命令系统 (command)

命令系统处理用户输入的命令，并将其路由到相应的处理器。

**主要功能：**
- 命令注册
- 参数解析
- 命令路由
- 帮助生成

**设计特点：**
- 装饰器语法
- 类型安全
- 自动参数验证
- 灵活的命令别名

### 4. 事件系统 (event)

事件系统实现了基于发布-订阅模式的事件处理机制。

**主要功能：**
- 事件分发
- 事件过滤
- 事件优先级
- 异步处理

**设计特点：**
- 高性能事件总线
- 类型安全的事件定义
- 支持事件过滤器
- 异步事件处理

### 5. 插件系统 (plugin)

插件系统提供了可扩展的插件架构，支持动态加载和卸载插件。

**主要功能：**
- 插件生命周期管理
- 插件依赖处理
- 插件配置管理
- 插件热重载

**设计特点：**
- 基于约定的插件开发
- 自动依赖注入
- 配置热更新
- 优雅的插件隔离

### 6. 消息队列 (queue)

消息队列模块处理消息的异步传递和请求的排队处理。

**主要功能：**
- 消息缓冲
- 请求限流
- 优先级队列
- 消息过滤

**设计特点：**
- 高性能实现
- 内存安全
- 可配置的队列策略
- 支持优先级

## 接口说明

### 核心导出接口

```python
from core import (
    PermissionLevel,      # 权限级别定义
    get_plugin_manager,   # 获取插件管理器实例
    get_event_manager,    # 获取事件管理器实例
    get_command_manager,  # 获取命令管理器实例
    get_auth_manager,     # 获取权限管理器实例
)
```

### 权限系统接口

```python
from core.auth import AuthManager

# 权限检查
await auth_manager.check_permission(user_id, permission_level)

# 设置权限
await auth_manager.set_permission(user_id, permission_level)

# 获取用户权限
level = await auth_manager.get_permission_level(user_id)
```

### 事件系统接口

```python
from core.event import EventBus, Event

# 注册事件监听器
@event_bus.on('message')
async def handle_message(event: Event):
    pass

# 发布事件
await event_bus.emit('message', data={'content': 'Hello'})

# 使用事件过滤器
@event_bus.on('message', filter=lambda e: e.group_id == 123456)
async def handle_group_message(event):
    pass
```

### 插件系统接口

```python
from core.plugin import BasePlugin

class MyPlugin(BasePlugin):
    name = 'my_plugin'
    version = '1.0.0'
    description = '示例插件'
    
    async def on_load(self):
        # 插件加载时的初始化
        pass
        
    async def on_unload(self):
        # 插件卸载时的清理
        pass
        
    @command('hello')
    async def hello_command(self, ctx):
        await ctx.reply('Hello!')
```

### 命令系统接口

```python
from core.command import Command, CommandContext

# 注册命令
@command('test')
async def test_command(ctx: CommandContext):
    await ctx.reply('Test command executed!')

# 带参数的命令
@command('echo', params=['message'])
async def echo_command(ctx: CommandContext, message: str):
    await ctx.reply(f'Echo: {message}')

# 带权限检查的命令
@command('admin', permission_level=PermissionLevel.ADMIN)
async def admin_command(ctx: CommandContext):
    await ctx.reply('Admin command executed!')
```

## 最佳实践

### 1. 异步编程
- 使用 `async/await` 语法
- 避免阻塞操作
- 合理使用事件循环
- 处理异步异常

### 2. 错误处理
- 使用自定义异常
- 实现错误恢复
- 提供详细日志
- 优雅降级

### 3. 性能优化
- 使用内存缓存
- 实现请求合并
- 优化事件分发
- 控制资源使用

### 4. 可扩展性
- 遵循开闭原则
- 使用依赖注入
- 实现插件接口
- 保持向后兼容

### 5. 安全性
- 实现访问控制
- 验证用户输入
- 保护敏感数据
- 防止资源滥用

## 待改进项

1. **性能优化**
   - 实现事件批处理
   - 优化消息队列
   - 改进插件加载机制

2. **可观测性**
   - 添加性能指标
   - 完善日志系统
   - 实现分布式追踪

3. **稳定性**
   - 增强错误恢复
   - 改进内存管理
   - 添加熔断机制

4. **安全性**
   - 增强权限系统
   - 添加速率限制
   - 实现审计日志

5. **可维护性**
   - 改进文档
   - 添加单元测试
   - 规范代码风格

## 使用示例

```python
from core.bot import Bot
from core.plugin import BasePlugin
from core.event import EventBus
from core.command import CommandManager

# 创建机器人实例
bot = Bot()

# 注册事件处理器
@bot.on('message')
async def handle_message(event):
    print(f"收到消息: {event.message}")

# 注册命令
@bot.command('hello')
async def hello(ctx):
    await ctx.reply('Hello, World!')

# 创建插件
class MyPlugin(BasePlugin):
    name = 'my_plugin'
    version = '1.0.0'
    
    async def on_load(self):
        print('插件已加载')
    
    async def on_unload(self):
        print('插件已卸载')

# 运行机器人
bot.run()
```

## 注意事项

1. 所有核心组件都是异步的，需要在异步上下文中使用
2. 插件之间应该通过事件系统通信，避免直接调用
3. 注意处理异步操作中的异常
4. 合理使用权限系统控制命令访问
5. 遵循插件开发规范，确保可维护性
6. 注意资源的合理使用和释放
7. 保持良好的日志记录习惯

## 代码优化建议

### 1. 包导出优化
- 在 `__init__.py` 中补充缺失的类型导出
- 添加类型注解和文档字符串
- 规范化导出接口命名

### 2. 重复代码消除
- 将通用的日志记录逻辑抽取到基类
- 统一错误处理机制
- 创建共享的工具函数库

### 3. 类型系统完善
- 为所有公共接口添加类型注解
- 使用 Protocol 定义接口契约
- 添加运行时类型检查

### 4. 异步优化
- 使用连接池管理数据库连接
- 实现批量事件处理
- 优化异步队列实现

### 5. 测试改进
- 添加单元测试用例
- 实现集成测试
- 添加性能基准测试 