import pygame
import math
import functools
import art
from art import aadraw   # anti-aliased drop-in for pygame.draw (see CLAUDE.md "Rendering rule")
from constants import *


@functools.lru_cache(maxsize=None)
def _font(name: str, size: int, bold: bool = False) -> pygame.font.Font:
    return pygame.font.SysFont(name, size, bold=bold)


def draw_ollie_sprite(surf, sx, sy, facing=1, anim_state="idle", frame=0, tail_angle=0.0):
    """
    Draw Ollie at pixel top-left (sx, sy).  Callable from any screen — not just gameplay.
    facing: 1=right, -1=left
    """
    flip = facing == -1
    state = anim_state
    t = frame

    body_color = APRICOT
    curl_color = PEACH

    leg_off = int(math.sin(t * 0.3) * 4) if state == "run" else 0

    # Body
    aadraw.ellipse(surf, body_color, (sx + 8, sy + 20, 32, 24))

    # Fluffy chest
    aadraw.circle(surf, curl_color, (sx + 22, sy + 28), 10)
    aadraw.circle(surf, curl_color, (sx + 14, sy + 26), 7)
    aadraw.circle(surf, curl_color, (sx + 30, sy + 26), 7)

    # Head
    aadraw.circle(surf, body_color, (sx + 24, sy + 14), 14)

    # Fluffy head puffs — tight curls for the poodle look
    for ox in [-6, 0, 6]:
        aadraw.circle(surf, curl_color, (sx + 24 + ox, sy + 8), 7)
    for ox, oy in [(-10, 6), (10, 6), (-4, 3), (4, 3)]:
        aadraw.circle(surf, curl_color, (sx + 24 + ox, sy + 8 + oy), 4)

    # Eye
    ex = sx + 30 if not flip else sx + 18
    aadraw.circle(surf, BLACK, (ex, sy + 13), 3)
    aadraw.circle(surf, WHITE, (ex + 1, sy + 12), 1)

    # Nose
    nx = sx + 33 if not flip else sx + 15
    aadraw.ellipse(surf, (40, 20, 10), (nx, sy + 18, 7, 5))

    # Ear (behind the head, on the back side)
    ear_x = sx + 10 if not flip else sx + 30
    aadraw.ellipse(surf, APRICOT, (ear_x, sy + 10, 10, 16))
    aadraw.ellipse(surf, curl_color, (ear_x + 1, sy + 11, 8, 13))

    # Legs
    if state == "sit":
        # Haunches tucked to the sides, paws visible below the body
        aadraw.ellipse(surf, body_color, (sx + 4,  sy + 35, 16, 15))
        aadraw.ellipse(surf, body_color, (sx + 26, sy + 35, 16, 15))
        aadraw.circle(surf, curl_color,  (sx + 12, sy + 46), 5)
        aadraw.circle(surf, curl_color,  (sx + 34, sy + 46), 5)
    else:
        for i, lx in enumerate([12, 24]):
            bob = leg_off if i % 2 == 0 else -leg_off
            aadraw.rect(surf, body_color, (sx + lx, sy + 38 + bob, 8, 10))
            aadraw.circle(surf, curl_color, (sx + lx + 4, sy + 48 + bob), 5)

    # Tail — rooted on the BACK of the dog (opposite side from face)
    ang = math.radians(tail_angle)
    tx = sx + (8 if not flip else 36)          # left when facing right, right when facing left
    ty = sy + 28
    tex = tx + int(math.cos(ang) * 14 * (-1 if not flip else 1))  # extends away from face
    tey = ty + int(math.sin(ang) * 14) - 6
    aadraw.line(surf, body_color, (tx, ty), (tex, tey), 4)

    # State overlays
    if state == "wag":
        pass  # tail movement is the wag indicator; no end-poof
    if state == "sad":
        for i in range(3):
            aadraw.line(surf, BLUE, (sx + 16 + i * 6, sy - 4), (sx + 14 + i * 6, sy - 12), 2)
    if state == "alert":
        mark = _font("Arial", 18, True).render("!", True, RED)
        surf.blit(mark, (sx + 20, sy - 20))
    if state == "celebrate":
        # Big smile arc
        aadraw.arc(surf, (200, 70, 50),
                        (sx + 16, sy + 18, 16, 9), math.pi, 2 * math.pi, 3)
        # Rosy cheeks
        chk_x = sx + 31 if not flip else sx + 15
        aadraw.circle(surf, (255, 170, 150), (chk_x, sy + 17), 5)
        # Star sparkles above head
        for i in range(4):
            ang = math.radians(i * 90 + t * 4)
            stx = sx + 24 + int(math.cos(ang) * 18)
            sty = sy - 10 + int(math.sin(ang) * 8)
            aadraw.circle(surf, GOLD, (stx, sty), 3)
            aadraw.circle(surf, WHITE, (stx, sty), 1)


