"""
LearningAgent: Processes user feedback to continuously improve signal scoring.
This is the self-learning core of the system.
"""
from crewai import Agent, Task
from langchain_ollama import ChatOllama
from typing import List, Optional


def create_learning_agent(model: str, base_url: str) -> Agent:
    llm = ChatOllama(model=model, base_url=base_url, temperature=0.1)

    return Agent(
        role="Adaptive Learning Specialist",
        goal=(
            "Analyze user feedback on delivered intelligence briefs and generate specific, "
            "quantified adjustments to the signal scoring system. "
            "Identify patterns in what the user finds valuable vs noise. "
            "Output concrete weight adjustments and preference profile updates."
        ),
        backstory=(
            "You are a machine learning specialist and behavioral economist. "
            "You have built recommendation systems that learn user preferences from minimal feedback. "
            "You understand that a single 'thumbs down' contains more information than 10 'thumbs up'. "
            "You look for patterns: which DOMAINS get consistent positive feedback, "
            "which SOURCE TYPES correlate with engagement, and which SIGNAL TYPES "
            "the user consistently ignores."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=2
    )


def create_learning_task(
    agent: Agent,
    context: List[Task],
    feedback_data: Optional[list] = None
) -> Task:
    feedback_str = ""
    if feedback_data:
        feedback_str = f"\n\nUSER FEEDBACK DATA:\n{feedback_data}\n"

    return Task(
        description=(
            "Analyze the performance of this intelligence cycle and generate learning updates.\n\n"
            f"{feedback_str}"
            "YOUR ANALYSIS TASKS:\n\n"
            "1. BRIEF PERFORMANCE REVIEW:\n"
            "   - Which sections of the brief got positive user feedback?\n"
            "   - Which signals were marked as noise?\n"
            "   - What patterns emerge from ignored content?\n\n"
            "2. WEIGHT ADJUSTMENT RECOMMENDATIONS:\n"
            "   - Generate specific delta values for each scoring dimension\n"
            "   - Generate domain preference score adjustments\n"
            "   - Identify sources to boost or deprioritize\n\n"
            "3. SOURCE QUALITY ASSESSMENT:\n"
            "   - Which sources generated the highest-rated signals?\n"
            "   - Are there gaps (domains with no signals) that need new sources?\n\n"
            "4. NEXT CYCLE RECOMMENDATIONS:\n"
            "   - Specific adjustments to improve the next brief\n"
            "   - Any new keywords or topics to add to monitoring\n"
            "   - Sources to add or remove"
        ),
        agent=agent,
        context=context,
        expected_output=(
            "A JSON object with: "
            "'weight_adjustments' (dict of dimension -> delta), "
            "'domain_adjustments' (dict of domain -> delta), "
            "'source_boosts' (list of source names), "
            "'source_penalties' (list of source names), "
            "'new_keywords' (list), "
            "'performance_summary' (string), "
            "'recommendations' (list of strings)"
        )
    )
