from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
from OpenGL.GLUT import GLUT_BITMAP_HELVETICA_18
import random

# ----------------------------
# Camera & world config
# ----------------------------
camera_pos = (0, 300, 650)
fovY = 130
GRID_LENGTH = 500

# Grid centers (6x6)
a = -GRID_LENGTH + GRID_LENGTH/6   # center of first cell
b = GRID_LENGTH/3                  # cell width

# ----------------------------
# Enemy state
# ----------------------------
ex = a + b * int(random.randint(0, 5))
ey = a + b * int(random.randint(0, 5))

ENEMY_RADIUS = 50.0
color_changer = 0           # 0 => green, 1 => red
color_change_decider = 0
draw_r = 0.0                # current pulse radius

# Pulse animation timer (visual only)
SPAWN_TIME_TRACKER = 2500   # initial pulse period (ms units of random_var ticks)
spawn_time_tracker = SPAWN_TIME_TRACKER
PULSE_DECAY_STEP = 250      # reduce period by this amount WHEN threshold reached
MIN_SPAWN_PERIOD = 400      # fastest it will go (lower period => faster)
random_var = 0              # increments every frame
last_t = 0                  # for detecting pulse wrap-around

# Score-gated speed-ups
speed_change_score = 0
SPEED_CHANGE_SCORE_LIMIT = 10

# ----------------------------
# Hammer state
# ----------------------------
hx = a
hy = -a
strike = 250                # hammer z offset (bigger = higher)
strike_rotate = 0
strike_direction = 1
hit = False                 # striking?
CELL_TOL  = 0.001           # same-cell tolerance

# ----------------------------
# Game state
# ----------------------------
LIFE_INIT = 5
MISSES_LIMIT = 10
score = 0
life = LIFE_INIT
misses = 0
game_over = False

# ----------------------------
# Combo & Bonus Round state
# ----------------------------
consecutive_green_hits = 0

in_bonus_round = False
BONUS_DURATION_MS = 10000   # 10 seconds bonus
bonus_row_index = 0         # 0..5 row to stick to
bonus_end_time_ms = 0

# ============================
# Utility / game logic
# ============================

def check_same_cell():
    """Are hammer and enemy in the same grid cell center?"""
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

    speed_change_score = 0  # reset the gating counter

    enemy_position()        # new position + (maybe) color

def trigger_bonus_round():
    """Enable bonus: only green enemies, fixed row, golden row tint."""
    global in_bonus_round, bonus_end_time_ms, bonus_row_index
    global color_changer, ex, ey

    if in_bonus_round:
        return

    in_bonus_round = True
    now = glutGet(GLUT_ELAPSED_TIME)
    bonus_end_time_ms = now + BONUS_DURATION_MS

    bonus_row_index = random.randint(0, 5)

    # Lock to green and fixed row
    color_changer = 0
    ey = a + b * bonus_row_index
    ex = a + b * random.randint(0, 5)

def end_bonus_round():
    """Restore normal mode after bonus."""
    global in_bonus_round, consecutive_green_hits
    global color_changer

    in_bonus_round = False
    consecutive_green_hits = 0
    # Color returns to normal on next enemy_position()

def enemy_position():
    """Place enemy at a new random cell; handle color toggles unless in bonus."""
    global ex, ey, color_changer, color_change_decider

    if in_bonus_round:
        # Fixed row, random column, always green
        color_changer = 0
        ey = a + b * bonus_row_index
        ex = a + b * int(random.randint(0, 5))
        return

    ex = a + b * int(random.randint(0, 5))
    ey = a + b * int(random.randint(0, 5))

    # simple pseudo-random color changes
    if color_change_decider % 2 == 0:
        color_changer = random.randint(0, 1)  # 0 green, 1 red
        color_change_decider = 0
    if color_changer == 1 and color_change_decider % 3 == 1:
        color_changer = 0
    color_change_decider += 1

