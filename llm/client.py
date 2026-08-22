import os
import json
from pathlib import Path
from datetime import datetime, timezone
import random
import time

from openai import (
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
)

from openai import OpenAI
from dotenv import load_dotenv
from pydantic import ValidationError

from .schema import ResumeExtractResponse


load_dotenv()

client = OpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
    timeout=30.0,
    max_retries=0,
)


PROMPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "prompts"
    / "resume-extraction-v1.md"
)


def load_resume_prompt():
    return PROMPT_PATH.read_text(encoding="utf-8")



def call_llm_with_retry(messages, repair=False):
    for attempt in range(3):
        start_time = time.perf_counter()

        try:
            response = client.chat.completions.create(
                model=os.environ["LLM_MODEL"],
                messages=messages,
                temperature=0.2,
            )

            duration_ms = (
                time.perf_counter() - start_time
            ) * 1000

            log_llm_usage(
                response=response,
                duration_ms=duration_ms,
                repair=repair,
            )

            return response

        except APITimeoutError:
            if attempt == 2:
                raise

            delay = 2 ** attempt
            jitter = random.uniform(0, 0.25)
            time.sleep(delay + jitter)

        except APIStatusError as error:
            if error.status_code not in {429, 500, 502, 503, 504}:
                raise

            if attempt == 2:
                raise

            retry_after = error.response.headers.get("retry-after")

            if retry_after:
                delay = float(retry_after)
            else:
                delay = 2 ** attempt

            jitter = random.uniform(0, 0.25)
            time.sleep(delay + jitter)


def call_llm(text: str):
    messages = [
        {
            "role": "system",
            "content": load_resume_prompt(),
        },
        {
            "role": "user",
            "content": text,
        },
    ]

    response = call_llm_with_retry(messages)

    return response.choices[0].message.content


def repair_llm_output(text: str, broken_output: str, error: str):
    repair_prompt = f"""
{load_resume_prompt()}

Your previous answer was rejected for this reason:
{error}

Your previous answer was:
{broken_output}

Return only corrected JSON matching the schema.
Do not include markdown code fences.
Do not include explanations.
"""

    messages = [
        {
            "role": "system",
            "content": repair_prompt,
        },
        {
            "role": "user",
            "content": text,
        },
    ]

    response = call_llm_with_retry(messages, repair=True)

    return response.choices[0].message.content


def parse_json(raw_output: str):
    """
    Extract a JSON object from the model output.

    Handles:
    - plain JSON
    - JSON inside ```json ... ```
    - extra text before/after the JSON
    """
    cleaned = raw_output.strip()

    # Remove markdown code fences if present
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines[0].strip().startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    # Find the JSON object
    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output")

    json_text = cleaned[start:end + 1]

    return json.loads(json_text)


def validate_output(data):
    """
    Validate parsed JSON against the ResumeExtractResponse schema.
    """
    return ResumeExtractResponse.model_validate(data)


def quarantine_failure(
    input_text: str,
    raw_output: str,
    repaired_output: str,
    error: str,
):
    logs_dir = Path(__file__).resolve().parents[1] / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    quarantine_path = logs_dir / "quarantine.jsonl"

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input": input_text,
        "raw_output": raw_output,
        "repaired_output": repaired_output,
        "error": error,
        "prompt_version": "resume-extraction-v1",
    }

    with quarantine_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")



def log_llm_usage(response, duration_ms: float, repair: bool):
    logs_dir = Path(__file__).resolve().parents[1] / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    usage_path = logs_dir / "llm_usage.jsonl"

    record = {
        "prompt_version": "resume-extraction-v1",
        "model": os.environ["LLM_MODEL"],
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
        "duration_ms": round(duration_ms, 2),
        "repair": repair,
    }

    with usage_path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")


def extract_resume(text: str):
    """
    Call the LLM and return its raw output.
    """
    return call_llm(text)