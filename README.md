# NapcatBot

NapcatBot 是一个基于 NcatBot 框架的 QQ 群消息爬取与分析工具，支持插件扩展，可以实现群消息统计、活跃度分析等功能。

## 项目架构

项目采用模块化设计，主要包含以下部分：

### 目录结构

```
NapcatBot/
├── src/                  # 源代码目录
│   ├── core/             # 核心模块
│   │   ├── __init__.py   # 核心模块初始化文件
│   │   ├── auth.py       # 权限管理模块
│   │   ├── command_manager.py  # 命令管理模块
│   │   ├── event_manager.py    # 事件管理模块
│   │   └── plugin_manager.py   # 插件管理模块
│   └── utils/            # 工具模块
│       ├── __init__.py   # 工具模块初始化文件
│       ├── config.py     # 配置管理模块
│       ├── database.py   # 数据库模块
│       ├── logger.py     # 日志模块
│       ├── message_parser.py  # 消息解析模块
│       └── queue.py      # 消息队列模块
├── plugins/              # 插件目录
│   ├── example/          # 示例插件
│   │   └── __init__.py   # 插件入口文件
│   └── stats/            # 统计插件
│       └── __init__.py   # 插件入口文件
├── data/                 # 数据目录
│   └── database.db       # 数据库文件
├── logs/                 # 日志目录
├── config.json           # 配置文件
├── main.py               # 主程序入口
└── README.md             # 项目说明文件
```

### 核心模块

- **权限管理模块 (auth.py)**: 管理用户权限和命令权限
- **命令管理模块 (command_manager.py)**: 注册和处理命令
- **事件管理模块 (event_manager.py)**: 处理和分发事件
- **插件管理模块 (plugin_manager.py)**: 加载和管理插件

### 工具模块

- **配置管理模块 (config.py)**: 加载和管理配置文件
- **数据库模块 (database.py)**: 管理数据库连接和操作
- **日志模块 (logger.py)**: 提供日志功能
- **消息解析模块 (message_parser.py)**: 解析和处理消息
- **消息队列模块 (queue.py)**: 控制消息发送频率

### 数据库结构

NapcatBot 使用 SQLite 数据库存储数据，主要包含以下表：

#### 群信息表 (group_info)

```sql
CREATE TABLE IF NOT EXISTS group_info (
    group_id INTEGER PRIMARY KEY,
    group_name TEXT,
    member_count INTEGER,
    max_member_count INTEGER,
    owner_id INTEGER,
    admin_count INTEGER,
    last_active_time INTEGER,
    join_time INTEGER,
    created_time INTEGER
)
```

#### 群成员表 (group_members)

```sql
CREATE TABLE IF NOT EXISTS group_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id INTEGER,
    user_id INTEGER,
    nickname TEXT,
    card TEXT,
    sex TEXT,
    age INTEGER,
    area TEXT,
    join_time INTEGER,
    last_sent_time INTEGER,
    level TEXT,
    role TEXT,
    unfriendly INTEGER DEFAULT 0,
    title TEXT,
    title_expire_time INTEGER,
    card_changeable INTEGER,
    shut_up_timestamp INTEGER,
    UNIQUE(group_id, user_id),
    FOREIGN KEY(group_id) REFERENCES group_info(group_id) ON DELETE CASCADE
)
```

#### 消息表 (messages)

```sql
CREATE TABLE IF NOT EXISTS messages (
    message_id TEXT PRIMARY KEY,
    group_id INTEGER,
    user_id INTEGER,
    message_type TEXT,
    content TEXT,
    raw_message TEXT,
    time INTEGER,
    message_seq INTEGER,
    message_data TEXT,
    FOREIGN KEY(group_id) REFERENCES group_info(group_id) ON DELETE CASCADE
)
```

## 安装与配置

### 环境要求

- Python 3.8 或更高版本
- NcatBot 框架

### 安装步骤

1. 克隆仓库

```bash
git clone https://github.com/yourusername/NapcatBot.git
cd NapcatBot
```

2. 安装依赖

```bash
pip install -r requirements.txt
```

3. 创建配置文件

创建 `config.json` 文件，内容如下：

