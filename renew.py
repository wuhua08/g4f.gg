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

def parse_time_to_seconds(time_str):
    try:
        parts = time_str.strip().split(':')
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except:
        pass
    return 0

if __name__ == "__main__":
    print("\n===== 🚀 g4f.gg 自动续期 (精准点击版) =====")

    if os.path.exists(SCREENSHOT_PATH):
        try: os.remove(SCREENSHOT_PATH)
        except: pass

    try:
        # ✨ 恢复 1920x1080 桌面大分辨率，防止移动端布局导致坐标错位
        with SB(uc=True, test=True, locale_code="en", window_size="1920,1080") as sb:
            sb.uc_open_with_reconnect(TARGET_URL, 10)
            sb.sleep(5)
            sb.maximize_window() # 强制最大化窗口

            # 1. 记录点击前的初始时间
            time_before_str = "无法获取"
            time_before_secs = 0
            try:
                time_before_str = sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]/following-sibling::div[1]")
                time_before_secs = parse_time_to_seconds(time_before_str)
                print(f"⏱️ 点击前服务器剩余时间: {time_before_str}")
            except Exception as e:
                print(f"⚠️ 无法读取初始时间: {e}")

            print("🔍 正在定位续期按钮...")
            selectors = [
                "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(text(), 'ADD')]"
            ]
            
            target_selector = None
            for selector in selectors:
                if sb.is_element_visible(selector):
                    target_selector = selector
                    break

            if not target_selector:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：未能定位到续期按钮，请检查页面是否改版", SCREENSHOT_PATH)
                sys.exit(1)

            # ✨ 2. 确保滚动到按钮可见区域再点击
            print(f"🎯 发现目标按钮，正在滚动并聚焦...")
            sb.scroll_to_element(target_selector)
            sb.sleep(2)

            # ✨ 3. 组合拳点击策略
            print("👇 正在尝试标准点击...")
            sb.click(target_selector) # 优先采用你原脚本成功的原生点击
            sb.sleep(3)

            # 检查是否成功唤起验证码或者成功刷新，如果没有，用 JS 强行注入点击
            if not sb.is_text_visible("VERIFY YOU'RE HUMAN") and not ("hours added" in sb.get_page_source().lower()):
                print("⚠️ 标准点击似乎未生效，正在尝试 JavaScript 强行点击...")
                sb.js_click(target_selector)
                sb.sleep(3)

            # 4. 对抗人机验证弹窗
            if sb.is_text_visible("VERIFY YOU'RE HUMAN") or sb.is_text_visible("请确认您是真人"):
                print("⚠️ 成功触发 Cloudflare Turnstile 人机验证弹窗！开始尝试自动破解...")
                for i in range(3):
                    print(f"🔄 正在进行第 {i+1} 次尝试过验证...")
                    sb.uc_gui_click_captcha() # 尝试点击验证框
                    sb.sleep(6)
                    if not sb.is_text_visible("VERIFY YOU'RE HUMAN") and not sb.is_text_visible("请确认您是真人"):
                        print("🎉 验证码弹窗已消失！")
                        break
            else:
                print("ℹ️ 未检测到验证码弹窗，可能直接通过或点击未响应。")

            print("⏳ 等待最终结果确认...")
            sb.sleep(10)
            sb.save_screenshot(SCREENSHOT_PATH)

            # 5. 记录点击后的时间
            time_after_str = "无法获取"
            time_after_secs = 0
            try:
                time_after_str = sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]/following-sibling::div[1]")
                time_after_secs = parse_time_to_seconds(time_after_str)
                print(f"⏱️ 点击后服务器剩余时间: {time_after_str}")
            except:
                pass

            # 6. 最终严格校验
            page_source = sb.get_page_source().lower()
            has_success_toast = "hours added" in page_source or "已延长" in page_source
            time_increased = (time_after_secs - time_before_secs) > 3600 

            if has_success_toast or time_increased:
                success_msg = f"✅ 续期真正成功！\n当前剩余时间：{time_after_str}"
                print(f"\n🎉 {success_msg}")
                send_tg_with_screenshot(success_msg, SCREENSHOT_PATH)
            else:
                fail_msg = f"❌ 续期失败：按钮点击未生效或未通过验证。\n点击前: {time_before_str}\n点击后: {time_after_str}"
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
