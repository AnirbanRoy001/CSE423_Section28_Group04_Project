from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import random
import math
import numpy as np
import time



# Game Starting
GAME_START = False
GAME_OPTION = 0  # 1=Hammer Havoc, 2=Maze Shooter, 3=Strike Planes

# Shared camera (menu / Game 1)
camera_pos = (0, 300, 650)
fovY = 130



# =====================================================================================
# =====================================================================================
# Game 1 : Hammer Havoc

GRID_LENGTH = 500
a = -GRID_LENGTH + GRID_LENGTH/6   # center of first cell
b = GRID_LENGTH/3                  # cell width

program_start_time = time.time()

# Enemy state
ex = a + b * int(random.randint(0, 5))
ey = a + b * int(random.randint(0, 5))

ENEMY_RADIUS = 50.0
color_changer = 0           # 0 => green, 1 => red
color_change_decider = 0
draw_r = 0.0                # current pulse radius

# Enemy spawn animation timer
SPAWN_TIME_TRACKER = 2500   # initial spawn period (ms units of random_var ticks)
spawn_time_tracker = SPAWN_TIME_TRACKER
PULSE_DECAY_STEP = 250
MIN_SPAWN_PERIOD = 400
random_var = 0
last_t = 0

# speed-up depending on score increase
speed_change_score = 0
SPEED_CHANGE_SCORE_LIMIT = 10

# Hammer state
hx = a
hy = -a
strike = 250
strike_rotate = 0
strike_direction = 1
hit = False
CELL_TOL  = 0.001

# Game state
LIFE_INIT = 5
MISSES_LIMIT = 10
score = 0
life = LIFE_INIT
misses = 0
game_over = False

# Combo & Bonus Round state
consecutive_green_hits = 0
in_bonus_round = False
BONUS_DURATION_MS = 10000
bonus_row_index = 0
bonus_end_time_ms = 0


# Game 1 functions

def check_same_cell():
    return (abs(ex - hx) < CELL_TOL) and (abs(ey - hy) < CELL_TOL)

def check_end_conditions():
    global game_over
    if life <= 0 or misses >= MISSES_LIMIT:
        game_over = True

def reset_game():
    global score, life, misses, game_over
    global ex, ey, hx, hy, strike, hit
    global spawn_time_tracker, random_var, last_t
    global color_changer, color_change_decider
    global consecutive_green_hits, in_bonus_round, bonus_end_time_ms
    global bonus_row_index, speed_change_score

    score = 0
    life = LIFE_INIT
    misses = 0
    game_over = False

    spawn_time_tracker = SPAWN_TIME_TRACKER
    random_var = 0
    last_t = 0

    hit = False
    strike = 250

    hx = a
    hy = -a

    consecutive_green_hits = 0
    in_bonus_round = False
    bonus_end_time_ms = 0
    bonus_row_index = 0

    speed_change_score = 0
    enemy_position()

def get_elapsed_time():
    return int((time.time() - program_start_time) * 1000)

def trigger_bonus_round():
    global in_bonus_round, bonus_end_time_ms, bonus_row_index
    global color_changer, ex, ey
    if in_bonus_round:
        return
    in_bonus_round = True
    now = glutGet(GLUT_ELAPSED_TIME)
    bonus_end_time_ms = now + BONUS_DURATION_MS
    bonus_row_index = random.randint(0, 5)
    color_changer = 0
    ey = a + b * bonus_row_index
    ex = a + b * random.randint(0, 5)

def end_bonus_round():
    global in_bonus_round, consecutive_green_hits
    in_bonus_round = False
    consecutive_green_hits = 0

def enemy_position():
    global ex, ey, color_changer, color_change_decider
    if in_bonus_round:
        color_changer = 0
        ey = a + b * bonus_row_index
        ex = a + b * int(random.randint(0, 5))
        return
    ex = a + b * int(random.randint(0, 5))
    ey = a + b * int(random.randint(0, 5))
    if color_change_decider % 2 == 0:
        color_changer = random.randint(0, 1)  # 0 green, 1 red
        color_change_decider = 0
    if color_changer == 1 and color_change_decider % 3 == 1:
        color_changer = 0
    color_change_decider += 1

# ----------------------------
# Game 1 rendering
# ----------------------------
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

def draw_hammer():
    global game_over
    glPushMatrix()
    glColor3f(0.2, 0.3, 0.3 if not game_over else 0)
    if game_over: glColor3f(1,0,0)
    glTranslatef(0, 0, 100); glRotatef(90, -1, 0, 0)
    gluCylinder(gluNewQuadric(), 20, 20, 250, 10, 10)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0.5, 0.3, 0.3 if not game_over else 0)
    if game_over: glColor3f(1,0,0)
    glTranslatef(0, 0, 100); glRotatef(90, -1, 0, 0)
    gluCylinder(gluNewQuadric(), 20, 20, 250, 10, 10)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0.5, 0, 0 if not game_over else 0)
    if game_over: glColor3f(1,0,0)
    glTranslatef(0, 250, 100); glRotatef(90, -1, 0, 0)
    glutSolidCube(30)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0, 0, 0 if not game_over else 0)
    if game_over: glColor3f(1,0,0)
    glTranslatef(0, 0, 100); glRotatef(90, -1, 0, 0)
    gluCylinder(gluNewQuadric(), 22, 22, 40, 10, 10)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 0)
    glColor3f(0.5, 0.25, 0.1 if not game_over else 0)
    if game_over: glColor3f(1,0,0)
    glutSolidCube(100)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 0)
    glColor3f(0.6, 0.35, 0.2 if not game_over else 0)
    if game_over: glColor3f(1,0,0)
    glScalef(2, 2, 2)
    gluCylinder(gluNewQuadric(), 25, 25, 100, 30, 10)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0.5, 0.25, 0.1 if not game_over else 0)
    if game_over: glColor3f(1,0,0)
    glTranslatef(0, 0, 185)
    glutSolidCube(100)
    glPopMatrix()

def draw_shadow():
    glPushMatrix()
    glTranslatef(0, 0, 0)
    glColor3f(1, 0.6, 0.6)
    gluCylinder(gluNewQuadric(), 50, 50, 10, 30, 10)
    glPopMatrix()

def drawEnemy():
    global draw_r
    period = max(spawn_time_tracker, 1)
    t = random_var % period
    half = period / 2.0
    s = t / half if t <= half else 2.0 - (t / half)
    s = max(0.0, min(1.0, s))
    draw_r = ENEMY_RADIUS * s
    base_color = [float(color_changer), float(1 - color_changer), 0.0]
    curr_color = [c * s for c in base_color]
    glPushMatrix()
    glTranslatef(ex, ey, 0)
    glScalef(1, 1, s)
    glColor3f(*curr_color)
    gluSphere(gluNewQuadric(), 50, 20, 10)
    glTranslatef(0, 0, ENEMY_RADIUS)
    glColor3f(0,0,0)
    gluSphere(gluNewQuadric(), 25, 20, 10)
    glPopMatrix()



# =====================================================================================
# =====================================================================================
# Game 2 : Maze Shooter

# Constants
MAZE_SIZE = 15
CELL_SIZE = 2.0
WALL_HEIGHT = 2.0
PLAYER_HEIGHT = 1.8
ENEMY_HEIGHT_2 = 1.5
BULLET_SPEED_2 = 0.2
ENEMY_SPEED_2 = 0.005
MAX_LIVES_2 = 5
MAX_MISSED_BULLETS_2 = 10

