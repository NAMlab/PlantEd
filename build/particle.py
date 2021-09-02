import pygame, random
from pygame.locals import *
import numpy as np
from pygame import Rect


class Particle:
    def __init__(self, x, y, lifetime=None, color=(0, 0, 0), speed=[0.0, 0.0], size=10, image=None,
                 apply_gravity=False):
        self.speed = speed
        self.image = image
        self.x = x
        self.y = y
        self.lifetime = lifetime
        self.color = color
        self.apply_gravity = apply_gravity
        self.size = size
        self.active = True

    def move(self, dt):
        self.x += self.speed[0] * dt * 60
        self.y += self.speed[1] * dt * 60
        if self.apply_gravity:
            self.speed[1] = self.speed[1] + 0.1
            if abs(self.speed[0]) > 0:
                self.speed[0] = self.speed[0] - 0.2 * self.speed[0] / abs(self.speed[0])
            else:
                self.speed[0] = 0
        if self.lifetime:
            delta = self.lifetime - 0.2
            if delta > 0:
                self.lifetime = delta
            else:
                self.lifetime = 0
                self.active = False


class PointsParticle(Particle):
    def __init__(self, image, points, speed):
        super().__init__(x=points[0][0], y=points[0][1], image=image, speed=speed)
        self.points = points
        self.index = 0
        self.direction = [0, 0]

    def move(self, dt):
        # calculate movement from current to next point
        if not self.active:
            return
        if self.index + 1 >= len(self.points):
            self.index = 0
            self.x, self.y = self.points[self.index]
        x_dist = (self.points[self.index + 1][0] - self.points[self.index][0])
        self.direction[0] = x_dist / abs(x_dist) if x_dist != 0 else 0
        y_dist = (self.points[self.index + 1][1] - self.points[self.index][1])
        self.direction[1] = y_dist / abs(y_dist) if y_dist != 0 else 0
        self.x += self.direction[0] * self.speed[0] * dt * 40
        self.y += self.direction[1] * self.speed[0] * dt * 40
        # check if point reached
        if self.direction[0] < 0 and self.x < self.points[self.index + 1][0] or self.direction[0] > 0 and self.x > \
                self.points[self.index + 1][0]:
            self.index += 1
        elif self.direction[1] < 0 and self.y < self.points[self.index + 1][1] or self.direction[1] > 0 and self.y > \
                self.points[self.index + 1][1]:
            self.index += 1


class ParticleSystem:
    def __init__(self, max_particles, spawn_box=Rect(0, 0, 0, 0), boundary_box=None, color=(0, 0, 0),
                 direction=None, size=10, lifetime=None, apply_gravity=False, speed=None, size_over_lifetime=True,
                 images=[], despawn_images=[], despawn_animation=None, spread=None, once=False, active=True):
        if speed is None:
            speed = [0.0, 0.0]
        self.apply_gravity = apply_gravity
        self.size_over_lifetime = size_over_lifetime
        self.boundary_box = boundary_box if not None else Rect(0, 0, 0, 0)
        self.lifetime = lifetime
        self.spread = spread
        self.images = images
        self.despawn_images = despawn_images
        self.particles = 0
        self.size = size
        self.once = once
        self.speed = speed
        self.max_particles = max_particles
        self.spawn_box = spawn_box
        self.color = color
        self.active = active
        self.particles = []
        self.despawn_animation = despawn_animation
        self.direction = direction
        self.particle_counter = 0

    def update(self, dt):
        if self.particle_counter < self.max_particles and self.active:
            if self.once:
                while (self.particle_counter < self.max_particles and self.active):
                    self.generate_particle()
            else:
                self.generate_particle()
        for particle in self.particles:
            if self.check_boundaries(particle):
                particle.move(dt)
            else:
                if self.despawn_animation:
                    self.despawn_animation(self.despawn_images, 100, (particle.x, particle.y))
                self.particles.remove(particle)
        self.particles = [particle for particle in self.particles if particle.active == True]
        if not self.once:
            self.particle_counter = len(self.particles)

    def generate_particle(self):
        x, y = self.calc_spawn()
        image = None
        if self.images:
            image = self.images[random.randint(0, len(self.images) - 1)]
        speed = self.speed.copy()
        if speed[1] != 0:
            speed[1] = speed[1] + (random.randint(0, 20) - 10) / 10
        if self.spread:
            if self.spread[0] > 0:
                speed[0] = (speed[0] + ((random.randint(0, 20) - 10) / 10) * self.spread[0])
            if self.spread[1] > 0:
                speed[1] = (speed[1] + ((random.randint(0, 20) - 10) / 10) * self.spread[1])

        self.particles.append(
            Particle(x, y, color=self.color, image=image, speed=speed, size=self.size, apply_gravity=self.apply_gravity,
                     lifetime=self.lifetime))
        self.particle_counter += 1

    def check_boundaries(self, particle):
        if self.boundary_box:
            # if self.boundary_box.collidepoint(particle.x, particle.y):
            if particle.y < self.boundary_box[1] + self.boundary_box[3] + random.randint(0, 100) - 50:
                return True
            else:
                return False
        else:
            return True

    def calc_spawn(self):
        x = random.randint(self.spawn_box[0], self.spawn_box[0] + self.spawn_box[2])
        y = random.randint(self.spawn_box[1], self.spawn_box[1] + self.spawn_box[3])
        return x, y

    def deactivate(self):
        self.particle_counter = 0
        self.active = False
        self.particles.clear()

    def activate(self):
        if self.once:
            self.particle_counter = 0
            self.particles.clear()
        self.active = True

    def draw(self, screen):
        for particle in self.particles:
            if particle.image:
                screen.blit(particle.image, (particle.x, particle.y))
            else:
                if particle.lifetime != None and self.size_over_lifetime:
                    size = particle.lifetime
                else:
                    size = particle.size
                pygame.draw.circle(screen, particle.color, (particle.x, particle.y), size)


