#!/usr/bin/env python3
"""
Quick Provider Health Check
Tests all SMS providers and reports their status.
"""

import asyncio
import aiohttp
import ssl
import sys
import os
from urllib.parse import urlparse
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sms_bomber.api.providers import ProviderRegistry

console = Console()


async def test_provider(provider, phone: str, timeout: float = 8.0) -> dict:
    """Test a single provider."""
    url = provider.get_formatted_url(phone)
    data = provider.get_request_data(phone)
    
    # Headers
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
        "Content-Type": "application/json",
        "Origin": base_url,
        "Referer": base_url + "/",
    }
    
    # SSL context
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    
    try:
        client_timeout = aiohttp.ClientTimeout(total=timeout)
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)
        
        async with aiohttp.ClientSession(timeout=client_timeout, connector=connector) as session:
            async with session.post(url, json=data, headers=headers) as response:
                body = await response.text()
                body_lower = body.lower()
                
                # Check for success
                success = False
                if response.status in [200, 201, 202]:
                    if any(kw in body_lower for kw in ['success', 'ok', 'sent', 'otp', 'code', 'verify']):
                        success = True
                    elif any(kw in body_lower for kw in ['exist', 'already', 'registered', 'found']):
                        success = True
                    elif not any(kw in body_lower for kw in ['error', 'fail', 'invalid', 'wrong']):
                        success = True
                
                return {
                    "name": provider.name,
                    "status": response.status,
                    "success": success,
                    "message": "OK" if success else body[:100]
                }
                
    except asyncio.TimeoutError:
        return {
            "name": provider.name,
            "status": 0,
            "success": False,
            "message": "Timeout"
        }
    except Exception as e:
        return {
            "name": provider.name,
            "status": 0,
            "success": False,
            "message": str(e)[:80]
        }


async def check_all_providers(phone: str):
    """Check all providers."""
    registry = ProviderRegistry()
    providers = registry.get_all_providers()
    
    console.print(Panel.fit(
        f"[bold cyan]Provider Health Check[/bold cyan]\n"
        f"Testing {len(providers)} providers...",
        border_style="cyan"
    ))
    
    # Run all tests concurrently
    tasks = [test_provider(p, phone) for p in providers]
    results = await asyncio.gather(*tasks)
    
    # Create results table
    table = Table(title="Provider Status")
    table.add_column("Provider", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("HTTP", justify="center")
    table.add_column("Message", style="dim")
    
    working = 0
    for r in results:
        if r["success"]:
            status_icon = "[green]✓[/green]"
            working += 1
        else:
            status_icon = "[red]✗[/red]"
        
        table.add_row(
            r["name"],
            status_icon,
            str(r["status"]) if r["status"] else "-",
            r["message"][:50] if not r["success"] else ""
        )
    
    console.print(table)
    
    # Summary
    rate = (working / len(providers)) * 100 if providers else 0
    console.print(f"\n[bold]Summary:[/bold] {working}/{len(providers)} providers working ({rate:.1f}%)")
    
    if rate < 80:
        console.print("[yellow]⚠️ Consider running fix_providers.py to update failing providers[/yellow]")


def main():
    if len(sys.argv) < 2:
        console.print("[yellow]Usage: python check_providers.py <phone_number>[/yellow]")
        console.print("[dim]Example: python check_providers.py 09123456789[/dim]")
        sys.exit(1)
    
    phone = sys.argv[1]
    asyncio.run(check_all_providers(phone))


if __name__ == "__main__":
    main()
