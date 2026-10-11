from __future__ import annotations

import json
import re
from typing import Any

from pydantic import BaseModel, Field, field_validator


class GeneratedQuestion(BaseModel):
    question: str
    options: list[str]
    correct_index: int
    explanation: str = ""
    difficulty: str = "medium"
    topic: str = ""
    competency: str = ""
    source_label: str = "S1"

    @field_validator("question")
    @classmethod
    def nonempty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("empty question")
        return v

    @field_validator("options")
    @classmethod
    def four_unique(cls, v: list[str]) -> list[str]:
        cleaned = [str(x).strip() for x in v]
        if len(cleaned) != 4:
            raise ValueError("need exactly 4 options")
        if any(not x for x in cleaned):
            raise ValueError("empty option")
        if len(set(x.lower() for x in cleaned)) < 4:
            raise ValueError("duplicate options")
        return cleaned

    @field_validator("correct_index")
    @classmethod
    def in_range(cls, v: int) -> int:
        if v not in (0, 1, 2, 3):
            raise ValueError("correct_index must be 0-3")
        return v

    @field_validator("difficulty")
    @classmethod
    def diff_ok(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in ("easy", "medium", "hard"):
            raise ValueError("bad difficulty")
        return v


class GeneratedQuiz(BaseModel):
    questions: list[GeneratedQuestion] = Field(min_length=1)


def strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def extract_json_value(text: str) -> Any:
    text = strip_fences(text)
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        if start == -1:
            continue
        depth = 0
        in_str = False
        escape = False
        for i, ch in enumerate(text[start:], start):
            if in_str:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    blob = text[start : i + 1]
                    blob = re.sub(r",\s*([}\]])", r"\1", blob)
                    return json.loads(blob)
    return json.loads(text)


def parse_quiz_json(text: str) -> GeneratedQuiz:
    data = extract_json_value(text)
    if isinstance(data, list):
        data = {"questions": data}
    quiz = GeneratedQuiz.model_validate(data)
    seen = set()
    unique = []
    for q in quiz.questions:
        key = q.question.lower().strip()
        if key in seen:
            continue
        seen.add(key)
        unique.append(q)
    if not unique:
        raise ValueError("no unique questions")
    return GeneratedQuiz(questions=unique)
