from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, Literal

class Settings(BaseSettings):
    """
    アプリケーション設定クラス
    環境変数から設定を読み込みます。
    """
    # SNMP 設定
    snmp_version: Literal["v2c", "v3", "both"] = Field("v2c", description="SNMPバージョン")
    community_string: str = Field("public", description="SNMP v2c コミュニティ名")
    
    # SNMP v3 設定 (v3使用時は必須推奨だが、環境変数で柔軟に扱えるようOptionalにする)
    usm_user: Optional[str] = Field(None, description="SNMP v3 ユーザー名")
    usm_auth_key: Optional[str] = Field(None, description="SNMP v3 認証キー")
    usm_priv_key: Optional[str] = Field(None, description="SNMP v3 暗号化キー")
    snmp_engine_id: Optional[str] = Field(None, description="SNMP Engine ID (Hex文字列)")

    # 出力設定
    output_mode: Literal["stdout", "webhook"] = Field("stdout", description="出力モード")
    webhook_url: Optional[str] = Field(None, description="Webhook送信先URL")

    # MIB 設定
    mib_dir: str = Field("/opt/mibs", description="コンパイル済みMIBディレクトリのパス")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False  # 環境変数の大文字小文字を区別しない

settings = Settings()
