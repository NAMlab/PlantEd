import config
import pygame
from utils.gametime import GameTime

class Tree:
    def __init__(self, pos, images, environment):
        self.pos = pos
        self.season = 0             # what tree to show
        self.hour = 0               # brightness for 24 hours generated
        self.percentage_overlay = 0 # overlay for next season
        self.image = images[0]
        #self.surface = pygame.Surface(self.image.size(), pygame.SRCALPHA)
        self.base_images = images   # 4 base images to generate from
        self.environment = environment
        self.gametime = GameTime.instance()
        self.images = []

        self.prepare_hourly_images()

    def prepare_hourly_images(self):
        # darkest 0,1,2,3,4
        hourly_images = self.darken_image(self.base_images[0],0,255,48)
        # 0 : 24
        # slowly brighter 5,6,7,8,9,10
        # brightes 11,12,13,14,15,16
        # slowly darker 17,18,19,20,21,22,23
        ordered_images = []

        myorder = [17,18,19,20,21,22,23,24,25,26,26,26,
                   26,26,26,26,26,26,25,24,23,22,
                   21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8,
                   7, 7, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
        ordered_images = [hourly_images[i] for i in myorder]
        self.images.append(ordered_images)

    def darken_image(self, image, from_alpha, to_alpha, steps):
        images = []

        increment = (to_alpha-from_alpha)/steps
        print(increment)

        for step in range(steps):
            ghost_image = image.copy()
            ghost_image.fill((0,0,0,from_alpha+increment*step), special_flags=pygame.BLEND_RGBA_MULT)
            shaded_image = image.copy()
            shaded_image.blit(ghost_image, (0,0))
            images.append(shaded_image)

        return images


    def update(self, dt):
        #days, hours, minutes = self.environment.get_day_time()
        self.hour = int((self.environment.get_day_time_t()-1) * len(self.images[0])/2)
        self.image = self.images[0][self.hour]
        print(self.hour, (self.environment.get_day_time_t()-1), self.environment.get_day_time())



    def handle_event(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_t:
            self.hour += 1
            if self.hour >= len(self.images[0]):
                self.hour = 0
            self.image = self.images[self.season][self.hour]
        if e.type == pygame.KEYDOWN and e.key == pygame.K_z:
            self.season += 1
            if self.season >= len(self.images):
                self.season = 0
            self.image = self.images[self.season][self.hour]


    def draw(self, screen):
        screen.blit(self.image, self.pos)



    '''def generate_day_night_images(self, amount, image):
        day_night_images = [self.apply_shading(image, (0,0,0,127*i/amount)) for i in range(amount)]
        return day_night_images

    def apply_shading(self, image, color):
        shaded_image = self.shaded_image(image, color)
        return shaded_image

    def ghost_image(self, image, color):
        shaded = image.copy()
        shaded.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
        return shaded

    def overlay_test(self):
        self.image = self.get_mixed(self.base_images[1],self.base_images[2],self.percentage_overlay)

    def get_mixed(self, image, overlay, alpha):
        overlay_copy = overlay.copy()
        overlay_copy.fill((255,255,255,alpha), special_flags=pygame.BLEND_RGBA_MULT)
        image.blit(overlay_copy, (0,0))

        return image

    def shaded_image(self, image, color):
        copied = image.copy()
        ghost = self.ghost_image(image, color)
        copied.blit(ghost, (0, 0))
        return copied'''