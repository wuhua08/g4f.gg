import os
import sys
import time
from seleniumbase import SB
import requests

# ==========================================
# 核心配置
# ==========================================
TARGET_URL = "https://g4f.gg/wufuyang"
TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")
SCREENSHOT_PATH = "renew_result.png"

def send_tg_with_screenshot(text, screenshot_path):
    print(f"\n📤 正在发送 Telegram 通知...")
    if not TG_TOKEN or not TG_CHAT_ID:
        print("❌ 通知失败：TG_TOKEN 或 TG_CHAT_ID 为空")
        return
    if not os.path.exists(screenshot_path):
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            data = {"chat_id": TG_CHAT_ID, "text": f"🤖 G4F 自动续期\n{text}"}
            requests.post(url, json=data, timeout=10)
            return
        except Exception as e:
            print(f"❌ 文字消息发送异常：{e}")
            return
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        with open(screenshot_path, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": TG_CHAT_ID, "caption": f"🤖 G4F 自动续期\n{text}"}
            requests.post(url, files=files, data=data, timeout=15)
    except Exception as e:
        print(f"❌ 发送带截图通知异常：{e}")

# 🚀 将时间字符串 (如 71:55:46) 转换为秒数，用于精准对比
def parse_time_to_seconds(time_str):
    try:
        parts = time_str.strip().split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except:
        pass
    return 0

if __name__ == "__main__":
    print("\n===== 🚀 g4f.gg 自动续期 (严格校验版) =====")

    if os.path.exists(SCREENSHOT_PATH):
        try: os.remove(SCREENSHOT_PATH)
        except: pass

    try:
        # 使用 SeleniumBase 的 UC (Undetected) 模式
        with SB(uc=True, test=True, locale_code="en") as sb:
            sb.uc_open_with_reconnect(TARGET_URL, 10)
            sb.sleep(8) 

            # 1. 记录点击前的初始时间
            time_before_str = "无法获取"
            time_before_secs = 0
            try:
                time_before_str = sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]/following-sibling::div[1]")
                time_before_secs = parse_time_to_seconds(time_before_str)
                print(f"⏱️ 点击前服务器剩余时间: {time_before_str} ({time_before_secs} 秒)")
            except Exception as e:
                print(f"⚠️ 无法读取初始时间: {e}")

            print("🔍 正在定位并点击续期按钮...")
            selectors = [
                "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(text(), 'ADD')]"
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    sb.uc_click(selector, timeout=10)
                    print(f"✅ 已触发点击动作 (选择器: {selector})")
                    clicked = True
                    break
                except Exception:
                    continue 

            if not clicked:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：未能定位到续期按钮", SCREENSHOT_PATH)
                sys.exit(1)

            # 2. ✨ 核心强化：专门对抗人机验证弹窗
            sb.sleep(3)
            # 检测页面是否弹出了 "VERIFY YOU'RE HUMAN" 的文本
            if sb.is_text_visible("VERIFY YOU'RE HUMAN") or sb.is_text_visible("请确认您是真人"):
                print("⚠️ 检测到 Cloudflare Turnstile 人机验证弹窗！开始尝试自动破解...")
                for i in range(3): # 最多尝试点击 3 次验证码
                    print(f"🔄 正在进行第 {i+1} 次尝试过验证...")
                    sb.uc_gui_click_captcha() # 调用 SB 内置的坐标/图形验证码点击帮手
                    sb.sleep(6)
                    if not sb.is_text_visible("VERIFY YOU'RE HUMAN") and not sb.is_text_visible("请确认您是真人"):
                        print("🎉 验证码弹窗已消失，疑似通过！")
                        break
            else:
                print("ℹ️ 未检测到明显的验证码弹窗，继续等待页面刷新...")

            sb.sleep(10)
            sb.save_screenshot(SCREENSHOT_PATH)

            # 3. 记录点击后的时间
            time_after_str = "无法获取"
            time_after_secs = 0
            try:
                time_after_str = sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]/following-sibling::div[1]")
                time_after_secs = parse_time_to_seconds(time_after_str)
                print(f"⏱️ 点击后服务器剩余时间: {time_after_str} ({time_after_secs} 秒)")
            except:
                pass

            # 4. ✨ 严格的成功双重判定逻辑
            page_source = sb.get_page_source()
            # 判定条件 1：页面出现了官方成功绿条文本
            has_success_toast = "hours added" in page_source or "已延长" in page_source
            # 判定条件 2：点击后的秒数明显大于点击前的秒数（增加超过 1 小时以上，排除误差）
            time_increased = (time_after_secs - time_before_secs) > 3600 

            if has_success_toast or time_increased:
                success_msg = f"✅ 续期真正成功！\n当前剩余时间：{time_after_str}"
                print(f"\n🎉 {success_msg}")
                send_tg_with_screenshot(success_msg, SCREENSHOT_PATH)
            else:
                fail_msg = f"❌ 续期失败：时间未增加。\n点击前: {time_before_str}\n点击后: {time_after_str}\n原因：大概率卡在 Cloudflare 验证码处。"
                print(f"\n{fail_msg}")
                send_tg_with_screenshot(fail_msg, SCREENSHOT_PATH)
                sys.exit(1)

    except Exception as e:
        error_msg = f"❌ 💥 脚本运行异常：{str(e)}"
        print(f"\n{error_msg}")
        if os.path.exists(SCREENSHOT_PATH):
            send_tg_with_screenshot(error_msg, SCREENSHOT_PATH)
        else:
            send_tg_with_screenshot(error_msg, "")
        sys.exit(1)

    print("\n===== 🛑 脚本执行完成 =====")
