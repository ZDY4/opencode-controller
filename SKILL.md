---
name: opencode-controller
description: "Control OpenCode programmatically via its HTTP Server API. Use when you need to run coding tasks through OpenCode headlessly, manage multiple OpenCode sessions, or integrate OpenCode into automated workflows. Supports automatic server startup, session management, async task execution, and result retrieval."
---

# OpenCode Controller

Control OpenCode programmatically via its HTTP Server API.

## What This Skill Does

This skill allows you to:
- Start and manage OpenCode HTTP server automatically
- Create and manage OpenCode sessions
- Send coding tasks to OpenCode
- Retrieve results asynchronously
- Monitor task progress

## ⚠️ Critical Requirements

### 1. Must Specify Agent

**Important:** When sending messages, you **must** specify the `agent` parameter. Without it, OpenCode will not process the message.

```powershell
# ❌ WRONG - Message will not be processed
Send-OpenCodeMessage -Controller $ctrl -SessionId $id -Message "List files"

# ✅ CORRECT - Use 'general' agent for most tasks
Send-OpenCodeMessage -Controller $ctrl -SessionId $id -Message "List files" -Agent "general"
```

**Available Agents:**
- `general` - General-purpose tasks (recommended for most use cases)
- `chief` - Complex coordination tasks
- `explore` - Codebase exploration
- `deputy`, `researcher`, `writer`, `editor` - Specialized sub-agents

### 2. Directory Access

**Windows:** OpenCode may have restrictions on certain directories. If you encounter access issues, ensure your working directory is accessible.

**Mac/Linux:** No known directory restrictions. OpenCode can access any directory the user has permission to read/write.

**Note:** Previous documentation mentioned specific Windows path restrictions. Testing confirmed these restrictions do not apply on Mac systems.

## Quick Start (PowerShell - Windows)

For Windows environments without Python:

```powershell
# Load the script (dot-source)
. .\scripts\opencode_controller.ps1

# Create controller
$ctrl = New-OpenCodeController -WorkingDir "D:\newtype-profile\my-project"

# Create session
$session = New-OpenCodeSession -Controller $ctrl -Title "Fix bug"

# Send task (CRITICAL: specify -Agent!)
$response = Send-OpenCodeMessage -Controller $ctrl `
    -SessionId $session.id `
    -Message "Create a hello.txt file with greeting" `
    -Agent "general"

# Check response
$response.parts | Where-Object { $_.type -eq "text" } | ForEach-Object { $_.text }

# Cleanup
Remove-OpenCodeSession -Controller $ctrl -SessionId $session.id
```

## API Reference (PowerShell)

### OpenCodeController Object

```powershell
$ctrl = @{
    Port = 4096                    # Server port
    ServerHost = "127.0.0.1"       # Server host
    WorkingDir = "D:\newtype-profile"  # Working directory
    AutoStart = $true              # Auto-start server if not running
    BaseUrl = "http://127.0.0.1:4096"
}
```

### Functions

**`New-OpenCodeController`**
```powershell
$ctrl = New-OpenCodeController `
    -Port 4096 `
    -WorkingDir "D:\newtype-profile" `
    -AutoStart $true
```

**`New-OpenCodeSession`**
```powershell
$session = New-OpenCodeSession -Controller $ctrl -Title "Task description"
# Returns: @{ id = "ses_xxx"; title = "..."; ... }
```

**`Send-OpenCodeMessage`** ⭐ RECOMMENDED
```powershell
$response = Send-OpenCodeMessage `
    -Controller $ctrl `
    -SessionId $session.id `
    -Message "Your task here" `
    -Agent "general"              # REQUIRED!

# Extract text from response
$text = $response.parts | Where-Object { $_.type -eq "text" } | ForEach-Object { $_.text }
```

**`Send-OpenCodeMessageAsync`** ⚠️ Not Recommended
```powershell
# Fire-and-forget (may not trigger processing)
Send-OpenCodeMessageAsync -Controller $ctrl -SessionId $session.id -Message "Task"
```

**`Wait-OpenCodeCompletion`** ⚠️ Known Issues
```powershell
# May timeout even when task succeeds
$result = Wait-OpenCodeCompletion `
    -Controller $ctrl `
    -SessionId $session.id `
    -Timeout 60
