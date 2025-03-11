---
title: NcatBot API 文档
createTime: 2023/07/15 15:30:00
permalink: /guide/api-docs/
---

# NcatBot API 文档

## 1. API 调用基础

NcatBot 提供**异步**的 API 调用，用于完成各种操作。提供 API 的类是 `BotAPI`，`BotClient` 类的成员 `api`（即示例代码中的 `bot.api`）是一个 `BotAPI` 实例。

### 1.1 在回调函数中调用 API

在回调函数中，调用 `bot.api` 的成员方法即可完成回复：

```python
@bot.private_event()
async def on_private_message(msg: PrivateMessage):
    if msg.raw_message == '测试':
        await bot.api.post_private_msg(msg.user_id, text="NcatBot 测试成功喵~")
```

### 1.2 快速回复

`GroupMessage` 和 `PrivateMessage` 类型事件定义了 `reply()` 方法，可以通过 `msg.reply()` 方法快速回复：

```python
@bot.group_event()
async def on_group_message(msg: GroupMessage):
    if msg.raw_message == '测试':
        await msg.reply('NcatBot 测试成功喵~')
```

### 1.3 在插件中调用 API

在插件中，API 通过 `self.api` 调用：

```python
class MyPlugin(BasePlugin):
    @bot.group_event()
    async def on_group_event(self, msg: GroupMessage):
        if msg.raw_message == "测试":
            await self.api.post_group_msg(msg.group_id, text="Ncatbot 插件测试成功喵")
```

## 2. 消息构造

NcatBot 支持两种消息构造方式：使用 MessageChain 和使用命名参数。

### 2.1 消息发送函数

能够发送消息的函数一共有四个：

- `BotAPI.post_group_msg()`：发送群消息
- `BotAPI.post_private_msg()`：发送私聊消息
- `GroupMessage.reply()`：回复群消息
- `PrivateMessage.reply()`：回复私聊消息

它们都支持"MessageChain"和"命名参数"两种格式的消息。

### 2.2 使用 MessageChain 构造消息（推荐）

MessageChain 是一种组合多个消息元素的方式，类似于 mirai 的消息链。

#### 导入相关类

```python
from ncatbot.core.element import (
    MessageChain,  # 消息链，用于组合多个消息元素
    Text,          # 文本消息
    Reply,         # 回复消息
    At,            # @某人
    AtAll,         # @全体成员
    Dice,          # 骰子
    Face,          # QQ表情
    Image,         # 图片
    Json,          # JSON消息
    Music,         # 音乐分享 (网易云, QQ 音乐等)
    CustomMusic,   # 自定义音乐分享
    Record,        # 语音
    Rps,           # 猜拳
    Video,         # 视频
    File,          # 文件
)
```

#### 构造消息链

```python
# 构造消息链
message = MessageChain([
    "喵喵喵~",
    Text("你好"),
    At(123456),
    Image("meow.jpg"),
    [
        Face(123),
        Image("https://example.com/meow.jpg"),
        Reply(13579),
    ]
])
message += MessageChain(["咕咕咕"])
message = message + At(234567)
await bot.api.post_group_msg(group_id=123456, rtf=message)
```

MessageChain 的主要用法：
- 列表化构造：构造时传入一个列表，列表中的元素是列表或者 Element 类（列表至多嵌套一层）
- 通过 `+` 运算符连接：`MessageChain` 对可发送对象均可右加
- 单纯文本可以不使用 `Element` 类，直接传入字符串即可

*可发送对象: `MessageChain`, `Element`, `str`*

#### 消息元素构造

- `Text(str)`：文本消息
- `Reply(message_id)`：回复消息，多条 `Reply` 只生效第一条
- `At(qq_id)`：@ 某人
- `AtAll()`：@ 全体成员
- `Dice()`：骰子
- `Face(face_id)`：QQ 表情
- `Image(str)`：图片，支持本地路径（推荐绝对路径）、URL、Base64 编码
- `Json(json_str)`：JSON 消息
- `Music(type, id)`：音乐分享，type 为平台类型（qq/163/kugou/migu/kuwo），id 为音乐 ID
- `CustomMusic(dict)`：自定义音乐，需包含 url（跳转链接）、audio（音频链接）、title（标题）等字段
- `Record(str)`：语音
- `Rps()`：猜拳
- `Video(str)`：视频，支持本地路径（推荐绝对路径）和 URL
- `File(str)`：文件，支持本地路径（推荐绝对路径）

#### 发送消息链

```python
await bot.api.post_group_msg(group_id=123456, rtf=message)
await msg.reply(rtf=message)
```

### 2.3 使用命名参数构造消息

命名参数构造消息更适合简单的消息发送：

```python
await bot.api.post_group_msg(group_id=123456, text="喵喵喵~", reply=13579)
await msg.reply(face=123, at=1234567)
```

可用的命名参数：
- `text: str`：文本消息
- `face: int`：QQ 表情
- `json: str`：JSON 消息
- `markdown: str`：Markdown 消息
- `at: Union[int, str]`：@ 某人
- `reply: Union[int, str]`：回复消息
- `music: Union[list, dict]`：音乐分享
- `dice: bool`：骰子
- `rps: bool`：猜拳
- `image: str`：图片

