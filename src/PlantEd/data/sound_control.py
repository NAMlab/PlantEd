"""
Loop through a set of sounds on demand via callback
Use options to set volumes
"""

import os
import random
from pathlib import Path

import pygame.mixer

from PlantEd import config
from PlantEd.data.assets import AssetHandler


fileDir = Path(__file__)
data_dir = fileDir.parent


class SoundControl:
    def __init__(self):
        options = config.load_options()
        self.music_volume = options["music_volume"]
        self.sfx_volume = options["sfx_volume"]
        self.channel = pygame.mixer.Channel(1)

        self.asset_handler = AssetHandler.instance()

        self.start_sfx = self.fill_sfx_array(config.START_PATH, self.sfx_volume)
        self.ambience = self.fill_sfx_array(config.AMBIENCE_PATH, self.sfx_volume)
        self.music = self.fill_music_array(config.MUSIC_PATH, self.music_volume)
        self.bee_sfx = self.fill_sfx_array(config.BEE_SFX_PATH, self.sfx_volume)
        self.snail_sfx = self.fill_sfx_array(config.SNAIL_SFX_PATH, self.sfx_volume)
        self.bug_sfx = self.fill_sfx_array(config.BUG_SFX_PATH, self.sfx_volume)
        self.select_sfx = self.fill_sfx_array(config.SELECT_SFX_PATH, self.sfx_volume)
        # self.confirm_sfx = self.fill_sfx_array(config.CONFIRM_SFX_PATH, self.sfx_volume)
        self.buy_sfx = self.fill_sfx_array(config.BUY_SFX_PATH, self.sfx_volume)
        self.alert_sfx = self.fill_sfx_array(config.ALERT_SFX_PATH, self.sfx_volume)
        self.error_sfx = self.fill_sfx_array(config.ERROR_SFX_PATH, self.sfx_volume)
        self.toggle_sfx = self.fill_sfx_array(config.TOGGLE_SFX_PATH, self.sfx_volume)
        self.loose_sfx = self.fill_sfx_array(config.LOOSE_SFX_PATH, self.sfx_volume)
        self.select_organs_sfx = self.fill_sfx_array(
            config.ORGANS_SFX_PATH, self.sfx_volume
        )
        self.hive_clicked_sfx = self.fill_sfx_array(
            config.HIVE_SFX_PATH, self.sfx_volume
        )
        self.watering_can_sfx = self.fill_sfx_array(
            config.WATERING_CAN, self.sfx_volume
        )
        self.nitrogen_sfx = self.fill_sfx_array(config.NITROGEN, self.sfx_volume)
        self.level_up_sfx = self.fill_sfx_array(config.LEVEL_UP, self.sfx_volume)
        self.spraycan_sfx = self.fill_sfx_array(config.SPRAYCAN, self.sfx_volume)
        self.reward_sfx = self.fill_sfx_array(config.REWARD, self.sfx_volume)
        self.pop_seed = self.fill_sfx_array(config.POP_SEED, self.sfx_volume)

        self.sfx = []
        self.sfx.append(self.start_sfx)
        self.sfx.append(self.ambience)
        self.sfx.append(self.bee_sfx)
        self.sfx.append(self.snail_sfx)
        self.sfx.append(self.bug_sfx)
        self.sfx.append(self.select_sfx)
        # self.sfx.append(self.confirm_sfx)
        self.sfx.append(self.buy_sfx)
        self.sfx.append(self.alert_sfx)
        self.sfx.append(self.error_sfx)
        self.sfx.append(self.toggle_sfx)
        self.sfx.append(self.loose_sfx)
        self.sfx.append(self.select_organs_sfx)
        self.sfx.append(self.hive_clicked_sfx)
        self.sfx.append(self.spraycan_sfx)
        self.sfx.append(self.watering_can_sfx)
        self.sfx.append(self.level_up_sfx)
        self.sfx.append(self.nitrogen_sfx)
        self.sfx.append(self.reward_sfx)
        self.sfx.append(self.pop_seed)

    def play_music(self):
        i = int(random.random() * len(self.music))
        self.channel.play(self.music[i], -1)

    def play_start_sfx(self):
        i = int(random.random() * len(self.start_sfx))
        self.start_sfx[i].play()

    def play_bee_sfx(self):
        i = int(random.random() * len(self.bee_sfx))
        self.bee_sfx[i].play()

    def play_snail_sfx(self):
        i = int(random.random() * len(self.snail_sfx))
        self.snail_sfx[i].play()

    def play_bug_sfx(self):
        i = int(random.random() * len(self.bug_sfx))
        self.bug_sfx[i].play()

    def play_select_sfx(self):
        i = int(random.random() * len(self.select_sfx))
        self.select_sfx[i].play()

    def play_confirm_sfx(self):
        i = int(random.random() * len(self.confirm_sfx))
        self.confirm_sfx[i].play()

    def play_buy_sfx(self):
        i = int(random.random() * len(self.buy_sfx))
        self.buy_sfx[i].play()

    def play_alert_sfx(self):
        i = int(random.random() * len(self.alert_sfx))
        self.alert_sfx[i].play()

    def play_error_sfx(self):
        i = int(random.random() * len(self.error_sfx))
        self.error_sfx[i].play()

    def play_toggle_sfx(self):
        i = int(random.random() * len(self.toggle_sfx))
        self.toggle_sfx[i].play()

    def play_loose_sfx(self):
        i = int(random.random() * len(self.loose_sfx))
        self.loose_sfx[i].play()

    def play_select_organs_sfx(self):
        i = int(random.random() * len(self.select_organs_sfx))
        self.select_organs_sfx[i].play()

    def play_hive_clicked_sfx(self):
        i = int(random.random() * len(self.hive_clicked_sfx))
        self.hive_clicked_sfx[i].play()

    def play_level_up_sfx(self):
        i = int(random.random() * len(self.level_up_sfx))
        self.level_up_sfx[i].play()

    def play_watering_can_sfx(self):
        # i = int(random.random() * len(self.hive_clicked_sfx))
        self.watering_can_sfx[0].play(-1)

    def stop_watering_can_sfx(self):
        self.watering_can_sfx[0].stop()

    def play_spraycan_sfx(self):
        i = int(random.random() * len(self.spraycan_sfx))
        self.spraycan_sfx[i].play()

    def play_nitrogen_sfx(self):
        i = int(random.random() * len(self.nitrogen_sfx))
        self.nitrogen_sfx[i].play()

    def play_reward_sfx(self):
        i = int(random.random() * len(self.reward_sfx))
        self.reward_sfx[i].play()

    def play_pop_seed_sfx(self):
        i = int(random.random() * len(self.pop_seed))
        self.pop_seed[i].play()

    def fill_sfx_array(self, relative_path, volume=None):
        path = data_dir / "assets" / relative_path
        dir_list = os.listdir(path)
        sound_array: list = []
        for item in dir_list:
            path_to_file = relative_path + "/" + item
            sound_array.append(self.asset_handler.sfx(path_to_file, volume))
        return sound_array

    def fill_music_array(self, relative_path, volume=None):
        path = data_dir / "assets" / relative_path
        dir_list = os.listdir(path)
        sound_array: list = []
        for item in dir_list:
            path_to_file = relative_path + "/" + item
            sound_array.append(self.asset_handler.sfx(path_to_file, volume))
        return sound_array

    def reload_options(self):
        options = config.load_options()
        self.music_volume = options["music_volume"]
        self.sfx_volume = options["sfx_volume"]

        for sfx_list in self.sfx:
            for sound in sfx_list:
                sound.set_volume(self.sfx_volume)
        for song in self.music:
            song.set_volume(self.music_volume)