```

**`Remove-OpenCodeSession`**
```powershell
Remove-OpenCodeSession -Controller $ctrl -SessionId $session.id
```

## Usage Patterns

### Pattern 1: Simple Task with Result Verification

**Recommended approach** - Don't rely on `Wait-OpenCodeCompletion`, verify results directly:

```powershell
. .\scripts\opencode_controller.ps1

$ctrl = New-OpenCodeController -WorkingDir "D:\newtype-profile\my-project"
$session = New-OpenCodeSession -Controller $ctrl -Title "Create config"

# Send task
$response = Send-OpenCodeMessage -Controller $ctrl `
    -SessionId $session.id `
    -Message "Create a config.json file with { name: 'test' }" `
    -Agent "general"

Write-Host "Task acknowledged: $($response.parts[0].text)"

# Wait for background processing
Start-Sleep -Seconds 5

# Verify result directly (don't trust API status)
if (Test-Path "D:\newtype-profile\my-project\config.json") {
    Write-Host "✓ Success!"
    Get-Content "D:\newtype-profile\my-project\config.json"
} else {
    Write-Host "✗ Task may have failed"
}

# Cleanup
Remove-OpenCodeSession -Controller $ctrl -SessionId $session.id
```

### Pattern 2: Code Editing Task

```powershell
. .\scripts\opencode_controller.ps1

$ctrl = New-OpenCodeController -WorkingDir "D:\newtype-profile\project"
$session = New-OpenCodeSession -Controller $ctrl -Title "Refactor code"

# Multi-step task
$task = @"
Read the file at D:\newtype-profile\project\utils.py and:
1. Add docstrings to all functions
2. Add type hints
3. Save the updated file
"@

$response = Send-OpenCodeMessage -Controller $ctrl `
    -SessionId $session.id `
    -Message $task `
    -Agent "general"

# Check assistant response
$response.parts | Where-Object { $_.type -eq "text" } | ForEach-Object { $_.text }
```

### Pattern 3: Batch Processing

```powershell
. .\scripts\opencode_controller.ps1

$ctrl = New-OpenCodeController -WorkingDir "D:\newtype-profile"
$tasks = @(
    "Create file1.txt with content A",
    "Create file2.txt with content B",
    "Create file3.txt with content C"
)

