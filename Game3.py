from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time

# Camera-related variables - Fixed to start from cannon side
camera_pos = (0, -800, 300)  # Position camera behind cannon
fovY = 120
GRID_LENGTH = 600

# Game state variables
cannon_rotation = 0  # Horizontal rotation of cannon
cannon_elevation = 45  # Vertical elevation of cannon
bullets = []
enemies = []
explosions = []
powerups = []
score = 0
lives = 5  # Changed from 3 to 5
game_over = False
wave_number = 1
last_enemy_spawn = 0
enemy_spawn_delay = 2.0  # seconds between enemy spawns
wave_enemies_spawned = 0
enemies_per_wave = 5

# Cheat mode variables
cheat_mode = False
cheat_cooldown = 0
auto_fire_timer = 0

# Power-up variables
double_shot = False
rapid_fire = False
shield_active = False
powerup_timers = {"double": 0, "rapid": 0, "shield": 0}

# New variables for consecutive hits
consecutive_hits = 0
last_hit_time = 0
HIT_TIMEOUT = 3.0  # seconds between hits to count as consecutive

class HomingBullet:
    def __init__(self, x, y, z, target_enemy):
        self.x, self.y, self.z = x, y, z
        self.target = target_enemy
        self.speed = 600  # Faster speed for cheat mode
        self.life = 5.0  # Longer lifetime for cheat mode
        self.vx, self.vy, self.vz = 0, 0, 0  # Initialize velocity
        
    def update(self, dt):
        if self.target and self.target in enemies:  # If target still exists
            # Calculate direction to target
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            dz = self.target.z - self.z
            
            # Normalize direction
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            if dist > 0:
                self.vx = (dx / dist) * self.speed
                self.vy = (dy / dist) * self.speed
                self.vz = (dz / dist) * self.speed
                
            # Move toward target
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.z += self.vz * dt
        else:
            # If target is gone, continue in last direction
            self.x += self.vx * dt
            self.y += self.vy * dt
            self.z += self.vz * dt
            
        self.life -= dt

    def is_alive(self):
        return self.life > 0 and self.z >= 0

class Bullet:
    def __init__(self, x, y, z, vx, vy, vz):
        self.x, self.y, self.z = x, y, z
        self.vx, self.vy, self.vz = vx, vy, vz
        self.life = 3.0  # Bullet lifetime in seconds

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        self.life -= dt

    def is_alive(self):
        return self.life > 0 and self.z >= 0

class Enemy:
    def __init__(self, enemy_type="drone"):
        self.type = enemy_type
        if enemy_type == "bomber":
            self.size = 40
            self.speed = 50 + wave_number * 5
            self.health = 3
        else:  # drone
            self.size = 20
            self.speed = 80 + wave_number * 10
            self.health = 1

        # Random starting position at far end of grid (opposite of cannon)
        self.x = random.uniform(-300, 300)
        self.y = 500  # Start from far end
        self.z = random.uniform(200, 600)  # Various heights

        # Movement pattern
        self.movement_type = random.choice(["straight", "zigzag", "curve"])
        self.time_alive = 0
        self.amplitude = random.uniform(50, 150)

    def update(self, dt):
        self.time_alive += dt

        # Move towards cannon (negative Y direction)
        self.y -= self.speed * dt

        # Apply movement pattern
        if self.movement_type == "zigzag":
            self.x += math.sin(self.time_alive * 3) * self.amplitude * dt
        elif self.movement_type == "curve":
            self.x += math.sin(self.time_alive * 2) * self.amplitude * dt
            self.z += math.cos(self.time_alive * 1.5) * 30 * dt  # Slight altitude variation

    def is_alive(self):
        return self.z > -50 and self.health > 0

    def reached_ground(self):
        return self.y <= -500  # Reached cannon side of grid

class Explosion:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z
        self.size = 0
        self.max_size = 50
        self.life = 0.5

    def update(self, dt):
        self.life -= dt
        self.size = self.max_size * (1 - self.life / 0.5)

    def is_alive(self):
        return self.life > 0

