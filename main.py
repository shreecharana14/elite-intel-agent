"""
Elite Intel Agent — Main Entry Point

Starts the full system:
1. Initializes memory (ChromaDB + SQLite)
2. Loads configuration
3. Sets up the 4-agent intelligence crew
4. Starts Telegram bot
5. Schedules intelligence cycles
6. Runs the async event loop
"""
import asyncio
import os
import yaml
from dotenv import load_dotenv
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from memory.vector_store import VectorStore
from memory.knowledge_base import KnowledgeBase
from ingestion.rss_fetcher import RSSFetcher
from ingestion.financial_data import FinancialDataFetcher
from ingestion.social_signals import SocialSignalFetcher
from ingestion.patent_monitor import PatentMonitor
from ingestion.regulatory_monitor import RegulatoryMonitor
from scoring.signal_scorer import SignalScorer
from scoring.feedback_learner import FeedbackLearner
from delivery.telegram_bot import TelegramDelivery
from delivery.whatsapp_bot import WhatsAppDelivery
from scheduler.job_scheduler import IntelScheduler
from agents.orchestrator import IntelOrchestrator

# Load environment variables
load_dotenv()

console = Console()


def load_config() -> dict:
    """Load YAML configuration files."""
    config = {}
    for config_file in ["config/sources.yaml", "config/scoring.yaml"]:
        try:
            with open(config_file, "r") as f:
                config.update(yaml.safe_load(f))
        except FileNotFoundError:
            logger.warning(f"[Config] {config_file} not found, using defaults")
    return config


async def run_intelligence_pipeline(
    config: dict,
    knowledge_base: KnowledgeBase,
    vector_store: VectorStore,
    scorer: SignalScorer,
    telegram: TelegramDelivery,
    whatsapp: WhatsAppDelivery,
    orchestrator: IntelOrchestrator
):
    """
    Execute one full intelligence pipeline cycle:
    Ingest -> Score -> Synthesize (via agents) -> Deliver
    """
    logger.info("====== INTELLIGENCE CYCLE STARTING ======")

    # 1. INGEST from all sources
    seen_ids = knowledge_base.get_seen_ids()

    rss = RSSFetcher(config, seen_ids=seen_ids)
    financial = FinancialDataFetcher(config)
    social = SocialSignalFetcher(config)
    patents = PatentMonitor(config)
    regulatory = RegulatoryMonitor(config)

    all_items = []
    all_items.extend(rss.fetch_all(max_age_hours=24))
    all_items.extend(financial.fetch_all())
    all_items.extend(social.fetch_all())
    all_items.extend(patents.fetch_all())
    all_items.extend(regulatory.fetch_all())

    logger.info(f"[Pipeline] Total raw items ingested: {len(all_items)}")

    if not all_items:
        logger.warning("[Pipeline] No new items found. Skipping cycle.")
        return

    # 2. DEDUPLICATE via vector store
    unique_items = []
    for item in all_items:
        if not vector_store.is_duplicate(f"{item.title} {item.raw_summary}"):
            unique_items.append(item)

    logger.info(f"[Pipeline] Unique items after deduplication: {len(unique_items)}")

    # 3. SCORE items
    domain_biases = knowledge_base.get_preference("domain_biases", {
        "ai": 1.0, "finance": 1.0, "geopolitics": 1.0,
        "biotech": 1.0, "quantum": 1.0, "energy": 1.0
    })
    scoring_weights = knowledge_base.get_scoring_weights()

    scorer_instance = SignalScorer(weights=scoring_weights, domain_biases=domain_biases)
    scored_items = scorer_instance.batch_score(unique_items, vector_store=vector_store)

    min_score = float(os.getenv("MIN_SIGNAL_SCORE", "65"))
    elite_items = [item for item in scored_items if item["composite_score"] >= min_score]

    logger.info(f"[Pipeline] Elite items (score >= {min_score}): {len(elite_items)}")

    # Check for critical signals (score >= 88)
    critical_items = [i for i in elite_items if i["composite_score"] >= 88]
    if critical_items:
        alert_text = f"🚨 CRITICAL SIGNAL: {critical_items[0]['title']}\n{critical_items[0]['url']}"
        await telegram.send_alert(alert_text)
        whatsapp.send_alert(alert_text)

    # Store all scored items
    for item in scored_items:
        knowledge_base.store_item(item)
        knowledge_base.mark_seen(item["id"])
        vector_store.add_item(
            item_id=item["id"],
            text=f"{item['title']} {item['raw_summary']}",
            metadata={
                "source": item["source"],
                "domain": str(item["domain"]),
                "score": item["composite_score"],
                "timestamp": item["timestamp"]
            }
        )

    if not elite_items:
        logger.info("[Pipeline] No elite items found above threshold. No brief sent.")
        return

    # 4. SYNTHESIZE via agents
    max_items = int(os.getenv("MAX_BRIEF_ITEMS", "7"))
    top_items_for_brief = elite_items[:max_items]

    try:
        # Prepare context string for agents
        items_context = "\n\n".join([
            f"ITEM {i+1} [Score: {item['composite_score']}]:\n"
            f"Title: {item['title']}\n"
            f"Source: {item['source']}\n"
            f"Domain: {item['domain']}\n"
            f"Summary: {item['raw_summary'][:400]}\n"
            f"Rationale: {item['rationale']}"
            for i, item in enumerate(top_items_for_brief)
        ])

        result = orchestrator.run_intelligence_cycle()
        brief_text = result.get("brief", items_context)

    except Exception as e:
        logger.error(f"[Pipeline] Agent synthesis failed: {e}. Using direct format.")
        # Fallback: format brief directly without agents
        brief_text = _format_brief_fallback(top_items_for_brief)

    # 5. DELIVER
    item_ids = [item["id"] for item in top_items_for_brief]
    brief_id = knowledge_base.store_brief(brief_text, item_ids)

    msg_id = await telegram.send_brief(brief_text, brief_id, item_ids)
    if msg_id:
        logger.info(f"[Pipeline] Brief #{brief_id} delivered via Telegram")

    wa_sid = whatsapp.send_brief(brief_text)
    if wa_sid:
        logger.info(f"[Pipeline] Brief #{brief_id} delivered via WhatsApp")

    logger.info("====== INTELLIGENCE CYCLE COMPLETE ======")


