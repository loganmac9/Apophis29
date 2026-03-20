import pygame
import math


class Visual:
    """
    Simple 2D visualization of Earth's elliptical orbit around the Sun.
    Uses the radii and velocities arrays from VisVivaEarth to animate the orbit.
    """

    def __init__(self, radii, velocities, semi_major_axis):
        self.radii = radii
        self.velocities = velocities
        self.semi_major_axis = semi_major_axis

        # Pygame setup
        pygame.init()
        self.width = 1200
        self.height = 800
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Earth's Orbit Visualization")

        # Colors
        self.BLACK = (0, 0, 0)
        self.YELLOW = (255, 255, 0)
        self.GREEN = (0, 255, 0)
        self.WHITE = (255, 255, 255)

        # Sun position (offset from center to show ellipse)
        self.sun_x = self.width // 2 - 100
        self.sun_y = self.height // 2

        # Scale factor to fit orbit on screen (km to pixels)
        self.scale = 400 / self.semi_major_axis  # 400 pixels for semi-major axis

        # Animation state
        self.current_index = 0
        self.going_forward = True
        self.clock = pygame.time.Clock()

    def run(self):
        """Main animation loop"""
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Clearing screen
            self.screen.fill(self.BLACK)

            # Drawing Sun
            pygame.draw.circle(self.screen, self.YELLOW, (self.sun_x, self.sun_y), 30)

            # Drawing orbit path (ellipse outline)
            self.draw_orbit_path()

            # Get the current position
            angle = self.get_angle_for_index(self.current_index)
            radius = self.radii[self.current_index]
            velocity = self.velocities[self.current_index]

            # Calculate Earth's position
            earth_x = self.sun_x + int(radius * self.scale * math.cos(angle))
            earth_y = self.sun_y + int(radius * self.scale * math.sin(angle))

            # Drawing  Earth
            pygame.draw.circle(self.screen, self.GREEN, (earth_x, earth_y), 15)

            # Displaying info
            self.display_info(radius, velocity)

            # Update display
            pygame.display.flip()

            # Update index based on direction
            if self.going_forward:
                self.current_index += 1
                if self.current_index >= len(self.radii):
                    self.current_index = len(self.radii) - 2
                    self.going_forward = False
            else:
                self.current_index -= 1
                if self.current_index < 0:
                    self.current_index = 1
                    self.going_forward = True

            # Frame rate based on velocity (higher velocity = faster animation)
            # Scaling velocity to reasonable frame rate (30-120 fps range)
            fps = 60  # Base frame rate
            self.clock.tick(fps)

        pygame.quit()

    def get_angle_for_index(self, index):
        """Calculate angle based on position in orbit"""
        if self.going_forward:
            # From perihelion (0°) to aphelion (180°)
            return math.pi * (index / (len(self.radii) - 1))
        else:
            # From aphelion (180°) back to perihelion (360°/0°)
            return math.pi + math.pi * (1 - index / (len(self.radii) - 1))

    def draw_orbit_path(self):
        """Draw the elliptical orbit path"""
        points = []
        for i in range(len(self.radii)):
            angle = math.pi * (i / (len(self.radii) - 1))
            radius = self.radii[i]
            x = self.sun_x + int(radius * self.scale * math.cos(angle))
            y = self.sun_y + int(radius * self.scale * math.sin(angle))
            points.append((x, y))

        # Complete the ellipse by mirroring points
        for i in range(len(self.radii) - 2, -1, -1):
            angle = math.pi + math.pi * (1 - i / (len(self.radii) - 1))
            radius = self.radii[i]
            x = self.sun_x + int(radius * self.scale * math.cos(angle))
            y = self.sun_y + int(radius * self.scale * math.sin(angle))
            points.append((x, y))

        if len(points) > 2:
            pygame.draw.lines(self.screen, self.WHITE, True, points, 1)

    def display_info(self, radius, velocity):
        """Display current orbital parameters"""
        font = pygame.font.Font(None, 24)

        radius_text = font.render(f"Radius: {radius / 1e6:.3f} million km", True, self.WHITE)
        velocity_text = font.render(f"Velocity: {velocity / 1000:.3f} km/s", True, self.WHITE)

        self.screen.blit(radius_text, (10, 10))
        self.screen.blit(velocity_text, (10, 35))

# Example usage:
# Assuming you have a VisVivaEarth instance called 'earth'
# earth.getVelocity()  # This populates radii and velocities
# viz = OrbitalVisualization(earth.radii, earth.velocities, earth.semiMajorAxis)
# viz.run()