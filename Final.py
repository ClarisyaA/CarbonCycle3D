import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import random
import numpy as np

# Konstanta
WIDTH, HEIGHT = 1400, 900
FPS = 60

# Fungsi helper untuk menggambar sphere tanpa GLUT
def draw_sphere(radius, slices=20, stacks=20):
    quadric = gluNewQuadric()
    gluSphere(quadric, radius, slices, stacks)
    gluDeleteQuadric(quadric)

# Fungsi helper untuk menggambar cube
def draw_cube(size=1.0):
    s = size / 2.0
    vertices = [
        [-s, -s, -s], [s, -s, -s], [s, s, -s], [-s, s, -s],  # Back
        [-s, -s, s], [s, -s, s], [s, s, s], [-s, s, s]       # Front
    ]
    
    faces = [
        [0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4],
        [2, 3, 7, 6], [0, 3, 7, 4], [1, 2, 6, 5]
    ]
    
    normals = [
        [0, 0, -1], [0, 0, 1], [0, -1, 0],
        [0, 1, 0], [-1, 0, 0], [1, 0, 0]
    ]
    
    glBegin(GL_QUADS)
    for i, face in enumerate(faces):
        glNormal3fv(normals[i])
        for vertex in face:
            glVertex3fv(vertices[vertex])
    glEnd()

# Class untuk partikel CO2
class CO2Particle:
    def __init__(self, x, y, z):
        self.pos = [x, y, z]
        self.velocity = [random.uniform(-0.03, 0.03), random.uniform(0.01, 0.04), random.uniform(-0.03, 0.03)]
        self.size = random.uniform(0.06, 0.12)
        self.lifetime = random.uniform(4, 8)
        self.age = 0
        self.float_offset = random.uniform(0, 2 * math.pi)
        
    def update(self, dt, time):
        self.age += dt
        
        # Float movement
        self.pos[0] += self.velocity[0] + math.sin(time + self.float_offset) * 0.01
        self.pos[1] += self.velocity[1] * 0.3
        self.pos[2] += self.velocity[2] + math.cos(time + self.float_offset) * 0.01
        
        # Boundary check
        if self.pos[1] > 4:
            self.pos[1] = -2
        if abs(self.pos[0]) > 6:
            self.velocity[0] *= -1
        if abs(self.pos[2]) > 6:
            self.velocity[2] *= -1
                
        return self.age < self.lifetime
    
    def draw(self):
        glPushMatrix()
        glTranslatef(*self.pos)
        
        # Glow effect
        glColor4f(0.3, 0.5, 0.9, 0.25)
        draw_sphere(self.size * 1.8, 10, 10)
        
        # Main particle
        glColor4f(0.4, 0.65, 1.0, 0.8)
        draw_sphere(self.size, 10, 10)
        glPopMatrix()

# Class untuk Tree
class Tree:
    def __init__(self, x, y, z):
        self.pos = [x, y, z]
        self.sway = 0
        self.absorbing = False
        self.absorb_timer = 0
        self.growth = 1.0
        
    def update(self, dt, time):
        self.sway = math.sin(time * 2 + self.pos[0]) * 0.08
        self.absorb_timer -= dt
        if self.absorb_timer <= 0:
            self.absorbing = False
        
        # Gentle breathing animation
        self.growth = 1.0 + math.sin(time * 1.5 + self.pos[0]) * 0.05
    
    def absorb_co2(self):
        self.absorbing = True
        self.absorb_timer = 1.2
        
    def draw(self):
        glPushMatrix()
        glTranslatef(*self.pos)
        glRotatef(self.sway * 8, 0, 0, 1)
        
        # Trunk
        glColor3f(0.45, 0.30, 0.15)
        glPushMatrix()
        glTranslatef(0, -0.3, 0)
        glScalef(0.18, 0.7, 0.18)
        draw_cube(1.0)
        glPopMatrix()
        
        # Leaves - main
        scale = self.growth
        if self.absorbing:
            glColor3f(0.1, 1.0, 0.4)  # Bright green when absorbing
        else:
            glColor3f(0.15, 0.60, 0.20)
        
        glPushMatrix()
        glTranslatef(0, 0.35, 0)
        glScalef(scale, scale, scale)
        draw_sphere(0.55, 16, 16)
        glPopMatrix()
        
        # Side leaves
        glColor3f(0.25, 0.75, 0.30)
        glPushMatrix()
        glTranslatef(-0.35, 0.20, 0)
        glScalef(scale, scale, scale)
        draw_sphere(0.38, 14, 14)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(0.35, 0.20, 0)
        glScalef(scale, scale, scale)
        draw_sphere(0.38, 14, 14)
        glPopMatrix()
        
        # Glow effect when absorbing
        if self.absorbing:
            glColor4f(0.2, 1.0, 0.3, 0.4)
            glPushMatrix()
            glTranslatef(0, 0.35, 0)
            draw_sphere(0.75, 16, 16)
            glPopMatrix()
        
        glPopMatrix()