class PowerUp:
    def __init__(self, x, y, z, ptype):
        self.x, self.y, self.z = x, y, z
        self.type = ptype  # "double", "rapid", "shield"
        self.size = 15
        self.rotation = 0

    def update(self, dt):
        self.z -= 30 * dt  # Fall slowly
        self.rotation += 180 * dt  # Rotate for visibility

    def is_alive(self):
        return self.z > 0

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_cannon():
    glPushMatrix()

    # Position cannon at bottom center of grid
    glTranslatef(0, -400, 0)

    # Cannon platform/base
    glColor3f(0.2, 0.2, 0.2)
    glPushMatrix()
    glScalef(3, 1.5, 0.3)
    glutSolidCube(60)
    glPopMatrix()

    # Support pillars
    glColor3f(0.3, 0.3, 0.3)
    positions = [(-40, -20, 10), (40, -20, 10), (-40, 20, 10), (40, 20, 10)]
    for px, py, pz in positions:
        glPushMatrix()
        glTranslatef(px, py, pz)
        glutSolidCylinder(8, 20, 6, 6)
        glPopMatrix()

    # Main turret base
    glTranslatef(0, 0, 25)
    glColor3f(0.4, 0.4, 0.4)
    glutSolidCylinder(35, 25, 8, 8)

    # Rotating turret
    glRotatef(cannon_rotation, 0, 0, 1)
    glTranslatef(0, 0, 25)
    glColor3f(0.5, 0.5, 0.5)

    # Turret housing
    glPushMatrix()
    glScalef(1.5, 2, 1)
    glutSolidCube(40)
    glPopMatrix()

    # Gun barrels (dual barrel like in image)
    glRotatef(-cannon_elevation, 1, 0, 0)

    # Left barrel
    glPushMatrix()
    glTranslatef(-15, 20, 0)
    glColor3f(0.3, 0.3, 0.3)
    glutSolidCylinder(6, 100, 8, 8)
    # Barrel tip
    glTranslatef(0, 0, 100)
    glColor3f(0.8, 0.6, 0.2)
    glutSolidCylinder(8, 5, 6, 6)
    glPopMatrix()

    # Right barrel
    glPushMatrix()
    glTranslatef(15, 20, 0)
    glColor3f(0.3, 0.3, 0.3)
    glutSolidCylinder(6, 100, 8, 8)
    # Barrel tip
    glTranslatef(0, 0, 100)
    glColor3f(0.8, 0.6, 0.2)
    glutSolidCylinder(8, 5, 6, 6)
    glPopMatrix()

    glPopMatrix()

