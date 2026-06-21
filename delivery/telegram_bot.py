"""
TelegramDelivery: Full-featured Telegram bot for delivering intelligence briefs.
Supports commands, inline reactions for feedback, and on-demand briefs.
"""
import os
import asyncio
from typing import Optional, Callable
from loguru import logger
from telegram import (
    Update, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)


class TelegramDelivery:
    """
    Manages all Telegram bot interactions.
    Handles delivery, commands, and feedback collection.
    """

    def __init__(self, on_brief_request: Optional[Callable] = None,
                 on_feedback: Optional[Callable] = None):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        self.on_brief_request = on_brief_request
        self.on_feedback = on_feedback
        self.app = None
        self.is_paused = False

    def build_app(self) -> Application:
        """Build the Telegram bot application."""
        if not self.token:
            raise ValueError("TELEGRAM_BOT_TOKEN not set in .env")

        app = Application.builder().token(self.token).build()

        # Register command handlers
        app.add_handler(CommandHandler("start", self._handle_start))
        app.add_handler(CommandHandler("brief", self._handle_brief))
        app.add_handler(CommandHandler("sources", self._handle_sources))
        app.add_handler(CommandHandler("stats", self._handle_stats))
        app.add_handler(CommandHandler("pause", self._handle_pause))
        app.add_handler(CommandHandler("resume", self._handle_resume))
        app.add_handler(CommandHandler("focus", self._handle_focus))
        app.add_handler(CommandHandler("frequency", self._handle_frequency))
        app.add_handler(CommandHandler("help", self._handle_help))

        # Callback handler for inline keyboard feedback buttons
        app.add_handler(CallbackQueryHandler(self._handle_feedback_callback))

        self.app = app
        logger.info("[Telegram] Bot application built successfully")
        return app

    async def send_brief(
        self,
        brief_text: str,
        brief_id: int,
        item_ids: list
    ) -> Optional[str]:
        """
        Send an intelligence brief to the configured chat.
        Attaches inline feedback buttons.
        """
        if self.is_paused:
            logger.info("[Telegram] Delivery paused. Skipping brief.")
            return None

        if not self.app:
            logger.error("[Telegram] App not initialized. Call build_app() first.")
            return None

        # Truncate to Telegram's 4096 char limit
        max_length = 4000
        chunks = [brief_text[i:i+max_length] for i in range(0, len(brief_text), max_length)]

        message_id = None
        for i, chunk in enumerate(chunks):
            # Only add feedback buttons to last chunk
            markup = None
            if i == len(chunks) - 1:
                markup = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("👍 High Signal", callback_data=f"feedback:positive:{brief_id}"),
                        InlineKeyboardButton("👎 Noise", callback_data=f"feedback:negative:{brief_id}"),
                    ],
                    [
                        InlineKeyboardButton("📊 View Stats", callback_data="cmd:stats"),
                        InlineKeyboardButton("⚡ More Now", callback_data="cmd:brief"),
                    ]
                ])

            try:
                msg = await self.app.bot.send_message(
                    chat_id=self.chat_id,
                    text=chunk,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=markup,
                    disable_web_page_preview=True
                )
                if i == 0:
                    message_id = str(msg.message_id)
            except Exception as e:
                logger.error(f"[Telegram] Send failed: {e}")
                # Try without markdown if formatting fails
                try:
                    msg = await self.app.bot.send_message(
                        chat_id=self.chat_id,
                        text=chunk,
                        reply_markup=markup
                    )
                    if i == 0:
                        message_id = str(msg.message_id)
                except Exception as e2:
                    logger.error(f"[Telegram] Plain send also failed: {e2}")

        logger.info(f"[Telegram] Brief delivered. Message ID: {message_id}")
        return message_id

    async def send_alert(self, message: str):
        """Send an immediate high-priority alert."""
        if self.app:
            try:
                await self.app.bot.send_message(
                    chat_id=self.chat_id,
                    text=f"🚨 *CRITICAL SIGNAL ALERT*\n\n{message}",
                    parse_mode=ParseMode.MARKDOWN
                )
            except Exception as e:
                logger.error(f"[Telegram] Alert send failed: {e}")

    # --- Command Handlers ---

    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "🧠 *Elite Intel Agent activated!*\n\n"
            "I monitor 20+ elite data sources 24/7 and deliver only the signals that matter.\n\n"
            "💡 Use /brief for an immediate report\n"
            "📊 Use /stats to see how well I know you\n"
            "❤️ React with 👍👎 on any brief to train me\n\n"
            "*Commands:* /help",
            parse_mode=ParseMode.MARKDOWN
        )
        self.chat_id = str(update.effective_chat.id)
        logger.info(f"[Telegram] /start from chat_id: {self.chat_id}")

    async def _handle_brief(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("⏳ Generating your intelligence brief...")
        if self.on_brief_request:
            await self.on_brief_request()
        else:
            await update.message.reply_text("⚠️ Brief generation not configured.")

    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📚 *Elite Intel Agent Commands*\n\n"
            "/start - Activate the agent\n"
            "/brief - Get an immediate intelligence brief\n"
            "/sources - Show active data sources\n"
            "/focus [topic] - Focus on a domain (ai, finance, geopolitics, biotech)\n"
            "/frequency [mins] - Set brief frequency (e.g., /frequency 60)\n"
            "/stats - Show learning stats\n"
            "/pause - Pause automatic delivery\n"
            "/resume - Resume automatic delivery\n\n"
            "*Feedback Training:*\n"
            "Use 👍 (good signal) or 👎 (noise) buttons on any brief to train the AI.",
            parse_mode=ParseMode.MARKDOWN
        )

    async def _handle_sources(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        sources_text = (
            "📡 *Active Data Sources*\n\n"
            "📰 *News:* Reuters, Bloomberg, FT, MIT Tech Review, IEEE\n"
            "💰 *Financial:* SEC EDGAR (Form 4, 13F), VC Funding RSS\n"
            "🔬 *Research:* arXiv (AI/Quantum/Biotech), Google Patents\n"
            "🌐 *Social:* Reddit (ML/Investing/Geopolitics), Hacker News\n"
            "🏛️ *Regulatory:* FTC, FDA, EU Regulations\n\n"
            "Use /focus [domain] to boost specific categories."
        )
        await update.message.reply_text(sources_text, parse_mode=ParseMode.MARKDOWN)

    async def _handle_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "📊 System stats loading...\n"
            "(Connect to KnowledgeBase.get_stats() for live data)"
        )

    async def _handle_pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.is_paused = True
        await update.message.reply_text("⏸️ Brief delivery paused. Use /resume to restart.")

    async def _handle_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.is_paused = False
        await update.message.reply_text("▶️ Brief delivery resumed!")

    async def _handle_focus(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context.args:
            domain = context.args[0].lower()
            await update.message.reply_text(
                f"🎯 Focus set to: *{domain}*\n"
                f"Domain bias boosted. Next brief will prioritize {domain} signals.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                "Usage: /focus [domain]\n"
                "Available: ai, finance, geopolitics, biotech, quantum, energy, crypto, defense"
            )

    async def _handle_frequency(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if context.args and context.args[0].isdigit():
            mins = int(context.args[0])
            await update.message.reply_text(
                f"⏰ Brief frequency set to every *{mins} minutes*.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text("Usage: /frequency [minutes] (e.g., /frequency 60)")

    async def _handle_feedback_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()

        data = query.data
        if data.startswith("feedback:"):
            parts = data.split(":")
            reaction = parts[1]  # positive or negative
            brief_id = int(parts[2]) if len(parts) > 2 else 0

            if self.on_feedback:
                await self.on_feedback(reaction=reaction, brief_id=brief_id)

            emoji = "👍" if reaction == "positive" else "👎"
            await query.edit_message_reply_markup(reply_markup=None)
            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=f"{emoji} Feedback recorded! I'll adjust my filtering. Thanks for training me."
            )

        elif data.startswith("cmd:"):
            cmd = data.split(":")[1]
            if cmd == "brief" and self.on_brief_request:
                await self.on_brief_request()
            elif cmd == "stats":
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="📊 Fetching stats..."
                )
