from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import numpy as np
import time
import sys

# Game Constants
MAZE_SIZE = 15
CELL_SIZE = 2.0
WALL_HEIGHT = 2.0
PLAYER_HEIGHT = 1.8
ENEMY_HEIGHT = 1.5
BULLET_SPEED = 0.2
ENEMY_SPEED = 0.005  # Reduced from 0.02 to make enemies slower
MAX_LIVES = 5
MAX_MISSED_BULLETS = 10

# Game State
playerLives = MAX_LIVES
score = 0
missedBullets = 0
gameOver = False
cheatMode = False
autoCamera = False
firstPersonView = False
topDownView = False

# Player State
playerX, playerY, playerZ = 0.0, 0.0, 0.0
playerAngle = 0.0
gunAngle = 0.0

# Camera State
cameraX, cameraY, cameraZ = 0.0, 10.0, 10.0
cameraAngleX, cameraAngleY = -30.0, 0.0

# Cheat mode variables
cheatShootTimer = 0
cheatShootInterval = 5  # frames between shots in cheat mode
cheatRotationAngle = 0  # For 360-degree rotation in cheat mode

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

# Enemy class
class Enemy:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.z = 0.0
        self.breathPhase = random.random() * math.pi * 2
        self.alive = True
        self.respawnTimer = 0
        
    def update(self, targetX, targetY):
        if not self.alive:
            # Handle respawn timer
            self.respawnTimer += 1
            if self.respawnTimer > 300:  # Respawn after 5 seconds (60 frames/sec)
                self.respawn()
            return
            
        # In cheat mode, enemies don't move
        if cheatMode:
            return
            
        # Move toward player
        dx = targetX - self.x
        dy = targetY - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 0.1:
            self.x += (dx / dist) * ENEMY_SPEED
            self.y += (dy / dist) * ENEMY_SPEED
            
        # Update breathing animation
        self.breathPhase += 0.05
        
    def respawn(self):
        # Find a valid position in the maze
        while True:
            x = random.randint(1, MAZE_SIZE-2)
            y = random.randint(1, MAZE_SIZE-2)
            if maze[x][y] == 0:  # Check if it's a path
                self.x = x * CELL_SIZE - (MAZE_SIZE * CELL_SIZE / 2) + CELL_SIZE/2
                self.y = y * CELL_SIZE - (MAZE_SIZE * CELL_SIZE / 2) + CELL_SIZE/2
                self.alive = True
                self.respawnTimer = 0
                break

# Bullet class
class Bullet:
    def __init__(self, x, y, z, angle):
        self.x = x
        self.y = y
        self.z = z
        self.angle = angle
        self.active = True
        
    def update(self):
        self.x += math.sin(math.radians(self.angle)) * BULLET_SPEED
        self.y += math.cos(math.radians(self.angle)) * BULLET_SPEED
        
        # Check if bullet is out of bounds
        max_dist = MAZE_SIZE * CELL_SIZE
        if (abs(self.x) > max_dist or abs(self.y) > max_dist):
            self.active = False
            global missedBullets
            missedBullets += 1

# Initialize enemies
enemies = []
for i in range(5):
    while True:
        x = random.randint(1, MAZE_SIZE-2)
        y = random.randint(1, MAZE_SIZE-2)
        if maze[x][y] == 0:  # Check if it's a path
            enemies.append(Enemy(
                x * CELL_SIZE - (MAZE_SIZE * CELL_SIZE / 2) + CELL_SIZE/2,
                y * CELL_SIZE - (MAZE_SIZE * CELL_SIZE / 2) + CELL_SIZE/2
            ))
            break

# Initialize bullets list
bullets = []

# Find player start position (center of maze)
playerX = 0.0
playerY = 0.0
playerZ = PLAYER_HEIGHT / 2

# Manual lighting calculation function
def calculate_lighting(x, y, z, base_color):
    # Simple manual lighting based on distance from player
    dx = x - playerX
    dy = y - playerY
    dz = z - playerZ
    distance = math.sqrt(dx*dx + dy*dy + dz*dz)
    
    # Light intensity decreases with distance
    intensity = max(0.3, 1.0 - distance / 30.0)
    
    # Apply lighting to base color
    r = base_color[0] * intensity
    g = base_color[1] * intensity
    b = base_color[2] * intensity
    
    return (r, g, b)

