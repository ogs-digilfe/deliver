# deliverについて

## 概要

stockdbで使っているFastAPIで作成したAPIサーバー。  
ポート8080で待ち受け。

## 動作環境・前提条件

### ソフトウェア

- systemdを採用したLinux環境
- Git（リポジトリの取得・更新時に使用）
- Python 3.12以上（`pyproject.toml`の`requires-python`で指定）
- [uv](https://docs.astral.sh/uv/)がインストールされていること

deliverのPython環境と依存関係はuvで管理し、`uv run`経由で起動する。

APIサーバーのPythonパッケージは`uv sync --no-dev`でインストールするため、FastAPIやUvicornを個別にインストールする必要はない。

## 開発環境の構築

### Gitリポジトリ

以下のコマンドでリポジトリをcloneし、プロジェクトのルートへ移動する。

```bash
git clone https://github.com/ogs-digilfe/deliver.git
cd deliver
```

### Python実行環境の構築

依存関係と Python 環境は [uv](https://docs.astral.sh/uv/) で管理する。
リポジトリのルートで以下を実行する。

```bash
# Python 環境の作成と依存関係の同期
uv sync
```

`uv sync` は API の実行依存に加え、開発用の JupyterLab もインストールする。
API の実行に必要な依存のみ同期する場合は次のようにする。

```bash
uv sync --no-dev
```

### 管理ユーザーの追加

```bash
uv run python -m deliver.add_newadmin
```

### deliverをsystemdサービスとして登録

参考用のユニットファイルは `deploy/deliver.service.example` で管理する。以下のプレースホルダーを実環境の値に置き換えて使用する。

| プレースホルダー          | 設定する値           | 確認コマンドの例   |
| ----------------- | --------------- | ---------- |
| `<SERVICE_USER>`  | サービスを実行するユーザー   | `whoami`   |
| `<SERVICE_GROUP>` | サービスを実行するグループ   | `id -gn`   |
| `<PROJECT_ROOT>`  | リポジトリの絶対パス      | `pwd`      |
| `<UV_EXECUTABLE>` | `uv`実行ファイルの絶対パス | `which uv` |

テンプレートをsystemdのユニットファイルとして配置し、プレースホルダーを編集する。

```bash
sudo install -m 0644 deploy/deliver.service.example /etc/systemd/system/deliver.service
sudoedit /etc/systemd/system/deliver.service
```

設定を検証してから、サービスを登録・起動する。`enable --now`により、OS起動時の自動起動を有効化すると同時にサービスを起動する。

```bash
sudo systemd-analyze verify /etc/systemd/system/deliver.service
sudo systemctl daemon-reload
sudo systemctl enable --now deliver
sudo systemctl status deliver --no-pager
```

サービス実行ユーザーには、`deliver/data`、`deliver/tmp`、`userdb`への読み書き権限が必要となる。また、TCPポート8080が未使用であり、外部から接続する場合はファイアウォールで通信が許可されている必要がある。

systemdでは`uv run --frozen --no-dev`を使う。`--frozen`により起動時に`uv.lock`が書き換えられることを防ぎ、`--no-dev`によりJupyterLabなどを実行環境から除外する。

## 開発環境で利用するコマンド等

### JupyterLab

開発やツール作成でJupyterLabを利用する場合は、以下のコマンドで起動する。

```bash
uv run jupyter lab
```

### テスト

テストはpytestで実行する。

```bash
uv run pytest
```

### uvを利用したPython依存関係の管理

`pyproject.toml` で依存関係の意図を管理し、`uv.lock` で実際のバージョンを固定する。
依存関係を変更するときは `uv add <package>` または `uv remove <package>` を使う。

## 接続情報

| 項目 | 設定値 |
| --- | --- |
| IPアドレス | `<SERVER_IP_ADDRESS>` |
| 待ち受けポート | 8080 |
| URL | `http://<SERVER_IP_ADDRESS>:8080` |

## 開発時にdeliverを直接起動する場合

開発時にAPIサーバーを直接起動する場合は、リポジトリのルートで以下を実行する。  
通常運用では、systemdサービスとして起動する。

```bash
uv run uvicorn deliver.main:app --reload --host 0.0.0.0 --port 8080
```
