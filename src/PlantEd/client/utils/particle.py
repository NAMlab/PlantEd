import pygame, random
from pygame import Rect

"""
With a set list of particle systems, once can be activated at a time.
Basically a fancy timer to switch them on and off.
"""


class ParticleExplosion:
    def __init__(self, systems, interval, play_explosion_sound):
        self.systems: list[ParticleSystem] = systems
        self.interval: float = interval
        self.timer: int = 0
        self.current_system: int = 0
        self.running: bool = False
        self.play_explosion_sound: callable = play_explosion_sound

    def update(self, dt):
        for system in self.systems:
            system.update(dt)
        if self.running:
            self.timer -= dt
            if self.timer <= 0:
                self.systems[self.current_system].activate()
                self.play_explosion_sound()
                self.timer = self.interval
                self.current_system += 1
                if self.current_system >= len(self.systems):
                    self.stop()

    def start(self):
        if len(self.systems) > 0:
            print("LENS: ", len(self.systems))
            self.timer = self.interval
            self.running = True
            self.current_system = 0

    def stop(self):
        self.running = False
        self.current_system = 0
        self.timer = 0

    def draw(self, screen):
        for system in self.systems:
            system.draw(screen)


class Particle:
    def __init__(
            self,
            pos: tuple[float, float],
            vel: tuple[float, float],
            size: float,
            gravity: float = 0,
            braking: float = 0,
            lifetime: float = -1,

    ):
        self.pos = pos
        self.vel = vel
        self.size = size
        self.gravity = gravity
        self.braking = braking
        self.lifetime = lifetime
        self.dead = False

    def move(self, dt):
        self.vel = (
            self.vel[0],
            self.vel[1] + (self.gravity * dt)
        )
        self.pos = (
            self.pos[0] + self.vel[0] * dt,
            self.pos[1] + self.vel[1] * dt
        )


class ParticleSystem:
    def __init__(
            self,
            max_particles: int,
            spawn_box: pygame.Rect,
            boundary_box: pygame.Rect = None,
            vel: tuple[float, float] = (0,0),
            spread: tuple[float, float] = (0, 0),
            color: tuple[int, int, int] = (0, 0, 0),
            size: float = 10,
            gravity: float = 0,
            braking: float = 0,
            lifetime: float = -1,
            once: bool = False,
            size_over_lifetime: bool = False,
            active: bool = False
    ):
        self.max_particles = max_particles
        self.spawn_box = spawn_box
        self.boundary_box = boundary_box
        self.vel = vel
        self.spread = spread
        self.color = color
        self.gravity = gravity
        self.size = size
        self.braking = braking
        self.lifetime = lifetime
        self.once = once
        self.size_over_lifetime = size_over_lifetime
        self.active = active
        self.particles: list[Particle] = []

    def activate(self):
        self.active = True

    def deactivate(self):
        self.active = False

    def generate_particle(self):
        pos = (
            self.spawn_box[0] + self.spawn_box[2] * random.random(),
            self.spawn_box[1] + self.spawn_box[3] * random.random()
        )
        vel = (
            self.vel[0] + self.spread[0] * random.random(),
            self.vel[1] + self.spread[1] * random.random(),
        )

        self.particles.append(Particle(
            pos=pos,
            vel=vel,
            size=self.size,
            gravity=self.gravity,
            braking=self.braking,
            lifetime=self.lifetime,
        ))

    def check_boundary(self, pos: tuple[float, float]) -> bool:
        in_bounds = True
        if not self.boundary_box:
            return in_bounds
        if not(self.boundary_box[0] < pos[0] < (self.boundary_box[0] + self.boundary_box[2])):
            in_bounds = False
        if not(self.boundary_box[1] < pos[1] < (self.boundary_box[1] + self.boundary_box[3])):
            in_bounds = False
        return in_bounds

    def update(self, dt):
        if len(self.particles) < self.max_particles and self.active:
            if self.once:
                for i in range(self.max_particles-len(self.particles)):
                    self.generate_particle()
                    self.deactivate()
            else:
                self.generate_particle()

        for particle in self.particles:
            # check if lifetimes matter
            if self.lifetime > 0:
                particle.lifetime -= dt
                if particle.lifetime <= 0:
                    particle.lifetime = 0
                    if self.once:
                        particle.dead = True
                    else:
                        self.reset_particle(particle)

            if not particle.dead:
                if self.check_boundary(particle.pos):
                    particle.move(dt)
                else:
                    self.reset_particle(particle)

        #alive_particles = filter(lambda dead: not dead, self.particles)
        #self.particles = list(alive_particles)
        self.particles = [particle for particle in self.particles if particle.dead is not True]

    def reset_particle(self, particle):
        if not self.active:
            particle.dead = True
            return
        # move particle to new spawn and reset its values
        particle.pos = (
            self.spawn_box[0] + self.spawn_box[2] * random.random(),
            self.spawn_box[1] + self.spawn_box[3] * random.random()
        )
        particle.vel = (
            self.vel[0] + self.spread[0] * random.random(),
            self.vel[1] + self.spread[1] * random.random(),
        )
        particle.lifetime = self.lifetime

    def draw(self, screen):
        for particle in self.particles:
            if particle.dead:
                continue
            size = particle.size
            if self.size_over_lifetime:
                size = particle.lifetime/self.lifetime * particle.size
            pygame.draw.circle(screen, self.color, particle.pos, size)
'''

class Inwards_Particle_System(ParticleSystem):
    def __init__(
            self,
            max_particles,
            spawn_box,
            color,
            size=None,
            lifetime=None,
            active=False,
            center=None,
    ):
        super().__init__(
            max_particles,
            spawn_box=spawn_box,
            size=size,
            lifetime=lifetime,
            color=color,
            active=active,
        )
        self.center = (
            (center[0] + spawn_box[0], center[1] + spawn_box[1])
            if center
            else (
                self.spawn_box[0] + self.spawn_box[2] / 2,
                self.spawn_box[1] + self.spawn_box[3] / 2,
            )
        )

    def generate_particle(self):
        x, y = (
            random.random() * self.spawn_box[2] + self.spawn_box[0],
            random.random() * self.spawn_box[3] + self.spawn_box[1],
        )
        speed = ((self.center[0] - x) / 10, (self.center[1] - y) / 10)
        self.particles.append(
            Particle(x, y, self.lifetime, self.color, speed, self.size)
        )

    def check_boundaries(self, particle):
        if particle.x - self.center[0] < 10:
            if particle.y - self.center[1] < 10:
                return False
        return True

    def update(self, dt):
        if not self.active:
            return
        if self.particle_counter < self.max_particles and self.active:
            if self.once:
                while (
                        self.particle_counter < self.max_particles and self.active
                ):
                    self.generate_particle()
            else:
                self.generate_particle()
        for particle in self.particles:
            if self.check_boundaries(particle):
                particle.move(dt)
            else:
                if self.despawn_animation:
                    self.despawn_animation(
                        self.despawn_images, 100, (particle.x, particle.y)
                    )
                self.particles.remove(particle)
        if len(self.particles) <= 0 and self.once:
            self.active = False
        self.particles = [
            particle for particle in self.particles if particle.active == True
        ]
        if not self.once:
            self.particle_counter = len(self.particles)
'''