# YouTube Intelligence & Automation Agent

YouTube動画の字幕を自動取得し、Gemini AIで要約。結果をLINEに通知＆Notionに蓄積するPythonシステム。

## 🚀 機能

- **YouTube動画解析** — URL直接入力 or チャンネル監視モード
- **字幕自動取得** — 日本語/英語/自動生成字幕に対応
- **Gemini AI要約** — 概要・重要ポイント・アクションアイテムを構造化
- **LINE通知** — サムネイル付きでリアルタイム通知
- **Notion保存** — データベースに構造化データとして蓄積

## 📋 必要なAPIキー

| サービス | キー | 取得先 |
|---|---|---|
| YouTube Data API | `YOUTUBE_API_KEY` | [Google Cloud Console](https://console.cloud.google.com/) |
| Gemini API | `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/) |
| LINE Messaging API | `LINE_CHANNEL_ACCESS_TOKEN`, `LINE_USER_ID` | [LINE Developers](https://developers.line.biz/) |
| Notion API | `NOTION_TOKEN`, `NOTION_DATABASE_ID` | [Notion Integrations](https://www.notion.so/my-integrations) |

## ⚙️ セットアップ

```bash
# 1. 依存ライブラリをインストール
cd youtube-agent
pip install -r requirements.txt

# 2. 環境変数ファイルを作成
cp .env.example .env

# 3. .env にAPIキーを設定（エディタで編集）
```

### Notionデータベースの準備

以下のプロパティを持つデータベースを作成してください：

| プロパティ名 | タイプ |
|---|---|
| タイトル | Title |
| URL | URL |
| 要約 | Rich Text |
| 投稿日 | Date |

作成後、Integrationをデータベースに接続（Share → Add integration）してください。

### LINE Messaging APIの準備

1. [LINE Developers Console](https://developers.line.biz/) でMessaging APIチャネルを作成
2. Channel Access Token（長期）を発行
3. Basic Settings → Your user ID をコピー

## 🎯 使い方

### 単一動画を処理

```bash
python main.py --url "https://www.youtube.com/watch?v=VIDEO_ID"
```

### チャンネルの最新動画を処理

```bash
python main.py --channel "UCxxxxxxx" --count 5
```

### ドライランモード（テスト用）

LINE通知とNotion保存をスキップし、要約結果のみ表示：

```bash
python main.py --url "https://www.youtube.com/watch?v=VIDEO_ID" --dry-run
```

## 🧪 テスト

```bash
python -m pytest tests/test_services.py -v
```

## 📁 ファイル構成

```
youtube-agent/
├── .env.example          # APIキーテンプレート
├── requirements.txt      # 依存ライブラリ
├── README.md             # このファイル
├── config.py             # 環境変数管理
├── youtube_service.py    # YouTube動画情報・字幕取得
├── gemini_service.py     # Gemini AI要約
├── line_service.py       # LINE通知
├── notion_service.py     # Notionページ作成
├── main.py               # CLIエントリーポイント
└── tests/
    └── test_services.py  # 単体テスト
```
