import pygame
import math

# Initialize the display
pygame.init()
screen = pygame.display.set_mode((400, 400))

# Define the center of the pentagrams
center = (200, 200)

# Define the radius of the pentagrams
radius = 100

# Define the number of points in the pentagrams
points = 5

# Define the angle between each point in radians
angle = 2 * math.pi / points

# Define the initial angle offset
angle_offset = 0

# Define the angle offset change per frame
angle_offset_delta = 0.05

# Define the line thickness
line_thickness = 10

# Main game loop
running = True
clock = pygame.time.Clock()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear the screen
    screen.fill((0, 0, 0))

    # Draw the first pentagram
    for i in range(points):
        angle_start = i * angle + angle_offset
        x = center[0] + radius * math.cos(angle_start)
        y = center[1] + radius * math.sin(angle_start)
        next_x = center[0] + radius * math.cos(angle_start + angle)
        next_y = center[1] + radius * math.sin(angle_start + angle)
        pygame.draw.line(screen, (255, 0, 0), (x, y), (next_x, next_y), line_thickness)

    # Draw the second pentagram
    for i in range(points):
        angle_start = i * angle
        x = center[0] + radius * 2/3 * math.cos(angle_start)
        y = center[1] + radius * 2/3 * math.sin(angle_start)
        next_x = center[0] + radius * 2/3 * math.cos(angle_start + angle)
        next_y = center[1] + radius * 2/3 * math.sin(angle_start + angle)
        pygame.draw.line(screen, (255, 0, 0), (x, y), (next_x, next_y), line_thickness)

    # Update the angle offset
    angle_offset += angle_offset_delta

    # Update the display
    pygame.display.update()
    clock.tick(60)

# Quit Pygame
pygame.quit()
