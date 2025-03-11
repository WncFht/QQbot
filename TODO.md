# NapcatBot 插件化分层架构设计

本文档详细描述了 NapcatBot 项目的插件化分层架构设计，包括各个模块的功能、职责以及实现细节。

## 1. 整体架构

```
NapcatBot/
├── src/                  # 源代码目录
│   ├── core/             # 核心框架
│   │   ├── bot/          # 机器人核心
│   │   ├── plugin/       # 插件系统
│   │   ├── event/        # 事件系统
│   │   ├── command/      # 命令系统
│   │   └── auth/         # 权限系统
│   ├── services/         # 服务层
│   │   ├── message/      # 消息服务
│   │   ├── user/         # 用户服务
│   │   ├── group/        # 群组服务
│   │   └── stats/        # 统计服务
│   ├── repositories/     # 数据访问层
│   │   ├── message/      # 消息仓储
│   │   ├── user/         # 用户仓储
│   │   ├── group/        # 群组仓储
│   │   └── base/         # 基础仓储
│   ├── api/              # API接口层
│   │   ├── rest/         # REST API
│   │   └── websocket/    # WebSocket API
│   └── utils/            # 工具模块
│       ├── config/       # 配置工具
│       ├── database/     # 数据库工具
│       ├── logger/       # 日志工具
│       ├── http/         # HTTP客户端
│       └── parser/       # 解析工具
├── plugins/              # 插件目录（保持在根目录）
│   ├── base/             # 插件基类
│   └── [plugin_folders]/ # 各插件目录
├── config/               # 配置文件目录
│   ├── default.json      # 默认配置
│   ├── development.json  # 开发环境配置
│   └── production.json   # 生产环境配置
├── data/                 # 数据目录
│   ├── database.db       # 主数据库文件
│   └── plugins/          # 插件数据目录
├── logs/                 # 日志目录
│   ├── app.log           # 应用日志
│   └── plugins/          # 插件日志目录
├── tests/                # 测试目录
├── docs/                 # 文档目录
└── main.py               # 主程序入口
```

## 2. 核心框架层 (Core)

核心框架层是整个系统的基础，提供了插件系统、事件系统、命令系统和权限系统等核心功能。

### 2.1 机器人核心 (Bot)

**功能**：
- 初始化和管理机器人实例
- 处理机器人生命周期
- 连接和管理与QQ平台的通信

**需要实现的文件**：
- `src/core/bot/__init__.py`：模块初始化
- `src/core/bot/bot.py`：机器人核心类
- `src/core/bot/client.py`：QQ客户端接口

### 2.2 插件系统 (Plugin)

**功能**：
- 插件加载、卸载和管理
- 插件依赖解析
- 插件生命周期管理

**需要实现的文件**：
- `src/core/plugin/__init__.py`：模块初始化
- `src/core/plugin/manager.py`：插件管理器
- `src/core/plugin/base.py`：插件基类
- `src/core/plugin/loader.py`：插件加载器

### 2.3 事件系统 (Event)

**功能**：
- 事件定义和管理
- 事件分发和处理
- 事件总线实现

**需要实现的文件**：
- `src/core/event/__init__.py`：模块初始化
- `src/core/event/bus.py`：事件总线
- `src/core/event/handler.py`：事件处理器
- `src/core/event/types.py`：事件类型定义

### 2.4 命令系统 (Command)

**功能**：
- 命令注册和管理
- 命令解析和执行
- 命令帮助生成

**需要实现的文件**：
- `src/core/command/__init__.py`：模块初始化
- `src/core/command/manager.py`：命令管理器
- `src/core/command/parser.py`：命令解析器
- `src/core/command/handler.py`：命令处理器

### 2.5 权限系统 (Auth)

**功能**：
- 用户权限管理
- 权限检查和验证
- 角色定义和管理

**需要实现的文件**：
- `src/core/auth/__init__.py`：模块初始化
- `src/core/auth/manager.py`：权限管理器
- `src/core/auth/permission.py`：权限定义
- `src/core/auth/role.py`：角色定义

## 3. 服务层 (Services)

服务层负责实现业务逻辑，是连接核心层和数据访问层的桥梁。

### 3.1 消息服务 (Message)

**功能**：
- 消息处理和分发
- 消息格式化和转换
- 消息发送和接收

**需要实现的文件**：
- `src/services/message/__init__.py`：模块初始化
- `src/services/message/service.py`：消息服务类
- `src/services/message/formatter.py`：消息格式化器