命名参数构造的消息不区分顺序，一般只使用 `at` 消息和至多一个其它类型。

### 2.4 使用建议

- 无复杂顺序组合的文本采用普通参数发送
- 有复杂顺序组合的消息采用消息链发送

示例：
- `bot.api.post_group_msg(123456789, "你好")`：发送一句 "你好"
- `bot.api.post_group_msg(123456789, "你好呀", at=123456)`：发送一句 "你好呀" 并 @ QQ 号为 123456 的用户
- `bot.api.post_group_msg(123456789, "你好呀", reply=13579)`：向 id 为 13579 的消息回复 "你好呀"
- `bot.api.post_group_msg(123456789, rtf=MessageChain([Text("你好")]))`：发送一条消息链

## 3. API 列表

### 3.1 重要接口

#### 发送私聊/群聊合并转发消息

```python
async def send_private_forward_msg(self, user_id: Union[int, str], messages: list[str])
async def send_group_forward_msg(self, group_id: Union[int, str], messages: list[str])
```

- `user_id`：发送目标 QQ 号
- `group_id`：发送目标群号
- `messages`：消息 id 构成的列表

示例：`bot.api.send_private_forward_msg(123456789, ["123456789", "987654321"])`

### 3.2 消息接口

#### 发送群消息/私聊消息

```python
async def post_group_msg(
    self,
    group_id: Union[int, str],
    text: str = None,
    face: int = None,
    json: str = None,
    markdown: str = None,
    at: Union[int, str] = None,
    reply: Union[int, str] = None,
    music: Union[list, dict] = None,
    dice: bool = False,
    rps: bool = False,
    image: str = None,
    rtf: MessageChain = None,
)

async def post_private_msg(
    self,
    user_id: Union[int, str],
    text: str = None,
    face: int = None,
    json: str = None,
    markdown: str = None,
    reply: Union[int, str] = None,
    music: Union[list, dict] = None,
    dice: bool = False,
    rps: bool = False,
    image: str = None,
    rtf: MessageChain = None,
)
```

#### 设置消息已读

```python
async def mark_msg_as_read(self, group_id: Union[int, str] = None, user_id: Union[int, str] = None)
async def mark_group_msg_as_read(self, group_id: Union[int, str])
async def mark_private_msg_as_read(self, user_id: Union[int, str])
async def mark_all_as_read(self)
```

#### 消息操作

```python
async def delete_msg(self, message_id: Union[int, str])
async def get_msg(self, message_id: Union[int, str])
async def get_forward_msg(self, message_id: str)
```

#### 多媒体消息

```python
async def get_image(self, image_id: str)
async def get_record(self, record_id: str, output_type: str = "mp3")
async def get_file(self, file_id: str)
```

#### 消息历史

```python
async def get_group_msg_history(
    self,
    group_id: Union[int, str],
    message_seq: Union[int, str],
    count: int,
    reverse_order: bool,
)

async def get_friend_msg_history(
    self,
    user_id: Union[int, str],
    message_seq: Union[int, str],
    count: int,
    reverse_order: bool,
)
```

### 3.3 用户接口

#### 用户信息

```python
async def set_qq_profile(self, nickname: str, personal_note: str, sex: str)
async def get_user_card(self, user_id: int, phone_number: str)
async def set_qq_avatar(self, avatar: str)
async def set_self_long_nick(self, longnick: str)
async def get_stranger_info(self, user_id: Union[int, str])
```

#### 好友操作

```python
async def get_friends_with_category(self)
async def get_friend_list(self, cache: bool)
async def set_friend_add_request(self, flag: str, approve: bool, remark: str)
async def delete_friend(
    self,
    user_id: Union[int, str],
    friend_id: Union[int, str],
    temp_block: bool,
    temp_both_del: bool,
)
```

#### 其他用户操作

```python
async def set_online_status(self, status: str)
async def send_like(self, user_id: str, times: int)
async def create_collection(self, rawdata: str, brief: str)
async def get_profile_like(self)
async def fetch_custom_face(self, count: int)
async def upload_private_file(self, user_id: Union[int, str], file: str, name: str)
async def nc_get_user_status(self, user_id: Union[int, str])
```

### 3.4 群组接口

#### 群管理

```python
async def set_group_kick(
    self,
    group_id: Union[int, str],
    user_id: Union[int, str],
    reject_add_request: bool = False,
)

async def set_group_ban(
    self, group_id: Union[int, str], user_id: Union[int, str], duration: int
)

async def set_group_whole_ban(self, group_id: Union[int, str], enable: bool)

async def set_group_admin(
    self, group_id: Union[int, str], user_id: Union[int, str], enable: bool
)

async def set_group_card(
    self, group_id: Union[int, str], user_id: Union[int, str], card: str
)

async def set_group_name(self, group_id: Union[int, str], group_name: str)

async def set_group_leave(self, group_id: Union[int, str])

async def set_group_special_title(
    self, group_id: Union[int, str], user_id: Union[int, str], special_title: str
)
```

