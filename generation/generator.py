"""Multi-model LLM generation with OpenAI and Anthropic support."""
import logging
import re
from typing import Dict, Any, List
from config import (
    OPENAI_API_KEY,
    ANTHROPIC_API_KEY,
    GENERATION_MODEL,
    GENERATION_TEMPERATURE,
    MAX_TOKENS,
    ENABLE_STREAMING,
)

logger = logging.getLogger(__name__)


class MultiModelGenerator:
    """Handles LLM generation with support for multiple providers."""

    def __init__(self, model: str = GENERATION_MODEL):
        """
        Initialize generator with specified model.

        Args:
            model: Model name (gpt-4o, claude-3-5-sonnet-20241022, etc.)
        """
        self.model = model
        self._init_client()

    def _init_client(self):
        """Initialize appropriate client based on model."""
        if "gpt" in self.model.lower() or "o1" in self.model.lower():
            if not OPENAI_API_KEY:
                logger.warning("No OpenAI API key, will use mock generation")
                self.client = None
                self.provider = "mock"
            else:
                from openai import OpenAI
                self.client = OpenAI(api_key=OPENAI_API_KEY)
                self.provider = "openai"
        elif "claude" in self.model.lower():
            if not ANTHROPIC_API_KEY:
                logger.warning("No Anthropic API key, will use mock generation")
                self.client = None
                self.provider = "mock"
            else:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=ANTHROPIC_API_KEY)
                self.provider = "anthropic"
        else:
            logger.warning(f"Unknown model {self.model}, using mock generation")
            self.client = None
            self.provider = "mock"

        logger.info(f"Initialized {self.provider} generator with model: {self.model}")

    def generate(
        self, system_prompt: str, user_prompt: str, temperature: float = GENERATION_TEMPERATURE
    ) -> str:
        """
        Generate response using configured model.

        Args:
            system_prompt: System/role prompt
            user_prompt: User query/instruction
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        logger.info(f"Generating with {self.provider} ({self.model})")

        if self.provider == "openai":
            return self._generate_openai(system_prompt, user_prompt, temperature)
        elif self.provider == "anthropic":
            return self._generate_anthropic(system_prompt, user_prompt, temperature)
        else:
            return self._generate_mock(system_prompt, user_prompt)

    def _generate_openai(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        """Generate using OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=MAX_TOKENS,
                stream=ENABLE_STREAMING,
            )

            if ENABLE_STREAMING:
                # Collect streamed response
                chunks = []
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        chunks.append(chunk.choices[0].delta.content)
                return "".join(chunks)
            else:
                return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            return self._generate_mock(system_prompt, user_prompt)

    def _generate_anthropic(self, system_prompt: str, user_prompt: str, temperature: float) -> str:
        """Generate using Anthropic API."""
        try:
            response = self.client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                temperature=temperature,
                max_tokens=MAX_TOKENS,
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            return self._generate_mock(system_prompt, user_prompt)

    def _generate_mock(self, system_prompt: str, user_prompt: str) -> str:
        """Generate mock response for testing."""
        return (
            "## Mock Generated Brief\n\n"
            "This is a mock response generated without API access.\n\n"
            "**Summary**: The available information suggests significant expertise and experience.\n\n"
            "**Key Insights**:\n"
            "- Notable background in the field [source#0#0]\n"
            "- Demonstrated leadership capabilities [source#1#0]\n"
            "- Strong technical foundation [source#2#0]\n\n"
            "**Citations**: [source#0#0], [source#1#0], [source#2#0]\n\n"
            "*Note: This is a mock response. Configure API keys for real generation.*"
        )

    def extract_citations(self, text: str) -> List[str]:
        """
        Extract citation chunk IDs from generated text.

        Args:
            text: Generated text with citations in [chunk_id] format

        Returns:
            List of unique chunk IDs
        """
        # Find all [chunk_id] patterns
        pattern = r'\[([^\]]+#\d+#\d+)\]'
        matches = re.findall(pattern, text)
        return list(set(matches))
