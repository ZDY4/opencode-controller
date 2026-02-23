#!/usr/bin/env python3
"""
OpenCode 任务监控器 - 优化版
监控 OpenCode 任务执行状态，完成后自动通知
"""

import sys
import time
import os
from pathlib import Path

# 添加 skill 路径
sys.path.insert(0, str(Path(__file__).parent))

from opencode_controller import OpenCodeController
from datetime import datetime


def load_env_file(env_path: Path) -> bool:
    """手动解析 .env 文件，不依赖 dotenv 包"""
    if not env_path.exists():
        return False
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    # 只设置尚未存在的环境变量
                    if key not in os.environ:
                        os.environ[key] = value
        return True
    except Exception:
        return False


def get_telegram_config() -> tuple:
    """
    获取 Telegram 配置，按优先级查找：
    1. 系统环境变量（已设置）
    2. 当前工作目录的 .env
    3. OpenClaw 项目目录的 .env
    4. 返回 None，让调用者处理错误
    
    Returns:
        (bot_token, proxy) 或 (None, None)
    """
    # 优先级1: 已存在的环境变量
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    proxy = os.getenv("HTTP_PROXY")
    
    if bot_token:
        return bot_token, proxy
    
    # 优先级2: 当前工作目录的 .env
    cwd_env = Path.cwd() / ".env"
    if load_env_file(cwd_env):
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        proxy = os.getenv("HTTP_PROXY")
        if bot_token:
            return bot_token, proxy
    
    # 优先级3: OpenClaw 项目目录的 .env
    # 尝试找到 quant 项目的 .env
    possible_paths = [
        Path.home() / ".openclaw" / "workspace" / "quant" / ".env",
        Path.home() / "openclaw" / "workspace" / "quant" / ".env",
        Path(__file__).parent.parent.parent.parent / "quant" / ".env",
    ]
    
    for env_path in possible_paths:
        if load_env_file(env_path):
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            proxy = os.getenv("HTTP_PROXY")
            if bot_token:
                return bot_token, proxy
    
    # 未找到
    return None, None


def get_poll_interval(check_count: int) -> int:
    """动态轮询间隔 - 指数退避策略"""
    if check_count <= 2:
        return 30    # 前2次：每30秒
    elif check_count <= 5:
        return 60    # 第3-5次：每1分钟
    elif check_count <= 10:
        return 120   # 第6-10次：每2分钟
    else:
        return 180   # 之后：每3分钟


def check_task_completion(ctrl: OpenCodeController, session_id: str, 
                          last_count: int) -> tuple:
    """
    检查任务完成状态
    
    Returns:
        (is_completed, is_stuck, current_count, status_message)
    """
    try:
        # 获取 session 状态
        status_info = ctrl.get_session_status(session_id)
        current_status = status_info.get('status', 'unknown')
        
        # 获取消息
        messages = ctrl.get_messages(session_id)
        current_count = len(messages)
        
        # 判断条件1：OpenCode API 报告 idle 状态
        is_idle = current_status == 'idle'
        
        # 判断条件2：最后一条是 assistant 回复且较长
        last_is_assistant = False
        completion_indicators = False
        
        if messages:
            last_msg = messages[-1]
            if last_msg.get('role') == 'assistant':
                last_is_assistant = True
                text = last_msg.get('text', '')
                indicators = ['完成', '总结', '优化', '修复', '报告', '✅', '✓', 
                            'finished', 'completed', 'done', 'summary']
                completion_indicators = any(kw in text for kw in indicators) or len(text) > 800
        
        # 综合判断
        if is_idle and last_is_assistant:
            return True, False, current_count, "Session idle + assistant response"
        
        if current_count == last_count and last_is_assistant and completion_indicators:
            return True, False, current_count, "No new messages + completion indicators"
            
        return False, False, current_count, "Task in progress"
        
    except Exception as e:
        return False, False, last_count, f"Check failed: {e}"


