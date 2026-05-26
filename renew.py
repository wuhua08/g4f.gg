import os
import sys
import time
from seleniumbase import SB
from selenium.webdriver.common.by import By
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
    print("\n===== 🚀 g4f.gg 自动续期 (Iframe 穿透破盾版) =====")

    if os.path.exists(SCREENSHOT_PATH):
        try:
            os.remove(SCREENSHOT_PATH)
        except:
            pass

    try:
        # 💡 优化 1：使用隐身能力更强的 headless2=True 配合 uc=True
        with SB(uc=True, headless2=True, window_size="1920,1080") as sb:
            
            print(f"🌐 正在打开目标网址: {TARGET_URL}")
            sb.uc_open_with_reconnect(TARGET_URL, 4)
            sb.sleep(8)  # 等待初始页面渲染

            print("🔍 步骤 1：正在寻找并点击续期按钮...")
            selectors = [
                "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD 3 HOURS')]",
                "//button[contains(., 'ADD')]",
                "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'RENEW')]"
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    if sb.is_element_visible(selector):
                        sb.click(selector, timeout=5)
                        print(f"✅ 成功点击续期按钮 (匹配选择器: {selector})")
                        clicked = True
                        break
                except Exception:
                    continue 

            if not clicked:
                sb.save_screenshot(SCREENSHOT_PATH)
                try:
                    with open("page_source.html", "w", encoding="utf-8") as f:
                        f.write(sb.get_page_source())
                except:
                    pass
                send_tg_with_screenshot("❌ 续期失败：未能在初始页面中定位到续期按钮", SCREENSHOT_PATH)
                sys.exit(1)

            # 💡 优化 2：遵照触发逻辑，点击按钮后强制等待验证码弹窗完全浮现
            print("⏳ 步骤 2：已点击续期按钮，等待 Cloudflare 验证码弹窗完全加载...")
            sb.sleep(7)  

            # 💡 优化 3：【核心】Iframe 穿透打击技术
            print("🛡️ 步骤 3：开始攻克 Cloudflare Turnstile 真人验证...")
            cf_solved = False
            
            # 定义 Cloudflare 常见的特有 iframe 选择器
            iframe_selectors = [
                "iframe[src*='cloudflare']", 
                "iframe[src*='turnstile']", 
                "iframe[title*='verification']"
            ]
            
            try:
                for iframe_sel in iframe_selectors:
                    if sb.is_element_present(iframe_sel):
                        print(f"🎯 检测到验证码容器 {iframe_sel}，正在切入内部...")
                        sb.switch_to_frame(iframe_sel)
                        sb.sleep(1)
                        
                        # 验证码内部核心复选框的常见标签选择器
                        inner_targets = ["input[type='checkbox']", "#challenge-stage", ".ctp-checkbox-label", "span.mark", "body"]
                        for target in inner_targets:
                            try:
                                sb.click(target, timeout=3)
                                print(f"⚡ 成功穿透并点击了验证码组件: {target}")
                                cf_solved = True
                                break
                            except:
                                continue
                        
                        sb.switch_to_default_content()  # 切回主页面
                        if cf_solved:
                            break
            except Exception as ie:
                print(f"⚠️ Iframe 穿透尝试中发生异常: {ie}")
                sb.switch_to_default_content()

            # 💡 优化 4：如果穿透法没点中，使用官方内置的 GUI 自动化算法做最后的兜底
            if not cf_solved:
                print("🔄 穿透法未确认成功，启动官方内置 GUI 智能识别点击...")
                try:
                    sb.uc_gui_click_captcha()
                    print("🔘 已触发 GUI 备用点击指令...")
                    cf_solved = True
                except Exception as ce:
                    print(f"❌ 备用点击也失败: {ce}")

            print("👆 验证操作已提交，等待 Cloudflare 放行及后台刷新...")
            sb.sleep(15)  # 给验证通过和服务器数据同步留出充裕时间

            # 最终结果截图
            sb.save_screenshot(SCREENSHOT_PATH)

            print("📊 步骤 4：正在获取续期后的服务器剩余时间...")
            remaining = "无法获取"
            try:
                remaining = sb.get_text("//div[contains(., 'SERVER TIME REMAINING')]/following-sibling::div[1]")
            except:
                try:
                    remaining = sb.get_text("//*[contains(., 'REMAINING') or contains(., '剩余时间')]")
                except:
                    pass

            success_msg = f"✅ 续期流程执行完毕！\n请查看最新通知截图。\n系统提取到的剩余时间：{remaining}"
            print(f"\n🎉 {success_msg}")
            send_tg_with_screenshot(success_msg, SCREENSHOT_PATH)

    except Exception as e:
        error_msg = f"❌ 续期异常退出：{str(e)}"
        print(f"\n{error_msg}")
        if os.path.exists(SCREENSHOT_PATH):
            send_tg_with_screenshot(error_msg, SCREENSHOT_PATH)
        else:
            send_tg_with_screenshot(error_msg, "")
        sys.exit(1)

    print("\n===== 🛑 脚本执行完成 =====")
