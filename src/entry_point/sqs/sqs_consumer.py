"""SQS Consumer with concurrent message processing."""

import asyncio
import json
import signal
from typing import Any, Generic, Protocol, TypeVar

import aioboto3

from core.use_cases.base import BaseUseCase
from infra.adapters.logging import logger
from infra.config import QueueConfig, Settings, get_settings

T = TypeVar("T")


class FromDict(Protocol[T]):
    pass


class SQSConsumer(Generic[T]):
    """
    Asynchronous SQS consumer with concurrent message processing.

    This implementation follows hexagonal architecture principles,
    isolating AWS SQS infrastructure concerns from business logic.
    """

    def __init__(
        self,
        queue_config: QueueConfig,
        command: type[FromDict[T]],
        use_case: BaseUseCase[T],
        settings: Settings = get_settings(),
    ):
        """
        Initialize SQS consumer.

        Args:
            queue_config: Queue configuration value object
            command: Command class with .from_dict(dict) -> T
            processor: BaseUseCase[T] implementation to process the command
        """
        self.config = queue_config
        self.command_type = command
        self.processor = use_case
        self.semaphore = asyncio.Semaphore(queue_config.max_concurrent_messages)
        self.settings = settings

        self.endpoint_url = getattr(self.settings, "aws_endpoint_url", None)

        self.session = aioboto3.Session()
        self._running = False
        self._tasks: set = set()
        self._shutdown_event = asyncio.Event()

        logger.info(
            "sqs_consumer_initialized",
            queue_url=queue_config.queue_url,
            max_concurrent=queue_config.max_concurrent_messages,
        )

    async def process_message(self, message: dict[str, Any], sqs_client: Any) -> None:
        """
        Process a single message with concurrency control.

        Args:
            message: SQS message
            sqs_client: aioboto3 SQS client
        """
        message_id = message.get("MessageId", "unknown")
        receipt_handle = message.get("ReceiptHandle", "")

        async with self.semaphore:
            try:
                approximate_receive_count = int(
                    message.get("Attributes", {}).get("ApproximateReceiveCount", "1")
                )

                logger.info(
                    "message_received",
                    message_id=message_id,
                    approximate_receive_count=approximate_receive_count,
                )

                try:
                    body_data = json.loads(message.get("Body", "{}"))
                    command: T = self.command_type(**body_data)
                except (json.JSONDecodeError, Exception) as e:
                    logger.error("failed_to_parse_message", error=str(e))
                    raise e
                else:
                    await self.processor.execute(command)

                    if receipt_handle:
                        await sqs_client.delete_message(
                            QueueUrl=self.config.queue_url, ReceiptHandle=receipt_handle
                        )

            except Exception as e:
                logger.error(
                    "message_processing_exception",
                    message_id=message_id,
                    error=str(e),
                    exc_info=True,
                )
                raise e

    async def _fetch_and_process_messages(self, sqs_client: Any) -> None:
        """Fetch messages and spawn processing tasks."""
        try:
            self._running = True
            response = await sqs_client.receive_message(
                QueueUrl=self.config.queue_url,
                MaxNumberOfMessages=self.config.max_number_of_messages,
                WaitTimeSeconds=self.config.wait_time_seconds,
                AttributeNames=["All"],
                MessageAttributeNames=["All"],
            )

            messages = response.get("Messages", [])

            if messages:
                logger.debug("messages_fetched", count=len(messages))

                for message in messages:
                    task = asyncio.create_task(
                        self.process_message(message, sqs_client)
                    )
                    self._tasks.add(task)
                    task.add_done_callback(self._tasks.discard)

        except Exception as e:
            logger.error("fetch_messages_error", error=str(e), exc_info=True)
            self._running = False
            await asyncio.sleep(5)

    async def start(self) -> None:
        """
        Start consuming messages from SQS.

        This method runs indefinitely until stopped.
        """
        self._running = True
        logger.info("sqs_consumer_starting")

        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self.stop()))

        try:
            client_kwargs = {}

            client_kwargs["region_name"] = self.settings.aws_region

            if self.endpoint_url:
                client_kwargs["endpoint_url"] = self.endpoint_url

            async with self.session.client("sqs", **client_kwargs) as sqs_client:
                logger.info("sqs_consumer_started", queue_url=self.config.queue_url)

                while True:
                    if self._shutdown_event.is_set():
                        break

                    await self._fetch_and_process_messages(sqs_client)

        except asyncio.CancelledError:
            logger.info("sqs_consumer_cancelled")
        except Exception as e:
            logger.error("sqs_consumer_error", error=str(e), exc_info=True)
        finally:
            await self._cleanup()

    async def stop(self) -> None:
        """Stop the consumer gracefully."""
        logger.info("sqs_consumer_stopping")
        self._running = False
        self._shutdown_event.set()

    async def _cleanup(self) -> None:
        """Wait for all processing tasks to complete."""
        if self._tasks:
            logger.info("waiting_for_tasks_to_complete", task_count=len(self._tasks))
            await asyncio.gather(*self._tasks, return_exceptions=True)

        logger.info("sqs_consumer_stopped")

    @property
    def is_healthy(self) -> bool:
        """Check if consumer is healthy."""
        return self._running and not self._shutdown_event.is_set()