class PointParticleSystem(ParticleSystem):
    def __init__(self, points, max_particles, images, speed, active=True, callback=None):
        super().__init__(max_particles, images=images, speed=speed, active=active)
        self.points = points
        self.callback = callback

    def change_points(self, points):
        self.points = points

    def set_max_particles(self, max_particles):
        if max_particles < self.max_particles:
            self.particles.clear()
        self.max_particles = max_particles

    def update(self, dt):
        if self.callback:
            self.set_max_particles(int(self.callback()))
        if self.particle_counter < self.max_particles and random.randint(0, 10) < 1 and self.active:
            self.particle_counter += 1
            self.particles.append(PointsParticle(points=self.points, image=self.images[0], speed=self.speed))
        for particle in self.particles:
            if particle.active:
                particle.move(dt)



class StillParticles(ParticleSystem):
    '''
    _(self, max_particles, spawn_box=Rect(0, 0, 0, 0), boundary_box=None, color=(0, 0, 0),
                 direction=None, size=10, lifetime=None, apply_gravity=False, speed=None,
                 images=[], despawn_images=[], despawn_animation=None, spread=None, once=False, active=True):
    '''

    def __init__(self, max_particles, spawn_box, boundary_box, color, speed, size, once, active=True, callback=None):
        super().__init__(max_particles, spawn_box, boundary_box, color, speed=speed, size=size, once=once,
                         active=active)
        self.callback = callback

    def update(self, dt):
        if self.callback:
            self.max_particles = int(self.callback()*1000) #max 0.0012/0.05
        while self.max_particles > len(self.particles):
            self.generate_particle()
        while self.max_particles < len(self.particles) and len(self.particles) > 0:
            self.destroy_particle()

    def destroy_particle(self):
        self.particles.pop(0)

    def generate_particle(self):
        self.color = (random.randint(0,100), self.color[1], random.randint(50, 200))
        x, y = self.calc_spawn()
        image = None
        if self.images:
            image = self.images[random.randint(0, len(self.images) - 1)]
        speed = self.speed.copy()
        if speed[1] != 0:
            speed[1] = speed[1] + (random.randint(0, 20) - 10) / 10
        if self.spread:
            if self.spread[0] > 0:
                speed[0] = (speed[0] + ((random.randint(0, 20) - 10) / 10) * self.spread[0])
            if self.spread[1] > 0:
                speed[1] = (speed[1] + ((random.randint(0, 20) - 10) / 10) * self.spread[1])

        self.particles.append(
            Particle(x, y, color=self.color, image=image, speed=speed, size=self.size, apply_gravity=self.apply_gravity,
                     lifetime=self.lifetime))
        self.particle_counter += 1