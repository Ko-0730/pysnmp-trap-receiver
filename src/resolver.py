from pysnmp.smi import builder, view, error
from src.config import settings
import logging
import os

logger = logging.getLogger(__name__)

class MibResolver:
    """
    MIB定義に基づいてOIDを解決するクラス。
    事前にコンパイルされたMIBモジュールを使用します。
    """

    def __init__(self):
        """
        MibBuilderとMibViewControllerを初期化し、
        設定されたMIBディレクトリをロードパスに追加します。
        """
        self.mibBuilder = builder.MibBuilder()
        
        # MIBソースディレクトリの設定
        # pysnmpのデフォルトパスに加えて、カスタムMIBディレクトリを追加
        mib_path = os.path.abspath(settings.mib_dir)
        if os.path.exists(mib_path):
            self.mibBuilder.addMibSources(builder.DirMibSource(mib_path))
            logger.info(f"Added MIB source directory: {mib_path}")
        else:
            logger.warning(f"MIB directory not found: {mib_path}")

        # コンパイル機能を使用する場合の設定（pysmiが必要）
        # pysnmpに標準MIBが含まれていない場合、外部から取得してコンパイルする設定を追加
        try:
            from pysnmp.smi import compiler
            # コンパイラを追加し、IF-MIBなどを自動的にダウンロード・コンパイルする
            # デフォルトのソースに加えて、一般的なMIBリポジトリを追加
            compiler.addMibCompiler(self.mibBuilder, sources=[
                'https://mibs.pysnmp.com/asn1/@mib@'
            ])
            # コンパイル済みファイルの保存先
            self.mibBuilder.addMibSources(builder.DirMibSource('/opt/mibs'))
            
        except Exception as e:
            logger.warning(f"Failed to configure MIB compiler: {e}")

        self.mibViewController = view.MibViewController(self.mibBuilder)
        
        # 指定ディレクトリ内のMIBモジュールをロード
        self._load_mibs_from_directory(mib_path)

    def _load_mibs_from_directory(self, mib_path):
        """
        指定されたディレクトリ内のMIBモジュールをロードします。
        """
        if not os.path.exists(mib_path):
            logger.warning(f"MIB directory not found: {mib_path}")
            return

        loaded_modules = []
        try:
            # ディレクトリ内のファイルを走査
            for filename in os.listdir(mib_path):
                # .pyファイルのみ対象（コンパイル済みMIB）
                if filename.endswith('.py') and not filename.startswith('__init__'):
                    module_name = filename[:-3]
                    try:
                        self.mibBuilder.loadModules(module_name)
                        loaded_modules.append(module_name)
                        logger.debug(f"Loaded MIB module: {module_name}")
                    except error.MibNotFoundError:
                        logger.warning(f"Failed to load MIB module: {module_name}")
                    except Exception as e:
                        logger.warning(f"Error loading {module_name}: {e}")
            
            if loaded_modules:
                logger.info(f"Successfully loaded {len(loaded_modules)} MIB modules from {mib_path}")
            else:
                logger.info(f"No MIB modules found in {mib_path}")

            # 標準的なMIBがロードされていない場合の警告（オプション）
            # 必要であればここでチェックするか、あるいはユーザーに委ねる
            
        except Exception as e:
            logger.error(f"Error scanning MIB directory {mib_path}: {e}")

    def resolve(self, oid, value=None):
        """
        OIDと値を解決して、可読性の高い形式（MIB名, オブジェクト名, 整形された値）を返します。
        
        Args:
            oid: 解決対象のOID (ObjectIdentifier or str)
            value: 対応する値 (Any, optional)

        Returns:
            dict: {
                "oid": "1.3.6...", 
                "name": "sysUpTime", 
                "mib": "SNMPv2-MIB", 
                "value": "12345" 
            }
        """
        try:
            # OID解決
            varBind = view.MibViewController(self.mibBuilder).getNodeName(oid)
            oid_obj, label, suffix = varBind
            
            # MIBモジュール名とオブジェクト名を取得
            modName, symName, _ = self.mibViewController.getNodeLocation(oid_obj)
            
            # 値の解決（型情報などに基づく整形）
            # ここでは単純化のため、pysnmpのprettyPrintを使用
            formatted_value = value.prettyPrint() if hasattr(value, 'prettyPrint') else str(value)
            
            return {
                "oid": str(oid),
                "mib": modName,
                "name": symName,
                "suffix": ".".join(str(x) for x in suffix),
                "value": formatted_value
            }

        except error.SmiError as e:
            # 解決失敗時
            logger.debug(f"MIB resolution failed for OID {oid}: {e}")
            return {
                "oid": str(oid),
                "mib": "UNKNOWN",
                "name": str(oid),
                "suffix": "",
                "value": str(value) if value is not None else ""
            }
        except Exception as e:
            logger.error(f"Unexpected error during resolution: {e}")
            return {
                "oid": str(oid),
                "mib": "ERROR",
                "name": str(oid),
                "suffix": "",
                "value": str(value) if value is not None else ""
            }
