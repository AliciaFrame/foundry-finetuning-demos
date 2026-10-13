import argparse
import json
import operator
import random
from collections.abc import Iterable
from pathlib import Path


SYSTEM_PROMPT = """You are an expert in arithmetic problem solving. Given a target number and a list of numbers, your task is to combine all of the numbers exactly once using addition (+), subtraction (-), multiplication (*), or division (/) to reach the target.

- You must use every number exactly once.
- Use parentheses as needed to control the order of operations.
- Return only a valid JSON object with this exact shape:
  {
    "expression": "...",
    "result": "..."
  }
- Both values must be strings.
- If the exact target is not possible, return the closest valid result using all numbers.
"""

OPERATIONS = (
    ("+", operator.add),
    ("-", operator.sub),
    ("*", operator.mul),
    ("/", operator.truediv),
)


def combine(values: list[tuple[float, str]], rng: random.Random) -> tuple[float, str]:
    work = values[:]
    while len(work) > 1:
        left_index, right_index = rng.sample(range(len(work)), 2)
        left = work.pop(max(left_index, right_index))
        right = work.pop(min(left_index, right_index))
        symbol, operation = rng.choice(OPERATIONS)
        if symbol == "/" and right[0] == 0:
            work.extend((left, right))
            continue
        value = operation(left[0], right[0])
        work.append((value, f"({left[1]} {symbol} {right[1]})"))
    return work[0]


def generate_puzzles(count: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    puzzles = []
    seen = set()
    while len(puzzles) < count:
        numbers = rng.sample(range(1, 101), 4)
        value, _ = combine([(float(number), str(number)) for number in numbers], rng)
        if not value.is_integer() or not 10 <= value <= 999:
            continue
        target = int(value)
        key = (target, tuple(sorted(numbers)))
        if key in seen:
            continue
        seen.add(key)
        puzzles.append({"target": str(target), "nums": json.dumps(numbers)})
    return puzzles


def rft_row(item: dict) -> dict:
    return {
        "messages": [
            {
                "role": "user",
                "content": (
                    f"{SYSTEM_PROMPT}\nInput:\n\n"
                    f"Target: {item['target']}\nNumbers: {item['nums']}"
                ),
            }
        ],
        "target": item["target"],
        "nums": item["nums"],
    }


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate deterministic, license-clear Countdown RFT data."
    )
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parents[1] / "data")
    parser.add_argument("--seed", type=int, default=20260515)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    train = generate_puzzles(245, args.seed)
    validation = generate_puzzles(256, args.seed + 1)
    write_jsonl(args.output_dir / "countdown_train_raw.jsonl", train)
    write_jsonl(args.output_dir / "countdown_valid_raw.jsonl", validation)
    write_jsonl(args.output_dir / "countdown_train_25.jsonl", map(rft_row, train[:25]))
    write_jsonl(args.output_dir / "countdown_train_100.jsonl", map(rft_row, train[:100]))
    write_jsonl(args.output_dir / "countdown_valid_15.jsonl", map(rft_row, validation[:15]))
    write_jsonl(args.output_dir / "countdown_valid_50.jsonl", map(rft_row, validation[:50]))
    write_jsonl(
        args.output_dir / "countdown_eval_100.jsonl",
        ({"item": row} for row in validation[50:150]),
    )
    print(f"Wrote deterministic Countdown datasets to {args.output_dir}.")


if __name__ == "__main__":
    main()
