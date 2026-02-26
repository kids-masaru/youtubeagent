"""環境変数の読み込みと設定管理"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()


class Config:
    """全APIキーと設定を一元管理するクラス"""

    # YouTube Data API
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")

    # Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # LINE Messaging API
    LINE_CHANNEL_ACCESS_TOKEN: str = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
    LINE_USER_ID: str = os.getenv("LINE_USER_ID", "")

    # Notion API
    NOTION_TOKEN: str = os.getenv("NOTION_TOKEN", "")
    NOTION_DATABASE_ID: str = os.getenv("NOTION_DATABASE_ID", "")

    @classmethod
    def validate(cls, required_keys: list[str] | None = None) -> bool:
        """必要なAPIキーがすべて設定されているか検証する。

        Args:
            required_keys: 検証するキー名のリスト。Noneの場合は全キーを検証。

        Returns:
            すべてのキーが設定されていれば True。
        """
        all_keys = {
            "YOUTUBE_API_KEY": cls.YOUTUBE_API_KEY,
            "GEMINI_API_KEY": cls.GEMINI_API_KEY,
            "LINE_CHANNEL_ACCESS_TOKEN": cls.LINE_CHANNEL_ACCESS_TOKEN,
            "LINE_USER_ID": cls.LINE_USER_ID,
            "NOTION_TOKEN": cls.NOTION_TOKEN,
            "NOTION_DATABASE_ID": cls.NOTION_DATABASE_ID,
        }

        keys_to_check = (
            {k: all_keys[k] for k in required_keys if k in all_keys}
            if required_keys
            else all_keys
        )

        missing = [k for k, v in keys_to_check.items() if not v]

        if missing:
            print("❌ 以下のAPIキーが .env に設定されていません:", file=sys.stderr)
            for key in missing:
                print(f"   - {key}", file=sys.stderr)
            print(
                "\n💡 .env.example をコピーして .env を作成し、各キーを設定してください。",
                file=sys.stderr,
            )
            return False

        return True