def _format_brief_fallback(items: list) -> str:
    """Fallback formatter when agents are unavailable."""
    from datetime import datetime
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    critical = [i for i in items if i["composite_score"] >= 88]
    high = [i for i in items if 75 <= i["composite_score"] < 88]
    watch = [i for i in items if i["composite_score"] < 75]

    lines = [f"🧠 *ELITE INTEL BRIEF*\n{now}\n"]

    if critical:
        lines.append("🔴 *CRITICAL SIGNALS*")
        for item in critical:
            lines.append(f"• [{item['source']}] {item['title']}\n  Score: {item['composite_score']} | {item['url']}")

    if high:
        lines.append("\n🟠 *HIGH SIGNAL*")
        for item in high:
            lines.append(f"• [{item['source']}] {item['title']}\n  {item['raw_summary'][:200]}...\n  🔗 {item['url']}")

    if watch:
        lines.append("\n🟡 *WATCH LIST*")
        for item in watch:
            lines.append(f"• [{item['source']}] {item['title']} (Score: {item['composite_score']})")

    lines.append("\n---\n_React 👍👎 to train the AI_")
    return "\n".join(lines)


async def main():
    """Main async entry point."""
    console.print(Panel(
        Text("🧠 Elite Intel Agent\nStarting up...", justify="center"),
        style="bold blue"
    ))

    # Load config
    config = load_config()
    logger.info("[Main] Configuration loaded")

    # Initialize memory
    data_dir = os.getenv("DATA_DIR", "./data")
    os.makedirs(data_dir, exist_ok=True)

    knowledge_base = KnowledgeBase(data_dir=data_dir)
    vector_store = VectorStore(data_dir=f"{data_dir}/chromadb")
    scorer = SignalScorer(
        weights=knowledge_base.get_scoring_weights(),
        domain_biases=knowledge_base.get_preference("domain_biases", {})
    )
    learner = FeedbackLearner(knowledge_base=knowledge_base)
    orchestrator = IntelOrchestrator(config=config, knowledge_base=knowledge_base)

    # Initialize delivery
    telegram = TelegramDelivery(
        on_brief_request=lambda: asyncio.create_task(
            run_intelligence_pipeline(config, knowledge_base, vector_store, scorer, telegram, whatsapp, orchestrator)
        ),
        on_feedback=lambda reaction, brief_id: asyncio.create_task(
            asyncio.coroutine(lambda: learner.process_feedback("last", brief_id, reaction))()
        )
    )
    whatsapp = WhatsAppDelivery()

    # Build Telegram app
    telegram_app = telegram.build_app()

    # Initialize scheduler
    scheduler = IntelScheduler()
    scheduler.add_intelligence_cycle(
        lambda: asyncio.create_task(
            run_intelligence_pipeline(config, knowledge_base, vector_store, scorer, telegram, whatsapp, orchestrator)
        )
    )
    scheduler.add_learning_cycle(
        lambda: learner.run_learning_cycle()
    )

    # Start scheduler
    scheduler.start()

    # Log startup stats
    stats = knowledge_base.get_stats()
    vs_stats = vector_store.get_stats()
    logger.info(f"[Main] Memory: {stats}")
    logger.info(f"[Main] Vector store: {vs_stats}")

    console.print(Panel(
        f"[green]✅ Elite Intel Agent Running![/green]\n\n"
        f"Schedule: Every {os.getenv('SCHEDULE_INTERVAL_MINUTES', '60')} minutes\n"
        f"Domains: {os.getenv('INTEREST_DOMAINS', 'all')}\n"
        f"Items in memory: {vs_stats['total_items']}\n"
        f"Min signal score: {os.getenv('MIN_SIGNAL_SCORE', '65')}",
        title="Status"
    ))

    # Start Telegram bot (this blocks until stopped)
    logger.info("[Main] Starting Telegram bot...")
    async with telegram_app:
        await telegram_app.initialize()
        await telegram_app.start()
        await telegram_app.updater.start_polling(drop_pending_updates=True)

        logger.info("[Main] System fully operational. Waiting for scheduled cycles...")

        # Keep running
        try:
            await asyncio.Event().wait()
        except (KeyboardInterrupt, SystemExit):
            logger.info("[Main] Shutdown signal received")
        finally:
            scheduler.shutdown()
            await telegram_app.updater.stop()
            await telegram_app.stop()
            logger.info("[Main] Graceful shutdown complete")


if __name__ == "__main__":
    # Configure logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logger.add(
        "logs/elite_intel_{time}.log",
        rotation="1 day",
        retention="7 days",
        level=log_level
    )
    os.makedirs("logs", exist_ok=True)
    asyncio.run(main())
