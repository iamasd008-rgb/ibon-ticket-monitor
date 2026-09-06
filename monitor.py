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

        # 1. 檢查售完字樣
        sold_out_flags = ["已售完", "全數售完", "暫無票券", "全數售罄"]
        is_sold_out = any(flag in page_text for flag in sold_out_flags)

        # 2. 只有在「完全沒有售完字樣」的情況下，才判定為有票
        # 排除常駐的「前往購票」假警報
        if not is_sold_out:
            print("偵測到『售完』標記消失，可能有釋票！發送推播。")
            send_discord_notify(
                "偵測到售罄狀態解除！",
                "頁面目前未顯示售完，可能有退票釋出，請點擊連結手動確認！"
            )
        else:
            print("目前網頁明確標記已售完，不發送通知。")

    except Exception as e:
        print(f"執行爬蟲時發生錯誤: {e}")

if __name__ == "__main__":
    check_ticket_status()