# Draw a brick texture on a wall face
def draw_brick_texture(x, y, z, width, height, depth, base_color):
    # Calculate lighting for this position
    lit_color = calculate_lighting(x, y, z, base_color)
    glColor3f(lit_color[0], lit_color[1], lit_color[2])
    
    # Draw the main wall face
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(width, depth, height)
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Draw brick pattern (lines)
    brick_width = width / 4
    brick_height = height / 8
    
    glColor3f(lit_color[0] * 0.7, lit_color[1] * 0.7, lit_color[2] * 0.7)
    glBegin(GL_LINES)
    
    # Horizontal lines
    for i in range(1, 8):
        z_pos = z - height/2 + i * brick_height
        glVertex3f(x - width/2, y, z_pos)
        glVertex3f(x + width/2, y, z_pos)
    
    # Vertical lines (staggered for brick pattern)
    for i in range(5):
        x_pos = x - width/2 + i * brick_width
        offset = 0 if i % 2 == 0 else brick_height/2
        glVertex3f(x_pos, y, z - height/2 + offset)
        glVertex3f(x_pos, y, z + height/2 - (brick_height/2 if i % 2 == 1 else 0))
    
    glEnd()

# OpenGL drawing functions
def draw_floor():
    # Calculate lighting for floor
    lit_color = calculate_lighting(0, 0, 0, (0.0, 0.6, 0.0))
    glColor3f(lit_color[0], lit_color[1], lit_color[2])
    
    size = MAZE_SIZE * CELL_SIZE / 2
    glBegin(GL_QUADS)
    glVertex3f(-size, -size, 0.0)
    glVertex3f(size, -size, 0.0)
    glVertex3f(size, size, 0.0)
    glVertex3f(-size, size, 0.0)
    glEnd()

def draw_walls():
    half_size = MAZE_SIZE * CELL_SIZE / 2
    
    for i in range(MAZE_SIZE):
        for j in range(MAZE_SIZE):
            if maze[i][j] == 1:  # Wall
                x = i * CELL_SIZE - half_size
                y = j * CELL_SIZE - half_size
                
                # Draw brick texture for walls
                draw_brick_texture(
                    x + CELL_SIZE/2, 
                    y + CELL_SIZE/2, 
                    WALL_HEIGHT/2,
                    CELL_SIZE, 
                    WALL_HEIGHT, 
                    CELL_SIZE,
                    (0.5, 0.3, 0.1)  # Brown color for bricks
                )
            elif maze[i][j] == 2:  # Door (slightly different color)
                x = i * CELL_SIZE - half_size
                y = j * CELL_SIZE - half_size
                
                # Draw door with different color
                lit_color = calculate_lighting(x + CELL_SIZE/2, y + CELL_SIZE/2, WALL_HEIGHT/2, (0.6, 0.4, 0.2))
                glColor3f(lit_color[0], lit_color[1], lit_color[2])
                
                glPushMatrix()
                glTranslatef(x + CELL_SIZE/2, y + CELL_SIZE/2, WALL_HEIGHT/2)
                glScalef(CELL_SIZE, CELL_SIZE, WALL_HEIGHT)
                glutSolidCube(1.0)
                glPopMatrix()

