"""Bottom-up enumerative synthesis for a small integer arithmetic DSL."""

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Iterator, Sequence


Example = tuple[int, int, int]


@dataclass(frozen=True)
class Program:
    source: str
    size: int
    outputs: tuple[int, ...]


def parse_examples(text: str) -> list[Example]:
    """Read one comma-separated x,y,output triple per nonempty line."""
    examples = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        fields = line.split(",")
        if len(fields) != 3:
            raise ValueError(f"line {line_number}: expected three comma-separated integers")
        try:
            x, y, output = (int(field.strip()) for field in fields)
        except ValueError as error:
            raise ValueError(f"line {line_number}: expected integers") from error
        examples.append((x, y, output))
    if not examples:
        raise ValueError("at least one input-output example is required")
    return examples


def enumerate_programs(
    examples: Sequence[Example], max_size: int | None = None
) -> Iterator[Program]:
    """Yield every DSL expression in nondecreasing token count.

    Within each size, use operator order +,-,*, then increasing left
    subtree size, then the previously generated left and right programs.
    Cache output vectors so a parent needs only one operation per example.
    No expressions are pruned, including equivalent expressions.
    """
    if not examples:
        raise ValueError("at least one input-output example is required")
    if max_size is not None and max_size < 1:
        raise ValueError("max_size must be positive")

    by_size: dict[int, list[Program]] = {1: []}
    terminals = (
        ("x", tuple(x for x, _, _ in examples)),
        ("y", tuple(y for _, y, _ in examples)),
        ("0", (0,) * len(examples)),
        ("1", (1,) * len(examples)),
        ("2", (2,) * len(examples)),
    )
    for source, outputs in terminals:
        program = Program(source, 1, outputs)
        by_size[1].append(program)
        yield program

    # A binary expression has size 1 + left.size + right.size.
    # Thus every valid size is odd: 1, 3, 5, ... .
    size = 3
    while max_size is None or size <= max_size:
        by_size[size] = []
        for operator in ("+", "-", "*"):
            for left_size in range(1, size - 1, 2):
                right_size = size - 1 - left_size
                for left in by_size[left_size]:
                    for right in by_size[right_size]:
                        pairs = zip(left.outputs, right.outputs)
                        if operator == "+":
                            outputs = tuple(a + b for a, b in pairs)
                        elif operator == "-":
                            outputs = tuple(a - b for a, b in pairs)
                        else:
                            outputs = tuple(a * b for a, b in pairs)
                        program = Program(
                            f"{operator} {left.source} {right.source}", size, outputs
                        )
                        by_size[size].append(program)
                        yield program
        size += 2


def synthesize(
    examples: Sequence[Example], max_size: int | None = None
) -> str | None:
    """Return the first matching program, or None if a finite bound is exhausted."""
    expected = tuple(output for _, _, output in examples)
    for program in enumerate_programs(examples, max_size):
        if program.outputs == expected:
            return program.source
    return None


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="example file, or - to read standard input")
    parser.add_argument("--max-size", type=int, help="optional maximum token count")
    args = parser.parse_args(argv)
    try:
        text = sys.stdin.read() if args.file == "-" else Path(args.file).read_text()
        examples = parse_examples(text)
        result = synthesize(examples, args.max_size)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    if result is None:
        print(f"No program found with at most {args.max_size} tokens.", file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
