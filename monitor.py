import os
import requests
from bs4 import BeautifulSoup

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
TARGET_URL = "https://ticket.ibon.com.tw/ActivityInfo/Details/39903"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7"
}

def send_discord_notify(title, message):
    if not DISCORD_WEBHOOK_URL:
        print("未設定 DISCORD_WEBHOOK_URL，略過推播。")
        return
        
    payload = {
        "content": f"🚨 **【ibon 票況變更通知】**\n**{title}**\n{message}\n🔗 **快速購票連結**: {TARGET_URL}"
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
        response = requests.get(TARGET_URL, headers=HEADERS, timeout=15)
        response.encoding = "utf-8"

        if response.status_code != 200:
            print(f"網頁請求失敗，代碼: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, "html.parser")
        page_text = soup.get_text()

        sold_out_flags = ["已售完", "全數售完", "暫無票券"]
        is_sold_out = any(flag in page_text for flag in sold_out_flags)

        buy_button_flags = ["立即購票", "前往購票", "尚有票券"]
        has_buy_button = any(flag in page_text for flag in buy_button_flags)

        print(f"檢查結果 -> 是否標記售完: {is_sold_out} | 是否有購票字樣: {has_buy_button}")

        if not is_sold_out or has_buy_button:
            print("偵測到可能有票，發送 Discord 通知！")
            send_discord_notify(
                "偵測到活動頁面開放購票或有釋票！",
                "頁面目前顯示非售完狀態，請火速手動前往確認並作答！"
            )
        else:
            print("目前確認全數售完，持續監控中。")

    except Exception as e:
        print(f"執行爬蟲時發生錯誤: {e}")

if __name__ == "__main__":
    check_ticket_status()
