"""
SynthesisAgent: Builds the elite intelligence brief from scored signals.
This is where dots get connected and insights are generated.
"""
from crewai import Agent, Task
from langchain_ollama import ChatOllama
from typing import List


def create_synthesis_agent(model: str, base_url: str) -> Agent:
    llm = ChatOllama(model=model, base_url=base_url, temperature=0.3)

    return Agent(
        role="Strategic Intelligence Synthesizer",
        goal=(
            "Transform scored signals into a concise, actionable intelligence brief. "
            "Connect dots across domains, identify second-order implications, and present "
            "insights in a format that allows immediate decision-making. "
            "Think like a $10B hedge fund's chief strategist."
        ),
        backstory=(
            "You are a seasoned strategist who has advised sovereign wealth funds, "
            "top-tier VCs, and government intelligence agencies. You are famous for "
            "your ability to see what others miss: the patent filing that predicted "
            "the acquisition, the regulatory shift that changed the industry, the "
            "hiring pattern that revealed a product pivot before it was announced. "
            "You write with precision. Every sentence either informs a decision or is cut."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=3
    )


def create_synthesis_task(agent: Agent, context: List[Task]) -> Task:
    return Task(
        description=(
            "Create an elite intelligence brief from the top signals provided by the SignalAgent.\n\n"
            "BRIEF FORMAT:\n\n"
            "🧠 ELITE INTEL BRIEF\n"
            "[Date & Time]\n\n"
            "🔴 CRITICAL SIGNALS (Score 88+)\n"
            "[If any exist — items requiring immediate attention]\n\n"
            "🟠 HIGH SIGNAL (Score 75-87)\n"
            "[2-3 most important insights with dot-connection analysis]\n\n"
            "🟡 WATCH LIST (Score 65-74)\n"
            "[2-3 emerging trends worth monitoring]\n\n"
            "🔗 CROSS-DOMAIN CONNECTIONS\n"
            "[1-2 non-obvious connections between signals from different domains]\n\n"
            "⚡ SECOND-ORDER IMPLICATIONS\n"
            "[What will LIKELY happen next as a result of these signals?]\n\n"
            "🎯 DECISION TRIGGERS\n"
            "[Specific conditions that should trigger action: IF X happens, THEN consider Y]\n\n"
            "RULES:\n"
            "- Maximum 700 words total\n"
            "- Every claim must be traceable to a source\n"
            "- No generic analysis. Only non-obvious insights\n"
            "- Write for someone who has 3 minutes and needs to make decisions\n"
            "- Use emojis for visual scanning in Telegram/WhatsApp"
        ),
        agent=agent,
        context=context,
        expected_output=(
            "A formatted intelligence brief in Markdown, ready to be sent to Telegram/WhatsApp. "
            "Includes all sections described in the format. Maximum 700 words. "
            "Ends with: 'Sources: [list of sources used]'"
        )
    )
