"""
Level 3 — Heaven.

Ollie rides the magic carpet up through the clouds, then must make his way
across the kingdom of heaven:  past the floaty "weird" Cloud Spirits, scooping
up as much money (coins) as he can, all the way up the Great Staircase to the
pearly gates where the Singing Angels are overjoyed to see him — and finally to
God on a flying throne.  One touch and Ollie has no more pain and all the food
he could ever want, and he gets a home to live in up in heaven.

Layout (8 000 px):
  Cloud Landing     0–1 300   gentle hop-clouds, "Welcome to Heaven"
  Spirit Gauntlet   1 300–4 600   weird Cloud Spirits + showers of coins
  Great Staircase   4 600–6 500   ascending cloud steps climbing skyward
  Pearly Gates      6 500–7 400   the Singing Angels greet Ollie
  God's Throne      7 400–8 000   the flying throne — touch it to win

Same interface as Level / Level2 (update / update_camera / draw_background /
draw_world / draw_characters / .events / .platforms / .camera_x / .width) so
game.py drives it exactly like the other levels.  Coins reuse the ("score", …)
event; the throne emits ("reached_god",).
"""

import pygame
import math
import random
import functools
import art
from art import aadraw   # anti-aliased drop-in for pygame.draw (see CLAUDE.md "Rendering rule")
from constants import *


@functools.lru_cache(maxsize=None)
def _font(name: str, size: int, bold: bool = False) -> pygame.font.Font:
    return pygame.font.SysFont(name, size, bold=bold)


def _plat(x, y, w):
    return pygame.Rect(x, y, w, PLATFORM_THICK)


@functools.lru_cache(maxsize=64)
def _cloud_sprite(w, h, color):
    """Pre-rendered cloud (a cluster of overlapping ellipses), centred in a
    2w x 2h surface.  Clouds only come in a handful of sizes, so drawing each
    one once and blitting it is far cheaper than ~10 anti-aliased ellipses per
    cloud per frame."""
    spr = pygame.Surface((w * 2, h * 2), pygame.SRCALPHA)
    cx, cy = w, h
    puffs = [(-w * 0.34, h * 0.10, w * 0.42, h * 0.62),
             (w * 0.34, h * 0.10, w * 0.42, h * 0.62),
             (-w * 0.12, -h * 0.18, w * 0.50, h * 0.78),
             (w * 0.16, -h * 0.12, w * 0.46, h * 0.74),
             (0, h * 0.20, w * 0.72, h * 0.56)]
    for ox, oy, ew, eh in puffs:
        # Each puff goes on its own layer and is alpha-blitted on: drawing them
        # straight onto one transparent surface lets each soft edge punch a
        # see-through seam into the puffs underneath.  The MAX fill restores the
        # full colour on the soft edge pixels (gfxdraw darkens them against the
        # transparent backdrop) while leaving their alpha alone.
        layer = pygame.Surface(spr.get_size(), pygame.SRCALPHA)
        aadraw.ellipse(layer, color, (cx + ox - ew / 2, cy + oy - eh / 2, ew, eh))
        layer.fill((*color[:3], 0), special_flags=pygame.BLEND_RGBA_MAX)
        spr.blit(layer, (0, 0))
    return spr


def _cloud(surf, cx, cy, w, h, color=(255, 255, 255), shadow=False):
    """A soft fluffy cloud centred at (cx, cy).  Used for the floor, the
    platforms and the throne."""
    if shadow:
        art.ground_shadow(surf, cx, int(cy + h * 0.45), int(w * 0.9), int(h * 0.4), 50)
    surf.blit(_cloud_sprite(int(w), int(h), color), (int(cx) - int(w), int(cy) - int(h)))


