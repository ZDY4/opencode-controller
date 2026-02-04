# OpenCode Controller Skill - 开发总结

**开发时间：** 2026-02-04  
**状态：** ✅ 完成并推送到 GitHub

---

## 🎯 项目回顾

### 核心目标
让 OpenClaw 能够通过 HTTP API 控制 OpenCode，解决 Windows 上 `opencode run` 卡住的问题。

### 最终成果
- ✅ 完整的 PowerShell 控制脚本
- ✅ 经过充分测试的 API 封装
- ✅ 详细文档（SKILL.md, README.md, TEST_LOG.md）
- ✅ GitHub 开源发布

---

## 🔧 技术挑战与解决方案

### 挑战 1：PowerShell 变量冲突
**问题：** `$Host` 是 PowerShell 保留变量，导致冲突

**解决：**
```powershell
# ❌ 错误
$controller = @{ Host = $Host; ... }

# ✅ 正确
$controller = @{ ServerHost = $ServerHost; ... }
```

**经验：** 避免使用 `$Host`, `$PSScriptRoot` 等保留变量名

---

### 挑战 2：启动 npm 脚本
**问题：** `Start-Process -FilePath "opencode"` 无法启动，因为 opencode 是 .ps1 脚本

**解决：**
```powershell
# ❌ 错误 - 无法直接启动 npm 脚本
Start-Process -FilePath "opencode" -ArgumentList "serve"

# ✅ 正确 - 使用 cmd 作为中介
Start-Process -FilePath "cmd" `
    -ArgumentList "/c", "opencode serve --port $Port" `
    -WorkingDirectory $WorkingDir
```

**经验：** Windows 上的 npm 全局命令需要通过 cmd 调用

---

### 挑战 3：GET 请求带 body
**问题：** `Get-OpenCodeMessages` 尝试在 GET 请求中发送 body，导致 ProtocolViolationException

**解决：**
```powershell
# ❌ 错误 - GET 请求不能有 body
Invoke-RestMethod -Uri $url -Method GET -Body @{ limit = $Limit }

# ✅ 正确 - 使用查询参数
$path = "/session/$SessionId/message?limit=$Limit"
Invoke-RestMethod -Uri "$($Controller.BaseUrl)$path" -Method GET
```

**经验：** HTTP GET 请求不能有 body，参数应放在 URL 查询字符串中

---

## 💡 关键发现

### 发现 1：必须指定 Agent 参数
这是最重要的发现！不指定 agent，消息不会被处理。

```powershell
# ❌ 消息进入但无响应
Send-OpenCodeMessage -Message "Task"  # 无声无息

# ✅ 正确处理并响应
Send-OpenCodeMessage -Message "Task" -Agent "general"
```

**可用 agents：**
- `general` - 通用任务（推荐）
- `chief` - 复杂协调
- `explore` - 代码探索
- `deputy`, `researcher`, `writer`, `editor` - 专业代理

---

### 发现 2：异步模式不可靠
`Send-OpenCodeMessageAsync` 使用 `prompt_async` 端点，但消息发送后不会触发处理。

**建议：** 使用同步模式 (`noReply=$false`)，虽然会等待，但更可靠

---

### 发现 3：状态检测不可靠
`Wait-OpenCodeCompletion` 依赖 `session/status` 端点，但该端点经常返回空或状态不准确。

**建议：** 不要依赖状态检测，直接验证结果：
```powershell
# ❌ 可能超时，即使任务成功
Wait-OpenCodeCompletion -Timeout 60

# ✅ 直接检查结果
if (Test-Path $expectedFile) { "Success!" }
```

---

### 发现 4：目录访问限制可配置
OpenCode 的目录限制不是硬编码的，可以通过配置文件修改：

```json
// ~/.config/opencode/opencode.json
{
  "allowedDirectories": [
    "D:\\newtype-profile",
    "D:\\my-projects"
  ]
}
```

---

## 🧪 测试策略

### 测试方法
由于状态检测不可靠，采用**结果验证法**：

1. 发送任务
2. 等待合理时间（5-30秒，视任务复杂度）
3. 直接验证预期结果（文件是否存在、内容是否正确）

### 已验证的功能矩阵

| 功能 | 测试状态 | 备注 |
|------|---------|------|
| 服务器启动 | ✅ | 通过 cmd /c 启动 |
| 创建会话 | ✅ | 正常 |
| 发送消息 | ✅ | 必须使用 -Agent |
| 文件创建 | ✅ | 在允许目录内 |
| 代码编辑 | ✅ | 读取→修改→保存 |
| 插件安装 | ✅ | oh-my-opencode 成功 |
| ultrawork 任务 | ✅ | 复杂多文件任务 |

---

## 📝 文档经验

### README 编写的教训

**第一稿：** 泛泛介绍功能，没抓住核心  
**第二稿：** 强调"让 OpenClaw 控制 OpenCode"，开门见山

**要点：**
- 首段就要说明"这是什么"和"解决什么问题"
- 使用场景要具体、真实
- 区分"这是 Skill 的限制"和"这是底层工具的限制"

---

## 🚀 发布 checklist

- [x] 代码修复完成
- [x] 功能测试通过
- [x] SKILL.md 详细文档
- [x] README.md 项目介绍
- [x] TEST_LOG.md 测试记录
- [x] Git commit 信息清晰
- [x] 推送到 GitHub
- [x] README 突出核心价值

---

## 🎓 学到的经验

### 关于 Skill 开发
1. **先解决底层问题** - 修复 bug 再写文档
2. **测试要覆盖真实场景** - 不只是 API 调用，要有实际任务
3. **文档要迭代** - 第一稿往往抓不住重点，需要重写
4. **记录测试过程** - TEST_LOG.md 很有价值

### 关于 OpenCode API
1. HTTP API 比 CLI 更稳定（Windows 上）
2. Agent 参数是必需的
3. 状态检测不可靠，要结果验证
4. serve 模式需要正确配置才能处理消息

### 关于 oh-my-opencode
1. ultrawork 模式非常强大，可以一次性完成复杂任务
2. 插件安装后会添加更多 agent 配置
3. 免费模型（glm-4.7-free）也能完成大部分任务

---

## 🔮 未来可能的改进

1. **Python 版本完善** - 目前主要测试了 PowerShell 版本
2. **错误重试机制** - 添加指数退避重试
3. **更智能的等待** - 基于消息内容而非固定时间
4. **更多 oh-my-opencode 功能** - 探索其他 agent 模式
5. **批量任务管理** - 多会话并行处理

---

## 💬 用户反馈准备

### 可能的问题

**Q: 为什么我的消息没有响应？**  
A: 必须使用 `-Agent "general"` 参数

**Q: 可以访问其他目录吗？**  
A: 可以，修改 OpenCode 配置文件的 `allowedDirectories`

**Q: Windows 上能用吗？**  
A: 这正是这个 Skill 的主要目标平台！

**Q: 和直接运行 `opencode run` 有什么区别？**  
A: 绕过 TTY 问题，支持程序化调用，可以从 OpenClaw 中触发

---

## 🎉 最终成果

**GitHub 仓库：** https://github.com/wumajiehechuan-lab/opencode-controller

**解决的问题：**
- ✅ Windows opencode run 卡住
- ✅ OpenClaw 无法调用 OpenCode
- ✅ 程序化控制 OpenCode 的需求

**带来的价值：**
- OpenClaw 用户可以直接让 OpenCode 写代码
- 自动化脚本可以批量处理编程任务
- 打通了两个强大 AI 工具的能力

---

*Developed with ❤️ and 🦞*
