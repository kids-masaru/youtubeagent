"""LINE Messaging APIによる通知サービス"""

import requests

from config import Config


def send_notification(
    title: str,
    summary: str,
    video_url: str,
    thumbnail_url: str = "",
) -> bool:
    """LINE Messaging APIのPush Messageで通知を送信する。

    Args:
        title: 動画タイトル。
        summary: Gemini要約テキスト。
        video_url: 動画URL。
        thumbnail_url: サムネイルURL（オプション）。

    Returns:
        送信成功ならTrue。
    """
    # メッセージ本文を組み立て
    text_body = (
        f"🎬 {title}\n"
        f"{'─' * 20}\n"
        f"{summary}\n"
        f"{'─' * 20}\n"
        f"🔗 {video_url}"
    )

    messages = []

    # サムネイル画像メッセージ（あれば先に送信）
    if thumbnail_url:
        messages.append(
            {
                "type": "image",
                "originalContentUrl": thumbnail_url,
                "previewImageUrl": thumbnail_url,
            }
        )

    # テキストメッセージ（LINE Messaging APIの5000文字制限対応）
    if len(text_body) > 5000:
        text_body = text_body[:4990] + "\n..."

    messages.append({"type": "text", "text": text_body})

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
        print("✅ LINE通知を送信しました")
        return True
    else:
        print(f"❌ LINE通知の送信に失敗しました: {response.status_code}")
        print(f"   レスポンス: {response.text}")
        return False
