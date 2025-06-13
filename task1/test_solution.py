import pytest
from solution import strict


@strict
def sum_two(a: int, b: int) -> int:
    return a + b


def test_sum_two_correct():
    assert sum_two(1, 2) == 3


def test_sum_two_type_error():
    with pytest.raises(TypeError):
        sum_two(1, 2.4)


def test_kwargs_support():
    @strict
    def greet(name: str, age: int = 18):
        return f"{name}, {age}"

    assert greet("Alice", age=30) == "Alice, 30"
    assert greet("Bob") == "Bob, 18"

    with pytest.raises(TypeError):
        greet("Charlie", age="old")


def test_mixed_args_and_kwargs():
    @strict
    def mix(a: int, b: float = 1.0, c: str = "ok"):
        return f"{a}, {b}, {c}"

    assert mix(5) == "5, 1.0, ok"
    assert mix(5, 2.5, c="great") == "5, 2.5, great"

    with pytest.raises(TypeError):
        mix(5, c=42)


def test_no_annotation_error():
    with pytest.raises(TypeError):
        @strict
        def broken(x, y: int):
            return x + y
