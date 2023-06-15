from PlantEd.utils.button import Slider
from unittest import TestCase
from PlantEd import config
import logging


class TestSlider(TestCase):
    def setUp(self):
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger().setLevel(logging.DEBUG)

    def test_subtraction(self):
        initial_percent = 100
        slider: Slider = Slider(
            (0,0,100,100),
            config.FONT,
            (20,20),
            percent=initial_percent,
            )

        # normal subtraction
        target_percent = 10
        delta = 90
        slider.sub_percentage(delta)
        self.assertEqual(slider.get_percentage(), target_percent)

        # subtraction, not enough percent to subtract -> should return difference
        slider.set_percentage(50)
        self.assertEqual(slider.get_percentage(), 50)
        target_percent = -10
        delta = 60
        excess = slider.sub_percentage(60)
        self.assertEqual(slider.get_percentage(), 0)
        self.assertEqual(excess, target_percent)

        # addition
        slider.set_percentage(10)
        self.assertEqual(slider.get_percentage(), 10)
        target_percent = 100
        delta = 90
        slider.sub_percentage(-90)
        self.assertEqual(slider.get_percentage(), target_percent)

        # add to much
        slider.set_percentage(50)
        self.assertEqual(slider.get_percentage(), 50)
        target_percent = 110
        delta = -60
        excess = slider.sub_percentage(delta)
        self.assertEqual(10, excess)
        self.assertEqual(slider.get_percentage(), 100)