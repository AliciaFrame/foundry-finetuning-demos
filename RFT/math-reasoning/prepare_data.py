import argparse
import json
from pathlib import Path

from datasets import load_dataset


DATASET_NAME = "open-r1/OpenR1-Math-220k"
DATASET_REVISION = "e4e141ec9dea9f8326f4d347be56105859b2bd68"
SYSTEM_PROMPT = (
    "You are a mathematical reasoning expert. Solve problems with detailed "
    "step-by-step thinking and provide final answers in \\boxed{} format. "
    "Show all intermediate calculations and explain your reasoning clearly."
)


def has_balanced_braces(value: str) -> bool:
    depth = 0
    for char in value:
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                return False
    return depth == 0


def is_usable(row: dict) -> bool:
    problem = row.get("problem")
    answer = row.get("answer")
    return (
        isinstance(problem, str)
        and bool(problem.strip())
        and isinstance(answer, str)
        and 0 < len(answer.strip()) <= 500
        and row.get("correctness_count", 0) >= 2
        and has_balanced_braces(answer)
        and not answer.rstrip().endswith(("\\", "{"))
        and "\\ldots" not in answer
    )


def build_rows(count: int) -> list[dict]:
    source = load_dataset(
        DATASET_NAME,
        split="train",
        revision=DATASET_REVISION,
        streaming=True,
    )
    rows = []
    for item in source:
        if not is_usable(item):
            continue
        rows.append(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": f"{SYSTEM_PROMPT}\n\n{item['problem'].strip()}",
                    }
                ],
                "answer": item["answer"].strip(),
            }
        )
        if len(rows) == count:
            return rows
    raise RuntimeError(f"Only found {len(rows)} usable rows; expected {count}.")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Regenerate the pinned OpenR1-Math RFT demonstration subset."
    )
    parser.add_argument("--train-count", type=int, default=100)
    parser.add_argument("--validation-count", type=int, default=10)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parent)
    args = parser.parse_args()

    total = args.train_count + args.validation_count
    rows = build_rows(total)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "training_rft.jsonl", rows[: args.train_count])
    write_jsonl(args.output_dir / "validation_rft.jsonl", rows[args.train_count :])
    print(
        f"Wrote {args.train_count} training and {args.validation_count} "
        f"validation rows to {args.output_dir}."
    )


if __name__ == "__main__":
    main()
