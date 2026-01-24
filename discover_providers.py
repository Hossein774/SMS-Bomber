#!/usr/bin/env python3

"""
SMS Provider Discovery Tool
Automatically discovers new SMS/OTP API endpoints from Iranian websites.

Usage:
    python discover_providers.py                    # Discovery only (no testing)
    python discover_providers.py 09123456789        # Discovery + test with phone
    python discover_providers.py 09123456789 --export  # Discovery + test + export
"""

import asyncio
import sys
import os
import argparse

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel

console = Console()


def print_banner():
    """Print the discovery tool banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════╗
    ║          🔍 SMS Provider Discovery Tool 🔍            ║
    ║                                                        ║
    ║   Automatically finds SMS/OTP API endpoints            ║
    ║   from Iranian websites and services                   ║
    ╚═══════════════════════════════════════════════════════╝
    """
    console.print(banner, style="cyan")


async def run_discovery(phone: str = None, export: bool = True, add_to_registry: bool = False):
    """Run the discovery process."""
    from sms_bomber.tools.provider_discovery import ProviderDiscovery
    
    discovery = ProviderDiscovery()
    
    # Show target count
    console.print(f"[cyan]🎯 Scanning {len(discovery.target_domains)} Iranian websites...[/cyan]\n")
    
    # Run discovery
    await discovery.discover_all(test_phone=phone)
    
    if not discovery.discovered:
        console.print("[yellow]No new endpoints discovered.[/yellow]")
        return
    
    # Export results
    if export:
        # Create data directory if needed
        os.makedirs("data", exist_ok=True)
        
        console.print("\n[bold]📁 Exporting results...[/bold]")
        discovery.export_providers("data/discovered_providers.json")
        discovery.export_as_python("data/discovered_providers.py")
    
    # Add to registry
    if add_to_registry and discovery.get_working_providers():
        console.print("\n[bold]➕ Adding working providers to registry...[/bold]")
        try:
            from sms_bomber.api.providers import ProviderRegistry, Provider
            
            registry = ProviderRegistry()
            added = 0
            
            for endpoint in discovery.get_working_providers():
                provider = Provider(
                    name=endpoint.name,
                    url=endpoint.url,
                    data_template=endpoint.data_template
                )
                registry.add_provider(provider)
                added += 1
            
            console.print(f"[green]✅ Added {added} new providers to registry![/green]")
        except Exception as e:
            console.print(f"[red]❌ Failed to add providers: {e}[/red]")
    
    # Summary
    working = discovery.get_working_providers()
    high_conf = discovery.get_high_confidence_providers(0.6)
    
    console.print(Panel.fit(
        f"[bold]📊 Discovery Summary[/bold]\n\n"
        f"Total Discovered: [cyan]{len(discovery.discovered)}[/cyan]\n"
        f"Working: [green]{len(working)}[/green]\n"
        f"High Confidence: [yellow]{len(high_conf)}[/yellow]\n\n"
        f"[dim]Results exported to data/ directory[/dim]",
        border_style="green"
    ))
    
    return discovery


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="SMS Provider Discovery Tool - Find new SMS/OTP endpoints",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python discover_providers.py                     # Discover only
  python discover_providers.py 09123456789         # Discover and test
  python discover_providers.py 09123456789 --add   # Discover, test, and add to registry
  python discover_providers.py --no-export         # Discover without exporting
        """
    )
    
    parser.add_argument(
        "phone",
        nargs="?",
        help="Phone number to test discovered endpoints (format: 09xxxxxxxxx)"
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Don't export results to files"
    )
    parser.add_argument(
        "--add",
        action="store_true",
        help="Add working providers to the registry"
    )
    
    args = parser.parse_args()
    
    # Validate phone number if provided
    if args.phone:
        if not args.phone.startswith('09') or len(args.phone) != 11:
            console.print("[red]❌ Invalid phone number format. Use: 09xxxxxxxxx[/red]")
            sys.exit(1)
    
    print_banner()
    
    if args.phone:
        console.print(f"📱 Test Phone: [green]{args.phone}[/green]")
    else:
        console.print("[yellow]ℹ️  No phone number provided - endpoints won't be tested[/yellow]")
        console.print("[dim]   Use: python discover_providers.py 09123456789[/dim]")
    
    console.print()
    
    try:
        asyncio.run(run_discovery(
            phone=args.phone,
            export=not args.no_export,
            add_to_registry=args.add
        ))
    except KeyboardInterrupt:
        console.print("\n[yellow]❌ Discovery cancelled by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]❌ Error during discovery: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