def draw_player():
    # Calculate lighting for player
    lit_color = calculate_lighting(playerX, playerY, playerZ, (1.0, 1.0, 1.0))
    
    # Draw player body
    glPushMatrix()
    glTranslatef(playerX, playerY, playerZ)
    glRotatef(playerAngle, 0, 0, 1)
    
    # Head (sphere)
    glPushMatrix()
    glTranslatef(0, 0, 0.7)
    glColor3f(lit_color[0] * 1.0, lit_color[1] * 0.8, lit_color[2] * 0.6)  # Skin color with lighting
    glutSolidSphere(0.2, 20, 20)
    glPopMatrix()
    
    # Torso (cuboid)
    glPushMatrix()
    glTranslatef(0, 0, 0.35)
    glScalef(0.4, 0.3, 0.7)
    glColor3f(lit_color[0] * 0.0, lit_color[1] * 0.0, lit_color[2] * 1.0)  # Blue torso with lighting
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Arms (cylinders)
    glPushMatrix()
    glTranslatef(0.25, 0, 0.4)
    glRotatef(90, 0, 1, 0)
    glColor3f(lit_color[0] * 0.0, lit_color[1] * 0.0, lit_color[2] * 1.0)  # Blue arms with lighting
    glutSolidCylinder(0.07, 0.4, 20, 20)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-0.25, 0, 0.4)
    glRotatef(90, 0, 1, 0)
    glutSolidCylinder(0.07, 0.4, 20, 20)
    glPopMatrix()
    
    # Legs (cylinders)
    glPushMatrix()
    glTranslatef(0.1, 0, -0.1)
    glRotatef(90, 1, 0, 0)
    glColor3f(lit_color[0] * 0.5, lit_color[1] * 0.5, lit_color[2] * 0.5)  # Gray legs with lighting
    glutSolidCylinder(0.08, 0.4, 20, 20)
    glPopMatrix()
    
    glPushMatrix()
    glTranslatef(-0.1, 0, -0.1)
    glRotatef(90, 1, 0, 0)
    glutSolidCylinder(0.03, 0.2, 20, 20)
    glPopMatrix()
    
    # Draw gun
    glPushMatrix()
    glTranslatef(0.3, 0, 0.5)
    glRotatef(gunAngle, 0, 0, 1)
    
    # Gun body (cuboid)
    glPushMatrix()
    glTranslatef(0.1, 0, 0)
    glScalef(0.2, 0.1, 0.1)
    glColor3f(lit_color[0] * 0.2, lit_color[1] * 0.2, lit_color[2] * 0.2)  # Dark gray gun with lighting
    glutSolidCube(1.0)
    glPopMatrix()
    
    # Gun barrel (cylinder)
    glPushMatrix()
    glTranslatef(0.2, 0, 0)
    glRotatef(90, 0, 1, 0)
    glutSolidCylinder(0.03, 0.2, 20, 20)
    glPopMatrix()
    
    glPopMatrix()  # Gun rotation
    glPopMatrix()  # Player transformation

def draw_enemies():
    for enemy in enemies:
        if not enemy.alive:
            continue
            
        # Calculate lighting for enemy
        lit_color = calculate_lighting(enemy.x, enemy.y, enemy.z, (1.0, 1.0, 1.0))
            
        glPushMatrix()
        glTranslatef(enemy.x, enemy.y, enemy.z)
        
        # In cheat mode, make enemies blue to indicate they're frozen
        if cheatMode:
            glColor3f(lit_color[0] * 0.0, lit_color[1] * 0.0, lit_color[2] * 1.0)  # Blue enemy in cheat mode
        else:
            glColor3f(lit_color[0] * 1.0, lit_color[1] * 0.0, lit_color[2] * 0.0)  # Red enemy in normal mode
        
        # Breathing animation (scale up and down)
        breathScale = 0.9 + 0.1 * math.sin(enemy.breathPhase)
        
        # Bottom sphere (body)
        glPushMatrix()
        glTranslatef(0, 0, 0.5)
        glScalef(1.0, 1.0, breathScale)
        glutSolidSphere(0.3, 20, 20)
        glPopMatrix()
        
        # Top sphere (head)
        glPushMatrix()
        glTranslatef(0, 0, 1.0)
        glScalef(0.7, 0.7, breathScale)
        glutSolidSphere(0.2, 20, 20)
        glPopMatrix()
        
        glPopMatrix()

