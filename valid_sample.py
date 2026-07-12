# valid_sample.py
# Upload this file to CodeLint to see a GREEN "Code is valid" result.

def factorial(n: int) -> int:
    """Return the factorial of n recursively."""
    if n < 0:
        raise ValueError("n must be non-negative")
    return 1 if n == 0 else n * factorial(n - 1)


def is_palindrome(s: str) -> bool:
    """Check whether a string is a palindrome (case-insensitive)."""
    cleaned = s.lower().replace(" ", "")
    return cleaned == cleaned[::-1]


class Stack:
    """A simple generic stack implementation."""

    def __init__(self):
        self._data = []

    def push(self, item):
        self._data.append(item)

    def pop(self):
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self._data.pop()

    def peek(self):
        if self.is_empty():
            raise IndexError("peek at empty stack")
        return self._data[-1]

    def is_empty(self) -> bool:
        return len(self._data) == 0

    def __len__(self) -> int:
        return len(self._data)


if __name__ == "__main__":
    print(factorial(6))                  # 720
    print(is_palindrome("Race a car"))   # False
    print(is_palindrome("A man a plan a canal Panama"))  # True

    s = Stack()
    s.push(10)
    s.push(20)
    print(s.pop())   # 20
    print(s.peek())  # 10