# State
playerLives2 = MAX_LIVES_2
score2 = 0
missedBullets2 = 0
gameOver2 = False
cheatMode2 = False
autoCamera2 = False
firstPersonView2 = False
topDownView2 = False

# Player
playerX2, playerY2, playerZ2 = 0.0, 0.0, PLAYER_HEIGHT / 2
playerAngle2 = 0.0
gunAngle2 = 0.0

# Camera
cameraX2, cameraY2, cameraZ2 = 0.0, 10.0, 10.0
cameraAngleX2, cameraAngleY2 = -30.0, 0.0

# Cheat mode helpers
cheatShootTimer2 = 0
cheatShootInterval2 = 5
cheatRotationAngle2 = 0

# Maze Definition (1 = wall, 0 = path, 2 = door)
maze = [
 [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
 [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
 [1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1],
 [1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 1],
 [1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 0, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1],
 [1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 0, 1],
 [1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
 [1, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1],
 [1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
 [1, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1],
 [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1],
 [1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1],
 [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1],
 [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
]

class Enemy2:
    def __init__(self, x, y):
        self.x = x; self.y = y; self.z = 0.0
        self.breathPhase = random.random() * math.pi * 2
        self.alive = True
        self.respawnTimer = 0
    def update(self, targetX, targetY):
        if not self.alive:
            self.respawnTimer += 1
            if self.respawnTimer > 300:
                self.respawn()
            return
        if cheatMode2: return
        dx = targetX - self.x; dy = targetY - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 0.1:
            self.x += (dx / dist) * ENEMY_SPEED_2
            self.y += (dy / dist) * ENEMY_SPEED_2
        self.breathPhase += 0.05
    def respawn(self):
        while True:
            x = random.randint(1, MAZE_SIZE-2)
            y = random.randint(1, MAZE_SIZE-2)
            if maze[x][y] == 0:
                self.x = x * CELL_SIZE - (MAZE_SIZE * CELL_SIZE / 2) + CELL_SIZE/2
                self.y = y * CELL_SIZE - (MAZE_SIZE * CELL_SIZE / 2) + CELL_SIZE/2
                self.alive = True
                self.respawnTimer = 0
                break

class Bullet2:
    def __init__(self, x, y, z, angle):
        self.x = x; self.y = y; self.z = z
        self.angle = angle
        self.active = True
    def update(self):
        self.x += math.sin(math.radians(self.angle)) * BULLET_SPEED_2
        self.y += math.cos(math.radians(self.angle)) * BULLET_SPEED_2
        max_dist = MAZE_SIZE * CELL_SIZE
        if (abs(self.x) > max_dist or abs(self.y) > max_dist):
            self.active = False
            global missedBullets2
            missedBullets2 += 1

enemies2 = []
for i in range(5):
    while True:
        x = random.randint(1, MAZE_SIZE-2)
        y = random.randint(1, MAZE_SIZE-2)
        if maze[x][y] == 0:
            enemies2.append(Enemy2(
                x * CELL_SIZE - (MAZE_SIZE * CELL_SIZE / 2) + CELL_SIZE/2,
                y * CELL_SIZE - (MAZE_SIZE * CELL_SIZE / 2) + CELL_SIZE/2
            ))
            break

bullets2 = []

def calculate_lighting2(x, y, z, base_color):
    dx = x - playerX2; dy = y - playerY2; dz = z - playerZ2
    distance = math.sqrt(dx*dx + dy*dy + dz*dz)
    intensity = max(0.3, 1.0 - distance / 30.0)
    r = base_color[0] * intensity
    g = base_color[1] * intensity
    b = base_color[2] * intensity
    return (r, g, b)

def draw_brick_texture2(x, y, z, width, height, depth, base_color):
    lit_color = calculate_lighting2(x, y, z, base_color)
    glColor3f(*lit_color)
    glPushMatrix(); glTranslatef(x, y, z); glScalef(width, depth, height); glutSolidCube(1.0); glPopMatrix()
    brick_width = width / 4; brick_height = height / 8
    glColor3f(lit_color[0]*0.7, lit_color[1]*0.7, lit_color[2]*0.7)
    glBegin(GL_LINES)
    for i in range(1, 8):
        z_pos = z - height/2 + i * brick_height
        glVertex3f(x - width/2, y, z_pos); glVertex3f(x + width/2, y, z_pos)
    for i in range(5):
        x_pos = x - width/2 + i * brick_width
        offset = 0 if i % 2 == 0 else brick_height/2
        glVertex3f(x_pos, y, z - height/2 + offset)
        glVertex3f(x_pos, y, z + height/2 - (brick_height/2 if i % 2 == 1 else 0))
    glEnd()

def draw_floor2():
    lit_color = calculate_lighting2(0, 0, 0, (0.0, 0.6, 0.0))
    glColor3f(*lit_color)
    size = MAZE_SIZE * CELL_SIZE / 2
    glBegin(GL_QUADS)
    glVertex3f(-size, -size, 0.0); glVertex3f(size, -size, 0.0)
    glVertex3f(size, size, 0.0); glVertex3f(-size, size, 0.0)
    glEnd()

def draw_walls2():
    half_size = MAZE_SIZE * CELL_SIZE / 2
    for i in range(MAZE_SIZE):
        for j in range(MAZE_SIZE):
            x = i * CELL_SIZE - half_size
            y = j * CELL_SIZE - half_size
            if maze[i][j] == 1:
                draw_brick_texture2(x + CELL_SIZE/2, y + CELL_SIZE/2, WALL_HEIGHT/2,
                                    CELL_SIZE, WALL_HEIGHT, CELL_SIZE, (0.5, 0.3, 0.1))
            elif maze[i][j] == 2:
                lit_color = calculate_lighting2(x + CELL_SIZE/2, y + CELL_SIZE/2, WALL_HEIGHT/2, (0.6, 0.4, 0.2))
                glColor3f(*lit_color)
                glPushMatrix(); glTranslatef(x + CELL_SIZE/2, y + CELL_SIZE/2, WALL_HEIGHT/2)
                glScalef(CELL_SIZE, CELL_SIZE, WALL_HEIGHT); glutSolidCube(1.0); glPopMatrix()

def draw_player2():
    lit = calculate_lighting2(playerX2, playerY2, playerZ2, (1.0,1.0,1.0))
    glPushMatrix(); glTranslatef(playerX2, playerY2, playerZ2); glRotatef(playerAngle2, 0,0,1)
    glPushMatrix(); glTranslatef(0,0,0.7); glColor3f(lit[0]*1.0, lit[1]*0.8, lit[2]*0.6); glutSolidSphere(0.2,20,20); glPopMatrix()
    glPushMatrix(); glTranslatef(0,0,0.35); glScalef(0.4,0.3,0.7); glColor3f(lit[0]*0.0, lit[1]*0.0, lit[2]*1.0); glutSolidCube(1.0); glPopMatrix()
    glPushMatrix(); glTranslatef(0.25,0,0.4); glRotatef(90,0,1,0); glColor3f(lit[0]*0.0, lit[1]*0.0, lit[2]*1.0); glutSolidCylinder(0.07,0.4,20,20); glPopMatrix()
    glPushMatrix(); glTranslatef(-0.25,0,0.4); glRotatef(90,0,1,0); glutSolidCylinder(0.07,0.4,20,20); glPopMatrix()
    glPushMatrix(); glTranslatef(0.1,0,-0.1); glRotatef(90,1,0,0); glColor3f(lit[0]*0.5,lit[1]*0.5,lit[2]*0.5); glutSolidCylinder(0.08,0.4,20,20); glPopMatrix()
    glPushMatrix(); glTranslatef(-0.1,0,-0.1); glRotatef(90,1,0,0); glutSolidCylinder(0.03,0.2,20,20); glPopMatrix()
    glPushMatrix(); glTranslatef(0.3,0,0.5); glRotatef(gunAngle2,0,0,1)
    glPushMatrix(); glTranslatef(0.1,0,0); glScalef(0.2,0.1,0.1); glColor3f(lit[0]*0.2,lit[1]*0.2,lit[2]*0.2); glutSolidCube(1.0); glPopMatrix()
    glPushMatrix(); glTranslatef(0.2,0,0); glRotatef(90,0,1,0); glutSolidCylinder(0.03,0.2,20,20); glPopMatrix()
    glPopMatrix(); glPopMatrix()

def draw_enemies2():
    for enemy in enemies2:
        if not enemy.alive: continue
        lit = calculate_lighting2(enemy.x, enemy.y, enemy.z, (1.0,1.0,1.0))
        glPushMatrix(); glTranslatef(enemy.x, enemy.y, enemy.z)
        if cheatMode2: glColor3f(lit[0]*0.0, lit[1]*0.0, lit[2]*1.0)
        else: glColor3f(lit[0]*1.0, lit[1]*0.0, lit[2]*0.0)
        breath = 0.9 + 0.1 * math.sin(enemy.breathPhase)
        glPushMatrix(); glTranslatef(0,0,0.5); glScalef(1,1,breath); glutSolidSphere(0.3,20,20); glPopMatrix()
        glPushMatrix(); glTranslatef(0,0,1.0); glScalef(0.7,0.7,breath); glutSolidSphere(0.2,20,20); glPopMatrix()
        glPopMatrix()

def draw_bullets2():
    for bullet in bullets2:
        if bullet.active:
            lit = calculate_lighting2(bullet.x, bullet.y, bullet.z, (1.0,1.0,0.0))
            glColor3f(*lit)
            glPushMatrix(); glTranslatef(bullet.x, bullet.y, bullet.z); glutSolidCube(0.1); glPopMatrix()

def draw_crosshair2():
    glMatrixMode(GL_PROJECTION); glPushMatrix(); glLoadIdentity(); gluOrtho2D(0,1000,0,800)
    glMatrixMode(GL_MODELVIEW); glPushMatrix(); glLoadIdentity()
    cx, cy, size, thick = 500, 400, 10, 2
    glColor3f(1,0,0); glLineWidth(thick)
    glBegin(GL_LINES)
    glVertex2f(cx-size, cy); glVertex2f(cx+size, cy)
    glVertex2f(cx, cy-size); glVertex2f(cx, cy+size)
    glEnd()
    glPopMatrix(); glMatrixMode(GL_PROJECTION); glPopMatrix(); glMatrixMode(GL_MODELVIEW)

def draw_gun_sight2():
    dx = math.sin(math.radians(playerAngle2 + gunAngle2))
    dy = math.cos(math.radians(playerAngle2 + gunAngle2))
    gun_off_x = 0.3 * math.sin(math.radians(playerAngle2))
    gun_off_y = 0.3 * math.cos(math.radians(playerAngle2))
    barrel_off_x = 0.2 * math.sin(math.radians(playerAngle2 + gunAngle2))
    barrel_off_y = 0.2 * math.cos(math.radians(playerAngle2 + gunAngle2))
    tot_x = gun_off_x + barrel_off_x; tot_y = gun_off_y + barrel_off_y
    sx = playerX2 + tot_x; sy = playerY2 + tot_y; sz = playerZ2 + 0.5
    glColor3f(1,0,0); glLineWidth(2.0)
    glBegin(GL_LINES); glVertex3f(sx,sy,sz); glVertex3f(sx+dx*5, sy+dy*5, sz); glEnd()
    glPushMatrix(); glTranslatef(sx,sy,sz); glColor3f(1,0,0); glutSolidSphere(0.05,10,10); glPopMatrix()

def draw_hud2():
    glColor3f(1,1,1)
    draw_text(10, 770, f"Lives: {playerLives2}  Score: {score2}  Missed: {missedBullets2}/10")
    if gameOver2: draw_text(300, 400, "GAME OVER - Press R to restart")
    if cheatMode2: draw_text(10, 750, "CHEAT MODE ACTIVE - Enemies Frozen")
    if firstPersonView2: draw_text(10, 730, "FIRST PERSON VIEW")
    if topDownView2: draw_text(10, 710, "TOP DOWN VIEW")

def check_collision2(x, y):
    half = MAZE_SIZE * CELL_SIZE / 2
    gx = int((x + half) / CELL_SIZE); gy = int((y + half) / CELL_SIZE)
    if (gx < 0 or gx >= MAZE_SIZE or gy < 0 or gy >= MAZE_SIZE or maze[gx][gy] == 1):
        return True
    return False

def check_bullet_enemy_collision2():
    global score2
    for bullet in bullets2:
        if not bullet.active: continue
        for enemy in enemies2:
            if not enemy.alive: continue
            dx = bullet.x - enemy.x; dy = bullet.y - enemy.y
            if math.sqrt(dx*dx + dy*dy) < 0.5:
                bullet.active = False
                enemy.alive = False
                score2 += 10

def check_enemy_player_collision2():
    global playerLives2, gameOver2
    if cheatMode2: return
    for enemy in enemies2:
        if not enemy.alive: continue
        dx = playerX2 - enemy.x; dy = playerY2 - enemy.y
        if math.sqrt(dx*dx + dy*dy) < 0.8:
            enemy.alive = False
            playerLives2 -= 1
            if playerLives2 <= 0:
                gameOver2 = True

def update_game2():
    global missedBullets2, gameOver2
    if gameOver2: return
    for enemy in enemies2:
        enemy.update(playerX2, playerY2)
    for bullet in bullets2[:]:
        bullet.update()
        if not bullet.active:
            bullets2.remove(bullet)
    check_bullet_enemy_collision2()
    check_enemy_player_collision2()
    if missedBullets2 >= MAX_MISSED_BULLETS_2:
        gameOver2 = True

def fire_bullet2():
    gun_off_x = 0.3 * math.sin(math.radians(playerAngle2))
    gun_off_y = 0.3 * math.cos(math.radians(playerAngle2))
    barrel_off_x = 0.2 * math.sin(math.radians(playerAngle2 + gunAngle2))
    barrel_off_y = 0.2 * math.cos(math.radians(playerAngle2 + gunAngle2))
    gx = playerX2 + gun_off_x + barrel_off_x
    gy = playerY2 + gun_off_y + barrel_off_y
    gz = playerZ2 + 0.5
    angle = playerAngle2 + gunAngle2
    bullets2.append(Bullet2(gx, gy, gz, angle))

def fire_bullet_angle2(angle):
    gun_off_x = 0.3 * math.sin(math.radians(playerAngle2))
    gun_off_y = 0.3 * math.cos(math.radians(playerAngle2))
    gx = playerX2 + gun_off_x; gy = playerY2 + gun_off_y; gz = playerZ2 + 0.5
    bullets2.append(Bullet2(gx, gy, gz, angle))

def restart_game2():
    global playerLives2, score2, missedBullets2, gameOver2
    global firstPersonView2, topDownView2, cheatMode2
    global cheatShootTimer2, cheatRotationAngle2
    global playerX2, playerY2, playerZ2, playerAngle2, gunAngle2
    global enemies2, bullets2
    playerLives2 = MAX_LIVES_2; score2 = 0; missedBullets2 = 0; gameOver2 = False
    firstPersonView2 = False; topDownView2 = False; cheatMode2 = False
    cheatShootTimer2 = 0; cheatRotationAngle2 = 0
    playerX2, playerY2, playerZ2 = 0.0, 0.0, PLAYER_HEIGHT / 2
    playerAngle2 = 0.0; gunAngle2 = 0.0
    enemies2 = []
    for i in range(5):
        while True:
            x = random.randint(1, MAZE_SIZE-2)
            y = random.randint(1, MAZE_SIZE-2)
            if maze[x][y] == 0:
                enemies2.append(Enemy2(
                    x * CELL_SIZE - (MAZE_SIZE * CELL_SIZE / 2) + CELL_SIZE/2,
                    y * CELL_SIZE - (MAZE_SIZE * CELL_SIZE / 2) + CELL_SIZE/2
                ))
                break
    bullets2 = []



# =====================================================================================
# =====================================================================================

# Game 3 : Strike Planes

# Camera / grid
camera_pos3 = (0, -800, 300)
fovY3 = 120
GRID_LENGTH3 = 600

# State
cannon_rotation = 0
cannon_elevation = 45
bullets3 = []
enemies3 = []
explosions3 = []
powerups3 = []
score3 = 0
lives3 = 5
game_over3 = False
wave_number3 = 1
last_enemy_spawn3 = 0
enemy_spawn_delay3 = 2.0
wave_enemies_spawned3 = 0
enemies_per_wave3 = 5

# Cheat / powerups
cheat_mode3 = False
cheat_cooldown3 = 0
auto_fire_timer3 = 0
double_shot3 = False
rapid_fire3 = False
shield_active3 = False
powerup_timers3 = {"double": 0, "rapid": 0, "shield": 0}

consecutive_hits3 = 0
last_hit_time3 = 0
HIT_TIMEOUT3 = 3.0

class HomingBullet3:
    def __init__(self, x, y, z, target_enemy):
        self.x, self.y, self.z = x, y, z
        self.target = target_enemy
        self.speed = 600
        self.life = 5.0
        self.vx, self.vy, self.vz = 0, 0, 0
    def update(self, dt):
        if self.target and self.target in enemies3:
            dx = self.target.x - self.x; dy = self.target.y - self.y; dz = self.target.z - self.z
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            if dist > 0:
                self.vx = (dx / dist) * self.speed
                self.vy = (dy / dist) * self.speed
                self.vz = (dz / dist) * self.speed
            self.x += self.vx * dt; self.y += self.vy * dt; self.z += self.vz * dt
        else:
            self.x += self.vx * dt; self.y += self.vy * dt; self.z += self.vz * dt
        self.life -= dt
    def is_alive(self):
        return self.life > 0 and self.z >= 0

class Bullet3:
    def __init__(self, x, y, z, vx, vy, vz):
        self.x, self.y, self.z = x, y, z
        self.vx, self.vy, self.vz = vx, vy, vz
        self.life = 3.0
    def update(self, dt):
        self.x += self.vx * dt; self.y += self.vy * dt; self.z += self.vz * dt
        self.life -= dt
    def is_alive(self):
        return self.life > 0 and self.z >= 0

class Enemy3:
    def __init__(self, enemy_type="drone"):
        self.type = enemy_type
        if enemy_type == "bomber":
            self.size = 40; self.speed = 50 + wave_number3 * 5; self.health = 3
        else:
            self.size = 20; self.speed = 80 + wave_number3 * 10; self.health = 1
        self.x = random.uniform(-300, 300)
        self.y = 500
        self.z = random.uniform(200, 600)
        self.movement_type = random.choice(["straight", "zigzag", "curve"])
        self.time_alive = 0; self.amplitude = random.uniform(50, 150)
    def update(self, dt):
        self.time_alive += dt
        self.y -= self.speed * dt
        if self.movement_type == "zigzag":
            self.x += math.sin(self.time_alive * 3) * self.amplitude * dt
        elif self.movement_type == "curve":
            self.x += math.sin(self.time_alive * 2) * self.amplitude * dt
            self.z += math.cos(self.time_alive * 1.5) * 30 * dt
    def is_alive(self):
        return self.z > -50 and self.health > 0
    def reached_ground(self):
        return self.y <= -500

class Explosion3:
    def __init__(self, x, y, z):
        self.x, self.y, self.z = x, y, z
        self.size = 0; self.max_size = 50; self.life = 0.5
    def update(self, dt):
        self.life -= dt
        self.size = self.max_size * (1 - self.life / 0.5)
    def is_alive(self):
        return self.life > 0

class PowerUp3:
    def __init__(self, x, y, z, ptype):
        self.x, self.y, self.z = x, y, z
        self.type = ptype; self.size = 15; self.rotation = 0
    def update(self, dt):
        self.z -= 30 * dt; self.rotation += 180 * dt
    def is_alive(self):
        return self.z > 0

def draw_cannon3():
    glPushMatrix()
    glTranslatef(0, -400, 0)
    glColor3f(0.2,0.2,0.2); glPushMatrix(); glScalef(3,1.5,0.3); glutSolidCube(60); glPopMatrix()
    glColor3f(0.3,0.3,0.3)
    for px,py,pz in [(-40,-20,10),(40,-20,10),(-40,20,10),(40,20,10)]:
        glPushMatrix(); glTranslatef(px,py,pz); glutSolidCylinder(8,20,6,6); glPopMatrix()
    glTranslatef(0,0,25); glColor3f(0.4,0.4,0.4); glutSolidCylinder(35,25,8,8)
    glRotatef(cannon_rotation,0,0,1); glTranslatef(0,0,25); glColor3f(0.5,0.5,0.5)
    glPushMatrix(); glScalef(1.5,2,1); glutSolidCube(40); glPopMatrix()
    glRotatef(-cannon_elevation,1,0,0)
    # Left barrel
    glPushMatrix(); glTranslatef(-15,20,0); glColor3f(0.3,0.3,0.3); glutSolidCylinder(6,100,8,8)
    glTranslatef(0,0,100); glColor3f(0.8,0.6,0.2); glutSolidCylinder(8,5,6,6); glPopMatrix()
    # Right barrel
    glPushMatrix(); glTranslatef(15,20,0); glColor3f(0.3,0.3,0.3); glutSolidCylinder(6,100,8,8)
    glTranslatef(0,0,100); glColor3f(0.8,0.6,0.2); glutSolidCylinder(8,5,6,6); glPopMatrix()
    glPopMatrix()

def draw_enemies3():
    for enemy in enemies3:
        glPushMatrix(); glTranslatef(enemy.x, enemy.y, enemy.z)
        if enemy.type == "bomber":
            glRotatef(180,0,0,1)
            glColor3f(0.2,0.4,0.2)
            glPushMatrix(); glRotatef(90,1,0,0); glutSolidCylinder(12,80,8,8); glPopMatrix()
            glPushMatrix(); glTranslatef(0,30,5); glColor3f(0.1,0.1,0.3); glutSolidSphere(15,8,8); glPopMatrix()
            glPushMatrix(); glTranslatef(0,0,25); glColor3f(0.3,0.3,0.3); glutSolidCylinder(3,5,6,6)
            glColor3f(0.7,0.7,0.7); glRotatef(enemy.time_alive*720,0,0,1)
            glBegin(GL_QUADS)
            glVertex3f(-60,-2,5); glVertex3f(60,-2,5); glVertex3f(60,2,5); glVertex3f(-60,2,5)
            glVertex3f(-2,-60,5); glVertex3f(2,-60,5); glVertex3f(2,60,5); glVertex3f(-2,60,5)
            glEnd(); glPopMatrix()
            glPushMatrix(); glTranslatef(15,-35,10); glRotatef(90,1,0,0); glColor3f(0.3,0.3,0.3)
            glutSolidCylinder(2,3,6,6); glRotatef(enemy.time_alive*720,0,1,0); glColor3f(0.7,0.7,0.7)
            glBegin(GL_QUADS)
            glVertex3f(-15,3,-1); glVertex3f(15,3,-1); glVertex3f(15,3,1); glVertex3f(-15,3,1)
            glEnd(); glPopMatrix()
        else:
            glRotatef(180,0,0,1)
            glColor3f(0.3,0.3,0.3)
            glPushMatrix(); glScalef(1.5,3,0.8); glutSolidCube(15); glPopMatrix()
            glColor3f(0.4,0.4,0.4); glPushMatrix(); glScalef(4,0.3,0.2); glutSolidCube(20); glPopMatrix()
            glPushMatrix(); glTranslatef(0,20,0); glColor3f(0.2,0.2,0.2); glutSolidCylinder(2,8,6,6)
            glRotatef(enemy.time_alive*1440,0,1,0); glColor3f(0.7,0.7,0.7)
            glBegin(GL_QUADS)
            glVertex3f(-25,8,-1); glVertex3f(25,8,-1); glVertex3f(25,8,1); glVertex3f(-25,8,1)
            glEnd(); glPopMatrix()
            glPushMatrix(); glTranslatef(0,-15,5); glScalef(0.5,1,1.5); glutSolidCube(10); glPopMatrix()
        glPopMatrix()

def draw_bullets3():
    for bullet in bullets3:
        glPushMatrix(); glTranslatef(bullet.x, bullet.y, bullet.z)
        if isinstance(bullet, HomingBullet3): glColor3f(1,0.2,0.2)
        else: glColor3f(1,0.8,0.2)
        glutSolidSphere(4,6,6)
        if isinstance(bullet, HomingBullet3): glColor3f(1,0.2,0.2)
        else: glColor3f(1,0.5,0)
        glBegin(GL_LINES)
        glVertex3f(0,0,0); glVertex3f(-getattr(bullet,'vx',0)*0.02, -getattr(bullet,'vy',0)*0.02, -getattr(bullet,'vz',0)*0.02)
        glEnd()
        glPopMatrix()

def draw_explosions3():
    for ex3 in explosions3:
        glPushMatrix(); glTranslatef(ex3.x, ex3.y, ex3.z)
        glColor3f(1,0.8,0); glutSolidSphere(ex3.size*0.6,8,8)
        glColor3f(1,0.4,0); glutSolidSphere(ex3.size*0.8,8,8)
        glColor3f(0.8,0.2,0); glutSolidSphere(ex3.size,8,8)
        for i in range(8):
            ang = i*45; dx = ex3.size*0.7*math.cos(math.radians(ang)); dy = ex3.size*0.7*math.sin(math.radians(ang))
            glPushMatrix(); glTranslatef(dx,dy,random.uniform(-10,10)); glColor3f(0.9,0.6,0.1); glutSolidCube(4); glPopMatrix()
        glPopMatrix()

def draw_powerups3():
    for p in powerups3:
        glPushMatrix(); glTranslatef(p.x,p.y,p.z); glRotatef(p.rotation,0,0,1)
        if p.type == "double": glColor3f(0,1,0)
        elif p.type == "rapid": glColor3f(0,0,1)
        else: glColor3f(1,0,1)
        glutSolidCube(p.size); glPopMatrix()

def fire_bullet3():
    current_time = time.time()
    fire_delay = 0.1 if rapid_fire3 else 0.3
    if hasattr(fire_bullet3, 'last_time'):
        if current_time - fire_bullet3.last_time < fire_delay:
            return
    fire_bullet3.last_time = current_time

    speed = 500
    rot = math.radians(cannon_rotation)
    elev = math.radians(cannon_elevation)
    cos_r = math.cos(rot); sin_r = math.sin(rot)
    cos_e = math.cos(elev); sin_e = math.sin(elev)

    barrel_length = 100
    cannon_base_y = -400
    Tz = 25
    barrel_offsets = [(-15, 20), (15, 20)]

    def local_to_world(lx, ly, lz):
        x1 = lx
        y1 = cos_e * ly + sin_e * lz
        z1 = -sin_e * ly + cos_e * lz
        z1 += Tz
        x2 = cos_r * x1 - sin_r * y1
        y2 = sin_r * x1 + cos_r * y1
        z2 = z1
        z2 += Tz
        y2 += cannon_base_y
        return (x2, y2, z2)

    for lx, ly in barrel_offsets:
        tip = local_to_world(lx, ly, barrel_length)
        base = local_to_world(lx, ly, 0)
        dx = tip[0]-base[0]; dy = tip[1]-base[1]; dz = tip[2]-base[2]
        dist = math.sqrt(dx*dx + dy*dy + dz*dz) or 1.0
        dirx, diry, dirz = dx/dist, dy/dist, dz/dist
        bullets3.append(Bullet3(tip[0], tip[1], tip[2], dirx*speed, diry*speed, dirz*speed))

    if double_shot3:
        for i in range(2):
            spread = 10.0*(i-0.5); lx = spread; ly = 20
            tip = local_to_world(lx, ly, barrel_length); base = local_to_world(lx, ly, 0)
            dx = tip[0]-base[0]; dy = tip[1]-base[1]; dz = tip[2]-base[2]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz) or 1.0
            dirx, diry, dirz = dx/dist, dy/dist, dz/dist
            bullets3.append(Bullet3(tip[0], tip[1], tip[2], dirx*speed, diry*speed, dirz*speed))

def spawn_enemy3():
    global wave_enemies_spawned3, last_enemy_spawn3
    now = time.time()
    if wave_enemies_spawned3 < enemies_per_wave3:
        if now - last_enemy_spawn3 > enemy_spawn_delay3:
            etype = "bomber" if random.random() < 0.3 else "drone"
            enemies3.append(Enemy3(etype))
            wave_enemies_spawned3 += 1
            last_enemy_spawn3 = now

def spawn_powerup3(x,y,z):
    if random.random() < 0.3:
        ptype = random.choice(["double","rapid","shield"])
        powerups3.append(PowerUp3(x,y,z,ptype))

def check_collisions3():
    global score3, lives3, consecutive_hits3, last_hit_time3
    for b in bullets3[:]:
        for e in enemies3[:]:
            dist = math.sqrt((b.x-e.x)**2 + (b.y-e.y)**2 + (b.z-e.z)**2)
            if dist < e.size:
                e.health -= 1
                if b in bullets3: bullets3.remove(b)
                if e.health <= 0:
                    explosions3.append(Explosion3(e.x,e.y,e.z))
                    spawn_powerup3(e.x,e.y,e.z)
                    score3 += 1
                    now = time.time()
                    if now - last_hit_time3 > HIT_TIMEOUT3:
                        consecutive_hits3 = 1
                    else:
                        consecutive_hits3 += 1
                    last_hit_time3 = now
                    if consecutive_hits3 % 3 == 0:
                        lives3 += 3
                    enemies3.remove(e)
                break
    for p in powerups3[:]:
        dist = math.sqrt(p.x**2 + (p.y+400)**2 + p.z**2)
        if dist < 80:
            activate_powerup3(p.type)
            powerups3.remove(p)

def activate_powerup3(ptype):
    global double_shot3, rapid_fire3, shield_active3
    if ptype == "double":
        double_shot3 = True; powerup_timers3["double"] = time.time() + 10
    elif ptype == "rapid":
        rapid_fire3 = True; powerup_timers3["rapid"] = time.time() + 8
    elif ptype == "shield":
        shield_active3 = True; powerup_timers3["shield"] = time.time() + 15

def update_powerups3():
    global double_shot3, rapid_fire3, shield_active3
    now = time.time()
    if double_shot3 and now > powerup_timers3["double"]: double_shot3 = False
    if rapid_fire3 and now > powerup_timers3["rapid"]: rapid_fire3 = False
    if shield_active3 and now > powerup_timers3["shield"]: shield_active3 = False

def cheat_mode_targeting3():
    global cannon_rotation, cannon_elevation, auto_fire_timer3
    if not enemies3: return
    nearest = None; mind = 1e18
    for e in enemies3:
        dx, dy, dz = e.x, e.y + 400, e.z
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        if dist < mind: mind = dist; nearest = e
    if nearest:
        dx, dy, dz = nearest.x, nearest.y + 400, nearest.z
        cannon_rotation = math.degrees(math.atan2(dx, dy))
        cannon_elevation = max(0, min(90, math.degrees(math.atan2(dz, math.sqrt(dx*dx + dy*dy)))))
        now = time.time()
        if now - auto_fire_timer3 > 0.2:
            rot = math.radians(cannon_rotation); elev = math.radians(cannon_elevation)
            cos_r = math.cos(rot); sin_r = math.sin(rot); cos_e = math.cos(elev); sin_e = math.sin(elev)
            def local_to_world(lx, ly, lz):
                x1 = lx; y1 = cos_e*ly + sin_e*lz; z1 = -sin_e*ly + cos_e*lz
                z1 += 25
                x2 = cos_r*x1 - sin_r*y1; y2 = sin_r*x1 + cos_r*y1; z2 = z1
                z2 += 25; y2 += -400
                return (x2,y2,z2)
            left_tip = local_to_world(-15,20,100)
            right_tip = local_to_world(15,20,100)
            bullets3.append(HomingBullet3(left_tip[0], left_tip[1], left_tip[2], nearest))
            bullets3.append(HomingBullet3(right_tip[0], right_tip[1], right_tip[2], nearest))
            auto_fire_timer3 = now

def update_game3(dt):
    global lives3, game_over3, wave_number3, wave_enemies_spawned3, enemy_spawn_delay3, cheat_cooldown3
    global consecutive_hits3
    now = time.time()
    if now - last_hit_time3 > HIT_TIMEOUT3:
        consecutive_hits3 = 0
    for b in bullets3[:]:
        b.update(dt)
        if not b.is_alive():
            bullets3.remove(b)
    for e in enemies3[:]:
        e.update(dt)
        if e.reached_ground():
            if not shield_active3:
                lives3 -= 1
            enemies3.remove(e)
            if lives3 <= 0:
                game_over3 = True
        elif not e.is_alive():
            enemies3.remove(e)
    for ex3 in explosions3[:]:
        ex3.update(dt)
        if not ex3.is_alive():
            explosions3.remove(ex3)
    for p in powerups3[:]:
        p.update(dt)
        if not p.is_alive():
            powerups3.remove(p)
    spawn_enemy3()
    if wave_enemies_spawned3 >= enemies_per_wave3 and not enemies3:
        wave_number3 += 1
        wave_enemies_spawned3 = 0
        enemy_spawn_delay3 = max(0.5, enemy_spawn_delay3 - 0.2)
    if cheat_cooldown3 > 0:
        cheat_cooldown3 -= dt
    if cheat_mode3 and cheat_cooldown3 <= 0:
        cheat_mode_targeting3()
    update_powerups3()
    check_collisions3()

def reset_game3():
    global score3, lives3, game_over3, wave_number3, wave_enemies_spawned3
    global bullets3, enemies3, explosions3, powerups3
    global double_shot3, rapid_fire3, shield_active3, cheat_mode3
    global consecutive_hits3, last_hit_time3
    score3 = 0; lives3 = 5; game_over3 = False
    wave_number3 = 1; wave_enemies_spawned3 = 0
    bullets3.clear(); enemies3.clear(); explosions3.clear(); powerups3.clear()
    double_shot3 = False; rapid_fire3 = False; shield_active3 = False
    cheat_mode3 = False; consecutive_hits3 = 0; last_hit_time3 = 0



# =====================================================================================
# =====================================================================================


def keyboardListener(key, x, y):
    global GAME_START, GAME_OPTION, hit
    if not GAME_START:
        if key == b'1': GAME_OPTION = 1; GAME_START = True
        if key == b'2': GAME_OPTION = 2; GAME_START = True
        if key == b'3': GAME_OPTION = 3; GAME_START = True
    else:
        if key == b'0': GAME_START = False; GAME_OPTION = 0

    # Game-1 =======================================================
    if GAME_START and GAME_OPTION == 1:
        if key == b' ' and not game_over: hit = True
        if key == b'r': reset_game()

    # Game-2 =======================================================
    if GAME_START and GAME_OPTION == 2:
        global playerAngle2, gunAngle2, cheatMode2, autoCamera2, firstPersonView2, topDownView2
        global playerX2, playerY2, playerZ2
        if key in (b'w', b'W'):
            topDownView2 = not topDownView2
            if topDownView2: firstPersonView2 = False
        elif key in (b's', b'S'):
            firstPersonView2 = not firstPersonView2
            if firstPersonView2: topDownView2 = False
        elif key in (b'a', b'A'):
            nx = playerX2 - math.sin(math.radians(playerAngle2 + 90)) * 0.1
            ny = playerY2 - math.cos(math.radians(playerAngle2 + 90)) * 0.1
            if not check_collision2(nx, ny): playerX2, playerY2 = nx, ny
        elif key in (b'd', b'D'):
            nx = playerX2 + math.sin(math.radians(playerAngle2 + 90)) * 0.1
            ny = playerY2 + math.cos(math.radians(playerAngle2 + 90)) * 0.1
            if not check_collision2(nx, ny): playerX2, playerY2 = nx, ny
        elif key in (b'c', b'C'):
            cheatMode2 = not cheatMode2
        elif key in (b'v', b'V'):
            if cheatMode2: autoCamera2 = not autoCamera2
        elif key in (b'r', b'R'):
            if gameOver2: restart_game2()
        elif key == b' ':
            fire_bullet2()
        glutPostRedisplay()

    # Game-3 =======================================================
    if GAME_START and GAME_OPTION == 3:
        global cannon_rotation, cannon_elevation, cheat_mode3, cheat_cooldown3
        if key == b'a': cannon_rotation += 5
        if key == b'd': cannon_rotation -= 5
        if key == b'w': cannon_elevation = max(0, cannon_elevation - 3)
        if key == b's': cannon_elevation = min(90, cannon_elevation + 3)
        if key == b' ': fire_bullet3()
        if key == b'c':
            if cheat_cooldown3 <= 0:
                cheat_mode3 = not cheat_mode3
                if cheat_mode3:
                    cheat_cooldown3 = 5.0
        if key == b'r': reset_game3()

def specialKeyListener(key, x, y):
    # Game-1 =======================================================
    if GAME_START and GAME_OPTION == 1:
        global hx, hy, b
        if game_over: return
        if key == GLUT_KEY_UP:
            np = hy - b
            if np > -GRID_LENGTH: hy = np
        if key == GLUT_KEY_DOWN:
            np = hy + b
            if np < GRID_LENGTH: hy = np
        if key == GLUT_KEY_LEFT:
            np = hx + b
            if np < GRID_LENGTH: hx = np
        if key == GLUT_KEY_RIGHT:
            np = hx - b
            if np > -GRID_LENGTH: hx = np

    # Game-2 =======================================================
    if GAME_START and GAME_OPTION == 2:
        global gunAngle2, cameraX2, cameraY2, cameraZ2, cameraAngleX2, cameraAngleY2
        global playerX2, playerY2, playerAngle2
        if key == GLUT_KEY_LEFT:
            if glutGetModifiers() & GLUT_ACTIVE_CTRL:
                cameraAngleY2 += 2.0
                cameraX2 = 10 * math.sin(math.radians(cameraAngleY2))
                cameraZ2 = 10 * math.cos(math.radians(cameraAngleY2))
            else:
                playerAngle2 += 2.0
        elif key == GLUT_KEY_RIGHT:
            if glutGetModifiers() & GLUT_ACTIVE_CTRL:
                cameraAngleY2 -= 2.0
                cameraX2 = 10 * math.sin(math.radians(cameraAngleY2))
                cameraZ2 = 10 * math.cos(math.radians(cameraAngleY2))
            else:
                playerAngle2 -= 2.0
        elif key == GLUT_KEY_UP:
            if glutGetModifiers() & GLUT_ACTIVE_CTRL:
                cameraY2 += 0.5
            else:
                nx = playerX2 + math.sin(math.radians(playerAngle2)) * 0.1
                ny = playerY2 + math.cos(math.radians(playerAngle2)) * 0.1
                if not check_collision2(nx, ny): playerX2, playerY2 = nx, ny
        elif key == GLUT_KEY_DOWN:
            if glutGetModifiers() & GLUT_ACTIVE_CTRL:
                cameraY2 = max(cameraY2 - 0.5, 2.0)
            else:
                nx = playerX2 - math.sin(math.radians(playerAngle2)) * 0.1
                ny = playerY2 - math.cos(math.radians(playerAngle2)) * 0.1
                if not check_collision2(nx, ny): playerX2, playerY2 = nx, ny
        glutPostRedisplay()

    # Game-3 =======================================================
    if GAME_START and GAME_OPTION == 3:
        global camera_pos3, cannon_rotation, cannon_elevation
        x, y, z = camera_pos3
        if key == GLUT_KEY_UP: cannon_elevation = max(0, cannon_elevation - 3)
        elif key == GLUT_KEY_DOWN: cannon_elevation = min(90, cannon_elevation + 3)
        elif key == GLUT_KEY_LEFT: cannon_rotation += 5
        elif key == GLUT_KEY_RIGHT: cannon_rotation -= 5
        camera_pos3 = (x, y, z)

def mouseListener(button, state, x, y):
    # Game-2 =======================================================
    if GAME_START and GAME_OPTION == 2:
        if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            fire_bullet2()
        glutPostRedisplay()
    # Game-3 =======================================================
    if GAME_START and GAME_OPTION == 3:
        if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            fire_bullet3()

def setupCamera():
    # Game-2 =======================================================
    if GAME_START and GAME_OPTION == 2:
        glMatrixMode(GL_PROJECTION); glLoadIdentity()
        gluPerspective(45, 1.25, 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW); glLoadIdentity()
        if firstPersonView2:
            lookX = playerX2 + math.sin(math.radians(playerAngle2 + gunAngle2))
            lookY = playerY2 + math.cos(math.radians(playerAngle2 + gunAngle2))
            lookZ = playerZ2 + 0.5
            gluLookAt(playerX2, playerY2, playerZ2 + 0.5, lookX, lookY, lookZ, 0,0,1)
        elif topDownView2:
            gluLookAt(playerX2, playerY2, 20.0, playerX2, playerY2, 0.0, 0,1,0)
        else:
            gluLookAt(cameraX2, cameraY2, cameraZ2, playerX2, playerY2, playerZ2, 0,0,1)

    # Game-3 =======================================================
    elif GAME_START and GAME_OPTION == 3:
        glMatrixMode(GL_PROJECTION); glLoadIdentity()
        gluPerspective(fovY3, 1.25, 0.1, 1500)
        glMatrixMode(GL_MODELVIEW); glLoadIdentity()
        x, y, z = camera_pos3
        gluLookAt(x, y, z, 0, 0, 0, 0, 0, 1)

    # Menu / Game-1 ================================================
    else:
        glMatrixMode(GL_PROJECTION); glLoadIdentity()
        gluPerspective(fovY, 1.1, 100, 1500)
        glMatrixMode(GL_MODELVIEW); glLoadIdentity()
        x, y, z = camera_pos
        gluLookAt(x, y, z, 0, 0, 0, 0, 0, 1)
        
last_time_global = time.time()

def idle():
    global random_var, last_t, hit, strike, speed_change_score
    global life, score, misses, spawn_time_tracker
    global consecutive_green_hits, in_bonus_round
    global strike_rotate, strike_direction
    global last_time_global, program_start_time

    # Game-1 =======================================================
    if GAME_START and GAME_OPTION == 1:
        random_var += 1
        period = max(spawn_time_tracker, 1)
        t = random_var % period

        if in_bonus_round:
            now = get_elapsed_time()
            if now >= bonus_end_time_ms:
                end_bonus_round()

        respawned = False
        if not game_over:
            if hit:
                inc = 5 if strike_direction != 1 else 1
                strike += inc*strike_direction
                if strike > 250: strike_rotate = 10*strike_direction
                if strike >= 350: strike_direction *= -1
                if strike <= draw_r:
                    if check_same_cell():
                        if color_changer == 1:
                            life -= 1
                            consecutive_green_hits = 0
                        else:
                            score += 1
                            speed_change_score += 1
                            consecutive_green_hits += 1
                            if consecutive_green_hits >= 5 and not in_bonus_round:
                                trigger_bonus_round()
                            if speed_change_score >= SPEED_CHANGE_SCORE_LIMIT:
                                speed_change_score = 0
                                spawn_time_tracker = max(MIN_SPAWN_PERIOD, spawn_time_tracker - PULSE_DECAY_STEP)
                        enemy_position()
                        random_var = 0; t = 0; respawned = True
                    else:
                        # WRONG CELL -> count a miss
                        consecutive_green_hits = 0
                        misses += 1
                    hit = False; strike = 250; strike_direction = 1

            # Pulse wrap: NO miss on timeout (per your rule)
            if (not respawned) and (t < last_t):
                if not in_bonus_round: 
                    if (color_changer == 0):
                        # Missed a green cell
                        misses += 1
                        consecutive_green_hits = 0
                enemy_position()

                random_var = 0; t = 0

            check_end_conditions()

        last_t = t
        glutPostRedisplay()

    # Game-2 =======================================================
    if GAME_START and GAME_OPTION == 2:
        update_game2()
        glutPostRedisplay()

    # Game-3 =======================================================
    if GAME_START and GAME_OPTION == 3:
        now = time.time()
        dt = now - last_time_global
        last_time_global = now
        update_game3(dt)
        glutPostRedisplay()

def showScreen():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)

    if not GAME_START:
        setupCamera()
        draw_text(360, 460, "Select a Game Mode to Start")
        draw_text(400, 420, "1. Hammer Havoc")
        draw_text(405, 390, "2. Maze Shooter")
        draw_text(410, 360, "3. Strike Planes")
        glutSwapBuffers()
        return

    # Game-1 =======================================================
    if GAME_START:
        draw_text(650, 550, "Press '0' to go back to Menu.")
    if GAME_OPTION == 1:
        setupCamera()
        glPushMatrix(); glColor3f(0.3,0.3,0.4); glTranslatef(0,150,0); glutSolidCube(590); glPopMatrix()
        glBegin(GL_QUADS)
        length = (2 * GRID_LENGTH) / 6
        for i in range(0,6):
            for j in range(0,6):
                if i % 2 == 0: clr = [1,1,1] if j % 2 == 0 else [0.5,0.5,0.5]
                else: clr = [1,1,1] if j % 2 != 0 else [0.5,0.5,0.5]
                if in_bonus_round and i == bonus_row_index:
                    gold = [1.0, 0.95, 0.6]; alpha = 0.6
                    clr = [(1-alpha)*clr[0]+alpha*gold[0],
                           (1-alpha)*clr[1]+alpha*gold[1],
                           (1-alpha)*clr[2]+alpha*gold[2]]
                glColor3f(*clr)
                glVertex3f(-GRID_LENGTH + length*j, -GRID_LENGTH + length*i, 0)
                glVertex3f(-GRID_LENGTH + length*j, -GRID_LENGTH + length*(i+1), 0)
                glVertex3f(-GRID_LENGTH + length*(j+1), -GRID_LENGTH + length*(i+1), 0)
                glVertex3f(-GRID_LENGTH + length*(j+1), -GRID_LENGTH + length*i, 0)
        glEnd()

        if not game_over:
            glPushMatrix(); drawEnemy(); glPopMatrix()

        if game_over:
            draw_text(10, 550, "GAME OVER! Press 'R' to Restart.")
        else:
            draw_text(10, 550, f"Life: {life}")
            draw_text(10, 530, f"Score: {score}")
            draw_text(10, 510, f"Misses: {misses}/{MISSES_LIMIT}")
            draw_text(10, 490, "Space=Strike  Arrows=Move  R=Restart")
            draw_text(10, 470, f"Combo (Green x5): {consecutive_green_hits}/5")
            if in_bonus_round:
                remaining = max(0, (bonus_end_time_ms - get_elapsed_time()) // 1000)
                draw_text(10, 450, f"BONUS ROUND! Row {bonus_row_index+1}  ({remaining}s left)")

        glPushMatrix()
        if game_over: glTranslatef(-100,50,0)
        else: glTranslatef(hx, hy, 0)
        glPushMatrix(); glScalef(0.5,0.5,0.5)
        if game_over:
            glScalef(2,2,2); glRotatef(90,0,1,0); glRotatef(45,1,0,0)
        else:
            glRotatef(5,-1,-1,0); glRotatef(strike_rotate,-1,0,0); glTranslatef(0,0,strike)
        draw_hammer()
        glPopMatrix()
        if not game_over: draw_shadow()
        glPopMatrix()

    # Game-2 =======================================================
    if GAME_OPTION == 2:
        setupCamera()
        glPushMatrix()
        draw_floor2()
        draw_walls2()
        if not firstPersonView2: draw_player2()
        draw_enemies2()
        draw_bullets2()
        if not firstPersonView2: draw_gun_sight2()
        if firstPersonView2: draw_crosshair2()
        draw_hud2()
        glPopMatrix()

    # Game-3 =======================================================
    if GAME_OPTION == 3:
        setupCamera()
        glPushMatrix()
        glBegin(GL_QUADS)
        glColor3f(0.8,0.7,0.5)
        glVertex3f(-GRID_LENGTH3, GRID_LENGTH3, 0)
        glVertex3f(GRID_LENGTH3, GRID_LENGTH3, 0)
        glVertex3f(GRID_LENGTH3, -GRID_LENGTH3, 0)
        glVertex3f(-GRID_LENGTH3, -GRID_LENGTH3, 0)
        glEnd()
        glColor3f(0.6,0.5,0.3)
        glBegin(GL_LINES)
        for i in range(-GRID_LENGTH3, GRID_LENGTH3+1, 100):
            glVertex3f(i, -GRID_LENGTH3, 1); glVertex3f(i, GRID_LENGTH3, 1)
            glVertex3f(-GRID_LENGTH3, i, 1); glVertex3f(GRID_LENGTH3, i, 1)
        glEnd()
        draw_cannon3()
        draw_enemies3()
        draw_bullets3()
        draw_explosions3()
        draw_powerups3()
        if shield_active3:
            glPushMatrix(); glTranslatef(0,-400,50); glColor3f(0,1,1); glutSolidSphere(100,16,16); glPopMatrix()
        draw_text(20,670,f"Score: {score3}")
        draw_text(20,650,f"Lives: {lives3}")
        draw_text(20,630,f"Wave: {wave_number3}")
        draw_text(20,610,f"Enemies: {len(enemies3)}")
        draw_text(20,590,f"Consecutive Hits: {consecutive_hits3}")
        y_off = 670
        if double_shot3: draw_text(10,y_off,"DOUBLE SHOT!"); y_off -= 20
        if rapid_fire3: draw_text(10,y_off,"RAPID FIRE!"); y_off -= 20
        if shield_active3: draw_text(10,y_off,"SHIELD ACTIVE!"); y_off -= 20
        if cheat_mode3: draw_text(400,770,"AUTO LOCK-ON ACTIVE!")
        elif cheat_cooldown3 > 0: draw_text(400,770,f"Cheat Cooldown: {cheat_cooldown3:.1f}s")
        draw_text(10,100,"A/D or ←/→: Rotate | W/S or ↑/↓: Aim | Space/Click: Fire")
        draw_text(10,80,"C: Cheat Mode | R: Restart")
        if game_over3:
            draw_text(200,400,"GAME OVER!")
            draw_text(200,380,f"Final Score: {score3}")
            draw_text(200,360,"Press R to restart")
        glPopMatrix()

    glutSwapBuffers()

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowPosition(0, 0)
    glutInitWindowSize(1000, 800)
    glutCreateWindow(b"Triple Strike - 3 Mini Games in 1")
    glClearColor(0.6, 0.5, 0.8, 1.0)

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()
