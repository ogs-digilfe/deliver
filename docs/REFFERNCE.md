# deliver API リファレンス

## 概要

`deliver` は、株式関連のデータファイルをローカルファイルシステムへ保存し、HTTP 経由で配信する FastAPI アプリケーションである。

本書は現在の実装に基づき、各ルートの認証要件、リクエスト、レスポンス、および主なエラーを説明する。サーバーのセットアップと起動方法は [README](../README.md)、構成と設計上の制約は [architecture.md](architecture.md) を参照すること。

## 接続と表記

例では接続先を環境変数に設定する。

```bash
export DELIVER_BASE_URL="http://<SERVER_IP_ADDRESS>:8080"
```

認証が必要なルートでは、あらかじめ `POST /token` で取得したトークンを使用する。

```bash
export DELIVER_TOKEN="<ACCESS_TOKEN>"
```

アップロード例の `@` から始まる値は、クライアント上のファイルパスを表す。

## 認証と認可

| 権限表記 | 条件 |
| --- | --- |
| 不要 | Bearer トークンは不要 |
| active ユーザー | 有効な Bearer トークンを持ち、ユーザーの `status` が `active` |
| admin | active ユーザーであり、さらに `role` が `admin` |

Bearer トークンはサーバープロセスのメモリだけに保存され、有効期限はない。サーバーの再起動で失効する。また、複数の Uvicorn ワーカー間では共有されない。

認証・認可に関する代表的なエラーは次のとおりである。

| HTTP ステータス | 条件 | レスポンス例 |
| --- | --- | --- |
| `401 Unauthorized` | トークンがない、または無効 | `{"detail":"Not authenticated"}` または `{"detail":"Invalid authentication credentials"}` |
| `400 Bad Request` | トークンに対応するユーザーが inactive | `{"detail":"Inactive user"}` |
| `403 Forbidden` | active だが admin ではないユーザーが admin 専用ルートを呼び出した | `{"detail":"Fobiden"}` |

> `Fobiden` は現在の実装が返す文字列をそのまま記載している。

## ルート一覧

| メソッド | パス | 権限 | 概要 |
| --- | --- | --- | --- |
| `POST` | `/token` | 不要 | Bearer トークンを発行する |
| `GET` | `/logintest` | active ユーザー | 現在のユーザー情報を返す |
| `POST` | `/upload/` | admin | `deliver/data/` へファイルを保存する |
| `POST` | `/upload-kabutan-kessan/` | admin | 株探決算 HTML 用ディレクトリへ保存する |
| `POST` | `/upload-shikiho/` | admin | 四季報 HTML 用ディレクトリへ保存する |
| `POST` | `/upload-shikiho-online/` | admin | 四季報 HTML 用ディレクトリへ保存する |
| `POST` | `/upload-portfolio` | admin | portfolio ディレクトリへ ZIP を保存する |
| `GET` | `/download/` | active ユーザー | `deliver/data/` の指定ファイルを返す |
| `GET` | `/download-kabutan-kessan/` | active ユーザー | 固定名の株探決算 ZIP を返す |
| `GET` | `/download-shikiho/` | active ユーザー | 四季報 HTML 用ディレクトリの指定ファイルを返す |

## `POST /token`

ユーザー名とパスワードを照合し、以後の API 呼び出しに使用する Bearer トークンを発行する。

リクエスト本文は JSON ではなく、OAuth2 Password Request Form の `application/x-www-form-urlencoded` 形式で送信する。必須フィールドは `username` と `password` である。

```bash
curl --request POST \
  --url "$DELIVER_BASE_URL/token" \
  --header "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "username=<USERNAME>" \
  --data-urlencode "password=<PASSWORD>"
```

成功時は `200 OK` と次の JSON を返す。

```json
{
  "access_token": "<64_HEX_CHARACTERS>",
  "token_type": "bearer"
}
```

ユーザーが存在しない場合とパスワードが一致しない場合は、いずれも `400 Bad Request` を返す。

```json
{
  "detail": "Incorrect username or password"
}
```

