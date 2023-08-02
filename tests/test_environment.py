from unittest import TestCase

from PlantEd.server.environment.environment import Environment


class TestEnvironment(TestCase):
    def test_create(self):
        env = Environment()
        self.assertIsInstance(env, Environment)
        print(env)

    def test_to_dict(TestCase):
        env = Environment()
        


    # def test_from_dict()
    # def test_to_json()
    # def test_from_json()
    # def water/nitrate
    # def test/weather