"""YouTube動画情報取得サービス"""

import re
from urllib.parse import urlparse, parse_qs

from googleapiclient.discovery import build

from config import Config


def extract_video_id(url: str) -> str:
    """YouTube URLから動画IDを抽出する。

    対応形式:
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://www.youtube.com/embed/VIDEO_ID
        - https://www.youtube.com/shorts/VIDEO_ID

    Args:
        url: YouTube動画のURL。

    Returns:
        動画ID文字列。

    Raises:
        ValueError: URLから動画IDを抽出できない場合。
    """
    # 直接IDが渡された場合（11文字の英数字+ハイフン+アンダースコア）
    if re.match(r"^[A-Za-z0-9_-]{11}$", url):
        return url

    parsed = urlparse(url)

    # youtu.be/VIDEO_ID
    if parsed.hostname in ("youtu.be",):
        video_id = parsed.path.lstrip("/")
        if video_id:
            return video_id.split("/")[0]

    # youtube.com/watch?v=VIDEO_ID
    if parsed.hostname in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        if parsed.path == "/watch":
            qs = parse_qs(parsed.query)
            if "v" in qs:
                return qs["v"][0]

        # /embed/VIDEO_ID or /shorts/VIDEO_ID
        match = re.match(r"^/(embed|shorts|v)/([A-Za-z0-9_-]+)", parsed.path)
        if match:
            return match.group(2)

    raise ValueError(f"YouTube動画IDを抽出できません: {url}")


def get_video_info(video_id: str) -> dict:
    """YouTube Data APIで動画のメタデータを取得する。

    Args:
        video_id: YouTube動画ID。

    Returns:
        動画情報の辞書:
            - title: 動画タイトル
            - published_at: 公開日 (ISO 8601形式)
            - thumbnail_url: サムネイルURL
            - channel_title: チャンネル名
    """
    youtube = build("youtube", "v3", developerKey=Config.YOUTUBE_API_KEY)

    response = (
        youtube.videos()
        .list(part="snippet", id=video_id)
        .execute()
    )

    if not response.get("items"):
        raise ValueError(f"動画が見つかりません: {video_id}")

    snippet = response["items"][0]["snippet"]

    # サムネイル: maxres > high > medium > default の順に取得
    thumbnails = snippet.get("thumbnails", {})
    thumbnail_url = ""
    for quality in ("maxres", "high", "medium", "default"):
        if quality in thumbnails:
            thumbnail_url = thumbnails[quality]["url"]
            break

    return {
        "title": snippet["title"],
        "published_at": snippet["publishedAt"],
        "thumbnail_url": thumbnail_url,
        "channel_title": snippet["channelTitle"],
    }


def get_latest_videos(channel_id: str, max_results: int = 5) -> list[dict]:
    """チャンネルの最新動画リストを取得する。

    Args:
        channel_id: YouTubeチャンネルID。
        max_results: 取得する動画数（最大50）。

    Returns:
        動画情報のリスト。各要素は get_video_info と同じ形式 + video_id。
    """
    youtube = build("youtube", "v3", developerKey=Config.YOUTUBE_API_KEY)

    # チャンネルの最新動画を検索
    search_response = (
        youtube.search()
        .list(
            part="id",
            channelId=channel_id,
            order="date",
            type="video",
            maxResults=min(max_results, 50),
        )
        .execute()
    )

    videos = []
    for item in search_response.get("items", []):
        video_id = item["id"]["videoId"]
        try:
            info = get_video_info(video_id)
            info["video_id"] = video_id
            videos.append(info)
        except Exception as e:
            print(f"⚠️ 動画情報の取得に失敗 ({video_id}): {e}")

    return videos[:max_results]
