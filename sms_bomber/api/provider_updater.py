# sms_bomber/api/provider_updater.py
import json
import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import asdict
from pathlib import Path
from ..core.logger import logging
from .providers import Provider, ProviderRegistry

logger = logging.getLogger("sms_bomber")


class ProviderUpdater:
    """Tool for updating and testing SMS providers."""

    def __init__(self, registry: ProviderRegistry):
        self.registry = registry
        self.test_phone = "09123456789"  # Default test number

    async def test_provider(self, provider: Provider, timeout: float = 5.0) -> Dict[str, Any]:
        """Test if a provider's endpoint is still active."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
        }
        
        data = provider.get_request_data(self.test_phone)
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.post(provider.url, json=data, headers=headers) as response:
                    result = {
                        "provider": provider.name,
                        "url": provider.url,
                        "status_code": response.status,
                        "active": response.status < 500,  # Consider 4xx as potentially active
                        "response_time": response.headers.get("X-Response-Time", "N/A"),
                        "error": None
                    }
                    
                    # Try to get response content (first 200 chars)
                    try:
                        content = await response.text()
                        result["response_preview"] = content[:200] if content else "Empty response"
                    except:
                        result["response_preview"] = "Could not read response"
                        
                    return result
                    
        except asyncio.TimeoutError:
            return {
                "provider": provider.name,
                "url": provider.url,
                "status_code": None,
                "active": False,
                "error": "Timeout"
            }
        except Exception as e:
            return {
                "provider": provider.name,
                "url": provider.url,
                "status_code": None,
                "active": False,
                "error": str(e)
            }

    async def test_all_providers(self, max_concurrent: int = 10) -> List[Dict[str, Any]]:
        """Test all providers concurrently."""
        providers = self.registry.get_all_providers()
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def bounded_test(provider):
            async with semaphore:
                return await self.test_provider(provider)
        
        logger.info(f"Testing {len(providers)} providers...")
        tasks = [bounded_test(provider) for provider in providers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = [r for r in results if isinstance(r, dict)]
        return valid_results

    def export_providers_to_json(self, file_path: str) -> None:
        """Export current providers to JSON file."""
        providers_data = []
        for provider in self.registry.get_all_providers():
            provider_dict = asdict(provider)
            providers_data.append(provider_dict)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(providers_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(providers_data)} providers to {file_path}")

    def import_providers_from_json(self, file_path: str) -> int:
        """Import providers from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                providers_data = json.load(f)
            
            imported_count = 0
            for provider_dict in providers_data:
                provider = Provider(**provider_dict)
                self.registry.add_provider(provider)
                imported_count += 1
            
            logger.info(f"Imported {imported_count} providers from {file_path}")
            return imported_count
            
        except Exception as e:
            logger.error(f"Failed to import providers: {str(e)}")
            return 0

    def generate_provider_report(self, test_results: List[Dict[str, Any]]) -> str:
        """Generate a detailed report of provider test results."""
        active_count = sum(1 for r in test_results if r.get("active", False))
        total_count = len(test_results)
        
        report = f"""
=== SMS Provider Test Report ===
Total Providers: {total_count}
Active Providers: {active_count}
Inactive Providers: {total_count - active_count}
Success Rate: {(active_count/total_count*100):.1f}%

=== Detailed Results ===
"""
        
        # Sort by status (active first)
        sorted_results = sorted(test_results, key=lambda x: (not x.get("active", False), x["provider"]))
        
        for result in sorted_results:
            status = "✅ ACTIVE" if result.get("active", False) else "❌ INACTIVE"
            error_info = f" ({result.get('error', 'Unknown error')})" if result.get("error") else ""
            status_code = result.get("status_code", "N/A")
            
            report += f"\n{status} - {result['provider']} (HTTP {status_code}){error_info}"
            report += f"\n  URL: {result['url']}"
            
            if result.get("response_preview"):
                preview = result["response_preview"].replace('\n', ' ')[:100]
                report += f"\n  Response: {preview}..."
            
            report += "\n"
        
        return report

    def remove_inactive_providers(self, test_results: List[Dict[str, Any]]) -> int:
        """Remove providers that failed testing."""
        inactive_providers = [r["provider"] for r in test_results if not r.get("active", False)]
        
        # Create new provider list without inactive ones
        active_providers = [
            p for p in self.registry.get_all_providers() 
            if p.name not in inactive_providers
        ]
        
        # Replace the provider list
        self.registry.providers = active_providers
        
        removed_count = len(inactive_providers)
        logger.info(f"Removed {removed_count} inactive providers")
        return removed_count

    async def update_and_clean_providers(self, export_backup: bool = True) -> Dict[str, Any]:
        """Complete provider update workflow."""
        if export_backup:
            backup_file = f"providers_backup_{int(asyncio.get_event_loop().time())}.json"
            self.export_providers_to_json(backup_file)
            logger.info(f"Created backup: {backup_file}")
        
        # Test all providers
        test_results = await self.test_all_providers()
        
        # Generate report
        report = self.generate_provider_report(test_results)
        
        # Count results
        active_count = sum(1 for r in test_results if r.get("active", False))
        total_count = len(test_results)
        
        return {
            "total_tested": total_count,
            "active_count": active_count,
            "inactive_count": total_count - active_count,
            "success_rate": (active_count/total_count*100) if total_count > 0 else 0,
            "report": report,
            "test_results": test_results
        }


# Example usage functions
async def quick_provider_test():
    """Quick test of all providers."""
    registry = ProviderRegistry()
    updater = ProviderUpdater(registry)
    
    print("🔍 Testing all SMS providers...")
    results = await updater.update_and_clean_providers()
    
    print(f"\n📊 Results:")
    print(f"Total: {results['total_tested']}")
    print(f"Active: {results['active_count']}")
    print(f"Success Rate: {results['success_rate']:.1f}%")
    
    print(f"\n📋 Detailed Report:")
    print(results['report'])
    
    return results

if __name__ == "__main__":
    asyncio.run(quick_provider_test())
