"""YouTube Intelligence & Automation Agent — メインオーケストレーター"""

import argparse
import sys
import time
import traceback

from config import Config
from youtube_service import extract_video_id, get_video_info, get_latest_videos
from gemini_service import analyze_video, generate_daily_digest
from line_service import send_digest
from notion_service import create_page


def process_video(video_url: str, dry_run: bool = False) -> dict | None:
    """単一動画の処理パイプライン。

    1. 動画情報を取得（YouTube Data API）
    2. Geminiに直接URLを渡して分類+要約（字幕スクレイピング不要）
    3. Notionに保存（サムネイル・チャンネル名・ジャンル付き）

    Args:
        video_url: YouTube動画のURLまたは動画ID。
        dry_run: Trueの場合、Notionへの送信をスキップ。

    Returns:
        NEWS系の場合: {"title": str, "summary": str}（ダイジェスト素材）
        HOWTO/GENERAL系またはエラーの場合: None
    """
    print(f"\n{'═' * 50}")
    print(f"🎬 処理開始: {video_url}")
    print(f"{'═' * 50}")

    # --- Step 1: 動画ID抽出 ---
    try:
        video_id = extract_video_id(video_url)
        print(f"✅ 動画ID: {video_id}")
    except ValueError as e:
        print(f"❌ {e}")
        return None

    # --- Step 2: 動画情報取得（YouTube Data API） ---
    try:
        video_info = get_video_info(video_id)
        print(f"✅ タイトル: {video_info['title']}")
        print(f"   チャンネル: {video_info['channel_title']}")
        print(f"   公開日: {video_info['published_at']}")
    except Exception as e:
        print(f"❌ 動画情報の取得に失敗: {e}")
        return None

    # --- Step 3: Geminiで直接分析（分類+要約） ---
    full_url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        print(f"🔍 Geminiで動画を分析中...")
        result = analyze_video(full_url)
        category = result["category"]
        summary = result["summary"]
        print(f"✅ 分類: {category}")
        print(f"\n{'─' * 40}")
        print("📝 要約結果:")
        print(f"{'─' * 40}")
        print(summary)
        print(f"{'─' * 40}\n")
    except Exception as e:
        print(f"❌ Gemini分析に失敗: {type(e).__name__}: {e}")
        return None

    # --- Step 4: Notion保存（全分類、サムネイル・チャンネル名・ジャンル付き） ---
    if dry_run:
        print("🔸 [DRY-RUN] Notionページ作成をスキップしました")
    else:
        try:
            create_page(
                title=video_info["title"],
                url=full_url,
                summary=summary,
                published_date=video_info.get("published_at", ""),
                thumbnail_url=video_info.get("thumbnail_url", ""),
                channel_title=video_info.get("channel_title", ""),
                genre=category,
            )
        except Exception as e:
            print(f"⚠️ Notionページ作成でエラーが発生: {type(e).__name__}: {e}")

    print(f"\n{'═' * 50}")
    print(f"🎉 処理完了! (分類: {category})")
    print(f"{'═' * 50}\n")

    # NEWS系のみダイジェスト素材として返す
    if category == "NEWS":
        return {"title": video_info["title"], "summary": summary}
    else:
        print(f"ℹ️ {category}のためLINEダイジェストには含めません")
        return None


def process_channel(channel_id: str, count: int = 5, dry_run: bool = False) -> None:
    """チャンネルの最新動画を処理する。

    全動画をNotionに保存した後、NEWS系のみでダイジェストを生成してLINEに送信。

    Args:
        channel_id: YouTubeチャンネルID。
        count: 取得する動画数。
        dry_run: Trueの場合、LINE/Notionへの送信をスキップ。
    """
    print(f"\n📺 チャンネル {channel_id} の最新 {count} 件を取得中...")

    try:
        videos = get_latest_videos(channel_id, max_results=count)
    except Exception as e:
        print(f"❌ チャンネルの動画取得に失敗: {e}")
        return

    if not videos:
        print("⚠️ 動画が見つかりませんでした")
        return

    print(f"📋 {len(videos)} 件の動画を処理します\n")

    # --- 各動画を処理してNotionに保存、NEWS系の要約を収集 ---
    news_results = []
    for i, video in enumerate(videos, 1):
        print(f"\n--- [{i}/{len(videos)}] ---")
        video_url = f"https://www.youtube.com/watch?v={video['video_id']}"
        result = process_video(video_url, dry_run=dry_run)
        if result:
            news_results.append(result)

        # 動画間に3秒待機（API負荷軽減）
        if i < len(videos):
            print("⏳ 3秒待機中...")
            time.sleep(3)

    print(f"\n📊 結果: NEWS {len(news_results)} 件 / 全 {len(videos)} 件")

    # --- NEWS系のみでダイジェスト生成 & LINE送信 ---
    if news_results and not dry_run:
        print(f"\n📰 ダイジェストを生成中（{len(news_results)} 件のNEWS）...")
        try:
            digest = generate_daily_digest(news_results)
            print(f"\n{'─' * 40}")
            print("📰 ダイジェスト:")
            print(f"{'─' * 40}")
            print(digest)
            print(f"{'─' * 40}\n")

            send_digest(digest)
        except Exception as e:
            print(f"⚠️ ダイジェスト生成/送信でエラーが発生: {type(e).__name__}: {e}")
    elif news_results and dry_run:
        print("🔸 [DRY-RUN] ダイジェスト生成・LINE送信をスキップしました")
    else:
        print("ℹ️ NEWS系の動画がなかったため、ダイジェストは生成しません")


def main():
    """CLIエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="YouTube Intelligence & Automation Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 単一動画を処理（Notionに保存のみ）
  python main.py --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

  # チャンネルの最新2件を処理（Notion保存 + LINEダイジェスト）
  python main.py --channel "UCxxxxxxx" --count 2

  # ドライランモード（API送信をスキップ）
  python main.py --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ" --dry-run
        """,
    )
    parser.add_argument(
        "--url",
        type=str,
        help="処理するYouTube動画のURL",
    )
    parser.add_argument(
        "--channel",
        type=str,
        help="監視するYouTubeチャンネルID（カンマ区切りで複数指定可能）",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="チャンネルモードで取得する動画数（デフォルト: 5）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="LINE通知とNotion保存をスキップ（テスト用）",
    )

    args = parser.parse_args()

    if not args.url and not args.channel:
        parser.error("--url または --channel のいずれかを指定してください")

    # 必要なAPIキーの検証
    if args.dry_run:
        required_keys = ["YOUTUBE_API_KEY", "GEMINI_API_KEY"]
    else:
        required_keys = None  # 全キーを検証

    if not Config.validate(required_keys=required_keys):
        sys.exit(1)

    try:
        if args.url:
            result = process_video(args.url, dry_run=args.dry_run)
            sys.exit(0 if result is not None else 1)
        elif args.channel:
            # カンマ区切りで複数のチャンネルIDを処理可能にする
            channels = [c.strip() for c in args.channel.split(",") if c.strip()]
            for channel_id in channels:
                process_channel(channel_id, count=args.count, dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n\n⚠️ 処理を中断しました")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
