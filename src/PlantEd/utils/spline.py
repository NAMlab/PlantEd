import random
from typing import List, Tuple
from scipy.interpolate import CubicSpline
from scipy.special import comb
import pygame
import math
from pygame.locals import *
import numpy as np

from PlantEd import config
from PlantEd.utils.gametime import GameTime




class Cubic_Tree:
    def __init__(self, branches, camera):
        self.branches = branches
        self.camera = camera
        self.branches[0].main = True

    def grow_main(self):
        self.branches[0].grow()

    def grow_all(self):
        for branch in self.branches:
            branch.grow()

    def get_free_spots(self):
        spots = 0
        for branch in self.branches:
            for free_spot in branch.free_spots:
                if free_spot == config.FREE_SPOT:
                    spots += 1
        return spots


    def get_spots(self):
        spots = []
        for branch in self.branches:
            for free_spot in branch.free_spots:
                spots.append(free_spot)
        return spots


    def add_branch(self, highlight, mouse_pos):
        point = highlight[0]
        # left
        if mouse_pos[0] - point[0] < 0:
            points = [
                point,
                [point[0] - 50, point[1] - 20],
                [point[0] - 100, point[1] - 100],
            ]
        else:
            points = [
                point,
                [point[0] + 50, point[1] - 20],
                [point[0] + 100, point[1] - 100],
            ]
        self.branches[0].free_spots[highlight[2]] = config.BRANCH_SPOT
        self.branches.append(Cubic(points))

    def handle_event(self, e):
        for branch in self.branches:
            branch.handle_event(e, self.camera.offset_y)

    def update(self, dt):
        for branch in self.branches:
            branch.update(dt)

    def find_closest(self, pos, free_spots_only=False, without_top=False):
        closest_point = [1000, 1000]
        min_dist = 1000
        shortest_point_id = 0
        branch_id = 0
        for i in range(len(self.branches)):
            point, dist, point_id = self.branches[i].find_closest(
                pos, free_spots_only, without_top
            )
            if dist < min_dist:
                min_dist = dist
                closest_point = point
                shortest_point_id = point_id
                branch_id = i
        return (
            closest_point,
            branch_id,
            shortest_point_id,
        )  # point, branch_id, point_id

    def draw(self, screen, highlighted=False):
        # self.branches[0].draw(screen, tapering=True)
        for i in range(0, len(self.branches)):
            self.branches[i].draw(screen, highlighted)

    def get_rects(self):
        rects = []
        for branch in self.branches:
            branch_rects = branch.get_rects()
            for rect in branch_rects:
                rects.append(rect)
        return rects

    def toggle_move(self):
        for branch in self.branches:
            branch.move_offset = not branch.move_offset


