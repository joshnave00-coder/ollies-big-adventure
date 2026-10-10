import pygame
import math
import random
import functools
import art
from art import aadraw   # anti-aliased drop-in for pygame.draw (see CLAUDE.md "Rendering rule")
from constants import *
from characters import (Camper, DogCatcher, Bird, Hawk, GroundEnemy,
                        FriendlyGirl, WaterBottle, MagicCarpet)


@functools.lru_cache(maxsize=None)
def _font(name: str, size: int, bold: bool = False) -> pygame.font.Font:
    return pygame.font.SysFont(name, size, bold=bold)


def _plat(x, y, w):
    return pygame.Rect(x, y, w, PLATFORM_THICK)


class Level:
    def __init__(self):
        self.width = LEVEL_WIDTH
        self.camera_x = 0.0

        # ---- Platforms (world coords) ----
        self.platforms = [
            # Single continuous ground — no gaps so Ollie can never fall through
            _plat(0, GROUND_Y, LEVEL_WIDTH),
            # Elevated platforms
            _plat(300, 480, 180),
            _plat(560, 430, 150),
            _plat(820, 380, 200),
            _plat(1100, 460, 140),
            _plat(1650, 490, 160),
            _plat(1900, 420, 180),
            _plat(2100, 350, 200),
            _plat(2400, 460, 120),
            _plat(2650, 390, 160),
            _plat(2900, 460, 200),
            _plat(3100, 380, 160),
            _plat(3350, 440, 180),
            _plat(3650, 480, 120),
            _plat(3900, 410, 200),
            _plat(4200, 460, 140),
            _plat(4450, 390, 180),
            _plat(4700, 460, 160),
            _plat(4950, 380, 200),
            _plat(5200, 440, 160),
            _plat(5500, 390, 180),
            _plat(5750, 460, 140),
            _plat(5950, 420, 200),
        ]

        # ---- Characters ----
        # 3 campers spaced across the level with clear gaps between them
        self.campers = [
            Camper(500,  GROUND_Y - CAMPER_SIZE[1]),
            Camper(2600, GROUND_Y - CAMPER_SIZE[1]),
            Camper(4800, GROUND_Y - CAMPER_SIZE[1]),
        ]

        self.catchers = [
            DogCatcher(900, GROUND_Y - CATCHER_SIZE[1], 750, 1100),
            DogCatcher(2100, GROUND_Y - CATCHER_SIZE[1], 1900, 2400),
            DogCatcher(3600, GROUND_Y - CATCHER_SIZE[1], 3400, 3800),
            DogCatcher(5200, GROUND_Y - CATCHER_SIZE[1], 5000, 5400),
        ]

        self.birds = [Bird(x, y) for x, y in [
            (400, 460), (700, 380), (1200, 400), (1900, 350),
            (2500, 420), (2800, 360), (3200, 440), (3700, 380),
            (4100, 400), (4500, 360), (4900, 420), (5300, 380),
        ]]

        self.hawks = [Hawk(x, y) for x, y in [
            (1400, 200), (2800, 180), (4200, 220), (5600, 190),
        ]]

        self.ground_enemies = [
            GroundEnemy(1300, GROUND_Y - LION_SIZE[1]),
            GroundEnemy(3800, GROUND_Y - LION_SIZE[1]),
            GroundEnemy(4700, GROUND_Y - LION_SIZE[1]),
            GroundEnemy(5800, GROUND_Y - LION_SIZE[1]),
        ]

        # Lily (blonde) at 2 spots; Leia (brown hair) at 2 spots
        _gy = GROUND_Y - LILY_SIZE[1]
        self.friendly_girls = [
            FriendlyGirl(1600, _gy, "Lily", (255, 230, 80),
                         reward_label="Good boy!",   points=SCORE_LILY_TREAT),
            FriendlyGirl(4200, _gy, "Lily", (255, 230, 80),
                         reward_label="Good boy!",   points=SCORE_LILY_TREAT),
            FriendlyGirl(3100, _gy, "Leia", (160, 110, 60),
                         reward_label="You got this!", points=SCORE_LEIA_TREAT),
            FriendlyGirl(5600, _gy, "Leia", (160, 110, 60),
                         reward_label="You got this!", points=SCORE_LEIA_TREAT),
        ]

        self.water_bottle = WaterBottle(5700, GROUND_Y - 32)
        self.magic_carpet = MagicCarpet(6400, GROUND_Y - CARPET_SIZE[1] - 10)

        # Slide zone
        self.slide_rect = pygame.Rect(6000, GROUND_Y - 160, 200, 160)
        self.slide_triggered = False

        # ---- Scenery (purely decorative — no gameplay effect) ----
        # Foreground tree-line: (world x, pixel height, sprite variant)
        _tree_variants = ["tree_a", "tree_b", "tree_c", "tree_d", "tree_e",
                          "pine_a", "pine_b"]
        self.trees = [(random.randint(0, LEVEL_WIDTH),
                       random.randint(120, 240),
                       random.choice(_tree_variants))
                      for _ in range(46)]
        self.trees.sort(key=lambda t: t[1])   # short (distant) drawn first

        # Far mountains on the horizon (parallax 0.12)
        self.mountains = [(i * 820 + 150, i % 2)
                          for i in range(LEVEL_WIDTH // 820 + 2)]

        # Ground-level shrubs / grass tufts / flowers
        _decor = ["bush_a", "bush_b", "bush_c", "tuft_a", "tuft_b",
                  "flower_a", "flower_b"]
        self.scenery = [(random.randint(0, LEVEL_WIDTH), random.choice(_decor))
                        for _ in range(150)]

        # Tinted hill-strip layers reused by draw_background
        self.hills = []  # legacy field kept for compatibility; no longer drawn

        # Walk-right beginner hint (first 5 seconds)
        self.start_hint_timer = 300

        # Events tracking
        self.events = []  # filled by update(), read by game.py

    # ------------------------------------------------------------------ #
    def update_camera(self, player_x):
        target = player_x - SCROLL_THRESH
        self.camera_x += (target - self.camera_x) * 0.12
        self.camera_x = max(0, min(self.camera_x, self.width - SCREEN_WIDTH))

    def update(self, player):
        self.events.clear()
        if self.start_hint_timer > 0:
            self.start_hint_timer -= 1
        px = player.x

        # Campers — state is managed inside Camper.update()
        for c in self.campers:
            result = c.update(player, self.platforms)
            if result == "pet":
                self.events.append(("score", SCORE_PET, "Pet!"))
                self.events.append(("hearts",))          # pink heart particles on Ollie
            elif result == "treat":
                self.events.append(("score", SCORE_TREAT, "Treat!"))

        # Dog catchers
        for catcher in self.catchers:
            result = catcher.update(player, self.platforms)
            if result == "life_damage":
                self.events.append(("life_damage",))
            elif result == "alert":
                self.events.append(("alert",))

        # Birds
        for bird in self.birds[:]:
            result = bird.update(player, self.platforms)
            if result == "caught":
                self.events.append(("score", SCORE_BIRD, "Bird!"))
                self.birds.remove(bird)

        # Hawks
        for hawk in self.hawks:
            result = hawk.update(player, self.platforms)
            if result == "life_damage":
                self.events.append(("life_damage",))
            elif result == "alert":
                self.events.append(("alert",))

        # Ground enemies
        for enemy in self.ground_enemies:
            result = enemy.update(player, self.platforms)
            if result == "life_damage":
                self.events.append(("life_damage",))
            elif result == "alert":
                self.events.append(("alert",))

        # Lily & Leia — state (rewarded_this_visit + distance reset) managed inside FriendlyGirl
        for girl in self.friendly_girls:
            result = girl.update(player, self.platforms)
            if result == "treat":
                self.events.append(("score", girl.points, girl.reward_label))

        # Water bottle
        wb = self.water_bottle.update(player, self.platforms)
        if wb == "collected":
            self.events.append(("water",))

        # Slide — trigger when Ollie's left edge crosses the slide entrance
        if not self.slide_triggered and player.x >= self.slide_rect.x:
            self.slide_triggered = True
            self.events.append(("slide",))

        # Magic carpet
        self.magic_carpet.update(player, self.platforms)

        self.update_camera(px)

    # ------------------------------------------------------------------ #
    def _draw_hill_strip(self, surf, sprite, tint, height, parallax, y_base):
        """Tile a tinted Kenney hill silhouette across the screen at a parallax."""
        strip = art.tinted("sky/" + sprite, tint, height)
        sw = strip.get_width()
        start = -int((self.camera_x * parallax) % sw)
        x = start
        while x < SCREEN_WIDTH:
            surf.blit(strip, (x, y_base - height))
            x += sw

    def draw_background(self, surf):
        cam = self.camera_x

        # Sky gradient (deep blue up top fading to pale near the horizon)
        surf.blit(art.vgradient(SCREEN_WIDTH, GROUND_Y + 30,
                                (104, 194, 240), (205, 236, 246)), (0, 0))

        # Sun with a soft radial glow
        sun_x = int(190 - cam * 0.03) % (SCREEN_WIDTH + 260) - 130
        glow = art.radial_glow(140, (255, 240, 160), 110)
        surf.blit(glow, (sun_x - 140, 72 - 140))
        art.aadraw.circle(surf, (255, 243, 150), (sun_x, 72), 48)
        art.aadraw.circle(surf, (255, 250, 210), (sun_x, 72), 37)

        # Far mountains (parallax 0.12) — desaturated bluish for depth
        for wx, var in self.mountains:
            img = art.tinted("sky/mountain%d.png" % (var + 1), (150, 170, 200), 250)
            sx = int(wx - cam * 0.12)
            if -img.get_width() < sx < SCREEN_WIDTH:
                surf.blit(img, (sx, GROUND_Y - img.get_height() + 10))

        # Two tinted hill layers for depth (tuck below the ground line)
        self._draw_hill_strip(surf, "hills1.png", (150, 200, 150), 150, 0.30, GROUND_Y + 6)
        self._draw_hill_strip(surf, "hills2.png", (96, 168, 96), 120, 0.52, GROUND_Y + 8)

        # Clouds (parallax 0.1) using soft Kenney cloud sprites
        cloud_imgs = ["cloud_a", "cloud_b", "cloud_c", "cloud_d"]
        for i in range(22):
            cx_w = i * 360 + 80
            cy = 50 + (i % 4) * 46
            var = cloud_imgs[i % len(cloud_imgs)]
            img = art.scaled_h("sky/" + var + ".png", 60 + (i % 3) * 18)
            cx_s = int(cx_w - cam * 0.1) % (SCREEN_WIDTH + 400) - 200
            surf.blit(img, (cx_s, cy))

    def draw_world(self, surf):
        cam = self.camera_x
        TILE = 70

        # --- Tiled grass/dirt ground (grass-topped row + dirt fill below) ---
        grass = art.scaled("ground/grass_mid.png", TILE, TILE)
        dirt = art.scaled("ground/dirt.png", TILE, TILE)
        offset = int(cam) % TILE
        for sx in range(-offset, SCREEN_WIDTH + TILE, TILE):
            surf.blit(grass, (sx, GROUND_Y))
            y = GROUND_Y + TILE
            while y < SCREEN_HEIGHT:
                surf.blit(dirt, (sx, y))
                y += TILE

        # --- Foreground tree-line (sorted short→tall for a little depth) ---
        for wx, size, var in self.trees:
            img = art.scaled_h("foliage/" + var + ".png", size)
            sx = int(wx - cam)
            if -img.get_width() < sx < SCREEN_WIDTH + img.get_width():
                surf.blit(img, (sx - img.get_width() // 2,
                                GROUND_Y - img.get_height() + 8))

        # --- Ground shrubs / tufts / flowers ---
        for wx, kind in self.scenery:
            sx = int(wx - cam)
            if -80 < sx < SCREEN_WIDTH + 80:
                h = 30 if kind.startswith("tuft") else (40 if kind.startswith("flower") else 52)
                img = art.scaled_h("foliage/" + kind + ".png", h)
                surf.blit(img, (sx - img.get_width() // 2,
                                GROUND_Y - img.get_height() + 6))

        # --- Floating platforms as grass-capped ledges ---
        for p in self.platforms:
            if p.y == GROUND_Y:
                continue  # ground drawn above
            sx = p.x - int(cam)
            if -p.width < sx < SCREEN_WIDTH + p.width:
                strip_h = 56
                prev = surf.get_clip()
                surf.set_clip(pygame.Rect(sx, p.y, p.width, strip_h))
                for tx in range(0, p.width + TILE, TILE):
                    surf.blit(grass, (sx + tx, p.y))
                surf.set_clip(prev)
                # soft shadow under the ledge
                art.ground_shadow(surf, sx + p.width // 2, p.y + strip_h + 2,
                                  p.width, 14, 55)

        # Slide (near end)
        slide_sx = int(self.slide_rect.x - cam)
        if -300 < slide_sx < SCREEN_WIDTH + 300:
            self._draw_slide(surf, slide_sx)

        # The carpet only appears once Ollie has his water bottle.  If he got past
        # the slide without it (the bottle is easy to hop over), the end of the
        # level is empty — so point the way back instead of leaving a dead end.
        if self.slide_triggered and not self.water_bottle.collected:
            cx = int(self.magic_carpet.x - cam) + CARPET_SIZE[0] // 2
            if -300 < cx < SCREEN_WIDTH + 300:
                lines = [_font("Arial", 22, True).render("Ollie needs his water bottle!", True, WHITE),
                         _font("Arial", 18, True).render("←  Go back and grab it", True, LIGHT_BLUE)]
                w = max(l.get_width() for l in lines) + 28
                top = GROUND_Y - 150
                bg = pygame.Surface((w, 72), pygame.SRCALPHA)
                bg.fill(HUD_BG)
                surf.blit(bg, (cx - w // 2, top))
                pygame.draw.rect(surf, LIGHT_BLUE, (cx - w // 2, top, w, 72), 2, border_radius=8)
                for i, l in enumerate(lines):
                    surf.blit(l, (cx - l.get_width() // 2, top + 9 + i * 32))

        # Walk-right beginner hint (first 5 seconds, only when near start)
        if self.start_hint_timer > 0 and self.camera_x < 200:
            alpha = 255 if (self.start_hint_timer // 20) % 2 == 0 else 100
            hint = _font("Arial", 22, True).render("Walk right  \u2192", True, GOLD)
            hs = pygame.Surface((hint.get_width(), hint.get_height()), pygame.SRCALPHA)
            hs.blit(hint, (0, 0))
            hs.set_alpha(alpha)
            surf.blit(hs, (80, GROUND_Y - 90))

    def _draw_slide(self, surf, sx):
        """A proper metal playground slide that runs from a high deck on the
        left down to the right — glowing hot (Ollie needs water to ride it).
        Geometry matches the slide_rect Ollie animates along (top-left→bottom-right)."""
        sy = GROUND_Y - 160        # top of the slide deck (=420)
        t_ms = pygame.time.get_ticks()
        pulse = 0.7 + 0.3 * math.sin(t_ms * 0.004)

        METAL      = (158, 164, 176)
        METAL_DK   = (96, 100, 112)
        METAL_HI   = (224, 230, 240)
        RAIL       = (210, 64, 44)

        # Sliding surface: high end (left) down to low end (right)
        top = (sx + 16, sy + 16)
        bot = (sx + 196, GROUND_Y - 8)
        dx, dy = bot[0] - top[0], bot[1] - top[1]
        ln = math.hypot(dx, dy) or 1
        nx, ny = -dy / ln, dx / ln          # unit perpendicular, points downward
        th = 22                              # chute thickness
        u_top = (top[0] + nx * th, top[1] + ny * th)
        u_bot = (bot[0] + nx * th, bot[1] + ny * th)

        # Support legs (drawn first, behind the chute)
        for fx, fy in [(sx + 70 + nx * th, sy + 70), (u_bot[0] - 16, u_bot[1])]:
            aadraw.line(surf, METAL_DK, (fx, fy), (fx - 8, GROUND_Y + 26), 6)
            aadraw.line(surf, METAL, (fx, fy), (fx - 8, GROUND_Y + 26), 2)

        # Chute band (metallic) + curled lip at the bottom
        aadraw.polygon(surf, METAL, [top, bot, u_bot, u_top])
        aadraw.line(surf, METAL_DK, u_top, u_bot, 6)            # underside shadow
        aadraw.line(surf, METAL, top, bot, 6)                   # surface
        aadraw.line(surf, METAL_HI, (top[0] + 2, top[1]), (bot[0] - 2, bot[1]), 2)  # gloss
        aadraw.circle(surf, METAL, (int(bot[0]), int(bot[1] - 6)), 11)
        aadraw.circle(surf, METAL_HI, (int(bot[0]), int(bot[1] - 6)), 11, 2)

        # Gentle warm tint so the metal reads as "too hot to touch"
        aadraw.polygon(surf, (255, 140, 40, int(38 * pulse)), [top, bot, u_bot, u_top])

        # Side safety rail running just above the sliding edge
        aadraw.line(surf, RAIL, (top[0], top[1] - 18), (bot[0], bot[1] - 18), 5)
        for tt in (0.0, 0.5, 1.0):
            px, py = int(top[0] + dx * tt), int(top[1] + dy * tt)
            aadraw.line(surf, RAIL, (px, py - 2), (px, py - 18), 3)

        # High deck + ladder on the left
        deck_x, deck_y = sx - 30, sy + 8
        aadraw.rect(surf, METAL, (deck_x, deck_y, 52, 9), border_radius=3)
        aadraw.rect(surf, METAL_HI, (deck_x, deck_y, 52, 3), border_radius=2)
        aadraw.line(surf, RAIL, (deck_x, deck_y), (deck_x, deck_y - 32), 4)
        aadraw.line(surf, RAIL, (deck_x, deck_y - 32), (deck_x + 26, deck_y - 32), 4)
        for lx in (deck_x + 5, deck_x + 22):
            aadraw.line(surf, METAL_DK, (lx, deck_y), (lx, GROUND_Y), 4)
        for ry in range(int(deck_y) + 18, GROUND_Y, 18):
            aadraw.line(surf, METAL, (deck_x + 5, ry), (deck_x + 22, ry), 3)

        # Subtle warm glow along the chute (no cheesy shimmer lines)
        glow = art.radial_glow(96, (255, 120, 40), int(34 * pulse))
        surf.blit(glow, (int((top[0] + bot[0]) / 2) - 96,
                         int((top[1] + bot[1]) / 2) - 96))

        # Warning sign on a post (left of the slide)
        scx, scy = sx - 78, sy - 36
        aadraw.rect(surf, METAL_DK, (scx - 3, scy + 48, 6, GROUND_Y - (scy + 48)))
        tri = [(scx, scy), (scx + 30, scy + 48), (scx - 30, scy + 48)]
        aadraw.polygon(surf, SUN_YELLOW, tri)
        aadraw.polygon(surf, HOT_RED, tri, 3)
        surf.blit(_font("Arial", 24, True).render("!", True, HOT_RED), (scx - 5, scy + 12))
        hot_lbl = _font("Arial", 15, True).render("HOT!", True, HOT_RED)
        surf.blit(hot_lbl, (scx - hot_lbl.get_width() // 2, scy + 52))

    def draw_characters(self, surf):
        cam = self.camera_x
        # Sprite-based NPCs add their own contact shadow via art.blit_sprite;
        # procedural ones (lion) shadow themselves in their draw().
        for c in self.campers:
            c.draw(surf, cam)
        for catcher in self.catchers:
            catcher.draw(surf, cam)
        for bird in self.birds:
            bird.draw(surf, cam)
        for hawk in self.hawks:
            hawk.draw(surf, cam)
        for enemy in self.ground_enemies:
            enemy.draw(surf, cam)
        for girl in self.friendly_girls:
            girl.draw(surf, cam)
        self.water_bottle.draw(surf, cam)
        self.magic_carpet.draw(surf, cam)
