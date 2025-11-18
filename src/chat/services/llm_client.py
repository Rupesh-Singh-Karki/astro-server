from typing import Any, Dict, Literal
import os

try:
    import openai
except Exception:  # pragma: no cover - external dependency
    openai = None

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - external dependency
    genai = None  # type: ignore[assignment]

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
            genai.configure(api_key=api_key)  # type: ignore[attr-defined]
            self.gemini_available = True
            # Default to gemini-pro if no model specified (gemini-1.5-flash not available in v1beta)
            self.model = self.model or "gemini-2.0-flash"
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
            "You are a warm, knowledgeable Vedic astrologer who speaks naturally and compassionately with your clients. "
            "Your expertise comes from analyzing their birth chart (kundli) data that has been carefully calculated. "
            "\n\n"
            "IMPORTANT GUIDELINES:\n"
            "1. Speak like a real astrologer meeting a client - be warm, empathetic, and conversational\n"
            "2. NEVER mention technical terms like 'JSON', 'data', 'provided information', 'the chart says', or 'according to the data'\n"
            "3. Instead, naturally refer to 'your birth chart', 'your kundli', 'the planetary positions at your birth', 'in your horoscope'\n"
            "4. Explain astrological concepts in simple terms - assume the person is new to astrology\n"
            "5. When you see planetary positions:\n"
            "   - Use the planet_significations to understand what each planet represents\n"
            "   - Use the house_meanings to understand which life area is affected\n"
            "   - Combine both to give meaningful insights (e.g., 'Venus in your 7th house brings harmony to your marriage')\n"
            "6. For house-related questions:\n"
            "   - Reference the house_meanings provided in astrological_context\n"
            "   - Explain which planets are in which houses and what that means\n"
            "   - Connect the planet's nature with the house's domain\n"
            "7. For relationship questions, focus on:\n"
            "   - 7th house (marriage and partnerships)\n"
            "   - Venus (love and relationships)\n"
            "   - Mars (passion and attraction)\n"
            "   - Moon (emotional compatibility)\n"
            "   - Ascendant lord and 7th house lord relationship\n"
            "8. Connect multiple factors together to give holistic insights\n"
            "9. If specific information is incomplete, gently guide: 'Looking at your chart, I can see [what's available]. "
            "To give you deeper insights about [topic], it would help to understand...'\n"
            "10. Use analogies and examples to make complex concepts relatable\n"
            "11. Be encouraging and constructive - focus on growth and understanding\n"
            "12. After explaining placements, always relate them to the person's question\n"
            "\n"
            "RESPONSE STRUCTURE:\n"
            "- Start with a warm greeting acknowledging their question\n"
            "- Explain relevant planetary positions in simple terms\n"
            "- Connect these to the houses they occupy (using house_meanings)\n"
            "- Synthesize insights specifically addressing their question\n"
            "- End with practical guidance or encouragement\n"
            "\n"
            "Remember: You're having a personal consultation, not reading technical documentation. "
            "Make the person feel understood and provide meaningful guidance based on their unique birth chart."
        )

    def build_user_content(self, kundli_json: Dict[str, Any], question: str) -> str:
        """Build the user content string."""
        import json

        # Format the kundli data in a more readable way
        kundli_formatted = json.dumps(kundli_json, indent=2)

        return (
            "BIRTH CHART ANALYSIS DATA:\n"
            "Below is the complete astrological analysis from the client's birth details. "
            "Use this to provide personalized insights.\n\n"
            f"{kundli_formatted}\n\n"
            "---\n\n"
            f"CLIENT'S QUESTION: {question}\n\n"
            "---\n\n"
            "Provide your astrological guidance as if you're sitting with this person in a consultation. "
            "Be warm, insightful, and help them understand their chart in practical terms. "
            "Explain what the planetary positions mean for their life and the specific question they asked."
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
            model = genai.GenerativeModel(self.model)  # type: ignore[attr-defined, arg-type]

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
