"""Google Driveへの画像アップロードサービス"""

import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from config import Config


SCOPES = ["https://www.googleapis.com/auth/drive"]


def get_drive_service():
    """OAuth 2.0で認証し、Drive APIのサービスインスタンスを返す。"""
    creds = None
    token_path = os.path.join(os.path.dirname(__file__), "token.json")
    
    # 既存のトークンがあれば読み込む
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
    # 有効なクレデンシャルがない場合はログインプロセスを実行
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_secrets_file = Config.GOOGLE_CLIENT_SECRETS_FILE
            if not os.path.isabs(client_secrets_file):
                client_secrets_file = os.path.join(os.path.dirname(__file__), client_secrets_file)
                
            if not os.path.exists(client_secrets_file):
                raise FileNotFoundError(f"OAuthクライアントシークレットファイルが見つかりません: {client_secrets_file}\n"
                                        f"GCPコンソールからダウンロードして配置してください。")
            
            flow = InstalledAppFlow.from_client_secrets_file(
                client_secrets_file, SCOPES
            )
            # ローカルサーバーを起動してブラウザで認証
            creds = flow.run_local_server(port=0)
            
        # 次回以降のためにトークンを保存
        with open(token_path, "w") as token:
            token.write(creds.to_json())
            
    return build("drive", "v3", credentials=creds)


def upload_image_to_drive(file_path: str, filename: str = "") -> str:
    """画像ファイルをGoogle Driveにアップロードし、公開URLを返す。

    Args:
        file_path: アップロードする画像ファイルのローカルパス。
        filename: Drive上のファイル名。空の場合はローカルファイル名を使用。

    Returns:
        公開アクセス可能な画像URL。
    """
    if not filename:
        filename = os.path.basename(file_path)

    service = get_drive_service()

    # ファイルメタデータ
    file_metadata = {
        "name": filename,
        "parents": [Config.GOOGLE_DRIVE_FOLDER_ID],
    }

    # アップロード
    media = MediaFileUpload(file_path, mimetype="image/png", resumable=True)
    uploaded = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id", supportsAllDrives=True)
        .execute()
    )
    file_id = uploaded["id"]

    # 公開共有設定（誰でもリンクで閲覧可能）
    service.permissions().create(
        fileId=file_id,
        body={"type": "anyone", "role": "reader"},
    ).execute()

    # 直接アクセス可能な画像URL
    image_url = f"https://drive.google.com/uc?export=view&id={file_id}"
    print(f"✅ [Drive] 画像アップロード完了: {image_url}")

    return image_url
