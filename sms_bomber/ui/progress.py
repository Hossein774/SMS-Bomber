# sms_bomber/ui/progress.py
from dataclasses import dataclass
from typing import Dict, List
from rich.progress import Progress
from rich.live import Live
from rich.table import Table


@dataclass
class ProgressStats:
    """Statistics for the bombing progress."""

    total: int = 0
    succeeded: int = 0
    failed: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        return (self.succeeded / self.total * 100) if self.total > 0 else 0


class ProgressTracker:
    """Track and display bombing progress."""

    def __init__(self, total_requests: int):
        self.stats = ProgressStats(total=total_requests)
        self.provider_stats: Dict[str, Dict[str, int]] = {}

    def update(self, result: Dict[str, any]) -> None:
        """Update progress statistics."""
        provider = result["provider"]
        success = result["success"]

        if provider not in self.provider_stats:
            self.provider_stats[provider] = {"succeeded": 0, "failed": 0}

        if success:
            self.stats.succeeded += 1
            self.provider_stats[provider]["succeeded"] += 1
        else:
            self.stats.failed += 1
            self.provider_stats[provider]["failed"] += 1

    def get_stats_table(self) -> Table:
        """Generate a rich table with current statistics."""
        table = Table(title="Bombing Statistics")
        table.add_column("Provider")
        table.add_column("Succeeded")
        table.add_column("Failed")
        table.add_column("Success Rate")

        for provider, stats in self.provider_stats.items():
            total = stats["succeeded"] + stats["failed"]
            success_rate = (stats["succeeded"] / total * 100) if total > 0 else 0
            table.add_row(
                provider,
                str(stats["succeeded"]),
                str(stats["failed"]),
                f"{success_rate:.1f}%",
            )

        return table
