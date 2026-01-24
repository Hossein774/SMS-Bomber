#!/usr/bin/env python3

"""
Call Provider Test Script
Test call bombing providers for functionality.
"""

import asyncio
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sms_bomber.api.call_providers import CallProviderRegistry
from sms_bomber.api.call_client import CallBomberClient


async def test_call_providers(phone_number: str = "09123456789"):
    """Test all call providers."""
    registry = CallProviderRegistry()
    client = CallBomberClient()
    
    providers = registry.get_all_providers()
    print(f"🧪 Testing {len(providers)} call providers...")
    print("=" * 50)
    
    results = {"success": 0, "failed": 0, "total": len(providers)}
    
    for provider in providers:
        data = provider.get_request_data(phone_number)
        result = await client.send_call_request(
            provider.name, provider.url, data, provider.method
        )
        
        if result["success"]:
            status = f"✅ {result.get('status_code', 'OK')}"
            results["success"] += 1
        else:
            status = f"❌ {result.get('error', 'Failed')}"
            results["failed"] += 1
            
        print(f"{status:15} {provider.name:20} [{provider.call_type}]")
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {results['success']}/{results['total']} successful ({results['success']/results['total']*100:.1f}%)")
    
    return results


async def test_by_type():
    """Test providers grouped by type."""
    registry = CallProviderRegistry()
    
    types = ["voice", "callback"]
    
    for call_type in types:
        providers = registry.get_providers_by_type(call_type)
        if providers:
            print(f"\n🎯 Testing {call_type.upper()} providers ({len(providers)} total):")
            print("-" * 40)
            
            client = CallBomberClient()
            for provider in providers:
                data = provider.get_request_data("09123456789")
                result = await client.send_call_request(
                    provider.name, provider.url, data, provider.method
                )
                
                status = "✅" if result["success"] else "❌"
                print(f"  {status} {provider.name}")


if __name__ == "__main__":
    print("📞 Call Bomber Provider Tester")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        phone = sys.argv[1]
        print(f"Testing with phone number: {phone}")
        asyncio.run(test_call_providers(phone))
    else:
        print("Testing with default phone number...")
        asyncio.run(test_call_providers())
        
        print("\nTesting by provider type...")
        asyncio.run(test_by_type())
