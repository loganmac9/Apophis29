import pygame
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np

class Visualizer:

    def __init__(self, sim_data):
        self.sim_data = sim_data

        # Default colors and sizes for all possible bodies
        DEFAULT_COLORS = {
            "Sun": (1.0, 1.0, 0.0),
            "Earth": (0.0, 0.5, 1.0),
            "Moon": (0.8, 0.8, 0.8),
            "Apophis": (1.0, 0.3, 0.0),
            "Rocket": (0.0, 1.0, 0.0),
        }
        DEFAULT_SIZES = {
            "Sun": 12,
            "Earth": 6,
            "Moon": 3,
            "Apophis": 3,
            "Rocket": 2,
        }

        self.COLORS = {
            name: DEFAULT_COLORS[name]
            for name in sim_data.positions
            if name in DEFAULT_COLORS
        }
        self.SIZES = {
            name: DEFAULT_SIZES[name]
            for name in sim_data.positions
            if name in DEFAULT_SIZES
        }
        # pygame initialization
        pygame.init()

        self.camera_target = 'solar'

        # window (Width, Height).
        # Storing width and height as attributes so other methods can use them
        self.width = 1200
        self.height = 800
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.OPENGL | pygame.DOUBLEBUF)
        pygame.display.set_caption("Asteroid Capture System")

        # Playback state
        # set frame index:
        self.frame_index = 0
        self.playback_speed = 12  # frames to advance per render - Default = 1
        self.paused = False  # pause state

        # Scale factors for coordinate conversion.
        self.scale = 200      # 1 AU = 200 pixels, solar system view
        self.scale_earth = 50000    # zoomed into Earth-Moon system
        self.scale_asteroid = 100000   # zoomed into asteroid + drones
        self.zoom_mode = 'solar'  # current zoom mode

        # Clock Creation for Frame Rate:
        self.clock = pygame.time.Clock()
        # Font for HUD text
        self.font = pygame.font.SysFont('monospace', 16)
        self.FPS = 60

        # Total frames available from simulation
        self.total_frames = len(sim_data.times)

        # Camera rotation state — needed by setup_3d_camera and _handle_mouse
        self.camera_angle_x = 30.0  # tilted degrees, looking straight down at orbital plane
        self.camera_angle_y = 20.0
        self.camera_distance = 5.0  # Default = 3
        self.mouse_dragging = False
        self.last_mouse_pos = (0, 0)

        # HUD surface — needed by draw_orbits, draw_bodies, draw_hud
        self.hud_surface = pygame.Surface(
            (self.width, self.height), pygame.SRCALPHA
        )

        # Call OpenGL one-time setup at end of __init__
        self._init_opengl()

        self._precompute_gl_positions()



    # --------------------— OpenGL setup and 3D rendering  (built by Claude)---------------------------
    # ////////////////////////////////////////////////////////////////////////////////////////////
    # ////////////////////////////////////////////////////////////////////////////////////////////
    def _init_opengl(self):
        """One-time OpenGL state configuration called from __init__."""

        # Enable depth testing — closer objects draw in front of farther ones
        glEnable(GL_DEPTH_TEST)

        # Enable smooth point and line rendering
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)

        # Enable blending so alpha transparency works (needed for HUD texture)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Black background
        glClearColor(0.0, 0.0, 0.0, 1.0)

        # Set up the perspective projection matrix
        # This defines the camera lens — field of view, aspect ratio, near/far planes
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(
            45.0,  # field of view in degrees
            self.width / self.height,  # aspect ratio
            0.001,  # near clipping plane
            1000.0  # far clipping plane
        )
        glMatrixMode(GL_MODELVIEW)  # switch back to model/view matrix

        # Draw background stars once into a display list for efficiency
        self.star_list = self._build_star_field(2000)

    def _build_star_field(self, count):
        """
        Pre-renders a random star field into an OpenGL display list.
        Display lists are compiled once and replayed cheaply each frame.
        Stars are placed on a large sphere around the origin.
        """
        rng = np.random.default_rng(42)  # fixed seed — stars don't shuffle each frame

        # Random spherical coordinates converted to Cartesian
        theta = rng.uniform(0, 2 * np.pi, count)
        phi = rng.uniform(0, np.pi, count)
        radius = 500.0

        xs = radius * np.sin(phi) * np.cos(theta)
        ys = radius * np.sin(phi) * np.sin(theta)
        zs = radius * np.cos(phi)

        # Random brightness for each star (0.3 – 1.0)
        brightness = rng.uniform(0.3, 1.0, count)

        # Compile into display list
        star_list = glGenLists(1)
        glNewList(star_list, GL_COMPILE)
        glPointSize(1.5)
        glBegin(GL_POINTS)
        for i in range(count):
            b = brightness[i]
            glColor3f(b, b, b)
            glVertex3f(xs[i], ys[i], zs[i])
        glEnd()
        glEndList()

        return star_list

    def _precompute_gl_positions(self):
        print("Precomputing trajectories...")
        self.gl_trajectories = {}
        for name in self.COLORS:
            traj = self.sim_data.get_trajectory(name)
            self.gl_trajectories[name] = np.array(
                [self._world_to_gl(p) for p in traj]
            )
            print(f"  Precomputed {name}: {len(self.gl_trajectories[name])} positions")
        print("Precompute Finished.")
    def setup_3d_camera(self):
        """
        Called every frame to position and orient the camera.

        OpenGL has no camera object — instead we move the entire world
        in the opposite direction of where we want the camera to be.

        Steps:
          1. Clear colour and depth buffers
          2. Reset the modelview matrix to identity
          3. Pull camera back by camera_distance (zoom)
          4. Rotate the world by camera_angle_x (tilt) and camera_angle_y (spin)
          5. Translate so the current camera_target body is centred on screen
        """
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # Step 3 — pull camera back along the Z axis
        glTranslatef(0.0, 0.0, -self.camera_distance)

        # Step 4 — apply mouse-controlled rotations
        glRotatef(self.camera_angle_x, 1.0, 0.0, 0.0)  # tilt  (X axis)
        glRotatef(self.camera_angle_y, 0.0, 1.0, 0.0)  # spin  (Y axis)

        # Step 5 — centre on the target body
        # We negate the target's position to move the world so the target
        # sits at the origin (which is where the camera looks by default)
        target_pos = self._get_target_position()
        if target_pos is not None:
            glTranslatef(-target_pos[0], -target_pos[1], -target_pos[2])

        # Draw star field (depth writes disabled so stars always appear behind everything)
        glDepthMask(GL_FALSE)
        glCallList(self.star_list)
        glDepthMask(GL_TRUE)

    def _get_target_position(self):
        name_map = {
            'earth': 'Earth',
            'asteroid': 'Apophis',
        }
        body_name = name_map.get(self.camera_target)
        if body_name is None:
            if self.camera_distance < 3.0:
                self.camera_distance = 5.0
            return None

        traj = self.sim_data.get_trajectory(body_name)
        pos = traj[self.frame_index]
        return self._world_to_gl(pos)

    def _world_to_gl(self, position):
        # Positions already in AU — no conversion needed
        return np.array(position, dtype=float)

    def draw_3d_scene(self):
        self._draw_grid()

        for name, color in self.COLORS.items():
            gl_positions = self.gl_trajectories[name]
            draw_positions = gl_positions

            # Skip Moon trail in solar mode — invisible at that scale
            if name == 'Moon' and self.camera_target != 'earth':
                if self.frame_index < len(draw_positions):
                    pos = draw_positions[self.frame_index]
                    glColor3f(*color)
                    glPointSize(5.0)
                    glBegin(GL_POINTS)
                    glVertex3f(pos[0], pos[1], pos[2])
                    glEnd()
                continue

            # Trail — Moon uses every point, others every 10th
            step = 1 if name == 'Moon' else 10
            trail = draw_positions[:self.frame_index:step]
            if len(trail) >= 2:
                glLineWidth(1.5)
                glColor4f(color[0], color[1], color[2], 0.6)
                glBegin(GL_LINE_STRIP)
                for pt in trail:
                    glVertex3f(pt[0], pt[1], pt[2])
                glEnd()

            # Body at current position
            if self.frame_index < len(draw_positions):
                pos = draw_positions[self.frame_index]
                glColor3f(*color)
                size_px = self.SIZES[name]
                if name == "Sun":
                    self._draw_sphere(pos, radius=0.08)
                elif size_px >= 6:
                    self._draw_sphere(pos, radius=size_px * 0.0003)
                else:
                    # Moon gets bigger point in earth mode
                    if name == 'Moon' and self.camera_target == 'earth':
                        point_size = 8.0
                    else:
                        point_size = max(6.0, float(size_px))
                    glPointSize(point_size)
                    glBegin(GL_POINTS)
                    glVertex3f(pos[0], pos[1], pos[2])
                    glEnd()

    def _draw_sphere(self, position, radius):
        """
        Draws a filled sphere at `position` (GL units) with the given radius.
        Uses GLU quadric — no external geometry needed.
        """
        glPushMatrix()
        glTranslatef(position[0], position[1], position[2])
        quad = gluNewQuadric()
        gluQuadricNormals(quad, GLU_SMOOTH)
        gluSphere(quad, radius, 16, 16)  # 16 slices × 16 stacks
        gluDeleteQuadric(quad)
        glPopMatrix()

    def _draw_grid(self):
        # Grid only makes sense in solar view
        if self.camera_target != 'solar':
            return
        glLineWidth(1.5)
        glColor3f(0.2, 0.4, 0.8)

        limit = 8.0
        step = 1.0

        glBegin(GL_LINES)
        # Draw on x-y plane (z=0) instead of x-z plane (y=0)
        x = -limit
        while x <= limit + 1e-9:
            glVertex3f(x, -limit, 0.0)  # was (x, 0.0, -limit)
            glVertex3f(x, limit, 0.0)  # was (x, 0.0,  limit)
            x += step
        y = -limit
        while y <= limit + 1e-9:
            glVertex3f(-limit, y, 0.0)  # was (-limit, 0.0, z)
            glVertex3f(limit, y, 0.0)  # was ( limit, 0.0, z)
            y += step
        glEnd()

    def _handle_mouse(self):
        """
        Called each frame to update camera angles based on mouse drag.
        Left-button drag rotates the camera (orbit control).
        Scroll wheel zooms in/out.
        """
        mouse_buttons = pygame.mouse.get_pressed()
        mouse_pos = pygame.mouse.get_pos()

        if mouse_buttons[0]:  # left button held
            if self.mouse_dragging:
                dx = mouse_pos[0] - self.last_mouse_pos[0]
                dy = mouse_pos[1] - self.last_mouse_pos[1]
                self.camera_angle_y += dx * 2.0  # horizontal drag → spin
                self.camera_angle_x += dy * 2.0  # vertical drag   → tilt
                # Clamp tilt so camera never flips upside down
                self.camera_angle_x = max(-89.0, min(89.0, self.camera_angle_x))
            self.mouse_dragging = True
            self.last_mouse_pos = mouse_pos
        else:
            self.mouse_dragging = False

    def _handle_scroll(self, event):
        """Zooms the camera in/out via scroll wheel."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 4:  # scroll up → zoom in
                self.camera_distance = max(0.05, self.camera_distance * 0.9)
            elif event.button == 5:  # scroll down → zoom out
                self.camera_distance = min(500.0, self.camera_distance * 1.1)

    def _blit_hud_to_opengl(self):
        """
        Renders the pygame HUD surface as a full-screen OpenGL texture.

        Because OpenGL owns the window, we cannot use pygame.display.blit()
        directly.  Instead we:
          1. Draw HUD elements onto self.hud_surface (a normal pygame Surface)
          2. Upload that surface as an OpenGL texture
          3. Draw the texture as a screen-aligned quad in front of everything
        """
        # Convert pygame surface pixels to a byte string OpenGL can upload
        raw = pygame.image.tostring(self.hud_surface, 'RGBA', True)
        tex = glGenTextures(1)

        glBindTexture(GL_TEXTURE_2D, tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(
            GL_TEXTURE_2D, 0, GL_RGBA,
            self.width, self.height, 0,
            GL_RGBA, GL_UNSIGNED_BYTE, raw
        )

        # Switch to orthographic (2D) projection to draw the overlay quad
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -1, 1)

        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()

        glEnable(GL_TEXTURE_2D)
        glDisable(GL_DEPTH_TEST)

        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0);
        glVertex2f(0, 0)
        glTexCoord2f(1, 0);
        glVertex2f(self.width, 0)
        glTexCoord2f(1, 1);
        glVertex2f(self.width, self.height)
        glTexCoord2f(0, 1);
        glVertex2f(0, self.height)
        glEnd()

        glDisable(GL_TEXTURE_2D)
        glEnable(GL_DEPTH_TEST)

        # Restore matrices
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

        # Clean up texture (created fresh each frame — simple but correct)
        glDeleteTextures([tex])

# ////////////////////////////////////////////////////////////////////////////////////////////
# ////////////////////////////////////////////////////////////////////////////////////////////
# --------------------— OpenGL setup and 3D rendering  (built by Claude)---------------------------

    def handle_events(self):
        # Read keyboard input:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            # handles scroll wheel zoom
            self._handle_scroll(event)

            if event.type == pygame.KEYDOWN:
                # Max 10x speed, otherwise speed up by 1
                if event.key == pygame.K_RIGHT:
                    self.playback_speed = min(10, self.playback_speed + 1)
                    print(f"Speed: {self.playback_speed}x")

                if event.key == pygame.K_LEFT:
                    # If speed goes below 1 or negative, playback breaks.
                    self.playback_speed = max(1, self.playback_speed - 1)
                    print("Playback Slowed")

                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                    print("Toggled Pause/Unpause")

                if event.key == pygame.K_r:
                    self.frame_index = 0
                    print("Rewound to start")

                if event.key == pygame.K_z:
                    zoom_modes = ['solar', 'earth', 'asteroid']
                    current = zoom_modes.index(self.zoom_mode)
                    self.zoom_mode = zoom_modes[(current + 1) % 3]
                    print(f"Zoom mode: {self.zoom_mode}")

                # 30 days × 24 hours × 3600 seconds = 2,592,000 seconds
                # sim_data stores one frame per hour
                # So, 30 days = 30 × 24 = 720 frames
                if event.key == pygame.K_UP:
                    self.frame_index = min(self.total_frames - 1, self.frame_index + 720)
                    print("Jumped forward 30 days")

                if event.key == pygame.K_DOWN:
                    self.frame_index = max(0, self.frame_index - 720)
                    print("Jumped backward 30 days")

                if event.key == pygame.K_t:
                    # a toggle to have the camera go back and forth between the asteroid,
                    # earth/moon system and solar system.
                    # % 3 "wraps around." After 'asteroid' it cycles back to 'solar'
                    targets = ['solar', 'earth', 'asteroid']
                    current = targets.index(self.camera_target)
                    self.camera_target = targets[(current + 1) % 3]
                    print(f"Camera target: {self.camera_target}")

                    # Set zoom once when target changes — not every frame
                    # stops the "rubber banding"
                    if self.camera_target == 'solar':
                        self.camera_distance = 5.0
                    elif self.camera_target == 'earth':
                        self.camera_distance = 0.05  # Default = .05
                    elif self.camera_target == 'asteroid':
                        self.camera_distance = 0.02

    def run(self):
        running = True
        while running:
            # Calling handle_events
            self.handle_events()

            # mouse drag rotates camera
            self._handle_mouse()

            # Checking if paused, if not advance by playback speed.
            # Then, check that frame_index isn't greater than it's max value.
            # If it's greater, reset; if it's not set screen to black.
            if not self.paused:
                # min() prevents it ever exceeding the last frame.
                self.frame_index += self.playback_speed
                self.frame_index = min(self.total_frames - 1, self.frame_index)

                if self.frame_index >= self.total_frames - 1:
                    # pause at last frame
                    self.paused = True

            # OpenGL camera and 3D scene as long as sim is not paused.
            self.setup_3d_camera()
            self.draw_3d_scene()

            # Clear HUD surface each frame — fully transparent
            self.hud_surface.fill((0, 0, 0, 0))

            # Using OpenGL instead to do: draw_orbits(), draw_bodies()
            # draw orbital paths as long as sim is not paused.
            # self.draw_orbits()
            # draw body markers at current frame as long as sim is not paused.
            # self.draw_bodies()

            # draw HUD text overlay
            self.draw_hud()

            # Upload HUD as OpenGL texture overlay
            self._blit_hud_to_opengl()

            # updates the display
            pygame.display.flip()

            self.clock.tick(self.FPS)

    def world_to_screen(self, position):
        # Choose scale based on current zoom mode
        if self.zoom_mode == 'solar':
            scale = self.scale
        elif self.zoom_mode == 'earth':
            scale = self.scale_earth
        else:  # asteroid follow mode
            scale = self.scale_asteroid

        # negative y is important, without it orbits appear upside down.
        screen_x = int(position[0] * scale + self.width / 2)
        screen_y = int(-position[1] * scale + self.height / 2)
        return screen_x, screen_y

    def draw_orbits(self):
        # getting trajectory up to current frame.
        # name gets the planetary object, while color gets (1.0, 0.0, 0.5) for example.
        for name, color in self.COLORS.items():
            # .get_trajectory() only takes a body name.
            # get_trajectory returns a numpy array of shape (n_steps, 3).
            trajectory = self.sim_data.get_trajectory(name)

            # converting color from 0-1 to 0-255.
            color_255 = tuple(int(c * 255) for c in color)

            # gets the positions from trajectory.
            # slice first, then convert each position individually
            # The list comprehension loops through each position
            # -> up to frame_index and converts it to screen coordinates.
            points = [self.world_to_screen(pos) for pos in trajectory[:self.frame_index]]
            # Short version of above:
            # points = []
            # for pos in trajectory[:self.frame_index]:
            #     screen_coord = self.world_to_screen(pos)
            #     points.append(screen_coord)

            # need at least 2 points to draw a line
            if len(points) < 2:
                continue
            # draws the line
            pygame.draw.lines(self.hud_surface, color_255, False, points, 2)

    def draw_bodies(self):
        for name, color in self.COLORS.items():
            # Get the position at the current frame, not the full trajectory.
            trajectory = self.sim_data.get_trajectory(name)
            current_pos = trajectory[self.frame_index]

            # one SINGLE position to screen coordinates(points logic above gets a list)
            # make these local variable again.
            color_255 = tuple(int(c * 255) for c in color)
            screen_x, screen_y = self.world_to_screen(current_pos)
            # surface,    # self.screen
            # color,      # RGB tuple 0-255
            # center,     # (x, y) screen coordinates
            # radius      # size in pixels
            pygame.draw.circle(self.hud_surface, color_255, (screen_x, screen_y), self.SIZES[name])

            # WAITING TO FINISH DRONE CLASS...
            # Only draw drones when zoomed into asteroid
            # if self.zoom_mode == 'asteroid' and hasattr(self.body, 'is_drone'):
            # draw small colored dot for each drone
            # color indicates mode: green=thrusting, yellow=returning, red=charging

            # draw the body name next to it
            # render text to a surface
            label = self.font.render(name, True, color_255)
            # Blit it slightly offset from the body center
            self.hud_surface.blit(label, (screen_x + 8, screen_y - 8))

    def _format_distance(self, dist_au):
        # Converts AU to human-readable distance
        dist_km = dist_au * 1.496e8
        if dist_km > 1e6:
            return f"{dist_au:.4f} AU  ({dist_km / 1e6:.2f}M km)"
        elif dist_km > 1000:
            return f"{dist_au:.4f} AU  ({dist_km:,.0f} km)"
        else:
            return f"{dist_au:.6f} AU  ({dist_km:.1f} km)"

    def _format_velocity(self, speed_auyr):
        # Converts AU/year to km/s
        # 1 AU/year = 4.74057 km/s
        speed_kms = speed_auyr * 4.74057
        return f"{speed_kms:.2f} km/s"

    def draw_hud(self):
        # displays all the text information overlaid on the simulation.
        WHITE = (255, 255, 255, 255)
        y = 10  # pixel height
        line_height = 20

        # helper — renders one line and moves y down automatically by 20 pixels
        def draw_line(text):
            nonlocal y
            surface = self.font.render(text, True, WHITE)
            self.hud_surface.blit(surface, (10, y))
            y += line_height

        # Current time:
        current_time = self.sim_data.times[self.frame_index]
        days = current_time * 365.25
        draw_line(f"Time: {days:.1f} days  ({current_time:.3f} years)")
        '''
        current_time = self.sim_data.times[self.frame_index]
        days = current_time / 86400  # 86400 seconds per day
        draw_line(f"Time: {days:.1f} days")
        '''

        # Energy drift:
        e0 = self.sim_data.energies[0]
        ec = self.sim_data.energies[self.frame_index]
        drift = abs((ec - e0) / e0) * 100
        draw_line(f"Energy drift: {drift:.10f} %")

        # Body velocities(sim_data stores velocities):
        draw_line("--- Velocities ---")
        for name in self.COLORS:
            vel_array = np.array(self.sim_data.velocities[name])
            current_vel = vel_array[self.frame_index]
            speed = np.linalg.norm(current_vel)
            draw_line(f"  {name}: {self._format_velocity(speed)}")

        # Distances between bodies:
        draw_line("--- Distances ---")

        # helper to compute distance between two bodies at current frame
        def body_distance(name_a, name_b):
            # These lines read current frame_index every call
            pos_a = self.sim_data.get_trajectory(name_a)[self.frame_index]
            pos_b = self.sim_data.get_trajectory(name_b)[self.frame_index]
            return np.linalg.norm(pos_b - pos_a)

        draw_line(f"  Earth-Sun:    {self._format_distance(body_distance('Earth', 'Sun'))}")
        draw_line(f"  Apophis-Sun:  {self._format_distance(body_distance('Apophis', 'Sun'))}")
        if 'Moon' in self.sim_data.positions:
            draw_line(f"  Moon-Earth:   {self._format_distance(body_distance('Moon', 'Earth'))}")
        if 'Rocket' in self.sim_data.positions:
            draw_line(f"  Rocket-Earth: {self._format_distance(body_distance('Rocket', 'Earth'))}")

        # Current playback speed:
        draw_line(f"Speed: {self.playback_speed}x  {'PAUSED' if self.paused else 'PLAYING'}")

        draw_line("--- Controls ---")
        draw_line("[SPACE] Pause  [R] Rewind")
        draw_line("[←→] Speed    [↑↓] Jump 30 days")
        draw_line("[Z] Zoom       [T] Camera")