class Cubic:
    def __init__(self, points, color=config.GREEN, res=10, width=15):
        self.points = points
        self.offsets = self.points.copy()
        self.main = False
        self.gametime = GameTime.instance()
        self.timer = 0
        # self.free_points = self.points # points, that can be built on
        self.free_spots = [config.FREE_SPOT for i in range(len(points))]
        self.free_spots[0] = config.BASE_SPOT
        self.color = color
        self.res = res
        self.width = width

        self.move_offset = True
        self.drag = False
        self.id = 0

        self.selected = False
        self.curve = self.get_curve()
        self.new_curve = []
        self.interpolated = []
        self.growth_percentage = 1
        # print(self.curve)

    def get_curve(self):
        points = np.array(self.points)
        y = np.flip(points[:, 0])
        x = np.flip(points[:, 1])
        # use bc_type = 'natural' adds the constraints as we described above
        f = CubicSpline(x, y, bc_type="natural")
        x_new = np.linspace(x[0], x[-1], self.res + len(points) * 10)
        y_new = f(x_new)
        return list(zip(y_new, x_new))

    def grow(self, point=None):
        if not point:
            point = [
                self.points[-1][0] + random.randint(0, 80) - 40,
                self.points[-1][1] - 50,
            ]
        self.points.append(point)
        self.offsets = self.points.copy()
        self.free_spots.append(config.FREE_SPOT)
        self.new_curve = self.get_curve()
        self.growth_percentage = 0
        self.move_offset = False

    def get_rects(self):
        rects = []
        for point in self.curve:
            rects.append(pygame.Rect(point[0] - 10, point[1] - 10, 20, 20))
        return rects

    def enable_offset(self):
        self.move_offset = True

    def diable_offset(self):
        self.move_offset = False

    def update(self, dt):
        if self.growth_percentage < 1:
            self.interpolated = []
            for i in range(len(self.curve)):
                x = (
                    self.new_curve[i + 1][0] - self.curve[i][0]
                ) * self.growth_percentage + self.curve[i][0]
                y = (
                    self.new_curve[i + 1][1] - self.curve[i][1]
                ) * self.growth_percentage + self.curve[i][1]
                self.interpolated.append((x, y))
                self.growth_percentage += dt / 50
            self.interpolated.append(self.curve[-1])
        else:
            self.growth_percentage = 1
            self.curve = self.get_curve()
            self.new_curve = []
            self.move_offset = True

    def handle_event(self, e, offset_y):
        pos = pygame.mouse.get_pos()
        pos = (pos[0], pos[1] - offset_y)
        if self.move_offset:
            point, min_dist, id = self.find_closest(pos)
            if min_dist <= 15:
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if not self.selected:
                        self.timer = self.gametime.get_time()
                        self.selected = True
                    self.id = id
                    self.drag = True
        if e.type == pygame.MOUSEMOTION and self.drag:
            point, min_dist, self.id = self.find_closest(pos)
            if self.check_offset_bounds(self.id, pos):
                self.points[self.id] = pos
                self.curve = self.get_curve()
            if min_dist > 15:
                self.selected = False
        if e.type == pygame.MOUSEBUTTONUP and self.drag:
            self.drag = False
            deltatime = self.gametime.get_time() - self.timer
            if deltatime > 24000:
                self.selected = False
            if self.selected:
                pass

    def check_offset_bounds(self, id, pos):
        y_upper = self.get_upper(id)
        y_lower = self.get_lower(id)
        if y_upper:
            print(pos[1], y_upper[1])
            if pos[1] < y_upper[1] + 10:
                return False
        if y_lower:
            if pos[1] > y_lower[1] - 10:
                return False
        else:
            if self.main:
                return False

        x_dist = (
            self.points[id][0]
            - self.offsets[id][0]
            + pos[0]
            - self.points[id][0]
        )
        y_dist = (
            self.points[id][1]
            - self.offsets[id][1]
            + pos[1]
            - self.points[id][1]
        )

        dist = math.sqrt(x_dist * x_dist + y_dist * y_dist)
        if dist > 70:
            return False
        return True

    def get_upper(self, id):
        if id + 1 >= len(self.points):
            return None
        else:
            return self.points[id + 1]

    def get_lower(self, id):
        if id <= 0:
            return None
        else:
            return self.points[id - 1]

    def draw(self, screen, highlighted):
        if self.drag:
            pygame.draw.circle(
                screen, config.WHITE, self.offsets[self.id], 80, 2
            )
        if self.growth_percentage < 1:
            points = self.interpolated
        else:
            points = self.curve
        if self.move_offset:
            for point in self.points:
                pygame.draw.circle(screen, config.WHITE, point, 15, 2)
        self.draw_tapering(screen, points, highlighted)

    def draw_tapering(self, screen, points, highlighted):
        length = np.shape(points)[0]
        half = length / 2
        for i in range(1, length):
            tapering = 0
            if i < half:
                tapering = self.width / half
            if highlighted:
                pygame.draw.line(
                    screen,
                    config.WHITE,
                    (points[i - 1][0] + 1, points[i - 1][1]),
                    points[i],
                    width=int(self.width + 4 - (half - i) * tapering),
                )
            pygame.draw.line(
                screen,
                self.color,
                (points[i - 1][0] + 0, points[i - 1][1]),
                points[i],
                width=int(self.width - (half - i) * tapering),
            )
            pygame.draw.line(
                screen,
                self.color,
                (points[i - 1][0] + 1, points[i - 1][1]),
                points[i],
                width=int(self.width - (half - i) * tapering),
            )

    def find_closest(self, pos, free_spots_only=False, without_top=False):
        min_dist = 10000
        point = self.points[0]
        id = 0
        for i in range(len(self.points)):
            dist_x = pos[0] - self.points[i][0]
            dist_y = pos[1] - self.points[i][1]
            dist = math.sqrt(dist_x * dist_x + dist_y * dist_y)
            if dist < min_dist:
                if free_spots_only and self.free_spots[i] is not config.FREE_SPOT:
                    continue
                if without_top and i == len(self.points) - 1:
                    continue
                id = i
                min_dist = dist
                point = self.points[i]
        return point, min_dist, id


