#!/usr/bin/env python3

"""
Quick SMS Provider Update Script
Run this to quickly test and update your SMS providers.
"""

import asyncio
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sms_bomber.api.providers import ProviderRegistry
from sms_bomber.api.provider_updater import ProviderUpdater


async def quick_update():
    """Quick provider update and cleanup."""
    print("🚀 SMS Bomber - Quick Provider Update")
    print("=" * 40)
    
    # Initialize
    registry = ProviderRegistry()
    updater = ProviderUpdater(registry)
    
    print(f"📋 Found {len(registry.get_all_providers())} providers")
    
    # Test all providers
    print("\n🔍 Testing providers (this may take a minute)...")
    results = await updater.update_and_clean_providers()
    
    # Show summary
    print("\n📊 Results:")
    print(f"  Total: {results['total_tested']}")
    print(f"  Active: {results['active_count']} ({results['success_rate']:.1f}%)")
    print(f"  Inactive: {results['inactive_count']}")
    
    # Ask about cleanup
    if results['inactive_count'] > 0:
        print(f"\n🗑️  Found {results['inactive_count']} inactive providers")
        response = input("Remove inactive providers? (y/n): ")
        
        if response.lower() == 'y':
            removed = updater.remove_inactive_providers(results['test_results'])
            print(f"✅ Removed {removed} inactive providers")
            print(f"📋 {len(updater.registry.get_all_providers())} providers remaining")
    
    # Show active providers
    print(f"\n✅ Active providers:")
    active_results = [r for r in results['test_results'] if r.get('active', False)]
    for result in active_results[:10]:  # Show first 10
        print(f"  • {result['provider']} (HTTP {result.get('status_code', 'N/A')})")
    
    if len(active_results) > 10:
        print(f"  ... and {len(active_results) - 10} more")
    
    print(f"\n🎯 Ready for SMS bombing with {len(active_results)} active providers!")
    
    return results


if __name__ == "__main__":
    try:
        asyncio.run(quick_update())
    except KeyboardInterrupt:
        print("\n❌ Update cancelled by user")
    except Exception as e:
        print(f"\n❌ Error during update: {str(e)}")
        sys.exit(1)
