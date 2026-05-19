import os
import sys
import time
from seleniumbase import SB
from selenium.webdriver.common.by import By
import requests

# ==========================================
# 核心配置（和你 workflow 里的环境变量保持一致）
# ==========================================
TARGET_URL = "https://g4f.gg/wufuyang"
TG_TOKEN = os.getenv("TG_TOKEN", "")
TG_CHAT_ID = os.getenv("TG_CHAT_ID", "")
SCREENSHOT_PATH = "renew_result.png"

# ✅ 发送带截图的 Telegram 通知
def send_tg_with_screenshot(text, screenshot_path):
    print(f"\n📤 正在发送带截图的 Telegram 通知...")
    print(f"   TG_TOKEN: {'已设置' if TG_TOKEN else '空'}")
    print(f"   TG_CHAT_ID: {TG_CHAT_ID}")

    if not TG_TOKEN or not TG_CHAT_ID:
        print("❌ 通知失败：TG_TOKEN 或 TG_CHAT_ID 为空")
        return

    if not os.path.exists(screenshot_path):
        print(f"⚠️ 截图文件不存在：{screenshot_path}，只发送文字消息")
        try:
            url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
            data = {"chat_id": TG_CHAT_ID, "text": f"🤖 G4F 自动续期\n{text}"}
            r = requests.post(url, json=data, timeout=10)
            print(f"✅ 文字消息发送结果：状态码 {r.status_code}")
            return
        except Exception as e:
            print(f"❌ 文字消息发送异常：{e}")
            return

    # 发送带图片的消息
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
        # 使用 with 语句确保图片发送后文件流正常关闭，防止文件被系统占用
        with open(screenshot_path, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": TG_CHAT_ID, "caption": f"🤖 G4F 自动续期\n{text}"}
            r = requests.post(url, files=files, data=data, timeout=15)
        
        print(f"✅ 带截图通知发送结果：状态码 {r.status_code}")
        if r.status_code != 200:
            print(f"❌ 错误详情：{r.text}")
    except Exception as e:
        print(f"❌ 发送带截图通知异常：{e}")

# 主程序
if __name__ == "__main__":
    print("\n===== 🚀 g4f.gg 自动续期 =====")

    # 先删除旧截图
    if os.path.exists(SCREENSHOT_PATH):
        try:
            os.remove(SCREENSHOT_PATH)
        except Exception as e:
            print(f"⚠️ 无法删除旧截图: {e}")

    try:
        with SB(headless=True, window_size="1920,1080") as sb:
            sb.open(TARGET_URL)
            sb.sleep(15)  # 等待页面加载及 Cloudflare 盾（如有）

            # 🛠️ 优化后的续期按钮定位逻辑
            print("🔍 正在查找续期按钮...")
            renew_button = None
            
            # 方法 1：优先使用 XPath 强匹配（包含 "+ ADD 3 HOURS" 文本的按钮，忽略大小写和空格）
            try:
                xpath_selector = "//button[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]"
                btn = sb.find_element(By.XPATH, xpath_selector)
                if btn.is_displayed():
                    renew_button = btn
                    print(f"✅ 通过 XPath 精准找到续期按钮: {btn.text.strip()}")
            except:
                pass

            # 方法 2：如果 XPath 没找到，降级回滚到遍历检查（兼容模糊匹配）
            if not renew_button:
                all_buttons = sb.find_elements(By.XPATH, "//button")
                for btn in all_buttons:
                    try:
                        btn_text = btn.text.strip().upper()
                        if btn.is_displayed() and ("ADD 3 HOURS" in btn_text or "ADD" in btn_text):
                            renew_button = btn
                            print(f"✅ 通过遍历找到续期按钮：{btn.text.strip()}")
                            break
                    except:
                        pass

            # 如果依然没找到按钮
            if not renew_button:
                sb.save_screenshot(SCREENSHOT_PATH)
                send_tg_with_screenshot("❌ 续期失败：未找到指定的 [+ ADD 3 HOURS] 按钮", SCREENSHOT_PATH)
                sys.exit(1)

            # 点击续期
            sb.driver.execute_script("arguments[0].scrollIntoView(true);", renew_button)
            sb.sleep(2)
            sb.driver.execute_script("arguments[0].click();", renew_button)
            print("👆 已点击续期按钮，等待页面刷新...")
            sb.sleep(15)

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

            # 发送带截图的通知
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