### 3.2 用户服务 (User)

**功能**：
- 用户信息管理
- 用户行为分析
- 用户权限处理

**需要实现的文件**：
- `src/services/user/__init__.py`：模块初始化
- `src/services/user/service.py`：用户服务类
- `src/services/user/analyzer.py`：用户行为分析器

### 3.3 群组服务 (Group)

**功能**：
- 群组信息管理
- 群组成员管理
- 群组活跃度分析

**需要实现的文件**：
- `src/services/group/__init__.py`：模块初始化
- `src/services/group/service.py`：群组服务类
- `src/services/group/analyzer.py`：群组活跃度分析器

### 3.4 统计服务 (Stats)

**功能**：
- 消息统计分析
- 活跃度计算
- 报表生成

**需要实现的文件**：
- `src/services/stats/__init__.py`：模块初始化
- `src/services/stats/service.py`：统计服务类
- `src/services/stats/analyzer.py`：数据分析器
- `src/services/stats/reporter.py`：报表生成器

## 4. 数据访问层 (Repositories)

数据访问层负责与数据库交互，提供数据的增删改查操作。

### 4.1 基础仓储 (Base)

**功能**：
- 定义仓储接口
- 实现基础CRUD操作
- 提供事务支持

**需要实现的文件**：
- `src/repositories/base/__init__.py`：模块初始化
- `src/repositories/base/repository.py`：基础仓储类
- `src/repositories/base/transaction.py`：事务管理

### 4.2 消息仓储 (Message)

**功能**：
- 消息存储和检索
- 消息统计查询
- 消息历史管理

**需要实现的文件**：
- `src/repositories/message/__init__.py`：模块初始化
- `src/repositories/message/repository.py`：消息仓储类
- `src/repositories/message/models.py`：消息数据模型

### 4.3 用户仓储 (User)

**功能**：
- 用户信息存储和检索
- 用户行为记录
- 用户统计查询

**需要实现的文件**：
- `src/repositories/user/__init__.py`：模块初始化
- `src/repositories/user/repository.py`：用户仓储类
- `src/repositories/user/models.py`：用户数据模型

### 4.4 群组仓储 (Group)

**功能**：
- 群组信息存储和检索
- 群组成员管理
- 群组统计查询

**需要实现的文件**：
- `src/repositories/group/__init__.py`：模块初始化
- `src/repositories/group/repository.py`：群组仓储类
- `src/repositories/group/models.py`：群组数据模型

## 5. API接口层 (API)

API接口层提供了与外部系统交互的接口，作为核心系统的一部分。

### 5.1 REST API

**功能**：
- 提供RESTful API接口
- 处理HTTP请求和响应
- 实现API认证和授权

**需要实现的文件**：
- `src/api/rest/__init__.py`：模块初始化
- `src/api/rest/server.py`：REST服务器
- `src/api/rest/routes/`：API路由目录

### 5.2 WebSocket API

**功能**：
- 提供WebSocket实时通信
- 处理连接和消息
- 实现事件推送

**需要实现的文件**：
- `src/api/websocket/__init__.py`：模块初始化
- `src/api/websocket/server.py`：WebSocket服务器
- `src/api/websocket/handlers/`：WebSocket处理器目录

## 6. 工具模块 (Utils)

工具模块提供各种通用功能，供其他模块使用。

### 6.1 配置工具 (Config)

**功能**：
- 配置文件加载和解析
- 配置项管理
- 配置热更新

**需要实现的文件**：
- `src/utils/config/__init__.py`：模块初始化
- `src/utils/config/manager.py`：配置管理器
- `src/utils/config/loader.py`：配置加载器

**配置管理方案**：
- 使用JSON或YAML格式的配置文件，存放在根目录的`config`文件夹中
- 支持分层配置：默认配置、环境配置、用户配置
- 支持环境变量覆盖配置项，便于容器化部署
- 实现配置热更新，无需重启即可应用新配置
- 提供统一的配置访问接口，如`config.get('bot.uin')`
- 支持类型转换和默认值，如`config.get_int('server.port', 8080)`
- 支持配置变更通知，当配置变更时通知相关组件

### 6.2 数据库工具 (Database)

**功能**：
- 数据库连接管理
- SQL执行和查询
- 数据库迁移和备份

