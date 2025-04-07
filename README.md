# BanWords2 违禁词监控系统

BanWords2 是一个基于权值计算的违禁词监控系统，用于检测和处理群聊中的违规信息。系统会对消息内容进行扫描，当发现包含违禁词时，根据违禁词的权重累计分数，若总分超过阈值则自动处理。

## 运行机制

### 1. 权重计算系统

- 每个违禁词都有一个指定的权重值
- 当消息中包含违禁词时，对应权重会被累加到总分
- 当总分超过阈值(默认为 10 分)时，系统会自动触发处罚机制

### 2. 词库管理

- 支持全局默认违禁词库(`default.json`)
- 支持每个群独立设置的违禁词库(以群号命名的 json 文件)
- 群特定违禁词的优先级高于默认违禁词

### 3. 匹配方式

- 系统首先尝试使用正则表达式匹配
- 若正则表达式无效，则退回到普通字符串匹配

### 4. 自动处罚机制

当触发违禁词且总分超过阈值时：

1. 自动撤回触发消息
2. 对发送者实施禁言(默认 10 分钟)
3. 自动撤回该用户最近的历史消息
4. 向管理员发送私聊通知，包含：
   - 触发时间
   - 群号和用户 ID
   - 触发的违禁词列表及权重
   - 原始消息内容(Base64 编码)
   - 快捷操作命令

## 使用命令

### 群聊命令（仅管理员可用）

| 命令              | 说明                               |
| ----------------- | ---------------------------------- |
| `bw2`             | 开启/关闭 BanWords2 功能           |
| `bw2list`         | 查看当前群违禁词列表(通过私聊发送) |
| `bw2add词语 权重` | 添加违禁词，如`bw2add敏感词 5`     |
| `bw2rm词语`       | 删除违禁词，如`bw2rm敏感词`        |

### 管理员私聊命令

当系统触发后，会向管理员发送通知并提供以下快捷命令：

| 命令               | 说明                               |
| ------------------ | ---------------------------------- |
| `unban群号 用户ID` | 解除用户禁言                       |
| `t群号 用户ID`     | 将用户踢出群聊                     |
| `tl群号 用户ID`    | 将用户踢出群聊并拉黑(拒绝再次加群) |

## 数据存储

系统的所有数据存储在`data/BanWords2/`目录下：

- `default.json`：默认违禁词库
- `群号.json`：各群特定的违禁词库

每个违禁词库的格式为 JSON，键为违禁词，值为对应的权重。