def draw_enemies():
    for enemy in enemies:
        glPushMatrix()
        glTranslatef(enemy.x, enemy.y, enemy.z)

        if enemy.type == "bomber":
            # Draw bomber plane (like Apache helicopter from image)
            glRotatef(180, 0, 0, 1)  # Face toward cannon

            # Main fuselage
            glColor3f(0.2, 0.4, 0.2)  # Dark green military color
            glPushMatrix()
            glRotatef(90, 1, 0, 0)
            glutSolidCylinder(12, 80, 8, 8)
            glPopMatrix()

            # Cockpit
            glPushMatrix()
            glTranslatef(0, 30, 5)
            glColor3f(0.1, 0.1, 0.3)  # Dark blue glass
            glutSolidSphere(15, 8, 8)
            glPopMatrix()

            # Main rotor
            glPushMatrix()
            glTranslatef(0, 0, 25)
            glColor3f(0.3, 0.3, 0.3)
            glutSolidCylinder(3, 5, 6, 6)
            # Rotor blades
            glColor3f(0.7, 0.7, 0.7)
            glRotatef(enemy.time_alive * 720, 0, 0, 1)  # Fast spinning
            glBegin(GL_QUADS)
            glVertex3f(-60, -2, 5)
            glVertex3f(60, -2, 5)
            glVertex3f(60, 2, 5)
            glVertex3f(-60, 2, 5)
            glVertex3f(-2, -60, 5)
            glVertex3f(2, -60, 5)
            glVertex3f(2, 60, 5)
            glVertex3f(-2, 60, 5)
            glEnd()
            glPopMatrix()

            # Tail rotor
            glPushMatrix()
            glTranslatef(15, -35, 10)
            glRotatef(90, 1, 0, 0)
            glColor3f(0.3, 0.3, 0.3)
            glutSolidCylinder(2, 3, 6, 6)
            glRotatef(enemy.time_alive * 720, 0, 1, 0)
            glColor3f(0.7, 0.7, 0.7)
            glBegin(GL_QUADS)
            glVertex3f(-15, 3, -1)
            glVertex3f(15, 3, -1)
            glVertex3f(15, 3, 1)
            glVertex3f(-15, 3, 1)
            glEnd()
            glPopMatrix()

        else:  # drone
            # Draw military drone
            glRotatef(180, 0, 0, 1)  # Face toward cannon

            # Main body
            glColor3f(0.3, 0.3, 0.3)  # Dark gray military drone
            glPushMatrix()
            glScalef(1.5, 3, 0.8)
            glutSolidCube(15)
            glPopMatrix()

            # Wings
            glColor3f(0.4, 0.4, 0.4)
            glPushMatrix()
            glScalef(4, 0.3, 0.2)
            glutSolidCube(20)
            glPopMatrix()

            # Propeller
            glPushMatrix()
            glTranslatef(0, 20, 0)
            glColor3f(0.2, 0.2, 0.2)
            glutSolidCylinder(2, 8, 6, 6)
            glRotatef(enemy.time_alive * 1440, 0, 1, 0)  # Very fast spinning
            glColor3f(0.7, 0.7, 0.7)
            glBegin(GL_QUADS)
            glVertex3f(-25, 8, -1)
            glVertex3f(25, 8, -1)
            glVertex3f(25, 8, 1)
            glVertex3f(-25, 8, 1)
            glEnd()
            glPopMatrix()

            # Tail
            glPushMatrix()
            glTranslatef(0, -15, 5)
            glScalef(0.5, 1, 1.5)
            glutSolidCube(10)
            glPopMatrix()

        glPopMatrix()

def draw_bullets():
    # Draw tracer bullets with glowing effect
    for bullet in bullets:
        glPushMatrix()
        glTranslatef(bullet.x, bullet.y, bullet.z)

        # Different color for homing bullets in cheat mode
        if isinstance(bullet, HomingBullet):
            glColor3f(1, 0.2, 0.2)  # Red for cheat mode bullets
        else:
            glColor3f(1, 0.8, 0.2)  # Bright orange tracer effect
            
        glutSolidSphere(4, 6, 6)

        # Tracer trail effect
        if isinstance(bullet, HomingBullet):
            glColor3f(1, 0.2, 0.2)  # Red trail
        else:
            glColor3f(1, 0.5, 0)  # Orange trail
            
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(-bullet.vx * 0.02, -bullet.vy * 0.02, -bullet.vz * 0.02)
        glEnd()

        glPopMatrix()

def draw_explosions():
    for explosion in explosions:
        glPushMatrix()
        glTranslatef(explosion.x, explosion.y, explosion.z)

        # Multi-layered explosion effect
        glColor3f(1, 0.8, 0)  # Bright orange core
        glutSolidSphere(explosion.size * 0.6, 8, 8)

        glColor3f(1, 0.4, 0)  # Outer orange
        glutSolidSphere(explosion.size * 0.8, 8, 8)

        glColor3f(0.8, 0.2, 0)  # Red outer edge
        glutSolidSphere(explosion.size, 8, 8)

        # Explosion debris
        for i in range(8):
            angle = i * 45
            debris_x = explosion.size * 0.7 * math.cos(math.radians(angle))
            debris_y = explosion.size * 0.7 * math.sin(math.radians(angle))
            glPushMatrix()
            glTranslatef(debris_x, debris_y, random.uniform(-10, 10))
            glColor3f(0.9, 0.6, 0.1)
            glutSolidCube(4)
            glPopMatrix()

        glPopMatrix()

