# sms_bomber/ui/console.py
from typing import Optional
from rich.console import Console
from rich.theme import Theme
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

from sms_bomber.core.config import AppConfig


class ConsoleUI:
    """Rich-based console user interface."""

    def __init__(self):
        self.theme = Theme(
            {"info": "cyan", "success": "green", "error": "red", "warning": "yellow"}
        )
        self.console = Console(theme=self.theme)

    def display_banner(self) -> None:
        """Display application banner."""
        banner = """
        ╔═══════════════════════════════════════╗
        ║         SMS & Call Bomber 2.0         ║
        ╚═══════════════════════════════════════╝
        """
        self.console.print(banner, style="cyan bold")

    def display_config(self, config: "AppConfig") -> None:
        """Display current configuration."""
        table = Table(title="Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Target", config.target)
        table.add_row("Count", str(config.count))
        table.add_row("Threads", str(config.threads))
        table.add_row("Proxy", config.proxy or "None")
        
        # Show bombing mode
        if config.sms_only:
            mode = "SMS Only"
        elif config.calls_only:
            mode = "Calls Only"
        else:
            mode = "SMS + Calls"
        table.add_row("Mode", mode)

        self.console.print(table)

    def create_progress(self) -> Progress:
        """Create a progress bar."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=self.console,
        )