class Player:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.w, self.h = OLLIE_SIZE
        self.vx = 0.0
        self.vy = 0.0
        self.on_ground = False
        self.facing = 1  # 1=right, -1=left
        self.health = MAX_HEALTH
        self.score = 0
        self.lives = 3

        # Animation
        self.anim_state = "idle"   # idle, run, jump, wag, sad, alert, slide
        self.anim_timer = 0
        self.frame = 0
        self.invincible = 0        # frames of invincibility after hit
        self.tail_angle = 0.0
        self.tail_dir = 1
        self.jumped_this_frame = False

        # Particles
        self.particles = []

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def handle_input(self, keys):
        self.jumped_this_frame = False
        self.vx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx = -PLAYER_SPEED
            self.facing = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx = PLAYER_SPEED
            self.facing = 1
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vy = JUMP_POWER
            self.on_ground = False
            self.jumped_this_frame = True

    def apply_gravity(self):
        self.vy += GRAVITY
        if self.vy > 18:
            self.vy = 18

    def move_and_collide(self, platforms):
        self.x += self.vx
        self._collide_x(platforms)
        self.y += self.vy
        self.on_ground = False
        self._collide_y(platforms)
        # World left boundary
        if self.x < 0:
            self.x = 0
        # World right boundary — platforms[0] is the ground and spans the whole level,
        # so Ollie can't walk off the end of the world and vanish off-screen
        if platforms and self.x > platforms[0].right - self.w:
            self.x = float(platforms[0].right - self.w)
        # Safety floor — if Ollie falls off the bottom of the screen, snap back to ground
        if self.y > SCREEN_HEIGHT + 40:
            self.y = float(GROUND_Y - self.h)
            self.vy = 0.0
            self.on_ground = True

    def _collide_x(self, platforms):
        r = self.rect
        for p in platforms:
            if p.y != GROUND_Y:
                continue  # elevated platforms are one-way — no side collision
            if r.colliderect(p):
                if self.vx > 0:
                    self.x = p.left - self.w
                elif self.vx < 0:
                    self.x = p.right
                self.vx = 0

    def _collide_y(self, platforms):
        for p in platforms:
            # self.rect truncates y to whole pixels, which hid the fraction of a
            # pixel Ollie sinks each frame from gravity — he only "landed" every
            # other frame, so on_ground (and the run animation) flickered while
            # standing.  Count that partial pixel as overlap.
            r = self.rect
            if self.y + self.h > r.bottom:
                r.height += 1
            if not r.colliderect(p):
                continue
            if self.vy > 0:
                # One-way: only land if Ollie's feet were at or above the platform
                # top before this frame's Y move (prevents popping up through from below)
                prev_bottom = (self.y - self.vy) + self.h
                if prev_bottom <= p.top + 1:
                    self.y = p.top - self.h
                    self.on_ground = True
                    self.vy = 0
            # vy <= 0: pass through all platforms — jump-through is always allowed

    def lose_life(self):
        """Direct -1 life hit (enemy contact). Respects invincibility window."""
        if self.invincible > 0:
            return False
        self.lives -= 1
        self.invincible = INVINCIBLE_FRAMES
        self.vx = 0.0   # stop sliding so player stays in control after hit
        self.set_anim("sad", INVINCIBLE_FRAMES)
        return True

    def take_damage(self, amount):
        """HP-based damage (slide hazard etc.). Separate from enemy life-loss."""
        if self.invincible > 0:
            return False
        self.health -= amount
        self.invincible = INVINCIBLE_FRAMES
        self.set_anim("sad")
        if self.health <= 0:
            self.health = 0
            self.lives -= 1
            self.health = MAX_HEALTH
        return True

    def set_anim(self, state, duration=60):
        self.anim_state = state
        self.anim_timer = duration

    def update(self, keys, platforms):
        self.handle_input(keys)
        self.apply_gravity()
        self.move_and_collide(platforms)

        if self.invincible > 0:
            self.invincible -= 1

        # Determine base animation
        if self.anim_timer > 0:
            self.anim_timer -= 1
        else:
            if not self.on_ground:
                self.anim_state = "jump"
            elif abs(self.vx) > 0.1:
                self.anim_state = "run"
            else:
                self.anim_state = "idle"

        # Tail wag
        self.tail_angle += 6 * self.tail_dir
        if abs(self.tail_angle) > 25:
            self.tail_dir *= -1

        # Frame counter
        self.frame = (self.frame + 1) % 60

        # Update particles
        self.particles = [(px, py, pvx, pvy, life - 1, color)
                          for px, py, pvx, pvy, life, color in self.particles if life > 1]
        self.particles = [(px + pvx, py + pvy, pvx, pvy * 0.9, life, color)
                          for px, py, pvx, pvy, life, color in self.particles]

    def add_sparkles(self):
        import random
        cx, cy = self.x + self.w // 2, self.y
        for _ in range(12):
            vx = random.uniform(-3, 3)
            vy = random.uniform(-4, -1)
            color = random.choice([GOLD, SUN_YELLOW, WHITE, PEACH])
            self.particles.append((cx, cy, vx, vy, 40, color))

    def add_blue_sparkles(self):
        import random
        cx, cy = self.x + self.w // 2, self.y
        for _ in range(14):
            vx = random.uniform(-3, 3)
            vy = random.uniform(-4, -1)
            color = random.choice([LIGHT_BLUE, BLUE, WHITE, (100, 200, 255)])
            self.particles.append((cx, cy, vx, vy, 45, color))

    def add_hearts(self):
        import random
        cx, cy = self.x + self.w // 2, self.y + 4
        for _ in range(10):
            vx = random.uniform(-2.5, 2.5)
            vy = random.uniform(-3.5, -1.0)
            self.particles.append((cx, cy, vx, vy, 55, PINK))

    def draw(self, surf, cam_x):
        sx = int(self.x - cam_x)
        sy = int(self.y)

        # Soft contact shadow grounds the sprite
        art.ground_shadow(surf, sx + self.w // 2, sy + self.h - 1,
                          self.w + 4, 12, 70)

        if self.invincible > 0:
            # Alternate between visible-with-red-flash and invisible every 5 frames
            visible = (self.invincible // 5) % 2 == 0
            if visible:
                self._draw_ollie(surf, sx, sy)
                flash = pygame.Surface((self.w + 4, self.h + 4), pygame.SRCALPHA)
                flash.fill((220, 50, 50, 110))
                surf.blit(flash, (sx - 2, sy - 2))
            # Particles always draw so sparkles don't stutter
            for px, py, pvx, pvy, life, color in self.particles:
                r = max(2, life // 10)
                aadraw.circle(surf, color, (int(px - cam_x), int(py)), r)
            return

        self._draw_ollie(surf, sx, sy)

        # Draw particles
        for px, py, pvx, pvy, life, color in self.particles:
            r = max(2, life // 10)
            aadraw.circle(surf, color, (int(px - cam_x), int(py)), r)

    def _draw_ollie(self, surf, sx, sy):
        draw_ollie_sprite(surf, sx, sy, self.facing, self.anim_state, self.frame, self.tail_angle)