def draw_powerups():
    for powerup in powerups:
        glPushMatrix()
        glTranslatef(powerup.x, powerup.y, powerup.z)
        glRotatef(powerup.rotation, 0, 0, 1)

        if powerup.type == "double":
            glColor3f(0, 1, 0)  # Green
        elif powerup.type == "rapid":
            glColor3f(0, 0, 1)  # Blue
        else:  # shield
            glColor3f(1, 0, 1)  # Magenta

        glutSolidCube(powerup.size)
        glPopMatrix()

def calculate_barrel_position(barrel_offset):
    """Calculate the exact position of a barrel tip in world coordinates"""
    # Cannon base position (matching draw_cannon positioning)
    cannon_x, cannon_y, cannon_z = 0, -400, 50  # Base + turret height

    # Convert angles to radians
    rad_rot = math.radians(cannon_rotation)
    rad_elev = math.radians(cannon_elevation)

    # Apply transformations in the same order as draw_cannon():
    # 1. Start at turret center (after base translation and turret height)
    turret_center_x = cannon_x
    turret_center_y = cannon_y 
    turret_center_z = cannon_z

    # 2. Apply horizontal rotation around Z-axis
    # Barrel offset in rotated coordinate system (left/right of turret)
    rotated_offset_x = barrel_offset * math.cos(rad_rot + math.pi/2)
    rotated_offset_y = barrel_offset * math.sin(rad_rot + math.pi/2)

    # 3. Barrel forward position (20 units forward + 100 units barrel length)
    barrel_forward = 120  # 20 (turret forward) + 100 (barrel length)

    # Calculate barrel tip position accounting for both rotation and elevation
    barrel_tip_x = turret_center_x + rotated_offset_x + barrel_forward * math.sin(rad_rot) * math.cos(rad_elev)
    barrel_tip_y = turret_center_y + rotated_offset_y + barrel_forward * math.cos(rad_rot) * math.cos(rad_elev)
    barrel_tip_z = turret_center_z + barrel_forward * math.sin(rad_elev)

    return barrel_tip_x, barrel_tip_y, barrel_tip_z

