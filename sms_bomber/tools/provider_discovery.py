# sms_bomber/tools/provider_discovery.py
"""
Provider Discovery Tool
Automatically discovers new SMS/OTP API endpoints from websites.

How it works:
1. Crawls target websites (Iranian services)
2. Extracts JavaScript files
3. Searches for API patterns using regex
4. Validates discovered endpoints
5. Generates provider configurations
"""

import asyncio
import aiohttp
import re
import json
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich.panel import Panel

console = Console()


@dataclass
class DiscoveredEndpoint:
    """Represents a discovered API endpoint."""
    name: str
    url: str
    method: str = "POST"
    data_template: Dict = field(default_factory=dict)
    source: str = ""  # Where it was found
    confidence: float = 0.0  # How likely it's a valid SMS endpoint
    tested: bool = False
    working: bool = False
    status_code: Optional[int] = None
    response_time: Optional[float] = None


class ProviderDiscovery:
    """
    Automatically discovers SMS/OTP API endpoints.
    
    Discovery Process:
    1. Crawls target websites
    2. Extracts JavaScript files
    3. Searches for API patterns using regex
    4. Validates discovered endpoints
    5. Generates provider configurations
    """

    def __init__(self):
        self.discovered: List[DiscoveredEndpoint] = []
        self.timeout = aiohttp.ClientTimeout(total=15)
        self.scanned_urls: Set[str] = set()
        
        # Regex patterns to find SMS/OTP endpoints
        self.api_patterns = [
            # Direct API URL patterns
            r'["\']((https?://[^"\']*)(otp|sms|verify|auth|login|send-code|verification)[^"\']*)["\']',
            r'["\']((https?://[^"\']*)(phone|mobile|register|signup|authenticate)[^"\']*)["\']',
            
            # API path patterns (without domain)
            r'["\']((\/api\/[^"\']*)(otp|sms|verify|code)[^"\']*)["\']',
            r'["\']((\/v[0-9]+\/[^"\']*)(auth|login|register|user)[^"\']*)["\']',
            
            # Fetch/axios patterns
            r'fetch\s*\(\s*["\']([^"\']+)["\']',
            r'axios\s*\.\s*(post|get)\s*\(\s*["\']([^"\']+)["\']',
            r'\.post\s*\(\s*["\']([^"\']+)["\']',
            r'\.get\s*\(\s*["\']([^"\']+)["\']',
            
            # API config patterns
            r'["\']?api[Uu]rl["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'["\']?baseURL["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'["\']?endpoint["\']?\s*[:=]\s*["\']([^"\']+)["\']',
        ]
        
        # Keywords that indicate SMS/OTP functionality
        self.sms_keywords = [
            'otp', 'sms', 'verify', 'verification', 'send-code', 'sendcode',
            'phone', 'mobile', 'msisdn', 'cellphone', 'authenticate',
            'login', 'register', 'signup', 'sign-up', 'request-otp',
            'send-otp', 'resend', 'code', 'pin', 'token', 'call-verify'
        ]
        
        # Common Iranian service domains to scan
        self.target_domains = [
            # Ride-sharing & Transportation
            "https://snapp.ir",
            "https://tapsi.ir",
            "https://maxim.ir",
            
            # E-commerce
            "https://digikala.com",
            "https://basalam.com",
            "https://torob.com",
            "https://emalls.ir",
            
            # Classifieds
            "https://divar.ir",
            "https://sheypoor.com",
            
            # Travel & Booking
            "https://alibaba.ir",
            "https://snapptrip.com",
            "https://jabama.com",
            "https://eligasht.com",
            
            # Streaming & Entertainment
            "https://namava.ir",
            "https://filimo.com",
            "https://aparat.com",
            "https://telewebion.com",
            
            # Telecom
            "https://my.irancell.ir",
            "https://my.mci.ir",
            "https://my.rightel.ir",
            
            # App Stores
            "https://cafebazaar.ir",
            "https://myket.ir",
            
            # Food Delivery
            "https://snappfood.ir",
            "https://delino.com",
            
            # Digital Content
            "https://fidibo.com",
            "https://taaghche.com",
            "https://ketabrah.ir",
            
            # Deals & Coupons
            "https://netbarg.com",
            "https://takhfifan.com",
            
            # Banking & Fintech
            "https://banimode.com",
            "https://digipay.ir",
            
            # Other Services
            "https://ostadkar.ir",
            "https://achareh.ir",
            "https://pintapin.com",
        ]

    async def discover_all(self, test_phone: Optional[str] = None, max_concurrent: int = 5) -> List[DiscoveredEndpoint]:
        """
        Main discovery function - scans all target domains.
        
        Args:
            test_phone: Phone number to test discovered endpoints
            max_concurrent: Maximum concurrent domain scans
            
        Returns:
            List of discovered endpoints
        """
        console.print(Panel.fit(
            "[bold cyan]🔍 SMS Provider Discovery Tool[/bold cyan]\n"
            "Automatically finding SMS/OTP API endpoints...",
            border_style="cyan"
        ))
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            
            # Step 1: Crawl websites
            task = progress.add_task("[cyan]Scanning websites...", total=len(self.target_domains))
            
            async def scan_with_semaphore(domain):
                async with semaphore:
                    await self._scan_domain(domain)
                    progress.advance(task)
            
            tasks = [scan_with_semaphore(domain) for domain in self.target_domains]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Step 2: Validate endpoints if test phone provided
            if test_phone and self.discovered:
                progress.update(task, description="[green]Testing discovered endpoints...")
                await self._validate_endpoints(test_phone)
        
        # Show results
        self._display_results()
        
        return self.discovered

    async def _scan_domain(self, domain: str):
        """
        Scan a single domain for API endpoints.
        
        Process:
        1. Fetch main page HTML
        2. Extract JavaScript file URLs
        3. Fetch and analyze each JS file
        4. Search for API patterns
        """
        if domain in self.scanned_urls:
            return
            
        self.scanned_urls.add(domain)
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout, headers=headers) as session:
                # Fetch main page
                async with session.get(domain) as response:
                    if response.status != 200:
                        return
                    
                    html = await response.text()
                    
                    # Extract JS file URLs
                    js_urls = self._extract_js_urls(html, domain)
                    
                    # Analyze main page for inline scripts
                    self._analyze_content(html, domain)
                    
                    # Fetch and analyze each JS file (limit to prevent overload)
                    for js_url in js_urls[:15]:
                        if js_url in self.scanned_urls:
                            continue
                        self.scanned_urls.add(js_url)
                        
                        try:
                            async with session.get(js_url) as js_response:
                                if js_response.status == 200:
                                    js_content = await js_response.text()
                                    self._analyze_content(js_content, domain)
                        except:
                            continue
                            
        except asyncio.TimeoutError:
            pass  # Silently skip timeout
        except Exception as e:
            pass  # Silently skip failed domains

    def _extract_js_urls(self, html: str, base_domain: str) -> List[str]:
        """Extract JavaScript file URLs from HTML."""
        js_pattern = r'<script[^>]+src=["\']([^"\']+\.js[^"\']*)["\']'
        matches = re.findall(js_pattern, html, re.IGNORECASE)
        
        urls = []
        for match in matches:
            if match.startswith('http'):
                urls.append(match)
            elif match.startswith('//'):
                urls.append('https:' + match)
            elif match.startswith('/'):
                urls.append(base_domain.rstrip('/') + match)
            else:
                urls.append(base_domain.rstrip('/') + '/' + match)
        
        return urls

    def _analyze_content(self, content: str, source: str):
        """
        Analyze JavaScript/HTML content for API endpoints.
        
        Uses regex patterns to find:
        - API URLs containing SMS/OTP keywords
        - Fetch/axios API calls
        - Configuration objects with API endpoints
        """
        found_urls: Set[str] = set()
        
        # Apply each pattern
        for pattern in self.api_patterns:
            try:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    # Handle tuple results from regex groups
                    if isinstance(match, tuple):
                        url = match[0] if match[0] else (match[1] if len(match) > 1 else '')
                    else:
                        url = match
                    
                    if not url or len(url) < 10:
                        continue
                    
                    # Check if URL contains SMS-related keywords
                    if any(kw in url.lower() for kw in self.sms_keywords):
                        # Make URL absolute if needed
                        if url.startswith('/') and not url.startswith('//'):
                            domain_match = re.match(r'(https?://[^/]+)', source)
                            if domain_match:
                                url = domain_match.group(1) + url
                        
                        if url.startswith('http'):
                            found_urls.add(url)
            except:
                continue
        
        # Also look for API configuration objects
        config_patterns = [
            r'["\']?api[Uu]rl["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'["\']?baseURL["\']?\s*[:=]\s*["\']([^"\']+)["\']',
            r'["\']?API_ENDPOINT["\']?\s*[:=]\s*["\']([^"\']+)["\']',
        ]
        
        for pattern in config_patterns:
            try:
                config_matches = re.findall(pattern, content)
                for url in config_matches:
                    if any(kw in url.lower() for kw in self.sms_keywords):
                        if url.startswith('http'):
                            found_urls.add(url)
            except:
                continue
        
        # Create endpoint objects for each found URL
        for url in found_urls:
            self._add_endpoint(url, source)

    def _add_endpoint(self, url: str, source: str):
        """Add a discovered endpoint if not already found."""
        # Skip if already discovered
        if any(e.url == url for e in self.discovered):
            return
        
        # Skip common false positives
        false_positives = ['google', 'facebook', 'twitter', 'instagram', 'cdn', 'static', 'fonts']
        if any(fp in url.lower() for fp in false_positives):
            return
        
        # Calculate confidence score
        confidence = self._calculate_confidence(url)
        
        # Skip very low confidence
        if confidence < 0.2:
            return
        
        # Guess the data template based on URL
        data_template = self._guess_data_template(url)
        
        # Extract name from URL
        name = self._extract_name(url, source)
        
        endpoint = DiscoveredEndpoint(
            name=name,
            url=url,
            data_template=data_template,
            source=source,
            confidence=confidence
        )
        
        self.discovered.append(endpoint)

    def _calculate_confidence(self, url: str) -> float:
        """
        Calculate confidence score (0-1) that this is a valid SMS endpoint.
        
        Higher score for:
        - Contains 'otp', 'sms', 'verify' etc.
        - Has API version in path (v1, v2, etc.)
        - Contains 'auth', 'login', 'register'
        """
        score = 0.0
        url_lower = url.lower()
        
        # High confidence keywords (+0.25 each)
        high_keywords = ['otp', 'sms', 'send-code', 'sendcode', 'verification', 'verify-phone']
        for kw in high_keywords:
            if kw in url_lower:
                score += 0.25
        
        # Medium confidence keywords (+0.15 each)
        medium_keywords = ['auth', 'authenticate', 'login', 'register', 'signup', 'phone', 'mobile']
        for kw in medium_keywords:
            if kw in url_lower:
                score += 0.15
        
        # Low confidence keywords (+0.1 each)
        low_keywords = ['user', 'account', 'verify', 'code', 'token']
        for kw in low_keywords:
            if kw in url_lower:
                score += 0.1
        
        # Bonus for API indicators
        if re.search(r'/v\d+/', url_lower):
            score += 0.1
        if '/api/' in url_lower:
            score += 0.1
        if '/rest/' in url_lower:
            score += 0.05
        
        return min(score, 1.0)

    def _guess_data_template(self, url: str) -> Dict:
        """
        Guess the request data template based on URL patterns.
        
        Common patterns:
        - phone, mobile, msisdn, cellphone, phoneNumber
        """
        url_lower = url.lower()
        
        # Try to detect the phone field name
        if 'msisdn' in url_lower:
            return {"msisdn": "{phone}"}
        elif 'cellphone' in url_lower:
            return {"cellphone": "{phone}"}
        elif 'phonenumber' in url_lower or 'phone_number' in url_lower:
            return {"phoneNumber": "{phone}"}
        elif 'phone-number' in url_lower:
            return {"phone-number": "{phone}"}
        elif 'mobile' in url_lower:
            return {"mobile": "{phone}"}
        elif 'username' in url_lower:
            return {"username": "{phone}"}
        else:
            return {"phone": "{phone}"}

    def _extract_name(self, url: str, source: str) -> str:
        """Extract a readable name from URL/source."""
        # Try to get domain name
        domain_match = re.search(r'https?://(?:www\.)?([^/]+)', source)
        if domain_match:
            domain = domain_match.group(1)
            name = domain.split('.')[0].capitalize()
            
            # Add endpoint type
            url_lower = url.lower()
            if 'otp' in url_lower:
                name += " OTP"
            elif 'sms' in url_lower:
                name += " SMS"
            elif 'call' in url_lower:
                name += " Call"
            elif 'login' in url_lower:
                name += " Login"
            elif 'register' in url_lower:
                name += " Register"
            elif 'verify' in url_lower:
                name += " Verify"
            elif 'auth' in url_lower:
                name += " Auth"
            
            return name
        
        return "Unknown Provider"

    async def _validate_endpoints(self, test_phone: str, max_concurrent: int = 5):
        """Test discovered endpoints to see if they work."""
        semaphore = asyncio.Semaphore(max_concurrent)
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "fa-IR,fa;q=0.9,en;q=0.8",
        }
        
        async def test_endpoint(endpoint: DiscoveredEndpoint):
            async with semaphore:
                if endpoint.confidence < 0.3:
                    return  # Skip low confidence endpoints
                
                try:
                    # Prepare request data
                    data = {}
                    for key, value in endpoint.data_template.items():
                        if isinstance(value, str) and "{phone}" in value:
                            data[key] = value.replace("{phone}", test_phone)
                        else:
                            data[key] = value
                    
                    timeout = aiohttp.ClientTimeout(total=10)
                    
                    import time
                    start_time = time.time()
                    
                    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
                        async with session.post(endpoint.url, json=data) as response:
                            endpoint.tested = True
                            endpoint.status_code = response.status
                            endpoint.response_time = time.time() - start_time
                            
                            # Consider success if not 404/500/502/503
                            endpoint.working = response.status in [200, 201, 202, 400, 401, 403, 429]
                            
                except asyncio.TimeoutError:
                    endpoint.tested = True
                    endpoint.working = False
                except Exception:
                    endpoint.tested = True
                    endpoint.working = False
        
        tasks = [test_endpoint(endpoint) for endpoint in self.discovered]
        await asyncio.gather(*tasks, return_exceptions=True)

    def _display_results(self):
        """Display discovery results in a nice table."""
        if not self.discovered:
            console.print("[yellow]⚠️ No new endpoints discovered.[/yellow]")
            return
        
        # Sort by confidence
        self.discovered.sort(key=lambda x: (x.working, x.confidence), reverse=True)
        
        # Summary panel
        working_count = sum(1 for e in self.discovered if e.working)
        tested_count = sum(1 for e in self.discovered if e.tested)
        
        console.print(Panel.fit(
            f"[bold green]✅ Discovery Complete![/bold green]\n\n"
            f"Total Discovered: [cyan]{len(self.discovered)}[/cyan]\n"
            f"Tested: [yellow]{tested_count}[/yellow]\n"
            f"Working: [green]{working_count}[/green]",
            border_style="green"
        ))
        
        # Results table
        table = Table(title="🔍 Discovered Endpoints", show_lines=True)
        table.add_column("Name", style="cyan", max_width=20)
        table.add_column("URL", style="blue", max_width=45)
        table.add_column("Confidence", justify="center")
        table.add_column("Status", justify="center")
        table.add_column("Response", justify="center")
        
        for endpoint in self.discovered[:25]:  # Show top 25
            confidence_color = "green" if endpoint.confidence >= 0.6 else ("yellow" if endpoint.confidence >= 0.4 else "red")
            confidence_str = f"[{confidence_color}]{endpoint.confidence:.0%}[/{confidence_color}]"
            
            if endpoint.tested:
                if endpoint.working:
                    status = f"[green]✅ {endpoint.status_code}[/green]"
                else:
                    status = f"[red]❌ {endpoint.status_code or 'Failed'}[/red]"
            else:
                status = "[dim]⏳ Not tested[/dim]"
            
            response_time = f"{endpoint.response_time:.2f}s" if endpoint.response_time else "-"
            
            # Truncate URL for display
            display_url = endpoint.url[:45] + "..." if len(endpoint.url) > 45 else endpoint.url
            
            table.add_row(
                endpoint.name,
                display_url,
                confidence_str,
                status,
                response_time
            )
        
        console.print(table)
        
        if len(self.discovered) > 25:
            console.print(f"[dim]... and {len(self.discovered) - 25} more endpoints[/dim]")

    def export_providers(self, output_file: str = "discovered_providers.json") -> int:
        """Export discovered endpoints as JSON."""
        # Filter to working or high confidence endpoints
        export_list = [e for e in self.discovered if e.working or e.confidence >= 0.5]
        
        export_data = []
        for endpoint in export_list:
            export_data.append({
                "name": endpoint.name,
                "url": endpoint.url,
                "method": endpoint.method,
                "data_template": endpoint.data_template,
                "confidence": endpoint.confidence,
                "working": endpoint.working,
                "source": endpoint.source
            })
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        console.print(f"[green]✅ Exported {len(export_data)} providers to {output_file}[/green]")
        return len(export_data)

    def export_as_python(self, output_file: str = "discovered_providers.py") -> int:
        """Export discovered endpoints as Python Provider objects."""
        working = [e for e in self.discovered if e.working or e.confidence >= 0.5]
        
        code = '''# Auto-generated providers from discovery
# Generated by ProviderDiscovery Tool
# 
# Add these to your providers.py file

from sms_bomber.api.providers import Provider

discovered_providers = [
'''
        for endpoint in working:
            data_str = str(endpoint.data_template).replace("'", '"')
            code += f'''    Provider(
        name="{endpoint.name}",
        url="{endpoint.url}",
        data_template={data_str},
    ),
'''
        code += ''']

# To add to your registry:
# from sms_bomber.api.providers import ProviderRegistry
# registry = ProviderRegistry()
# for provider in discovered_providers:
#     registry.add_provider(provider)
'''
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(code)
        
        console.print(f"[green]✅ Exported {len(working)} providers to {output_file}[/green]")
        return len(working)

    def get_working_providers(self) -> List[DiscoveredEndpoint]:
        """Get list of working providers only."""
        return [e for e in self.discovered if e.working]

    def get_high_confidence_providers(self, min_confidence: float = 0.6) -> List[DiscoveredEndpoint]:
        """Get providers with confidence above threshold."""
        return [e for e in self.discovered if e.confidence >= min_confidence]


async def main():
    """Run provider discovery from command line."""
    import sys
    
    console.print("\n[bold cyan]📡 SMS Provider Discovery Tool[/bold cyan]")
    console.print("=" * 50)
    
    # Get test phone if provided
    test_phone = sys.argv[1] if len(sys.argv) > 1 else None
    
    if test_phone:
        console.print(f"📱 Will test endpoints with: [green]{test_phone}[/green]")
    else:
        console.print("[yellow]💡 Tip: Provide a phone number to test endpoints[/yellow]")
        console.print("[dim]   python -m sms_bomber.tools.provider_discovery 09123456789[/dim]")
    
    console.print()
    
    # Run discovery
    discovery = ProviderDiscovery()
    await discovery.discover_all(test_phone)
    
    # Export results
    if discovery.discovered:
        console.print("\n[bold]Exporting results...[/bold]")
        discovery.export_providers("data/discovered_providers.json")
        discovery.export_as_python("data/discovered_providers.py")
        
        # Show working providers
        working = discovery.get_working_providers()
        if working:
            console.print(f"\n[bold green]🎯 {len(working)} working providers ready to use![/bold green]")


if __name__ == "__main__":
    asyncio.run(main())
