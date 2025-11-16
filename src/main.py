"""
SQS Worker Main Entry Point

This is the main entry point for the SQS worker application.
It orchestrates the initialization and running of all components.
Architecture simplified: SQS Consumer → Handler → Domain Logic
"""

import asyncio

from dotenv import find_dotenv, load_dotenv

import entry_point.http.health as health
from core.entities.hello_command import HelloCommand
from core.use_cases.say_hello import SayHelloUseCase
from entry_point.sqs import SQSConsumer
from infra.adapters.logging import logger
from infra.config import QueueConfig, get_settings

load_dotenv(find_dotenv())


async def main() -> None:
    """Main application entry point."""
    settings = get_settings()

    health_server = health.HealthServer(
        host=settings.health_check_host,
        port=settings.health_check_port,
        health_check=lambda: all(c.is_healthy for c in consumers),
    )

    health_task = asyncio.create_task(health_server.start())

    logger.info(
        "application_starting",
        service_name=settings.service_name,
        environment=settings.environment,
    )

    consumers: list[SQSConsumer] = [
        SQSConsumer(
            queue_config=QueueConfig(
                queue_url=settings.sqs_queue_url,
                max_concurrent_messages=settings.max_concurrent_messages,
                wait_time_seconds=settings.wait_time_seconds,
                visibility_timeout=settings.visibility_timeout,
                max_number_of_messages=settings.max_number_of_messages,
            ),
            command=HelloCommand,
            use_case=SayHelloUseCase(
                logger=logger,
            ),
        )
    ]

    await asyncio.sleep(1)
    health_server.mark_ready()

    logger.info("application_ready")

    try:
        print("Application is running. Press Ctrl+C to exit.")

    except KeyboardInterrupt:
        logger.info("keyboard_interrupt_received")
    except Exception as e:
        logger.error("application_error", error=str(e), exc_info=True)
    finally:
        logger.info("application_shutting_down")

        health_server.mark_not_ready()

        health_task.cancel()

        try:
            await health_task
        except asyncio.CancelledError:
            pass

        logger.info("application_stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as ex:
        logger.error("application_error", error=str(ex), exc_info=True)
