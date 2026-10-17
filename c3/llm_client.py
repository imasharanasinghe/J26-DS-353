"""Thin wrapper so the proposer doesn't care which LLM provider you use.

Every call is logged to results/llm_log.jsonl (prompt, reply, model, time) so
experiments can be checked and repeated later.

Settings in .env:
  C3_LLM_PROVIDER = gemini | openai | anthropic     (default: gemini)
  C3_LLM_MODEL    = model name                      (defaults below)
  GEMINI_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone

from dotenv import load_dotenv

DEFAULT_MODELS = {
    "gemini": "gemini-3.6-flash",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5-20251001",
}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LOG = os.path.join(ROOT, "results", "llm_log.jsonl")


class LLMClient:
    def __init__(self, provider: str, model: str, max_tokens: int = 2000, log_path: str = DEFAULT_LOG):
        self.provider, self.model, self.max_tokens = provider, model, max_tokens
        self.log_path = log_path
        self.calls = 0
        self.failures = 0
        if provider == "gemini":
            from google import genai  # pip install google-genai
            self._c = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        elif provider == "openai":
            import openai  # pip install openai
            self._c = openai.OpenAI()
        elif provider == "anthropic":
            import anthropic  # pip install anthropic
            self._c = anthropic.Anthropic()
        else:
            raise ValueError(f"Unknown provider '{provider}'")

    @classmethod
    def from_env(cls) -> "LLMClient":
        load_dotenv()
        p = os.environ.get("C3_LLM_PROVIDER", "gemini").lower()
        return cls(p, os.environ.get("C3_LLM_MODEL", DEFAULT_MODELS.get(p, "")))

    # ------------------------------------------------------------------
    def _call(self, system: str, user: str, temperature: float) -> str:
        if self.provider == "gemini":
            from google.genai import types
            r = self._c.models.generate_content(
                model=self.model,
                contents=user,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=temperature,
                    max_output_tokens=self.max_tokens,
                    response_mime_type="application/json",
                ),
            )
            return r.text or ""
        if self.provider == "openai":
            r = self._c.chat.completions.create(
                model=self.model, temperature=temperature,
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}])
            return r.choices[0].message.content or ""
        r = self._c.messages.create(model=self.model, max_tokens=self.max_tokens,
                                    temperature=temperature, system=system,
                                    messages=[{"role": "user", "content": user}])
        return "".join(b.text for b in r.content if getattr(b, "type", "") == "text")

    def complete(self, system: str, user: str, temperature: float = 0.0,
                 retries: int = 2, tag: str = "") -> str:
        last_err = None
        for attempt in range(retries + 1):
            t0 = time.perf_counter()
            try:
                self.calls += 1
                text = self._call(system, user, temperature)
                self._log(tag, system, user, temperature, text, time.perf_counter() - t0, None)
                return text
            except Exception as e:  # network error, rate limit, bad key...
                last_err = e
                self.failures += 1
                self._log(tag, system, user, temperature, "", time.perf_counter() - t0, repr(e))
                if attempt < retries:
                    time.sleep(3 * (attempt + 1))
        raise RuntimeError(f"LLM call failed after {retries + 1} tries: {last_err}")

    def _log(self, tag, system, user, temperature, reply, seconds, error):
        try:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "time": datetime.now(timezone.utc).isoformat(),
                    "provider": self.provider, "model": self.model, "tag": tag,
                    "temperature": temperature, "seconds": round(seconds, 3),
                    "system": system, "user": user, "reply": reply, "error": error,
                }, ensure_ascii=False) + "\n")
        except OSError:
            pass  # logging must never break the experiment
