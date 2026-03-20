import pygame
import math


class VisualZoom:
    """
    Simple 2D visualization of Earth's elliptical orbit around the Sun.
    Uses the radii and velocities arrays from VisVivaEarth to animate the orbit.
    Supports panning (drag with mouse) and zooming (scroll wheel).
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
        pygame.display.set_caption("Earth's Orbit Visualization - Drag to pan, Scroll to zoom")

        # Colors
        self.BLACK = (0, 0, 0)
        self.YELLOW = (255, 255, 0)
        self.GREEN = (0, 255, 0)
        self.WHITE = (255, 255, 255)

        # Sun position (offset from center to show ellipse)
        self.sun_x = self.width // 2 - 100
        self.sun_y = self.height // 2

        # Scale factor to fit orbit on screen (km to pixels)
        self.base_scale = 400 / self.semi_major_axis  # 400 pixels for semi-major axis

        # Camera controls
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.camera_start_x = 0
        self.camera_start_y = 0

        # Animation state
        self.current_index = 0
        self.going_forward = True
        self.clock = pygame.time.Clock()

    def world_to_screen(self, x, y):
        """Convert world coordinates to screen coordinates with camera offset and zoom"""
        screen_x = (x + self.camera_x) * self.zoom
        screen_y = (y + self.camera_y) * self.zoom
        return int(screen_x), int(screen_y)

    def handle_events(self):
        """Handle mouse and keyboard events for camera control"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            # Mouse button down - start dragging
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button
                    self.dragging = True
                    self.drag_start_x, self.drag_start_y = event.pos
                    self.camera_start_x = self.camera_x
                    self.camera_start_y = self.camera_y

            # Mouse button up - stop dragging
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # Left mouse button
                    self.dragging = False

            # Mouse motion - update camera if dragging
            elif event.type == pygame.MOUSEMOTION:
                if self.dragging:
                    mouse_x, mouse_y = event.pos
                    dx = mouse_x - self.drag_start_x
                    dy = mouse_y - self.drag_start_y
                    self.camera_x = self.camera_start_x + dx / self.zoom
                    self.camera_y = self.camera_start_y + dy / self.zoom

            # Mouse wheel - zoom in/out
            elif event.type == pygame.MOUSEWHEEL:
                # Get mouse position for zoom center
                mouse_x, mouse_y = pygame.mouse.get_pos()

                # Calculate world position before zoom
                world_x_before = (mouse_x / self.zoom) - self.camera_x
                world_y_before = (mouse_y / self.zoom) - self.camera_y

                # Update zoom (wheel.y is positive for scroll up, negative for scroll down)
                zoom_factor = 1.1 if event.y > 0 else 0.9
                self.zoom *= zoom_factor

                # Clamp zoom to reasonable values
                self.zoom = max(0.1, min(self.zoom, 10.0))

                # Calculate world position after zoom
                world_x_after = (mouse_x / self.zoom) - self.camera_x
                world_y_after = (mouse_y / self.zoom) - self.camera_y

                # Adjust camera to keep mouse position stable
                self.camera_x += world_x_after - world_x_before
                self.camera_y += world_y_after - world_y_before

        return True

    def run(self):
        """Main animation loop"""
        running = True

        while running:
            running = self.handle_events()

            # Clear screen
            self.screen.fill(self.BLACK)

            # Draw orbit path (ellipse outline)
            self.draw_orbit_path()

            # Draw Sun
            sun_screen_x, sun_screen_y = self.world_to_screen(self.sun_x, self.sun_y)
            sun_radius = max(5, int(30 * self.zoom))  # Scale sun size with zoom, minimum 5 pixels
            pygame.draw.circle(self.screen, self.YELLOW, (sun_screen_x, sun_screen_y), sun_radius)

            # Get current position
            angle = self.get_angle_for_index(self.current_index)
            radius = self.radii[self.current_index]
            velocity = self.velocities[self.current_index]

            # Calculate Earth position
            earth_x = self.sun_x + int(radius * self.base_scale * math.cos(angle))
            earth_y = self.sun_y + int(radius * self.base_scale * math.sin(angle))

            # Convert to screen coordinates
            earth_screen_x, earth_screen_y = self.world_to_screen(earth_x, earth_y)

            # Draw Earth
            earth_radius = max(3, int(15 * self.zoom))  # Scale earth size with zoom, minimum 3 pixels
            pygame.draw.circle(self.screen, self.GREEN, (earth_screen_x, earth_screen_y), earth_radius)

            # Display info
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

            # Frame rate
            fps = 60
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
            x = self.sun_x + int(radius * self.base_scale * math.cos(angle))
            y = self.sun_y + int(radius * self.base_scale * math.sin(angle))

            # Convert to screen coordinates
            screen_x, screen_y = self.world_to_screen(x, y)
            points.append((screen_x, screen_y))

        # Complete the ellipse by mirroring points
        for i in range(len(self.radii) - 2, -1, -1):
            angle = math.pi + math.pi * (1 - i / (len(self.radii) - 1))
            radius = self.radii[i]
            x = self.sun_x + int(radius * self.base_scale * math.cos(angle))
            y = self.sun_y + int(radius * self.base_scale * math.sin(angle))

            # Convert to screen coordinates
            screen_x, screen_y = self.world_to_screen(x, y)
            points.append((screen_x, screen_y))

        if len(points) > 2:
            pygame.draw.lines(self.screen, self.WHITE, True, points, 1)

    def display_info(self, radius, velocity):
        """Display current orbital parameters and controls info"""
        font = pygame.font.Font(None, 24)

        radius_text = font.render(f"Radius: {radius / 1e6:.3f} million km", True, self.WHITE)
        velocity_text = font.render(f"Velocity: {velocity / 1000:.3f} km/s", True, self.WHITE)
        zoom_text = font.render(f"Zoom: {self.zoom:.2f}x", True, self.WHITE)
        controls_text = font.render("Controls: Drag to pan | Scroll to zoom", True, self.WHITE)

        self.screen.blit(radius_text, (10, 10))
        self.screen.blit(velocity_text, (10, 35))
        self.screen.blit(zoom_text, (10, 60))
        self.screen.blit(controls_text, (10, self.height - 30))

# Example usage:
# Assuming you have a VisVivaEarth instance called 'earth'
# earth.getVelocity()  # This populates radii and velocities
# viz = Visual(earth.radii, earth.velocities, earth.semiMajorAxis)
# viz.run()