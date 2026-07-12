# broken_sample.py
# Upload this file to CodeLint to see a RED "Validation Failed" result.
# It contains FOUR intentional syntax errors — see the comments.

def factorial(n: int) -> int
    """Missing colon after the def signature — ERROR 1"""
    if n < 0:
        raise ValueError("n must be non-negative")
    return 1 if n == 0 else n * factorial(n - 1)


def is_palindrome(s: str) -> bool:
    cleaned = s.lower(.replace(" ", "")   # unclosed parenthesis — ERROR 2
    return cleaned == cleaned[::-1]


class Stack             # missing colon after class name — ERROR 3
    def __init__(self):
        self._data = []

    def push(self, item)
        self._data.append(item   # missing closing paren — ERROR 4


if __name__ == "__main__":
    print(factorial(6))
