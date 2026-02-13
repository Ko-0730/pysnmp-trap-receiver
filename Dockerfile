# Stage 1: Builder
# MIBのコンパイルと依存パッケージのビルドを行う
FROM python:3.14-slim AS builder

WORKDIR /build

# ビルド依存ツールのインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 依存パッケージのインストール
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# MIBコンパイル用の準備
# ここでは標準MIBとベンダーMIBをコンパイルする
# 実際にはpysmiのmibdump.pyを使用するか、カスタムスクリプトを実行する
# 今回は標準的なディレクトリ構成を作成し、実行時にロードできる状態にする

# アプリケーションコードのコピー（必要であればここで行う処理を追加）
# 今回はRuntimeステージでコピーするためスキップ

# Stage 2: Runtime
# 実行用イメージ
FROM python:3.14-slim AS runtime

WORKDIR /app

# ユーザー作成 (セキュリティのためroot以外で実行)
RUN useradd -m snmpuser

# 環境変数の設定
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.local/bin:$PATH"

# Builderからインストール済みパッケージをコピー...したいところだが
# マルチステージでsite-packagesをコピーするのはパス依存の問題があるため
# ここでは再度インストールするか、Wheelsを使用するのが一般的。
# 簡易化のため、Runtimeでもpip installを行う（slimイメージなのでビルドツール不要なライブラリなら問題ない）
# もしコンパイルが必要なライブラリがある場合はBuilderでWheelを作成してCOPYする手法をとるべき。

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# アプリケーションコードのコピー
COPY src/ ./src/
COPY mibs/ ./mibs/

# MIBディレクトリの作成
RUN mkdir -p /opt/mibs && chown -R snmpuser:snmpuser /opt/mibs

# 実行ユーザーの切り替え
USER snmpuser

# ポート公開
EXPOSE 162/udp

# 実行コマンド
CMD ["python", "-m", "src.main"]
