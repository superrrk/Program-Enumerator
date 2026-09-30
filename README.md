# Enumerative arithmetic program synthesis

A dependency-free Python 3.10+ synthesizer for the DSL:

```text
E ::= x | y | 0 | 1 | 2 | + E E | - E E | * E E
```

Given integer input-output examples, it returns the first program that matches
every example. Programs use prefix (Polish) notation: `- * x x y` means `x*x-y`.

## Run

Each nonempty line of the input file must contain `x, y, expected_output`.
Negative integers and spaces are supported; no header is needed.

```sh
python3 synthesizer.py examples/addition.csv
# + x y

python3 synthesizer.py examples/square_minus_y.csv --max-size 5
# - * x x y

python3 -m unittest -v
```

Pass `-` as the filename to read examples from standard input.
Successful synthesis prints only the program and exits with status 0.
If a size limit is exhausted, the program reports that no solution was found
within the bound and exits with status 1. Invalid input exits with status 2.

The Python API is also available:

```python
from synthesizer import synthesize

program = synthesize([(1, 2, 3), (4, 5, 9), (0, 7, 7)], max_size=5)
assert program == "+ x y"
```

## How to explain the algorithm

1. Start with the five one-token programs: `x`, `y`, `0`, `1`, `2`.
2. Store programs in buckets indexed by their token count. Each program also
   stores its output on every example.
3. To generate a program of size `s`, select an operator and two smaller
   programs whose sizes add up to `s-1`. The operator contributes one token.
4. Build the prefix string and calculate its outputs by combining the two
   children's cached output vectors. For subtraction, order matters.
5. Immediately compare each candidate's outputs with the expected outputs.
   Return as soon as all examples match.

Only odd token counts occur, since leaves have size 1 and every internal node
has exactly two children. Search therefore visits sizes 1, 3, 5, and so on.
Within each size, the deterministic order is `+`, `-`, `*`, then increasing
left-child size, then the stored left and right candidate order. Equivalent
expressions are retained, so this is exhaustive syntactic enumeration.

Every DSL expression is either a leaf or an operator applied to two smaller
expressions. By induction, combining all smaller buckets generates every
expression of the current size. Since all smaller sizes are visited first,
the first matching program has the fewest tokens among all matching programs.
Multiple programs can fit the examples; the stated order breaks ties.
A match on the supplied examples does not guarantee the intended behavior on
unseen inputs.

## Cost and limitations

With `k` binary operators, a program has `2k+1` tokens. There are
`Catalan(k) * 3**k * 5**(k+1)` such programs, so exhaustive search grows rapidly.
For `m` examples, evaluating a new candidate costs `O(m)` arithmetic operations,
plus building its source string. Generated programs and output vectors are
kept in memory for reuse. Python integers have arbitrary precision, so actual
arithmetic cost also grows with the magnitude of values.

Without `--max-size`, the search continues until a solution is found, and may
run forever or exhaust resources if no solution exists. Use a small bound
such as `--max-size 5` or `--max-size 7` for exploratory runs. A bounded failure
does not prove that no larger solution exists.

The included tests cover the assignment example, each terminal, negative
inputs, operand order, nested programs, minimum size, malformed input, bounded
failure, and exhaustive counts through size 5. An independent prefix evaluator
checks every generated program through size 5 against its cached outputs.
The course-provided tests and answer key were not present in this workspace.

## GitHub submission

Push these files to your GitHub repository and submit the repository URL.
The source, examples, tests, and explanation are all included here.
