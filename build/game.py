import ctypes
import pygame
from pygame.locals import *
import numpy as np
from itertools import repeat
from plant import Plant
from button import Button, RadioButton, Slider, SliderGroup, ToggleButton
from particle import ParticleSystem, PointParticleSystem
from animation import OneShotAnimation
import os, sys
from tool_tip import ToolTipManager, ToolTip
from weather import Environment

currentdir = os.path.abspath('..')
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

pygame.init()
ctypes.windll.user32.SetProcessDPIAware()
true_res = (ctypes.windll.user32.GetSystemMetrics(0), ctypes.windll.user32.GetSystemMetrics(1))
screen = pygame.display.set_mode(true_res, pygame.FULLSCREEN | pygame.DOUBLEBUF, 16)
tmp_screen = pygame.display.set_mode(true_res, pygame.SRCALPHA)
GROWTH = 24
RECALC = 25
WIN = 1
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
plant_pos = (SCREEN_WIDTH - SCREEN_WIDTH/4, SCREEN_HEIGHT - SCREEN_HEIGHT/5)

FONT = pygame.font.SysFont('arial', 24)
TITLE_FONT = pygame.font.SysFont('arialblack', 24)

GREEN = (19, 155, 23)
BLUE = (75, 75, 200)
SKY_BLUE = (169, 247, 252)

# nice clutter free img manager
fileDir = os.path.dirname(os.path.realpath('__file__'))
assets_dir = os.path.join(fileDir, '../assets/')
_image_library = {}
def get_image(path):
        path = os.path.join(assets_dir, path)
        global _image_library
        image = _image_library.get(path)
        if image == None:
                canonicalized_path = path.replace('/', os.sep).replace('\\', os.sep)
                image = pygame.image.load(canonicalized_path).convert_alpha()
                _image_library[path] = image
        return image

def shake():
    s = -1  # looks unnecessary but maybe cool, int((random.randint(0,1)-0.5)*2)
    for _ in range(0, 3):
        for x in range(0, 20, 5):
            yield (x * -1, x * s)
        for x in range(20, 0, 5):
            yield (x * -1, x * s)
        s *= -1
    while True:
        yield (0, 0)

menu_plant = [get_image("plant_growth_pod/plant_growth_{index}.png".format(index=i)).convert_alpha() for i in range(0, 11)]
can = get_image("watering_can_outlined.png")
can_icon = pygame.transform.scale(can, (64,64)).convert_alpha()
can_tilted = get_image("watering_can_outlined_tilted.png")
background = pygame.transform.scale(get_image("background_empty_sky.png"), (SCREEN_WIDTH, SCREEN_HEIGHT)).convert_alpha()
leaf_icon = get_image("leaf_small.png").convert_alpha()
leaf_icon_big = pygame.transform.scale(leaf_icon, (128,128)).convert_alpha()
stem_icon = get_image("stem_small.png").convert_alpha()
stem_icon_big = pygame.transform.scale(stem_icon, (128,128)).convert_alpha()
root_icon = get_image("roots_small.png").convert_alpha()
root_icon_big = pygame.transform.scale(root_icon, (128,128)).convert_alpha()
starch_icon = get_image("starch.png").convert_alpha()
starch_icon_big = pygame.transform.scale(starch_icon, (128,128)).convert_alpha()
drain_icon = get_image("drain_icon.png").convert_alpha()
photo_energy = pygame.transform.scale(get_image("photo_energy.png"),(15,15)).convert_alpha()
starch_energy = pygame.transform.scale(get_image("starch_energy.png"),(15,15)).convert_alpha()
#pygame.mixer.music.load()
water_sound = pygame.mixer.Sound('../assets/water_can.mp3')
pygame.mixer.music.load('../assets/background_music.mp3')
pygame.mixer.music.play(-1,0)


class Scene(object):
    def __init__(self):
        pass

    def render(self, screen):
        raise NotImplementedError

    def update(self, dt):
        raise NotImplementedError

    def handle_events(self, events):
        raise NotImplementedError


