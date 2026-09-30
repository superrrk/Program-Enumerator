import unittest

from synthesizer import enumerate_programs, parse_examples, synthesize


def evaluate_prefix(source, x, y):
    """Independent evaluator used to verify synthesized text and cached outputs."""
    tokens = iter(source.split())

    def expression():
        token = next(tokens)
        if token in ("+", "-", "*"):
            left, right = expression(), expression()
            if token == "+":
                return left + right
            if token == "-":
                return left - right
            return left * right
        return {"x": x, "y": y, "0": 0, "1": 1, "2": 2}[token]

    result = expression()
    if next(tokens, None) is not None:
        raise AssertionError("trailing tokens")
    return result


class SynthesisTests(unittest.TestCase):
    def test_assignment_example(self):
        self.assertEqual(synthesize([(1, 2, 3), (4, 5, 9), (0, 7, 7)]), "+ x y")

    def test_terminals(self):
        for token in ("x", "y", "0", "1", "2"):
            examples = [(x, y, evaluate_prefix(token, x, y)) for x, y in [(3, 4), (5, 6)]]
            with self.subTest(token=token):
                self.assertEqual(synthesize(examples, 1), token)

    def test_subtraction_order(self):
        self.assertEqual(synthesize([(2, 5, 3), (7, 1, -6)], 3), "- y x")

    def test_multiplication_with_negative_inputs(self):
        self.assertEqual(synthesize([(-3, 4, -12), (2, 5, 10), (0, 8, 0)], 3), "* x y")

    def test_nested_expression_and_minimum_size(self):
        examples = [(1, 2, -1), (4, 5, 11), (0, 7, -7), (-3, 2, 7)]
        self.assertIsNone(synthesize(examples, 3))
        self.assertEqual(synthesize(examples, 5), "- * x x y")

    def test_exhaustive_enumeration_and_cached_evaluation(self):
        examples = [(-2, 3, 0), (0, -1, 0), (4, 5, 0)]
        programs = list(enumerate_programs(examples, 5))
        # 5 leaves; 3*5*5 size-3 trees; 3*(5*75 + 75*5) size-5 trees.
        self.assertEqual(len(programs), 5 + 75 + 2250)
        self.assertEqual(len({p.source for p in programs}), len(programs))
        sizes = [p.size for p in programs]
        self.assertEqual(sizes, sorted(sizes))
        for program in programs:
            self.assertEqual(program.size, len(program.source.split()))
            self.assertEqual(program.outputs, tuple(evaluate_prefix(program.source, x, y) for x, y, _ in examples))

    def test_bounded_failure_and_even_bound(self):
        examples = [(1, 2, 3), (4, 5, 9), (0, 7, 7)]
        self.assertIsNone(synthesize(examples, 2))
        self.assertEqual(synthesize(examples, 4), "+ x y")
        self.assertIsNone(synthesize([(1, 1, 0), (1, 1, 1)], 5))

    def test_invalid_search_arguments(self):
        with self.assertRaises(ValueError):
            synthesize([])
        for bound in (0, -1):
            with self.assertRaises(ValueError):
                synthesize([(1, 2, 3)], bound)

    def test_parse_examples(self):
        self.assertEqual(parse_examples("\n 1, 2, 3\n-4,5,-9\n"), [(1, 2, 3), (-4, 5, -9)])
        for text in ("", "\n", "1,2", "1,2,3,4", "1,no,3", "1.5,2,3"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_examples(text)


if __name__ == "__main__":
    unittest.main()
