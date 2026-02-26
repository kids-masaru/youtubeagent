"""各サービスモジュールの単体テスト"""

import unittest
from unittest.mock import patch, MagicMock

# テスト対象
from youtube_service import extract_video_id, _join_transcript


class TestExtractVideoId(unittest.TestCase):
    """YouTube URL解析のテスト"""

    def test_standard_url(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_short_url(self):
        url = "https://youtu.be/dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_embed_url(self):
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_shorts_url(self):
        url = "https://www.youtube.com/shorts/dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_direct_id(self):
        self.assertEqual(extract_video_id("dQw4w9WgXcQ"), "dQw4w9WgXcQ")

    def test_url_with_extra_params(self):
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120s"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_mobile_url(self):
        url = "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        self.assertEqual(extract_video_id(url), "dQw4w9WgXcQ")

    def test_invalid_url(self):
        with self.assertRaises(ValueError):
            extract_video_id("https://www.google.com")

    def test_empty_string(self):
        with self.assertRaises(ValueError):
            extract_video_id("")


class TestJoinTranscript(unittest.TestCase):
    """字幕テキスト結合のテスト"""

    def test_dict_entries(self):
        entries = [
            {"text": "こんにちは"},
            {"text": "世界"},
        ]
        result = _join_transcript(entries)
        self.assertEqual(result, "こんにちは 世界")

    def test_object_entries(self):
        entry1 = MagicMock()
        entry1.text = "Hello"
        entry2 = MagicMock()
        entry2.text = "World"
        result = _join_transcript([entry1, entry2])
        self.assertEqual(result, "Hello World")

    def test_empty_entries(self):
        result = _join_transcript([])
        self.assertEqual(result, "")


class TestGeminiService(unittest.TestCase):
    """Gemini要約サービスのテスト"""

    @patch("gemini_service.genai")
    def test_summarize_transcript(self, mock_genai):
        # モックのセットアップ
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = "【概要】テスト要約\n【重要なポイント】\n・ポイント1\n【アクションアイテム/結論】\nテスト結論"
        mock_client.models.generate_content.return_value = mock_response

        from gemini_service import summarize_transcript

        result = summarize_transcript("テスト字幕テキスト")
        self.assertIn("【概要】", result)
        self.assertIn("【重要なポイント】", result)
        mock_client.models.generate_content.assert_called_once()


class TestLineService(unittest.TestCase):
    """LINE通知サービスのテスト"""

    @patch("line_service.requests.post")
    @patch("line_service.Config")
    def test_send_notification_success(self, mock_config, mock_post):
        mock_config.LINE_CHANNEL_ACCESS_TOKEN = "test_token"
        mock_config.LINE_USER_ID = "test_user_id"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        from line_service import send_notification

        result = send_notification(
            title="テスト動画",
            summary="テスト要約",
            video_url="https://www.youtube.com/watch?v=test",
            thumbnail_url="https://img.youtube.com/test.jpg",
        )
        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch("line_service.requests.post")
    @patch("line_service.Config")
    def test_send_notification_failure(self, mock_config, mock_post):
        mock_config.LINE_CHANNEL_ACCESS_TOKEN = "test_token"
        mock_config.LINE_USER_ID = "test_user_id"
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_post.return_value = mock_response

        from line_service import send_notification

        result = send_notification(
            title="テスト動画",
            summary="テスト要約",
            video_url="https://www.youtube.com/watch?v=test",
        )
        self.assertFalse(result)


class TestNotionService(unittest.TestCase):
    """Notionページ作成サービスのテスト"""

    def test_split_rich_text(self):
        from notion_service import _split_rich_text

        # 短いテキスト
        result = _split_rich_text("短いテキスト", max_length=2000)
        self.assertEqual(len(result), 1)

        # 長いテキスト
        long_text = "a" * 5000
        result = _split_rich_text(long_text, max_length=2000)
        self.assertEqual(len(result), 3)

    def test_build_summary_blocks(self):
        from notion_service import _build_summary_blocks

        summary = "【概要】テスト概要\n・ポイント1\n・ポイント2\n通常テキスト"
        blocks = _build_summary_blocks(summary)
        self.assertTrue(len(blocks) >= 3)

        # 最初のブロックはheading_2
        self.assertEqual(blocks[0]["type"], "heading_2")

        # 箇条書きブロック
        bullet_blocks = [b for b in blocks if b["type"] == "bulleted_list_item"]
        self.assertEqual(len(bullet_blocks), 2)


if __name__ == "__main__":
    unittest.main()
