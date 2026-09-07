import os
import requests
import json

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
    """
    遞迴掃描 JSON 內所有的票種/區域節點，尋找非售完的票券
    """
    available_items = []
    
    if isinstance(data, dict):
        # 檢查常見代表「售罄」與「名稱」的欄位
        is_sold_out = None
        for key in ["isSoldOut", "IsSoldOut", "soldOut", "SoldOut"]:
            if key in data and isinstance(data[key], bool):
                is_sold_out = data[key]
                break
        
        # 如果該節點有明確標記「未售罄」
        if is_sold_out is False:
            name = data.get("name") or data.get("Name") or data.get("priceName") or "可購區域"
            price = data.get("price") or data.get("Price") or ""
            available_items.append(f"• {name} (票價: {price})".strip())
        
        # 繼續往下層子節點遞迴搜尋
        for v in data.values():
            available_items.extend(recursive_find_available_tickets(v))
            
    elif isinstance(data, list):
        for item in data:
            available_items.extend(recursive_find_available_tickets(item))
            
    return available_items

def check_ticket_status():
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            print(f"API 請求失敗，HTTP 代碼: {response.status_code}")
            return

        raw_text = response.text
        print(f"API 回傳長度: {len(raw_text)}")

        # 1. 嘗試以標準 JSON 解析
        try:
            data = response.json()
            available_areas = recursive_find_available_tickets(data)
        except Exception:
            available_areas = []

        # 2. 容錯機制：如果 JSON 結構異常，改用精準正則關鍵字比對
        # 只要出現 "IsSoldOut": false 或 "isSoldOut": false 就認定有票
        fallback_available = ('"IsSoldOut":false' in raw_text.replace(" ", "")) or \
                             ('"isSoldOut":false' in raw_text.replace(" ", ""))

        if available_areas:
            unique_areas = list(set(available_areas))
            detail_msg = "\n".join(unique_areas)
            print(f"偵測到有區域釋票: {detail_msg}")
            send_discord_notify(f"🎯 **偵測到以下區域釋出票券！**\n{detail_msg}\n請火速前往手動作答與購票！")
            
        elif fallback_available:
            print("備用語法判定：偵測到非售罄標籤！")
            send_discord_notify("🎯 **偵測到系統釋出剩餘票券！**\n請立即點擊連結前往確認！")
            
        else:
            print("目前所有區域均為售完狀態，持續監控中。")

    except Exception as e:
        print(f"執行爬蟲時發生錯誤: {e}")

if __name__ == "__main__":
    check_ticket_status()