```json
{
    "bot": {
        "account": "你的QQ号",
        "password": "你的密码",
        "protocol": 2
    },
    "plugins": {
        "disabled": []
    },
    "commands": {
        "prefixes": ["/", "#"]
    },
    "database": {
        "path": "data/database.db"
    },
    "log": {
        "level": "INFO",
        "dir": "logs"
    }
}
```

## 使用方法

### 启动机器人

```bash
python main.py
```

### 命令列表

NapcatBot 内置了一些命令，可以通过在群聊或私聊中发送命令来使用：

- `/stats [天数=7]` - 查看群聊统计信息
- `/rank [天数=7] [数量=10]` - 查看群聊发言排行
- `/mystat [天数=7]` - 查看个人统计信息
- `/hello [名字]` - 打招呼命令
- `/echo <内容>` - 回显命令

## 插件开发

NapcatBot 支持插件扩展，你可以开发自己的插件来扩展功能。

### 创建插件

1. 在 `plugins` 目录下创建一个新的目录，例如 `myplugin`
2. 在该目录下创建 `__init__.py` 文件
3. 在 `__init__.py` 文件中创建一个继承自 `Plugin` 的类

```python
from ncatbot.core.plugin import Plugin
from ncatbot.core.event import Event
from ncatbot.core.message import GroupMessage, PrivateMessage
from ncatbot.core.element import MessageChain, Plain
from src.core import PermissionLevel, get_command_manager

class MyPlugin(Plugin):
    """我的插件类"""
    
    def __init__(self):
        """初始化插件"""
        super().__init__()
        self.name = "myplugin"
        self.version = "1.0.0"
        self.description = "我的插件"
        self.author = "Your Name"
        
        # 注册命令
        cmd_mgr = get_command_manager()
        cmd_mgr.register_command(
            name="mycmd",
            handler=self.cmd_mycmd,
            permission=PermissionLevel.NORMAL,
            description="我的命令",
            usage="/mycmd [参数]"
        )
        
        self.logger.info(f"插件 {self.name} v{self.version} 已加载")
    
    async def on_enable(self):
        """插件启用时调用"""
        self.logger.info(f"插件 {self.name} 已启用")
        return True
    
    async def on_disable(self):
        """插件禁用时调用"""
        self.logger.info(f"插件 {self.name} 已禁用")
        return True
    
    async def on_group_message(self, event: GroupMessage):
        """处理群消息事件"""
        # 这里可以处理所有群消息
        pass
    
    async def cmd_mycmd(self, event: Event, args: str):
        """处理 mycmd 命令"""
        await event.reply(MessageChain([Plain(f"你输入的参数是：{args}")]))
```

### 插件生命周期

- `__init__`: 插件初始化时调用
- `on_enable`: 插件启用时调用
- `on_disable`: 插件禁用时调用
- `on_group_message`: 收到群消息时调用
- `on_private_message`: 收到私聊消息时调用

### 事件处理

插件可以通过实现特定的方法来处理事件，例如：

- `on_group_message(event: GroupMessage)`: 处理群消息事件
- `on_private_message(event: PrivateMessage)`: 处理私聊消息事件
- `on_group_member_increase(event: GroupMemberIncreaseEvent)`: 处理群成员增加事件
- `on_group_member_decrease(event: GroupMemberDecreaseEvent)`: 处理群成员减少事件

### 命令注册

插件可以通过命令管理器注册命令：

```python
cmd_mgr = get_command_manager()
cmd_mgr.register_command(
    name="mycmd",
    handler=self.cmd_mycmd,
    permission=PermissionLevel.NORMAL,
    description="我的命令",
    usage="/mycmd [参数]",
    aliases=["mc"]  # 命令别名
)
```

## 常见问题

### 如何添加新的插件？

将插件目录放入 `plugins` 目录下，重启机器人即可。

### 如何禁用插件？

在配置文件中的 `plugins.disabled` 数组中添加插件名称，例如：

```json
{
    "plugins": {
        "disabled": ["example"]
    }
}
```

### 如何修改命令前缀？

在配置文件中的 `commands.prefixes` 数组中修改，例如：

```json
{
    "commands": {
        "prefixes": ["/", "#", "!"]
    }
}
```

## 贡献指南

欢迎贡献代码或提出建议，请遵循以下步骤：

1. Fork 本仓库
2. 创建你的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交你的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开一个 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件