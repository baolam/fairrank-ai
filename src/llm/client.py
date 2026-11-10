"""Unified LLM API Client supporting Gemini, OpenAI, and deterministic mock mode."""

import os
import json
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class UnifiedLLMClient:
    """Wrapper that routes requests to Gemini, OpenAI, or local fallback."""

    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or os.getenv("LLM_PROVIDER", "gemini")).lower()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")

    def generate_json_response(
        self, system_instruction: str, user_prompt: str, response_kind: str = "scoring"
    ) -> Dict[str, Any]:
        """Calls the configured LLM API and parses JSON response.

        `response_kind` ("scoring" or "bias_audit") selects the correct offline
        fallback shape when no provider is reachable, since the scoring and
        bias-audit contracts have disjoint JSON schemas.
        """
        start_time = time.time()

        if self.provider == "gemini" and self.gemini_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_api_key)
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    system_instruction=system_instruction,
                    generation_config={"response_mime_type": "application/json", "temperature": 0.0},
                )
                response = model.generate_content(user_prompt)
                parsed = json.loads(response.text)
                parsed["latency_ms"] = (time.time() - start_time) * 1000.0
                return parsed
            except Exception as e:
                # Fallback on error
                return self._mock_fallback(response_kind, user_prompt, str(e), (time.time() - start_time) * 1000.0)

        elif self.provider == "openai" and self.openai_api_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=self.openai_api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.0,
                )
                raw_json = response.choices[0].message.content or "{}"
                parsed = json.loads(raw_json)
                parsed["latency_ms"] = (time.time() - start_time) * 1000.0
                return parsed
            except Exception as e:
                return self._mock_fallback(response_kind, user_prompt, str(e), (time.time() - start_time) * 1000.0)

        # Default fallback when API keys are not yet configured in .env
        return self._mock_fallback(
            response_kind, user_prompt, "API key not configured in environment", (time.time() - start_time) * 1000.0
        )

    def _mock_fallback(self, response_kind: str, prompt: str, note: str, latency: float) -> Dict[str, Any]:
        """Deterministic heuristic fallback adhering to strict JSON contract."""
        if response_kind == "bias_audit":
            return self._mock_bias_audit_fallback(prompt, note, latency)
        return self._mock_scoring_fallback(prompt, note, latency)

    def _mock_scoring_fallback(self, prompt: str, note: str, latency: float) -> Dict[str, Any]:
        """Deterministic heuristic fallback for candidate scoring requests."""
        prompt_lower = prompt.lower()
        score = 0.75
        grade = 1  # Potential Fit

        if any(w in prompt_lower for w in ["expert", "lead", "senior", "master", "phd", "8+ years"]):
            score = 0.90
            grade = 2  # Good Fit
        elif any(w in prompt_lower for w in ["unrelated", "no experience", "entry level"]):
            score = 0.35
            grade = 0  # No Fit

        return {
            "relevance_grade": grade,
            "fit_score": score,
            "key_qualifications": ["Relevant professional domain experience", "Core technical skills"],
            "missing_qualifications": ["Industry specific certifications"],
            "rationale": f"Candidate profile evaluated. [Offline/Fallback mode: {note}]",
            "token_usage": {"prompt_tokens": 120, "completion_tokens": 60},
            "latency_ms": latency,
        }

    def _mock_bias_audit_fallback(self, prompt: str, note: str, latency: float) -> Dict[str, Any]:
        """Deterministic fallback for bias-audit requests.

        Offline mode cannot actually probe the LLM for name sensitivity, so it
        must not assert invariance. It reports the audit as inconclusive and
        flags it for a real run instead of silently claiming "not sensitive".
        """
        distinct_groups = set()
        for line in prompt.splitlines():
            line = line.strip()
            if line.startswith("- [") and "]" in line:
                distinct_groups.add(line.split("[", 1)[1].split("]", 1)[0])

        multi_group_tested = len(distinct_groups) > 1

        return {
            "is_demographically_sensitive": multi_group_tested,
            "perceived_bias_score": 0.5 if multi_group_tested else 0.0,
            "audit_findings": [
                f"Offline fallback mode: could not query LLM provider ({note}).",
                "Cross-group counterfactual name variants were supplied but not evaluated by a live model."
                if multi_group_tested
                else "No cross-group counterfactual variants were detected in the request.",
            ],
            "proxy_tokens_detected": [],
            "recommendation": (
                "Inconclusive in offline mode. Configure GEMINI_API_KEY or OPENAI_API_KEY and "
                "re-run to obtain a real LLM-based demographic sensitivity judgment."
            ),
            "token_usage": {"prompt_tokens": 0, "completion_tokens": 0},
            "latency_ms": latency,
        }