# ============================
# Rendering
# ============================

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
    # handle
    glPushMatrix()
    glColor3f(0.2, 0.3, 0.3)
    if game_over:
        glColor3f(1,0,0)
    glTranslatef(0, 0, 100)
    glRotatef(90, -1, 0, 0)
    gluCylinder(gluNewQuadric(), 20, 20, 250, 10, 10)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0.5, 0.3, 0.3)
    if game_over:
        glColor3f(1,0,0)
    glTranslatef(0, 0, 100)
    glRotatef(90, -1, 0, 0)
    gluCylinder(gluNewQuadric(), 20, 20, 250, 10, 10)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0.5, 0, 0)
    if game_over:
        glColor3f(1,0,0)
    glTranslatef(0, 250, 100)
    glRotatef(90, -1, 0, 0)
    glutSolidCube(30)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0, 0, 0)
    if game_over:
        glColor3f(1,0,0)
    glTranslatef(0, 0, 100)
    glRotatef(90, -1, 0, 0)
    gluCylinder(gluNewQuadric(), 22, 22, 40, 10, 10)
    glPopMatrix()

    # head
    glPushMatrix()
    glTranslatef(0, 0, 0)
    glColor3f(0.5, 0.25, 0.1)
    if game_over:
        glColor3f(1,0,0)
    glutSolidCube(100)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0, 0)
    glColor3f(0.6, 0.35, 0.2)
    if game_over:
        glColor3f(1,0,0)
    glScalef(2, 2, 2)
    gluCylinder(gluNewQuadric(), 25, 25, 100, 30, 10)
    glPopMatrix()

    glPushMatrix()
    glColor3f(0.5, 0.25, 0.1)
    if game_over:
        glColor3f(1,0,0)
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
    """Draw enemy with fixed base radius, animated by uniform scaling (0..1..0).
       Color fades from black to full (green/red) as scale grows.
    """
    global draw_r

    # Compute triangle-wave scale factor s in [0,1]
    period = max(spawn_time_tracker, 1)   # guard
    t = random_var % period
    half = period / 2.0
    if t <= half:
        s = t / half
    else:
        s = 2.0 - (t / half)
    s = max(0.0, min(1.0, s))

    # Effective visible radius for strike/intersection logic (keeps existing mechanics)
    draw_r = ENEMY_RADIUS * s

    # Base color: red if color_changer==1 else green
    base_color = [float(color_changer), float(1 - color_changer), 0.0]

    # Fade from black to base color as s grows
    curr_color = [c * s for c in base_color]

    glPushMatrix()
    glTranslatef(ex, ey, 0)

    # Scale the entire enemy uniformly so body & head move together
    # (uniform scale uses the same factor on x,y,z; this keeps spheres spherical)
    glScalef(1, 1, s)

    # Body (fixed radius; visual size comes from the uniform scale)
    glColor3f(*curr_color)
    gluSphere(gluNewQuadric(), 50, 20, 10)

    # Head (positioned relative to base size so it scales together with the body)
    glTranslatef(0, 0, ENEMY_RADIUS)
    glColor3f(0,0,0)
    gluSphere(gluNewQuadric(), 25, 20, 10)

    glPopMatrix()


# ============================
# Input
# ============================

def keyboardListener(key, x, y):
    global hit
    if key == b' ' and not game_over:
        hit = True
    if key == b'r':
        reset_game()

def specialKeyListener(key, x, y):
    global hx, hy, b
    if game_over:
        return
    if key == GLUT_KEY_UP:
        changed_pos = hy - b
        if changed_pos > -GRID_LENGTH:
            hy = changed_pos
    if key == GLUT_KEY_DOWN:
        changed_pos = hy + b
        if changed_pos < GRID_LENGTH:
            hy = changed_pos
    if key == GLUT_KEY_LEFT:
        changed_pos = hx + b
        if changed_pos < GRID_LENGTH:
            hx = changed_pos
    if key == GLUT_KEY_RIGHT:
        changed_pos = hx - b
        if changed_pos > -GRID_LENGTH:
            hx = changed_pos

def mouseListener(button, state, x, y):
    if button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        pass

# ============================
# Camera & loop
# ============================

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, 1.1, 100, 1500)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    x, y, z = camera_pos
    gluLookAt(x, y, z, 0, 0, 0, 0, 0, 1)

