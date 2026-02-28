"""Gemini Imagenによるインフォグラフィック画像生成サービス"""

import os
import tempfile
from datetime import datetime, timezone, timedelta

from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

from config import Config


# 画像生成プロンプト
INFOGRAPHIC_PROMPT = """以下のAI・テクノロジーニュースダイジェストの内容を、
インフォグラフィック画像にまとめてください。

【スタイル指定 - 添付の参考画像の雰囲気に近づけてください】
- 白背景ベースでクリーンな印象
- パステルカラー（薄いグリーン、ブルー、オレンジ等）のカード型セクションで情報をブロック分け
- 各トピックにはシンプルなアイコンやイラストを添える
- 表・箇条書きを組み合わせた情報整理
- 日本語で表記
- タイトルは大きく上部に配置
- 全体的にシンプル・わかりやすい・清潔感のあるデザイン
- 縦長レイアウト（スマホ閲覧に最適化）

【タイトル】
📰 {today} AI・テクノロジー最新トピック

【トピック内容】
{digest_text}
"""


def generate_infographic(digest_text: str) -> str | None:
    """ダイジェスト内容からインフォグラフィック画像を生成する。

    Gemini Imagenを使用し、参考画像のスタイルに近いインフォグラフィックを生成。

    Args:
        digest_text: ダイジェストのテキスト内容。

    Returns:
        生成された画像のローカルファイルパス。生成失敗時はNone。
    """
    client = genai.Client(api_key=Config.GEMINI_API_KEY)

    # 今日の日付（日本時間）
    jst = timezone(timedelta(hours=9))
    today = datetime.now(jst).strftime("%m/%d")

    prompt = INFOGRAPHIC_PROMPT.format(today=today, digest_text=digest_text)

    # 参考画像を読み込む
    reference_path = os.path.join(os.path.dirname(__file__), "assets", "reference_style.png")
    parts = []

    if os.path.exists(reference_path):
        print("🎨 参考画像を読み込み中...")
        with open(reference_path, "rb") as f:
            ref_data = f.read()
        parts.append(types.Part.from_bytes(data=ref_data, mime_type="image/png"))

    parts.append(prompt)

    try:
        print("🖼️ インフォグラフィックを生成中...")
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=parts,
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # レスポンスから画像を抽出
        for part in response.candidates[0].content.parts:
            if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                # 一時ファイルに保存
                tmp_dir = tempfile.gettempdir()
                timestamp = datetime.now(jst).strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(tmp_dir, f"infographic_{timestamp}.png")

                image = Image.open(BytesIO(part.inline_data.data))
                image.save(output_path, "PNG")

                print(f"✅ インフォグラフィック生成完了: {output_path}")
                return output_path

        print("⚠️ レスポンスに画像が含まれていませんでした")
        return None

    except Exception as e:
        print(f"⚠️ インフォグラフィック生成でエラー: {type(e).__name__}: {e}")
        return None