def fire_bullet():
    current_time = time.time()

    # Rapid fire check
    fire_delay = 0.1 if rapid_fire else 0.3
    if hasattr(fire_bullet, 'last_time'):
        if current_time - fire_bullet.last_time < fire_delay:
            return
    fire_bullet.last_time = current_time

    speed = 500

    # angles (in radians) - we follow the same transform order used in draw_cannon:
    # glRotatef(cannon_rotation,0,0,1) then glRotatef(-cannon_elevation,1,0,0) etc.
    rot = math.radians(cannon_rotation)
    elev = math.radians(cannon_elevation)

    cos_r = math.cos(rot); sin_r = math.sin(rot)
    cos_e = math.cos(elev); sin_e = math.sin(elev)

    # geometry constants that match draw_cannon
    barrel_length = 100        # cylinder height used in drawing the barrel
    cannon_base_y = -400       # glTranslatef(0, -400, 0)
    # there are two +25 z translations in draw_cannon (one before and one after rotation),
    # we'll apply them below as T3 and T2 (both add +25 to Z)
    T_z_before_after = 25
    # actual local offsets used in draw_cannon for left/right barrel
    barrel_local_offsets = [(-15, 20), (15, 20)]

    def local_to_world(lx, ly, lz):
        """
        Apply the same sequence of transforms used in draw_cannon to a local point
        (lx, ly, lz) in barrel-local coordinates and return the world (x,y,z).
        Transform order (inner -> outer):
          1) T_tip  (local z translation by barrel length)
          2) T4     (local barrel offset: lx,ly,0)
          3) Rx(-e) (rotate about X by -elevation)
          4) T3     (add +25 in Z)
          5) Rz(rot) (rotate about Z by cannon_rotation)
          6) T2     (add +25 in Z)
          7) T1     (add (0,-400,0))
        """
        # Step A: point in barrel-local coordinates (already given as lx,ly,lz)

        # Step B: rotate about X by -elev (Rx(-e)):
        # Using rotation matrix around X:
        # x1 = lx
        # y1 = cos(-e)ly - sin(-e)lz  -> cos_ely + sin_elz  (since sin(-e) = -sin_e)
        # z1 = sin(-e)ly + cos(-e)lz  -> -sin_ely + cos_elz
        x1 = lx
        y1 = cos_e * ly + sin_e * lz
        z1 = -sin_e * ly + cos_e * lz

        # Step C: add the local +25 (T3)
        z1 += T_z_before_after

        # Step D: rotate about Z by rot (Rz(rot)):
        x2 = cos_r * x1 - sin_r * y1
        y2 = sin_r * x1 + cos_r * y1
        z2 = z1  # Z unaffected by Rz

        # Step E: add the outer +25 (T2)
        z2 += T_z_before_after

        # Step F: add base translation T1 (0, -400, 0)
        y2 += cannon_base_y

        return (x2, y2, z2)

    # For each barrel compute the world tip and a nearby base point -> direction = tip - base
    for lx, ly in barrel_local_offsets:
        tip_world = local_to_world(lx, ly, barrel_length)   # end of the cylinder
        base_world = local_to_world(lx, ly, 0)               # base of the cylinder (before tip)
        dx = tip_world[0] - base_world[0]
        dy = tip_world[1] - base_world[1]
        dz = tip_world[2] - base_world[2]
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        if dist < 1e-6:
            # fallback direction (shouldn't happen)
            dir_x, dir_y, dir_z = 0.0, 1.0, 0.0
        else:
            dir_x, dir_y, dir_z = dx/dist, dy/dist, dz/dist

        # bullet start = slightly in front of tip (use tip_world)
        start_x, start_y, start_z = tip_world

        vx = dir_x * speed
        vy = dir_y * speed
        vz = dir_z * speed

        bullets.append(Bullet(start_x, start_y, start_z, vx, vy, vz))

    # Double shot power-up: spawn small lateral spread bullets from center (optional)
    if double_shot:
        # center barrel local offset (mid between left/right)
        for i in range(2):
            spread = 10.0 * (i - 0.5)  # small left/right offset in local X
            lx = spread
            ly = 20
            tip_world = local_to_world(lx, ly, barrel_length)
            base_world = local_to_world(lx, ly, 0)
            dx = tip_world[0] - base_world[0]
            dy = tip_world[1] - base_world[1]
            dz = tip_world[2] - base_world[2]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            if dist < 1e-6:
                dir_x, dir_y, dir_z = 0.0, 1.0, 0.0
            else:
                dir_x, dir_y, dir_z = dx/dist, dy/dist, dz/dist
            bullets.append(Bullet(tip_world[0], tip_world[1], tip_world[2],
                                  dir_x*speed, dir_y*speed, dir_z*speed))

def spawn_enemy():
    global wave_enemies_spawned, last_enemy_spawn
    current_time = time.time()

    if wave_enemies_spawned < enemies_per_wave:
        if current_time - last_enemy_spawn > enemy_spawn_delay:
            enemy_type = "bomber" if random.random() < 0.3 else "drone"
            enemies.append(Enemy(enemy_type))
            wave_enemies_spawned += 1
            last_enemy_spawn = current_time

def spawn_powerup(x, y, z):
    if random.random() < 0.3:  # 30% chance
        ptype = random.choice(["double", "rapid", "shield"])
        powerups.append(PowerUp(x, y, z, ptype))

