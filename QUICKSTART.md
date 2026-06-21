# Elite Intel System — Quick Start (5 Minutes)

**This is the production-ready version.** No frameworks, no LLM loops, just speed and reliability.

---

## 1. Setup (2 min)

```bash
# Clone the repo
git clone https://github.com/shreecharana14/elite-intel-agent.git
cd elite-intel-agent

# Copy config
cp .env.minimal .env

# Install dependencies
pip install feedparser requests anthropic python-telegram-bot beautifulsoup4 python-dotenv
```

---

## 2. Configure (2 min)

Edit `.env`:

```bash
nano .env
```

Add these 3 keys:

```
CLAUDE_API_KEY=sk-ant-your-actual-key
TELEGRAM_BOT_TOKEN=your-bot-token-from-@botfather
TELEGRAM_CHAT_ID=your-chat-id
```

**Get them here:**
- **Claude API Key**: https://console.anthropic.com
- **Telegram Bot Token**: Chat with @BotFather on Telegram
- **Telegram Chat ID**: Send `/start` to your bot, check the logs

---

## 3. Test (1 min)

```bash
mkdir -p data logs
python minimal/fetch_and_score.py
```

**Expected output:**
```
[16:20:00] INFO: ============================================================
[16:20:00] INFO: 🚀 INTELLIGENCE CYCLE STARTING
[16:20:00] INFO: Step 1: Fetching data...
[16:20:05] INFO: 📡 Fetched 15 items from RSS feeds
[16:20:06] INFO: 💰 Fetched 3 SEC filings
[16:20:07] INFO: 📰 Fetched 4 HN stories
[16:20:08] INFO: ✅ Elite items (score >= 70): 5
[16:20:12] INFO: ✅ Brief sent to Telegram
[16:20:12] INFO: ✅ CYCLE COMPLETE in 12.3s
```

---

## 4. Automate (Optional)

Run every 30 minutes via cron:

```bash
crontab -e
```

Add this line:
```
*/30 7-18 * * 1-5 cd /path/to/elite-intel-agent && python minimal/fetch_and_score.py >> logs/job.log 2>&1
```

This runs Monday-Friday, 7am-6pm. Adjust times as needed.

---

## What It Does

```
Every 30 minutes:

1. Fetch (2s)      → RSS, SEC filings, HN stories
2. Score (1s)      → Novelty + Velocity + Authority + Actionability + Cross-Domain + Asymmetry
3. Deduplicate (0.5s) → SQLite check (no duplicate briefs)
4. Claude (4s)     → ONE API call to write the brief
5. Send (0.5s)     → Telegram notification

Total: ~10 seconds
```

---

## Cost

- **Claude API**: ~$0.10 per cycle = $3/day = $87/month (if running 24/7 every 30 min)
- **Recommended**: Run only during market hours (7am-6pm) = ~$26/month

---

## Customize

### Change scoring weights

Edit `minimal/scoring_rules.py`:
```python
weights = {
    "novelty": 0.25,          # How much "is this new?" matters
    "velocity": 0.20,         # How much "is it accelerating?" matters
    "source_authority": 0.15, # How much "is this credible?" matters
    "actionability": 0.20,    # How much "can I act on this?" matters
    "cross_domain": 0.10,     # How much "does this bridge domains?" matters
    "asymmetry": 0.10,        # How much "do 95% not know this?" matters
}
```

### Add/remove data sources

Edit `minimal/fetch_and_score.py`:
```python
feeds = [
    ("https://your-feed-url", "Source Name", ["domain1", "domain2"]),
    ...
]
```

### Change Claude prompt

Edit `generate_brief_with_claude()` in `minimal/fetch_and_score.py`.

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | `pip install feedparser requests anthropic python-telegram-bot beautifulsoup4 python-dotenv` |
| "No items found" | Check internet, feed URLs are live |
| "Claude API failed" | Check `CLAUDE_API_KEY` in `.env` |
| "Telegram send failed" | Check `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` |
| Cron not running | Check `crontab -l`, see logs: `tail -f logs/job.log` |

---

## Architecture

**This is honest code:**

- ✅ Plain Python for 99% of tasks
- ✅ ONE LLM call (for the actual hard part: writing the brief)
- ✅ Deterministic scoring (no hallucinations)
- ✅ Fast (10 seconds end-to-end)
- ✅ Cheap ($26-87/month)
- ✅ Reliable (no agent framework failures)

**Not magic. Discipline.**

You get elite intelligence because:

1. **Selective sources** (SEC filings, arXiv, HN — not Twitter)
2. **Explicit scoring rules** (novelty × velocity × authority = signal)
3. **Speed to action** (your phone buzzes in <10s)

---

## Next Steps

1. ✅ Run the test
2. ✅ Set up cron
3. 📊 Monitor: `tail -f logs/job.log`
4. 🎯 Adjust scoring weights based on what matters to you

---

**That's it. You now have an elite intelligence system.**

Questions? Check `minimal/README.md` for more details.
