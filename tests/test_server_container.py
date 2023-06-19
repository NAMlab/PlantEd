import logging
from unittest import TestCase

from PlantEd.server.server import ServerContainer

logging.basicConfig(
    level="DEBUG",
    format="%(asctime)s %(name)s %(levelname)s:%(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


class TestServerContainer(TestCase):

    def test_start_stop(self):
        logger.info("Run tests for the creation and start of the server.")

        server: ServerContainer = ServerContainer()

        logger.debug("Server successfully created.")

        self.assertIsInstance(server, ServerContainer)

        logger.debug("Starting the server.")

        server.start()

        logger.debug("Server started")

        server.stop()
