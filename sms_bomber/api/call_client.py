# sms_bomber/api/call_client.py
from typing import Dict, Optional, Any
import aiohttp
import asyncio
import ssl
from urllib.parse import urlparse
from ..core.logger import logging

logger = logging.getLogger("sms_bomber")


class CallBomberClient:
    """Asynchronous call bomber client."""

    def __init__(self, timeout: float = 5.0, proxy: Optional[Dict[str, str]] = None):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.proxy = proxy
        self._default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
            "Content-Type": "application/json",
            "DNT": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site"
        }
        # Create SSL context that ignores certificate errors
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def _get_headers(self, url: str) -> Dict[str, str]:
        """Generate headers with dynamic origin/referer."""
        headers = self._default_headers.copy()
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        headers["Origin"] = base_url
        headers["Referer"] = base_url + "/"
        return headers

    def _is_success(self, status: int, body: str) -> bool:
        """Check if the request was successful."""
        body_lower = body.lower()
        
        if status in [200, 201, 202]:
            if any(kw in body_lower for kw in ['success', 'ok', 'sent', 'otp', 'code', 'verify', 'call']):
                return True
            if not any(kw in body_lower for kw in ['error', 'fail', 'invalid', 'wrong']):
                return True
        return False

    async def send_call_request(
        self, provider_name: str, url: str, data: Dict[str, Any], method: str = "POST"
    ) -> Dict[str, Any]:
        """Send an asynchronous call request."""
        headers = self._get_headers(url)

        try:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(timeout=self.timeout, connector=connector) as session:
                if method.upper() == "GET":
                    async with session.get(url, params=data, headers=headers, proxy=self.proxy) as response:
                        body = await response.text()
                        success = self._is_success(response.status, body)
                        return {
                            "success": success,
                            "provider": provider_name,
                            "status_code": response.status,
                            "response": body[:500] if body else "",  # Include response body (truncated)
                            "type": "call"
                        }
                else:
                    async with session.post(url, json=data, headers=headers, proxy=self.proxy) as response:
                        body = await response.text()
                        success = self._is_success(response.status, body)
                        return {
                            "success": success,
                            "provider": provider_name,
                            "status_code": response.status,
                            "response": body[:500] if body else "",  # Include response body (truncated)
                            "type": "call"
                        }
        except asyncio.TimeoutError:
            return {
                "success": False,
                "provider": provider_name,
                "error": "Timeout - server took too long to respond",
                "type": "call"
            }
        except aiohttp.ClientConnectorError as e:
            return {
                "success": False,
                "provider": provider_name,
                "error": f"Connection error: {str(e)}",
                "type": "call"
            }
        except Exception as e:
            logger.error(f"Call request failed for {provider_name}: {str(e)}")
            return {
                "success": False,
                "provider": provider_name,
                "error": str(e),
                "type": "call"
            }
