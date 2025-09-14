# sms_bomber/api/client.py
from typing import Dict, Optional
import aiohttp
import asyncio
from fake_headers import Headers
from ..core.logger import logging

logger = logging.getLogger("sms_bomber")


class APIClient:
    """Asynchronous API client for sending SMS requests."""

    def __init__(self, timeout: float = 2.5, proxy: Optional[Dict[str, str]] = None):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.proxy = proxy
        self.headers_generator = Headers()

    async def send_request(
        self, provider_name: str, url: str, data: Dict[str, any]
    ) -> Dict[str, any]:
        """Send an asynchronous HTTP request to the provider."""
        headers = self.headers_generator.generate()

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    url, json=data, headers=headers, proxy=self.proxy
                ) as response:
                    response.raise_for_status()
                    return {
                        "success": True,
                        "provider": provider_name,
                        "status_code": response.status,
                    }
        except Exception as e:
            logger.error(f"Request failed for {provider_name}: {str(e)}")
            return {"success": False, "provider": provider_name, "error": str(e)}