# Class untuk Factory
class Factory:
    def __init__(self, x, y, z):
        self.pos = [x, y, z]
        self.smoke_timer = 0
        self.smoke_particles = []
        
    def update(self, dt):
        self.smoke_timer += dt
        
        # Update smoke particles
        self.smoke_particles = [s for s in self.smoke_particles if s['life'] > 0]
        for smoke in self.smoke_particles:
            smoke['y'] += 0.025
            smoke['x'] += random.uniform(-0.015, 0.015)
            smoke['z'] += random.uniform(-0.01, 0.01)
            smoke['life'] -= dt
            smoke['size'] += 0.012
            
    def emit_smoke(self):
        if self.smoke_timer > 0.15:
            self.smoke_timer = 0
            for chimney_x in [-0.2, 0.2]:
                self.smoke_particles.append({
                    'x': self.pos[0] + chimney_x, 
                    'y': self.pos[1] + 0.9, 
                    'z': self.pos[2],
                    'size': 0.12,
                    'life': 2.5
                })
    
    def draw(self):
        glPushMatrix()
        glTranslatef(*self.pos)
        
        # Building
        glColor3f(0.21, 0.36, 0.45)
        glPushMatrix()
        glScalef(0.9, 0.7, 0.7)
        draw_cube(1.0)
        glPopMatrix()
        
        # Windows
        glColor3f(0.70, 0.90, 1.00)
        for i in range(-1, 2):
            for j in range(2):
                glPushMatrix()
                glTranslatef(i * 0.28, -0.1 + j * 0.28, 0.36)
                glScalef(0.16, 0.16, 0.01)
                draw_cube(1.0)
                glPopMatrix()
        
        # Chimneys
        glColor3f(0.25, 0.28, 0.32)
        glPushMatrix()
        glTranslatef(-0.2, 0.6, 0)
        glScalef(0.16, 0.5, 0.16)
        draw_cube(1.0)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(0.2, 0.7, 0)
        glScalef(0.16, 0.6, 0.16)
        draw_cube(1.0)
        glPopMatrix()
        
        glPopMatrix()
        
        # Draw smoke
        for smoke in self.smoke_particles:
            alpha = smoke['life'] / 2.5
            glColor4f(0.65, 0.65, 0.68, alpha * 0.6)
            glPushMatrix()
            glTranslatef(smoke['x'], smoke['y'], smoke['z'])
            draw_sphere(smoke['size'], 10, 10)
            glPopMatrix()

