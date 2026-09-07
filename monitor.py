import os
import requests
import json
import time

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

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
        "content": f"🚨 **【ibon 釋票即時提醒】**\n{message}\n🔗 **快速購票連結**: {TARGET_URL}"
    }
    
    try:
        res = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        if res.status_code == 204:
            print("Discord 推播成功！")
        else:
            print(f"Discord 推播失敗，代碼: {res.status_code}")
    except Exception as e:
        print(f"推播發送例外: {e}")

def recursive_find_available_tickets(data):
    available_items = []
    if isinstance(data, dict):
        is_sold_out = None
        for key in ["isSoldOut", "IsSoldOut", "soldOut", "SoldOut"]:
            if key in data and isinstance(data[key], bool):
                is_sold_out = data[key]
                break
        
        if is_sold_out is False:
            name = data.get("name") or data.get("Name") or data.get("priceName") or "可購區域"
            price = data.get("price") or data.get("Price") or ""
            available_items.append(f"• {name} (票價: {price})".strip())
        
        for v in data.values():
            available_items.extend(recursive_find_available_tickets(v))
    elif isinstance(data, list):
        for item in data:
            available_items.extend(recursive_find_available_tickets(item))
    return available_items

def check_once():
    """執行單次檢查，若有票回傳 True，否則回傳 False"""
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"API 請求異常，代碼: {response.status_code}")
            return False

        raw_text = response.text
        try:
            data = response.json()
            available_areas = recursive_find_available_tickets(data)
        except Exception:
            available_areas = []

        fallback_available = ('"IsSoldOut":false' in raw_text.replace(" ", "")) or \
                             ('"isSoldOut":false' in raw_text.replace(" ", ""))

        if available_areas:
            unique_areas = list(set(available_areas))
            detail_msg = "\n".join(unique_areas)
            print(f"[{time.strftime('%H:%M:%S')}] 偵測到釋票: {detail_msg}")
            send_discord_notify(f"🎯 **偵測到以下區域釋出票券！**\n{detail_msg}\n請火速前往手動作答與購票！")
            return True
        elif fallback_available:
            print(f"[{time.strftime('%H:%M:%S')}] 備用判定：偵測到非售罄標籤！")
            send_discord_notify("🎯 **偵測到系統釋出剩餘票券！**\n請立即點擊連結前往確認！")
            return True
        else:
            print(f"[{time.strftime('%H:%M:%S')}] 目前所有區域均售罄。")
            return False
    except Exception as e:
        print(f"爬蟲錯誤: {e}")
        return False

def run_loop():
    # 每次啟動在背景持續運行 9 分鐘（540 秒），每 15 秒檢查一次
    total_duration = 540 
    interval = 15
    start_time = time.time()
    
    print(f"開始高頻監控，將持續運行 {total_duration//60} 分鐘，每 {interval} 秒檢查一次...")
    
    while time.time() - start_time < total_duration:
        found = check_once()
        if found:
            # 偵測到有票後暫緩 45 秒再查，避免同一張票連發好幾次 Discord 訊息
            time.sleep(45)
        else:
            time.sleep(interval)
            
    print("本輪監控結束，等待下一次排程接力。")

if __name__ == "__main__":
    run_loop()