class TitleScene(object):
    def __init__(self):
        super(TitleScene, self).__init__()
        self.font = pygame.font.SysFont('Arial', 56)
        self.sfont = pygame.font.SysFont('Arial', 32)
        self.centre = (SCREEN_WIDTH/2-menu_plant[0].get_width()/2, SCREEN_HEIGHT/7)
        self.particle_systems = []
        self.watering_can = can
        self.plant_size = 0
        self.plant_growth_pos = []
        self.offset = repeat((0, 0))
        self.max_plant_size = 100
        self.images = menu_plant
        self.image = self.images[0]
        self.mouse_pos = pygame.mouse.get_pos()
        pygame.mouse.set_visible(False)
        self.particle_systems.append(
            ParticleSystem(40, spawn_box=Rect(self.mouse_pos[0], self.mouse_pos[1], 0, 0), lifetime=8, color=BLUE ,apply_gravity=True,
                           speed=[0,5], spread=[3,0], active = False))
        self.text1 = self.font.render('PlantEd', True, (255, 255, 255))
        self.water_plant_text = self.sfont.render('> water plant to start <', True, (255, 255, 255))
        self.start_game_text = self.sfont.render('> press space to start <', True, (255, 255, 255))
        self.text2 = self.water_plant_text

    def render(self, screen):
        tmp_screen.fill((50, 50, 50))
        tmp_screen.blit(self.image, self.centre)
        tmp_screen.blit(self.text1, (SCREEN_WIDTH/8, SCREEN_HEIGHT/8))
        tmp_screen.blit(self.text2, (SCREEN_WIDTH/2-self.water_plant_text.get_width()/2, SCREEN_HEIGHT-SCREEN_HEIGHT/7))
        for system in self.particle_systems:
            if system.active:
                system.draw(screen)
        tmp_screen.blit(self.watering_can, (self.mouse_pos[0],self.mouse_pos[1]-100))
        screen.blit(tmp_screen, next(self.offset))

    def update(self, dt):
        step = self.max_plant_size / (len(self.images))
        index = int(self.plant_size/step)
        if index < len(self.images):
            self.image = self.images[index]
        if self.mouse_pos[0] > SCREEN_WIDTH / 3 and self.mouse_pos[0] < SCREEN_WIDTH / 3 * 2 and self.particle_systems[0].active:
            self.plant_size += 1
        if self.plant_size > self.max_plant_size:
            self.text2 = self.start_game_text
        for system in self.particle_systems:
            if system.active:
                system.update(dt)

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN and e.key == K_SPACE:
                if self.plant_size > self.max_plant_size:
                    self.manager.go_to(GameScene(0))
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            if e.type == KEYDOWN and e.key == K_a:
                self.offset = shake()
            if e.type == MOUSEBUTTONDOWN:
                self.particle_systems[0].activate()
                self.watering_can = can_tilted
            if e.type == MOUSEMOTION:
                self.mouse_pos = pygame.mouse.get_pos()
                self.particle_systems[0].spawn_box = pygame.Rect(self.mouse_pos[0], self.mouse_pos[1], 0, 0)
            if e.type == MOUSEBUTTONUP:
                self.particle_systems[0].deactivate()
                self.watering_can = can


class CustomScene(object):
    def __init__(self, text):
        self.text = text
        super(CustomScene, self).__init__()
        self.font = pygame.font.SysFont('Arial', 56)
        self.sfont = pygame.font.SysFont('Arial', 32)
        self.centre = (SCREEN_WIDTH, SCREEN_HEIGHT/2)

    def render(self, screen):
        screen.fill((0, 0, 0))
        text1 = self.font.render('PlantEd', True, (0, 0, 0))
        text2 = self.sfont.render('YOU WON!', True, (0, 0, 0))
        text3 = self.sfont.render('> press any key to continue <', True, (0, 0, 0))
        screen.blit(text1, (SCREEN_WIDTH/8, SCREEN_HEIGHT/8))
        screen.blit(text2, (SCREEN_WIDTH/8, SCREEN_HEIGHT/6))
        screen.blit(text3, (SCREEN_WIDTH/2-text3.get_width()/2, SCREEN_HEIGHT-SCREEN_HEIGHT/7))

    def update(self, dt):
        pass

    def handle_events(self, events):
        for e in events:
            if e.type == KEYDOWN:
                self.manager.go_to(TitleScene())


