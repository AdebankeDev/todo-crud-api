import json
from pathlib import Path

import requests


BASE_DIR = Path(__file__).resolve().parents[1]
CASES_PATH = BASE_DIR / "evals" / "cases.json"

API_URL = "http://127.0.0.1:8000/extract"


def load_cases():
    with CASES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def run_case(case):
    response = requests.post(
        API_URL,
        json={"text": case["input"]},
        timeout=40,
    )

    if response.status_code != 200:
        return None

    return response.json()


def main():
    cases = load_cases()

    matched = 0
    failures = []

    for case in cases:
        result = run_case(case)

        expected_name = case["expected"]["name"]

        if result is not None and result.get("name") == expected_name:
            matched += 1
        else:
            actual_name = None if result is None else result.get("name")

            failures.append(
                {
                    "id": case["id"],
                    "expected": expected_name,
                    "actual": actual_name,
                }
            )

    total = len(cases)
    percentage = (matched / total) * 100

    print(f"Evaluation: {matched}/{total}")
    print(f"Key-field accuracy: {percentage:.1f}%")

    if failures:
        print("\nFailures:")

        for failure in failures:
            print(
                f"- {failure['id']}: "
                f"expected {failure['expected']!r}, "
                f"got {failure['actual']!r}"
            )
    else:
        print("\nFailures: none")


if __name__ == "__main__":
    main()