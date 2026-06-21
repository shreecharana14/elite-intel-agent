"""
IntelScheduler: Manages all scheduled jobs for the intelligence cycle.
Handles the periodic data ingestion, scoring, synthesis, and delivery pipeline.
"""
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from typing import Callable


class IntelScheduler:
    """
    Schedules and coordinates all background jobs:
    1. Main intelligence cycle (configurable interval)
    2. Daily learning cycle (reviews feedback, updates weights)
    3. Source health check (ensures all feeds are working)
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self.interval_minutes = int(os.getenv("SCHEDULE_INTERVAL_MINUTES", "60"))

    def add_intelligence_cycle(self, job_fn: Callable):
        """Schedule the main intelligence pipeline."""
        self.scheduler.add_job(
            job_fn,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id="intelligence_cycle",
            name="Main Intelligence Cycle",
            replace_existing=True,
            max_instances=1,
            misfire_grace_time=300  # Allow 5 min delay before skipping
        )
        logger.info(f"[Scheduler] Intelligence cycle scheduled every {self.interval_minutes} minutes")

    def add_learning_cycle(self, job_fn: Callable):
        """Schedule the daily self-learning cycle at 3am UTC."""
        self.scheduler.add_job(
            job_fn,
            trigger=CronTrigger(hour=3, minute=0),
            id="learning_cycle",
            name="Daily Self-Learning Cycle",
            replace_existing=True,
            max_instances=1
        )
        logger.info("[Scheduler] Learning cycle scheduled daily at 03:00 UTC")

    def add_source_health_check(self, job_fn: Callable):
        """Schedule hourly source health checks."""
        self.scheduler.add_job(
            job_fn,
            trigger=IntervalTrigger(hours=6),
            id="source_health_check",
            name="Source Health Check",
            replace_existing=True
        )
        logger.info("[Scheduler] Source health check scheduled every 6 hours")

    def update_interval(self, minutes: int):
        """Dynamically update the intelligence cycle interval."""
        self.interval_minutes = minutes
        job = self.scheduler.get_job("intelligence_cycle")
        if job:
            job.reschedule(trigger=IntervalTrigger(minutes=minutes))
            logger.info(f"[Scheduler] Interval updated to {minutes} minutes")

    def start(self):
        """Start the scheduler."""
        self.scheduler.start()
        logger.info("[Scheduler] Started")

    def shutdown(self):
        """Gracefully shutdown."""
        self.scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Shutdown")

    def get_jobs_status(self) -> list:
        """Return status of all scheduled jobs."""
        return [
            {
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time)
            }
            for job in self.scheduler.get_jobs()
        ]