def monitor_opencode_task(session_id: str, task_name: str, chat_id: str = "6186153489",
                          max_no_change: int = 15, max_duration: int = 3600):
    """
    监控 OpenCode 任务直到完成，然后发送通知
    """
    print(f"🔍 开始监控任务: {task_name}")
    print(f"📋 Session ID: {session_id}")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查 Telegram 配置
    bot_token, _ = get_telegram_config()
    if not bot_token:
        print("⚠️  警告: 未找到 TELEGRAM_BOT_TOKEN，将无法发送通知")
        print("   请设置环境变量或在 .env 文件中配置")
    
    ctrl = OpenCodeController(
        port=4096, 
        working_dir=str(Path.cwd()),
        auto_start=False
    )
    
    check_count = 0
    last_message_count = 0
    no_change_count = 0
    start_time = time.time()
    
    while True:
        check_count += 1
        elapsed = time.time() - start_time
        
        # 检查是否超过最大监控时长
        if elapsed > max_duration:
            print(f"\n⏰ 超过最大监控时长 ({max_duration/60:.0f}分钟)，停止监控")
            send_telegram_notification(task_name, chat_id, completed=False, 
                                       message="监控超时")
            return False
        
        try:
            # 检查任务状态
            is_completed, is_stuck, current_count, status_msg = \
                check_task_completion(ctrl, session_id, last_message_count)
            
            # 打印进度
            poll_interval = get_poll_interval(check_count)
            print(f"  [{check_count:2d}] {datetime.now().strftime('%H:%M:%S')} | "
                  f"消息: {current_count:3d} | 状态: {status_msg[:20]:20s} | "
                  f"下次: {poll_interval//60}分{poll_interval%60:02d}秒")
            
            # 检查是否完成
            if is_completed:
                duration = time.time() - start_time
                print(f"\n✅ 任务完成！用时: {duration/60:.1f}分钟")
                
                send_telegram_notification(task_name, chat_id, completed=True, 
                                           duration=duration, message_count=current_count)
                return True
            
            # 检查是否卡住
            if current_count == last_message_count:
                no_change_count += 1
            else:
                no_change_count = 0
                last_message_count = current_count
            
            if no_change_count >= max_no_change:
                print(f"\n⚠️ 连续{max_no_change}次检查无变化")
                send_telegram_notification(task_name, chat_id, completed=False, stuck=True)
                return False
            
            # 动态等待
            time.sleep(poll_interval)
            
        except KeyboardInterrupt:
            print("\n\n🛑 用户中断监控")
            return False
            
        except Exception as e:
            print(f"  ❌ 检查出错: {e}")
            time.sleep(30)


def send_telegram_notification(task_name: str, chat_id: str, completed: bool = True, 
                               stuck: bool = False, duration: float = 0, 
                               message_count: int = 0, message: str = ""):
    """发送 Telegram 通知"""
    try:
        import requests
        
        bot_token, proxy = get_telegram_config()
        if not bot_token:
            print("  ⚠️ 未配置 TELEGRAM_BOT_TOKEN，跳过通知")
            return
        
        if completed:
            status_emoji = "✅"
            status_text = "任务完成！"
            duration_str = f"⏱ 用时: {duration/60:.1f}分钟\n" if duration > 0 else ""
            msg_str = f"💬 消息: {message_count} 条\n" if message_count > 0 else ""
            
            notify_msg = f"""{status_emoji} **OpenCode {status_text}**

📋 **{task_name}**
{duration_str}{msg_str}
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
            
        elif stuck:
            status_emoji = "⚠️"
            status_text = "任务状态异常"
            notify_msg = f"""{status_emoji} **OpenCode {status_text}**

📋 **{task_name}**
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

任务可能已完成或长时间无响应，请手动检查。"""
            
        else:
            status_emoji = "ℹ️"
            notify_msg = f"""{status_emoji} **OpenCode 任务更新**

📋 **{task_name}**
🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{message}"""
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": notify_msg,
            "parse_mode": "Markdown"
        }
        
        if proxy:
            requests.post(url, json=payload, 
                         proxies={'http': proxy, 'https': proxy}, 
                         timeout=10)
        else:
            requests.post(url, json=payload, timeout=10)
        
        print(f"  ✅ Telegram 通知已发送")
            
    except Exception as e:
        print(f"  ❌ 发送通知失败: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='监控 OpenCode 任务（优化版）')
    parser.add_argument('session_id', help='OpenCode 会话 ID')
    parser.add_argument('task_name', help='任务名称')
    parser.add_argument('--chat-id', default='6186153489', help='Telegram Chat ID')
    parser.add_argument('--max-no-change', type=int, default=15, 
                       help='最大无变化次数（默认15）')
    parser.add_argument('--max-duration', type=int, default=3600,
                       help='最大监控时长（秒，默认3600=1小时）')
    
    args = parser.parse_args()
    
    monitor_opencode_task(
        args.session_id, 
        args.task_name, 
        args.chat_id,
        args.max_no_change,
        args.max_duration
    )
