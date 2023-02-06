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
        # darkest 23,0,1,2,3,4
        night = self.darken_image(self.base_images[0], 210, 210, 6)
        # slowly brighter 5,6,7,8,9,10
        dawn = self.darken_image(self.base_images[0], 200, 150, 6)
        # brightes 11,12,13,14,15,16
        day = self.darken_image(self.base_images[0],140,140,6)
        # slowly darker 17,18,19,20,21,22
        dusk = self.darken_image(self.base_images[0], 140, 200, 6)
        ordered_images = night+dawn+day+dusk

        self.images.append(ordered_images)

    def darken_image(self, image, from_alpha, to_alpha, steps):
        images = []
        increment = (to_alpha-from_alpha)/steps

        for step in range(steps):
            ghost_image = image.copy()
            ghost_image.fill((0,0,0,from_alpha+increment*step), special_flags=pygame.BLEND_RGBA_MULT)
            shaded_image = image.copy()
            shaded_image.blit(ghost_image, (0,0))
            images.append(shaded_image)
        return images

    def darken_single_image(self, image, alpha):
        ghost_image = image.copy()
        ghost_image.fill((0, 0, 0, alpha), special_flags=pygame.BLEND_RGBA_MULT)
        shaded_image = image.copy()
        shaded_image.blit(ghost_image, (0, 0))
        return shaded_image

    def blend_images(self, image, blend, percentage):
        if not image:
            copy = pygame.Surface(blend.get_size(), pygame.SRCALPHA)
        else:
            copy = image.copy()
        ghost_image = blend.copy()
        ghost_image.set_alpha(min(int(percentage*255), 255)) #fill((255,255,255,min(255,int(1-percentage)*255)), special_flags=pygame.BLEND_RGBA_MULT)
        copy.blit(ghost_image, (0,0))
        #print(min(int(percentage)*255,255))
        return copy

    def update(self, dt):
        time = self.gametime.get_time()
        day = 1000*60*60*24
        fadeout = False
        base_image_index = 0
        opacity = 0

        # 0 - 8 spring
        if time < 9*day:
            base_image_index = 0
            opacity = time/(8*day)
        # 9 - 18 summer
        elif time < 18*day:
            fadeout = True
            base_image_index = 1
            opacity = (time-9*day)/(8*day)
        # 19 - 27 autum
        elif time < 24*day:
            fadeout = True
            base_image_index = 2
            opacity = (time-18*day)/(8*day)

        image = self.blend_images(self.base_images[base_image_index], self.base_images[base_image_index + 1], opacity)

        if fadeout:
            fading_image = self.blend_images(None, self.base_images[base_image_index - 1], 1-opacity)
            image = self.blend_images(fading_image, image, 100)
        image = self.darken_single_image(image, 128 - (self.environment.get_sun_intensity() + 1) * 64)




        self.image = image.copy()



        #days, hours, minutes = self.environment.get_day_time()
        #self.gametime.get_time()/(1000*60*60*self.gametime.GAMESPEED)
        #self.hour = int((self.environment.get_day_time_t()-1) * len(self.images[0])/2)
        #print(self.hour, (self.environment.get_day_time_t()-1), self.environment.get_day_time(), self.environment.get_sun_intensity())




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