class SceneMananger(object):
    def __init__(self):
        self.go_to(GameScene(0))

    def go_to(self, scene):
        self.scene = scene
        self.scene.manager = self


class GameScene(Scene):
    def __init__(self, level):
        super(GameScene, self).__init__()
        pygame.mouse.set_visible(True)
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.offset = repeat((0, 0))
        self.screen_changes = [pygame.Rect(0,0,SCREEN_WIDTH, SCREEN_HEIGHT)]
        self.manager = None
        self.hover_message = None
        self.font = TITLE_FONT  #pygame.font.SysFont('Arial', 24)
        self.sfont = FONT   #pygame.font.SysFont('Arial', 14)
        self._running = True
        self.plant = Plant(plant_pos)
        self.environment = Environment(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.particle_systems = []
        self.sprites = pygame.sprite.Group()
        self.button_sprites = pygame.sprite.Group()
        self.sliders = []
        self.items = []
        self.animations = []
        self.watering_can = {"active": False,
                             "button": Button(780, 260, 64, 64, [self.activate_watering_can], self.sfont,
                                              image=can_icon, post_hover_message=self.post_hover_message, hover_message="Water Your Plant, Cost: 1"),
                             "image": can,
                             "amount": 0,
                             "pouring": False}
        self.can = can

        #(660, 250, 200, 350)
        add_leaf_button = Button(676, 260, 64, 64, [self.plant.get_actions().add_leave], self.sfont,
                                 image=leaf_icon, post_hover_message=self.post_hover_message, hover_message="Buy one leaf, Cost: 1")
        self.items.append({"name": "add_leaf",
                           "button": add_leaf_button,
                           "cost": 1})
        self.button_sprites.add(add_leaf_button)
        self.items.append({"name": "can",
                           "button": self.watering_can["button"],
                           "cost": 1})
        self.button_sprites.add(self.watering_can["button"])

        radioButtons = [
            RadioButton(100, 70, 64, 64, [self.plant.set_target_organ_leaf, self.activate_biomass_objective], FONT, image=leaf_icon),
            RadioButton(180, 70, 64, 64, [self.plant.set_target_organ_stem, self.activate_biomass_objective], FONT, image=stem_icon),
            RadioButton(260, 70, 64, 64, [self.plant.set_target_organ_root, self.activate_biomass_objective], FONT, image=root_icon),
            RadioButton(460, 70, 64, 64, [self.plant.set_target_organ_starch, self.activate_starch_objective], FONT, image=starch_icon)
        ]
        for rb in radioButtons:
            rb.setRadioButtons(radioButtons)
            self.button_sprites.add(rb)
        radioButtons[2].button_down = True
        #self.add_leaf_button = Button(523, 503, 100, 40, [self.plant.get_actions().add_leave] , self.sfont, text="Buy Leaf")
        #self.button_sprites.add(Button(600, 600, 64, 64, [self.activate_watering_can()] , self.sfont, text="Activate Can"))

        self.button_sprites.add(ToggleButton(100, 385, 210, 40, [], self.sfont, "Photosysnthesis", pressed=True, fixed=True))
        toggle_starch_button = ToggleButton(460, 385, 150, 40, [self.toggle_starch_as_resource], self.sfont, "Drain Starch")
        self.plant.organs[3].toggle_button = toggle_starch_button
        self.button_sprites.add(toggle_starch_button)
        self.leaf_slider = Slider((100, 140, 15, 200), self.sfont, (50, 20), organ=self.plant.organs[0], plant=self.plant, active=False)
        self.stem_slider = Slider((180, 140, 15, 200), self.sfont, (50, 20), organ=self.plant.organs[1], plant=self.plant, active=False)
        self.root_slider = Slider((260, 140, 15, 200), self.sfont, (50, 20), organ=self.plant.organs[2], plant=self.plant, percent=100)
        self.sliders.append(self.leaf_slider)
        self.sliders.append(self.stem_slider)
        self.sliders.append(self.root_slider)
        SliderGroup([slider for slider in self.sliders], 100)
        self.sliders.append(Slider((536, 70, 15, 200), self.sfont, (50, 20), organ=self.plant.organs[3], plant=self.plant, percent=100))
        particle_photosynthesis_points = [[330,405],[380,405],[380,100],[330,100]]
        self.photosynthesis_particle = PointParticleSystem(particle_photosynthesis_points,self.plant.get_growth_rate()*20, images=[photo_energy], speed=(2,0), callback=self.plant.get_leaf_photon)
        particle_starch_points = [[430, 405], [380, 405], [380, 100], [330, 100]]
        self.starch_particle = PointParticleSystem(particle_starch_points, 30, images=[starch_energy], speed=(2,0), active=False, callback=self.plant.organs[3].get_rate)
        self.particle_systems.append(self.photosynthesis_particle)
        self.particle_systems.append(self.starch_particle)
        #self.can_particle_system = ParticleSystem(40, spawn_box=Rect(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, 0, 0), lifetime=8, color=BLUE, apply_gravity=True, speed=[0, 3], spread=True, active=False)
        self.can_particle_system = ParticleSystem(40, spawn_box=Rect(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2, 0, 0), lifetime=8, color=BLUE,apply_gravity=True,speed=[0, 5], spread=[3, 0], active=False)
        self.particle_systems.append(self.can_particle_system)

        self.tool_tip_manager = ToolTipManager(
            [ToolTip(855,150,0,0,["Welcome to PlantEd!", "> This is the first demo <", "Grow your seedling", "into a big plant."], self.sfont, self.font, button_group=self.button_sprites, mass=0),
             ToolTip(655,380,0,0,["Your seed has no Leaves yet.", "Use Your Starch Deposit", "But don't waste it"], self.sfont, button_group=self.button_sprites, mass=0, point=(-45,30)),
             ToolTip(370,140,0,0,["These are your main 3 Organs.", "Select them for Details.", "Once your roots are big enough", "your are able to grow a stem!"], self.sfont, button_group=self.button_sprites, mass=1, point=(-40,0)),
             ToolTip(300,300,0,0,["Grow your stem", "to get your first leaves", "The biomass can be", "split up between all organs."], self.sfont, button_group=self.button_sprites, mass=6, point=(-50,20)),
             ToolTip(685,450,0,0,["One leaf can be added"," for each skillpoint", "But remember to keep", "the stem big enough"], self.sfont, button_group=self.button_sprites, mass=10, point=(-50,20)),
             ToolTip(240, 230, 0, 0, ["You can fill up", "your starch deposit", "instead of growing"], self.sfont, button_group=self.button_sprites, mass=15, point=(50, 20)),
             ToolTip(850,300,0,0,["Congratulations, you reached", " 30gr of plant mass"], self.sfont, button_group=self.button_sprites, mass=30, point=(50,20)),
             ToolTip(1100,300,0,0,["50 Gramms!"], self.sfont, button_group=self.button_sprites, mass=50, point=(50,20)),
             ToolTip(1100,300,0,0,["100 Gramms!"], self.sfont, button_group=self.button_sprites, mass=100, point=(50,20)),
             ToolTip(1000,600,0,0,["You son of a b*tch did it!" "200 Gramms, thats game"], self.sfont, button_group=self.button_sprites, mass=200, point=(50,20),)],
            callback=self.plant.get_biomass)
        pygame.time.set_timer(GROWTH, 1000)

    def handle_events(self, event):
        for e in event:
            if e.type == GROWTH:
                self.plant.grow()
            if e.type == QUIT: raise SystemExit("QUIT")
            if e.type == KEYDOWN and e.key == K_ESCAPE:
                self.manager.go_to(TitleScene())
            if e.type == KEYDOWN and e.key == K_SPACE:
                self.manager.go_to(GameScene(0))
            for button in self.button_sprites:
                # all button_sprites handle their events
                button.handle_event(e)
            if self.watering_can["active"]:
                if e.type == MOUSEBUTTONDOWN:
                        self.watering_can["image"] = can_tilted
                        self.watering_can["pouring"] = True
                        self.can_particle_system.activate()
                        pygame.mixer.Sound.play(water_sound, -1)
                if e.type == MOUSEBUTTONUP:
                    self.watering_can["image"] = can
                    self.can_particle_system.deactivate()
                    pygame.mixer.Sound.stop(water_sound)
                    self.watering_can["pouring"] = False
                if e.type == MOUSEMOTION:
                    x,y = pygame.mouse.get_pos()
                    self.can_particle_system.spawn_box = Rect(x,y+100,0,0)
            if e.type == KEYDOWN and e.key == K_a:
                self.offset = shake()
                self.plant.soil_moisture = self.plant.soil_moisture + 1
            if e.type == KEYDOWN and e.key == K_d:
                self.plant.soil_moisture = self.plant.soil_moisture - 1
            for slider in self.sliders:
                slider.handle_event(e)
            self.plant.handle_event(e)
            for tips in self.tool_tip_manager.tool_tips:
                tips.handle_event(e)
            '''
            if e.type == WIN:
                print("you won")
                self.exit()'''

    def update(self, dt):
        #for animation in self.animations:
            #animation.update()
        self.plant.update()
        # beware of ugly
        if self.plant.get_biomass() > self.plant.seedling.max and not self.stem_slider.active:
            self.stem_slider.active = True
        if self.plant.organs[1].active_threshold >= 2 and not self.leaf_slider.active:
            self.leaf_slider.active = True

        #check day_night, sun_intensity

        for slider in self.sliders:
            slider.update()
        for system in self.particle_systems:
            system.update(dt)

        # watering can
        if self.watering_can["pouring"]:
            self.watering_can["amount"] -= 1
            if self.watering_can["amount"] <= 0:
                self.deactivate_watering_can()

        self.environment.update(dt, self.get_day_time(), self.get_sun_intensity())
        self.tool_tip_manager.update()

    def render(self, screen):
        self.draw_background(tmp_screen)
        self.environment.draw_background(tmp_screen)
        for sprite in self.sprites:
            if not sprite.update():
                self.sprites.remove(sprite)

        self.draw_plant(tmp_screen)
        #self.darken_display_daytime(tmp_screen) # --> find smth better
        self.sprites.draw(tmp_screen)
        self.draw_particle_systems(tmp_screen)
        self.draw_organ_ui(tmp_screen)
        self.environment.draw_foreground(tmp_screen)
        self.button_sprites.draw(tmp_screen)
        self.tool_tip_manager.draw(tmp_screen)

        if self.hover_message:
            x,y = pygame.mouse.get_pos()
            tmp_screen.blit(self.hover_message, (x+10,y))

        if self.watering_can["active"]:
            mouse_pos = pygame.mouse.get_pos()
            normalized_amount = (self.watering_can["image"].get_width()/100)*self.watering_can["amount"] # for max 100 amount
            pygame.draw.rect(tmp_screen, (255,255,255), (mouse_pos[0], mouse_pos[1],normalized_amount, 20))
            tmp_screen.blit(self.watering_can["image"], (mouse_pos))
        screen.blit(tmp_screen, next(self.offset))

    def exit(self):
        self.manager.go_to(CustomScene("You win!"))

    def die(self):
        self.manager.go_to(CustomScene("You lose!"))

    def post_hover_message(self, message):
        self.hover_message = message if message else None




    def activate_starch_objective(self):
        # change particle system to follow new lines
        if self.plant.produce_biomass:
            photosysnthesis_lines = self.photosynthesis_particle.points
            photosysnthesis_lines[3] = [430, 100]
            self.photosynthesis_particle.change_points(photosysnthesis_lines)
            self.photosynthesis_particle.particle_counter = 0
            self.photosynthesis_particle.particles.clear()
            starch_lines = self.starch_particle.points
            starch_lines[3] = [430, 100]
            self.starch_particle.change_points(starch_lines)
            self.starch_particle.particle_counter = 0
            self.starch_particle.particles.clear()
            self.plant.activate_starch_objective()

    def toggle_starch_as_resource(self):
        self.starch_particle.particles.clear()
        if self.plant.use_starch:
            self.starch_particle.active = False
            self.plant.deactivate_starch_resource()
        else:
            self.starch_particle.active = True
            self.plant.activate_starch_resource()

    def activate_biomass_objective(self):
        if not self.plant.produce_biomass:
            photosysnthesis_lines = self.photosynthesis_particle.points
            photosysnthesis_lines[3] = [330, 100]
            self.photosynthesis_particle.change_points(photosysnthesis_lines)
            self.photosynthesis_particle.particle_counter = 0
            self.photosynthesis_particle.particles.clear()
            starch_lines = self.starch_particle.points
            starch_lines[3] = [330, 100]
            self.starch_particle.change_points(starch_lines)
            self.starch_particle.particle_counter = 0
            self.starch_particle.particles.clear()
            self.plant.activate_biomass_objective()


    def get_day_time(self):
        # one day rl: ticks*60*60*24, ingame: ticks*6*60
        # one hour rl: ticks*60*60, ingame: ticks*6*60/24
        # one minute rl: ticks*60, ingame: ticks*6/24
        ticks = pygame.time.get_ticks()
        day = 1000*60
        hour = day/24
        min = hour/60
        hours = (ticks % day) / hour
        minutes = (ticks % hour) / min
        return hours, minutes

    def get_sun_intensity(self):
        return (np.sin(np.pi/2-np.pi/5+((pygame.time.get_ticks()/(1000 * 60)) * np.pi*2)))  # get time since start, convert to 0..1, 6 min interval

    # buy can basically
    def activate_watering_can(self):
        if self.plant.upgrade_points <= 0:
            return
        self.plant.upgrade_points -= 1
        self.watering_can["active"] = True
        self.watering_can["amount"] = 100
        pygame.mouse.set_visible(False)

    def deactivate_watering_can(self):
        pygame.mixer.Sound.stop(water_sound)
        self.can_particle_system.deactivate()
        self.watering_can["image"] = can
        self.watering_can["active"] = False
        self.watering_can["amount"] = 0
        pygame.mouse.set_visible(True)

    def add_animation(self, images, duration, pos, speed=1):
        self.sprites.add(OneShotAnimation(images, duration, pos, speed))

    def set_growth_target_leaves(self):
        self.plant.target_organ = self.plant.LEAVES

    def set_growth_target_stem(self):
        self.plant.target_organ = self.plant.STEM

    def set_growth_target_roots(self):
        self.plant.target_organ = self.plant.ROOTS

    def draw_particle_systems(self, screen):
        for system in self.particle_systems:
            system.draw(screen)

    def darken_display_daytime(self, screen):
        s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        day_time = (((self.get_sun_intensity() + 1) / 2) * 128)
        return day_time

    def draw_leave(self, screen, pos, size, rot, color):
        leave_surface = pygame.Surface((size[0], size[1]))
        surface = leave_surface.convert_alpha()  # check if necessary
        surface.fill((0, 0, 0, 0))  # "
        pygame.draw.ellipse(surface, color, Rect(0, 0, leave_surface.get_width(), leave_surface.get_height()))
        surface = pygame.transform.rotate(surface, rot)
        screen.blit(surface, (pos[0], pos[1] - surface.get_bounding_rect().height))

    def draw_background(self, screen):
        screen.fill(SKY_BLUE)
        screen.blit(background, (0,0))

    def draw_organ_ui(self, screen):
        white = (255, 255, 255)
        white_transparent = (255, 255, 255, 128)
        # new surface to get alpha
        s = pygame.Surface((SCREEN_WIDTH / 2, SCREEN_HEIGHT), pygame.SRCALPHA)
        w,h = s.get_size()

        # headbox
        pygame.draw.rect(s, (255, 255, 255, 180), Rect(60, 10, 580, 30), border_radius=3)
        production_text = self.font.render("Production", True, (0, 0, 0))  # title
        s.blit(production_text, dest=(290-production_text.get_size()[0]/2, 10))

        for slider in self.sliders:
            slider.draw(screen)

        # draw life tax
        life_tax_pos = Rect(360, 230, 64, 64)
        pygame.draw.rect(s, white_transparent, life_tax_pos, border_radius=5)
        starch_lvl = self.sfont.render("TAX", True, (0, 0, 0))  # title
        s.blit(starch_lvl, starch_lvl.get_rect(center=life_tax_pos.center))

        # draw starch details
        lvl_pos = Rect(530, 270, 64, 64)
        # linecolor white to red for flow
        # rgb--> color[0]
        green = blue = int(255 - self.plant.organs[3].percentage / 100 * 255)
        alpha = int(255-blue/2)
        for i in range(0,3):
            pygame.draw.line(s, (255, green, blue, alpha), (545, 280+i*10), (560, 300+i*10), width=4)
            pygame.draw.line(s, (255, green, blue, alpha), (575, 280+i*10), (560, 300+i*10), width=4)

        # draw starch pool
        pool_height = 180
        pool_rect = Rect(476, 150, 32, pool_height)
        pygame.draw.rect(s, white_transparent, pool_rect, border_radius=3)
        pool_limit = self.plant.organs[3].get_threshold()
        pool_level = self.plant.organs[3].mass * pool_height/pool_limit
        pool_rect = Rect(pool_rect[0], pool_rect[1]+pool_height-pool_level, 32, pool_level)
        pygame.draw.rect(s, white, pool_rect, border_radius=3)
        pool_level_text = self.sfont.render("{:.0f}".format(self.plant.organs[3].mass), True, (0, 0, 0))  # title
        s.blit(pool_level_text, pool_level_text.get_rect(center=pool_rect.center))

        # overal stats
        # plant health?
        # plant size
        # plant mass
        # leaf area, mass
        # skillpoints
        # temp
        pygame.draw.rect(s, (255,255,255,180), (660, 10, 200, 30), border_radius=3)
        plant_text = self.font.render("Plant Name", True, (0, 0, 0))  # title
        s.blit(plant_text, dest=(760-plant_text.get_size()[0]/2, 10))

        pygame.draw.rect(s, white_transparent, (660, 50, 200, 150), border_radius=3)

        # biomass
        biomass_text = self.sfont.render("Plant Mass:", True, (0, 0, 0))
        s.blit(biomass_text, dest=(670, 60))
        biomass = self.sfont.render("{:.4f}".format(self.plant.get_biomass()), True, (0, 0, 0))  # title
        s.blit(biomass, dest=(860-biomass.get_width()-5, 60))

        # skillpoints
        biomass_text = self.sfont.render("Chloroplast:", True, (0, 0, 0))
        s.blit(biomass_text, dest=(670, 90))
        biomass = self.sfont.render("{}".format(self.plant.upgrade_points), True, (0, 0, 0))  # title
        s.blit(biomass, dest=(860-biomass.get_width()-5, 90))

        # shop
        pygame.draw.rect(s, (255, 255, 255, 180), (660, 210, 200, 30), border_radius=3)
        shop_text = self.font.render("Shop", True, (0, 0, 0))  # title
        s.blit(shop_text, dest=(760 - shop_text.get_size()[0] / 2, 210))

        pygame.draw.rect(s, white_transparent, (660, 250, 200, 370), border_radius=3)
        #items



        # headbox
        pygame.draw.rect(s, (255, 255, 255, 180), Rect(60, 450, 580, 30), border_radius=3)
        leave_title = self.font.render("Organ", True, (0, 0, 0))  # title
        s.blit(leave_title, dest=(290 - leave_title.get_size()[0] / 2, 450))
        if self.plant.target_organ.type == self.plant.LEAVES:
            image = leaf_icon_big
            #self.button_sprites.add(self.button)
        elif self.plant.target_organ.type == self.plant.STEM:
            image = stem_icon_big
        elif self.plant.target_organ.type == self.plant.ROOTS:
            image = root_icon_big
        elif self.plant.target_organ.type == self.plant.STARCH:
            image = starch_icon_big

        # draw plant image + exp + lvl + rate + mass
        s.blit(image, (100,490))

        exp_width = 128
        pygame.draw.rect(s, white_transparent, Rect(100, 600, exp_width, 25), border_radius=0)
        needed_exp = self.plant.target_organ.get_threshold()
        exp = self.plant.target_organ.mass / needed_exp
        width = int(exp_width / 1 * exp)
        pygame.draw.rect(s, (255, 255, 255), Rect(100, 600, width, 25), border_radius=0)  # exp
        text_organ_mass = self.font.render("{:.2f} / {threshold}".format(self.plant.target_organ.mass,
                                                                    threshold=self.plant.target_organ.get_threshold()),
                                      True, (0, 0, 0))
        s.blit(text_organ_mass, dest=(105, 596))  # Todo change x, y

        pygame.draw.rect(s, white_transparent,(245, 490, 400, 125), border_radius=3)

        # growth_rate in seconds
        growth_rate = self.sfont.render("Growth Rate /s {:.5f}".format(self.plant.target_organ.growth_rate), True, (0, 0, 0))
        s.blit(growth_rate, dest=(245, 500))  # Todo change x, y

        # level
        pygame.draw.circle(s, white_transparent, (100, 510,), 20)
        pygame.draw.circle(s, white, (100, 510,), 20, width=3)
        level = self.sfont.render("{:.0f}".format(self.plant.target_organ.level), True, (0, 0, 0))
        s.blit(level, (100-level.get_width()/2,510-level.get_height()/2))

        # mass
        mass = self.sfont.render("Organ Mass {:.5f}".format(self.plant.target_organ.mass), True, (0, 0, 0))
        s.blit(mass, dest=(245, 550))

        # clock
        hours, minutes = self.get_day_time()
        output_string = "{0:02}:{1:02}".format(int(hours), int(minutes))
        clock_text = self.sfont.render(output_string, True, (0, 0, 0))
        screen.blit(clock_text, clock_text.get_rect(center=(SCREEN_WIDTH/2,20)))

        day_time = ((self.get_sun_intensity() + 1) / 2)
        sun_intensity = self.sfont.render("{:.2}".format(day_time), True, (0, 0, 0))
        screen.blit(sun_intensity, sun_intensity.get_rect(center=(SCREEN_WIDTH / 2+100, 20)))
        screen.blit(s, (0, 0))

    def draw_time_line(self, screen):
        # draw a simple grey line with 90° crosses
        line_length = int(self.width/2)
        surface = pygame.Surface((line_length, int(self.height/10)), pygame.SRCALPHA)
        pygame.draw.line(surface, (169, 169, 169, 100),
                         (0, int(self.height / 20)),
                         (line_length, int(self.height / 20)),
                         width=2)
        for i in range(0, 9):
            pygame.draw.line(surface, (169, 169, 169, 100),
                             (i*line_length/9+1, int(self.height / 20)-10),
                             (i*line_length/9+1, int(self.height / 20)+10),
                             width=2)
        screen.blit(surface, (self.width/2, 0))

    def draw_plant(self, screen):
        self.plant.draw(screen)

    def on_cleanup(self):
        pygame.quit()


def main():
    pygame.init()

    # screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
    pygame.display.set_caption("PlantEd_0.1")
    timer = pygame.time.Clock()
    running = True

    manager = SceneMananger()

    while running:
        dt = timer.tick(60)/1000.0

        fps = str(int(timer.get_fps()))
        fps_text = FONT.render(fps, False, (255,255,255))
        #print(fps)

        if pygame.event.get(QUIT):
            running = False
            return

        # manager handles the current scene
        manager.scene.handle_events(pygame.event.get())
        manager.scene.update(dt)
        manager.scene.render(screen)
        screen.blit(fps_text, (800, 30))
        pygame.display.update()

if __name__ == "__main__":
    main()