# Class untuk Cow
class Cow:
    def __init__(self, x, y, z):
        self.pos = [x, y, z]
        self.breath_timer = 0
        self.breathing = False
        self.walk_offset = random.uniform(0, 2 * math.pi)
        
    def update(self, dt, time):
        self.breath_timer += dt
        if self.breath_timer > 2.5:
            self.breathing = True
            if self.breath_timer > 3.0:
                self.breath_timer = 0
        else:
            self.breathing = False
    
    def draw(self, time):
        glPushMatrix()
        glTranslatef(*self.pos)
        
        # Gentle bobbing
        bob = math.sin(time * 2.5 + self.walk_offset) * 0.04
        glTranslatef(0, bob, 0)
        
        # Body
        glColor3f(0.255, 0.252, 0.247)
        glPushMatrix()
        glScalef(0.55, 0.35, 0.35)
        draw_cube(1.0)
        glPopMatrix()
        
        # Head
        glPushMatrix()
        glTranslatef(-0.38, 0.05, 0)
        glScalef(0.28, 0.23, 0.23)
        draw_cube(1.0)
        glPopMatrix()
        
        # Ears
        glColor3f(1.0, 0.9, 0.9)
        glPushMatrix()
        glTranslatef(-0.45, 0.15, 0.13)
        glScalef(0.08, 0.12, 0.02)
        draw_cube(1.0)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(-0.45, 0.15, -0.13)
        glScalef(0.08, 0.12, 0.02)
        draw_cube(1.0)
        glPopMatrix()
        
        # Spots
        glColor3f(0.1, 0.05, 0.05)
        glPushMatrix()
        glTranslatef(-0.12, 0.08, 0.19)
        draw_sphere(0.09, 10, 10)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(0.12, 0.02, 0.19)
        draw_sphere(0.10, 10, 10)
        glPopMatrix()
        
        # Legs
        glColor3f(0.95, 0.95, 0.95)
        for i in [-0.18, -0.06, 0.06, 0.18]:
            glPushMatrix()
            glTranslatef(i, -0.28, 0)
            glScalef(0.07, 0.24, 0.07)
            draw_cube(1.0)
            glPopMatrix()
        
        # Tail
        glPushMatrix()
        glTranslatef(0.35, -0.05, 0)
        glRotatef(20 + math.sin(time * 4) * 15, 0, 0, 1)
        glScalef(0.03, 0.25, 0.03)
        draw_cube(1.0)
        glPopMatrix()
        
        # CO2 bubble when breathing
        if self.breathing:
            glColor4f(0.35, 0.55, 0.95, 0.6)
            size = 0.18 if self.breath_timer < 2.7 else 0.22
            glPushMatrix()
            glTranslatef(-0.55, 0.18, 0)
            draw_sphere(size, 12, 12)
            glPopMatrix()
        
        glPopMatrix()

# Class untuk Car
class Car:
    def __init__(self, x, y, z):
        self.pos = [x, y, z]
        self.exhaust_particles = []
        self.exhaust_timer = 0
        self.wheel_rotation = 0
        
    def update(self, dt, time):
        self.exhaust_timer += dt
        self.wheel_rotation += dt * 100
        
        # Update exhaust
        self.exhaust_particles = [e for e in self.exhaust_particles if e['life'] > 0]
        for exhaust in self.exhaust_particles:
            exhaust['x'] += 0.025
            exhaust['y'] += random.uniform(-0.008, 0.012)
            exhaust['z'] += random.uniform(-0.005, 0.005)
            exhaust['life'] -= dt
            
    def emit_exhaust(self):
        if self.exhaust_timer > 0.25:
            self.exhaust_timer = 0
            self.exhaust_particles.append({
                'x': self.pos[0] + 0.45,
                'y': self.pos[1] - 0.12,
                'z': self.pos[2],
                'life': 1.8
            })
    
    def draw(self):
        glPushMatrix()
        glTranslatef(*self.pos)
        
        # Body
        glColor3f(0.95, 0.75, 0.1)
        glPushMatrix()
        glScalef(0.65, 0.23, 0.28)
        draw_cube(1.0)
        glPopMatrix()
        
        # Roof
        glPushMatrix()
        glTranslatef(0, 0.18, 0)
        glScalef(0.38, 0.22, 0.26)
        draw_cube(1.0)
        glPopMatrix()
        
        # Windows
        glColor3f(0.50, 0.75, 0.88)
        glPushMatrix()
        glTranslatef(-0.05, 0.18, 0.14)
        glScalef(0.16, 0.16, 0.01)
        draw_cube(1.0)
        glPopMatrix()
        
        glPushMatrix()
        glTranslatef(-0.05, 0.18, -0.14)
        glScalef(0.16, 0.16, 0.01)
        draw_cube(1.0)
        glPopMatrix()
        
        # Wheels
        glColor3f(0.15, 0.15, 0.15)
        for x in [-0.22, 0.22]:
            for z in [-0.17, 0.17]:
                glPushMatrix()
                glTranslatef(x, -0.17, z)
                glRotatef(self.wheel_rotation, 0, 0, 1)
                draw_sphere(0.09, 12, 12)
                glPopMatrix()
        
        glPopMatrix()
        
        # Draw exhaust
        for exhaust in self.exhaust_particles:
            alpha = exhaust['life'] / 1.8
            glColor4f(0.5, 0.5, 0.52, alpha * 0.65)
            glPushMatrix()
            glTranslatef(exhaust['x'], exhaust['y'], exhaust['z'])
            draw_sphere(0.10, 10, 10)
            glPopMatrix()

