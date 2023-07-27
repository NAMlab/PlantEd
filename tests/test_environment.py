from unittest import TestCase

from PlantEd.server.environment.environment import Environment


class TestEnvironment(TestCase):
    def test_create(self):
        env = Environment()
        self.assertIsInstance(env, Environment)
