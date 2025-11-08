"""Mode-specific prompt templates for brief generation."""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class BriefPrompter:
    """Generates mode-specific prompts for brief generation."""

    SYSTEM_PROMPTS = {
        "summary": """You are an expert interview preparation assistant. Your task is to create a concise, well-structured summary for interview preparation.

Focus on:
- Key background information
- Notable achievements and expertise
- Relevant experience and insights
- Important context for the interview

Be factual, concise, and cite your sources.""",
        "technical": """You are a technical interview preparation specialist. Your task is to analyze technical expertise and capabilities.

Focus on:
- Technical skills and technologies
- Patents, publications, and innovations
- Technical leadership and architecture decisions
- Engineering philosophy and approaches

Provide concrete examples with citations.""",
        "biographical": """You are a biographical research specialist. Your task is to provide comprehensive background information.

Focus on:
- Career trajectory and key positions
- Educational background
- Notable projects and initiatives
- Leadership style and values

Present a cohesive narrative with citations.""",
        "strategic": """You are a strategic business analyst. Your task is to analyze strategic vision and business acumen.

Focus on:
- Strategic initiatives and vision
- Business model and market positioning
- Competitive landscape understanding
- Growth strategies and execution

Provide strategic insights with evidence.""",
    }

    USER_PROMPT_TEMPLATE = """Based on the following information about {company} and {person}, generate a comprehensive brief in {mode} mode.

RETRIEVED CONTEXT:
{context}

INSTRUCTIONS:
1. Synthesize the key information relevant to {mode} analysis
2. Structure your response with clear sections
3. Cite your sources using [chunk_id] format
4. Highlight the most important insights
5. Keep the response focused and actionable for interview preparation

Generate the brief now:"""

    def __init__(self):
        """Initialize prompter."""
        pass

    def get_system_prompt(self, mode: str) -> str:
        """
        Get system prompt for a given mode.

        Args:
            mode: Brief mode (summary/technical/biographical/strategic)

        Returns:
            System prompt string
        """
        if mode not in self.SYSTEM_PROMPTS:
            logger.warning(f"Unknown mode '{mode}', using 'summary'")
            mode = "summary"

        return self.SYSTEM_PROMPTS[mode]

    def build_prompt(
        self,
        company: str,
        person: str,
        mode: str,
        retrieved_chunks: List[Dict[str, Any]],
    ) -> tuple[str, str]:
        """
        Build complete prompt from retrieved chunks.

        Args:
            company: Company name
            person: Person name
            mode: Brief mode
            retrieved_chunks: List of retrieved chunk dicts

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Build context string from chunks
        context_parts = []
        for chunk in retrieved_chunks:
            entities_str = ", ".join([f"{e['type']}:{e['text']}" for e in chunk.get("entities", [])[:3]])
            context_parts.append(
                f"[{chunk['chunk_id']}] (Score: {chunk.get('score', 0):.3f}, Entities: {entities_str})\n"
                f"{chunk['text']}\n"
            )

        context = "\n---\n".join(context_parts)

        # Build user prompt
        user_prompt = self.USER_PROMPT_TEMPLATE.format(
            company=company,
            person=person,
            mode=mode,
            context=context,
        )

        system_prompt = self.get_system_prompt(mode)

        logger.info(f"Built {mode} prompt with {len(retrieved_chunks)} chunks ({len(context)} chars)")

        return system_prompt, user_prompt