inactive ユーザーにもトークン自体は発行されるが、そのトークンで保護されたルートを呼び出すと `400 Bad Request` になる。

## `GET /logintest`

Bearer トークンを検証し、対応する active ユーザーの情報を返す。認証状態の確認に使用できる。

```bash
curl --request GET \
  --url "$DELIVER_BASE_URL/logintest" \
  --header "Authorization: Bearer $DELIVER_TOKEN"
```

成功時は `200 OK` とユーザー情報を返す。

```json
{
  "username": "<USERNAME>",
  "hashed_password": "<PASSWORD_HASH>",
  "salt": "<BASE64_SALT>",
  "role": "admin",
  "status": "active",
  "registered": "<REGISTERED_AT>",
  "updated": "<UPDATED_AT>"
}
```

このレスポンスには `hashed_password` と `salt` が含まれるため、出力やログの取り扱いに注意すること。

## ファイルアップロード

すべてのアップロードルートは `multipart/form-data` を受け取り、フォームフィールド名は `file` である。同名ファイルが存在する場合は上書きする。

`/upload-portfolio` 以外はファイル全体をメモリへ読み込んでから書き込む。大容量ファイルを送信する場合は、サーバーのメモリ使用量に注意すること。

### `POST /upload/`

任意のファイルを `deliver/data/<filename>` に保存する。

```bash
curl --request POST \
  --url "$DELIVER_BASE_URL/upload/" \
  --header "Authorization: Bearer $DELIVER_TOKEN" \
  --form "file=@./stock_data.parquet"
```

成功時は `200 OK` と、操作した管理ユーザーおよびファイル名を返す。

```json
{
  "user": {
    "username": "<USERNAME>",
    "hashed_password": "<PASSWORD_HASH>",
    "salt": "<BASE64_SALT>",
    "role": "admin",
    "status": "active",
    "registered": "<REGISTERED_AT>",
    "updated": "<UPDATED_AT>"
  },
  "upload_file": "stock_data.parquet"
}
```

### `POST /upload-kabutan-kessan/`

ファイルを `deliver/data/html/kabutan-kessan/<filename>` に保存する。

```bash
curl --request POST \
  --url "$DELIVER_BASE_URL/upload-kabutan-kessan/" \
  --header "Authorization: Bearer $DELIVER_TOKEN" \
  --form "file=@./kabutan_kessan.zip"
```

成功時の形式は `POST /upload/` と同じである。保存先ディレクトリはこのルートでは作成されないため、事前に存在し、サービス実行ユーザーが書き込める必要がある。存在しない場合、現在の実装では `500 Internal Server Error` になる。

### `POST /upload-shikiho/`

ファイルを `deliver/data/html/shikiho/<filename>` に保存する。保存先ディレクトリが存在しなければ自動作成する。

```bash
curl --request POST \
  --url "$DELIVER_BASE_URL/upload-shikiho/" \
  --header "Authorization: Bearer $DELIVER_TOKEN" \
  --form "file=@./shikiho.html"
```

成功時の形式は `POST /upload/` と同じである。

### `POST /upload-shikiho-online/`

ファイルを `deliver/data/html/shikiho/<filename>` に保存する。`POST /upload-shikiho/` と保存先は同じだが、このルート自身は保存先ディレクトリを作成しない。

```bash
curl --request POST \
  --url "$DELIVER_BASE_URL/upload-shikiho-online/" \
  --header "Authorization: Bearer $DELIVER_TOKEN" \
  --form "file=@./shikiho_online.html"
```

成功時の形式は `POST /upload/` と同じである。保存先が存在しない場合、現在の実装では `500 Internal Server Error` になる。

### `POST /upload-portfolio`

ZIP ファイルを `deliver/data/portfolio/<filename>` に保存する。ファイル名はパス要素を含まない単一の名前で、拡張子は大文字・小文字を問わず `.zip` でなければならない。

このルートは 1 MiB ごとにファイルを書き込み、一時ファイルへの書き込み完了後に同一ファイルシステム上で保存先へ置換する。これにより、不完全な内容が最終ファイル名で公開されることを防ぐ。

