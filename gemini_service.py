"""Gemini APIによる動画分析・要約・ダイジェスト生成サービス"""

from google import genai
from google.genai import types

from config import Config


# 分類＋要約プロンプト（YouTube URLをGeminiに直接渡す）
CLASSIFY_AND_SUMMARIZE_PROMPT = """あなたはYouTube動画の内容を正確かつ簡潔に要約する専門家です。
このYouTube動画を視聴して3つの作業を行ってください。

━━━━━━━━━━━━━━━━━━
■ 作業1: コンテンツ分類
━━━━━━━━━━━━━━━━━━
この動画の内容を以下の3つのいずれかに分類してください。
迷った場合は NEWS 寄りに判定してください。

【NEWS】新しい情報・最新ニュース
  例: 新サービスのリリース、既存サービスのアップデート、
      業界の最新動向、新機能の発表、法改正、新技術の登場

【HOWTO】作り方・使い方の解説
  例: アプリの作り方、ツールの操作方法、
      プログラミングチュートリアル、設定手順の解説

【GENERAL】一般的な知識・考え方
  例: リーダーシップ論、働き方改革、自己啓発、
      すでに広く知られている情報の再解説

━━━━━━━━━━━━━━━━━━
■ 作業2: キーワード抽出
━━━━━━━━━━━━━━━━━━
この動画の内容を表す重要なキーワードを3〜5個抽出してください。
固有名詞（サービス名、技術名など）を優先してください。

━━━━━━━━━━━━━━━━━━
■ 作業3: 要約
━━━━━━━━━━━━━━━━━━
日本語で以下のフォーマットに従って要約してください。

【概要】
（140文字程度で動画の内容を簡潔にまとめてください）

【重要なポイント】
・ポイント1
・ポイント2
・ポイント3

【アクションアイテム/結論】
（視聴者が取るべきアクションや動画の結論を簡潔に）

━━━━━━━━━━━━━━━━━━
■ 出力形式（厳守）
━━━━━━━━━━━━━━━━━━
必ず以下の順番で出力してください。

1行目: 分類ラベル（例: CATEGORY: NEWS）
2行目: キーワード（カンマ区切り。例: KEYWORDS: Gemini, SVG, AI活用）
3行目以降: 要約
"""


# ダイジェスト（日刊まとめ）プロンプトテンプレート
DIGEST_PROMPT = """あなたは最新のAI・テクノロジー情報をわかりやすくまとめる専門家です。
以下の複数の動画要約を読み、「本日の最新トピック」として
友人や知人に共有するための、読みやすいダイジェストを作成してください。

【厳守ルール】
- 情報源（チャンネル名、YouTube、動画など）には一切言及しないこと
- 「Notionに保存しました」「まとめました」等のシステム報告は書かないこと
- あたかも自分で最新情報を集めてまとめたかのような自然なトーンで書くこと
- トピックごとに番号（①②③...）付きで簡潔にまとめること
- 各トピックは2〜3行程度で要点だけ伝えること
- 最後に親しみのある一言（「気になるものがあれば聞いてね！」等）を添えること
- 全体で1000文字以内に収めること

【出力フォーマット】
📰 {today} AI・テクノロジー最新トピック

① （トピック名）
（2〜3行の説明）

② （トピック名）
（2〜3行の説明）

💡 （親しみのある一言）

---
以下が各動画の要約です:

{summaries}
"""


def analyze_video(video_url: str) -> dict:
    """YouTube動画をGeminiで直接分析する（分類+要約）。

    youtube-transcript-apiを使わず、GeminiにYouTube URLを直接渡して
    動画の内容を分析します。IPブロックのリスクがありません。

    Args:
        video_url: YouTube動画のURL。

    Returns:
        {"category": "NEWS"|"HOWTO"|"GENERAL", "summary": str}
    """
    client = genai.Client(api_key=Config.GEMINI_API_KEY)

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=[
            types.Part.from_uri(file_uri=video_url, mime_type="video/*"),
            CLASSIFY_AND_SUMMARIZE_PROMPT,
        ],
    )

    return _parse_classification_response(response.text)


def _parse_classification_response(text: str) -> dict:
    """Geminiの分類+キーワード+要約レスポンスをパースする。

    1行目: CATEGORY: NEWS
    2行目: KEYWORDS: Gemini, SVG, AI活用
    3行目以降: 要約テキスト

    Args:
        text: Geminiのレスポンステキスト。

    Returns:
        {"category": str, "keywords": list[str], "summary": str}
    """
    lines = text.strip().split("\n")

    category = "NEWS"  # デフォルト
    keywords = []
    summary_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip().upper()
        if stripped.startswith("CATEGORY:"):
            cat_value = line.strip().split(":", 1)[1].strip().upper()
            if "HOWTO" in cat_value:
                category = "HOWTO"
            elif "GENERAL" in cat_value:
                category = "GENERAL"
            else:
                category = "NEWS"
            summary_start = i + 1
        elif stripped.startswith("KEYWORDS:"):
            kw_value = line.strip().split(":", 1)[1].strip()
            keywords = [k.strip() for k in kw_value.split(",") if k.strip()]
            summary_start = i + 1
        else:
            # 分類・キーワード行以外が出てきたら要約の開始
            if summary_start <= i and (category != "NEWS" or keywords):
                break

    summary = "\n".join(lines[summary_start:]).strip()
    if not summary:
        summary = text  # パース失敗時は全文を要約とする

    return {"category": category, "keywords": keywords, "summary": summary}


def generate_daily_digest(summaries: list[dict]) -> str:
    """複数の動画要約から日刊ダイジェストを生成する。

    Args:
        summaries: 動画要約のリスト。各要素は {"title": str, "summary": str}。

    Returns:
        日刊ダイジェストテキスト。
    """
    from datetime import datetime, timezone, timedelta

    client = genai.Client(api_key=Config.GEMINI_API_KEY)

    # 今日の日付を取得（日本時間）
    jst = timezone(timedelta(hours=9))
    today = datetime.now(jst).strftime("%m/%d")

    # 要約を連結
    combined = ""
    for i, s in enumerate(summaries, 1):
        combined += f"--- 動画{i}: {s['title']} ---\n{s['summary']}\n\n"

    prompt = DIGEST_PROMPT.format(summaries=combined, today=today)

    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents=prompt,
    )

    return response.text