**需要实现的文件**：
- `src/utils/database/__init__.py`：模块初始化
- `src/utils/database/connection.py`：数据库连接管理
- `src/utils/database/migration.py`：数据库迁移工具
- `src/utils/database/backup.py`：数据库备份工具

### 6.3 日志工具 (Logger)

**功能**：
- 日志记录和管理
- 日志级别控制
- 日志文件轮转

**需要实现的文件**：
- `src/utils/logger/__init__.py`：模块初始化
- `src/utils/logger/manager.py`：日志管理器
- `src/utils/logger/formatter.py`：日志格式化器

### 6.4 HTTP客户端 (HTTP)

**功能**：
- HTTP请求发送和接收
- 请求重试和超时处理
- 响应解析

**需要实现的文件**：
- `src/utils/http/__init__.py`：模块初始化
- `src/utils/http/client.py`：HTTP客户端
- `src/utils/http/response.py`：响应处理器

### 6.5 解析工具 (Parser)

**功能**：
- 消息解析
- 命令解析
- 数据格式转换

**需要实现的文件**：
- `src/utils/parser/__init__.py`：模块初始化
- `src/utils/parser/message.py`：消息解析器
- `src/utils/parser/command.py`：命令解析器
- `src/utils/parser/converter.py`：数据转换器

## 7. 插件系统 (Plugins)

插件系统是NapcatBot的核心特性，允许通过插件扩展功能。插件保持在根目录下，强调其独立性和可扩展性。

### 7.1 插件基类 (Base)

**功能**：
- 定义插件接口
- 提供插件生命周期方法
- 实现插件通用功能

**需要实现的文件**：
- `plugins/base/__init__.py`：模块初始化
- `plugins/base/plugin.py`：插件基类

### 7.2 插件开发规范

每个插件应遵循以下结构：

```
plugins/my_plugin/
├── __init__.py          # 插件入口
├── plugin.py            # 插件主类
├── handlers/            # 事件处理器
├── commands/            # 命令处理器
├── utils/               # 插件工具函数
└── requirements.txt     # 插件依赖
```

**插件入口文件 (`__init__.py`) 示例**：

```python
"""
我的插件 - 插件描述
"""
from .plugin import MyPlugin

# 导出插件类
__all__ = ["MyPlugin"]

# 初始化插件实例
def init_plugin(event_bus, **kwargs):
    """初始化插件
    
    Args:
        event_bus: 事件总线
        **kwargs: 其他参数
        
    Returns:
        MyPlugin: 插件实例
    """
    return MyPlugin(event_bus=event_bus, **kwargs)
```

**插件主类 (`plugin.py`) 示例**：

```python
"""
我的插件主类
"""
from plugins.base import BasePlugin

class MyPlugin(BasePlugin):
    """我的插件类"""
    
    # 插件信息
    name = "MyPlugin"
    version = "1.0.0"
    
    # 插件依赖
    dependencies = {}
    
    # 元数据
    meta_data = {
        "description": "我的插件描述",
        "author": "作者名"
    }
    
    def __init__(self, event_bus=None, **kwargs):
        """初始化插件"""
        super().__init__(event_bus, **kwargs)
        # 初始化代码
        
    async def on_load(self):
        """插件加载时调用"""
        self.logger.info(f"插件 {self.name} 已加载")
        return True
        
    async def on_unload(self):
        """插件卸载时调用"""
        self.logger.info(f"插件 {self.name} 已卸载")
        return True
```

## 8. 数据和日志管理

### 8.1 数据目录结构

数据文件位于项目根目录下的`data`文件夹中，结构如下：

```
data/
├── database.db          # 主数据库文件
├── backups/             # 数据库备份目录
│   └── database_20230101_120000.db  # 备份文件示例
└── plugins/             # 插件数据目录
    ├── plugin1/         # 插件1的数据目录
    └── plugin2/         # 插件2的数据目录
```

**数据管理策略**：
- 主数据库文件存储在`data/database.db`
- 每个插件可以在`data/plugins/{plugin_name}/`目录下存储自己的数据
- 数据库定期备份到`data/backups/`目录
- 备份文件命名格式为`database_YYYYMMDD_HHMMSS.db`
- 自动清理过期备份，默认保留最近10个备份

### 8.2 日志目录结构

日志文件位于项目根目录下的`logs`文件夹中，结构如下：

