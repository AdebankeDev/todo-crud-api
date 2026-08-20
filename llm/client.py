import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url=os.environ["LLM_BASE_URL"],
    api_key=os.environ["LLM_API_KEY"],
)

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "resume-extraction-v1.md"


def load_resume_prompt():
    return PROMPT_PATH.read_text(encoding="utf-8")


def extract_resume(text: str):
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