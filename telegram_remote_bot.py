# -*- coding: utf-8 -*-
"""
텔레그램 원격 제어 & 알림 봇 (Telegram Remote Controller)
스마트폰 텔레그램을 통해 노트북을 원격 제어하고, 스크래핑 상태 확인,
스크래핑 재개, 브랜드 분석 실행, 화면 캡처, Git 푸시 등을 수행합니다.
"""

import os
import sys
import time
import glob
import subprocess
import requests
import json

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = r"c:\Users\passp\Desktop\univercity\4-2\taobao_jackets"
DOWNLOAD_DIR = os.path.join(BASE_DIR, "downloaded_jackets")
CONFIG_FILE = os.path.join(BASE_DIR, "telegram_config.json")

def load_telegram_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "bot_token": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        "chat_id": os.environ.get("TELEGRAM_CHAT_ID", "")
    }

def send_message(bot_token, chat_id, text):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"[-] Telegram 전송 실패: {e}")

def send_photo(bot_token, chat_id, photo_path, caption=""):
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    try:
        with open(photo_path, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": chat_id, "caption": caption}
            requests.post(url, data=data, files=files, timeout=20)
    except Exception as e:
        print(f"[-] Telegram 사진 전송 실패: {e}")

def capture_screen(save_path):
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        img.save(save_path, "JPEG", quality=75)
        return True
    except Exception as e:
        print(f"[-] 화면 캡처 실패: {e}")
        return False

def get_scraping_status():
    if not os.path.exists(DOWNLOAD_DIR):
        return "📁 다운로드 폴더 없음"
    
    folders = [f for f in glob.glob(os.path.join(DOWNLOAD_DIR, "item_*")) if os.path.isdir(f)]
    total_photos = len(glob.glob(os.path.join(DOWNLOAD_DIR, "item_*", "*.jpg")))
    
    # 50장 이상 완료된 상품과 미완료 상품 구분
    completed = []
    in_progress = []
    for f in folders:
        cnt = len(glob.glob(os.path.join(f, "*.jpg")))
        name = os.path.basename(f)
        if cnt >= 50:
            completed.append(f"{name} ({cnt}장)")
        else:
            in_progress.append(f"{name} ({cnt}장)")

    msg = f"📊 *[타오바오 자켓 수집 현황]*\n\n"
    msg += f"• 수집 대상 폴더: 총 {len(folders)}개\n"
    msg += f"• 100% 바닥 수집 완료: *{len(completed)}개*\n"
    msg += f"• 총 다운로드 사진: *{total_photos:,}장*\n\n"
    if in_progress:
        msg += f"⚠️ *진행 중/캡챠 대기*: {', '.join(in_progress)}\n"
    return msg

def run_bot():
    cfg = load_telegram_config()
    token = cfg.get("bot_token")
    admin_chat_id = cfg.get("chat_id")

    if not token:
        print("\n" + "="*60)
        print("🤖 [텔레그램 봇 설정 필요]")
        print("1. 텔레그램에서 @BotFather 검색 -> /newbot 으로 봇 생성")
        print("2. 발급받은 API 토큰을 telegram_config.json 에 저장하세요.")
        print(f'   예시: {{"bot_token": "YOUR_TOKEN", "chat_id": "YOUR_CHAT_ID"}}')
        print("="*60 + "\n")
        return

    print(f"[*] 텔레그램 봇이 활성화되었습니다. 스마트폰에서 명령어를 전송하세요...")
    last_update_id = 0

    while True:
        try:
            url = f"https://api.telegram.org/bot{token}/getUpdates?offset={last_update_id + 1}&timeout=30"
            resp = requests.get(url, timeout=40)
            if resp.status_code != 200:
                time.sleep(3)
                continue

            updates = resp.json().get("result", [])
            for u in updates:
                last_update_id = u["update_id"]
                msg = u.get("message", {})
                chat_id = msg.get("chat", {}).get("id")
                text = msg.get("text", "").strip()

                if not text or not chat_id:
                    continue

                print(f"[텔레그램 수신] chat_id={chat_id}: {text}")

                if text in ["/start", "/help"]:
                    help_text = (
                        "🧥 *타오바오 자켓 원격 제어 봇*\n\n"
                        "• `/status` : 현재 수집 진행률 & 사진 장수 확인\n"
                        "• `/screen` : 현재 노트북 화면 캡처 전송 (캡챠 확인용)\n"
                        "• `/scrape` : 스크래핑 계속 진행\n"
                        "• `/brand` : OpenCode Go 브랜드 판독 실행\n"
                        "• `/git` : 깃허브(finder)에 최신 데이터 푸시\n"
                    )
                    send_message(token, chat_id, help_text)

                elif text == "/status":
                    send_message(token, chat_id, get_scraping_status())

                elif text == "/screen":
                    send_message(token, chat_id, "📸 화면을 캡처하는 중입니다...")
                    screen_path = os.path.join(BASE_DIR, "current_screen.jpg")
                    if capture_screen(screen_path):
                        send_photo(token, chat_id, screen_path, caption="현재 노트북 화면")
                    else:
                        send_message(token, chat_id, "화면 캡처 실패")

                elif text == "/scrape":
                    send_message(token, chat_id, "🚀 스크래핑을 백그라운드에서 재개합니다...")
                    subprocess.Popen([sys.executable, os.path.join(BASE_DIR, "taobao_jacket_pipeline.py")], cwd=BASE_DIR)

                elif text == "/brand":
                    send_message(token, chat_id, "🧠 OpenCode Go 브랜드 판독을 시작합니다...")
                    subprocess.Popen([sys.executable, os.path.join(BASE_DIR, "opencode_jacket_analyzer.py")], cwd=BASE_DIR)

                elif text == "/git":
                    send_message(token, chat_id, "📦 Git 커밋 및 푸시 진행 중...")
                    cmd = 'git add . && git commit -m "Auto update from Telegram" && git push origin main'
                    out = subprocess.getoutput(cmd)
                    send_message(token, chat_id, f"```\n{out[:500]}\n```")

        except Exception as e:
            print(f"[-] 봇 루프 오류: {e}")
            time.sleep(3)

if __name__ == "__main__":
    run_bot()
