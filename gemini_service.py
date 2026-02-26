"""Gemini APIによる字幕要約サービス"""

from google import genai

from config import Config

# 要約プロンプトテンプレート
SUMMARY_PROMPT = """あなたはYouTube動画の内容を正確かつ簡潔に要約する専門家です。
以下のYouTube動画の字幕テキストを分析し、日本語で以下のフォーマットに厳密に従って要約してください。

【概要】
（140文字程度で動画の内容を簡潔にまとめてください）

【重要なポイント】
・ポイント1
・ポイント2
・ポイント3

【アクションアイテム/結論】
（視聴者が取るべきアクションや動画の結論を簡潔にまとめてください）

---
以下が字幕テキストです:

{transcript}
"""


def summarize_transcript(transcript: str) -> str:
    """字幕テキストをGemini APIで要約する。

    Args:
        transcript: YouTube動画の字幕テキスト。

    Returns:
        フォーマットされた要約テキスト。
    """
    client = genai.Client(api_key=Config.GEMINI_API_KEY)

    # 字幕が長すぎる場合は先頭を切り詰める（Gemini 2.0 Flashのコンテキスト上限考慮）
    max_chars = 100_000
    if len(transcript) > max_chars:
        transcript = transcript[:max_chars]
        transcript += "\n\n（※字幕テキストが長いため、途中までを使用しています）"

    prompt = SUMMARY_PROMPT.format(transcript=transcript)

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
    )

    return response.text
