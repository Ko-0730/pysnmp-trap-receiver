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
COPY mibs/src/ ./mibs/src/
COPY scripts/ ./scripts/

# コンパイル実行 (出力先: mibs/compiled)
RUN python scripts/compile_mibs.py mibs/src mibs/compiled

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
# コンパイル済みMIBをコピー
COPY --from=builder /build/mibs/compiled /opt/mibs
# 元のMIBソースも必要であればコピー（今回はコンパイル済みのみを使用するため除外も可能だが、念のため構造を維持する場合は残す）
# COPY mibs/ ./mibs/ 

# MIBディレクトリの権限設定
RUN chown -R snmpuser:snmpuser /opt/mibs

# 実行ユーザーの切り替え
USER snmpuser

# ポート公開
EXPOSE 162/udp

# 実行コマンド
CMD ["python", "-m", "src.main"]
