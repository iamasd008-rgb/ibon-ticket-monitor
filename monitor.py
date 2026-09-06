import os
import requests
import json

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# 活動頁面與 ibon 真正的票況資料 API
ACTIVITY_ID = "39903"
TARGET_URL = f"https://ticket.ibon.com.tw/ActivityInfo/Details/{ACTIVITY_ID}"
API_URL = f"https://ticket.ibon.com.tw/ActivityInfo/GetProductInformationApi?activityId={ACTIVITY_ID}"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": TARGET_URL,
    "X-Requested-With": "XMLHttpRequest"
}

def send_discord_notify(message):
    if not DISCORD_WEBHOOK_URL:
        print("未設定 DISCORD_WEBHOOK_URL，略過推播。")
        return
        
    payload = {
        "content": f"🚨 **【ibon 票況變更通知】**\n{message}\n🔗 **快速購票連結**: {TARGET_URL}"
    }
    
    try:
        res = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        if res.status_code == 204:
            print("Discord 推播成功！")
        else:
            print(f"Discord 推播失敗，代碼: {res.status_code}")
    except Exception as e:
        print(f"推播發送例外: {e}")

def check_ticket_status():
    try:
        # 直接查詢官方後端 JSON 資料
        response = requests.get(API_URL, headers=HEADERS, timeout=15)
        
        # 若 API 回傳失敗，再回退抓一般頁面檢查
        if response.status_code != 200:
            print(f"API 請求失敗，代碼: {response.status_code}")
            return

        raw_text = response.text
        print(f"API 回傳長度: {len(raw_text)}")

        # 在 ibon 系統的 API 資料中，售罄場次通常帶有 "IsSoldOut": true 或 status 標記
        # 若含有已售完狀態，且沒有可售狀態，則認定為全數售完
        has_sold_out_signal = ("已售完" in raw_text) or ('"IsSoldOut":true' in raw_text) or ('"isSoldOut":true' in raw_text)
        
        # 檢查是否有可購買狀態（非售完標籤）
        has_available_ticket = ('"IsSoldOut":false' in raw_text) or ('"isSoldOut":false' in raw_text)

        print(f"狀態比對 -> 售完標記: {has_sold_out_signal} | 可售標記: {has_available_ticket}")

        if has_available_ticket and not has_sold_out_signal:
            print("確認偵測到有效釋票！發送 Discord 推播。")
            send_discord_notify("🎯 偵測到官方後端釋出票券！請立即點擊連結前往搶購！")
        else:
            print("目前官方資料確認仍為售罄狀態，保持安靜。")

    except Exception as e:
        print(f"執行爬蟲時發生錯誤: {e}")

if __name__ == "__main__":
    check_ticket_status()