```bash
curl --request POST \
  --url "$DELIVER_BASE_URL/upload-portfolio" \
  --header "Authorization: Bearer $DELIVER_TOKEN" \
  --form "file=@./portfolio.zip"
```

成功時のレスポンス形式は `POST /upload/` と同じである。

無効なファイル名の場合は `400 Bad Request` を返す。

```json
{
  "detail": "Invalid filename"
}
```

ZIP 以外の拡張子の場合も `400 Bad Request` を返す。

```json
{
  "detail": "Only ZIP files are allowed"
}
```

拡張子だけを検査しており、ZIP 内部の形式や内容までは検証しない。

## ファイルダウンロード

ダウンロード成功時は `200 OK` でファイル本体を返す。レスポンスのメディアタイプは `application/octet-stream` で、`Content-Disposition` ヘッダーにはダウンロード用のファイル名が設定される。

### `GET /download/`

クエリパラメーター `filename` で指定した `deliver/data/<filename>` を返す。

```bash
curl --fail-with-body \
  --location \
  --url "$DELIVER_BASE_URL/download/?filename=stock_data.parquet" \
  --header "Authorization: Bearer $DELIVER_TOKEN" \
  --output ./stock_data.parquet
```

対象が存在しない場合は `404 Not Found` を返す。

```json
{
  "detail": "File not found"
}
```

### `GET /download-kabutan-kessan/`

`deliver/data/html/kabutan-kessan/kabutan_kessan.zip` を返す。ファイル名を指定するパラメーターはない。

```bash
curl --fail-with-body \
  --location \
  --url "$DELIVER_BASE_URL/download-kabutan-kessan/" \
  --header "Authorization: Bearer $DELIVER_TOKEN" \
  --output ./kabutan_kessan.zip
```

対象が存在しない場合は `404 Not Found` と `{"detail":"File not found"}` を返す。

### `GET /download-shikiho/`

クエリパラメーター `filename` で指定した `deliver/data/html/shikiho/<filename>` を返す。

```bash
curl --fail-with-body \
  --location \
  --get \
  --url "$DELIVER_BASE_URL/download-shikiho/" \
  --header "Authorization: Bearer $DELIVER_TOKEN" \
  --data-urlencode "filename=shikiho.html" \
  --output ./shikiho.html
```

対象が存在しない場合は `404 Not Found` と `{"detail":"File not found"}` を返す。

## バリデーションエラー

必須フォームフィールドや必須クエリパラメーターがない場合、FastAPI は `422 Unprocessable Entity` を返す。たとえば、`GET /download/` で `filename` を省略した場合が該当する。レスポンスの `detail` には、入力位置、エラー内容、エラー種別などが配列で含まれる。

## FastAPI 標準ルート

現在のアプリケーションでは FastAPI の標準ドキュメントルートを無効化していないため、認証なしで次のルートも利用できる。

| メソッド | パス | 内容 |
| --- | --- | --- |
| `GET` | `/docs` | Swagger UI |
| `GET` | `/redoc` | ReDoc |
| `GET` | `/openapi.json` | OpenAPI スキーマ |

ブラウザーで Swagger UI を開く例:

```text
http://<SERVER_IP_ADDRESS>:8080/docs
```

OpenAPI スキーマを保存する例:

```bash
curl --url "$DELIVER_BASE_URL/openapi.json" --output ./openapi.json
```

## 現行実装のファイル名に関する注意

`POST /upload-portfolio` を除くアップロードルート、および `GET /download/` と `GET /download-shikiho/` は、クライアントが指定したファイル名を安全な単一ファイル名であるか検証していない。絶対パスや `..` などを含む値は意図しない場所を参照する可能性があるため、信頼できるクライアントと値だけを使用すること。

これは現在の API の振る舞いを説明する注意事項であり、安全性を保証するものではない。外部公開する場合は、アプリケーション側で保存先・取得元ディレクトリから脱出できないよう検証を追加する必要がある。