$sessions = foreach ($task in $tasks) {
    $session = New-OpenCodeSession -Controller $ctrl -Title $task
    
    Send-OpenCodeMessage -Controller $ctrl `
        -SessionId $session.id `
        -Message $task `
        -Agent "general" | Out-Null
    
    $session.id
}

# Wait and verify
Start-Sleep -Seconds 10

foreach ($id in $sessions) {
    $session = Get-OpenCodeSession -Controller $ctrl -SessionId $id
    Write-Host "Session $($session.title): $($session.time.updated)"
    Remove-OpenCodeSession -Controller $ctrl -SessionId $id
}
```

### Pattern 4: Long-Running Task with Auto-Notification ⭐ NEW

For tasks that take a long time (e.g., code refactoring, comprehensive analysis), use the built-in monitor to get notified when complete:

**Python:**
```python
from opencode_controller import OpenCodeController
from opencode_monitor import start_monitor_in_background

# Create controller
ctrl = OpenCodeController(
    port=4096, 
    working_dir='/path/to/project', 
    auto_start=False
)

# Create session and send task
session = ctrl.create_session(title="Refactor Project")
response = ctrl.send_message(
    session_id=session['id'],
    message="Refactor the entire codebase...",
    agent='general'
)

# Start background monitor (runs independently)
monitor_pid = start_monitor_in_background(
    session_id=session['id'],
    task_name="Project Refactoring",
    chat_id="YOUR_TELEGRAM_CHAT_ID"
)

print(f"Task sent. Monitor PID: {monitor_pid}")
print("You will receive a Telegram notification when the task completes!")
```

**Shell:**
```bash
# Using the provided script
python3 scripts/opencode_monitor.py ses_xxx123 "My Task" --chat-id 6186153489

# Or with notify script
./scripts/start_monitor.sh ses_xxx123 "My Task" 6186153489
```

**How it works:**
- Checks every 5 minutes for new messages
- Detects task completion by analyzing message content
- Sends Telegram notification with task summary
- Handles stuck tasks (no activity for 50+ minutes)

**Configuration:**
Set these environment variables in your `.env` file:
```bash
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
HTTP_PROXY=http://127.0.0.1:7897  # optional
```

---

## newtype-profile Plugin Support

This skill supports the [newtype-profile](https://github.com/newtype-01/newtype-profile) plugin for content creation tasks.

### What is newtype-profile?

newtype-profile is an AI Agent collaboration framework designed for **content creation** (vs oh-my-opencode which focuses on coding). It simulates an editorial team with specialized roles:

| Agent | Role | Responsibility |
|-------|------|----------------|
| `chief` | Editor-in-Chief | Understands requirements, coordinates the team |
| `deputy` | Deputy Editor | Executes delegated tasks |
| `researcher` | Researcher | Gathers information and trends |
| `writer` | Writer | Creates content and drafts |
| `editor` | Editor | Refines and optimizes content |
| `fact-checker` | Fact-Checker | Validates sources and accuracy |
| `archivist` | Archivist | Knowledge base retrieval |
| `extractor` | Extractor | PDF/image content extraction |

### Installation

```bash
# Install the plugin
cd ~/.config/opencode
bun add newtype-profile

# Enable in config
echo '{"plugin":["newtype-profile"]}' > ~/.config/opencode/opencode.json
```

### Configuration

Create `~/.config/opencode/newtype-profile.json`:

```json
{
  "google_auth": true,
  "agents": {
    "chief": { "model": "google/antigravity-claude-opus-4-5-thinking-high" },
    "deputy": { "model": "google/antigravity-claude-sonnet-4-5" },
    "researcher": { "model": "google/antigravity-gemini-3-pro-high" },
    "writer": { "model": "google/antigravity-gemini-3-pro-high" },
    "editor": { "model": "google/antigravity-claude-sonnet-4-5" }
  }
}
```

### Usage Pattern: Content Creation

```powershell
. .\scripts\opencode_controller.ps1

$ctrl = New-OpenCodeController -WorkingDir "D:\newtype-profile"
$session = New-OpenCodeSession -Controller $ctrl -Title "Tech Report"

# Send content creation task
$task = @"
Write a comprehensive technical report about Claude Opus 4.6, including:
1. Model overview and release information
2. Key improvements over 4.5
3. Benchmark performance
4. Use case analysis
5. Final assessment

Save to: D:\newtype-profile\claude-opus-4-6-report.md
"@

$response = Send-OpenCodeMessage `
    -Controller $ctrl `
    -SessionId $session.id `
    -Message $task `
    -Agent "general" `
    -TimeoutSec 300  # Content creation may take longer

# Verify the output file
if (Test-Path "D:\newtype-profile\claude-opus-4-6-report.md") {
    Write-Host "✓ Report generated successfully!"
    Get-Content "D:\newtype-profile\claude-opus-4-6-report.md" -Head 20
}

Remove-OpenCodeSession -Controller $ctrl -SessionId $session.id
```

### Usage Pattern: Batch Article Generation

```powershell
. .\scripts\opencode_controller.ps1

$ctrl = New-OpenCodeController -WorkingDir "D:\newtype-profile\articles"

$topics = @(
    "AI Development Trends 2024",
    "Cloud Computing Best Practices",
    "Cybersecurity Fundamentals"
)

foreach ($topic in $topics) {
    $session = New-OpenCodeSession -Controller $ctrl -Title $topic
    
    $task = @"
Write a 1500-word article about "$topic".
Structure: Introduction → Key Points → Case Studies → Conclusion
Save to: D:\newtype-profile\articles\$($topic -replace '\s','-').md
"@
    
    Send-OpenCodeMessage `
        -Controller $ctrl `
        -SessionId $session.id `
        -Message $task `
        -Agent "general" | Out-Null
    
    Write-Host "Started: $topic"
}

# Wait for all tasks
Start-Sleep -Seconds 60

# Verify outputs
Get-ChildItem "D:\newtype-profile\articles\*.md" | Select-Object Name, Length
```

### Built-in Skills

newtype-profile includes specialized skills accessible via commands:

| Skill | Command | Description |
|-------|---------|-------------|
| Super Analyst | `/super-analyst` | Elite analytical consulting with 12 frameworks |
| Super Writer | `/super-writer` | Professional content creation with 6 methodologies |
| Playwright | `/playwright` | Browser automation for web scraping |

Example using built-in skills:

```powershell
$task = @"
/super-analyst

Analyze the competitive landscape of AI coding assistants.
Focus on: Claude, GPT-4, Gemini
Output: Structured comparison with SWOT analysis
"@

Send-OpenCodeMessage -Controller $ctrl -SessionId $session.id -Message $task -Agent "general"
```

### Best Practices for newtype-profile

1. **Be specific about output requirements**
   ```powershell
   # Good: Clear structure and format
   "Write a report with: 1) Executive Summary 2) Technical Details 3) Conclusion"
   
   # Less effective: Vague request
   "Write something about AI"
   ```

2. **Always specify save location**
   - newtype-profile works best when given explicit file paths
   - Ensures output can be verified and shared

3. **Use appropriate timeout**
   - Content creation takes longer than simple coding tasks
   - Recommend 300+ seconds for complex reports

4. **Leverage the editorial team**
   - Chief automatically delegates to specialist agents
   - No need to manually specify sub-agents

### Comparison: newtype-profile vs oh-my-opencode

| Aspect | oh-my-opencode | newtype-profile |
|--------|----------------|-----------------|
| **Best For** | Coding tasks | Content creation |
| **Main Agent** | Sisyphus | Chief (Editor-in-Chief) |
| **Task Command** | `sisyphus_task` | `chief_task` |
| **Key Strength** | Code refactoring | Research & writing |
| **Output Style** | Code & technical docs | Articles & reports |

---

## Known Issues & Limitations

### 1. Async Mode (`Send-OpenCodeMessageAsync`)
- **Status:** ⚠️ Not working reliably
- **Issue:** Messages sent via `prompt_async` endpoint may not trigger processing
- **Workaround:** Use synchronous `Send-OpenCodeMessage` instead

### 2. `Wait-ForCompletion` Status Detection
- **Status:** ⚠️ Unreliable
- **Issue:** May timeout even when task succeeds; session status endpoint returns empty
- **Workaround:** Verify results directly (e.g., check if file exists)

### 3. `Get-OpenCodeMessages` Returns Empty
- **Status:** ⚠️ Intermittent
- **Issue:** Sometimes returns empty array even when messages exist
- **Workaround:** Query directly via REST API if needed

### 4. Directory Restrictions
- **Status:** By design
- **Issue:** Can only access `D:\newtype-profile`, `C:\Users\admin\Documents`, `C:\Users\admin\Projects`
- **Workaround:** Use these directories or create symlinks

## Requirements

- OpenCode installed and available in PATH (`opencode --version`)
- PowerShell 5.1+ (Windows)
- Or Python 3.x with `requests` library

### Setup

**PowerShell (Windows - Recommended):**
```powershell
cd skills\opencode-controller\scripts
. .\opencode_controller.ps1
```

**Python (if available):**
```bash
cd scripts
pip install -r requirements.txt
python -c "from opencode_controller import OpenCodeController; print('OK')"
```

## Working Directory

Default working directory is `D:\newtype-profile`.

**Important:** OpenCode can only access files in allowed directories. The server will start in your specified directory, but file operations are restricted to:
- `D:\newtype-profile`
- `C:\Users\admin\Documents`
- `C:\Users\admin\Projects`

## Security Notes

- Server runs on localhost by default (127.0.0.1)
- No authentication in default setup (suitable for local use)
- All file operations restricted to allowed directories

## Troubleshooting

**"Server failed to start"**
```powershell
# Check OpenCode installation
opencode --version

# Check port availability
Get-NetTCPConnection -LocalPort 4096

# Check if process is running
Get-Process -Name "opencode","node"
```

**"Message not processed / No assistant response"**
- ✅ Make sure you specified `-Agent "general"`
- ✅ Check that working directory is in allowed list
- ✅ Try a simpler task first

**"Cannot access directory"**
- Use only allowed directories: `D:\newtype-profile`, `C:\Users\admin\Documents`, `C:\Users\admin\Projects`

**"Timeout waiting for completion"**
- This is a known issue with status detection
- Verify results directly instead of relying on `Wait-OpenCodeCompletion`

## Script Location

- PowerShell Controller: `scripts/opencode_controller.ps1`
- Python Controller: `scripts/opencode_controller.py`
- Requirements: `scripts/requirements.txt`

## Changelog

### 2026-02-08
- Added comprehensive newtype-profile plugin documentation
- Added content creation usage patterns
- Documented built-in skills (/super-analyst, /super-writer, /playwright)
- Added comparison: newtype-profile vs oh-my-opencode

### 2026-02-04
- Fixed `$Host` variable conflict → `$ServerHost`
- Fixed `Start-Process` npm script issue → use `cmd /c`
- Discovered critical requirement: must specify `-Agent` parameter
- Documented directory access restrictions
- Added known issues section
