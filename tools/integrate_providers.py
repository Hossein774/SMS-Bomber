#!/usr/bin/env python3

"""
Provider Integration Tool
Integrates discovered providers into the main provider registry.

Usage:
    python integrate_providers.py                   # Interactive mode
    python integrate_providers.py --auto            # Auto-add all working providers
    python integrate_providers.py --file providers.json  # Import from file
"""

import asyncio
import sys
import os
import json
import argparse

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm, IntPrompt

console = Console()


def load_discovered_providers(file_path: str = "data/discovered_providers.json"):
    """Load discovered providers from JSON file."""
    if not os.path.exists(file_path):
        console.print(f"[red]❌ File not found: {file_path}[/red]")
        console.print("[yellow]Run 'python discover_providers.py 09xxxxxxxxx' first[/yellow]")
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def display_providers(providers: list):
    """Display providers in a table."""
    table = Table(title="Discovered Providers")
    table.add_column("#", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("URL", style="blue", max_width=40)
    table.add_column("Confidence", justify="center")
    table.add_column("Working", justify="center")
    
    for i, p in enumerate(providers, 1):
        conf = f"{p.get('confidence', 0):.0%}"
        working = "✅" if p.get('working', False) else "❌"
        url = p['url'][:40] + "..." if len(p['url']) > 40 else p['url']
        
        table.add_row(str(i), p['name'], url, conf, working)
    
    console.print(table)


def add_providers_to_registry(providers: list):
    """Add providers to the main registry."""
    from sms_bomber.api.providers import ProviderRegistry, Provider
    
    # Read current providers.py
    providers_file = "sms_bomber/api/providers.py"
    
    with open(providers_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the end of default_providers list
    insert_marker = "        ]\n        self.providers.extend(default_providers)"
    
    if insert_marker not in content:
        console.print("[red]❌ Could not find insertion point in providers.py[/red]")
        return 0
    
    # Generate new provider code
    new_providers_code = ""
    for p in providers:
        data_str = str(p['data_template']).replace("'", '"')
        new_providers_code += f'''            Provider(
                name="{p['name']}",
                url="{p['url']}",
                data_template={p['data_template']},
            ),
'''
    
    # Add comment
    new_providers_code = f'''            # === Auto-discovered providers ===
{new_providers_code}'''
    
    # Insert into content
    new_content = content.replace(
        insert_marker,
        new_providers_code + "        ]\n        self.providers.extend(default_providers)"
    )
    
    # Write back
    with open(providers_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return len(providers)


def interactive_mode(providers: list):
    """Interactive provider selection."""
    console.print("\n[bold]🔧 Interactive Provider Integration[/bold]\n")
    
    # Filter working providers
    working = [p for p in providers if p.get('working', False)]
    high_conf = [p for p in providers if p.get('confidence', 0) >= 0.6]
    
    console.print(f"Total Discovered: {len(providers)}")
    console.print(f"Working: [green]{len(working)}[/green]")
    console.print(f"High Confidence: [yellow]{len(high_conf)}[/yellow]\n")
    
    display_providers(providers[:15])
    
    if len(providers) > 15:
        console.print(f"[dim]... and {len(providers) - 15} more[/dim]\n")
    
    console.print("\n[bold]Options:[/bold]")
    console.print("1. Add all working providers")
    console.print("2. Add high confidence providers (≥60%)")
    console.print("3. Select specific providers")
    console.print("4. Cancel")
    
    choice = IntPrompt.ask("Select option", choices=["1", "2", "3", "4"], default=1)
    
    if choice == 1:
        to_add = working
    elif choice == 2:
        to_add = high_conf
    elif choice == 3:
        # Select specific providers
        console.print("\nEnter provider numbers to add (comma-separated, e.g., 1,3,5):")
        selection = input("> ").strip()
        indices = [int(x.strip()) - 1 for x in selection.split(",") if x.strip().isdigit()]
        to_add = [providers[i] for i in indices if 0 <= i < len(providers)]
    else:
        console.print("[yellow]Cancelled[/yellow]")
        return
    
    if not to_add:
        console.print("[yellow]No providers selected[/yellow]")
        return
    
    if Confirm.ask(f"\nAdd {len(to_add)} providers to registry?"):
        added = add_providers_to_registry(to_add)
        console.print(f"[green]✅ Added {added} providers to registry![/green]")
        console.print("[cyan]Restart the bomber to use new providers[/cyan]")
    else:
        console.print("[yellow]Cancelled[/yellow]")


def main():
    parser = argparse.ArgumentParser(description="Integrate discovered providers")
    parser.add_argument("--auto", action="store_true", help="Auto-add all working providers")
    parser.add_argument("--file", help="JSON file with providers", default="data/discovered_providers.json")
    parser.add_argument("--min-confidence", type=float, default=0.5, help="Minimum confidence (0-1)")
    
    args = parser.parse_args()
    
    console.print("\n[bold cyan]🔧 Provider Integration Tool[/bold cyan]\n")
    
    # Load providers
    providers = load_discovered_providers(args.file)
    
    if not providers:
        return
    
    console.print(f"[green]✅ Loaded {len(providers)} discovered providers[/green]\n")
    
    if args.auto:
        # Auto mode - add all working providers above min confidence
        to_add = [
            p for p in providers 
            if p.get('working', False) and p.get('confidence', 0) >= args.min_confidence
        ]
        
        if to_add:
            console.print(f"Adding {len(to_add)} providers (confidence ≥ {args.min_confidence:.0%})...")
            added = add_providers_to_registry(to_add)
            console.print(f"[green]✅ Added {added} providers to registry![/green]")
        else:
            console.print("[yellow]No providers match the criteria[/yellow]")
    else:
        # Interactive mode
        interactive_mode(providers)


if __name__ == "__main__":
    main()
