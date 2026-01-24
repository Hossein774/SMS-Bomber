#!/usr/bin/env python3
"""
Quick Provider Tester & Adder
Use this to test new API endpoints and add working ones to the bomber.

Usage:
    python add_provider.py "ServiceName" "https://api.example.com/send-otp" "phone={phone}"
    python add_provider.py --test "https://api.example.com/send-otp?phone=09123456789"
"""

import asyncio
import aiohttp
import sys
import os
import re

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


async def test_url(url: str, method: str = "GET", data: dict = None):
    """Test if a URL works."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'fa-IR,fa;q=0.9,en;q=0.8',
        'Referer': 'https://www.google.com/',
        'Origin': url.split('/')[0] + '//' + url.split('/')[2],
    }
    
    timeout = aiohttp.ClientTimeout(total=10)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            if method.upper() == "GET":
                async with session.get(url, headers=headers) as resp:
                    text = await resp.text()
                    return {
                        'status': resp.status,
                        'success': resp.status in [200, 201, 202],
                        'response': text[:300]
                    }
            else:
                headers['Content-Type'] = 'application/json'
                async with session.post(url, json=data, headers=headers) as resp:
                    text = await resp.text()
                    return {
                        'status': resp.status,
                        'success': resp.status in [200, 201, 202],
                        'response': text[:300]
                    }
    except Exception as e:
        return {'status': 0, 'success': False, 'response': str(e)}


def add_provider_to_file(name: str, url: str, data_template: dict):
    """Add a new provider to providers.py"""
    providers_file = os.path.join(os.path.dirname(__file__), 'sms_bomber', 'api', 'providers.py')
    
    with open(providers_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find insertion point (before the closing bracket)
    insert_marker = "        ]\n        self.providers.extend(default_providers)"
    
    if insert_marker not in content:
        print("❌ Could not find insertion point")
        return False
    
    # Create new provider code
    new_provider = f'''            Provider(
                name="{name}",
                url="{url}",
                data_template={data_template},
            ),
'''
    
    new_content = content.replace(insert_marker, new_provider + insert_marker)
    
    with open(providers_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    return True


async def interactive_mode():
    """Interactive mode to test and add providers."""
    print("🔧 Provider Tester & Adder")
    print("=" * 50)
    print("\nHow to find API endpoints:")
    print("1. Open the website (e.g., torob.com)")
    print("2. Open Browser DevTools (F12)")
    print("3. Go to Network tab")
    print("4. Enter your phone number and click 'Send Code'")
    print("5. Look for the API request in Network tab")
    print("6. Copy the URL and paste it here")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Test a URL")
        print("2. Add a working provider")
        print("3. Exit")
        
        choice = input("\nSelect option (1/2/3): ").strip()
        
        if choice == "1":
            url = input("Enter URL to test (with phone number): ").strip()
            if not url:
                continue
            
            # Detect method
            method = "GET" if "?" in url else "POST"
            print(f"\n🔍 Testing {method} {url[:60]}...")
            
            result = await test_url(url, method)
            
            if result['success']:
                print(f"✅ SUCCESS! Status: {result['status']}")
            else:
                print(f"❌ FAILED! Status: {result['status']}")
            
            print(f"Response: {result['response'][:200]}")
            
        elif choice == "2":
            name = input("Provider name (e.g., Torob): ").strip()
            url = input("API URL (use {phone} as placeholder): ").strip()
            
            # Parse data template
            print("Data template options:")
            print("  1. phone={phone}")
            print("  2. mobile={phone}")
            print("  3. phoneNumber={phone}")
            print("  4. Custom")
            
            data_choice = input("Select (1/2/3/4): ").strip()
            
            if data_choice == "1":
                data_template = {"phone": "{phone}"}
            elif data_choice == "2":
                data_template = {"mobile": "{phone}"}
            elif data_choice == "3":
                data_template = {"phoneNumber": "{phone}"}
            else:
                custom = input("Enter as Python dict (e.g., {'phone': '{phone}'}): ").strip()
                try:
                    data_template = eval(custom)
                except:
                    print("❌ Invalid format")
                    continue
            
            # Test first
            test_url_with_phone = url.replace("{phone}", "09123456789")
            print(f"\n🔍 Testing {test_url_with_phone[:60]}...")
            
            result = await test_url(test_url_with_phone)
            
            if result['success']:
                print(f"✅ Works! Status: {result['status']}")
                
                if input("Add to providers? (y/n): ").lower() == 'y':
                    if add_provider_to_file(name, url, data_template):
                        print(f"✅ Added {name} to providers!")
                    else:
                        print("❌ Failed to add")
            else:
                print(f"❌ Failed! Status: {result['status']}")
                print(f"Response: {result['response'][:200]}")
                
                if input("Add anyway? (y/n): ").lower() == 'y':
                    if add_provider_to_file(name, url, data_template):
                        print(f"✅ Added {name} to providers!")
        
        elif choice == "3":
            break


async def quick_test(url: str):
    """Quick test a single URL."""
    print(f"🔍 Testing: {url[:80]}...")
    method = "GET" if "?" in url else "POST"
    result = await test_url(url, method)
    
    if result['success']:
        print(f"✅ SUCCESS! Status: {result['status']}")
    else:
        print(f"❌ FAILED! Status: {result['status']}")
    
    print(f"Response: {result['response']}")


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test" and len(sys.argv) > 2:
            asyncio.run(quick_test(sys.argv[2]))
        elif len(sys.argv) >= 4:
            # Quick add: name, url, data
            name = sys.argv[1]
            url = sys.argv[2]
            data_str = sys.argv[3]
            
            try:
                # Parse data template
                if "=" in data_str:
                    # Format: phone={phone}
                    parts = data_str.split("=")
                    data_template = {parts[0]: parts[1]}
                else:
                    data_template = eval(data_str)
                
                if add_provider_to_file(name, url, data_template):
                    print(f"✅ Added {name}!")
                else:
                    print("❌ Failed")
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            asyncio.run(interactive_mode())
    else:
        asyncio.run(interactive_mode())


if __name__ == "__main__":
    main()
