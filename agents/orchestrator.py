"""
Orchestrator: Coordinates all 4 agents in a CrewAI pipeline.
ResearchAgent -> SignalAgent -> SynthesisAgent -> LearningAgent
"""
import os
from crewai import Crew, Process
from loguru import logger
from agents.research_agent import create_research_agent, create_research_task
from agents.signal_agent import create_signal_agent, create_signal_task
from agents.synthesis_agent import create_synthesis_agent, create_synthesis_task
from agents.learning_agent import create_learning_agent, create_learning_task
from memory.knowledge_base import KnowledgeBase


class IntelOrchestrator:
    """
    The brain of the system. Runs the full intelligence pipeline:
    1. Research (gather raw data)
    2. Signal (filter and score)
    3. Synthesis (build insight narrative)
    4. Learning (process feedback, self-improve)
    """

    def __init__(self, config: dict, knowledge_base: KnowledgeBase):
        self.config = config
        self.kb = knowledge_base
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        logger.info(f"[Orchestrator] Initialized with model: {self.ollama_model}")

    def run_intelligence_cycle(self) -> dict:
        """
        Execute one full intelligence cycle.
        Returns: dict with 'brief', 'items', 'score_summary'
        """
        logger.info("[Orchestrator] Starting intelligence cycle...")

        # --- Build Agents ---
        research_agent = create_research_agent(self.ollama_model, self.ollama_base_url)
        signal_agent = create_signal_agent(self.ollama_model, self.ollama_base_url)
        synthesis_agent = create_synthesis_agent(self.ollama_model, self.ollama_base_url)
        learning_agent = create_learning_agent(self.ollama_model, self.ollama_base_url)

        # --- Build Tasks ---
        research_task = create_research_task(research_agent)
        signal_task = create_signal_task(signal_agent, context=[research_task])
        synthesis_task = create_synthesis_task(synthesis_agent, context=[signal_task])
        learning_task = create_learning_task(learning_agent, context=[synthesis_task])

        # --- Assemble Crew ---
        crew = Crew(
            agents=[research_agent, signal_agent, synthesis_agent, learning_agent],
            tasks=[research_task, signal_task, synthesis_task, learning_task],
            process=Process.sequential,
            verbose=True
        )

        # --- Run ---
        result = crew.kickoff()
        logger.info("[Orchestrator] Intelligence cycle complete.")

        return {
            "brief": str(result),
            "raw_output": result
        }

    def run_learning_cycle(self, feedback_data: list) -> None:
        """
        Standalone learning cycle — runs when user gives feedback.
        Does NOT run the full pipeline, only LearningAgent.
        """
        logger.info(f"[Orchestrator] Running learning cycle with {len(feedback_data)} feedback items")
        learning_agent = create_learning_agent(self.ollama_model, self.ollama_base_url)
        learning_task = create_learning_task(
            learning_agent,
            context=[],
            feedback_data=feedback_data
        )
        crew = Crew(
            agents=[learning_agent],
            tasks=[learning_task],
            process=Process.sequential,
            verbose=False
        )
        crew.kickoff()
        logger.info("[Orchestrator] Learning cycle complete.")