# Class untuk Soil/Ground dengan fosil
class Soil:
    def __init__(self, x, y, z):
        self.pos = [x, y, z]
        
    def draw(self):
        glPushMatrix()
        glTranslatef(*self.pos)
        
        # Soil layer
        glColor3f(0.45, 0.30, 0.20)
        glPushMatrix()
        glScalef(0.9, 0.25, 0.6)
        draw_cube(1.0)
        glPopMatrix()
        
        # Fossils/bones
        glColor3f(0.92, 0.90, 0.82)
        for i in range(3):
            glPushMatrix()
            glTranslatef(-0.3 + i * 0.3, 0, 0.1)
            glRotatef(45 + i * 30, 0, 0, 1)
            glScalef(0.18, 0.04, 0.04)
            draw_cube(1.0)
            glPopMatrix()
        
        # Small stones
        glColor3f(0.45, 0.30, 0.20)
        for i in range(4):
            glPushMatrix()
            glTranslatef(-0.35 + i * 0.25, -0.05, -0.15)
            draw_sphere(0.04, 8, 8)
            glPopMatrix()
        
        # Roots coming down
        glColor3f(0.45, 0.30, 0.15)
        for i in range(2):
            glPushMatrix()
            glTranslatef(-0.25 + i * 0.5, 0.18, 0)
            glScalef(0.025, 0.18, 0.025)
            draw_cube(1.0)
            glPopMatrix()
        
        glPopMatrix()

