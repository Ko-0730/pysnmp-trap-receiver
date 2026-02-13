import asyncio
import logging
import signal
import sys
from src.config import settings
from src.resolver import MibResolver
from src.listener import TrapListener
from src.dispatcher import Dispatcher

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """
    アプリケーションのメインエントリポイント。
    """
    logger.info("Starting SNMP Trap Receiver...")
    
    # コンポーネントの初期化
    resolver = MibResolver()
    dispatcher = Dispatcher()
    listener = TrapListener(resolver, dispatcher)

    # Dispatcherの初期化（Webhook用セッションなど）
    await dispatcher.initialize()

    # Listenerのセットアップと起動
    try:
        await listener.run()
    except Exception as e:
        logger.error(f"Failed to start listener: {e}")
        sys.exit(1)

    # 終了シグナルの待機
    stop_event = asyncio.Event()

    def handle_signal():
        logger.info("Received stop signal")
        stop_event.set()

    loop = asyncio.get_running_loop()
    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, handle_signal)
    except NotImplementedError:
        # Windowsなど一部環境での対応
        logger.warning("Signal handling is not supported on this platform")

    # 実行ループ
    logger.info("Application is running. Press Ctrl+C to exit.")
    await stop_event.wait()

    # クリーンアップ
    logger.info("Shutting down...")
    await dispatcher.close()
    logger.info("Shutdown complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # 既にシグナルハンドラで処理されているはずだが、念のため
        pass
