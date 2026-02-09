"""
Background scheduler for automated research scanning.
Uses APScheduler for cron-based scheduling.
Can be started alongside the FastAPI server.
"""

import logging
from typing import Optional

from research_scanner.config import ScannerConfig
from research_scanner.scanner import ResearchScanner

logger = logging.getLogger(__name__)


class ScanScheduler:
    """Manages scheduled research scans."""

    def __init__(self, config: ScannerConfig = None):
        self.config = config or ScannerConfig()
        self.scanner = ResearchScanner(self.config)
        self.scheduler = None

    def _run_scheduled_scan(self):
        """Execute a scan (called by scheduler)."""
        logger.info("Scheduled scan starting...")
        try:
            results = self.scanner.run_scan()
            logger.info(f"Scheduled scan complete: indexed {results.get('papers_indexed', 0)} papers")
        except Exception as e:
            logger.error(f"Scheduled scan failed: {e}")

    def start(self):
        """Start the background scheduler."""
        if not self.config.schedule_enabled:
            logger.info("Scheduling is disabled in config")
            return

        try:
            from apscheduler.schedulers.background import BackgroundScheduler
            from apscheduler.triggers.cron import CronTrigger
        except ImportError:
            logger.warning(
                "APScheduler not installed. Install with: pip install apscheduler\n"
                "Falling back to manual scans only."
            )
            return

        self.scheduler = BackgroundScheduler()

        # Parse cron expression: "0 3 * * *" → minute=0, hour=3
        parts = self.config.schedule_cron.split()
        if len(parts) == 5:
            trigger = CronTrigger(
                minute=parts[0],
                hour=parts[1],
                day=parts[2],
                month=parts[3],
                day_of_week=parts[4],
            )
        else:
            logger.warning(f"Invalid cron expression: {self.config.schedule_cron}, using daily at 3 AM")
            trigger = CronTrigger(hour=3, minute=0)

        self.scheduler.add_job(
            self._run_scheduled_scan,
            trigger=trigger,
            id="research_scan",
            name="Research Paper Scanner",
            replace_existing=True,
        )

        self.scheduler.start()
        logger.info(f"Scan scheduler started with cron: {self.config.schedule_cron}")

        # Optionally run a scan on startup
        if self.config.schedule_on_startup:
            logger.info("Running startup scan...")
            self._run_scheduled_scan()

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scan scheduler stopped")


def start_scheduler(config: ScannerConfig = None) -> ScanScheduler:
    """Convenience function to create and start a scheduler."""
    scheduler = ScanScheduler(config)
    scheduler.start()
    return scheduler
