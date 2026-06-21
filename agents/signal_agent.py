"""
SignalAgent: Scores every intelligence item for elite relevance.
This agent separates true signal from noise using 6 dimensions.
"""
from crewai import Agent, Task
from langchain_ollama import ChatOllama
from typing import List


def create_signal_agent(model: str, base_url: str) -> Agent:
    llm = ChatOllama(model=model, base_url=base_url, temperature=0.2)

    return Agent(
        role="Elite Signal Intelligence Analyst",
        goal=(
            "Score every intelligence item on 6 dimensions (Novelty, Velocity, Source Authority, "
            "Actionability, Cross-Domain Connection, Asymmetry) and calculate a composite signal "
            "score from 0-100. Only items above the configured threshold pass to synthesis."
        ),
        backstory=(
            "You are a quant analyst and intelligence specialist who has spent years developing "
            "frameworks for separating actionable intelligence from noise. You have seen thousands "
            "of news cycles and know that 95% of what appears important is not. You look for: "
            "information that is not yet priced in, trends at their inflection points, and signals "
            "that connect across seemingly unrelated domains."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )


def create_signal_task(agent: Agent, context: List[Task]) -> Task:
    return Task(
        description=(
            "Take the raw intelligence items from the ResearchAgent and score each one.\n\n"
            "SCORING DIMENSIONS (each scored 0-10):\n\n"
            "1. NOVELTY (25%): Is this truly new? Has the market/public already absorbed this?\n"
            "   - 10: Completely new, no coverage anywhere\n"
            "   - 5: Some niche coverage, not mainstream\n"
            "   - 0: Already on CNN/BBC/NYT\n\n"
            "2. VELOCITY (20%): Is the trend accelerating?\n"
            "   - 10: 3x+ increase in related signals in last 6 hours\n"
            "   - 5: Steady increase\n"
            "   - 0: No momentum\n\n"
            "3. SOURCE AUTHORITY (15%): How credible is the source?\n"
            "   - 10: Primary source (SEC filing, patent, regulatory order)\n"
            "   - 7: Tier-1 academic/financial publication\n"
            "   - 3: General media\n\n"
            "4. ACTIONABILITY (20%): Can you make a strategic decision based on this?\n"
            "   - 10: Direct action possible (buy, sell, apply, partner, avoid)\n"
            "   - 5: Informs strategy, not immediate action\n"
            "   - 0: Pure awareness, no action possible\n\n"
            "5. CROSS-DOMAIN (10%): Does this connect multiple domains?\n"
            "   - 10: Connects 3+ domains (e.g., AI + defense + geopolitics)\n"
            "   - 5: Connects 2 domains\n"
            "   - 0: Single domain only\n\n"
            "6. ASYMMETRY (10%): Do less than 5% of smart people know this yet?\n"
            "   - 10: Buried in a filing, paper, or obscure source\n"
            "   - 5: Niche community knows\n"
            "   - 0: Everyone knows\n\n"
            "COMPOSITE SCORE = weighted average of all dimensions x 10\n\n"
            "Output items sorted by composite score, highest first.\n"
            "Include ONLY items with score >= 65 in the 'elite_signals' list.\n"
            "Include a brief RATIONALE for each score."
        ),
        agent=agent,
        context=context,
        expected_output=(
            "A JSON object with: "
            "'elite_signals' (list of scored items above threshold), "
            "'filtered_out' (count of items below threshold), "
            "'top_score' (highest score), "
            "'avg_score' (average score). "
            "Each elite signal includes all original fields plus: "
            "score_breakdown (dict of 6 dimensions), composite_score, rationale."
        )
    )