def draw_bullets():
    for bullet in bullets:
        if bullet.active:
            # Calculate lighting for bullet
            lit_color = calculate_lighting(bullet.x, bullet.y, bullet.z, (1.0, 1.0, 0.0))
            glColor3f(lit_color[0], lit_color[1], lit_color[2])  # Yellow bullets with lighting
            
            glPushMatrix()
            glTranslatef(bullet.x, bullet.y, bullet.z)
            glutSolidCube(0.1)
            glPopMatrix()

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    glColor3f(1, 1, 1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    
    # Set up an orthographic projection that matches window coordinates
    gluOrtho2D(0, 1000, 0, 800)  # left, right, bottom, top

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw text at (x, y) in screen coordinates
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    
    # Restore original projection and modelview matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_hud():
    # Draw HUD elements
    glColor3f(1.0, 1.0, 1.0)
    
    # Render text
    draw_text(10, 770, f"Lives: {playerLives}  Score: {score}  Missed: {missedBullets}/10")
    
    if gameOver:
        draw_text(300, 400, "GAME OVER - Press R to restart")
    
    if cheatMode:
        draw_text(10, 750, "CHEAT MODE ACTIVE - Enemies Frozen")
    
    if firstPersonView:
        draw_text(10, 730, "FIRST PERSON VIEW")
    
    if topDownView:
        draw_text(10, 710, "TOP DOWN VIEW")

def draw_crosshair():
    # Switch to 2D orthographic projection for HUD elements
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Draw crosshair in the center of the screen
    center_x, center_y = 500, 400
    size = 10
    thickness = 2
    
    glColor3f(1.0, 0.0, 0.0)  # Red crosshair
    glLineWidth(thickness)
    
    glBegin(GL_LINES)
    # Horizontal line
    glVertex2f(center_x - size, center_y)
    glVertex2f(center_x + size, center_y)
    # Vertical line
    glVertex2f(center_x, center_y - size)
    glVertex2f(center_x, center_y + size)
    glEnd()
    
    # Restore matrices
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_gun_sight():
    # Calculate the direction of the bullet
    direction_x = math.sin(math.radians(playerAngle + gunAngle))
    direction_y = math.cos(math.radians(playerAngle + gunAngle))
    
    # Calculate gun position (same as in fire_bullet)
    gun_offset_x = 0.3 * math.sin(math.radians(playerAngle))
    gun_offset_y = 0.3 * math.cos(math.radians(playerAngle))
    barrel_offset_x = 0.2 * math.sin(math.radians(playerAngle + gunAngle))
    barrel_offset_y = 0.2 * math.cos(math.radians(playerAngle + gunAngle))
    total_offset_x = gun_offset_x + barrel_offset_x
    total_offset_y = gun_offset_y + barrel_offset_y
    
    start_x = playerX + total_offset_x
    start_y = playerY + total_offset_y
    start_z = playerZ + 0.5
    
    # Draw a red line showing the bullet trajectory
    glColor3f(1.0, 0.0, 0.0)
    glLineWidth(2.0)
    glBegin(GL_LINES)
    glVertex3f(start_x, start_y, start_z)
    glVertex3f(start_x + direction_x * 5, start_y + direction_y * 5, start_z)
    glEnd()
    
    # Draw a small sphere at the gun barrel
    glPushMatrix()
    glTranslatef(start_x, start_y, start_z)
    glColor3f(1.0, 0.0, 0.0)
    glutSolidSphere(0.05, 10, 10)
    glPopMatrix()

def check_collision(x, y):
    # Convert position to maze grid coordinates
    half_size = MAZE_SIZE * CELL_SIZE / 2
    gridX = int((x + half_size) / CELL_SIZE)
    gridY = int((y + half_size) / CELL_SIZE)
    
    # Check if position is within bounds and not a wall
    if (gridX < 0 or gridX >= MAZE_SIZE or 
        gridY < 0 or gridY >= MAZE_SIZE or 
        maze[gridX][gridY] == 1):
        return True
    return False

def check_bullet_enemy_collision():
    for bullet in bullets:
        if not bullet.active:
            continue
            
        for enemy in enemies:
            if not enemy.alive:
                continue
                
            # Simple distance-based collision detection
            dx = bullet.x - enemy.x
            dy = bullet.y - enemy.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < 0.5:  # Collision threshold
                bullet.active = False
                enemy.alive = False
                global score
                score += 10

def check_enemy_player_collision():
    # In cheat mode, enemies don't collide with player
    if cheatMode:
        return
        
    for enemy in enemies:
        if not enemy.alive:
            continue
            
        # Simple distance-based collision detection
        dx = playerX - enemy.x
        dy = playerY - enemy.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        if distance < 0.8:  # Collision threshold
            enemy.alive = False
            global playerLives
            playerLives -= 1
            if playerLives <= 0:
                global gameOver
                gameOver = True

def update_game():
    global playerX, playerY, playerZ, gameOver, missedBullets, cheatShootTimer, cheatRotationAngle
    
    if gameOver:
        return
        
    # Update enemies (they won't move in cheat mode)
    for enemy in enemies:
        enemy.update(playerX, playerY)
    
    # Update bullets
    for bullet in bullets[:]:
        bullet.update()
        if not bullet.active:
            bullets.remove(bullet)
    
    # Check collisions
    check_bullet_enemy_collision()
    check_enemy_player_collision()
    
    # Check game over conditions
    if missedBullets >= MAX_MISSED_BULLETS:
        gameOver = True

def fire_bullet():
    # Calculate bullet start position (at gun barrel)
    # The gun is positioned at 0.3 units from the player center
    gun_offset_x = 0.3 * math.sin(math.radians(playerAngle))
    gun_offset_y = 0.3 * math.cos(math.radians(playerAngle))
    
    # The gun barrel is at 0.2 units from the gun base (along the gun angle)
    barrel_offset_x = 0.2 * math.sin(math.radians(playerAngle + gunAngle))
    barrel_offset_y = 0.2 * math.cos(math.radians(playerAngle + gunAngle))
    
    # Total offset from player center
    total_offset_x = gun_offset_x + barrel_offset_x
    total_offset_y = gun_offset_y + barrel_offset_y
    
    gunX = playerX + total_offset_x
    gunY = playerY + total_offset_y
    gunZ = playerZ + 0.5  # Gun is at chest height
    
    # Calculate bullet direction (combine player and gun angles)
    bulletAngle = playerAngle + gunAngle
    
    bullets.append(Bullet(gunX, gunY, gunZ, bulletAngle))

def fire_bullet_angle(angle):
    # Calculate bullet start position (at gun barrel)
    gun_offset_x = 0.3 * math.sin(math.radians(playerAngle))
    gun_offset_y = 0.3 * math.cos(math.radians(playerAngle))
    
    gunX = playerX + gun_offset_x
    gunY = playerY + gun_offset_y
    gunZ = playerZ + 0.5
    
    bullets.append(Bullet(gunX, gunY, gunZ, angle))

def restart_game():
    global playerLives, score, missedBullets, gameOver
    global playerX, playerY, playerZ, playerAngle, gunAngle
    global enemies, bullets, firstPersonView, topDownView, cheatShootTimer, cheatRotationAngle, cheatMode
    
    playerLives = MAX_LIVES
    score = 0
    missedBullets = 0
    gameOver = False
    firstPersonView = False
    topDownView = False
    cheatMode = False
    cheatShootTimer = 0
    cheatRotationAngle = 0
    
    playerX, playerY, playerZ = 0.0, 0.0, PLAYER_HEIGHT / 2
    playerAngle = 0.0
    gunAngle = 0.0
    
    # Reset enemies
    enemies = []
    for i in range(5):
        while True:
            x = random.randint(1, MAZE_SIZE-2)
            y = random.randint(1, MAZE_SIZE-2)
            if maze[x][y] == 0:
                enemies.append(Enemy(
                    x * CELL_SIZE - (MAZE_SIZE * CELL_SIZE / 2) + CELL_SIZE/2,
                    y * CELL_SIZE - (MAZE_SIZE * CELL_SIZE / 2) + CELL_SIZE/2
                ))
                break
    
    # Clear bullets
    bullets = []

def keyboardListener(key, x, y):
    global playerAngle, gunAngle, cheatMode, autoCamera, firstPersonView, topDownView
    global playerX, playerY, playerZ  # Declare as global to modify them
    
    if key == b'w' or key == b'W':
        # Toggle top-down view
        topDownView = not topDownView
        firstPersonView = False if topDownView else firstPersonView
    
    elif key == b's' or key == b'S':
        # Toggle first-person view
        firstPersonView = not firstPersonView
        topDownView = False if firstPersonView else topDownView
    
    elif key == b'a' or key == b'A':
        # Move player left
        newX = playerX - math.sin(math.radians(playerAngle + 90)) * 0.1
        newY = playerY - math.cos(math.radians(playerAngle + 90)) * 0.1
        if not check_collision(newX, newY):
            playerX, playerY = newX, newY
    
    elif key == b'd' or key == b'D':
        # Move player right
        newX = playerX + math.sin(math.radians(playerAngle + 90)) * 0.1
        newY = playerY + math.cos(math.radians(playerAngle + 90)) * 0.1
        if not check_collision(newX, newY):
            playerX, playerY = newX, newY
    
    elif key == b'c' or key == b'C':
        # Toggle cheat mode
        cheatMode = not cheatMode
    
    elif key == b'v' or key == b'V':
        # Toggle auto camera (only in cheat mode)
        if cheatMode:
            autoCamera = not autoCamera
    
    elif key == b'r' or key == b'R':
        # Restart game
        if gameOver:
            restart_game()
    
    elif key == b' ':  # Space bar to shoot
        fire_bullet()
    
    glutPostRedisplay()

def specialKeyListener(key, x, y):
    global gunAngle, cameraX, cameraY, cameraZ, cameraAngleX, cameraAngleY
    global playerX, playerY, playerAngle # Add these to modify player position
    
    if key == GLUT_KEY_LEFT:
        if glutGetModifiers() & GLUT_ACTIVE_CTRL:
            # Rotate camera left
            cameraAngleY += 2.0
            cameraX = 10 * math.sin(math.radians(cameraAngleY))
            cameraZ = 10 * math.cos(math.radians(cameraAngleY))
        else:
            # Rotate player left
            playerAngle += 2.0
    
    elif key == GLUT_KEY_RIGHT:
        if glutGetModifiers() & GLUT_ACTIVE_CTRL:
            # Rotate camera right
            cameraAngleY -= 2.0
            cameraX = 10 * math.sin(math.radians(cameraAngleY))
            cameraZ = 10 * math.cos(math.radians(cameraAngleY))
        else:
            # Rotate player right
            playerAngle -= 2.0
    
    elif key == GLUT_KEY_UP:
        if glutGetModifiers() & GLUT_ACTIVE_CTRL:
            # Move camera up
            cameraY += 0.5
        else:
            # Move player forward
            newX = playerX + math.sin(math.radians(playerAngle)) * 0.1
            newY = playerY + math.cos(math.radians(playerAngle)) * 0.1
            if not check_collision(newX, newY):
                playerX, playerY = newX, newY
    
    elif key == GLUT_KEY_DOWN:
        if glutGetModifiers() & GLUT_ACTIVE_CTRL:
            # Move camera down
            cameraY = max(cameraY - 0.5, 2.0)
        else:
            # Move player backward
            newX = playerX - math.sin(math.radians(playerAngle)) * 0.1
            newY = playerY - math.cos(math.radians(playerAngle)) * 0.1
            if not check_collision(newX, newY):
                playerX, playerY = newX, newY
    
    glutPostRedisplay()

def mouseListener(button, state, x, y):
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        fire_bullet()
    glutPostRedisplay()

def idle():
    update_game()
    glutPostRedisplay()

def setupCamera():
    """
    Configures the camera's projection and view settings.
    Uses a perspective projection and positions the camera to look at the target.
    """
    glMatrixMode(GL_PROJECTION)  # Switch to projection matrix mode
    glLoadIdentity()  # Reset the projection matrix
    # Set up a perspective projection (field of view, aspect ratio, near clip, far clip)
    gluPerspective(45, 1.25, 0.1, 1000.0)  # Changed from fovY to 45
    glMatrixMode(GL_MODELVIEW)  # Switch to model-view matrix mode
    glLoadIdentity()  # Reset the model-view matrix

    # Set camera position based on view mode
    if firstPersonView:
        # First-person view (from player's perspective)
        lookX = playerX + math.sin(math.radians(playerAngle + gunAngle))
        lookY = playerY + math.cos(math.radians(playerAngle + gunAngle))
        lookZ = playerZ + 0.5
        
        gluLookAt(
            playerX, playerY, playerZ + 0.5,  # Eye position
            lookX, lookY, lookZ,  # Look at point
            0, 0, 1  # Up vector
        )
    elif topDownView:
        # Top-down view
        gluLookAt(
            playerX, playerY, 20.0,  # Eye position (above player)
            playerX, playerY, 0.0,   # Look at point (player position)
            0, 1, 0                  # Up vector
        )
    else:
        # Third-person view
        gluLookAt(
            cameraX, cameraY, cameraZ,  # Eye position
            playerX, playerY, playerZ,  # Look at point
            0, 0, 1  # Up vector
        )

def showScreen():
    """
    Display function to render the game scene:
    - Clears the screen and sets up the camera.
    - Draws everything of the screen
    """
    # Clear color and depth buffers
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()  # Reset modelview matrix
    glViewport(0, 0, 1000, 800)  # Set viewport size

    setupCamera()  # Configure camera perspective

    # Draw game elements
    draw_floor()
    draw_walls()
    if not firstPersonView:
        draw_player()
    draw_enemies()
    draw_bullets()
    
    # Draw gun sight to show where bullets will be fired from
    if not firstPersonView:  # Only show in third-person view
        draw_gun_sight()
    
    # Draw crosshair in first-person view
    if firstPersonView:
        draw_crosshair()
    
    # Draw HUD
    draw_hud()

    # Swap buffers for smooth rendering (double buffering)
    glutSwapBuffers()

# Main function to set up OpenGL window and loop
def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)  # Double buffering, RGB color, depth test
    glutInitWindowSize(1000, 800)  # Window size
    glutInitWindowPosition(0, 0)  # Window position
    wind = glutCreateWindow(b"3D Maze Shooting Game")  # Create the window

    # Set background color
    glClearColor(0.5, 0.7, 1.0, 1.0)  # Sky blue background

    glutDisplayFunc(showScreen)  # Register display function
    glutKeyboardFunc(keyboardListener)  # Register keyboard listener
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)  # Register the idle function to update the game

    glutMainLoop()  # Enter the GLUT main loop

if __name__ == "__main__":
    main()