def check_collisions():
    global score, lives, consecutive_hits, last_hit_time

    # Bullet-enemy collisions
    for bullet in bullets[:]:
        for enemy in enemies[:]:
            dist = math.sqrt((bullet.x - enemy.x)**2 + 
                           (bullet.y - enemy.y)**2 + 
                           (bullet.z - enemy.z)**2)
            if dist < enemy.size:
                enemy.health -= 1
                if bullet in bullets:
                    bullets.remove(bullet)
                if enemy.health <= 0:
                    explosions.append(Explosion(enemy.x, enemy.y, enemy.z))
                    spawn_powerup(enemy.x, enemy.y, enemy.z)
                    score += 1
                    
                    # Update consecutive hits
                    current_time = time.time()
                    if current_time - last_hit_time > HIT_TIMEOUT:
                        consecutive_hits = 1
                    else:
                        consecutive_hits += 1
                    
                    last_hit_time = current_time
                    
                    # Award extra lives for 3 consecutive hits
                    if consecutive_hits % 3 == 0:
                        lives += 3
                    
                    enemies.remove(enemy)
                break

    # Player-powerup collisions (adjusted for cannon position)
    for powerup in powerups[:]:
        dist = math.sqrt(powerup.x**2 + (powerup.y + 400)**2 + powerup.z**2)
        if dist < 80:  # Close to cannon
            activate_powerup(powerup.type)
            powerups.remove(powerup)

def activate_powerup(ptype):
    global double_shot, rapid_fire, shield_active

    if ptype == "double":
        double_shot = True
        powerup_timers["double"] = time.time() + 10
    elif ptype == "rapid":
        rapid_fire = True
        powerup_timers["rapid"] = time.time() + 8
    elif ptype == "shield":
        shield_active = True
        powerup_timers["shield"] = time.time() + 15

def update_powerups():
    global double_shot, rapid_fire, shield_active
    current_time = time.time()

    if double_shot and current_time > powerup_timers["double"]:
        double_shot = False
    if rapid_fire and current_time > powerup_timers["rapid"]:
        rapid_fire = False
    if shield_active and current_time > powerup_timers["shield"]:
        shield_active = False

def cheat_mode_targeting():
    global cannon_rotation, cannon_elevation, auto_fire_timer

    if not enemies:
        return

    # Find nearest enemy
    nearest_enemy = None
    min_dist = float('inf')

    # Find nearest enemy (adjusted for cannon position)
    for enemy in enemies:
        dx = enemy.x
        dy = enemy.y + 400  # Adjust for cannon position
        dz = enemy.z
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        if dist < min_dist:
            min_dist = dist
            nearest_enemy = enemy

    if nearest_enemy:
        # Calculate angle to target (adjusted for cannon position)
        dx = nearest_enemy.x
        dy = nearest_enemy.y + 400  # Adjust for cannon position
        dz = nearest_enemy.z

        target_rotation = math.degrees(math.atan2(dx, dy))
        target_elevation = math.degrees(math.atan2(dz, math.sqrt(dx*dx + dy*dy)))

        cannon_rotation = target_rotation
        cannon_elevation = max(0, min(90, target_elevation))

        # Auto fire with homing bullets
        current_time = time.time()
        if current_time - auto_fire_timer > 0.2:
            # Use the same barrel position calculation as regular firing
            rot = math.radians(cannon_rotation)
            elev = math.radians(cannon_elevation)
            
            cos_r = math.cos(rot)
            sin_r = math.sin(rot)
            cos_e = math.cos(elev)
            sin_e = math.sin(elev)
            
            # Calculate barrel positions using the same method as fire_bullet()
            def local_to_world(lx, ly, lz):
                # Rotate about X by -elevation
                x1 = lx
                y1 = cos_e * ly + sin_e * lz
                z1 = -sin_e * ly + cos_e * lz
                
                # Add the local +25 (T3)
                z1 += 25
                
                # Rotate about Z by rotation
                x2 = cos_r * x1 - sin_r * y1
                y2 = sin_r * x1 + cos_r * y1
                z2 = z1
                
                # Add the outer +25 (T2)
                z2 += 25
                
                # Add base translation (0, -400, 0)
                y2 += -400
                
                return (x2, y2, z2)
            
            # Left barrel position
            left_tip = local_to_world(-15, 20, 100)
            # Right barrel position
            right_tip = local_to_world(15, 20, 100)
            
            # Create homing bullets from both barrels
            bullets.append(HomingBullet(left_tip[0], left_tip[1], left_tip[2], nearest_enemy))
            bullets.append(HomingBullet(right_tip[0], right_tip[1], right_tip[2], nearest_enemy))
            
            auto_fire_timer = current_time

