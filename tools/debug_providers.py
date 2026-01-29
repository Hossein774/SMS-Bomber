#!/usr/bin/env python3
"""
Provider Debugger Tool
Analyzes why providers fail and suggests fixes.
"""

import asyncio
import aiohttp
import json
import sys
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sms_bomber.api.providers import ProviderRegistry, Provider

console = Console()


@dataclass
class DebugResult:
    """Result of debugging a provider."""
    provider_name: str
    url: str
    status_code: Optional[int]
    success: bool
    error: Optional[str]
    response_body: Optional[str]
    response_headers: Dict[str, str]
    diagnosis: str
    fix_suggestion: str


class ProviderDebugger:
    """Debug and fix SMS providers."""

    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=10)
        
        # Different header configurations to try
        self.header_configs = {
            "minimal": {
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            "browser": {
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Origin": "https://example.com",
                "Referer": "https://example.com/",
                "DNT": "1",
                "Connection": "keep-alive",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-site",
            },
            "mobile": {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "okhttp/4.9.0",
                "Accept-Encoding": "gzip",
            },
            "persian": {
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "fa-IR,fa;q=0.9",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Origin": "",  # Will be set dynamically
                "Referer": "",  # Will be set dynamically
            },
        }

    async def debug_provider(
        self, 
        provider: Provider, 
        phone: str,
        header_type: str = "browser"
    ) -> DebugResult:
        """Debug a single provider with detailed analysis."""
        
        # Get headers
        headers = self.header_configs.get(header_type, self.header_configs["browser"]).copy()
        
        # Set dynamic origin/referer based on URL
        if "Origin" in headers:
            from urllib.parse import urlparse
            parsed = urlparse(provider.url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            headers["Origin"] = base_url
            headers["Referer"] = base_url + "/"
        
        # Get request data
        data = provider.get_request_data(phone)
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    provider.url,
                    json=data,
                    headers=headers,
                    ssl=False  # Disable SSL verification for testing
                ) as response:
                    status = response.status
                    resp_headers = dict(response.headers)
                    
                    try:
                        body = await response.text()
                        body = body[:500]  # Limit response size
                    except:
                        body = "Could not read response body"
                    
                    # Diagnose the issue
                    diagnosis, fix = self._diagnose(status, body, resp_headers, provider)
                    
                    return DebugResult(
                        provider_name=provider.name,
                        url=provider.url,
                        status_code=status,
                        success=status in [200, 201, 202],
                        error=None,
                        response_body=body,
                        response_headers=resp_headers,
                        diagnosis=diagnosis,
                        fix_suggestion=fix
                    )
                    
        except asyncio.TimeoutError:
            return DebugResult(
                provider_name=provider.name,
                url=provider.url,
                status_code=None,
                success=False,
                error="Timeout",
                response_body=None,
                response_headers={},
                diagnosis="Request timed out - server too slow or blocking",
                fix_suggestion="Try increasing timeout or using a proxy"
            )
        except aiohttp.ClientConnectorError as e:
            return DebugResult(
                provider_name=provider.name,
                url=provider.url,
                status_code=None,
                success=False,
                error=f"Connection error: {str(e)}",
                response_body=None,
                response_headers={},
                diagnosis="Cannot connect to server - URL may be wrong or server is down",
                fix_suggestion="Check if the URL is correct or find alternative endpoint"
            )
        except Exception as e:
            return DebugResult(
                provider_name=provider.name,
                url=provider.url,
                status_code=None,
                success=False,
                error=str(e),
                response_body=None,
                response_headers={},
                diagnosis=f"Unexpected error: {str(e)}",
                fix_suggestion="Check error details and fix accordingly"
            )

    def _diagnose(
        self, 
        status: int, 
        body: str, 
        headers: Dict, 
        provider: Provider
    ) -> tuple:
        """Diagnose the issue based on response."""
        
        body_lower = body.lower() if body else ""
        
        # Success cases
        if status in [200, 201, 202]:
            if any(kw in body_lower for kw in ['success', 'ok', 'sent', 'otp', 'code']):
                return "✅ Working correctly", "No fix needed"
            elif any(kw in body_lower for kw in ['already', 'exist', 'registered']):
                return "✅ Working (user exists)", "No fix needed"
            else:
                return "✅ Request accepted", "No fix needed"
        
        # Client errors (4xx)
        if status == 400:
            if 'phone' in body_lower or 'mobile' in body_lower or 'invalid' in body_lower:
                return "❌ Invalid phone format", "Try different phone field name or format (e.g., +98, 98, 09)"
            elif 'required' in body_lower:
                return "❌ Missing required fields", "Check what fields the API expects"
            else:
                return "❌ Bad request format", "Check request body structure"
        
        if status == 401:
            return "❌ Authentication required", "Need to add auth token or API key"
        
        if status == 403:
            if 'captcha' in body_lower:
                return "❌ Captcha required", "Cannot bypass - need captcha solver"
            elif 'blocked' in body_lower or 'ban' in body_lower:
                return "❌ IP blocked", "Use proxy rotation"
            else:
                return "❌ Access forbidden", "Try different headers (Origin, Referer)"
        
        if status == 404:
            return "❌ Endpoint not found", "URL is wrong - find the correct API endpoint"
        
        if status == 405:
            return "❌ Method not allowed", "Try GET instead of POST or vice versa"
        
        if status == 415:
            return "❌ Unsupported media type", "Try application/x-www-form-urlencoded instead of JSON"
        
        if status == 429:
            return "⚠️ Rate limited", "Add delays between requests or use proxies"
        
        # Server errors (5xx)
        if status >= 500:
            return "❌ Server error", "Server issue - try again later"
        
        return f"❓ Unknown status {status}", "Analyze response body for clues"

    async def debug_all_providers(self, phone: str) -> List[DebugResult]:
        """Debug all providers."""
        registry = ProviderRegistry()
        providers = registry.get_all_providers()
        
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Debugging providers...", total=len(providers))
            
            for provider in providers:
                progress.update(task, description=f"Testing {provider.name}...")
                result = await self.debug_provider(provider, phone)
                results.append(result)
                progress.advance(task)
        
        return results

    async def try_fix_provider(
        self, 
        provider: Provider, 
        phone: str
    ) -> Dict[str, Any]:
        """Try different configurations to fix a provider."""
        
        console.print(f"\n[bold cyan]🔧 Attempting to fix: {provider.name}[/bold cyan]")
        
        fixes_tried = []
        
        # Try different header configurations
        for header_name, headers in self.header_configs.items():
            result = await self.debug_provider(provider, phone, header_name)
            
            fixes_tried.append({
                "config": header_name,
                "status": result.status_code,
                "success": result.success,
            })
            
            if result.success:
                console.print(f"[green]✅ Fixed with '{header_name}' headers![/green]")
                return {
                    "fixed": True,
                    "config": header_name,
                    "headers": headers,
                    "result": result
                }
        
        # Try different phone formats
        phone_formats = [
            ("original", phone),
            ("no_zero", phone[1:] if phone.startswith("0") else phone),
            ("plus98", f"+98{phone[1:]}" if phone.startswith("0") else f"+98{phone}"),
            ("98", f"98{phone[1:]}" if phone.startswith("0") else f"98{phone}"),
        ]
        
        for format_name, formatted_phone in phone_formats:
            # Create modified provider with different phone
            test_provider = Provider(
                name=provider.name,
                url=provider.url,
                data_template={"phone": formatted_phone}  # Direct phone, no template
            )
            
            result = await self.debug_provider(test_provider, formatted_phone, "browser")
            
            fixes_tried.append({
                "config": f"phone_{format_name}",
                "status": result.status_code,
                "success": result.success,
            })
            
            if result.success:
                console.print(f"[green]✅ Fixed with '{format_name}' phone format![/green]")
                return {
                    "fixed": True,
                    "phone_format": format_name,
                    "result": result
                }
        
        # Try different field names
        field_names = ["phone", "mobile", "phoneNumber", "phone_number", "msisdn", "cellphone", "tel", "username"]
        
        for field in field_names:
            test_provider = Provider(
                name=provider.name,
                url=provider.url,
                data_template={field: "{phone}"}
            )
            
            result = await self.debug_provider(test_provider, phone, "browser")
            
            fixes_tried.append({
                "config": f"field_{field}",
                "status": result.status_code,
                "success": result.success,
            })
            
            if result.success:
                console.print(f"[green]✅ Fixed with '{field}' field name![/green]")
                return {
                    "fixed": True,
                    "field_name": field,
                    "result": result
                }
        
        console.print(f"[red]❌ Could not auto-fix {provider.name}[/red]")
        return {
            "fixed": False,
            "attempts": fixes_tried
        }

    def display_results(self, results: List[DebugResult]):
        """Display debug results in a nice table."""
        
        # Separate working and failing
        working = [r for r in results if r.success]
        failing = [r for r in results if not r.success]
        
        console.print(f"\n[bold green]✅ Working Providers: {len(working)}[/bold green]")
        console.print(f"[bold red]❌ Failing Providers: {len(failing)}[/bold red]")
        
        # Show failing providers with diagnosis
        if failing:
            table = Table(title="❌ Failing Providers - Diagnosis")
            table.add_column("Provider", style="cyan")
            table.add_column("Status", justify="center")
            table.add_column("Diagnosis", style="yellow")
            table.add_column("Suggested Fix", style="green")
            
            for result in failing:
                status = str(result.status_code) if result.status_code else result.error or "Error"
                table.add_row(
                    result.provider_name,
                    status,
                    result.diagnosis[:40],
                    result.fix_suggestion[:40]
                )
            
            console.print(table)


async def main():
    """Main function."""
    console.print(Panel.fit(
        "[bold cyan]🔍 Provider Debugger Tool[/bold cyan]\n"
        "Analyzes why providers fail and suggests fixes",
        border_style="cyan"
    ))
    
    # Get phone number
    if len(sys.argv) > 1:
        phone = sys.argv[1]
    else:
        phone = console.input("\n📱 Enter test phone number: ")
    
    debugger = ProviderDebugger()
    
    # Debug all providers
    console.print("\n[bold]Step 1: Analyzing all providers...[/bold]")
    results = await debugger.debug_all_providers(phone)
    debugger.display_results(results)
    
    # Offer to fix failing providers
    failing = [r for r in results if not r.success]
    
    if failing:
        console.print(f"\n[bold yellow]Found {len(failing)} failing providers[/bold yellow]")
        fix_choice = console.input("\nTry to auto-fix failing providers? [y/n]: ")
        
        if fix_choice.lower() == 'y':
            console.print("\n[bold]Step 2: Attempting auto-fixes...[/bold]")
            
            registry = ProviderRegistry()
            providers = registry.get_all_providers()
            
            fixed_count = 0
            for result in failing[:10]:  # Limit to first 10 failing
                provider = next((p for p in providers if p.name == result.provider_name), None)
                if provider:
                    fix_result = await debugger.try_fix_provider(provider, phone)
                    if fix_result.get("fixed"):
                        fixed_count += 1
            
            console.print(f"\n[bold green]✅ Auto-fixed {fixed_count} providers![/bold green]")
    
    console.print("\n[bold]Done![/bold]")


if __name__ == "__main__":
    asyncio.run(main())
