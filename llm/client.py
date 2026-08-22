import os
import json
from pathlib import Path
from datetime import datetime, timezone

from openai import OpenAI
from dotenv import load_dotenv
from pydantic import ValidationError

from .schema import ResumeExtractResponse

load_dotenv()

client = OpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
)

PROMPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "prompts"
    / "resume-extraction-v1.md"
)


def load_resume_prompt():
    return PROMPT_PATH.read_text(encoding="utf-8")


def call_llm(text: str):
    response = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[
            {
                "role": "system",
                "content": load_resume_prompt(),
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        temperature=0.2,
    )

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

    response = client.chat.completions.create(
        model=os.environ["LLM_MODEL"],
        messages=[
            {
                "role": "system",
                "content": repair_prompt,
            },
            {
                "role": "user",
                "content": text,
            },
        ],
        temperature=0.2,
    )

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


def extract_resume(text: str):
    """
    Call the LLM and return its raw output.
    """
    return call_llm(text)