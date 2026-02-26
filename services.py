from __future__ import annotations

import json
import copy
from typing import Any

import httpx
import yaml
import anthropic

from config import CV_CONTENT_DIR, CV_APP_URL, ANTHROPIC_API_KEY, CLAUDE_MODEL
from models import Change, AnalyzeResponse
from prompts import SYSTEM_PROMPT, build_user_prompt


def load_cv(version: str) -> dict[str, Any]:
    path = CV_CONTENT_DIR / f"content_{version}.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_nested_value(data: dict, path: str) -> Any:
    keys = path.split(".")
    current = data
    for key in keys:
        if isinstance(current, list):
            current = current[int(key)]
        elif isinstance(current, dict):
            current = current[key]
        else:
            return None
    return current


def set_nested_value(data: dict, path: str, value: Any) -> None:
    keys = path.split(".")
    current = data
    for key in keys[:-1]:
        if isinstance(current, list):
            current = current[int(key)]
        else:
            current = current[key]
    last_key = keys[-1]
    if isinstance(current, list):
        current[int(last_key)] = value
    else:
        current[last_key] = value


async def analyze_cv(cv_data: dict, language: str, job_description: str) -> AnalyzeResponse:
    client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

    user_prompt = build_user_prompt(cv_data, language, job_description)

    message = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    response_text = message.content[0].text.strip()
    if response_text.startswith("```"):
        response_text = response_text.split("\n", 1)[1]
        response_text = response_text.rsplit("```", 1)[0].strip()
    result = json.loads(response_text)

    changes = [
        Change(
            section=c["section"],
            field_path=c["field_path"],
            original_value=c["original_value"],
            adapted_value=c["adapted_value"],
            reason=c["reason"],
        )
        for c in result["changes"]
    ]

    adapted_full = copy.deepcopy(cv_data)
    for c in result["changes"]:
        set_nested_value(adapted_full[language], c["field_path"], c["adapted_value"])

    return AnalyzeResponse(
        job_title=result.get("job_title", "Unknown Position"),
        original_data=cv_data,
        adapted_data=adapted_full,
        changes=changes,
    )


def apply_changes(
    original_data: dict[str, Any],
    adapted_data: dict[str, Any],
    language: str,
    accepted_paths: list[str],
) -> dict[str, Any]:
    merged = copy.deepcopy(original_data)

    for path in accepted_paths:
        try:
            value = get_nested_value(adapted_data[language], path)
            set_nested_value(merged[language], path, value)
        except (KeyError, IndexError, TypeError):
            continue

    return merged


async def generate_pdf(cv_data: dict[str, Any], language: str) -> bytes:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{CV_APP_URL}/api/generate",
            json={"language": language, "data": cv_data},
        )
        response.raise_for_status()
        return response.content
