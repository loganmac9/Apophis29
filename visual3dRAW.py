print("VISUAL3D LOADED - LATEST VERSION WITH DEBUG")

import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math


class Visual3D:
    """
    3D visualization of orbital systems using PyOpenGL.
    Supports orbital inclination, pan, zoom, and rotation controls.
    Earth moves at calculated orbital velocity.
    """

    def __init__(self, radii, velocities, semi_major_axis, inclination=0.0):
        """
        Initialize 3D visualization

        Args:
            radii: Array of orbital radii (meters)
            velocities: Array of orbital velocities (m/s)
            semi_major_axis: Semi-major axis of orbit (meters)
            inclination: Orbital inclination in degrees
        """
        self.radii = radii
        self.velocities = velocities
        self.semi_major_axis = semi_major_axis
        self.inclination = math.radians(inclination)

        print(f"Initialized with {len(radii)} orbital points")
        print(f"Radii range: {min(radii) / 1e9:.3f} to {max(radii) / 1e9:.3f} billion m")

        # Pygame and OpenGL setup
        pygame.init()
        self.width = 1200
        self.height = 800
        self.screen = pygame.display.set_mode((self.width, self.height), DOUBLEBUF | OPENGL)
        pygame.display.set_caption("3D Orbital Visualization")

        # Setup OpenGL perspective
        self.setup_opengl()

        # Scale factor to normalize orbit size
        self.scale = 2.0 / self.semi_major_axis

        # Camera controls
        self.camera_distance = 5.0
        self.camera_rotation_x = 30.0
        self.camera_rotation_y = 45.0
        self.camera_pan_x = 0.0
        self.camera_pan_y = 0.0

        # Mouse state
        self.mouse_dragging = False
        self.mouse_panning = False
        self.mouse_last_x = 0
        self.mouse_last_y = 0

        # Animation state
        self.current_position = 0.0
        self.going_forward = True
        self.clock = pygame.time.Clock()
        self.time_scale = 1000000.0  # Speed up factor (1 million times real time)

        # Display info
        self.font = pygame.font.Font(None, 24)

    def setup_opengl(self):
        """Configure OpenGL settings"""
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

        glLightfv(GL_LIGHT0, GL_POSITION, (5, 5, 5, 1))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.3, 0.3, 0.3, 1))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.8, 0.8, 0.8, 1))

        glMatrixMode(GL_PROJECTION)
        gluPerspective(45, (self.width / self.height), 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)

    def handle_events(self):
        """Handle mouse and keyboard events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.mouse_dragging = True
                    self.mouse_last_x, self.mouse_last_y = event.pos
                elif event.button == 3:
                    self.mouse_panning = True
                    self.mouse_last_x, self.mouse_last_y = event.pos

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.mouse_dragging = False
                elif event.button == 3:
                    self.mouse_panning = False

            elif event.type == pygame.MOUSEMOTION:
                mouse_x, mouse_y = event.pos
                dx = mouse_x - self.mouse_last_x
                dy = mouse_y - self.mouse_last_y

                if self.mouse_dragging:
                    self.camera_rotation_y += dx * 0.5
                    self.camera_rotation_x += dy * 0.5
                    self.camera_rotation_x = max(-90, min(90, self.camera_rotation_x))

                elif self.mouse_panning:
                    self.camera_pan_x += dx * 0.01
                    self.camera_pan_y -= dy * 0.01

                self.mouse_last_x = mouse_x
                self.mouse_last_y = mouse_y

            elif event.type == pygame.MOUSEWHEEL:
                self.camera_distance -= event.y * 0.5
                self.camera_distance = max(2.0, min(20.0, self.camera_distance))

        return True

    def get_interpolated_values(self, position):
        """Get interpolated radius and velocity at continuous position"""
        position = max(0, min(position, len(self.radii) - 1))
        index_low = int(position)
        index_high = min(index_low + 1, len(self.radii) - 1)
        t = position - index_low

        radius = self.radii[index_low] * (1 - t) + self.radii[index_high] * t
        velocity = self.velocities[index_low] * (1 - t) + self.velocities[index_high] * t

        return radius, velocity

    def calculate_distance_between_points(self, index1, index2):
        """Calculate arc distance between two orbital points"""
        if index1 == index2:
            return 1.0  # Return small positive value to avoid division by zero

        # Ensure indices are valid
        index1 = max(0, min(int(index1), len(self.radii) - 1))
        index2 = max(0, min(int(index2), len(self.radii) - 1))

        angle1 = self.get_angle_for_position(index1)
        angle2 = self.get_angle_for_position(index2)

        r1 = self.radii[index1]
        r2 = self.radii[index2]

        # Calculate 3D positions with inclination
        x1, y1, z1 = self.get_3d_position(r1, angle1)
        x2, y2, z2 = self.get_3d_position(r2, angle2)

        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)

        # Return a minimum distance to prevent division issues
        return max(distance, 0.0001)
        """Get interpolated radius and velocity at continuous position"""
        position = max(0, min(position, len(self.radii) - 1))
        index_low = int(position)
        index_high = min(index_low + 1, len(self.radii) - 1)
        t = position - index_low

        radius = self.radii[index_low] * (1 - t) + self.radii[index_high] * t
        velocity = self.velocities[index_low] * (1 - t) + self.velocities[index_high] * t

        return radius, velocity

    def get_angle_for_position(self, position):
        """Calculate orbital angle for position in the full orbit"""
        max_pos = len(self.radii) - 1

        if max_pos == 0:
            return 0

        normalized = position / max_pos

        if self.going_forward:
            angle = normalized * math.pi
        else:
            angle = math.pi * (2.0 - normalized)

        return angle

    def get_3d_position(self, radius, angle):
        """Convert orbital position to 3D coordinates with inclination"""
        x = radius * math.cos(angle) * self.scale
        y_orbit = radius * math.sin(angle) * self.scale

        y = y_orbit * math.cos(self.inclination)
        z = y_orbit * math.sin(self.inclination)

        return x, y, z

    def draw_sphere(self, radius, slices=20, stacks=20):
        """Draw a sphere using GLU"""
        quad = gluNewQuadric()
        gluSphere(quad, radius, slices, stacks)
        gluDeleteQuadric(quad)

    def draw_sun(self):
        """Draw the Sun at origin"""
        glPushMatrix()
        glColor3f(1.0, 1.0, 0.0)
        self.draw_sphere(0.15)
        glPopMatrix()

    def draw_earth(self, x, y, z):
        """Draw Earth at given position"""
        glPushMatrix()
        glTranslatef(x, y, z)
        glColor3f(0.0, 1.0, 0.0)
        self.draw_sphere(0.08)
        glPopMatrix()

    def draw_orbit_path(self):
        """Draw the orbital path as a line"""
        glDisable(GL_LIGHTING)
        glColor3f(1.0, 1.0, 1.0)
        glLineWidth(1.0)

        glBegin(GL_LINE_LOOP)

        for i in range(len(self.radii)):
            angle = math.pi * (i / (len(self.radii) - 1))
            radius = self.radii[i]
            x, y, z = self.get_3d_position(radius, angle)
            glVertex3f(x, y, z)

        for i in range(len(self.radii) - 2, -1, -1):
            angle = math.pi + math.pi * (1 - i / (len(self.radii) - 1))
            radius = self.radii[i]
            x, y, z = self.get_3d_position(radius, angle)
            glVertex3f(x, y, z)

        glEnd()
        glEnable(GL_LIGHTING)

    def draw_reference_plane(self):
        """Draw a reference grid plane"""
        glDisable(GL_LIGHTING)
        glColor3f(0.2, 0.2, 0.2)
        glLineWidth(1.0)

        size = 3.0
        step = 0.5

        glBegin(GL_LINES)
        x = -size
        while x <= size:
            glVertex3f(x, -size, 0)
            glVertex3f(x, size, 0)
            x += step

        y = -size
        while y <= size:
            glVertex3f(-size, y, 0)
            glVertex3f(size, y, 0)
            y += step

        glEnd()
        glEnable(GL_LIGHTING)

    def setup_camera(self):
        """Setup camera view"""
        glLoadIdentity()
        glTranslatef(self.camera_pan_x, self.camera_pan_y, -self.camera_distance)
        glRotatef(self.camera_rotation_x, 1, 0, 0)
        glRotatef(self.camera_rotation_y, 0, 1, 0)

    def draw_2d_overlay(self, radius, velocity):
        """Draw 2D text overlay on 3D scene"""
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)

        y_offset = self.height - 30

        texts = [
            f"Radius: {radius / 1e6:.3f} million km",
            f"Velocity: {velocity / 1000:.3f} km/s",
            f"Position: {self.current_position:.2f} / {len(self.radii) - 1}",
            f"Direction: {'FORWARD' if self.going_forward else 'BACKWARD'}",
            f"Inclination: {math.degrees(self.inclination):.2f} deg",
            f"Time Scale: {self.time_scale:.0f}x",
            "L-drag: Rotate | R-drag: Pan | Scroll: Zoom"
        ]

        for text in texts:
            text_surface = self.font.render(text, True, (255, 255, 255), (0, 0, 0))
            text_data = pygame.image.tostring(text_surface, "RGBA", True)

            glRasterPos2i(10, y_offset)
            glDrawPixels(text_surface.get_width(), text_surface.get_height(),
                         GL_RGBA, GL_UNSIGNED_BYTE, text_data)
            y_offset -= 25

        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)

        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    def run(self):
        """Main visualization loop"""
        running = True
        fps = 60
        frame_count = 0

        print(f"\nStarting animation loop with physics-based velocity")
        print(f"Time scale: {self.time_scale}x real time")

        while running:
            running = self.handle_events()

            # Calculate time step (in simulated seconds)
            dt = (1.0 / fps) * self.time_scale

            # Get current velocity
            _, current_velocity = self.get_interpolated_values(self.current_position)

            # Calculate distance to travel this frame (in meters)
            distance_to_travel = current_velocity * dt

            # Calculate distance between current and next array position
            current_index = int(self.current_position)
            next_index = min(current_index + 1, len(self.radii) - 1)
            segment_distance = self.calculate_distance_between_points(current_index, next_index)

            # Convert distance to position increment
            # segment_distance is in scaled units, distance_to_travel is in meters
            # We need to scale distance_to_travel by self.scale
            scaled_distance = distance_to_travel * self.scale
            position_increment = scaled_distance / segment_distance

            # Clamp increment to prevent overshooting (max 2.0 positions per frame)
            position_increment = min(position_increment, 2.0)

            # Debug every 30 frames
            if frame_count % 30 == 0:
                print(
                    f"Frame {frame_count}: pos={self.current_position:.2f}, vel={current_velocity / 1000:.2f} km/s, inc={position_increment:.3f}")

            frame_count += 1

            # Update position
            if self.going_forward:
                self.current_position += position_increment
                if self.current_position >= len(self.radii) - 1:
                    self.current_position = len(self.radii) - 1
                    self.going_forward = False
                    print(f"Reached aphelion, switching to BACKWARD")
            else:
                self.current_position -= position_increment
                if self.current_position <= 0:
                    self.current_position = 0
                    self.going_forward = True
                    print(f"Reached perihelion, switching to FORWARD")

            # Rendering
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            self.setup_camera()
            self.draw_reference_plane()
            self.draw_orbit_path()
            self.draw_sun()

            # Draw Earth
            radius, velocity = self.get_interpolated_values(self.current_position)
            angle = self.get_angle_for_position(self.current_position)
            earth_x, earth_y, earth_z = self.get_3d_position(radius, angle)
            self.draw_earth(earth_x, earth_y, earth_z)

            self.draw_2d_overlay(radius, velocity)

            pygame.display.flip()
            self.clock.tick(fps)

        pygame.quit()