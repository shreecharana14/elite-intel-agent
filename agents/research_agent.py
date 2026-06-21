"""
ResearchAgent: Gathers raw intelligence from all configured sources.
This agent is the 'eyes and ears' of the system.
"""
from crewai import Agent, Task
from langchain_ollama import ChatOllama


def create_research_agent(model: str, base_url: str) -> Agent:
    llm = ChatOllama(model=model, base_url=base_url, temperature=0.1)

    return Agent(
        role="Elite Intelligence Researcher",
        goal=(
            "Gather the most relevant, high-signal raw intelligence from all configured "
            "data sources. Focus on PRIMARY sources: regulatory filings, patent applications, "
            "insider transactions, academic preprints, and expert commentary. "
            "Prioritize information that the general public does NOT yet have access to."
        ),
        backstory=(
            "You are a former intelligence analyst trained to separate signal from noise. "
            "You know that the best intelligence comes from reading what no one else reads: "
            "SEC filings before they trend, patent applications before products launch, "
            "and academic papers before they reach mainstream media. "
            "You never summarize what everyone already knows."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5
    )


def create_research_task(agent: Agent) -> Task:
    return Task(
        description=(
            "Perform a comprehensive intelligence sweep across all active data sources. "
            "\n\nYour job:\n"
            "1. Review the latest items from all RSS feeds, financial APIs, patent databases, "
            "   regulatory sources, and social signal monitors.\n"
            "2. Identify items that are NOVEL (not seen before), TIMELY (last 24 hours), "
            "   and from HIGH-AUTHORITY sources.\n"
            "3. Group findings by domain: [AI, Finance, Geopolitics, Biotech, Quantum, Energy, Defense]\n"
            "4. For each item include: title, source, url, domain, raw_summary, timestamp\n"
            "5. Flag any item that appears to be a PRIMARY source (not a media report about it)\n"
            "\nOutput: A structured JSON list of raw intelligence items."
        ),
        agent=agent,
        expected_output=(
            "A JSON array of intelligence items, each with: "
            "title, source, url, domain, raw_summary, timestamp, is_primary_source (bool), "
            "initial_importance (low/medium/high/critical)"
        )
    )
