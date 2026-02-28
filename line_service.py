"""LINE Messaging APIによる通知サービス"""

import requests

from config import Config


def send_digest(digest_text: str, image_url: str = "") -> bool:
    """日刊ダイジェストをLINEに送信する。

    テキストダイジェストに加え、インフォグラフィック画像も送信可能。

    Args:
        digest_text: Geminiが生成したダイジェストテキスト。
        image_url: インフォグラフィック画像の公開URL（省略可）。

    Returns:
        送信成功ならTrue。
    """
    # LINE Messaging APIの5000文字制限対応
    if len(digest_text) > 5000:
        digest_text = digest_text[:4990] + "\n..."

    messages = []

    # 画像があれば先に追加（LINEでは最大5メッセージまで同時送信可能）
    if image_url:
        messages.append({
            "type": "image",
            "originalContentUrl": image_url,
            "previewImageUrl": image_url,
        })

    messages.append({"type": "text", "text": digest_text})

    # LINE Messaging API Push Message
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {Config.LINE_CHANNEL_ACCESS_TOKEN}",
    }
    payload = {
        "to": Config.LINE_USER_ID,
        "messages": messages,
    }

    response = requests.post(url, json=payload, headers=headers, timeout=30)

    if response.status_code == 200:
        print("✅ LINEダイジェストを送信しました")
        return True
    else:
        print(f"❌ LINEダイジェストの送信に失敗しました: {response.status_code}")
        print(f"   レスポンス: {response.text}")
        return False
