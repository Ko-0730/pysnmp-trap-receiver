import aiohttp
import asyncio
import json
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from src.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)

class Dispatcher:
    """
    Trapデータの転送・出力を担当するクラス。
    標準出力またはWebhookへの送信を行います。
    """

    def __init__(self):
        self.session = None

    async def initialize(self):
        """
        非同期HTTPセッションを初期化します。
        Webhookモード時のみ必要です。
        """
        if settings.output_mode == "webhook" and not self.session:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """
        HTTPセッションをクローズします。
        """
        if self.session:
            await self.session.close()

    async def dispatch(self, trap_data: dict):
        """
        Trapデータを設定された出力先に転送します。
        
        Args:
            trap_data: 送信するTrapデータの辞書
        """
        # タイムスタンプの付与
        if "timestamp" not in trap_data:
            trap_data["timestamp"] = datetime.utcnow().isoformat() + "Z"

        if settings.output_mode == "stdout":
            self._dispatch_stdout(trap_data)
        elif settings.output_mode == "webhook":
            await self._dispatch_webhook(trap_data)
        else:
            logger.warning(f"Unknown output mode: {settings.output_mode}")

    def _dispatch_stdout(self, data: dict):
        """
        標準出力にJSON形式で出力します。
        """
        try:
            print(json.dumps(data, ensure_ascii=False))
        except Exception as e:
            logger.error(f"Failed to write to stdout: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError))
    )
    async def _dispatch_webhook(self, data: dict):
        """
        Webhook URLにデータをPOSTします。
        Tenacityを使用してリトライを行います。
        """
        if not self.session:
            await self.initialize()

        if not settings.webhook_url:
            logger.error("Webhook URL is not configured.")
            return

        try:
            async with self.session.post(settings.webhook_url, json=data) as response:
                if response.status >= 400:
                    logger.error(f"Webhook failed with status {response.status}: {await response.text()}")
                    response.raise_for_status()
                else:
                    logger.debug(f"Webhook sent successfully: {response.status}")
        except Exception as e:
            logger.warning(f"Webhook dispatch failed: {e}")
            raise
