# Elite Intel System — Minimal Version

The production-ready version. No agent frameworks, no hallucinations, no BS.

## Setup (5 minutes)

### 1. Copy config and add API keys

```bash
cp .env.minimal .env

# Edit .env with:
# CLAUDE_API_KEY=sk-ant-...
# TELEGRAM_BOT_TOKEN=your_token
# TELEGRAM_CHAT_ID=your_chat_id
```

### 2. Install dependencies

```bash
pip install feedparser requests anthropic python-telegram-bot python-dotenv
```

### 3. Create data directory

```bash
mkdir -p data logs
```

### 4. Test the script

```bash
python minimal/fetch_and_score.py
```

**Expected output:**
```
[16:20:00] INFO: ============================================================
[16:20:00] INFO: 🚀 INTELLIGENCE CYCLE STARTING
[16:20:00] INFO: ============================================================
[16:20:00] INFO: Step 1: Fetching data...
[16:20:05] INFO: 📡 Fetched 15 items from RSS feeds
[16:20:06] INFO: 💰 Fetched 3 SEC filings
[16:20:07] INFO: 📰 Fetched 4 HN stories
[16:20:07] INFO: ✅ Total items fetched: 22
[16:20:07] INFO: Step 2: Scoring items...
[16:20:08] INFO: ✅ Elite items (score >= 70): 5
[16:20:08] INFO: Step 3: Calling Claude for synthesis...
[16:20:12] INFO: ✅ Claude response received
[16:20:12] INFO: Step 4: Saving and sending...
[16:20:13] INFO: ✅ Brief sent to Telegram
[16:20:13] INFO: ============================================================
[16:20:13] INFO: ✅ CYCLE COMPLETE in 13.2s
[16:20:13] INFO: ============================================================
```

### 5. Setup cron (automation)

```bash
crontab -e
```

Add this line:
```
*/30 7-18 * * 1-5 cd /path/to/elite-intel-agent && python minimal/fetch_and_score.py >> logs/job.log 2>&1
```

This runs every 30 minutes, Monday-Friday, 7am-6pm.

## What Happens

1. **Fetch (2s):** RSS feeds, SEC filings, HN top stories
2. **Score (1s):** Pure Python scoring logic (novelty, velocity, authority, actionability, cross-domain, asymmetry)
3. **Dedupe (0.5s):** SQLite check (don't send duplicate briefs)
4. **Claude (4s):** ONE API call to synthesize top 5-7 items into a brief
5. **Telegram (0.5s):** Send the brief to your phone

**Total time: ~10 seconds**

## How It Differs from the "Full" Version

| Aspect | Full Version | Minimal Version |
|--------|---|---|
| LLM Calls Per Cycle | 4+ (agents) | 1 (synthesis) |
| Complexity | 50+ files | 5 files |
| Latency | 20-30s | 8-12s |
| Cost | $2-5/day | $0.10/cycle |
| Hallucinations | Possible | Impossible |
| Debuggability | Hard | Easy |

## Cost Breakdown

- **Claude API:** 2 items × 350 tokens avg = 700 tokens per call
- **2 calls/hour × 24 × 365 = 17.5M tokens/year**
- **At $3/1M input tokens = ~$53/year**
- **At $15/1M output tokens = ~$260/year**
- **Total: ~$313/year = $26/month**

## Customization

### Change which sources to fetch

Edit `minimal/fetch_and_score.py` and modify the `feeds` list:

```python
feeds = [
    ("https://your-feed-url", "Source Name", ["domain1", "domain2"]),
    ...
]
```

### Adjust scoring weights

Edit `minimal/scoring_rules.py`:

```python
weights = {
    "novelty": 0.25,          # How much new info matters
    "velocity": 0.20,         # How much acceleration matters
    "source_authority": 0.15, # How much trust matters
    "actionability": 0.20,    # How much "can I act?" matters
    "cross_domain": 0.10,     # How much domain bridging matters
    "asymmetry": 0.10,        # How much obscurity matters
}
```

### Change Claude prompt

Edit the `generate_brief_with_claude()` function:

```python
prompt = f"""YOUR CUSTOM PROMPT HERE

{items_text}

Keep it under 350 words."""
```

## Monitoring

Check the logs:

```bash
tail -f logs/job.log
```

Or query the database:

```python
import sqlite3
conn = sqlite3.connect("data/intel.db")
cursor = conn.cursor()
cursor.execute("SELECT created_at, item_count FROM briefs ORDER BY created_at DESC LIMIT 10")
for row in cursor.fetchall():
    print(row)
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `ModuleNotFoundError: No module named 'feedparser'` | `pip install feedparser` |
| `No items found` | Check your internet and feeds are online |
| `Claude API call failed` | Check `CLAUDE_API_KEY` in `.env` |
| `Telegram send failed` | Check `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` |
| `Cron job not running` | Check `crontab -l` and see logs with `tail -f logs/job.log` |

## What Makes This "Elite"

Not magic. **Discipline.**

You get elite intelligence because:

1. **Selective sources** — You're not reading the news. You're reading regulatory filings, academic papers, insider trades, and technical discussions.
2. **Deterministic scoring** — You explicitly define what "signal" means. No LLM drift.
3. **Speed to action** — Your phone buzzes in <10 seconds. The market moves in minutes.

That's it.