class Beziere:
    def __init__(
        self,
        list_of_points: List[Tuple[float, float]],
        color=config.GREEN,
        res=100,
        width=10,
    ):
        """
        list_of_points: Control points in the xy plane on which to interpolate. These
            points control the behavior (shape) of the Bezier curve.
        """
        self.list_of_points = list_of_points
        self.offsets = [(0, 0) for point in self.list_of_points]
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
        self.spring_constant = 10  # m/s^2
        self.forces = []
        self.velocities = [
            (0, 0) for point in self.list_of_points
        ]  # resulting v from N|m/s^2
        self.offsets = [
            (0, 0) for point in self.list_of_points
        ]  # resulting x/y from v|m/s

        # final list of points to be drawn
        self.points_to_draw = []
        self.get_current_points_to_draw()
        # self.update(0)

    def basis_function(
        self, t: float, list_of_points: List[Tuple[float, float]], degree: int
    ):
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
                comb(degree, i) * ((1 - t) ** (degree - i)) * (t**i)
            )
        # the basis must sum up to 1 for it to produce a valid Bezier curve.
        # assert round(sum(output_values), 5) == 1
        return output_values

    def bezier_curve_function(
        self, t: float, list_of_points: List[Tuple[float, float]], degree: int
    ) -> Tuple[float, float]:
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
        return (x, y)

    def list_at_resolution(
        self, list_of_points: List[Tuple[float, float]], degree: int
    ):
        """
        This function gets x and y of bezier_curve_function at all resolution points
        To conform with basis_function and bezier_curve_function 0 <= t <= 1
        Return: list of points at the given resolution
        """
        points = []

        for i in range(0, self.resolution + 1):
            t = i / self.resolution
            assert 0 <= t <= 1, "Time t must be between 0 and 1."
            points.append(
                self.bezier_curve_function(t, list_of_points, degree)
            )
        return points

    # add dt
    def update(self, dt):
        if self.growth_percentage < 1.0:
            self.growth_percentage += 0.01
            # point added to grow into
            self.get_current_points_to_draw()
        else:
            self.growth_percentage = 1
        # self.apply_forces(dt)

    def update_tip(self, id=-1, sunpos=(0, 0)):
        # x,y = self.list_of_points[-1]

        # direction
        # length

        if sunpos[0] != 0:
            target_x, target_y = sunpos

            dist = math.sqrt(
                (self.list_of_points[-2][0] - self.list_of_points[-1][0]) ** 2
                + (self.list_of_points[-2][1] - self.list_of_points[-1][1])
                ** 2
            )

            x = math.sin(dist) * (target_x - self.list_of_points[-2][0])
            y = math.cos(dist) * (target_y - self.list_of_points[-2][1])

            # self.list_of_points[-1] = point
            self.get_current_points_to_draw()

    def find_closest(self, pos):
        min_dist = 10000
        t = 0
        for i in range(1, len(self.points_to_draw)):
            dist_x = pos[0] - self.points_to_draw[i][0]
            dist_y = pos[1] - self.points_to_draw[i][1]
            dist = math.sqrt(dist_x * dist_x + dist_y * dist_y)
            if dist < min_dist:
                min_dist = dist
                t = i / len(self.points_to_draw)
        return t

    def get_rects(self, width=5, offset_y=0):
        rects = []
        for point in self.points_to_draw:
            rects.append(
                pygame.Rect(
                    point[0] - width / 2,
                    point[1] - width / 2 + offset_y,
                    width,
                    width,
                )
            )
        return rects

    def apply_forces(self, dt):
        # initialise offsets, maybe stupid in case of growth --> growth should append offset
        # if len(self.offsets) < len(self.points_to_draw):
        #    for i in range(0,len(self.points_to_draw)):
        #        self.offsets.append((0,0))
        # apply all forces on each control point, incorporate mass and therefore inertia
        # gets called 60 times a second
        # for force in self.forces:
        #    for i in range (0,len(self.points_to_draw)):
        #        height_multiplicator = 1 - point[1]/SCREEN_HEIGHT #multiplies string_constant
        #        resulting_force = offset[i][0] -  #string_constant + currentforce
        #        self.velocities.append()

        spring_constant = 1

        # F = m * a
        for i in range(0, len(self.list_of_points)):
            # current spring_force
            elongation_x = (
                -self.offsets[i][0]
                if len(self.offsets) >= len(self.list_of_points)
                else 0
            )
            elongation_y = (
                -self.offsets[i][1]
                if len(self.offsets) >= len(self.list_of_points)
                else 0
            )

            # get the current spring force
            spring_force = (
                spring_constant * elongation_x,
                spring_constant * elongation_y,
            )
            sum_forces_x = spring_force[0]
            sum_forces_y = spring_force[1]

            # sum forces
            for force in self.forces:
                sum_forces_x += force[0]
                sum_forces_y += force[1]

            # for i in range(0,len(self.list_of_points)):
            height_multiplicator = (
                1 - self.list_of_points[i][1] / config.SCREEN_HEIGHT
            )  # used as mass
            # calculate a to get v over dt to get x,y
            a_x = sum_forces_x / height_multiplicator
            a_y = sum_forces_y / height_multiplicator

            velocity_x, velocity_y = self.velocities[i]
            updated_velocity_x = (velocity_x + (a_x * dt / 10)) * 0.99
            updated_velocity_y = (velocity_y + (a_y * dt / 10)) * 0.99
            self.velocities[i] = (updated_velocity_x, updated_velocity_y)

            self.offsets[i] = (
                updated_velocity_x * dt / 10,
                updated_velocity_y * dt / 10,
            )

    def get_point(self, t):
        # self, t: float, list_of_points: List[Tuple[float, float]], degree: int) -> Tuple[float, float]:
        if self.growth_percentage < 1.0:
            old_point = self.bezier_curve_function(
                t, self.last_point_list, len(self.last_point_list) - 1
            )
            new_point = self.bezier_curve_function(
                t, self.list_of_points, self.degree
            )
            x = (
                new_point[0] - old_point[0]
            ) * self.growth_percentage + old_point[0]
            y = (
                new_point[1] - old_point[1]
            ) * self.growth_percentage + old_point[1]
        else:
            return self.bezier_curve_function(
                t, self.list_of_points, self.degree
            )
        return (x, y)

    def get_current_points_to_draw(self):
        if self.growth_percentage < 1.0:
            old_points = self.list_at_resolution(
                self.last_point_list, len(self.last_point_list) - 1
            )
            new_points = self.list_at_resolution(
                self.list_of_points, self.degree
            )
            # draw new points
            # pygame.draw.lines(screen, (255, 255, 255), False, new_points)

            interpolated_points = []
            for i in range(0, len(old_points)):
                x = (
                    new_points[i][0] - old_points[i][0]
                ) * self.growth_percentage + old_points[i][0]
                y = (
                    new_points[i][1] - old_points[i][1]
                ) * self.growth_percentage + old_points[i][1]
                interpolated_points.append((x, y))
            # pygame.draw.lines(screen, (0,255,0), False, interpolated_points, 5)
            self.points_to_draw = interpolated_points
        else:
            # old_points = self.list_at_resolution(self.list_of_points, self.degree)
            self.points_to_draw = self.list_at_resolution(
                self.list_of_points, self.degree
            )

    def apply_force(self, force):
        # two-dimensional force may be added to apply at every control point
        # unsure if forces should be applied at interpolated points
        self.forces.append(force)

    def handle_event(self, e):
        """if e.type == KEYDOWN and e.key == K_PLUS:
            self.forces.append((10, 0))
        if e.type == KEYDOWN and e.key == K_MINUS:
            self.forces = []"""
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
        half = len(self.points_to_draw) / 2

        # tapering
        for i in range(1, len(self.points_to_draw)):
            tapering = 0
            if i > half:
                tapering = self.width / half
            pygame.draw.line(
                screen,
                config.WHITE,
                self.points_to_draw[i - 1],
                self.points_to_draw[i],
                width=int(self.width + 2 - (i - half) * tapering),
            )
        self.draw(screen)

    def draw(self, screen):
        # draw should not contain logic, points_to_draw are drawn without further calculation
        # draw list_of_points

        half = len(self.points_to_draw) / 2

        # tapering
        for i in range(1, len(self.points_to_draw)):
            tapering = 0
            if i > half:
                tapering = self.width / half
            # pygame.draw.line(screen, (0,0,0), self.points_to_draw[i-1],self.points_to_draw[i],width=int(self.width-tapering*i))
            pygame.draw.line(
                screen,
                self.color,
                self.points_to_draw[i - 1],
                self.points_to_draw[i],
                width=int(self.width - (i - half) * tapering),
            )
        # pygame.draw.lines(screen, (0,0,0), False, self.points_to_draw, width=7)
        # pygame.draw.lines(screen, config.GREEN, False, self.points_to_draw, width=5)

        # draw control points
        # for i in range (0,len(self.list_of_points)):
        #    #point = (self.list_of_points[i][0]+self.offsets[i][0],self.list_of_points[i][1]+self.offsets[i][1])
        #    point = (self.list_of_points[i][0],self.list_of_points[i][1])
        #    pygame.draw.circle(screen, (255,0,0),point, 5)

        def unit_vector(self, vector):
            return vector / np.linalg.norm(vector)

        def angle_between(self, v1, v2):
            v1_u = self.unit_vector(v1)
            v2_u = self.unit_vector(v2)
            return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))
