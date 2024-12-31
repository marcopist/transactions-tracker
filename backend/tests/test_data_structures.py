from dataclasses import dataclass
from transactions.data_structures.structured_enum import StructuredEnum

def test_structured_enum():
    class Maybe(StructuredEnum):
        @dataclass
        class Just:
            value: int

        @dataclass
        class Nothing:
            pass

    assert Maybe.Just(value=1).value == 1
    assert Maybe.Nothing() is not None
    assert Maybe.Just(value=1) != Maybe.Nothing()
    assert isinstance(Maybe.Just(value=1), Maybe)
    assert isinstance(Maybe.Nothing(), Maybe)

    class Either(StructuredEnum):
        @dataclass
        class Left:
            value: int

        @dataclass
        class Right:
            value: int

    assert Either.Left(value=1).value == 1
    assert Either.Right(value=1).value == 1
    assert Either.Left(value=1) != Either.Right(value=1)
    assert isinstance(Either.Left(value=1), Either)

    assert Maybe.Just(value=1).model_dump() == {"Just": {"value": 1}}
    assert Maybe.model_validate({"Just": {"value": 1}}) == Maybe.Just(value=1)