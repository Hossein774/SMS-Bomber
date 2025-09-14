#!/usr/bin/env python3

"""
SMS Bomber Provider Management Tool
Use this script to test, update, and manage SMS providers.
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sms_bomber.api.providers import ProviderRegistry, Provider
from sms_bomber.api.provider_updater import ProviderUpdater
from sms_bomber.core.logger import setup_logger


async def test_providers(args):
    """Test all providers and show results."""
    registry = ProviderRegistry()
    updater = ProviderUpdater(registry)
    
    print("🔍 Testing all SMS providers...")
    results = await updater.update_and_clean_providers(export_backup=False)
    
    print(f"\n📊 Summary:")
    print(f"  Total Providers: {results['total_tested']}")
    print(f"  Active: {results['active_count']} ({results['success_rate']:.1f}%)")
    print(f"  Inactive: {results['inactive_count']}")
    
    if args.verbose:
        print(f"\n📋 Detailed Report:")
        print(results['report'])
    
    if args.remove_inactive:
        removed = updater.remove_inactive_providers(results['test_results'])
        print(f"\n🗑️  Removed {removed} inactive providers")


def add_provider(args):
    """Add a new provider interactively."""
    registry = ProviderRegistry()
    
    print("➕ Adding new SMS provider")
    print("=" * 40)
    
    name = args.name or input("Provider name: ")
    url = args.url or input("API URL: ")
    
    print("\nData template format:")
    print("  Use {phone} as placeholder for phone number")
    print("  Example: {'mobile': '{phone}', 'type': 'sms'}")
    
    if args.data:
        try:
            data_template = eval(args.data)
        except:
            print("❌ Invalid data template format")
            return
    else:
        data_input = input("Data template (as Python dict): ")
        try:
            data_template = eval(data_input)
        except:
            print("❌ Invalid data template format")
            return
    
    # Create and add provider
    provider = Provider(name=name, url=url, data_template=data_template)
    registry.add_provider(provider)
    
    print(f"✅ Added provider: {name}")
    
    # Test the new provider
    if input("\nTest new provider? (y/n): ").lower() == 'y':
        updater = ProviderUpdater(registry)
        print("🔍 Testing new provider...")
        result = asyncio.run(updater.test_provider(provider))
        
        status = "✅ ACTIVE" if result.get("active", False) else "❌ INACTIVE"
        print(f"{status} - {result.get('status_code', 'N/A')}")
        if result.get("error"):
            print(f"Error: {result['error']}")


def list_providers(args):
    """List all current providers."""
    registry = ProviderRegistry()
    providers = registry.get_all_providers()
    
    print(f"📋 Current SMS Providers ({len(providers)} total)")
    print("=" * 50)
    
    for i, provider in enumerate(providers, 1):
        print(f"{i:2d}. {provider.name}")
        if args.verbose:
            print(f"     URL: {provider.url}")
            print(f"     Data: {provider.data_template}")
            print()


def export_providers(args):
    """Export providers to JSON file."""
    registry = ProviderRegistry()
    updater = ProviderUpdater(registry)
    
    output_file = args.output or "providers_export.json"
    updater.export_providers_to_json(output_file)
    print(f"✅ Exported providers to: {output_file}")


def import_providers(args):
    """Import providers from JSON file."""
    if not os.path.exists(args.file):
        print(f"❌ File not found: {args.file}")
        return
    
    registry = ProviderRegistry()
    updater = ProviderUpdater(registry)
    
    count = updater.import_providers_from_json(args.file)
    print(f"✅ Imported {count} providers from: {args.file}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="SMS Bomber Provider Management")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test all providers")
    test_parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed results")
    test_parser.add_argument("--remove-inactive", action="store_true", help="Remove inactive providers")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add new provider")
    add_parser.add_argument("--name", help="Provider name")
    add_parser.add_argument("--url", help="API URL")
    add_parser.add_argument("--data", help="Data template as string")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all providers")
    list_parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed info")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export providers to JSON")
    export_parser.add_argument("-o", "--output", help="Output file path")
    
    # Import command
    import_parser = subparsers.add_parser("import", help="Import providers from JSON")
    import_parser.add_argument("file", help="JSON file to import")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Setup logging
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    setup_logger(log_dir)
    
    # Execute command
    if args.command == "test":
        asyncio.run(test_providers(args))
    elif args.command == "add":
        add_provider(args)
    elif args.command == "list":
        list_providers(args)
    elif args.command == "export":
        export_providers(args)
    elif args.command == "import":
        import_providers(args)


if __name__ == "__main__":
    main()
