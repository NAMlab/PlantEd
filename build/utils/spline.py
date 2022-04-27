from typing import List, Tuple
from scipy.special import comb
from scipy.spatial.distance import pdist
import pygame
import math
from pygame.locals import *
import config

SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080


# basic L-System
# draw first line along direction (20 pix) - A
# draw end of line - B
# turn right +
# turn left -

# Rules for fibroot
# rule 1: B -> AB
# rule 2: A -> A+A

class Beziere:
    def __init__(self, list_of_points: List[Tuple[float, float]], color=config.GREEN, res=100, width=10):
        """
        list_of_points: Control points in the xy plane on which to interpolate. These
            points control the behavior (shape) of the Bezier curve.
        """
        self.list_of_points = list_of_points
        self.offsets = [(0,0) for point in self.list_of_points]
        self.color = color
        self.resolution = res
        self.width = width
        # Degree determines the flexibility of the curve.
        # Degree = 1 will produce a straight line.
        self.degree = len(list_of_points) - 1

        # interpolated animation of growth
        # last list of points copies the current list without the last entry
        self.last_point_list = None
        self.growth_percentage = 1

        # player interaction, interger of pressed point in self.list_of_points
        self.pressed = -1

        # physics
        self.spring_constant = 10 #m/s^2
        self.forces = []
        self.velocities = [(0,0) for point in self.list_of_points] # resulting v from N|m/s^2
        self.offsets = [(0,0) for point in self.list_of_points] # resulting x/y from v|m/s

        #final list of points to be drawn
        self.points_to_draw = []
        self.get_current_points_to_draw()
        #self.update(0)

    def basis_function(self, t: float, list_of_points: List[Tuple[float, float]], degree: int):
        """
        The basis function determines the weight of each control point at time t.
        t: time value between 0 and 1 inclusive at which to evaluate the basis of the curve.
        returns the x, y values of basis function at time t

        #>>> curve = BezierCurve([(1,1), (1,2)])
        #>>> curve.basis_function(0)
        [1.0, 0.0]
        #>>> curve.basis_function(1)
        [0.0, 1.0]
        """
        assert 0 <= t <= 1, "Time t must be between 0 and 1."
        output_values: List[float] = []
        for i in range(len(list_of_points)):
            # basis function for each i
            output_values.append(
                comb(degree, i) * ((1 - t) ** (degree - i)) * (t ** i)
            )
        # the basis must sum up to 1 for it to produce a valid Bezier curve.
        #assert round(sum(output_values), 5) == 1
        return output_values


    def bezier_curve_function(self, t: float, list_of_points: List[Tuple[float, float]], degree: int) -> Tuple[float, float]:
        """
        The function to produce the values of the Bezier curve at time t.
            t: the value of time t at which to evaluate the Bezier function
        Returns the x, y coordinates of the Bezier curve at time t.
            The first point in the curve is when t = 0.
            The last point in the curve is when t = 1.

        #>>> curve = BezierCurve([(1,1), (1,2)])
        #>>> curve.bezier_curve_function(0)
        (1.0, 1.0)
        #>>> curve.bezier_curve_function(1)
        (1.0, 2.0)
        """

        assert 0 <= t <= 1, "Time t must be between 0 and 1."

        basis_function = self.basis_function(t, list_of_points, degree)
        x = 0.0
        y = 0.0
        for i in range(len(list_of_points)):
            # For all points, sum up the product of i-th basis function and i-th point.
            x += basis_function[i] * (list_of_points[i][0])
            y += basis_function[i] * (list_of_points[i][1])
            #print('X: ',x, '  Y: ',y, 'X PRE',basis_function[i],self.list_of_points[i][0], self.offset[i][0])
        return (x, y)

    def list_at_resolution(self, list_of_points: List[Tuple[float, float]], degree: int):
        '''
        This function gets x and y of bezier_curve_function at all resolution points
        To conform with basis_function and bezier_curve_function 0 <= t <= 1
        Return: list of points at the given resolution
        '''
        points = []

        for i in range(0,self.resolution+1):
            t = i / self.resolution
            assert 0 <= t <= 1, "Time t must be between 0 and 1."
            points.append(self.bezier_curve_function(t, list_of_points, degree))
        return points

    #add dt
    def update(self, dt):
        if self.growth_percentage < 1.0:
            self.growth_percentage += 0.01
            #point added to grow into
        else:
            self.growth_percentage = 1
        self.get_current_points_to_draw()
        #self.apply_forces(dt)

    def find_closest(self, pos):
        min_dist = 10000
        t = 0
        for i in range(1,len(self.points_to_draw)):
            dist_x = pos[0] - self.points_to_draw[i][0]
            dist_y = pos[1] - self.points_to_draw[i][1]
            dist = math.sqrt(dist_x*dist_x+dist_y*dist_y)
            if dist < min_dist:
                min_dist = dist
                t = i/len(self.points_to_draw)
        return t

    def get_rects(self, width=5, offset_y=0):
        rects = []
        for point in self.points_to_draw:
            rects.append(pygame.Rect(point[0]-width/2,point[1]-width/2+offset_y,width,width))
        return rects


    def apply_forces(self, dt):
        #initialise offsets, maybe stupid in case of growth --> growth should append offset
        #if len(self.offsets) < len(self.points_to_draw):
        #    for i in range(0,len(self.points_to_draw)):
        #        self.offsets.append((0,0))
        #apply all forces on each control point, incorporate mass and therefore inertia
        #gets called 60 times a second
        #for force in self.forces:
        #    for i in range (0,len(self.points_to_draw)):
        #        height_multiplicator = 1 - point[1]/SCREEN_HEIGHT #multiplies string_constant
        #        resulting_force = offset[i][0] -  #string_constant + currentforce
        #        self.velocities.append()

        spring_constant = 1

        # F = m * a
        for i in range(0, len(self.list_of_points)):
            # current spring_force
            elongation_x = -self.offsets[i][0] if len(self.offsets) >= len(self.list_of_points) else 0
            elongation_y = -self.offsets[i][1] if len(self.offsets) >= len(self.list_of_points) else 0

            # get the current spring force
            spring_force = (spring_constant * elongation_x, spring_constant * elongation_y)
            sum_forces_x = spring_force[0]
            sum_forces_y = spring_force[1]

            # sum forces
            for force in self.forces:
                sum_forces_x += force[0]
                sum_forces_y += force[1]


            #for i in range(0,len(self.list_of_points)):
            height_multiplicator = 1 - self.list_of_points[i][1] / SCREEN_HEIGHT  # used as mass
            # calculate a to get v over dt to get x,y
            a_x = sum_forces_x / height_multiplicator
            a_y = sum_forces_y / height_multiplicator

            velocity_x, velocity_y = self.velocities[i]
            #print(velocity_x, velocity_y)
            updated_velocity_x = (velocity_x + (a_x * dt/10)) * 0.99
            updated_velocity_y = (velocity_y + (a_y * dt/10)) * 0.99
            self.velocities[i] = (updated_velocity_x, updated_velocity_y)

            self.offsets[i] = (updated_velocity_x * dt/10, updated_velocity_y * dt/10)
            #print(velocity_x, velocity_y)
            #print(i, a_x*dt, a_y*dt, velocity_x*dt, velocity_y*dt)

    def get_point(self, t):
        # self, t: float, list_of_points: List[Tuple[float, float]], degree: int) -> Tuple[float, float]:
        if self.growth_percentage < 1.0:
            old_point = self.bezier_curve_function(t, self.last_point_list, len(self.last_point_list)-1)
            new_point = self.bezier_curve_function(t, self.list_of_points, self.degree)
            x = (new_point[0] - old_point[0]) * self.growth_percentage + old_point[0]
            y = (new_point[1] - old_point[1]) * self.growth_percentage + old_point[1]
        else:
            return self.bezier_curve_function(t, self.list_of_points, self.degree)
        return (x,y)

    def get_current_points_to_draw(self):
        if self.growth_percentage < 1.0:
            old_points = self.list_at_resolution(self.last_point_list, len(self.last_point_list)-1)
            new_points = self.list_at_resolution(self.list_of_points, self.degree)
            #draw new points
            #pygame.draw.lines(screen, (255, 255, 255), False, new_points)

            interpolated_points = []
            for i in range(0,len(old_points)):
                x = (new_points[i][0] - old_points[i][0]) * self.growth_percentage + old_points[i][0]
                y = (new_points[i][1] - old_points[i][1]) * self.growth_percentage + old_points[i][1]
                interpolated_points.append((x,y))
            #pygame.draw.lines(screen, (0,255,0), False, interpolated_points, 5)
            self.points_to_draw = interpolated_points
        else:
            #old_points = self.list_at_resolution(self.list_of_points, self.degree)
            self.points_to_draw = self.list_at_resolution(self.list_of_points, self.degree)

    def apply_force(self, force):
        #two-dimensional force may be added to apply at every control point
        #unsure if forces should be applied at interpolated points
        self.forces.append(force)

    def handle_event(self,e):
        if e.type == KEYDOWN and e.key == K_PLUS:
            self.forces.append((10, 0))
        if e.type == KEYDOWN and e.key == K_MINUS:
            self.forces = []
        if e.type == MOUSEMOTION and self.pressed > -1:
            mouse_pos = pygame.mouse.get_pos()
            self.list_of_points[self.pressed] = mouse_pos

        if e.type == MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for i in range(0, len(self.list_of_points)):
                if math.dist(mouse_pos, self.list_of_points[i]) < 10:
                    self.pressed = i

        if e.type == MOUSEBUTTONUP:
            mouse_pos = pygame.mouse.get_pos()
            self.pressed = -1


    def add_point(self, point):
        self.list_of_points.append(point)
        self.resolution += 1
        self.degree += 1

    def grow_point(self, point):
        self.last_point_list = self.list_of_points.copy()
        self.list_of_points.append(point)
        self.resolution += 1
        self.degree += 1
        self.growth_percentage = 0

    def print_points(self):
        print(self.points_to_draw)

    def draw_highlighted(self, screen):
        for i in range(1,len(self.points_to_draw)):
            pygame.draw.line(screen, config.WHITE, self.points_to_draw[i-1],self.points_to_draw[i],width=int(12-0.05*i))
        self.draw(screen)

    def draw(self, screen):
        # draw should not contain logic, points_to_draw are drawn without further calculation
        #draw list_of_points

        # tapering
        for i in range(1,len(self.points_to_draw)):
            pygame.draw.line(screen, (0,0,0), self.points_to_draw[i-1],self.points_to_draw[i],width=int(self.width-0.05*i))
            pygame.draw.line(screen, self.color, self.points_to_draw[i-1],self.points_to_draw[i],width=int((self.width-2)-0.05*i))
        #pygame.draw.lines(screen, (0,0,0), False, self.points_to_draw, width=7)
        #pygame.draw.lines(screen, config.GREEN, False, self.points_to_draw, width=5)

        # draw control points
        for i in range (0,len(self.list_of_points)):
            #point = (self.list_of_points[i][0]+self.offsets[i][0],self.list_of_points[i][1]+self.offsets[i][1])
            point = (self.list_of_points[i][0],self.list_of_points[i][1])
            pygame.draw.circle(screen, (255,0,0),point, 5)