@functools.lru_cache(maxsize=1)
def _god_rays():
    """Screen-fixed god-rays overlay — static, so rendered once."""
    rays = pygame.Surface((SCREEN_WIDTH, GROUND_Y), pygame.SRCALPHA)
    origin = (int(SCREEN_WIDTH * 0.7), -60)
    for i in range(7):
        bx = i * (SCREEN_WIDTH // 6)
        aadraw.polygon(rays, (255, 250, 220, 16),
                       [origin, (bx - 70, GROUND_Y), (bx + 70, GROUND_Y)])
    return rays


def _on_screen(obj, cam_x, margin=200):
    """True if obj is within `margin` px of the visible screen (skip drawing otherwise)."""
    sx = obj.x - cam_x
    return -obj.w - margin < sx < SCREEN_WIDTH + margin


# ──────────────────────────────────────────────────────────────────────────────
# Coin — the "money" Ollie collects (brand-new pickup mechanic for Level 3)
# ──────────────────────────────────────────────────────────────────────────────
class Coin:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.w, self.h = COIN_SIZE
        self.frame = random.randint(0, 60)   # desync the spin/bob between coins
        self.collected = False
        self.active = True

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, player, platforms):
        self.frame += 1
        if self.collected:
            return None
        if self.rect.colliderect(player.rect):
            self.collected = True
            return "coin"
        return None

    def draw(self, surf, cam_x):
        if self.collected:
            return
        bob = int(math.sin(self.frame * 0.1) * 4)
        cx = int(self.x - cam_x) + self.w // 2
        cy = int(self.y) + self.h // 2 + bob
        # Soft golden glow
        surf.blit(art.radial_glow(20, (255, 225, 90), 60), (cx - 20, cy - 20))
        # Spin: width pulses like a rotating disc
        rw = max(3, int(abs(math.cos(self.frame * 0.12)) * self.w))
        rh = self.h
        aadraw.ellipse(surf, (210, 160, 20), (cx - rw // 2, cy - rh // 2, rw, rh))
        aadraw.ellipse(surf, GOLD,           (cx - rw // 2 + 2, cy - rh // 2 + 2, max(1, rw - 4), rh - 4))
        if rw > 10:
            aadraw.ellipse(surf, (255, 240, 170), (cx - rw // 2 + 4, cy - rh // 2 + 4, rw - 8, rh - 8), 2)
            # little dollar mark / shine
            aadraw.line(surf, (210, 160, 20), (cx, cy - 6), (cx, cy + 6), 2)
            aadraw.circle(surf, WHITE, (cx - rw // 6, cy - rh // 4), 2)


# ──────────────────────────────────────────────────────────────────────────────
# Cloud Spirit — the floaty "weird people" Ollie must get past
# ──────────────────────────────────────────────────────────────────────────────
class CloudSpirit:
    PALETTE = [(206, 188, 244), (190, 220, 246), (246, 206, 226),
               (206, 240, 220), (244, 226, 196)]

    def __init__(self, x, patrol_left, patrol_right, base_y, tint=0):
        self.x = float(x)
        self.base_y = float(base_y)
        self.y = float(base_y)
        self.w, self.h = SPIRIT_SIZE
        self.spawn_x = float(x)
        self.patrol_left = patrol_left
        self.patrol_right = patrol_right
        self.dir = 1
        self.facing = 1
        self.frame = random.randint(0, 120)
        self.color = self.PALETTE[tint % len(self.PALETTE)]
        self.state = "patrol"
        self.active = True

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, player, platforms):
        self.frame = (self.frame + 1) % 240
        if not self.active:
            return None

        if abs(player.x - self.spawn_x) > ENEMY_RESPAWN_DIST:
            self.x = self.spawn_x
            self.state = "patrol"

        dx = player.x - self.x
        dist = abs(dx)
        self.state = "chase" if dist < SPIRIT_CHASE_RAD else "patrol"

        if self.state == "chase":
            if dist > 14:   # dead-zone so it doesn't jitter right under Ollie
                self.dir = 1 if dx > 0 else -1
                self.x += self.dir * SPIRIT_CHASE_SPD
        else:
            self.x += self.dir * SPIRIT_PATROL_SPD
            if self.x <= self.patrol_left:
                self.x = float(self.patrol_left)
                self.dir = 1
            elif self.x >= self.patrol_right:
                self.x = float(self.patrol_right)
                self.dir = -1
        self.facing = self.dir

        # Drift up and down like a balloon
        self.y = self.base_y + math.sin(self.frame * 0.06) * 14

        if self.rect.colliderect(player.rect):
            return "life_damage"
        if ENEMY_ALERT_RAD > dist > SPIRIT_CHASE_RAD * 0.7:
            return "alert"
        return None

    def draw(self, surf, cam_x):
        if not self.active:
            return
        w, h = self.w, self.h
        pad = 22
        spr = pygame.Surface((w + pad * 2, h + pad * 2), pygame.SRCALPHA)
        cx, cy = w // 2 + pad, h // 2 + pad
        sgn = 1 if self.facing >= 0 else -1
        wob = math.sin(self.frame * 0.12) * 3

        # Outer glow aura
        aadraw.circle(spr, (*self.color, 60), (cx, cy), w // 2 + 14)
        aadraw.circle(spr, (*self.color, 90), (cx, cy), w // 2 + 6)

        # Wobbly ghost-like body — rounded top, wavy tendril bottom
        body_top = cy - h // 2 + 6
        aadraw.ellipse(spr, (*self.color, 225), (cx - w // 2, body_top, w, h - 6))
        tend_y = body_top + h - 12
        for i in range(4):
            tx = cx - w // 2 + 6 + i * (w - 12) // 3
            bump = 8 + int(math.sin(self.frame * 0.18 + i) * 4)
            aadraw.circle(spr, (*self.color, 225), (tx, int(tend_y + bump)), 7)
        # Lighter belly sheen
        aadraw.ellipse(spr, (255, 255, 255, 110), (cx - w // 4, body_top + 6, w // 2, h // 2))

        # Two big googly eyes that look toward Ollie
        for eo in (-9, 9):
            ex = cx + eo + int(sgn * 2)
            ey = cy - 6 + int(wob)
            aadraw.circle(spr, (255, 255, 255, 255), (ex, ey), 8)
            aadraw.circle(spr, (60, 60, 90, 255), (ex + sgn * 2, ey + 1), 4)
            aadraw.circle(spr, (255, 255, 255, 255), (ex + sgn * 2 + 1, ey), 1)
        # Little surprised 'o' mouth + rosy cheeks
        aadraw.ellipse(spr, (120, 90, 120, 220), (cx - 4, cy + 8, 8, 7))
        aadraw.circle(spr, (255, 170, 180, 150), (cx - 16, cy + 4), 3)
        aadraw.circle(spr, (255, 170, 180, 150), (cx + 16, cy + 4), 3)
        # Stubby wavy arms
        for s in (-1, 1):
            ax = cx + s * (w // 2 - 2)
            aadraw.line(spr, (*self.color, 235), (ax, cy + 2),
                        (ax + s * 8, cy - 4 + int(wob * s)), 5)

        sx = int(self.x - cam_x) - pad
        surf.blit(spr, (sx, int(self.y) - pad))


# ──────────────────────────────────────────────────────────────────────────────
# Singing Angel — friendly greeter at the pearly gates (purely joyful, no harm)
# ──────────────────────────────────────────────────────────────────────────────
class SingingAngel:
    def __init__(self, x, feet_y, tint=0):
        self.w, self.h = SING_ANGEL_SIZE
        self.x = float(x)
        self.y = float(feet_y - self.h)
        self.frame = random.randint(0, 120)
        self.notes = []   # floating musical notes: [x, y, vx, vy, life]
        self.active = True
        self.greeting = False
        self.robe = [(245, 245, 255), (255, 244, 224), (244, 248, 255)][tint % 3]

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, player, platforms):
        self.frame += 1
        dist = abs(player.x - (self.x + self.w / 2))
        self.greeting = dist < 360

        # Sing faster when Ollie is close
        rate = 16 if self.greeting else 30
        if self.frame % rate == 0:
            self.notes.append([self.x + self.w / 2 + random.uniform(-10, 18),
                               self.y + 6, random.uniform(-0.4, 0.8),
                               random.uniform(-1.4, -0.9), 46])
        self.notes = [[nx + vx, ny + vy, vx, vy, life - 1]
                      for nx, ny, vx, vy, life in self.notes if life > 1]
        return None   # angels never hurt Ollie — they're just happy to see him

    def _note(self, surf, x, y, alpha, cam_x):
        col = (255, 240, 170, alpha)
        aadraw.ellipse(surf, col, (int(x - cam_x) - 4, int(y), 8, 6))
        aadraw.line(surf, col, (int(x - cam_x) + 3, int(y)), (int(x - cam_x) + 3, int(y) - 12), 2)
        aadraw.line(surf, col, (int(x - cam_x) + 3, int(y) - 12), (int(x - cam_x) + 9, int(y) - 9), 2)

    def draw(self, surf, cam_x):
        sx = int(self.x - cam_x)
        bob = int(math.sin(self.frame * 0.08) * 4)
        sy = int(self.y) + bob
        cx = sx + self.w // 2

        # Floating notes (drawn behind so the angel sits in front)
        for nx, ny, vx, vy, life in self.notes:
            self._note(surf, nx, ny + bob, max(0, min(255, life * 5)), cam_x)

        # Soft halo glow
        surf.blit(art.radial_glow(34, (255, 244, 180), 70), (cx - 34, sy - 16))

        # Wings — gently flapping behind the body
        wf = int(math.sin(self.frame * 0.18) * 6)
        for side in (-1, 1):
            base_x = cx + side * 8
            for k, (col, ww, hh) in enumerate([((212, 220, 248), 30, 32),
                                               ((236, 240, 252), 22, 24),
                                               (WHITE, 14, 16)]):
                aadraw.ellipse(surf, col,
                               (base_x + side * (3 + k * 4) - ww // 2,
                                sy + 16 - wf + k * 3, ww, hh))

        # Flowing robe
        aadraw.polygon(surf, self.robe, [(cx - 15, sy + 26), (cx + 15, sy + 26),
                                         (cx + 21, sy + 66), (cx - 21, sy + 66)])
        aadraw.polygon(surf, art.shade(self.robe, 0.92),
                       [(cx, sy + 26), (cx + 15, sy + 26), (cx + 21, sy + 66), (cx, sy + 66)])
        aadraw.line(surf, GOLD, (cx - 20, sy + 64), (cx + 20, sy + 64), 2)

        # Arms — raised in joyful song
        raise_amt = 10 if self.greeting else 4
        aadraw.line(surf, (255, 234, 206), (cx - 9, sy + 30), (cx - 17, sy + 24 - raise_amt), 4)
        aadraw.line(surf, (255, 234, 206), (cx + 9, sy + 30), (cx + 17, sy + 24 - raise_amt), 4)

        # Head + serene singing face (open little mouth, rosy cheeks)
        aadraw.circle(surf, (255, 232, 198), (cx, sy + 14), 11)
        aadraw.circle(surf, (255, 190, 175), (cx - 5, sy + 16), 2)
        aadraw.circle(surf, (255, 190, 175), (cx + 5, sy + 16), 2)
        aadraw.arc(surf, (90, 60, 40), (cx - 6, sy + 10, 5, 4), 0, math.pi, 2)
        aadraw.arc(surf, (90, 60, 40), (cx + 1, sy + 10, 5, 4), 0, math.pi, 2)
        aadraw.ellipse(surf, (180, 90, 90), (cx - 3, sy + 17, 6, 5))   # singing mouth

        # Glowing halo ring
        halo_y = sy + 1 + int(math.sin(self.frame * 0.1) * 2)
        aadraw.ellipse(surf, GOLD, (cx - 12, halo_y - 3, 24, 8), 3)


# ──────────────────────────────────────────────────────────────────────────────
# God's flying throne — the goal of Level 3
# ──────────────────────────────────────────────────────────────────────────────
class GodThrone:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.w, self.h = THRONE_SIZE
        self.frame = 0
        self.active = True
        self.reached = False

    @property
    def rect(self):
        # Touch zone is the lower half (where the figure / seat is) so Ollie
        # standing on the cloud platform reaches it by walking in.
        return pygame.Rect(int(self.x + 14), int(self.y + self.h // 2),
                           self.w - 28, self.h // 2 + 20)

    def update(self, player, platforms):
        self.frame += 1
        if not self.active or self.reached:
            return None
        if self.rect.colliderect(player.rect):
            self.reached = True
            return "reached_god"
        return None

    def draw(self, surf, cam_x):
        sx = int(self.x - cam_x)
        sy = int(self.y)
        cx = sx + self.w // 2
        float_y = int(math.sin(self.frame * 0.05) * 6)
        sy += float_y

        # Huge radiant glow behind everything
        pulse = 0.8 + 0.2 * math.sin(self.frame * 0.08)
        surf.blit(art.radial_glow(190, (255, 244, 180), int(120 * pulse) // 4 * 4),
                  (cx - 190, sy + self.h // 2 - 190))

        # Radiating beams of light
        beam = pygame.Surface((self.w + 240, self.h + 240), pygame.SRCALPHA)
        bcx, bcy = (self.w + 240) // 2, (self.h + 240) // 2
        for i in range(12):
            ang = math.radians(i * 30 + self.frame * 0.4)
            ex = bcx + math.cos(ang) * 300
            ey = bcy + math.sin(ang) * 300
            aadraw.polygon(beam, (255, 248, 200, 26),
                           [(bcx, bcy),
                            (ex + math.cos(ang + 0.05) * 8, ey + math.sin(ang + 0.05) * 8),
                            (ex - math.cos(ang + 0.05) * 8, ey - math.sin(ang + 0.05) * 8)])
        surf.blit(beam, (cx - bcx, sy + self.h // 2 - bcy))

        # Little clouds the throne floats on
        _cloud(surf, cx, sy + self.h - 6, self.w + 30, 34, (250, 250, 255))

        # Golden throne — tall ornate back + seat
        back = (236, 196, 70)
        back_dk = (198, 150, 36)
        aadraw.rect(surf, back, (cx - 40, sy + 18, 80, self.h - 36), border_radius=14)
        aadraw.rect(surf, back_dk, (cx - 40, sy + 18, 80, self.h - 36), 3, border_radius=14)
        # Throne crown points
        for ox in (-30, 0, 30):
            aadraw.polygon(surf, GOLD, [(cx + ox - 9, sy + 22), (cx + ox + 9, sy + 22),
                                        (cx + ox, sy + 2)])
            aadraw.circle(surf, (255, 240, 170), (cx + ox, sy + 4), 3)
        # Armrests
        for s in (-1, 1):
            aadraw.rect(surf, back, (cx + s * 40 - 8, sy + self.h // 2, 16, 40), border_radius=6)

        # The radiant figure — a gentle, glowing presence (kept abstract & warm)
        fy = sy + 40
        # Robe of light
        aadraw.polygon(surf, (255, 255, 250),
                       [(cx - 22, fy + 18), (cx + 22, fy + 18),
                        (cx + 30, fy + 78), (cx - 30, fy + 78)])
        aadraw.polygon(surf, (255, 248, 224),
                       [(cx, fy + 18), (cx + 22, fy + 18), (cx + 30, fy + 78), (cx, fy + 78)])
        aadraw.line(surf, GOLD, (cx - 28, fy + 74), (cx + 28, fy + 74), 3)
        # Welcoming open arms
        aadraw.line(surf, (255, 252, 238), (cx - 14, fy + 26), (cx - 34, fy + 14), 6)
        aadraw.line(surf, (255, 252, 238), (cx + 14, fy + 26), (cx + 34, fy + 14), 6)
        aadraw.circle(surf, (255, 252, 238), (cx - 36, fy + 12), 4)
        aadraw.circle(surf, (255, 252, 238), (cx + 36, fy + 12), 4)
        # Head wreathed in light + serene, kind face
        aadraw.circle(surf, (255, 246, 224), (cx, fy + 2), 15)
        aadraw.arc(surf, (150, 120, 80), (cx - 7, fy - 1, 6, 5), 0, math.pi, 2)
        aadraw.arc(surf, (150, 120, 80), (cx + 1, fy - 1, 6, 5), 0, math.pi, 2)
        aadraw.arc(surf, (200, 140, 120), (cx - 6, fy + 6, 12, 6), 0, math.pi, 2)  # gentle smile
        # Brilliant halo
        for r, a in [(30, 50), (24, 90), (18, 140)]:
            ring = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            aadraw.circle(ring, (255, 248, 190, a), (r + 2, r + 2), r, 3)
            surf.blit(ring, (cx - r - 2, fy - 16 - r))

        # Orbiting sparkles
        for i in range(7):
            ang = self.frame * 0.04 + i * (2 * math.pi / 7)
            stx = cx + int(math.cos(ang) * (self.w // 2 + 16))
            sty = sy + self.h // 2 + int(math.sin(ang) * (self.h // 2))
            aadraw.circle(surf, SUN_YELLOW, (stx, sty), 3)
            aadraw.circle(surf, WHITE, (stx, sty), 1)

        # Welcoming label
        lbl = _font("Arial", 16, True).render("Come home, Ollie", True, (180, 130, 30))
        bg = pygame.Surface((lbl.get_width() + 14, lbl.get_height() + 8), pygame.SRCALPHA)
        bg.fill((255, 255, 255, 150))
        surf.blit(bg, (cx - bg.get_width() // 2, sy - 26))
        surf.blit(lbl, (cx - lbl.get_width() // 2, sy - 22))


# ──────────────────────────────────────────────────────────────────────────────
# Level3
# ──────────────────────────────────────────────────────────────────────────────
class Level3:
    """8 000 px sky level: pass the Cloud Spirits, gather coins, climb the great
    staircase to the Singing Angels, and touch God on the flying throne."""

    def __init__(self):
        self.width = LEVEL3_WIDTH
        self.camera_x = 0.0

        # ── Platforms ────────────────────────────────────────────────────
        # platforms[0] is the single continuous cloud floor (no gaps!).
        self.platforms = [
            _plat(0, GROUND_Y, LEVEL3_WIDTH),     # continuous cloud floor

            # Cloud Landing — gentle warm-up hops
            _plat(360, 500, 150),
            _plat(650, 452, 150),
            _plat(960, 500, 150),

            # Spirit Gauntlet — hop-clouds for coins while dodging spirits
            _plat(1500, 470, 150),
            _plat(1830, 430, 150),
            _plat(2160, 480, 150),
            _plat(2500, 440, 150),
            _plat(2850, 470, 160),
            _plat(3200, 430, 150),
            _plat(3560, 480, 150),
            _plat(3900, 440, 160),
            _plat(4250, 470, 150),

            # Great Staircase — climbs from the floor up into the high heavens
            _plat(4650, 520, 150),
            _plat(4920, 470, 150),
            _plat(5190, 420, 150),
            _plat(5460, 370, 150),
            _plat(5730, 320, 150),
            _plat(6000, 270, 150),
            _plat(6270, 232, 170),

            # Pearly Gates landing — where the Singing Angels stand
            _plat(6540, 232, 380),
            _plat(7000, 232, 320),

            # God's high cloud — the flying throne rests here
            _plat(7400, 200, 380),
        ]

        # ── Coins (money) — scattered generously across the whole climb ───
        coin_spots = [
            (300, 500), (470, 452), (700, 408), (1010, 456), (1180, 536),
            (1560, 426), (1720, 536), (1890, 388), (2070, 500), (2220, 440),
            (2560, 398), (2740, 536), (2910, 428), (3090, 520), (3260, 388),
            (3430, 536), (3620, 438), (3800, 520), (3960, 398), (4140, 520),
            (4310, 428), (4520, 536),
            (4720, 482), (4990, 432), (5260, 382), (5530, 332),
            (5800, 282), (6070, 232), (6340, 194),
            (6700, 194), (7080, 194), (7300, 162),
        ]
        self.coins = [Coin(x, y) for x, y in coin_spots]

        # ── Cloud Spirits — the "weird people" ───────────────────────────
        self.spirits = [
            CloudSpirit(1600, 1400, 1980, GROUND_Y - SPIRIT_SIZE[1], 0),
            CloudSpirit(2230, 2000, 2520, 470, 1),
            CloudSpirit(2750, 2520, 3050, GROUND_Y - SPIRIT_SIZE[1], 2),
            CloudSpirit(3170, 2900, 3460, 430, 3),
            CloudSpirit(3560, 3300, 3860, GROUND_Y - SPIRIT_SIZE[1], 4),
            CloudSpirit(3980, 3700, 4260, 442, 0),
            CloudSpirit(4360, 4140, 4560, GROUND_Y - SPIRIT_SIZE[1], 1),
            CloudSpirit(5180, 5020, 5400, 360, 2),
            CloudSpirit(5880, 5740, 6080, 262, 3),
        ]

        # ── Singing Angels at the pearly gates ───────────────────────────
        self.angels = [
            SingingAngel(6600, 232, 0),
            SingingAngel(6740, 232, 1),
            SingingAngel(6880, 232, 2),
            SingingAngel(7060, 232, 0),
            SingingAngel(7210, 232, 1),
        ]

        # ── God on the flying throne (the goal) ──────────────────────────
        self.throne = GodThrone(7470, 50)

        self.start_hint_timer = 240
        self.events = []

        # Composed sky layer (see draw_background) and the warm tint it was built for
        self._sky = None
        self._sky_warm = -1

    # ────────────────────────────────────────────────────────────────────
    def update_camera(self, player_x):
        target = player_x - SCROLL_THRESH
        self.camera_x += (target - self.camera_x) * 0.12
        self.camera_x = max(0, min(self.camera_x, self.width - SCREEN_WIDTH))

    def update(self, player):
        self.events.clear()
        if self.start_hint_timer > 0:
            self.start_hint_timer -= 1

        for spirit in self.spirits:
            r = spirit.update(player, self.platforms)
            if r == "life_damage":
                self.events.append(("life_damage",))
            elif r == "alert":
                self.events.append(("alert",))

        for coin in self.coins:
            if coin.update(player, self.platforms) == "coin":
                self.events.append(("score", SCORE_COIN, "Coin!"))

        for angel in self.angels:
            angel.update(player, self.platforms)

        if self.throne.update(player, self.platforms) == "reached_god":
            self.events.append(("reached_god",))

        self.update_camera(player.x)

    # ────────────────────────────────────────────────────────────────────
    def draw_background(self, surf):
        cam = self.camera_x

        # Dreamy sky: soft periwinkle up top fading to warm gold near the floor.
        # Heaven brightens the closer Ollie gets to God (right side glows gold),
        # with soft screen-fixed god-rays on top.  All three layers only change
        # when the warm tint steps, so they are composed once per step and the
        # frame costs a single opaque blit.
        prog = min(1.0, max(0.0, (cam + SCREEN_WIDTH * 0.5) / self.width))
        warm_a = int(70 * prog) if prog > 0.05 else 0
        if self._sky is None or self._sky_warm != warm_a:
            sky = art.vgradient(SCREEN_WIDTH, GROUND_Y + 30,
                                (150, 168, 232), (255, 242, 206)).copy()
            if warm_a:
                warm = pygame.Surface(sky.get_size(), pygame.SRCALPHA)
                warm.fill((255, 236, 170, warm_a))
                sky.blit(warm, (0, 0))
            sky.blit(_god_rays(), (0, 0))
            self._sky, self._sky_warm = sky, warm_a
        surf.blit(self._sky, (0, 0))
        # Nothing else paints below the cloud floor, so clear it every frame —
        # otherwise leftovers from the previous screen show through and the
        # pause / game-over overlays darken it a little more each frame.
        surf.fill((255, 242, 206), (0, GROUND_Y + 30, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y - 30))

        # Big radiant glow around God's world position (parallax-locked)
        god_sx = int(7536 - cam)
        if -300 < god_sx < SCREEN_WIDTH + 300:
            surf.blit(art.radial_glow(260, (255, 246, 190), 70), (god_sx - 260, 120 - 260 + 200))

        # Layered drifting clouds (back layer slow, front layer faster)
        cloud_imgs = ["cloud_a", "cloud_b", "cloud_c", "cloud_d"]
        for i in range(20):
            cw = i * 430 + 60
            cy = 40 + (i % 5) * 70
            img = art.scaled_h("sky/" + cloud_imgs[i % 4] + ".png", 70 + (i % 3) * 26)
            sxp = int(cw - cam * 0.18) % (SCREEN_WIDTH + 500) - 250
            surf.blit(img, (sxp, cy))

        # Distant pearly gate silhouette behind the landing
        self._draw_far_gate(surf, cam)

    def _draw_far_gate(self, surf, cam):
        gx = int(6760 - cam * 0.6)   # gentle parallax
        if not (-400 < gx < SCREEN_WIDTH + 400):
            return
        top = 150
        col = (255, 244, 210)
        for ox in (-150, 150):
            aadraw.rect(surf, col, (gx + ox - 16, top, 32, GROUND_Y - top), border_radius=10)
            aadraw.circle(surf, (255, 236, 180), (gx + ox, top), 18)
        # Arch
        aadraw.arc(surf, col, (gx - 166, top - 70, 332, 160), 0, math.pi, 14)

    # ────────────────────────────────────────────────────────────────────
    def draw_world(self, surf):
        cam = self.camera_x

        # --- Fluffy cloud floor across the bottom ---
        # Warm underglow first, then a run of overlapping cloud puffs.
        glow = pygame.Surface((SCREEN_WIDTH, 60), pygame.SRCALPHA)
        glow.fill((255, 226, 150, 60))
        surf.blit(glow, (0, GROUND_Y + 6))
        seg = 150
        offset = int(cam) % seg
        for sx in range(-offset - seg, SCREEN_WIDTH + seg, seg):
            _cloud(surf, sx + seg // 2, GROUND_Y + 14, seg + 40, 64, (255, 255, 255))

        # --- Cloud platforms (the elevated ledges + the staircase) ---
        for p in self.platforms[1:]:
            psx = int(p.x - cam)
            if -p.width - 40 < psx < SCREEN_WIDTH + 40:
                _cloud(surf, psx + p.width // 2, p.y + 14, p.width + 30, 46,
                       (255, 255, 255), shadow=True)
                # bright standable lip so the edge reads
                lip = pygame.Surface((p.width, 6), pygame.SRCALPHA)
                lip.fill((255, 255, 255, 230))
                surf.blit(lip, (psx, p.y - 1))

        # --- "Welcome to Heaven" sign near the start ---
        wsx = int(160 - cam)
        if -260 < wsx < SCREEN_WIDTH:
            txt = _font("Arial", 26, True).render("Welcome to Heaven", True, (90, 110, 180))
            bg = pygame.Surface((txt.get_width() + 24, txt.get_height() + 14), pygame.SRCALPHA)
            bg.fill((255, 255, 255, 180))
            surf.blit(bg, (wsx, 150))
            pygame.draw.rect(surf, GOLD, (wsx, 150, bg.get_width(), bg.get_height()),
                             3, border_radius=10)
            surf.blit(txt, (wsx + 12, 157))

        # --- Friendly signposts pointing the way up ---
        for wx, msg in [(4500, "Up the stairs!"), (6450, "The Gates of Heaven")]:
            ssx = int(wx - cam)
            if -240 < ssx < SCREEN_WIDTH:
                lbl = _font("Arial", 18, True).render(msg, True, (110, 90, 170))
                bg = pygame.Surface((lbl.get_width() + 16, lbl.get_height() + 8), pygame.SRCALPHA)
                bg.fill((255, 255, 255, 170))
                surf.blit(bg, (ssx, 120))
                surf.blit(lbl, (ssx + 8, 124))

        # --- Beginner hint ---
        if self.start_hint_timer > 0 and self.camera_x < 200:
            alpha = 255 if (self.start_hint_timer // 20) % 2 == 0 else 110
            hint = _font("Arial", 22, True).render("Walk right  →", True, (90, 110, 190))
            hs = pygame.Surface((hint.get_width(), hint.get_height()), pygame.SRCALPHA)
            hs.blit(hint, (0, 0))
            hs.set_alpha(alpha)
            surf.blit(hs, (90, GROUND_Y - 96))

    def draw_characters(self, surf):
        cam = self.camera_x
        # Only draw what is near the screen — most of the 8 000 px level isn't
        for coin in self.coins:
            if _on_screen(coin, cam):
                coin.draw(surf, cam)
        for spirit in self.spirits:
            if _on_screen(spirit, cam):
                spirit.draw(surf, cam)
        for angel in self.angels:
            if _on_screen(angel, cam):
                angel.draw(surf, cam)
        if _on_screen(self.throne, cam, 320):   # wide margin for its glow and beams
            self.throne.draw(surf, cam)
