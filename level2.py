"""
Level 2 — Interior of Ollie's house.
Ollie must sniff through 7 rooms to find his crate and the big bone waiting inside.

Room layout (8 000 px):
  Entry Hall  0–1 000   Roomba + guard cat
  Living Room 1 000–2 200   couch/bookshelf platforming, Roomba
  Hallway     2 200–2 800   narrow, patrol cat
  Kitchen     2 800–4 000   counter jumps, cat
  Dining Room 4 000–5 000   table/chair hops, Roomba
  Library     5 000–6 400   staircase shelves, patrol cat
  Corridor    6 400–7 000   fast cat
  Bedroom     7 000–8 000   2 cats guard the crate
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
    return art.font(size, bold)   # `name` is kept for call-site readability only


def _plat(x, y, w):
    return pygame.Rect(x, y, w, PLATFORM_THICK)


# ──────────────────────────────────────────────────────────────────────────────
# HouseCat
# ──────────────────────────────────────────────────────────────────────────────
class HouseCat:
    def __init__(self, x, patrol_left, patrol_right):
        self.x = float(x)
        self.y = float(GROUND_Y - CAT_SIZE[1])
        self.w, self.h = CAT_SIZE
        self.spawn_x = float(x)
        self.patrol_left = patrol_left
        self.patrol_right = patrol_right
        self.dir = 1
        self.state = "patrol"
        self.frame = 0
        self.active = True

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, player, platforms):
        self.frame = (self.frame + 1) % 120
        if not self.active:
            return None

        if abs(player.x - self.spawn_x) > ENEMY_RESPAWN_DIST:
            self.x = self.spawn_x
            self.state = "patrol"

        dx = player.x - self.x
        dist = abs(dx)

        self.state = "chase" if dist < CAT_CHASE_RAD else "patrol"

        if self.state == "chase":
            # Dead-zone stops the cat jittering when it is right under Ollie
            if dist > 14:
                self.dir = 1 if dx > 0 else -1
                self.x += self.dir * CAT_CHASE_SPD
        else:
            self.x += self.dir * CAT_PATROL_SPD
            if self.x <= self.patrol_left:
                self.x = float(self.patrol_left)
                self.dir = 1
            elif self.x >= self.patrol_right:
                self.x = float(self.patrol_right)
                self.dir = -1

        if self.rect.colliderect(player.rect):
            return "life_damage"
        if ENEMY_ALERT_RAD > dist > CAT_CHASE_RAD * 0.7:
            return "alert"
        return None

    def draw(self, surf, cam_x):
        if not self.active:
            return
        sx = int(self.x - cam_x)
        sy = int(self.y)
        w, h = self.w, self.h
        flip = self.dir < 0
        sgn = 1 if not flip else -1

        ORG    = (236, 152, 66)
        ORG_DK = (198, 116, 40)
        CREAM  = (250, 230, 196)
        PINK   = (240, 168, 168)

        head_cx = sx + (w - 9 if not flip else 9)

        # Tail (back side), gently swishing
        tx = sx + (6 if not flip else w - 6)
        tw = int(math.sin(self.frame * 0.12) * 6)
        aadraw.line(surf, ORG, (tx, sy + 20), (tx - sgn * 11, sy + 6 + tw), 5)
        aadraw.circle(surf, ORG_DK, (tx - sgn * 11, sy + 5 + tw), 4)

        # Legs
        for lx in [sx + 11, sx + 19, sx + w - 20, sx + w - 12]:
            aadraw.rect(surf, ORG_DK, (lx, sy + 21, 5, 9))
            aadraw.circle(surf, ORG, (lx + 2, sy + 29), 3)

        # Body + tabby stripes
        aadraw.ellipse(surf, ORG, (sx + 5, sy + 11, w - 10, 16))
        for k in range(3):
            bx2 = sx + 14 + k * 8
            aadraw.line(surf, ORG_DK, (bx2, sy + 12), (bx2, sy + 24), 2)

        # Head
        aadraw.circle(surf, ORG, (head_cx, sy + 10), 9)
        # Ears (with pink inner)
        for ox in (-7, 7):
            aadraw.polygon(surf, ORG, [(head_cx + ox - 3, sy + 4),
                                       (head_cx + ox, sy - 5), (head_cx + ox + 3, sy + 4)])
            aadraw.polygon(surf, PINK, [(head_cx + ox - 1, sy + 3),
                                        (head_cx + ox, sy - 1), (head_cx + ox + 1, sy + 3)])
        # Muzzle
        aadraw.ellipse(surf, CREAM, (head_cx + sgn * 1 - 7, sy + 9, 14, 9))
        # Eye
        ex = head_cx + sgn * 3
        aadraw.circle(surf, (80, 180, 100), (ex, sy + 7), 3)
        aadraw.circle(surf, BLACK, (ex + sgn, sy + 7), 2)
        # Nose + whiskers
        nx = head_cx + sgn * 6
        aadraw.circle(surf, (210, 96, 96), (nx, sy + 11), 1)
        for wy in (-1, 2):
            aadraw.line(surf, WHITE, (nx, sy + 11 + wy), (nx + sgn * 12, sy + 10 + wy), 1)


# ──────────────────────────────────────────────────────────────────────────────
# Roomba — fast robot vacuum; Ollie must jump over it
# ──────────────────────────────────────────────────────────────────────────────
class Roomba:
    def __init__(self, x, patrol_left, patrol_right):
        self.x = float(x)
        self.y = float(GROUND_Y - ROOMBA_SIZE[1])
        self.w, self.h = ROOMBA_SIZE
        self.spawn_x = float(x)
        self.patrol_left = patrol_left
        self.patrol_right = patrol_right
        self.dir = 1
        self.frame = 0
        self.active = True

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, player, platforms):
        self.frame = (self.frame + 1) % 120
        if not self.active:
            return None

        if abs(player.x - self.spawn_x) > ENEMY_RESPAWN_DIST:
            self.x = self.spawn_x
            self.dir = 1

        dx = player.x - self.x
        if abs(dx) < ROOMBA_CHASE_RAD:
            # Dead-zone stops the Roomba jittering when it is right under Ollie
            if abs(dx) > 14:
                self.dir = 1 if dx > 0 else -1
                self.x += self.dir * ROOMBA_CHASE_SPD
        else:
            self.x += self.dir * ROOMBA_PATROL_SPD
            if self.x <= self.patrol_left:
                self.x = float(self.patrol_left)
                self.dir = 1
            elif self.x >= self.patrol_right:
                self.x = float(self.patrol_right)
                self.dir = -1

        if self.rect.colliderect(player.rect):
            return "life_damage"
        return None

    def draw(self, surf, cam_x):
        if not self.active:
            return
        sx = int(self.x - cam_x)
        sy = int(self.y)
        cx = sx + self.w // 2
        cy = sy + self.h // 2
        rw, rh = self.w, self.h

        BODY    = (54, 56, 64)
        DOME    = (92, 96, 108)
        DOME_HI = (140, 146, 160)
        RIM     = (32, 34, 40)

        # Soft contact shadow
        art.ground_shadow(surf, cx, sy + rh + 1, rw + 6, 8, 70)

        # Disc body + domed top with a sheen
        aadraw.ellipse(surf, BODY, (sx, sy, rw, rh))
        aadraw.ellipse(surf, DOME, (sx + 3, sy + 1, rw - 6, rh - 5))
        aadraw.ellipse(surf, DOME_HI, (sx + 7, sy + 1, rw - 22, max(2, rh - 11)))

        # Front bumper on whichever side it faces
        if self.dir > 0:
            aadraw.ellipse(surf, RIM, (sx + rw - 12, sy + 1, 12, rh - 2))
        else:
            aadraw.ellipse(surf, RIM, (sx, sy + 1, 12, rh - 2))

        # Central sensor turret + camera dot
        aadraw.ellipse(surf, RIM, (cx - 6, cy - 3, 12, 6))
        aadraw.circle(surf, (120, 200, 255), (cx, cy), 2)
        aadraw.circle(surf, WHITE, (cx - 1, cy - 1), 1)

        # Gentle status LED
        led_x = cx + (rw // 2 - 7) * self.dir
        led = (120, 230, 130) if (self.frame // 18) % 2 == 0 else (70, 150, 80)
        aadraw.circle(surf, led, (led_x, cy), 2)

        # Rim highlight
        aadraw.ellipse(surf, DOME_HI, (sx, sy, rw, rh), 1)


# ──────────────────────────────────────────────────────────────────────────────
# BoneCrate — Level 2 goal
# ──────────────────────────────────────────────────────────────────────────────
class BoneCrate:
    def __init__(self, x):
        self.x = float(x)
        self.y = float(GROUND_Y - CRATE_SIZE[1])
        self.w, self.h = CRATE_SIZE
        self.active = True
        self.collected = False
        self.frame = 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, player, platforms):
        self.frame = (self.frame + 1) % 120
        if not self.active or self.collected:
            return None
        if self.rect.colliderect(player.rect):
            self.collected = True
            return "found_crate"
        return None

    def draw(self, surf, cam_x):
        if not self.active:
            return
        sx = int(self.x - cam_x)
        sy = int(self.y)

        # Pulsing golden glow
        glow_r = int(52 + math.sin(self.frame * 0.12) * 12)
        glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        aadraw.circle(glow, (255, 220, 50, 32), (glow_r, glow_r), glow_r)
        surf.blit(glow, (sx + 32 - glow_r, sy + 24 - glow_r))

        # Crate body
        aadraw.rect(surf, (160, 100, 40), (sx, sy, 64, 48))
        for y_off in [12, 24, 36]:
            aadraw.line(surf, (120, 70, 20), (sx, sy + y_off), (sx + 64, sy + y_off), 2)
        for x_off in [16, 48]:
            aadraw.line(surf, (120, 70, 20), (sx + x_off, sy), (sx + x_off, sy + 48), 2)
        aadraw.rect(surf, (120, 70, 20), (sx, sy, 64, 48), 3)

        # Big bone sticking out of top
        bx, by = sx + 22, sy - 22
        aadraw.rect(surf, WHITE, (bx + 6, by + 6, 8, 20))
        for kx, ky in [(bx + 4, by + 6), (bx + 16, by + 6),
                       (bx + 4, by + 26), (bx + 16, by + 26)]:
            aadraw.circle(surf, WHITE, (kx, ky), 6)


# ──────────────────────────────────────────────────────────────────────────────
# Level2
# ──────────────────────────────────────────────────────────────────────────────
class Level2:
    """8 000 px interior house level.  Seven rooms, seven cats, three Roombas."""

    def __init__(self):
        self.width = LEVEL2_WIDTH
        self.camera_x = 0.0

        # ── Platforms ───────────────────────────────────────────────────
        # Lean set — each is the visible top of a piece of furniture, so the
        # jump surfaces read clearly.  Ground is one continuous strip.
        self.platforms = [
            _plat(0, GROUND_Y, LEVEL2_WIDTH),   # continuous ground — no gaps

            _plat(320, 512, 90),    # entry crate step 1
            _plat(470, 470, 90),    # entry crate step 2

            _plat(1080, 524, 170),  # living-room couch seat

            _plat(2320, 474, 180),  # hallway wall shelf

            _plat(2880, 500, 240),  # kitchen counter top
            _plat(3320, 528, 150),  # kitchen island

            _plat(4180, 512, 230),  # dining table top

            _plat(5260, 500, 170),  # play-room table

            _plat(6600, 500, 130),  # corridor bench

            _plat(7150, 512, 260),  # bedroom bed
            _plat(7520, 492, 130),  # bedroom dresser
        ]

        # ── Enemies ─────────────────────────────────────────────────────
        self.cats = [
            HouseCat( 600,  360,  900),   # entry-hall guard
            HouseCat(1750, 1200, 2100),   # living-room — blocks bookshelf approach
            HouseCat(2500, 2260, 2740),   # hallway — patrols below the shelf
            HouseCat(3300, 2900, 3750),   # kitchen
            HouseCat(4650, 4200, 4960),   # dining room
            HouseCat(5700, 5300, 6080),   # library
            HouseCat(6700, 6450, 6950),   # corridor sprint
            HouseCat(7450, 7100, 7750),   # bedroom guardian #1
            HouseCat(7700, 7500, 7950),   # bedroom guardian #2 (near crate!)
        ]

        self.roombas = [
            Roomba(1900, 1500, 2150),   # living room — dodge while platforming
            Roomba(4250, 3950, 4600),   # dining room
            Roomba(6550, 6300, 6900),   # corridor to bedroom
        ]

        self.bone_crate = BoneCrate(7880)

        self.events = []

    # ────────────────────────────────────────────────────────────────────
    def update_camera(self, player_x):
        target = player_x - SCROLL_THRESH
        self.camera_x += (target - self.camera_x) * 0.12
        self.camera_x = max(0, min(self.camera_x, self.width - SCREEN_WIDTH))

    def update(self, player):
        self.events.clear()

        for cat in self.cats:
            r = cat.update(player, self.platforms)
            if r == "life_damage":
                self.events.append(("life_damage",))
            elif r == "alert":
                self.events.append(("alert",))

        for roomba in self.roombas:
            r = roomba.update(player, self.platforms)
            if r == "life_damage":
                self.events.append(("life_damage",))

        r = self.bone_crate.update(player, self.platforms)
        if r == "found_crate":
            self.events.append(("found_crate",))

        self.update_camera(player.x)

    # ────────────────────────────────────────────────────────────────────
    def draw_background(self, surf):
        cam = self.camera_x

        # Base wall — warm vertical gradient (lighter near ceiling) with a subtle
        # tiled wallpaper motif (recoloured CC0 pattern at low alpha).  Composed
        # once into a strip one tile wider than the screen, then scrolled with a
        # single opaque blit instead of dozens of translucent tile blits per frame.
        if not hasattr(self, "_wall"):
            wp = art.tinted("pattern/wall_a.png", (158, 126, 90), 132).copy()
            wp.set_alpha(26)
            tw, th = wp.get_size()
            wall = pygame.Surface((SCREEN_WIDTH + tw, GROUND_Y))
            grad = art.vgradient(SCREEN_WIDTH, GROUND_Y,
                                 (246, 230, 204), (224, 202, 172))
            wall.blit(grad, (0, 0))
            wall.blit(grad, (SCREEN_WIDTH, 0))
            for x in range(0, SCREEN_WIDTH + tw, tw):
                for y in range(62, GROUND_Y, th):
                    wall.blit(wp, (x, y))
            self._wall, self._wall_tile_w = wall, tw
        surf.blit(self._wall, (0, 0),
                  (int(cam) % self._wall_tile_w, 0, SCREEN_WIDTH, GROUND_Y))

        # Per-room wall tints (drawn as translucent overlays)
        room_tints = [
            (   0,  1000, (255, 245, 220, 0)),   # entry — same as base
            (1000,  2200, ( 10,   0,  30, 18)),   # living — slightly cooler purple
            (2200,  2800, (  0,   0,   0, 28)),   # hallway — darker
            (2800,  4000, (255, 255, 240, 0)),     # kitchen — bright
            (4000,  5000, ( 30,  10,   0, 22)),   # dining — warmer
            (5000,  6400, ( 20,   5,   0, 38)),   # library — dark wood
            (6400,  7000, (  0,   0,   0, 24)),   # corridor
            (7000,  8000, (  0,  10,  30, 30)),   # bedroom — cool blue-gray
        ]
        for wx0, wx1, (r, g, b, a) in room_tints:
            if a == 0:
                continue
            left  = max(0, int(wx0 - cam))
            right = min(SCREEN_WIDTH, int(wx1 - cam))
            if right > left:
                ov = pygame.Surface((right - left, GROUND_Y), pygame.SRCALPHA)
                ov.fill((r, g, b, a))
                surf.blit(ov, (left, 0))

        # Ceiling strip (subtle gradient + crown moulding)
        surf.blit(art.vgradient(SCREEN_WIDTH, 62, (216, 200, 168), (198, 180, 148)), (0, 0))
        aadraw.rect(surf, (182, 162, 132), (0, 58, SCREEN_WIDTH, 4))
        aadraw.line(surf, (160, 140, 112), (0, 62), (SCREEN_WIDTH, 62), 2)

        # Wooden floor — warm gradient with parallax-locked plank seams
        floor_h = SCREEN_HEIGHT - GROUND_Y
        surf.blit(art.vgradient(SCREEN_WIDTH, floor_h, (140, 84, 38), (104, 58, 22)),
                  (0, GROUND_Y))
        offset = int(cam % 80)
        for gx in range(-offset, SCREEN_WIDTH + 80, 80):
            aadraw.line(surf, (92, 50, 16), (gx, GROUND_Y), (gx, SCREEN_HEIGHT), 1)
            aadraw.line(surf, (158, 100, 50), (gx + 1, GROUND_Y), (gx + 1, SCREEN_HEIGHT), 1)
        for gy in range(GROUND_Y + 22, SCREEN_HEIGHT, 22):
            aadraw.line(surf, (90, 50, 16), (0, gy), (SCREEN_WIDTH, gy), 1)
        # Soft sheen where the floor meets the wall
        sheen = pygame.Surface((SCREEN_WIDTH, 26), pygame.SRCALPHA)
        sheen.fill((255, 240, 210, 40))
        surf.blit(sheen, (0, GROUND_Y))
        # Baseboard
        aadraw.rect(surf, (176, 136, 76), (0, GROUND_Y - 12, SCREEN_WIDTH, 12))
        aadraw.rect(surf, (196, 158, 98), (0, GROUND_Y - 12, SCREEN_WIDTH, 3))
        aadraw.line(surf, (142, 102, 52),
                         (0, GROUND_Y - 1), (SCREEN_WIDTH, GROUND_Y - 1), 2)

        # Ceiling lamp — fixed screen center for ambient light
        lsx = SCREEN_WIDTH // 2
        aadraw.rect(surf, (162, 148, 122), (lsx - 8, 42, 16, 20))
        aadraw.polygon(surf, (242, 220, 158),
                            [(lsx - 18, 62), (lsx + 18, 62),
                             (lsx + 12, 42), (lsx - 12, 42)])
        glow_surf = pygame.Surface((110, 76), pygame.SRCALPHA)
        aadraw.ellipse(glow_surf, (255, 242, 182, 26), (0, 0, 110, 76))
        surf.blit(glow_surf, (lsx - 55, 58))

        self._draw_room_decor(surf, cam)
        self._draw_room_details(surf, cam)

    # ────────────────────────────────────────────────────────────────────
    def _draw_room_decor(self, surf, cam):
        """Behind-the-furniture room dressing: wainscoting, rugs, warm light
        pools and potted plants.  Big, cheap richness with no gameplay impact."""
        def sx(wx):
            return int(wx - cam)

        # Wainscoting (lower wall panelling) across every room
        wtop = GROUND_Y - 12 - 116
        pygame.draw.rect(surf, (208, 190, 158), (0, wtop, SCREEN_WIDTH, 116))
        off = int(cam) % 124
        for x in range(-off, SCREEN_WIDTH + 124, 124):
            aadraw.rect(surf, (190, 172, 140), (x + 6, wtop + 8, 104, 100),
                        2, border_radius=8)
            aadraw.line(surf, (224, 208, 178), (x + 10, wtop + 12), (x + 10, wtop + 104), 1)
        # Chair rail along the top of the wainscoting
        pygame.draw.rect(surf, (150, 118, 74), (0, wtop - 5, SCREEN_WIDTH, 9))
        pygame.draw.rect(surf, (182, 148, 96), (0, wtop - 5, SCREEN_WIDTH, 3))

        # Warm pools of light on the floor (one per room centre)
        for wx in [500, 1600, 2500, 3400, 4500, 5700, 6700, 7500]:
            lx = sx(wx)
            if -160 < lx < SCREEN_WIDTH + 160:
                surf.blit(art.radial_glow(120, (255, 238, 198), 34),
                          (lx - 120, GROUND_Y - 138))

        # Soft area rugs per room
        for wx, col in [(500, (120, 72, 150)), (1600, (150, 60, 60)),
                        (3400, (60, 112, 120)), (4500, (158, 120, 60)),
                        (5700, (78, 92, 146)), (7500, (120, 82, 60))]:
            rx = sx(wx)
            if -240 < rx < SCREEN_WIDTH + 240:
                rug = pygame.Surface((380, 48), pygame.SRCALPHA)
                aadraw.ellipse(rug, (col[0], col[1], col[2], 205), (0, 0, 380, 48))
                aadraw.ellipse(rug, (255, 255, 255, 70), (24, 7, 332, 12))
                aadraw.ellipse(rug, (255, 255, 255, 55), (0, 0, 380, 48), 3)
                surf.blit(rug, (rx - 190, GROUND_Y - 8))

        # Potted plants in the corners of several rooms
        for wx, hgt, leaf in [(250, 96, "bush_b"), (1360, 120, "tree_b"),
                              (2480, 96, "bush_a"), (4980, 120, "tree_d"),
                              (6360, 96, "bush_c"), (7050, 96, "bush_b")]:
            px = sx(wx)
            if -120 < px < SCREEN_WIDTH + 120:
                pot_top = GROUND_Y - 26
                leafimg = art.scaled_h("foliage/" + leaf + ".png", hgt)
                surf.blit(leafimg, (px - leafimg.get_width() // 2,
                                    pot_top - leafimg.get_height() + 10))
                art.panel(surf, (px - 20, pot_top, 40, 28), (168, 102, 60),
                          radius=6, outline=(120, 72, 40))

    # ────────────────────────────────────────────────────────────────────
    def _draw_room_details(self, surf, cam):
        def sx(wx):
            return int(wx - cam)

        font_sm = _font("Arial", 14, True)

        # ── Local helpers ─────────────────────────────────────────────
        def crate(x, top, w=90):
            """Wooden crate that doubles as a jump step (top == platform top)."""
            h = GROUND_Y - top
            art.panel(surf, (x, top, w, h), (172, 118, 62), radius=6, outline=(120, 78, 40))
            aadraw.line(surf, (124, 80, 42), (x + 6, top + h // 2), (x + w - 6, top + h // 2), 2)
            aadraw.line(surf, (124, 80, 42), (x + w // 2, top + 5), (x + w // 2, top + h - 4), 2)

        def framed(px, py, w, h, kind):
            """A real little framed picture on the wall (not a solid block)."""
            art.panel(surf, (px - 5, py - 5, w + 10, h + 10), (124, 88, 52), radius=4)
            aadraw.rect(surf, (210, 233, 246), (px, py, w, h))          # sky
            if kind == "house":
                aadraw.rect(surf, (226, 208, 170), (int(px + w * .30), int(py + h * .46),
                                                    int(w * .42), int(h * .5)))
                aadraw.polygon(surf, (192, 86, 60),
                               [(int(px + w * .2), int(py + h * .46)),
                                (int(px + w * .8), int(py + h * .46)),
                                (int(px + w * .5), int(py + h * .15))])
                aadraw.rect(surf, (120, 80, 50), (int(px + w * .45), int(py + h * .68),
                                                  int(w * .12), int(h * .28)))
            elif kind == "sun":
                aadraw.rect(surf, (132, 198, 102), (px, int(py + h * .66), w, int(h * .34)))
                aadraw.circle(surf, (255, 210, 72), (int(px + w * .72), int(py + h * .3)), int(h * .18))
            elif kind == "family":
                aadraw.rect(surf, (132, 198, 102), (px, int(py + h * .74), w, int(h * .26)))
                for i, c in enumerate([(232, 120, 140), (110, 150, 220), (240, 200, 90)]):
                    fx, fy = int(px + w * (.3 + i * .2)), int(py + h * .4)
                    aadraw.circle(surf, c, (fx, fy), max(3, int(h * .1)))
                    aadraw.line(surf, c, (fx, fy + int(h * .1)), (fx, int(py + h * .72)), 3)
            elif kind == "hearts":
                for i in range(2):
                    hx, hy = int(px + w * (.34 + i * .34)), int(py + h * .46)
                    aadraw.circle(surf, (220, 80, 110), (hx - 4, hy), 4)
                    aadraw.circle(surf, (220, 80, 110), (hx + 4, hy), 4)
                    aadraw.polygon(surf, (220, 80, 110),
                                   [(hx - 8, hy + 1), (hx + 8, hy + 1), (hx, hy + 11)])
            aadraw.rect(surf, (150, 110, 70), (px, py, w, h), 2)

        # ── Room labels (subtle signs on the wall) ───────────────────
        for label, wx in [("Entry Hall", 80), ("Living Room", 1050),
                          ("Hallway", 2250), ("Kitchen", 2830),
                          ("Dining Room", 4020), ("Play Room", 5020),
                          ("Corridor", 6420), ("Master Bedroom", 7020)]:
            lx = sx(wx)
            if -200 < lx < SCREEN_WIDTH:
                surf.blit(font_sm.render(label, True, (150, 128, 98)), (lx, 70))

        # ── Doorframes between rooms ──────────────────────────────────
        for door_wx in [1000, 2200, 2800, 4000, 5000, 6400, 7000]:
            dx = sx(door_wx)
            if -30 < dx < SCREEN_WIDTH:
                aadraw.rect(surf, (180, 140, 80), (dx - 12, 62, 12, GROUND_Y - 62), border_radius=2)
                aadraw.rect(surf, (180, 140, 80), (dx + 120, 62, 12, GROUND_Y - 62), border_radius=2)
                aadraw.rect(surf, (190, 150, 90), (dx - 12, 60, 144, 16), border_radius=3)

        # ════════ Entry Hall (0–1 000) ════════
        # Coat rack
        crx = sx(120)
        if -60 < crx < SCREEN_WIDTH:
            aadraw.line(surf, (120, 80, 40), (crx, 250), (crx, GROUND_Y), 6)
            for i, c in enumerate([(190, 70, 70), (70, 110, 190)]):
                aadraw.line(surf, (120, 80, 40), (crx, 270 + i * 34),
                            (crx + (18 if i % 2 == 0 else -18), 258 + i * 34), 4)
                art.panel(surf, (crx + (12 if i % 2 == 0 else -28), 262 + i * 34, 18, 40), c, radius=7, shadow=False)
        # Console table + vase, framed picture above
        etx = sx(700)
        if -120 < etx < SCREEN_WIDTH:
            art.panel(surf, (etx, 498, 104, 12), (150, 96, 44), radius=4)
            for lx in (etx + 6, etx + 90):
                aadraw.rect(surf, (120, 78, 36), (lx, 510, 8, GROUND_Y - 510))
            aadraw.ellipse(surf, (90, 150, 170), (etx + 42, 470, 18, 30))
            aadraw.ellipse(surf, (120, 180, 200), (etx + 46, 474, 8, 14))
            framed(etx + 28, 360, 50, 44, "family")
        # Jump-step crates to clear the entry guard cat
        cs1 = sx(320)
        if -120 < cs1 < SCREEN_WIDTH:
            crate(cs1, 512)
        cs2 = sx(470)
        if -120 < cs2 < SCREEN_WIDTH:
            crate(cs2, 470)

        # ════════ Living Room (1 000–2 200) ════════
        # Wall-mounted flat-screen TV (above the couch, on the wall)
        tvx = sx(1090)
        if -140 < tvx < SCREEN_WIDTH:
            art.panel(surf, (tvx, 300, 150, 92), (40, 42, 50), radius=8)
            aadraw.rect(surf, (26, 34, 46), (tvx + 8, 308, 134, 76), border_radius=4)
            aadraw.rect(surf, (60, 104, 150), (tvx + 12, 312, 126, 68), border_radius=3)
            aadraw.line(surf, (90, 150, 200), (tvx + 18, 322), (tvx + 60, 322), 2)
        # Couch — sits on the floor; seat top (524) is the jump platform
        coux = sx(1080)
        if -260 < coux < SCREEN_WIDTH:
            art.panel(surf, (coux, 492, 178, 40), (96, 60, 152), radius=12)        # backrest
            art.panel(surf, (coux - 6, 510, 26, 64), (88, 54, 144), radius=10)     # left arm
            art.panel(surf, (coux + 158, 510, 26, 64), (88, 54, 144), radius=10)   # right arm
            art.panel(surf, (coux + 12, 518, 154, 16), (122, 82, 180), radius=8, shadow=False)  # seat cushion (top=524)
            for lx in (coux + 6, coux + 158):                                       # legs
                aadraw.rect(surf, (70, 44, 26), (lx, 568, 10, 12))
        # Coffee table (decor, on floor)
        ctx = sx(1370)
        if -120 < ctx < SCREEN_WIDTH:
            art.panel(surf, (ctx, 540, 110, 12), (150, 100, 52), radius=4)
            for lx in (ctx + 6, ctx + 92):
                aadraw.rect(surf, (120, 80, 40), (lx, 552, 8, 28))
        # Bookshelf (on floor, real horizontal shelves with books)
        bkx = sx(1940)
        if -90 < bkx < SCREEN_WIDTH:
            art.panel(surf, (bkx, 360, 96, 220), (124, 80, 38), radius=6)
            for r in range(4):
                shelf_y = 384 + r * 52
                aadraw.rect(surf, (96, 60, 26), (bkx + 6, shelf_y + 40, 84, 5))   # shelf board
                for c, bc in enumerate([(180, 60, 60), (60, 110, 180), (70, 160, 80),
                                        (200, 180, 70), (150, 80, 160), (210, 130, 70)]):
                    bh = 30 + (c % 3) * 6
                    aadraw.rect(surf, bc, (bkx + 8 + c * 13, shelf_y + 40 - bh, 11, bh))
            aadraw.rect(surf, (96, 60, 26), (bkx, 360, 96, 220), 2, border_radius=6)
        # Framed pictures on the wall
        framed(sx(1500), 200, 64, 48, "house")
        framed(sx(1700), 196, 48, 60, "sun")

        # ════════ Hallway (2 200–2 800) ════════
        # Wall shelf (jump platform at 474)
        hsx = sx(2320)
        if -200 < hsx < SCREEN_WIDTH:
            art.panel(surf, (hsx, 474, 180, 12), (150, 100, 52), radius=4)
            aadraw.polygon(surf, (120, 80, 40), [(hsx + 6, 486), (hsx + 6, 506), (hsx + 24, 486)])
            aadraw.polygon(surf, (120, 80, 40), [(hsx + 174, 486), (hsx + 174, 506), (hsx + 156, 486)])
            framed(hsx + 60, 430, 56, 38, "hearts")
        # Wall sconces
        for scx_wx in [2360, 2620]:
            scx = sx(scx_wx)
            if -40 < scx < SCREEN_WIDTH:
                aadraw.rect(surf, (160, 140, 100), (scx - 4, 150, 8, 26))
                aadraw.polygon(surf, (244, 224, 168),
                               [(scx - 12, 178), (scx + 12, 178), (scx + 7, 156), (scx - 7, 156)])
                surf.blit(art.radial_glow(40, (255, 238, 180), 40), (scx - 40, 150))

        # ════════ Kitchen (2 800–4 000) — counter, sink, range, fridge ════════
        # Upper wall cabinets
        ucx = sx(2880)
        if -540 < ucx < SCREEN_WIDTH:
            art.panel(surf, (ucx, 330, 520, 96), (214, 206, 188), radius=6)
            for i in range(5):
                dx2 = ucx + 8 + i * 102
                aadraw.rect(surf, (196, 188, 168), (dx2, 338, 92, 80), border_radius=4)
                aadraw.rect(surf, (168, 160, 140), (dx2, 338, 92, 80), 2, border_radius=4)
                aadraw.rect(surf, (140, 132, 112), (dx2 + 78, 372, 6, 14), border_radius=2)
        # Base counter (top at 500 = platform) with cabinet doors + sink
        bcx = sx(2860)
        if -300 < bcx < SCREEN_WIDTH:
            art.panel(surf, (bcx, 500, 280, 80), (210, 200, 182), radius=4)        # cabinet body
            art.panel(surf, (bcx - 4, 492, 288, 14), (236, 230, 220), radius=4)    # countertop
            for i in range(3):
                dx2 = bcx + 8 + i * 92
                aadraw.rect(surf, (188, 180, 160), (dx2, 512, 84, 60), border_radius=4)
                aadraw.rect(surf, (160, 152, 132), (dx2, 512, 84, 60), 2, border_radius=4)
                aadraw.rect(surf, (130, 122, 104), (dx2 + 70, 536, 6, 14), border_radius=2)
            # Sink basin + faucet (in the countertop)
            aadraw.rect(surf, (150, 156, 164), (bcx + 150, 486, 70, 14), border_radius=4)
            aadraw.rect(surf, (110, 116, 126), (bcx + 156, 488, 58, 9), border_radius=3)
            aadraw.line(surf, (150, 156, 164), (bcx + 214, 488), (bcx + 214, 470), 4)
            aadraw.line(surf, (150, 156, 164), (bcx + 214, 470), (bcx + 198, 470), 4)
        # Free-standing range/oven with hood (sits next to the counter)
        rgx = sx(3150)
        if -120 < rgx < SCREEN_WIDTH:
            art.panel(surf, (rgx, 500, 90, 80), (78, 80, 88), radius=6)            # body
            art.panel(surf, (rgx + 8, 522, 74, 46), (40, 42, 48), radius=5, shadow=False)  # oven door
            aadraw.rect(surf, (120, 150, 180), (rgx + 14, 528, 62, 28), border_radius=3)   # window
            aadraw.rect(surf, (150, 152, 158), (rgx + 14, 514, 62, 5), border_radius=2)    # handle
            aadraw.rect(surf, (60, 62, 70), (rgx, 492, 90, 10), border_radius=3)           # cooktop
            for i, bx2 in enumerate([rgx + 22, rgx + 44, rgx + 66]):                       # burners
                warm = i == 1
                aadraw.circle(surf, (40, 42, 48), (bx2, 497), 7)
                aadraw.circle(surf, (255, 110, 30) if warm else (90, 92, 100), (bx2, 497), 4)
                if warm:
                    surf.blit(art.radial_glow(20, (255, 120, 30), 70), (bx2 - 20, 497 - 20))
            for kx in (rgx + 20, rgx + 70):                                                # knobs
                aadraw.circle(surf, (180, 182, 188), (kx, 510), 3)
            # Range hood
            aadraw.polygon(surf, (150, 152, 158),
                           [(rgx + 6, 430), (rgx + 84, 430), (rgx + 72, 408), (rgx + 18, 408)])
            aadraw.rect(surf, (170, 172, 178), (rgx + 18, 396, 54, 14), border_radius=3)
        # Kitchen island (lower jump step, top 528)
        isx = sx(3320)
        if -180 < isx < SCREEN_WIDTH:
            art.panel(surf, (isx, 528, 150, 52), (176, 120, 70), radius=5)
            art.panel(surf, (isx - 4, 520, 158, 12), (224, 216, 204), radius=4)
            for i in range(2):
                aadraw.rect(surf, (150, 100, 56), (isx + 12 + i * 74, 540, 60, 34), 2, border_radius=4)
        # Little breakfast table + 2 stools
        ktx = sx(3700)
        if -140 < ktx < SCREEN_WIDTH:
            aadraw.ellipse(surf, (200, 150, 96), (ktx, 524, 96, 16))
            aadraw.rect(surf, (160, 110, 60), (ktx + 44, 538, 8, GROUND_Y - 538))
            aadraw.ellipse(surf, (150, 100, 54), (ktx + 30, 572, 36, 8))
            for soff in (-26, 110):
                aadraw.ellipse(surf, (170, 120, 70), (ktx + soff, 548, 28, 10))
                aadraw.rect(surf, (140, 96, 50), (ktx + soff + 12, 556, 6, GROUND_Y - 556))
        # Fridge (tall, two doors, handles)
        frx = sx(3870)
        if -90 < frx < SCREEN_WIDTH:
            art.panel(surf, (frx, 322, 84, 258), (230, 232, 238), radius=12)
            aadraw.line(surf, (180, 182, 190), (frx + 4, 410), (frx + 80, 410), 3)   # freezer split
            aadraw.rect(surf, (150, 152, 160), (frx + 66, 346, 7, 50), border_radius=3)  # upper handle
            aadraw.rect(surf, (150, 152, 160), (frx + 66, 424, 7, 120), border_radius=3) # lower handle
            aadraw.rect(surf, (208, 210, 218), (frx, 322, 84, 258), 2, border_radius=12)

        # ════════ Dining Room (4 000–5 000) ════════
        # Dining table (top at 512 = platform) with legs, cloth, plates
        dtx = sx(4180)
        if -260 < dtx < SCREEN_WIDTH:
            for lx in (dtx + 14, dtx + 206):
                aadraw.rect(surf, (120, 78, 38), (lx, 524, 12, GROUND_Y - 524))
            art.panel(surf, (dtx, 504, 230, 18), (160, 104, 54), radius=5)          # tabletop
            art.panel(surf, (dtx + 16, 514, 198, 10), (228, 224, 214), radius=4, shadow=False)  # runner
            for px2 in (dtx + 50, dtx + 115, dtx + 180):
                aadraw.ellipse(surf, WHITE, (px2 - 12, 500, 24, 8))
                aadraw.ellipse(surf, (210, 212, 216), (px2 - 8, 501, 16, 5))
        # Chairs
        for chx in (sx(4150), sx(4404)):
            if -60 < chx < SCREEN_WIDTH:
                art.panel(surf, (chx, 520, 30, 8), (150, 98, 50), radius=3, shadow=False)
                art.panel(surf, (chx + 2, 486, 26, 36), (160, 106, 56), radius=4, shadow=False)
                for lx in (chx + 2, chx + 22):
                    aadraw.rect(surf, (120, 78, 38), (lx, 528, 6, GROUND_Y - 528))
        # Sideboard against the wall + picture above
        bufx = sx(4600)
        if -160 < bufx < SCREEN_WIDTH:
            art.panel(surf, (bufx, 470, 150, 110), (160, 104, 50), radius=6)
            for i in range(2):
                aadraw.rect(surf, (134, 84, 36), (bufx + 8 + i * 72, 480, 64, 56), 2, border_radius=4)
                aadraw.circle(surf, (210, 168, 80), (bufx + 40 + i * 72, 508), 4)
            framed(bufx + 44, 360, 62, 46, "family")
        # Chandelier above the table
        chlx = sx(4290)
        if -80 < chlx < SCREEN_WIDTH:
            aadraw.rect(surf, (160, 140, 100), (chlx, 62, 6, 56))
            aadraw.ellipse(surf, (206, 176, 104), (chlx - 30, 116, 66, 16))
            for i in range(5):
                aadraw.circle(surf, (255, 240, 160), (chlx - 24 + i * 12, 120), 4)
            surf.blit(art.radial_glow(70, (255, 240, 180), 30), (chlx - 67, 96))

        # ════════ Play Room (5 000–6 400) — cosy, simple ════════
        # Low play table (jump step at 500)
        ptx = sx(5260)
        if -200 < ptx < SCREEN_WIDTH:
            art.panel(surf, (ptx, 500, 170, 14), (180, 130, 80), radius=5)
            for lx in (ptx + 10, ptx + 150):
                aadraw.rect(surf, (140, 96, 54), (lx, 514, 9, GROUND_Y - 514))
            # building blocks on top
            for i, c in enumerate([(210, 80, 80), (80, 150, 210), (240, 200, 80)]):
                art.panel(surf, (ptx + 30 + i * 30, 480, 22, 22), c, radius=3, shadow=False)
        # Short kid bookshelf with a few books
        sbx = sx(5560)
        if -120 < sbx < SCREEN_WIDTH:
            art.panel(surf, (sbx, 470, 110, 110), (132, 88, 46), radius=6)
            aadraw.rect(surf, (104, 66, 30), (sbx + 6, 522, 98, 5))
            for c, bc in enumerate([(200, 70, 70), (70, 150, 90), (70, 120, 200), (210, 170, 70)]):
                aadraw.rect(surf, bc, (sbx + 10 + c * 16, 484, 13, 34))
        # Toy chest
        tcx = sx(5760)
        if -120 < tcx < SCREEN_WIDTH:
            art.panel(surf, (tcx, 524, 96, 56), (180, 120, 70), radius=8)
            art.panel(surf, (tcx - 4, 508, 104, 22), (196, 134, 80), radius=8, shadow=False)
            aadraw.circle(surf, (220, 180, 90), (tcx + 48, 540), 4)
        # Hint sign
        hintx = sx(5200)
        if -160 < hintx < SCREEN_WIDTH:
            surf.blit(_font("Arial", 15, True).render("Getting warmer, Ollie!", True, (210, 150, 60)),
                      (hintx, 110))

        # ════════ Corridor (6 400–7 000) ════════
        for pic_wx, kind in [(6470, "family"), (6620, "hearts"), (6770, "house"), (6910, "sun")]:
            framed(sx(pic_wx), 190, 48, 40, kind)
        # Bench (jump step at 500)
        bnx = sx(6600)
        if -160 < bnx < SCREEN_WIDTH:
            art.panel(surf, (bnx, 500, 130, 12), (160, 108, 58), radius=5)
            art.panel(surf, (bnx + 4, 470, 122, 32), (150, 100, 52), radius=4, shadow=False)
            for lx in (bnx + 6, bnx + 116):
                aadraw.rect(surf, (120, 80, 42), (lx, 512, 8, GROUND_Y - 512))

        # ════════ Master Bedroom (7 000–8 000) ════════
        # Night window with moon + stars
        winx = sx(7040)
        if -150 < winx < SCREEN_WIDTH:
            art.panel(surf, (winx, 130, 130, 184), (40, 56, 110), radius=8)
            for stx, sty in [(winx + 18, 154), (winx + 74, 164), (winx + 42, 192),
                             (winx + 106, 148), (winx + 92, 204), (winx + 30, 224)]:
                aadraw.circle(surf, WHITE, (stx, sty), 2)
            aadraw.circle(surf, (250, 246, 210), (winx + 96, 162), 17)
            aadraw.circle(surf, (40, 56, 110), (winx + 104, 156), 13)
            aadraw.rect(surf, (60, 80, 150), (winx, 130, 130, 184), 5, border_radius=8)
            aadraw.line(surf, (60, 80, 150), (winx + 65, 132), (winx + 65, 312), 3)
        # Bed — headboard, mattress (top 512), blanket, pillow; on the floor
        bedx = sx(7150)
        if -300 < bedx < SCREEN_WIDTH:
            art.panel(surf, (bedx - 6, 446, 26, 96), (150, 96, 50), radius=8)       # headboard
            art.panel(surf, (bedx + 12, 512, 248, 30), (214, 206, 230), radius=8)   # mattress
            art.panel(surf, (bedx + 70, 512, 190, 30), (150, 120, 200), radius=8, shadow=False)  # blanket
            art.panel(surf, (bedx + 18, 500, 46, 22), WHITE, radius=8, shadow=False)             # pillow
            for lx in (bedx + 14, bedx + 250):
                aadraw.rect(surf, (110, 70, 36), (lx, 564, 10, 16))
        # Wardrobe (tall, on the floor)
        wrdx = sx(7470)
        if -120 < wrdx < SCREEN_WIDTH:
            art.panel(surf, (wrdx, 300, 120, 280), (138, 90, 42), radius=8)
            aadraw.line(surf, (104, 64, 26), (wrdx + 60, 308), (wrdx + 60, 572), 2)
            for door_y in (380, 480):
                aadraw.circle(surf, (210, 168, 84), (wrdx + 52, door_y), 5)
                aadraw.circle(surf, (210, 168, 84), (wrdx + 68, door_y), 5)
            aadraw.rect(surf, (104, 64, 26), (wrdx, 300, 120, 280), 2, border_radius=8)
        # Dresser (jump step at 492)
        drx = sx(7520)
        if -160 < drx < SCREEN_WIDTH:
            art.panel(surf, (drx, 492, 130, 88), (152, 98, 48), radius=6)
            for r in range(2):
                aadraw.rect(surf, (130, 82, 36), (drx + 6, 500 + r * 42, 118, 36), 2, border_radius=4)
                aadraw.circle(surf, (210, 168, 84), (drx + 65, 518 + r * 42), 4)
        # Nightstand by the crate
        nsx = sx(7760)
        if -120 < nsx < SCREEN_WIDTH:
            art.panel(surf, (nsx, 512, 80, 68), (160, 104, 52), radius=6)
            aadraw.circle(surf, (210, 168, 84), (nsx + 40, 540), 4)
        # "Your Crate!" sign with arrow
        signx = sx(7880)
        if -90 < signx < SCREEN_WIDTH:
            acx = signx + 32
            aadraw.line(surf, GOLD, (acx, 440), (acx, 466), 3)
            aadraw.polygon(surf, GOLD, [(acx - 9, 466), (acx + 9, 466), (acx, 478)])
            surf.blit(_font("Arial", 18, True).render("Your Crate!", True, GOLD), (signx, 418))

    # ────────────────────────────────────────────────────────────────────
    def draw_world(self, surf):
        """Platforms are the tops of furniture (drawn in the background), so here
        we only add a soft highlight lip so the standable edge reads clearly."""
        cam = self.camera_x
        for plat in self.platforms[1:]:
            psx = int(plat.x - cam)
            if -20 < psx < SCREEN_WIDTH + 20:
                lip = pygame.Surface((plat.width, 6), pygame.SRCALPHA)
                lip.fill((255, 250, 235, 55))
                surf.blit(lip, (psx, plat.y - 1))

    def draw_characters(self, surf):
        cam = self.camera_x
        # Only draw enemies near the screen — most of the house is off-screen
        def visible(e):
            return -e.w - 100 < e.x - cam < SCREEN_WIDTH + 100

        for cat in self.cats:
            if not visible(cat):
                continue
            if cat.active:
                art.ground_shadow(surf, int(cat.x - cam) + cat.w // 2,
                                  int(cat.y) + cat.h - 1, cat.w + 6, 11, 60)
            cat.draw(surf, cam)
        for roomba in self.roombas:
            if visible(roomba):
                roomba.draw(surf, cam)
        self.bone_crate.draw(surf, cam)
