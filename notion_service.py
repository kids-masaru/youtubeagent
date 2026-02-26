"""Notion APIによるデータベースページ作成サービス"""

from notion_client import Client

from config import Config


def create_page(
    title: str,
    url: str,
    summary: str,
    published_date: str,
) -> dict:
    """Notionデータベースに新しいページを作成する。

    Args:
        title: 動画タイトル。
        url: 動画URL。
        summary: Gemini要約テキスト。
        published_date: 公開日（ISO 8601形式、例: "2025-01-15T00:00:00Z"）。

    Returns:
        作成されたページのレスポンス辞書。
    """
    notion = Client(auth=Config.NOTION_TOKEN)

    # 日付を YYYY-MM-DD 形式に変換
    date_str = published_date[:10] if published_date else ""

    # 要約テキストをNotion Rich Text制限（2000文字）に対応
    summary_chunks = _split_rich_text(summary, max_length=2000)

    properties = {
        "タイトル": {
            "title": [
                {
                    "text": {
                        "content": title[:2000],  # Title制限
                    }
                }
            ]
        },
        "URL": {
            "url": url,
        },
        "投稿日": {
            "date": {
                "start": date_str,
            }
            if date_str
            else None,
        },
    }

    # 投稿日がない場合はプロパティを除外
    if not date_str:
        del properties["投稿日"]

    # ページを作成（要約はページ本文のchildren blocksとして追加）
    page = notion.pages.create(
        parent={"database_id": Config.NOTION_DATABASE_ID},
        properties=properties,
        children=_build_summary_blocks(summary),
    )

    # 要約プロパティも更新（Rich TextプロパティがDBにある場合）
    try:
        notion.pages.update(
            page_id=page["id"],
            properties={
                "要約": {
                    "rich_text": [
                        {"text": {"content": chunk}} for chunk in summary_chunks
                    ]
                },
            },
        )
    except Exception:
        # 「要約」プロパティがデータベースにない場合はスキップ
        # （本文には既に追加済み）
        pass

    print(f"✅ Notionページを作成しました: {page.get('url', page['id'])}")
    return page


def _split_rich_text(text: str, max_length: int = 2000) -> list[str]:
    """テキストをNotionのRich Text制限に合わせて分割する。"""
    chunks = []
    while text:
        chunks.append(text[:max_length])
        text = text[max_length:]
    return chunks if chunks else [""]


def _build_summary_blocks(summary: str) -> list[dict]:
    """要約テキストからNotionのブロック要素を構築する。

    行ごとに適切なブロックタイプに変換する。
    """
    blocks = []
    lines = summary.split("\n")

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # 見出し行（【...】で始まる行）
        if stripped.startswith("【") and "】" in stripped:
            blocks.append(
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [{"text": {"content": stripped[:2000]}}]
                    },
                }
            )
        # 箇条書き（・で始まる行）
        elif stripped.startswith("・") or stripped.startswith("- "):
            content = stripped.lstrip("・- ").strip()
            blocks.append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {
                        "rich_text": [{"text": {"content": content[:2000]}}]
                    },
                }
            )
        # 区切り線
        elif stripped == "---" or stripped == "─" * len(stripped):
            blocks.append(
                {
                    "object": "block",
                    "type": "divider",
                    "divider": {},
                }
            )
        # 通常テキスト
        else:
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": stripped[:2000]}}]
                    },
                }
            )

    return blocks
