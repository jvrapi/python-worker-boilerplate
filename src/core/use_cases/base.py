"""Domain service interfaces - Pure business logic contracts."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class BaseUseCase(Generic[T], ABC):
    """
    Domain service interface for processing a command of type T.

    This defines the contract for processing.
    Implementations should be provided in the application layer.
    """

    @abstractmethod
    async def execute(self, command: T) -> None:
        """
        Process a command.

        Args:
            command: The command to process

        Returns:
            None
        """
        ...
