# OpenCode Controller Skill for OpenClaw

[![License](https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square)](LICENSE)
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-green.svg?style=flat-square)](https://openclaw.ai)
[![OpenCode](https://img.shields.io/badge/OpenCode-Controller-purple.svg?style=flat-square)](https://opencode.ai)

> **让 OpenClaw 具备控制 OpenCode 的能力**

这是一个 [OpenClaw](https://openclaw.ai) Skill，让你的 OpenClaw AI 助手能够通过 HTTP API 控制 [OpenCode](https://opencode.ai) AI 编程助手。

## 🎯 核心目的

**解决一个问题：在 Windows 上，`opencode run` 命令会卡住。**

这个 Skill 通过 OpenCode 的 HTTP Server API 绕过 TTY 问题，让 OpenClaw 能够：

1. **自动管理 OpenCode 服务器** - 启动、监控、重启
2. **创建编程会话** - 在指定目录创建独立的工作空间
3. **发送编程任务** - 让 OpenCode 执行编码任务（写代码、改代码、文件操作）
4. **获取执行结果** - 接收 OpenCode 的响应和生成的文件

**最终效果：** OpenClaw 用户可以直接说「帮我用 OpenCode 写个 Python 脚本」，OpenClaw 会自动调用 OpenCode 完成并返回结果。

---

## 🚀 为什么需要这个 Skill？

### 场景 1：Windows 用户想使用 OpenCode

**问题：**
```powershell
# 在 Windows 上执行会卡住
opencode run "Create a todo app"
# ⏳ 永远等待...
```

**解决方案（使用本 Skill）：**
```powershell
# OpenClaw 自动通过 HTTP API 调用 OpenCode
# 不依赖 TTY，稳定可靠 ✅
```

### 场景 2：OpenClaw 用户想用 OpenCode 的能力

**用户说：**
> "帮我用 OpenCode 创建一个任务管理器网页"

**OpenClaw 执行（使用本 Skill）：**
1. 自动启动 OpenCode HTTP 服务器
2. 创建会话
3. 发送任务给 OpenCode
4. OpenCode 生成代码并保存文件
5. OpenClaw 告知用户完成

### 场景 3：自动化工作流

**批量处理：**
```powershell
# OpenClaw 脚本批量调用 OpenCode 处理多个文件
foreach ($file in $files) {
    OpenCode-Refactor -File $file
}
```

---

## 📦 安装

### 前置要求

- [OpenClaw](https://openclaw.ai) 已安装并运行
- [OpenCode](https://opencode.ai) 已安装 (`opencode --version`)
- PowerShell 5.1+ (Windows)

### 安装步骤

1. **克隆 Skill 到 OpenClaw 工作目录**

```powershell
cd $env:USERPROFILE\.openclaw\workspace\skills
git clone https://github.com/wumajiehechuan-lab/opencode-controller.git
```

2. **加载 Skill**

```powershell
# 在 OpenClaw 会话中或 PowerShell 中
. $env:USERPROFILE\.openclaw\workspace\skills\opencode-controller\scripts\opencode_controller.ps1
```

3. **验证安装**

```powershell
# 创建测试控制器
$ctrl = New-OpenCodeController -WorkingDir "D:\newtype-profile"
Write-Host "OpenCode Controller loaded successfully!"
```

---

## 💡 使用方式

### 方式 1：OpenClaw 直接调用

配置好 Skill 后，OpenClaw 用户可以直接说：

> "用 OpenCode 帮我写一个计算 BMI 的 Python 脚本"

OpenClaw 会自动：
1. 加载 OpenCode Controller Skill
2. 启动 OpenCode 服务器（如果未运行）
3. 创建会话
4. 发送任务给 OpenCode
5. 返回生成的代码给用户

### 方式 2：PowerShell 脚本中调用

```powershell
# 加载 Skill
. .\scripts\opencode_controller.ps1

# 初始化控制器
$ctrl = New-OpenCodeController -WorkingDir "D:\my-project"

# 创建会话
$session = New-OpenCodeSession -Controller $ctrl -Title "Refactor Code"

# 发送任务给 OpenCode
$response = Send-OpenCodeMessage `
    -Controller $ctrl `
    -SessionId $session.id `
    -Message "Refactor utils.py to use async/await" `
    -Agent "general"

# 处理响应
$response.parts | Where-Object { $_.type -eq "text" } | ForEach-Object { $_.text }
```

### 方式 3：OpenClaw 自动化工作流

在 OpenClaw 的自动化脚本中使用：

```powershell
# OpenClaw 心跳任务示例
# 每天自动让 OpenCode 检查代码质量

. $SKILL_PATH\opencode-controller\scripts\opencode_controller.ps1

$ctrl = New-OpenCodeController -WorkingDir $PROJECT_DIR
$session = New-OpenCodeSession -Controller $ctrl -Title "Daily Code Review"

Send-OpenCodeMessage -Controller $ctrl -SessionId $session.id `
    -Message "Review all Python files for code quality issues" `
    -Agent "general"
```

---

## 🔧 核心功能

### 1. 服务器管理

```powershell
# 自动启动 OpenCode 服务器（如果未运行）
$ctrl = New-OpenCodeController -Port 4096 -AutoStart $true

# 检查服务器状态
$running = Test-OpenCodeServer -Controller $ctrl

# 手动停止服务器
Stop-OpenCodeServer -Controller $ctrl
```

### 2. 会话管理

```powershell
# 创建会话（在指定工作目录）
$session = New-OpenCodeSession `
    -Controller $ctrl `
    -Title "Fix login bug" `
    -WorkingDir "D:\my-project"

# 列出所有会话
$sessions = Get-OpenCodeSession -Controller $ctrl

# 删除会话
Remove-OpenCodeSession -Controller $ctrl -SessionId $session.id
```

### 3. 任务执行

```powershell
# 发送任务（同步等待响应）
$response = Send-OpenCodeMessage `
    -Controller $ctrl `
    -SessionId $session.id `
    -Message "Fix the auth bug in auth.ts" `
    -Agent "general" `              # 必需参数！
    -TimeoutSec 120

# 提取文本响应
$text = $response.parts | Where-Object { $_.type -eq "text" }
```

### 4. oh-my-opencode 支持

如果安装了 oh-my-opencode 插件，支持高级模式：

```powershell
# 使用 ultrawork 模式执行复杂任务
$task = @"
ultrawork

Create a complete todo list web application with:
- HTML/CSS/JavaScript
- Tailwind CSS styling
- Local storage persistence
- Responsive design

Save to: D:\projects\todo-app\index.html
"@

$response = Send-OpenCodeMessage `
    -Controller $ctrl `
    -SessionId $session.id `
    -Message $task `
    -Agent "general" `
    -TimeoutSec 300
```

---

## ⚠️ 重要注意事项

### 必须指定 Agent 参数

**最常见错误！** 发送消息时必须指定 `-Agent`：

```powershell
# ❌ 错误 - 消息不会被处理
Send-OpenCodeMessage -SessionId $id -Message "List files"

# ✅ 正确
Send-OpenCodeMessage -SessionId $id -Message "List files" -Agent "general"
```

### 目录访问限制

这是 OpenCode 的安全限制，**不是本 Skill 的限制**。

默认允许访问：
- `D:\newtype-profile`
- `C:\Users\admin\Documents`
- `C:\Users\admin\Projects`

**如何修改：** 编辑 `~/.config/opencode/opencode.json`：

```json
{
  "allowedDirectories": [
    "D:\\newtype-profile",
    "D:\\my-projects",
    "C:\\work"
  ]
}
```

---

## 🧪 测试验证

本 Skill 已通过以下测试：

| 功能 | 状态 |
|------|------|
| 服务器自动启动/停止 | ✅ |
| 会话创建/删除 | ✅ |
| 消息发送与响应 | ✅ |
| 文件操作 | ✅ |
| 代码编辑任务 | ✅ |
| oh-my-opencode 插件安装 | ✅ |
| ultrawork 复杂任务 | ✅ |

详细测试记录见 [TEST_LOG.md](TEST_LOG.md)。

---

## 📁 文件结构

```
opencode-controller/
├── README.md              # 本文件
├── SKILL.md               # 详细 API 文档
├── TEST_LOG.md            # 测试记录
├── scripts/
│   ├── opencode_controller.ps1   # PowerShell 实现
│   ├── opencode_controller.py    # Python 实现
│   ├── example.py                # 使用示例
│   └── requirements.txt          # Python 依赖
└── .gitignore
```

---

## 🔗 相关项目

- [OpenClaw](https://openclaw.ai) - 开源 AI 助手框架
- [OpenCode](https://opencode.ai) - AI 编程助手
- [oh-my-opencode](https://github.com/code-yeongyu/oh-my-opencode) - OpenCode 增强插件

---

## 📄 许可证

MIT © wumajiehechuan-lab

---

## 💡 为什么创建这个 Skill？

**核心需求：** 让 OpenClaw 用户能够无缝使用 OpenCode 的编程能力。

**解决的问题：**
1. Windows 上 `opencode run` 的 TTY 问题
2. OpenClaw 和 OpenCode 之间的集成空白
3. 自动化工作流中程序化调用 OpenCode 的需求

**带来的价值：**
- OpenClaw 用户无需离开聊天界面就能让 OpenCode 写代码
- 自动化脚本可以批量调用 OpenCode 处理任务
- 打通了两个强大 AI 工具的能力

---

**让 OpenClaw 和 OpenCode 一起工作！** 🦞🤖
