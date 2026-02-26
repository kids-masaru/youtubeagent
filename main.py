"""YouTube Intelligence & Automation Agent — メインオーケストレーター"""

import argparse
import sys
import traceback

from config import Config
from youtube_service import extract_video_id, get_video_info, get_transcript, get_latest_videos
from gemini_service import summarize_transcript
from line_service import send_notification
from notion_service import create_page


def process_video(video_url: str, dry_run: bool = False) -> bool:
    """単一動画の処理パイプライン。

    1. 動画情報を取得
    2. 字幕を取得
    3. Geminiで要約
    4. LINE通知
    5. Notionに保存

    Args:
        video_url: YouTube動画のURLまたは動画ID。
        dry_run: Trueの場合、LINE/Notionへの送信をスキップしログのみ出力。

    Returns:
        処理成功ならTrue。
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
        return False

    # --- Step 2: 動画情報取得 ---
    try:
        video_info = get_video_info(video_id)
        print(f"✅ タイトル: {video_info['title']}")
        print(f"   チャンネル: {video_info['channel_title']}")
        print(f"   公開日: {video_info['published_at']}")
    except Exception as e:
        print(f"❌ 動画情報の取得に失敗: {e}")
        return False

    # --- Step 3: 字幕取得 ---
    try:
        transcript = get_transcript(video_id)
        print(f"✅ 字幕取得完了 ({len(transcript)} 文字)")
    except Exception as e:
        print(f"❌ 字幕の取得に失敗: {e}")
        return False

    # --- Step 4: Gemini要約 ---
    try:
        summary = summarize_transcript(transcript)
        print(f"\n{'─' * 40}")
        print("📝 要約結果:")
        print(f"{'─' * 40}")
        print(summary)
        print(f"{'─' * 40}\n")
    except Exception as e:
        print(f"❌ 要約の生成に失敗: {e}")
        return False

    # --- Step 5: LINE通知 ---
    full_url = f"https://www.youtube.com/watch?v={video_id}"
    if dry_run:
        print("🔸 [DRY-RUN] LINE通知をスキップしました")
    else:
        try:
            line_result = send_notification(
                title=video_info["title"],
                summary=summary,
                video_url=full_url,
                thumbnail_url=video_info.get("thumbnail_url", ""),
            )
            if not line_result:
                print("⚠️ LINE通知の送信に問題がありました")
        except Exception as e:
            print(f"⚠️ LINE通知でエラーが発生: {e}")

    # --- Step 6: Notion保存 ---
    if dry_run:
        print("🔸 [DRY-RUN] Notionページ作成をスキップしました")
    else:
        try:
            create_page(
                title=video_info["title"],
                url=full_url,
                summary=summary,
                published_date=video_info.get("published_at", ""),
            )
        except Exception as e:
            print(f"⚠️ Notionページ作成でエラーが発生: {e}")

    print(f"\n{'═' * 50}")
    print("🎉 処理完了!")
    print(f"{'═' * 50}\n")
    return True


def process_channel(channel_id: str, count: int = 5, dry_run: bool = False) -> None:
    """チャンネルの最新動画を処理する。

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

    success_count = 0
    for i, video in enumerate(videos, 1):
        print(f"\n--- [{i}/{len(videos)}] ---")
        video_url = f"https://www.youtube.com/watch?v={video['video_id']}"
        if process_video(video_url, dry_run=dry_run):
            success_count += 1

    print(f"\n📊 結果: {success_count}/{len(videos)} 件の処理に成功しました")


def main():
    """CLIエントリーポイント"""
    parser = argparse.ArgumentParser(
        description="YouTube Intelligence & Automation Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 単一動画を処理
  python main.py --url "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

  # チャンネルの最新5件を処理
  python main.py --channel "UCxxxxxxx" --count 5

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
        help="監視するYouTubeチャンネルID",
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
            success = process_video(args.url, dry_run=args.dry_run)
            sys.exit(0 if success else 1)
        elif args.channel:
            process_channel(args.channel, count=args.count, dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n\n⚠️ 処理を中断しました")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 予期しないエラーが発生しました: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
