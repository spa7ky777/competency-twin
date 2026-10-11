from __future__ import annotations

import httpx

from app.ai import prompts
from app.ai.json_utils import parse_quiz_json
from app.config import Settings
from app.core.errors import (
    LLMInvalidOutputError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
    OllamaUnavailableError,
)


class OllamaService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.timeout = settings.ollama_timeout_seconds

    def health_check(self) -> dict:
        try:
            with httpx.Client(timeout=5.0) as client:
                r = client.get(f"{self.base}/api/tags")
                r.raise_for_status()
                names = [m.get("name", "") for m in r.json().get("models", [])]
        except Exception:
            return {
                "ok": False,
                "reachable": False,
                "model_installed": False,
                "model": self.model,
                "status": "down",
                "message": "Local AI is unavailable. Please start Ollama and ensure the configured model is installed.",
            }
        installed = any(self.model == n or n.startswith(self.model.split(":")[0]) and self.model in n for n in names)
        if not installed:
            installed = any(self.model in n or n.split(":")[0] == self.model.split(":")[0] for n in names)
            # exact match preferred
            installed = self.model in names or any(n.startswith(self.model) for n in names)
        return {
            "ok": installed,
            "reachable": True,
            "model_installed": installed,
            "model": self.model,
            "installed_models": names,
            "status": "ok" if installed else "model_missing",
            "message": None
            if installed
            else f"Local AI is unavailable. Please start Ollama and ensure the configured model is installed. Run: ollama pull {self.model}",
        }

    def _chat(self, prompt: str, json_mode: bool = False) -> str:
        payload: dict = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"temperature": self.settings.ollama_temperature},
        }
        if json_mode:
            payload["format"] = "json"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                tags = client.get(f"{self.base}/api/tags")
                tags.raise_for_status()
                names = [m.get("name", "") for m in tags.json().get("models", [])]
                if self.model not in names and not any(n.startswith(self.model) for n in names):
                    raise OllamaModelNotFoundError(self.model)
                r = client.post(f"{self.base}/api/chat", json=payload)
                r.raise_for_status()
                return r.json().get("message", {}).get("content", "")
        except OllamaModelNotFoundError:
            raise
        except httpx.TimeoutException:
            raise OllamaTimeoutError()
        except Exception as exc:
            raise OllamaUnavailableError() from exc

    def generate_answer(self, question: str, context_chunks: list[dict], subject: str = "", unit: str = "", topic: str = "") -> str:
        labeled = []
        used = 0
        cap = self.settings.max_context_chars
        for i, ch in enumerate(context_chunks, 1):
            text = ch.get("text") or ch.get("excerpt") or ""
            piece = f"[S{i}] {text}"
            if used + len(piece) > cap:
                break
            labeled.append(piece)
            used += len(piece)
        prompt = prompts.RAG_ANSWER.format(
            subject=subject or "n/a",
            unit=unit or "n/a",
            topic=topic or "n/a",
            context="\n\n".join(labeled) or "(no excerpts)",
            question=question,
        )
        return self._chat(prompt, json_mode=False)

    def generate_quiz(self, context_chunks: list[dict], n: int, difficulty: str, topic: str, competency: str) -> list[dict]:
        labeled = []
        used = 0
        for i, ch in enumerate(context_chunks, 1):
            text = ch.get("text") or ""
            piece = f"[S{i}] {text}"
            if used + len(piece) > self.settings.max_context_chars:
                break
            labeled.append(piece)
            used += len(piece)
        context = "\n\n".join(labeled) or "(no excerpts)"
        prompt = prompts.MCQ_GENERATE.format(n=n, difficulty=difficulty, topic=topic, competency=competency, context=context)
        last_err = "invalid"
        raw = ""
        for attempt in range(self.settings.llm_json_retries):
            raw = self._chat(prompt if attempt == 0 else prompts.MCQ_FIX.format(error=last_err, previous=raw), json_mode=True)
            try:
                quiz = parse_quiz_json(raw)
                return [q.model_dump() for q in quiz.questions]
            except Exception as exc:
                last_err = str(exc)
        raise LLMInvalidOutputError("The local model returned invalid JSON after retries. Try again.")

    def generate_explanation(self, question: str, correct_answer: str, context: str) -> str:
        prompt = prompts.EXPLANATION.format(question=question, correct=correct_answer, context=context)
        return self._chat(prompt)

    def analyze_competency(self, profile_data: dict) -> str:
        prompt = prompts.COMPETENCY_ANALYSIS.format(
            strongest=profile_data.get("strongest", "n/a"),
            weakest=profile_data.get("weakest", "n/a"),
            coverage=profile_data.get("coverage", "n/a"),
            unassessed=profile_data.get("unassessed", "n/a"),
        )
        return self._chat(prompt)

    def validate_question_grounding(self, question: str, source_chunks: list[dict]) -> dict:
        ctx = "\n".join((c.get("text") or "")[:400] for c in source_chunks)
        prompt = prompts.QUESTION_VALIDATE.format(question=question, correct="", context=ctx)
        raw = self._chat(prompt, json_mode=True)
        try:
            from app.ai.json_utils import extract_json_value

            data = extract_json_value(raw)
            return {"supported": bool(data.get("supported")), "reason": str(data.get("reason", ""))}
        except Exception:
            return {"supported": True, "reason": "parse_failed"}
