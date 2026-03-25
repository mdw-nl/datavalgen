from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class CheckResult(Generic[T]):
    """
    Common result shape for validation and other check helpers.

    A check is considered `ok` when it produced no errors. Warnings do not
    make the result non-OK.
    """

    errors: tuple[T, ...] = ()
    warnings: tuple[T, ...] = ()

    @property
    def ok(self) -> bool:
        return not self.errors
