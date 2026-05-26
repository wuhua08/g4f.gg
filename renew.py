import os
import sys
from seleniumbase import SB
import requests

# ==========================================
# 核心配置
# ==========================================
TARGET_URL = "https://g4f.gg/wufuyang"
TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")
SCREENSHOT_PATH = "renew_result.png"

# ✅ 发送带截图的 Telegram 通知
def send_tg_with_screenshot(text, screenshot_path):
    print(f"\n📤 正在发送带截图的 Telegram 通知...")
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

# 主程序
if __name__ == "__main__":
    print("\n===== 🚀 g4f.gg 自动续期 =====")

    if os.path.exists(SCREENSHOT_PATH):
        try:
            os.remove(SCREENSHOT_PATH)
        except:
            pass

    try:
        # 关键修改 1 & 2: 
        # 加入 uc=True 启用防检测模式
        # 建议使用 headless2=True (新版无头模式) 替代 headless=True，过 CF 验证成功率更高
        with SB(uc=True, headless2=True, window_size="1920,1080") as sb:
            sb.open(TARGET_URL)
            sb.sleep(15)  # 等待页面加载

            print("🔍 正在执行续期点击...")
            
            selectors = [
                "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(text(), 'ADD')]"
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    sb.click(selector, timeout=10)
                    print(f"✅ 成功点击按钮 (选择器: {selector})")
                    clicked = True
                    break
                except Exception:
                    continue 

            if not clicked:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：未能在规定时间内定位并点击按钮", SCREENSHOT_PATH)
                sys.exit(1)

            print("👆 已点击续期按钮，等待验证框出现...")
            sb.sleep(5)
            
            # ==========================================
            # 关键修改 3: 捕获并处理 Cloudflare Turnstile 验证框
            # ==========================================
            try:
                # 查找 Cloudflare 验证框的 iframe
                cf_iframe = "iframe[src*='challenges.cloudflare.com']"
                if sb.is_element_present(cf_iframe):
                    print("🛡️ 检测到 Cloudflare 验证框，正在尝试处理...")
                    sb.switch_to_frame(cf_iframe)
                    
                    # 尝试点击复选框 (Turnstile 的结构点 body 或者 checkbox 均可触发)
                    try:
                        sb.click("input[type='checkbox']", timeout=3)
                    except:
                        sb.click("body", timeout=3)
                        
                    sb.switch_to_default_content() # 别忘了切回主页面
                    print("✅ 已点击验证框，等待验证通过...")
                    sb.sleep(12) # 给验证留出足够时间
            except Exception as e:
                sb.switch_to_default_content()
                print(f"⚠️ 未检测到验证框或处理异常 (可能未触发或已自动通过): {e}")

            print("⏳ 最终等待页面刷新...")
            sb.sleep(10)

            # 续期完成后截图
            sb.save_screenshot(SCREENSHOT_PATH)

            # 获取剩余时间
            remaining = "无法获取"
            try:
                remaining = sb.get_text("//div[contains(text(), 'SERVER TIME REMAINING')]/following-sibling::div[1]")
            except:
                pass

            success_msg = f"✅ 续期成功！\n剩余时间：{remaining}"
            print(f"\n🎉 {success_msg}")
            send_tg_with_screenshot(success_msg, SCREENSHOT_PATH)

    except Exception as e:
        error_msg = f"❌ 续期失败：{str(e)}"
        print(f"\n{error_msg}")
        if os.path.exists(SCREENSHOT_PATH):
            send_tg_with_screenshot(error_msg, SCREENSHOT_PATH)
        else:
            send_tg_with_screenshot(error_msg, "")
        sys.exit(1)

    print("\n===== 🛑 脚本执行完成 =====")
