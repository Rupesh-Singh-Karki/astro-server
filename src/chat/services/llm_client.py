from typing import Any, Dict, Literal
import os

try:
    import openai
except Exception:  # pragma: no cover - external dependency
    openai = None

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - external dependency
    genai = None

from src.utils.logger import logger

log = logger(__name__)


class LLMClient:
    """LLM client supporting both OpenAI and Google Gemini APIs.

    Priority:
    1. If GEMINI_API_KEY is set, uses Gemini
    2. If OPENAI_API_KEY is set, uses OpenAI
    3. Otherwise, raises error

    Environment Variables:
    - GEMINI_API_KEY: Google Gemini API key
    - OPENAI_API_KEY: OpenAI API key
    - LLM_PROVIDER: Override provider selection ('gemini' or 'openai')
    """

    def __init__(
        self,
        provider: Literal["gemini", "openai", "auto"] = "auto",
        model: str | None = None,
    ) -> None:
        self.provider = provider
        self.model = model

        # Auto-detect provider if set to "auto"
        if provider == "auto":
            provider_override = os.getenv("LLM_PROVIDER", "").lower()
            if provider_override in ("gemini", "openai"):
                self.provider = provider_override  # type: ignore
            elif os.getenv("GEMINI_API_KEY"):
                self.provider = "gemini"
            elif os.getenv("OPENAI_API_KEY"):
                self.provider = "openai"
            else:
                log.warning("No LLM API keys found; LLM calls will fail.")
                self.provider = "openai"  # default fallback

        # Initialize based on provider
        if self.provider == "gemini":
            self._init_gemini()
        else:
            self._init_openai()

    def _init_gemini(self) -> None:
        """Initialize Google Gemini client."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or genai is None:
            log.warning("Gemini SDK or API key not available; LLM calls will fail.")
            self.gemini_available = False
        else:
            genai.configure(api_key=api_key)
            self.gemini_available = True
            # Default to gemini-1.5-flash if no model specified
            self.model = self.model or "gemini-1.5-flash"
            log.info(f"Using Gemini model: {self.model}")

    def _init_openai(self) -> None:
        """Initialize OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or openai is None:
            log.warning("OpenAI SDK or API key not available; LLM calls will fail.")
            self.openai_available = False
        else:
            openai.api_key = api_key
            self.openai_available = True
            # Default to gpt-4o-mini if no model specified
            self.model = self.model or "gpt-4o-mini"
            log.info(f"Using OpenAI model: {self.model}")

    def craft_system_prompt(self) -> str:
        return (
            "You are a helpful Vedic astrologer assistant. You MUST ONLY use the provided kundli JSON data "
            "to answer user queries. You must NOT attempt to compute any astrological positions or claims yourself. "
            "If information is missing in the kundli JSON, say so and ask the user for the missing data. "
            "Respond conversationally and explain insights based ONLY on the kundli JSON input."
        )

    def build_user_content(self, kundli_json: Dict[str, Any], question: str) -> str:
        """Build the user content string."""
        return (
            "Here is the computed kundli JSON (do not recalculate or change it).\n\n"
            + "KUNDLI_JSON:\n"
            + str(kundli_json)
            + "\n\n"
            + "User question: "
            + question
            + "\n\n"
            + "Answer in a friendly, conversational tone and ground every statement explicitly on the kundli data."
        )

    async def ask(
        self, kundli_json: Dict[str, Any], question: str, max_tokens: int = 512
    ) -> str:
        """Ask the LLM a question based on kundli data."""
        if self.provider == "gemini":
            return await self._ask_gemini(kundli_json, question, max_tokens)
        else:
            return await self._ask_openai(kundli_json, question, max_tokens)

    async def _ask_gemini(
        self, kundli_json: Dict[str, Any], question: str, max_tokens: int
    ) -> str:
        """Use Gemini API to get response."""
        if genai is None or not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError(
                "Gemini SDK or API key is not available. Set GEMINI_API_KEY and install google-generativeai."
            )

        try:
            model = genai.GenerativeModel(self.model)

            # Gemini doesn't have a separate system message, so we prepend it to user content
            system_prompt = self.craft_system_prompt()
            user_content = self.build_user_content(kundli_json, question)
            full_prompt = f"{system_prompt}\n\n{user_content}"

            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.7,
                ),
            )

            return response.text

        except Exception as e:  # pragma: no cover - external call
            log.error(f"Failed to get Gemini response: {e}")
            raise

    async def _ask_openai(
        self, kundli_json: Dict[str, Any], question: str, max_tokens: int
    ) -> str:
        """Use OpenAI API to get response."""
        if openai is None or not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError(
                "OpenAI SDK or API key is not available. Set OPENAI_API_KEY and install openai."
            )

        try:
            messages = [
                {"role": "system", "content": self.craft_system_prompt()},
                {
                    "role": "user",
                    "content": self.build_user_content(kundli_json, question),
                },
            ]

            resp = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7,
            )

            return resp["choices"][0]["message"]["content"]

        except Exception as e:  # pragma: no cover - external call
            log.error(f"Failed to parse OpenAI response: {e}")
            raise


# Singleton client instance - will auto-detect provider
llm_client = LLMClient()
