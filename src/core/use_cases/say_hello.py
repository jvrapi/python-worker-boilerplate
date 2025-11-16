from core.ports.logger import Logger
from src.core.entities.hello_command import HelloCommand

from .base import BaseUseCase


class SayHelloUseCase(BaseUseCase[HelloCommand]):
    def __init__(
        self,
        logger: Logger,
    ):
        self.logger = logger

    def execute(self, command: HelloCommand) -> str:
        self.logger.info("Saying hello to %s", command.name)
        return f"Hello, {command.name}!"
