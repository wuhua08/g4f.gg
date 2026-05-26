sb.open(TARGET_URL)
sb.sleep(8)

print("🔍 点击 ADD 3 HOURS...")

# 先点续期
sb.click("//button[contains(.,'ADD 3 HOURS')]", timeout=10)

sb.sleep(3)

print("🔍 检查是否弹出 Cloudflare...")

# 验证弹出后处理
try:
    sb.uc_gui_click_captcha()
    print("✅ 已完成 Cloudflare 验证")
except Exception as e:
    print(f"⚠️ 验证未出现: {e}")

sb.sleep(8)

# 有些站点验证后需要再点一次
try:
    sb.click("//button[contains(.,'ADD 3 HOURS')]", timeout=10)
    print("✅ 二次点击成功")
except:
    pass

sb.sleep(10)
