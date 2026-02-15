from pysnmp.entity import engine, config
from pysnmp.carrier.asyncio.dgram import udp
from pysnmp.entity.rfc3413 import ntfrcv
from pysnmp.proto.api import v2c
from src.config import settings
from src.resolver import MibResolver
from src.dispatcher import Dispatcher
import logging
import asyncio
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class TrapListener:
    """
    SNMP Trapを受信し、ResolverとDispatcherへ処理を委譲するクラス。
    """

    def __init__(self, resolver: MibResolver, dispatcher: Dispatcher):
        self.resolver = resolver
        self.dispatcher = dispatcher
        
        # SnmpEngineの初期化
        # EngineIDが指定されている場合は設定
        snmp_engine_id = None
        if settings.snmp_engine_id:
            try:
                # 0x... 形式の文字列をbytesに変換
                snmp_engine_id = bytes.fromhex(settings.snmp_engine_id.replace("0x", ""))
            except ValueError:
                logger.warning(f"Invalid SNMP Engine ID format: {settings.snmp_engine_id}")

        self.snmpEngine = engine.SnmpEngine(snmpEngineID=snmp_engine_id)

    def _cbFun(self, snmpEngine, stateReference, contextEngineId, contextName,
               varBinds, cbCtx):
        """
        Trap受信時のコールバック関数。
        """
        transportDomain, transportAddress = snmpEngine.msgAndPduDsp.get_transport_info(stateReference)
        logger.info(f"Received Trap from {transportAddress}")

        resolved_vars = []
        for name, val in varBinds:
            resolved = self.resolver.resolve(name, val)
            resolved_vars.append(resolved)

        trap_data = {
            "source_ip": transportAddress[0],
            "source_port": transportAddress[1],
            "snmp_version": "v3" if contextEngineId else "v2c", # 簡易判定
            "variables": resolved_vars,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # 非同期処理としてDispatcherへ渡す
        asyncio.create_task(self.dispatcher.dispatch(trap_data))

    def setup(self):
        """
        SNMPエンジンの設定（ユーザー、トランスポートなど）を行います。
        """
        # トランスポート設定 (UDP/162)
        config.addTransport(
            self.snmpEngine,
            udp.domainName,
            udp.UdpTransport().openServerMode(('0.0.0.0', 162))
        )

        # v2c設定
        if settings.snmp_version in ["v2c", "both"]:
            config.addV1System(self.snmpEngine, 'my-area', settings.community_string)
            logger.info(f"SNMP v2c enabled with community: {settings.community_string}")

        # v3設定
        if settings.snmp_version in ["v3", "both"]:
            if settings.usm_user:
                auth_proto = config.usmHMACMD5AuthProtocol # Default to MD5
                priv_proto = config.usmDESPrivProtocol     # Default to DES
                
                # TODO: 認証・暗号化プロトコルの選択を詳細化する場合はここで分岐処理が必要
                # 現状は簡易実装としてデフォルトを使用するが、必要に応じて設定値からパースする

                config.addV3User(
                    self.snmpEngine,
                    settings.usm_user,
                    auth_proto, settings.usm_auth_key,
                    priv_proto, settings.usm_priv_key
                )
                logger.info(f"SNMP v3 enabled for user: {settings.usm_user}")
            else:
                logger.warning("SNMP v3 is enabled but USM user is not configured.")

        # NotificationReceiverの登録
        ntfrcv.NotificationReceiver(self.snmpEngine, self._cbFun)

    async def run(self):
        """
        リスナーを開始します。
        """
        self.setup()
        logger.info("SNMP Trap Listener started on UDP/162")
        
        # pysnmpの非同期ループへの統合はSnmpEngineが自動で行うため、
        # ここではループを維持するだけでよいが、
        # 実際にはメインループが動いていればよい。
        # SnmpEngineが内部でasyncioのトランスポートを使用しているため。
        pass
