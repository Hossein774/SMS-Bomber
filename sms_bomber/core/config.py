# sms_bomber/core/config.py
from dataclasses import dataclass
from typing import Optional
import os
from pathlib import Path


@dataclass
class AppConfig:
    """Application configuration settings."""

    target: str
    count: int = 1
    threads: int = 5
    verbose: bool = False
    proxy: Optional[str] = None
    timeout: float = 2.5
    log_dir: Path = Path("logs")
    sms_only: bool = False
    calls_only: bool = False
    no_delay: bool = False
    call_delay: int = 20

    @property
    def proxy_dict(self) -> Optional[dict]:
        """Convert proxy string to dictionary format."""
        return {"http": self.proxy, "https": self.proxy} if self.proxy else None

    def validate(self) -> None:
        """Validate configuration settings."""
        if not self.target.isdigit():
            raise ValueError("Target phone number must contain only digits")
        if self.count < 1:
            raise ValueError("Count must be greater than 0")
        if self.threads < 1:
            raise ValueError("Thread count must be greater than 0")
        if not self.log_dir.exists():
            self.log_dir.mkdir(parents=True)