#### 群信息

```python
async def get_group_info(self, group_id: Union[int, str])
async def get_group_info_ex(self, group_id: Union[int, str])
async def get_group_list(self, no_cache: bool = False)
async def get_group_member_info(
    self, group_id: Union[int, str], user_id: Union[int, str], no_cache: bool
)
async def get_group_member_list(
    self, group_id: Union[int, str], no_cache: bool = False
)
async def get_group_honor_info(self, group_id: Union[int, str])
async def get_group_at_all_remain(self, group_id: Union[int, str])
```

#### 群公告

```python
async def send_group_notice(
    self, group_id: Union[int, str], content: str, image: str = None
)
async def get_group_notice(self, group_id: Union[int, str])
async def del_group_notice(self, group_id: Union[int, str], notice_id: str)
```

#### 群文件

```python
async def upload_group_file(
    self, group_id: Union[int, str], file: str, name: str, folder_id: str
)
async def create_group_file_folder(
    self, group_id: Union[int, str], folder_name: str
)
async def delete_group_file(self, group_id: Union[int, str], file_id: str)
async def delete_group_folder(self, group_id: Union[int, str], folder_id: str)
async def get_group_file_system_info(self, group_id: Union[int, str])
async def get_group_root_files(self, group_id: Union[int, str])
async def get_group_files_by_folder(
    self, group_id: Union[int, str], folder_id: str, file_count: int
)
async def get_group_file_url(self, group_id: Union[int, str], file_id: str)
```

#### 群其他功能

```python
async def set_essence_msg(self, message_id: Union[int, str])
async def delete_essence_msg(self, message_id: Union[int, str])
async def get_essence_msg_list(self, group_id: Union[int, str])
async def set_group_add_request(self, flag: str, approve: bool, reason: str = None)
async def set_group_sign(self, group_id: Union[int, str])
async def send_group_sign(self, group_id: Union[int, str])
```

### 3.5 系统接口

```python
async def get_login_info(self)
async def get_client_key(self)
async def get_robot_uin_range(self)
async def ocr_image(self, image: str)
async def translate_en2zh(self, words: list)
async def set_input_status(self, event_type: int, user_id: Union[int, str])
async def download_file(
    self,
    thread_count: int,
    headers: Union[dict, str],
    base64: str = None,
    url: str = None,
    name: str = None,
)
async def get_cookies(self, domain: str)
async def get_csrf_token(self)
async def get_credentials(self, domain: str)
async def can_send_image(self)
async def can_send_record(self)
async def get_status(self)
async def get_version_info(self)
```

## 4. 实践示例

### 4.1 捕获指定群聊的指定消息内容，并发送消息

```python
from ncatbot.core import BotClient
from ncatbot.core.message import GroupMessage

bot = BotClient()

@bot.group_event()
async def on_group_message(msg:GroupMessage):
    group_uin = 12345678  # 指定群聊的账号
    if msg.group_id == group_uin and msg.raw_message == "你好":
        await bot.api.post_group_msg(msg.group_id, text="你好呀，有什么需要我帮忙的吗？")

bot.run()
```

### 4.2 捕获指定群聊的指定用户的指定信息，并进行图片回复

```python
from ncatbot.core import BotClient
from ncatbot.core.message import GroupMessage

bot = BotClient()

@bot.group_event()
async def on_group_message(msg:GroupMessage):
    group_uin = 12345678  # 指定群聊的账号
    user_uin = 987654321  # 指定用户的账号
    if msg.group_id == group_uin and msg.user_id == user_uin and msg.raw_message == "你好":
        await bot.api.post_group_file(group_id=group_uin, image="https://example.com/image.png")  # 文件路径支持本地绝对路径，相对路径，网址以及base64

bot.run()
```

### 4.3 使用消息链发送复杂消息

```python
from ncatbot.core import BotClient
from ncatbot.core.message import GroupMessage
from ncatbot.core.element import MessageChain, Text, At, Image, Face

bot = BotClient()

@bot.group_event()
async def on_group_message(msg:GroupMessage):
    if msg.raw_message == "复杂消息":
        message = MessageChain([
            "这是一条复杂消息：\n",
            At(msg.user_id),  # @发送者
            Text(" 你好！\n"),
            Face(123),  # 添加表情
            Image("https://example.com/image.png")  # 添加图片
        ])
        await msg.reply(rtf=message)

bot.run()
```

## 总结

NcatBot 提供了丰富的 API 接口，支持消息发送、群管理、用户操作等多种功能。通过异步调用这些 API，可以实现各种复杂的机器人功能。消息构造支持 MessageChain 和命名参数两种方式，可以根据需求选择合适的方式。

在实际开发中，建议先熟悉基本的 API 调用方式，然后逐步探索更复杂的功能。对于复杂的消息构造，推荐使用 MessageChain；对于简单的消息发送，可以直接使用命名参数。 