def idle():
    global random_var, last_t, hit, strike, speed_change_score
    global life, score, misses, spawn_time_tracker
    global consecutive_green_hits, in_bonus_round
    global strike_rotate, strike_direction

    # advance pulse
    random_var += 1
    period = max(spawn_time_tracker, 1)
    t = random_var % period

    # Bonus timer check
    if in_bonus_round:
        now = glutGet(GLUT_ELAPSED_TIME)
        if now >= bonus_end_time_ms:
            end_bonus_round()

    respawned_this_frame = False

    if not game_over:
        # ------- Strike resolution -------
        if hit:
            inc = 5
            if strike_direction == 1:
                inc = 1
            strike += inc*strike_direction
            if strike > 250:
                strike_rotate = 10*strike_direction
            if strike >= 350:
                strike_direction *= -1
            # Intersect the sphere boundary?
            if strike <= draw_r:
                if check_same_cell():
                    # Correct cell
                    if color_changer == 1:   # red -> penalty, break combo
                        life -= 1
                        consecutive_green_hits = 0
                    else:                    # green -> reward, advance combo
                        score += 1
                        speed_change_score += 1
                        consecutive_green_hits += 1

                        # Trigger bonus on 5 green hits in a row
                        if consecutive_green_hits >= 5 and not in_bonus_round:
                            trigger_bonus_round()

                        # Speed change ONLY after every 10 points
                        if speed_change_score >= SPEED_CHANGE_SCORE_LIMIT:
                            speed_change_score = 0
                            spawn_time_tracker = max(
                                MIN_SPAWN_PERIOD, 
                                spawn_time_tracker - PULSE_DECAY_STEP
                            )

                    enemy_position()
                    # reset pulse so new enemy starts at radius 0
                    random_var = 0
                    t = 0
                    respawned_this_frame = True
                else:
                    # WRONG CELL: end strike and break combo (no score, no speed change)
                    consecutive_green_hits = 0

                # end the strike either way
                hit = False
                strike = 250
                strike_direction = 1

        # --- Pulse wrap (radius reached 0 naturally) ---
        # No speed change on timeouts; only score-based reductions every 10 points.
        if (not respawned_this_frame) and (t < last_t):
            if in_bonus_round:
                # Bonus: no miss penalty, still respawn in fixed row (green only)
                enemy_position()
            else:
                # Normal: count a miss ONLY if the expiring enemy was green
                was_green = (color_changer == 0)
                enemy_position()
                if was_green:
                    misses += 1
                    consecutive_green_hits = 0

            # Reset the pulse (no spawn period change here)
            random_var = 0
            t = 0

        check_end_conditions()

    last_t = t
    glutPostRedisplay()

def showScreen():
    global strike_rotate
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    setupCamera()

    #board ground
    glPushMatrix()
    glColor3f(0.3, 0.3, 0.4)
    glTranslatef(0, 150, 0)
    glutSolidCube(590)
    glPopMatrix()

    # board (6x6)
    glBegin(GL_QUADS)
    length = (2 * GRID_LENGTH) / 6

    for i in range(0, 6):
        # Row base color pattern
        for j in range(0, 6):
            if i % 2 == 0:
                clr = [1, 1, 1] if j % 2 == 0 else [0.5, 0.5, 0.5]
            else:
                clr = [1, 1, 1] if j % 2 != 0 else [0.5, 0.5, 0.5]

            # Tint the bonus row with a light golden color
            if in_bonus_round and i == bonus_row_index:
                # Blend towards gold-ish tone
                gold = [1.0, 0.95, 0.6]
                alpha = 0.6  # how strong the tint is
                clr = [
                    (1 - alpha) * clr[0] + alpha * gold[0],
                    (1 - alpha) * clr[1] + alpha * gold[1],
                    (1 - alpha) * clr[2] + alpha * gold[2],
                ]

            glColor3f(*clr)
            glVertex3f(-GRID_LENGTH + length*j, -GRID_LENGTH + length*i, 0)
            glVertex3f(-GRID_LENGTH + length*j, -GRID_LENGTH + length*(i+1), 0)
            glVertex3f(-GRID_LENGTH + length*(j+1), -GRID_LENGTH + length*(i+1), 0)
            glVertex3f(-GRID_LENGTH + length*(j+1), -GRID_LENGTH + length*i, 0)

    glEnd()

    if not game_over:
        glPushMatrix()
        drawEnemy()
        glPopMatrix()

    # HUD
    if game_over:
        draw_text(10, 550, "GAME OVER! Press 'R' to Restart.")
    else:
        draw_text(10, 550, f"Life: {life}")
        draw_text(10, 530, f"Score: {score}")
        draw_text(10, 510, f"Misses: {misses}/{MISSES_LIMIT}")
        draw_text(10, 490, "Space=Strike  Arrows=Move  R=Restart")
        draw_text(10, 470, f"Combo (Green x5): {consecutive_green_hits}/5")
        if in_bonus_round:
            remaining = max(0, (bonus_end_time_ms - glutGet(GLUT_ELAPSED_TIME)) // 1000)
            draw_text(10, 450, f"BONUS ROUND! Row {bonus_row_index+1}  ({remaining}s left)")

    # hammer + shadow
    glPushMatrix()
    if game_over:
        glTranslatef(-100,50,0)
    else:
        glTranslatef(hx, hy, 0)
    glPushMatrix()
    glScalef(0.5, 0.5, 0.5)
    if game_over:
        glScalef(2, 2, 2)
        glRotatef(90, 0, 1, 0)
        glRotatef(45, 1, 0, 0)
    else:
        glRotatef(5, -1, -1, 0)
        glRotatef(strike_rotate, -1, 0, 0)
        glTranslatef(0, 0, strike)
    draw_hammer()
    glPopMatrix()
    if not game_over:
        draw_shadow()
    glPopMatrix()

    glutSwapBuffers()

# ============================
# Main
# ============================

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 570)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"3D OpenGL Intro")

    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    glutMainLoop()

if __name__ == "__main__":
    main()