# Main simulation class
class CarbonCycleSimulation:
    def __init__(self):
        pygame.init()
        
        # Get display info for better window handling
        display_info = pygame.display.Info()
        self.screen_width = min(WIDTH, display_info.current_w - 100)
        self.screen_height = min(HEIGHT, display_info.current_h - 100)
        
        self.display = pygame.display.set_mode((self.screen_width, self.screen_height), DOUBLEBUF | OPENGL | RESIZABLE)
        pygame.display.set_caption("Simulasi 3D Siklus Karbon - Interaktif")
        
        self.setup_opengl()
        self.reset_scene()
        
        # Font for UI
        self.font = pygame.font.Font(None, 40)
        self.small_font = pygame.font.Font(None, 26)
        
    def setup_opengl(self):
        # Setup OpenGL
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHT1)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        
        # Sky blue background
        glClearColor(0.53, 0.81, 0.92, 1.0)
        
        # Main light (sun)
        glLight(GL_LIGHT0, GL_POSITION, (8, 12, 6, 1))
        glLight(GL_LIGHT0, GL_AMBIENT, (0.5, 0.5, 0.5, 1))
        glLight(GL_LIGHT0, GL_DIFFUSE, (1.0, 0.98, 0.9, 1))
        glLight(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 0.9, 1))
        
        # Fill light
        glLight(GL_LIGHT1, GL_POSITION, (-5, 8, -5, 1))
        glLight(GL_LIGHT1, GL_AMBIENT, (0.3, 0.3, 0.35, 1))
        glLight(GL_LIGHT1, GL_DIFFUSE, (0.5, 0.5, 0.6, 1))
        
        # Perspective
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(50, self.screen_width / self.screen_height, 0.1, 50.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslatef(0, -1, -16)
        
    def reset_scene(self):
        # Game state
        self.clock = pygame.time.Clock()
        self.running = True
        self.paused = False
        self.time = 0
        
        # Camera rotation
        self.rotation_x = 25
        self.rotation_y = 0
        self.auto_rotate = True
        self.mouse_down = False
        self.last_mouse_pos = None
        
        # Objects
        self.trees = []
        self.factories = []
        self.cows = []
        self.cars = []
        self.soils = []
        self.co2_particles = []
        
        # Stats
        self.co2_level = 100
        self.photosynthesis_rate = 0
        self.emission_rate = 0
        
        # Initialize scene
        self.init_scene()
        
    def init_scene(self):
        # Add initial objects in a circle
        angles = np.linspace(0, 2 * np.pi, 12, endpoint=False)
        radius = 4.5
        
        for i, angle in enumerate(angles):
            x = radius * np.cos(angle)
            z = radius * np.sin(angle)
            
            if i % 4 == 0:
                self.trees.append(Tree(x, -1, z))
            elif i % 4 == 1:
                self.factories.append(Factory(x, -1, z))
            elif i % 4 == 2:
                self.cows.append(Cow(x, -1, z))
            else:
                self.cars.append(Car(x, -1, z))
        
        # Add soil at bottom - fixed positions
        soil_positions = [
            (-3.5, -2.3, 0),
            (-0.5, -2.3, 0),
            (2.5, -2.3, 0)
        ]
        for pos in soil_positions:
            self.soils.append(Soil(*pos))
        
        # Add some initial CO2 particles
        for _ in range(30):
            x = random.uniform(-4, 4)
            y = random.uniform(-1, 3)
            z = random.uniform(-4, 4)
            self.co2_particles.append(CO2Particle(x, y, z))
    
    def add_object(self, obj_type):
        angle = random.uniform(0, 2 * np.pi)
        radius = random.uniform(3.5, 5.5)
        x = radius * np.cos(angle)
        z = radius * np.sin(angle)
        
        if obj_type == 'tree':
            self.trees.append(Tree(x, -1, z))
            self.co2_level -= 5
        elif obj_type == 'factory':
            self.factories.append(Factory(x, -1, z))
            self.co2_level += 10
        elif obj_type == 'cow':
            self.cows.append(Cow(x, -1, z))
            self.co2_level += 3
        elif obj_type == 'car':
            self.cars.append(Car(x, -1, z))
            self.co2_level += 8
    
    def draw_text_2d(self, text, x, y, font, color=(255, 255, 255)):
        text_surface = font.render(text, True, color)
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.screen_width, self.screen_height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        
        glRasterPos2f(x, y)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(),
                     GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    
    def draw_clouds(self):
        glDisable(GL_LIGHTING)
        
        # Multiple cloud layers
        cloud_positions = [
            (-8, 6, -10), (5, 7, -12), (-3, 8, -15),
            (10, 6.5, -8), (-6, 7.5, -11), (3, 8.5, -14),
            (8, 6, -13), (-10, 7, -9)
        ]
        
        for i, (x, y, z) in enumerate(cloud_positions):
            offset_x = math.sin(self.time * 0.3 + i) * 2
            offset_y = math.sin(self.time * 0.5 + i * 0.7) * 0.3
            
            glColor4f(1.0, 1.0, 1.0, 0.85)
            glPushMatrix()
            glTranslatef(x + offset_x, y + offset_y, z)
            
            # Multi-sphere cloud
            draw_sphere(1.2, 12, 12)
            glTranslatef(0.8, 0, 0)
            draw_sphere(1.0, 12, 12)
            glTranslatef(-0.4, 0.3, 0)
            draw_sphere(0.9, 12, 12)
            glTranslatef(-0.8, 0, 0)
            draw_sphere(0.85, 12, 12)
            
            glPopMatrix()
        
        glEnable(GL_LIGHTING)
    
    def draw_co2_center(self):
        # Central CO2 visualization
        glPushMatrix()
        glTranslatef(0, 1.5, 0)
        
        # Pulsing effect
        pulse = 1.0 + 0.15 * math.sin(self.time * 3)
        
        # Outer glow
        glColor4f(0.35, 0.55, 0.95, 0.25)
        draw_sphere(0.9 * pulse, 20, 20)
        
        # Main sphere
        glColor4f(0.45, 0.70, 1.0, 0.7)
        draw_sphere(0.65 * pulse, 20, 20)
        
        # Inner core
        glColor4f(0.6, 0.8, 1.0, 0.9)
        draw_sphere(0.4 * pulse, 20, 20)
        
        glPopMatrix()
    
    def update(self, dt):
        if self.paused:
            return
            
        self.time += dt
        
        # Update all objects
        for tree in self.trees:
            tree.update(dt, self.time)
            
        for factory in self.factories:
            factory.update(dt)
            factory.emit_smoke()
            
        for cow in self.cows:
            cow.update(dt, self.time)
            
        for car in self.cars:
            car.update(dt, self.time)
            car.emit_exhaust()
        
        # Update CO2 particles
        self.co2_particles = [p for p in self.co2_particles if p.update(dt, self.time)]
        
        # Add new CO2 from sources more dynamically
        if random.random() < 0.15:
            if self.factories:
                factory = random.choice(self.factories)
                for _ in range(2):
                    self.co2_particles.append(CO2Particle(
                        factory.pos[0] + random.uniform(-0.3, 0.3), 
                        factory.pos[1] + 0.8, 
                        factory.pos[2] + random.uniform(-0.3, 0.3)
                    ))
                    
        if random.random() < 0.08 and self.cows:
            cow = random.choice(self.cows)
            self.co2_particles.append(CO2Particle(
                cow.pos[0] - 0.4, cow.pos[1] + 0.3, cow.pos[2]
            ))
        
        if random.random() < 0.12 and self.cars:
            car = random.choice(self.cars)
            self.co2_particles.append(CO2Particle(
                car.pos[0] + 0.4, car.pos[1] - 0.1, car.pos[2]
            ))
        
        # Trees absorb CO2 - more dynamic
        for tree in self.trees:
            for particle in self.co2_particles[:]:
                dx = particle.pos[0] - tree.pos[0]
                dy = particle.pos[1] - tree.pos[1]
                dz = particle.pos[2] - tree.pos[2]
                dist = math.sqrt(dx*dx + dy*dy + dz*dz)
                
                if dist < 0.9:
                    self.co2_particles.remove(particle)
                    tree.absorb_co2()
                    self.co2_level -= 0.5
                    break
        
        # Calculate rates
        self.photosynthesis_rate = len(self.trees) * 2
        self.emission_rate = len(self.factories) * 5 + len(self.cars) * 3 + len(self.cows)
        
        # Update CO2 level
        self.co2_level += (self.emission_rate - self.photosynthesis_rate) * dt * 0.1
        self.co2_level = max(0, min(500, self.co2_level))
        
        # Auto rotation
        if self.auto_rotate and not self.mouse_down:
            self.rotation_y += 12 * dt
    
    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        glPushMatrix()
        
        # Apply rotation
        glRotatef(self.rotation_x, 1, 0, 0)
        glRotatef(self.rotation_y, 0, 1, 0)
        
        # Draw clouds in background
        self.draw_clouds()
        
        # Draw ground plane (grass)
        glDisable(GL_LIGHTING)
        glColor3f(0.4, 0.75, 0.35)
        glBegin(GL_QUADS)
        glVertex3f(-12, -2.2, -12)
        glVertex3f(12, -2.2, -12)
        glVertex3f(12, -2.2, 12)
        glVertex3f(-12, -2.2, 12)
        glEnd()
        
        # Add some grass details
        glColor3f(0.35, 0.70, 0.30)
        for i in range(20):
            for j in range(20):
                x = -10 + i
                z = -10 + j
                if random.random() < 0.3:
                    glBegin(GL_TRIANGLES)
                    glVertex3f(x, -2.2, z)
                    glVertex3f(x + 0.05, -2.1, z)
                    glVertex3f(x + 0.1, -2.2, z)
                    glEnd()
        
        glEnable(GL_LIGHTING)
        
        # Draw central CO2
        self.draw_co2_center()
        
        # Draw all objects
        for tree in self.trees:
            tree.draw()
            
        for factory in self.factories:
            factory.draw()
            
        for cow in self.cows:
            cow.draw(self.time)
            
        for car in self.cars:
            car.draw()
            
        for soil in self.soils:
            soil.draw()
            
        for particle in self.co2_particles:
            particle.draw()
        
        # Draw sun
        glDisable(GL_LIGHTING)
        glColor3f(1.0, 0.95, 0.7)
        glPushMatrix()
        glTranslatef(8, 10, -12)
        draw_sphere(1.5, 20, 20)
        glPopMatrix()
        glEnable(GL_LIGHTING)
        
        glPopMatrix()
        
        # Draw UI
        self.draw_ui()
        
        pygame.display.flip()
    
    def draw_ui(self):
        # Semi-transparent background for text
        glDisable(GL_LIGHTING)
        glDisable(GL_DEPTH_TEST)
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.screen_width, self.screen_height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # Dark overlay for title
        glColor4f(0.0, 0.0, 0.0, 0.5)
        glBegin(GL_QUADS)
        glVertex2f(0, 0)
        glVertex2f(self.screen_width, 0)
        glVertex2f(self.screen_width, 70)
        glVertex2f(0, 70)
        glEnd()
        
        # Stats background
        glColor4f(0.0, 0.0, 0.0, 0.4)
        glBegin(GL_QUADS)
        glVertex2f(10, 75)
        glVertex2f(350, 75)
        glVertex2f(350, 330)
        glVertex2f(10, 330)
        glEnd()
        
        # Controls background
        glBegin(GL_QUADS)
        glVertex2f(10, self.screen_height - 180)
        glVertex2f(520, self.screen_height - 180)
        glVertex2f(520, self.screen_height - 10)
        glVertex2f(10, self.screen_height - 180)
        glEnd()
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        
        # Title
        self.draw_text_2d("SIMULASI 3D SIKLUS KARBON", 25, 35, self.font, (255, 255, 150))
        
        # Stats
        y = 105
        co2_color = (100, 255, 150) if self.co2_level < 150 else (255, 200, 100) if self.co2_level < 300 else (255, 100, 100)
        self.draw_text_2d(f"CO2 Level: {int(self.co2_level)} ppm", 25, y, self.small_font, co2_color)
        self.draw_text_2d(f"Fotosintesis: -{self.photosynthesis_rate}", 25, y + 35, self.small_font, (100, 255, 150))
        self.draw_text_2d(f"Emisi: +{self.emission_rate}", 25, y + 70, self.small_font, (255, 150, 150))
        
        # Object counts
        y = 245
        self.draw_text_2d(f"🌳 Pohon: {len(self.trees)}", 25, y, self.small_font, (150, 255, 150))
        self.draw_text_2d(f"🏭 Pabrik: {len(self.factories)}", 25, y + 30, self.small_font, (200, 200, 200))
        self.draw_text_2d(f"🐄 Hewan: {len(self.cows)}", 25, y + 60, self.small_font, (255, 230, 180))
        self.draw_text_2d(f"🚗 Mobil: {len(self.cars)}", 25, y + 90, self.small_font, (255, 235, 150))
        
        # Controls
        y = self.screen_height - 165
        self.draw_text_2d("KONTROL:", 25, y, self.small_font, (255, 255, 150))
        self.draw_text_2d("T - Tambah Pohon (kurangi CO2)", 25, y + 30, self.small_font, (220, 220, 220))
        self.draw_text_2d("F - Tambah Pabrik | C - Tambah Hewan | V - Tambah Mobil", 25, y + 58, self.small_font, (220, 220, 220))
        self.draw_text_2d("SPACE - Pause | R - Reset | Mouse Drag - Rotate", 25, y + 86, self.small_font, (220, 220, 220))
        self.draw_text_2d("A - Toggle Auto-Rotate", 25, y + 114, self.small_font, (220, 220, 220))
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                
            elif event.type == pygame.VIDEORESIZE:
                self.screen_width = event.w
                self.screen_height = event.h
                glViewport(0, 0, event.w, event.h)
                glMatrixMode(GL_PROJECTION)
                glLoadIdentity()
                gluPerspective(50, event.w / event.h, 0.1, 50.0)
                glMatrixMode(GL_MODELVIEW)
                
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.reset_scene()
                elif event.key == pygame.K_t:
                    self.add_object('tree')
                elif event.key == pygame.K_f:
                    self.add_object('factory')
                elif event.key == pygame.K_c:
                    self.add_object('cow')
                elif event.key == pygame.K_v:
                    self.add_object('car')
                elif event.key == pygame.K_a:
                    self.auto_rotate = not self.auto_rotate
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
                    
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_down = True
                self.last_mouse_pos = pygame.mouse.get_pos()
                self.auto_rotate = False
                
            elif event.type == pygame.MOUSEBUTTONUP:
                self.mouse_down = False
                
            elif event.type == pygame.MOUSEMOTION:
                if self.mouse_down and self.last_mouse_pos:
                    x, y = pygame.mouse.get_pos()
                    dx = x - self.last_mouse_pos[0]
                    dy = y - self.last_mouse_pos[1]
                    
                    self.rotation_y += dx * 0.4
                    self.rotation_x += dy * 0.4
                    self.rotation_x = max(-90, min(90, self.rotation_x))
                    
                    self.last_mouse_pos = (x, y)
    
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            
            self.handle_events()
            self.update(dt)
            self.draw()
        
        pygame.quit()

# Main entry point
if __name__ == "__main__":
    sim = CarbonCycleSimulation()
    sim.run()