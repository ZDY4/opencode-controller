#!/usr/bin/env python3
"""
OpenCode 任务监控器
监控 OpenCode 任务执行状态，完成后自动通知
"""

import sys
import time
sys.path.insert(0, '/Users/jujuren/.openclaw/workspace/skills/opencode-controller/scripts')

from opencode_controller import OpenCodeController
from datetime import datetime

def monitor_opencode_task(session_id: str, task_name: str, chat_id: str = "6186153489"):
    """
    监控 OpenCode 任务直到完成，然后发送通知
    
    Args:
        session_id: OpenCode 会话ID
        task_name: 任务名称（用于通知显示）
        chat_id: Telegram 聊天ID
    """
    print(f"🔍 开始监控任务: {task_name}")
    print(f"📋 Session ID: {session_id}")
    print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    ctrl = OpenCodeController(
        port=4096, 
        working_dir='/Users/jujuren/.openclaw/workspace/quant', 
        auto_start=False
    )
    
    check_count = 0
    last_message_count = 0
    no_change_count = 0
    
    while True:
        check_count += 1
        
        try:
            # 获取会话消息
            messages = ctrl.get_messages(session_id)
            current_count = len(messages)
            
            # 检查是否有新消息
            if current_count > last_message_count:
                print(f"  📝 检测到新消息 ({current_count} 条)")
                last_message_count = current_count
                no_change_count = 0
                
                # 检查最后一条消息是否是最终结果
                last_msg = messages[-1] if messages else None
                if last_msg and last_msg.get('role') == 'assistant':
                    text = last_msg.get('text', '')
                    # 如果消息很长且包含"完成"、"总结"等关键词，可能是最终结果
                    if len(text) > 500 and any(kw in text for kw in ['完成', '总结', '优化', '修复', '报告', '✅']):
                        print(f"\n✅ 任务似乎已完成！")
                        print(f"📊 总消息数: {current_count}")
                        print(f"🕐 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        # 发送 Telegram 通知
                        send_telegram_notification(task_name, chat_id, completed=True)
                        return True
            else:
                no_change_count += 1
                
            # 如果超过 10 次检查没有变化（约50分钟），认为任务可能卡住了或已完成
            if no_change_count >= 10:
                print(f"\n⚠️ 超过10次检查无变化，任务可能已完成或卡住")
                send_telegram_notification(task_name, chat_id, completed=False, stuck=True)
                return False
                
            # 每 5 分钟检查一次
            print(f"  ⏳ 第 {check_count} 次检查，等待 5 分钟...")
            time.sleep(300)  # 5分钟
            
        except Exception as e:
            print(f"  ❌ 检查出错: {e}")
            time.sleep(60)  # 出错后1分钟再试

def send_telegram_notification(task_name: str, chat_id: str, completed: bool = True, stuck: bool = False):
    """发送 Telegram 通知"""
    try:
        import requests
        import os
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "REDACTED")
        proxy = os.getenv("HTTP_PROXY", "http://127.0.0.1:7897")
        
        if completed and not stuck:
            message = f"""✅ **OpenCode 任务完成！**

📋 任务名称：{task_name}
🕐 完成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

任务已成功完成，请查看结果。"""
        elif stuck:
            message = f"""⚠️ **OpenCode 任务状态异常**

📋 任务名称：{task_name}
🕐 检查时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

任务可能已完成或长时间无响应，请手动检查。"""
        else:
            message = f"""ℹ️ **OpenCode 任务更新**

📋 任务名称：{task_name}
🕐 时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

有新的进展，请查看。"""
        
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        if proxy:
            requests.post(url, json=payload, proxies={'http': proxy, 'https': proxy}, timeout=10)
        else:
            requests.post(url, json=payload, timeout=10)
            
        print(f"  ✅ Telegram 通知已发送")
        
    except Exception as e:
        print(f"  ❌ 发送通知失败: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='监控 OpenCode 任务')
    parser.add_argument('session_id', help='OpenCode 会话 ID')
    parser.add_argument('task_name', help='任务名称')
    parser.add_argument('--chat-id', default='6186153489', help='Telegram Chat ID')
    
    args = parser.parse_args()
    
    monitor_opencode_task(args.session_id, args.task_name, args.chat_id)