def update_game(dt):
    global lives, game_over, wave_number, wave_enemies_spawned, cheat_cooldown, consecutive_hits, last_hit_time

    if game_over:
        return

    # Update consecutive hits timer
    current_time = time.time()
    if current_time - last_hit_time > HIT_TIMEOUT:
        consecutive_hits = 0

    # Update bullets
    for bullet in bullets[:]:
        bullet.update(dt)
        if not bullet.is_alive():
            bullets.remove(bullet)

    # Update enemies
    for enemy in enemies[:]:
        enemy.update(dt)
        if enemy.reached_ground():
            if not shield_active:
                lives -= 1
            enemies.remove(enemy)
            if lives <= 0:
                game_over = True
        elif not enemy.is_alive():
            enemies.remove(enemy)

    # Update explosions
    for explosion in explosions[:]:
        explosion.update(dt)
        if not explosion.is_alive():
            explosions.remove(explosion)

    # Update powerups
    for powerup in powerups[:]:
        powerup.update(dt)
        if not powerup.is_alive():
            powerups.remove(powerup)

    # Spawn enemies
    spawn_enemy()

    # Check for next wave
    if wave_enemies_spawned >= enemies_per_wave and not enemies:
        wave_number += 1
        wave_enemies_spawned = 0
        global enemy_spawn_delay
        enemy_spawn_delay = max(0.5, enemy_spawn_delay - 0.2)  # Faster spawning

    # Update cheat mode cooldown
    if cheat_cooldown > 0:
        cheat_cooldown -= dt

    # Cheat mode auto-targeting
    if cheat_mode and cheat_cooldown <= 0:
        cheat_mode_targeting()

    # Update power-ups
    update_powerups()

    # Check collisions
    check_collisions()

def reset_game():
    global score, lives, game_over, wave_number, wave_enemies_spawned
    global bullets, enemies, explosions, powerups
    global double_shot, rapid_fire, shield_active, cheat_mode
    global consecutive_hits, last_hit_time

    score = 0
    lives = 5  # Changed from 3 to 5
    game_over = False
    wave_number = 1
    wave_enemies_spawned = 0
    bullets.clear()
    enemies.clear()
    explosions.clear()
    powerups.clear()
    double_shot = False
    rapid_fire = False
    shield_active = False
    cheat_mode = False
    consecutive_hits = 0
    last_hit_time = 0

def keyboardListener(key, x, y):
    global cannon_rotation, cannon_elevation, cheat_mode, cheat_cooldown

    # Rotate cannon left (A key)
    if key == b'a':
        cannon_rotation += 5

    # Rotate cannon right (D key)
    if key == b'd':
        cannon_rotation -= 5

    # Aim up (W key)
    if key == b'w':
        cannon_elevation = max(0, cannon_elevation - 3)

    # Aim down (S key)
    if key == b's':
        cannon_elevation = min(90, cannon_elevation + 3)

    # Fire (Spacebar)
    if key == b' ':
        fire_bullet()

    # Toggle cheat mode (C key)
    if key == b'c':
        if cheat_cooldown <= 0:
            cheat_mode = not cheat_mode
            if cheat_mode:
                cheat_cooldown = 5.0  # 5 second duration

    # Reset game (R key)
    if key == b'r':
        reset_game()

