import asyncio
import argparse
import sys
import os
import logging
from pysnmp.hlapi.asyncio import *

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 設定
TARGET_HOST = os.environ.get('TARGET_HOST', 'snmp-receiver')
TARGET_PORT = int(os.environ.get('TARGET_PORT', 162))
COMMUNITY = os.environ.get('COMMUNITY_STRING', 'public')

# OID定義
OID_LINK_DOWN = '1.3.6.1.6.3.1.1.5.3'
OID_LINK_UP = '1.3.6.1.6.3.1.1.5.4'
OID_IF_INDEX = '1.3.6.1.2.1.2.2.1.1.1'
OID_IF_ADMIN_STATUS = '1.3.6.1.2.1.2.2.1.7.1'
OID_IF_OPER_STATUS = '1.3.6.1.2.1.2.2.1.8.1'

async def send_trap(trap_type, if_index=1):
    """
    指定されたタイプのトラップを送信します。
    """
    if trap_type == 'linkDown':
        trap_oid = OID_LINK_DOWN
        status_val = 2  # down
    elif trap_type == 'linkUp':
        trap_oid = OID_LINK_UP
        status_val = 1  # up
    else:
        logger.error(f"Unknown trap type: {trap_type}")
        return

    logger.info(f"Sending {trap_type} trap to {TARGET_HOST}:{TARGET_PORT}...")

    errorIndication, errorStatus, errorIndex, varBinds = await send_notification(
        SnmpEngine(),
        CommunityData(COMMUNITY, mpModel=1),  # SNMPv2c
        await UdpTransportTarget.create((TARGET_HOST, TARGET_PORT)),
        ContextData(),
        'trap',
        NotificationType(
            ObjectIdentity(trap_oid)
        ).add_varbinds(
            (OID_IF_INDEX, Integer(if_index)),
            (OID_IF_ADMIN_STATUS, Integer(status_val)),
            (OID_IF_OPER_STATUS, Integer(status_val))
        )
    )

    if errorIndication:
        logger.error(f"Error sending trap: {errorIndication}")
    elif errorStatus:
        logger.error(f"Error status: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1] or '?'}")
    else:
        logger.info(f"Successfully sent {trap_type} trap.")

async def main():
    parser = argparse.ArgumentParser(description='Send SNMP LinkDown/LinkUp traps.')
    parser.add_argument('trap_type', choices=['linkDown', 'linkUp', 'both'], default='both', nargs='?',
                        help='Type of trap to send (default: both)')
    args = parser.parse_args()

    if args.trap_type == 'both':
        await send_trap('linkDown')
        await asyncio.sleep(1)
        await send_trap('linkUp')
    else:
        await send_trap(args.trap_type)

if __name__ == '__main__':
    asyncio.run(main())