```
logs/
├── app.log              # 主应用日志
├── error.log            # 错误日志
├── access.log           # 访问日志
└── plugins/             # 插件日志目录
    ├── plugin1.log      # 插件1的日志
    └── plugin2.log      # 插件2的日志
```

**日志管理策略**：
- 使用分级日志系统，支持DEBUG、INFO、WARNING、ERROR、CRITICAL五个级别
- 日志文件自动轮转，默认单个日志文件最大10MB，保留5个历史文件
- 主应用日志记录系统级别的信息
- 错误日志专门记录WARNING及以上级别的信息
- 访问日志记录API访问信息
- 每个插件有自己的日志文件，位于`logs/plugins/{plugin_name}.log`
- 提供日志查看和分析工具

## 9. 配置管理

### 9.1 配置文件结构

配置文件位于根目录的`config`文件夹中，采用JSON或YAML格式：

```
config/
├── default.json         # 默认配置
├── development.json     # 开发环境配置
├── production.json      # 生产环境配置
└── local.json           # 本地配置（不纳入版本控制）
```

### 9.2 配置项示例

```json
{
  "bot": {
    "uin": "123456789",
    "protocol": 2,
    "auto_reconnect": true
  },
  "server": {
    "ws_uri": "ws://localhost:3001",
    "token": "",
    "timeout": 30
  },
  "database": {
    "type": "sqlite",
    "path": "data/database.db",
    "backup_interval": 86400,
    "max_backups": 10
  },
  "log": {
    "level": "INFO",
    "dir": "logs",
    "max_size": 10485760,
    "backup_count": 5
  },
  "plugins": {
    "disabled": [],
    "data_dir": "data/plugins"
  }
}
```

### 9.3 配置访问接口

```python
# 获取配置项
bot_uin = config.get('bot.uin')
log_level = config.get('log.level', 'INFO')  # 提供默认值

# 类型转换
port = config.get_int('server.port', 8080)
auto_reconnect = config.get_bool('bot.auto_reconnect', True)

# 监听配置变更
@config.on_change('log.level')
def log_level_changed(new_value):
    logger.set_level(new_value)
```

## 10. 重构计划

### 10.1 第一阶段：核心框架重构

1. 重构核心框架层
   - 实现插件系统
   - 实现事件系统
   - 实现命令系统
   - 实现权限系统

2. 重构工具模块
   - 实现配置工具
   - 实现数据库工具
   - 实现日志工具
   - 实现解析工具

### 10.2 第二阶段：服务层和数据访问层重构

1. 重构数据访问层
   - 实现基础仓储
   - 实现消息仓储
   - 实现用户仓储
   - 实现群组仓储

2. 重构服务层
   - 实现消息服务
   - 实现用户服务
   - 实现群组服务
   - 实现统计服务

### 10.3 第三阶段：API接口层和插件系统重构

1. 实现API接口层
   - 实现REST API
   - 实现WebSocket API

2. 重构插件系统
   - 实现插件基类
   - 迁移现有插件
   - 开发新插件

### 10.4 第四阶段：测试和优化

1. 编写单元测试
2. 进行集成测试
3. 性能优化
4. 文档完善

## 11. 设计原则

在重构过程中，应遵循以下设计原则：

1. **单一职责原则**：每个类只负责一项职责
2. **开闭原则**：对扩展开放，对修改关闭
3. **依赖倒置原则**：高层模块不应依赖低层模块，两者都应依赖抽象
4. **接口隔离原则**：客户端不应依赖它不需要的接口
5. **组合优于继承**：优先使用组合而非继承来实现功能复用

## 12. 技术栈

- **编程语言**：Python 3.8+
- **数据库**：SQLite（可扩展支持MySQL、PostgreSQL）
- **Web框架**：FastAPI（用于API接口）
- **异步框架**：asyncio
- **测试框架**：pytest
- **文档工具**：Sphinx

## 13. 注意事项

1. 保持向后兼容性，确保现有插件能够平滑迁移
2. 提供详细的文档和示例，方便开发者理解和使用
3. 实现完善的错误处理和日志记录，便于问题排查
4. 考虑性能和资源消耗，避免不必要的开销
5. 遵循Python编码规范（PEP 8），保持代码风格一致
6. 插件目录保持在根目录，便于用户和开发者管理
7. 配置文件集中管理，支持多环境配置
8. 数据和日志文件放在根目录下的专用文件夹中，便于访问和管理
9. 实现自动备份和清理机制，避免数据丢失和磁盘空间耗尽