def specialKeyListener(key, x, y):
    global camera_pos, cannon_rotation, cannon_elevation

    # Arrow keys for camera movement and cannon control
    x_pos, y_pos, z_pos = camera_pos

    if key == GLUT_KEY_UP:
        cannon_elevation = max(0, cannon_elevation - 3)
    elif key == GLUT_KEY_DOWN:
        cannon_elevation = min(90, cannon_elevation + 3)
    elif key == GLUT_KEY_LEFT:
        cannon_rotation += 5
    elif key == GLUT_KEY_RIGHT:
        cannon_rotation -= 5

    camera_pos = (x_pos, y_pos, z_pos)

def mouseListener(button, state, x, y):
    # Left mouse button fires
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        fire_bullet()

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.25, 0.1, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    x, y, z = camera_pos
    gluLookAt(x, y, z, 0, 0, 0, 0, 0, 1)

# Global timer for consistent frame timing
last_time = time.time()

def idle():
    global last_time
    current_time = time.time()
    dt = current_time - last_time
    last_time = current_time

    update_game(dt)
    glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    setupCamera()

    # Draw grid floor with battlefield texture
    glBegin(GL_QUADS)
    # Desert sand color like in the image
    glColor3f(0.8, 0.7, 0.5)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glEnd()

    # Draw grid lines for battlefield effect
    glColor3f(0.6, 0.5, 0.3)
    glBegin(GL_LINES)
    for i in range(-GRID_LENGTH, GRID_LENGTH + 1, 100):
        glVertex3f(i, -GRID_LENGTH, 1)
        glVertex3f(i, GRID_LENGTH, 1)
        glVertex3f(-GRID_LENGTH, i, 1)
        glVertex3f(GRID_LENGTH, i, 1)
    glEnd()

    # Draw game objects
    draw_cannon()
    draw_enemies()
    draw_bullets()
    draw_explosions()
    draw_powerups()

    # Draw shield effect (adjusted for cannon position) - without transparency
    if shield_active:
        glPushMatrix()
        glTranslatef(0, -400, 50)  # Position at cannon
        glColor3f(0, 1, 1)  # Solid cyan instead of transparent
        glutSolidSphere(100, 16, 16)
        glPopMatrix()

    # Draw UI
    draw_text(10, 770, f"Score: {score}")
    draw_text(10, 750, f"Lives: {lives}")
    draw_text(10, 730, f"Wave: {wave_number}")
    draw_text(10, 710, f"Enemies: {len(enemies)}")
    draw_text(10, 690, f"Consecutive Hits: {consecutive_hits}")

    # Power-up indicators
    y_offset = 670
    if double_shot:
        draw_text(10, y_offset, "DOUBLE SHOT!")
        y_offset -= 20
    if rapid_fire:
        draw_text(10, y_offset, "RAPID FIRE!")
        y_offset -= 20
    if shield_active:
        draw_text(10, y_offset, "SHIELD ACTIVE!")
        y_offset -= 20

    # Cheat mode indicator
    if cheat_mode:
        draw_text(400, 770, "AUTO LOCK-ON ACTIVE!")
    elif cheat_cooldown > 0:
        draw_text(400, 770, f"Cheat Cooldown: {cheat_cooldown:.1f}s")

    # Controls
    draw_text(10, 50, "A/D or ←/→: Rotate | W/S or ↑/↓: Aim | Space/Click: Fire")
    draw_text(10, 30, "C: Cheat Mode | R: Restart")

    if game_over:
        draw_text(400, 400, "GAME OVER!")
        draw_text(350, 380, f"Final Score: {score}")
        draw_text(350, 360, "Press R to restart")

    glutSwapBuffers()

def main():
    global last_time
    last_time = time.time()

    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)  # Double buffering, RGB color, depth test
    glutInitWindowSize(1000, 800)  # Window size
    glutInitWindowPosition(0, 0)  # Window position
    wind = glutCreateWindow(b"3D Anti-Aircraft Cannon Defense")

    # Depth testing is already enabled through GLUT_DEPTH in glutInitDisplayMode
    glClearColor(0.7, 0.8, 0.9, 1.0)  # Sky blue background like the image

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()