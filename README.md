# SNMP Trap Receiver & Resolver

ネットワーク機器から送信されるSNMP Trap (v1/v2c/v3) を受信し、MIB定義に基づいてOIDを解決した後、JSON形式で標準出力またはWebhookへ送信するマイクロサービスです。

## 特徴

*   **SNMP v1/v2c/v3 対応**: 透過的に受信し、統一されたJSONフォーマットで出力します。
*   **MIB解決 (Resolution)**: 事前にコンパイルされたMIBモジュールを使用し、高速にOIDを名称に変換します。
*   **柔軟な出力 (Dispatcher)**: コンテナログ（stdout）またはHTTP WebhookへのPOST送信を選択可能です。
*   **堅牢性**: リトライロジック（Webhook送信時）とグレースフルシャットダウンを実装しています。
*   **Dockerネイティブ**: マルチステージビルドにより、軽量かつセキュアなコンテナイメージを提供します。

## ディレクトリ構成

```plaintext
.
├── Dockerfile                  # マルチステージビルド定義
├── docker-compose.yml          # ローカル開発用Composeファイル
├── requirements.txt            # Python依存パッケージ
├── mibs/
│   └── src/                    # ベンダーMIB格納用 (ユーザー配置)
└── src/
    ├── main.py                 # エントリーポイント
    ├── config.py               # 設定管理 (Pydantic)
    ├── listener.py             # SNMP受信ロジック (pysnmp)
    ├── resolver.py             # MIB解決ロジック
    └── dispatcher.py           # 送信・リトライロジック
```

## クイックスタート (Docker)

### 1. 起動

```bash
docker-compose up --build
```

デフォルトで UDP 162 ポートでリッスンを開始します。

### 2. Trap送信テスト

別ターミナルから `snmptrap` コマンド（net-snmp-utils等）でTrapを送信します。

**v2cの例:**
```bash
# sysName (1.3.6.1.2.1.1.5.0) を含むテストトラップ
snmptrap -v 2c -c public localhost:162 '' 1.3.6.1.4.1.8072.2.3.0.1 1.3.6.1.2.1.1.5.0 s "Test Trap Message"
```

**ログ出力例:**
```json
{
  "source_ip": "172.18.0.1",
  "source_port": 58923,
  "snmp_version": "v2c",
  "variables": [
    {
      "oid": "1.3.6.1.2.1.1.3.0",
      "mib": "SNMPv2-MIB",
      "name": "sysUpTime",
      "suffix": "0",
      "value": "12345"
    },
    {
      "oid": "1.3.6.1.6.3.1.1.4.1.0",
      "mib": "SNMPv2-MIB",
      "name": "snmpTrapOID",
      "suffix": "0",
      "value": "1.3.6.1.4.1.8072.2.3.0.1"
    },
    {
      "oid": "1.3.6.1.2.1.1.5.0",
      "mib": "SNMPv2-MIB",
      "name": "sysName",
      "suffix": "0",
      "value": "Test Trap Message"
    }
  ],
  "timestamp": "2024-05-20T10:00:00Z"
}
```

## 設定 (Configuration)

環境変数で動作を制御します。

| 変数名 | デフォルト | 説明 |
| :--- | :--- | :--- |
| `SNMP_VERSION` | `v2c` | `v2c`, `v3`, `both` のいずれか |
| `COMMUNITY_STRING` | `public` | v2c用コミュニティ名 |
| `USM_USER` | - | v3 ユーザー名 |
| `USM_AUTH_KEY` | - | v3 認証キー (MD5/DES想定) |
| `USM_PRIV_KEY` | - | v3 暗号化キー |
| `SNMP_ENGINE_ID` | - | v3 Engine ID (Hex文字列, 例: `0x8000000001`) |
| `OUTPUT_MODE` | `stdout` | `stdout` または `webhook` |
| `WEBHOOK_URL` | - | Webhook送信先URL (POST) |
| `MIB_DIR` | `/opt/mibs` | コンパイル済みMIBのロードパス |

## MIBの追加

カスタムMIB（ベンダーMIB）を使用するには、MIBファイル（`.mib` または `.my`）を `mibs/src/` ディレクトリに配置し、イメージをリビルドしてください。

※ 現在の実装では、ビルド時に自動コンパイルする機能は簡易化されています。本番運用では `pysmi` の `mibdump.py` を使用して事前にコンパイルしたJSON/Pythonファイルを配置するか、ビルドプロセスに組み込むことを推奨します。

## 開発 (Development)

### ローカル実行

```bash
# 仮想環境作成
python -m venv .venv
source .venv/bin/activate

# 依存インストール
pip install -r requirements.txt

# 実行
export OUTPUT_MODE=stdout
export PYTHONPATH=$PYTHONPATH:.
python -m src.main
```
