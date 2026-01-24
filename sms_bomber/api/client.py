# sms_bomber/api/client.py
from typing import Dict, Optional
import aiohttp
import asyncio
import ssl
from urllib.parse import urlparse
from ..core.logger import logging

logger = logging.getLogger("sms_bomber")


class APIClient:
    """Asynchronous API client for sending SMS requests."""

    def __init__(self, timeout: float = 5.0, proxy: Optional[Dict[str, str]] = None):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.proxy = proxy
        self._default_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        # Create SSL context that ignores certificate errors for problematic sites
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

    async def send_request(
        self, provider_name: str, url: str, data: Dict[str, any], content_type: str = "json", method: str = "POST"
    ) -> Dict[str, any]:
        """Send an asynchronous HTTP request to the provider."""
        headers = self._get_headers(url)
        
        # Update Content-Type header based on content_type
        if content_type == "form":
            headers["Content-Type"] = "application/x-www-form-urlencoded"

        try:
            connector = aiohttp.TCPConnector(ssl=self.ssl_context)
            async with aiohttp.ClientSession(timeout=self.timeout, connector=connector) as session:
                if method.upper() == "GET":
                    # For GET requests, don't send body
                    async with session.get(
                        url, headers=headers, proxy=self.proxy
                    ) as response:
                        body = await response.text()
                        success = self._is_success(response.status, body)
                        return {
                            "success": success,
                            "provider": provider_name,
                            "status_code": response.status,
                        }
                elif content_type == "form":
                    async with session.post(
                        url, data=data, headers=headers, proxy=self.proxy
                    ) as response:
                        body = await response.text()
                        success = self._is_success(response.status, body)
                        return {
                            "success": success,
                            "provider": provider_name,
                            "status_code": response.status,
                        }
                else:
                    async with session.post(
                        url, json=data, headers=headers, proxy=self.proxy
                    ) as response:
                        body = await response.text()
                        success = self._is_success(response.status, body)
                        return {
                            "success": success,
                            "provider": provider_name,
                            "status_code": response.status,
                        }
        except Exception as e:
            logger.error(f"Request failed for {provider_name}: {str(e)}")
            return {"success": False, "provider": provider_name, "error": str(e)}

    def _is_success(self, status: int, body: str) -> bool:
        """Check if the request was successful."""
        body_lower = body.lower()
        
        # Clear success indicators
        if status in [200, 201, 202]:
            # Check for positive indicators
            if any(kw in body_lower for kw in ['success', 'ok', 'sent', 'otp', 'code', 'verify']):
                return True
            # Check for "soft success" (user exists, etc.)
            if any(kw in body_lower for kw in ['exist', 'already', 'registered', 'found']):
                return True
            # If 200 and no error indicators, probably success
            if not any(kw in body_lower for kw in ['error', 'fail', 'invalid', 'wrong']):
                return True
        
        # Some APIs return 400 but still send SMS (validation error but OTP sent)
        if status == 400:
            if any(kw in body_lower for kw in ['sent', 'otp', 'code', 'verify']):
                return True
        
        return False
