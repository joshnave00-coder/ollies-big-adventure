import pygame
import math
import random
import functools
import art
from constants import *
from player import draw_ollie_sprite


@functools.lru_cache(maxsize=None)
def _font(name: str, size: int, bold: bool = False) -> pygame.font.Font:
    return pygame.font.SysFont(name, size, bold=bold)


class UI:
    def __init__(self, screen):
        self.screen = screen
        self.font_lg = pygame.font.SysFont("Arial", 48, bold=True)
        self.font_md = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_sm = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_xs = pygame.font.SysFont("Arial", 14)
        self.font_xl = pygame.font.SysFont("Arial", 72, bold=True)

        self.score_popups = []  # [(text, x, y, timer, color)]
        self.confetti = []
        self.confetti_active = False
        self.home_carpet_trail = []   # trail particles for the home-screen carpet fly-in
        self.ascend_trail = []        # trail particles for the carpet-to-Heaven ascent
        self._ascend_sky = None       # private copy of the heaven gradient (alpha is animated)

    # ------------------------------------------------------------------ #
    # HUD
    # ------------------------------------------------------------------ #
    def draw_hud(self, player, has_water, level_width=LEVEL_WIDTH, goal_label="Home"):
        surf = self.screen

        # Semi-transparent bar
        hud = pygame.Surface((SCREEN_WIDTH, 64), pygame.SRCALPHA)
        hud.fill((0, 0, 0, 140))
        surf.blit(hud, (0, 0))

        # Health bar
        pygame.draw.rect(surf, DARK_GRAY, (14, 10, 180, 20), border_radius=4)
        hp_w = int(180 * player.health / MAX_HEALTH)
        hp_col = HEALTH_GREEN if player.health > 40 else (255, 200, 0) if player.health > 20 else HEALTH_RED
        pygame.draw.rect(surf, hp_col, (14, 10, hp_w, 20), border_radius=4)
        pygame.draw.rect(surf, WHITE, (14, 10, 180, 20), 2, border_radius=4)
        hp_label = self.font_xs.render("HP", True, WHITE)
        surf.blit(hp_label, (18, 14))

        # Lives
        for i in range(player.lives):
            hx = 204 + i * 26
            # Paw icon
            pygame.draw.circle(surf, APRICOT, (hx + 8, 20), 8)
            for j, (ox, oy) in enumerate([(-6, -7), (0, -9), (6, -7), (-10, -2), (10, -2)]):
                pygame.draw.circle(surf, PEACH, (hx + 8 + ox, 20 + oy), 4)

        # Score
        score_txt = self.font_md.render(f"Score: {player.score}", True, GOLD)
        surf.blit(score_txt, (SCREEN_WIDTH // 2 - score_txt.get_width() // 2, 12))

        # Level progress bar (bottom of HUD strip)
        prog = min(1.0, max(0.0, player.x / level_width))
        pb_x, pb_y, pb_w = SCREEN_WIDTH // 2 - 180, 46, 360
        pygame.draw.rect(surf, (40, 40, 40), (pb_x, pb_y, pb_w, 10), border_radius=4)
        fill = int(pb_w * prog)
        if fill > 0:
            pygame.draw.rect(surf, PINK, (pb_x, pb_y, fill, 10), border_radius=4)
        pygame.draw.rect(surf, GOLD, (pb_x, pb_y, pb_w, 10), 1, border_radius=4)
        home_lbl = self.font_xs.render(f"{goal_label} \u2192", True, GOLD)
        surf.blit(home_lbl, (pb_x + pb_w + 6, pb_y - 2))

        # Water bottle indicator — procedural icon + label
        if has_water:
            bx = SCREEN_WIDTH - 108
            by = 8
            # Bottle body
            pygame.draw.rect(surf, LIGHT_BLUE,       (bx,      by + 8,  14, 20))
            pygame.draw.rect(surf, (190, 230, 255),  (bx + 2,  by + 10, 10, 14))
            # Cap
            pygame.draw.rect(surf, BLUE,             (bx + 3,  by + 3,   8,  6))
            # Shine
            pygame.draw.line(surf, WHITE, (bx + 3, by + 11), (bx + 3, by + 20), 2)
            # Label text
            wb_label = self.font_sm.render("Water", True, LIGHT_BLUE)
            surf.blit(wb_label, (bx + 18, by + 10))

    # ------------------------------------------------------------------ #
    # Score popup
    # ------------------------------------------------------------------ #
    def add_popup(self, text, x, y, color=GOLD):
        self.score_popups.append([text, x, y, 90, color])

    def clear_transient(self):
        """Drop leftover popups/confetti so they don't leak into the next level or run."""
        self.score_popups = []
        self.confetti = []
        self.confetti_active = False

    def update_popups(self):
        for p in self.score_popups:
            p[2] -= 1.2   # float up
            p[3] -= 1
        self.score_popups = [p for p in self.score_popups if p[3] > 0]

    def draw_popups(self, cam_x):
        for text, wx, wy, timer, color in self.score_popups:
            sx = int(wx - cam_x)
            alpha = min(255, timer * 3)
            label = self.font_sm.render(text, True, color)
            self.screen.blit(label, (sx - label.get_width() // 2, int(wy)))

    # ------------------------------------------------------------------ #
    # Title screen
    # ------------------------------------------------------------------ #
    def draw_title(self, frame, scores=None, sound_on=True):
        surf = self.screen
        if scores is None:
            scores = []

        # Sky gradient (matches the in-game look)
        surf.blit(art.vgradient(SCREEN_WIDTH, 610, (104, 194, 240), (205, 236, 246)), (0, 0))

        # Sun with soft glow
        sun_x, sun_y = 980, 90
        glow = art.radial_glow(150, (255, 240, 160), 110)
        surf.blit(glow, (sun_x - 150, sun_y - 150))
        art.aadraw.circle(surf, (255, 243, 150), (sun_x, sun_y), 56)
        art.aadraw.circle(surf, (255, 250, 210), (sun_x, sun_y), 44)

        # Clouds
        for cx, cy, var in [(250, 110, "cloud_a"), (560, 70, "cloud_b"),
                            (760, 140, "cloud_c"), (1120, 90, "cloud_d")]:
            surf.blit(art.scaled_h("sky/" + var + ".png", 70), (cx, cy))

        # Layered hills tucked behind the ground line
        for sprite, tint, h, yb in [("hills1.png", (150, 200, 150), 150, 586),
                                    ("hills2.png", (96, 168, 96), 120, 588)]:
            strip = art.tinted("sky/" + sprite, tint, h)
            x = 0
            while x < SCREEN_WIDTH:
                surf.blit(strip, (x, yb - h))
                x += strip.get_width()

        # Tiled grass/dirt ground at y=580
        grass = art.scaled("ground/grass_mid.png", 70, 70)
        dirt = art.scaled("ground/dirt.png", 70, 70)
        for sx in range(0, SCREEN_WIDTH + 70, 70):
            surf.blit(grass, (sx, 580))
            surf.blit(dirt, (sx, 650))

        # Foliage trees + bushes framing the scene
        for tx, var, h in [(90, "tree_a", 200), (200, "tree_d", 230),
                           (1090, "pine_a", 200), (1200, "tree_b", 220)]:
            img = art.scaled_h("foliage/" + var + ".png", h)
            surf.blit(img, (tx - img.get_width() // 2, 580 - img.get_height() + 8))
        for bx, var in [(40, "bush_a"), (300, "bush_b"), (1010, "bush_c"), (1240, "bush_a")]:
            img = art.scaled_h("foliage/" + var + ".png", 50)
            surf.blit(img, (bx - img.get_width() // 2, 580 - img.get_height() + 6))

        # Title box
        box = pygame.Surface((700, 120), pygame.SRCALPHA)
        box.fill((20, 40, 20, 180))
        surf.blit(box, (290, 160))
        pygame.draw.rect(surf, GOLD, (290, 160, 700, 120), 4, border_radius=12)

        title = self.font_lg.render("Ollie's Big Adventure", True, GOLD)
        surf.blit(title, (640 - title.get_width() // 2, 185))
        sub = self.font_sm.render("Ollie is lost. Help him find his way home!", True, CREAM)
        surf.blit(sub, (640 - sub.get_width() // 2, 248))

        # Controls (left-centre)
        ctrl_y = 330
        for line in [
            "Arrow Keys / WASD — Move & Jump",
            "Avoid Dog Catchers, Hawks & Lions",
            "Find Lily & Leia, pet Campers, chase Birds!",
        ]:
            lbl = self.font_xs.render(line, True, WHITE)
            surf.blit(lbl, (360 - lbl.get_width() // 2, ctrl_y))
            ctrl_y += 24

        # Start prompt (blink)
        if (frame // 30) % 2 == 0:
            start = self.font_md.render("Press SPACE or ENTER to Start", True, SUN_YELLOW)
            surf.blit(start, (370 - start.get_width() // 2, 410))

        # How-to-play prompt (steady, in a little rounded chip so kids spot it)
        htp = self.font_sm.render("Press  H  —  How to Play", True, WHITE)
        chip_w, chip_h = htp.get_width() + 28, htp.get_height() + 14
        chip = pygame.Surface((chip_w, chip_h), pygame.SRCALPHA)
        chip.fill((20, 40, 20, 190))
        surf.blit(chip, (370 - chip_w // 2, 452))
        pygame.draw.rect(surf, GOLD, (370 - chip_w // 2, 452, chip_w, chip_h),
                         2, border_radius=10)
        surf.blit(htp, (370 - htp.get_width() // 2, 459))

        # Leaderboard panel (right side)
        lb_x, lb_y, lb_w, lb_h = 760, 310, 350, 230
        lb_bg = pygame.Surface((lb_w, lb_h), pygame.SRCALPHA)
        lb_bg.fill((20, 40, 20, 190))
        surf.blit(lb_bg, (lb_x, lb_y))
        pygame.draw.rect(surf, GOLD, (lb_x, lb_y, lb_w, lb_h), 3, border_radius=10)

        lb_title = self.font_sm.render("HIGH SCORES", True, GOLD)
        surf.blit(lb_title, (lb_x + lb_w // 2 - lb_title.get_width() // 2, lb_y + 10))
        pygame.draw.line(surf, GOLD, (lb_x + 12, lb_y + 36), (lb_x + lb_w - 12, lb_y + 36), 1)

        medals = ["#1", "#2", "#3", "#4", "#5"]
        medal_colors = [GOLD, (192, 192, 192), (180, 120, 60), WHITE, WHITE]
        for rank, (medal, col) in enumerate(zip(medals, medal_colors)):
            ry = lb_y + 46 + rank * 34
            if rank < len(scores):
                sc, ini = scores[rank]
                rank_lbl = self.font_sm.render(medal, True, col)
                ini_lbl  = self.font_sm.render(ini,   True, col)
                sc_lbl   = self.font_sm.render(str(sc), True, col)
                surf.blit(rank_lbl, (lb_x + 14,              ry))
                surf.blit(ini_lbl,  (lb_x + 70,              ry))
                surf.blit(sc_lbl,   (lb_x + lb_w - 14 - sc_lbl.get_width(), ry))
            else:
                empty = self.font_sm.render(f"{medal}  ---", True, DARK_GRAY)
                surf.blit(empty, (lb_x + 14, ry))

        # Sound toggle indicator (bottom-right)
        snd_label = "[S] Sound: ON" if sound_on else "[S] Sound: OFF"
        snd_color = HEALTH_GREEN   if sound_on else HEALTH_RED
        snd_txt   = self.font_sm.render(snd_label, True, snd_color)
        snd_bg    = pygame.Surface((snd_txt.get_width() + 16, snd_txt.get_height() + 8),
                                   pygame.SRCALPHA)
        snd_bg.fill((0, 0, 0, 130))
        surf.blit(snd_bg,  (SCREEN_WIDTH - snd_bg.get_width()  - 14, SCREEN_HEIGHT - 42))
        surf.blit(snd_txt, (SCREEN_WIDTH - snd_txt.get_width() - 22, SCREEN_HEIGHT - 38))

        # Ollie on title — full in-game sprite, gently bobbing, on the grass
        tail_angle = math.sin(frame * 0.1) * 25
        bob = int(math.sin(frame * 0.07) * 5)
        art.ground_shadow(surf, 640, 580, 54, 14, 70)
        draw_ollie_sprite(surf, 616, 532 + bob, 1, "sit", frame, tail_angle)

    # ------------------------------------------------------------------ #
    # How to Play (kid-friendly instructions)
    # ------------------------------------------------------------------ #
    def _howto_icons(self):
        """One reusable instance of each creature/item, used as a labelled icon
        on the How-to-Play screen.  Built lazily (after the display exists) and
        cached, so the real in-game sprites teach kids exactly what to look for."""
        if not hasattr(self, "_icons"):
            from characters import (DogCatcher, Bird, Hawk, GroundEnemy,
                                     FriendlyGirl, WaterBottle, MagicCarpet)
            from level2 import HouseCat, Roomba, BoneCrate
            carpet = MagicCarpet(0, 0)
            carpet.active = True          # so it draws outside the carpet sequence
            self._icons = {
                "lily":    FriendlyGirl(0, 0, "Lily", (255, 230, 80)),
                "bird":    Bird(0, 0),
                "catcher": DogCatcher(0, 0, -50, 50),
                "lion":    GroundEnemy(0, 0),
                "hawk":    Hawk(0, 0),
                "cat":     HouseCat(0, -50, 50),
                "roomba":  Roomba(0, -50, 50),
                "water":   WaterBottle(0, 0),
                "carpet":  carpet,
                "crate":   BoneCrate(0),
            }
        return self._icons

    def _howto_icon(self, surf, key, cx, baseline, caption, cap_color=(40, 40, 40)):
        """Draw a creature/item centred at x=cx with its feet on `baseline`,
        with a caption underneath."""
        obj = self._howto_icons()[key]
        obj.frame = self.frame
        obj.x = cx - obj.w / 2
        obj.y = baseline - obj.h
        obj.draw(surf, 0)
        lbl = self.font_xs.render(caption, True, cap_color)
        surf.blit(lbl, (cx - lbl.get_width() // 2, baseline + 8))

    def _howto_band(self, surf, x, y, w, h, fill, border):
        """Soft rounded panel used to group a section of the instructions."""
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill(fill)
        surf.blit(panel, (x, y))
        pygame.draw.rect(surf, border, (x, y, w, h), 3, border_radius=14)

    def _draw_heart(self, surf, cx, cy, r=11):
        col = (230, 70, 90)
        pygame.draw.circle(surf, col, (cx - r // 2, cy - r // 4), r // 2 + 1)
        pygame.draw.circle(surf, col, (cx + r // 2, cy - r // 4), r // 2 + 1)
        pygame.draw.polygon(surf, col, [(cx - r, cy - r // 4),
                                        (cx + r, cy - r // 4), (cx, cy + r)])

    def draw_howto(self, frame, sound_on=True):
        self.frame = frame
        surf = self.screen

        # Cheerful sky backdrop (matches the game world)
        surf.blit(art.vgradient(SCREEN_WIDTH, SCREEN_HEIGHT,
                                (104, 194, 240), (214, 240, 247)), (0, 0))

        # ---- Heading with a little Ollie mascot ----
        title = self.font_xl.render("How to Play", True, (60, 110, 40))
        surf.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2 + 30, 14))
        draw_ollie_sprite(surf, SCREEN_WIDTH // 2 - title.get_width() // 2 - 40, 30,
                          1, "wag", frame, math.sin(frame * 0.15) * 25)

        # ---- Top panels: The Goal | How to Move ----
        self._howto_band(surf, 30, 96, 600, 150, (255, 255, 255, 210), GOLD)
        gh = self.font_md.render("The Goal", True, (200, 120, 30))
        surf.blit(gh, (50, 104))
        for i, line in enumerate([
            "Ollie the puppy is lost!",
            "Walk RIGHT to find his Magic Carpet and fly home.",
            "Then sniff through the house to find his BIG BONE!",
        ]):
            txt = self.font_sm.render(line, True, (40, 40, 40))
            surf.blit(txt, (50, 146 + i * 30))

        self._howto_band(surf, 650, 96, 600, 150, (255, 255, 255, 210), GOLD)
        mh = self.font_md.render("How to Move", True, (200, 120, 30))
        surf.blit(mh, (670, 104))
        self._draw_key(surf, 690, 150, "<")
        self._draw_key(surf, 740, 150, ">")
        move_lbl = self.font_sm.render("Arrow Keys or A / D  —  walk", True, (40, 40, 40))
        surf.blit(move_lbl, (800, 156))
        self._draw_key(surf, 690, 200, "Space", wide=True)
        jump_lbl = self.font_sm.render("Space or Up  —  jump", True, (40, 40, 40))
        surf.blit(jump_lbl, (800, 206))

        # ---- Friends band ----
        head = self.font_md.render("Ollie's Friends  —  go say hi!", True, (40, 130, 40))
        surf.blit(head, (40, 258))
        self._howto_icon(surf, "lily", 150, 360, "Lily & Leia give treats")
        self._howto_icon(surf, "bird", 360, 360, "Chase birds to catch them!")
        camper_txt1 = self.font_sm.render("Campers (by the SAFE tents)", True, (40, 40, 40))
        camper_txt2 = self.font_sm.render("love pets and give treats.", True, (40, 40, 40))
        surf.blit(camper_txt1, (560, 330))
        surf.blit(camper_txt2, (560, 356))

        # ---- Baddies band ----
        head2 = self.font_md.render("Watch out!  —  don't let them touch you", True, (190, 50, 50))
        surf.blit(head2, (40, 408))
        for key, cx, cap in [("catcher", 150, "Dog Catcher"), ("lion", 320, "Lion"),
                             ("hawk", 470, "Hawk"), ("cat", 620, "House Cat"),
                             ("roomba", 780, "Roomba")]:
            self._howto_icon(surf, key, cx, 500, cap)
        warn = self.font_sm.render("If one touches Ollie he loses a heart!", True, (190, 50, 50))
        surf.blit(warn, (900, 470))

        # ---- Goals band ----
        head3 = self.font_md.render("Find these!", True, (200, 120, 30))
        surf.blit(head3, (40, 524))
        self._howto_icon(surf, "water", 150, 612, "Drink the water")
        self._howto_icon(surf, "carpet", 360, 612, "Ride the carpet home")
        self._howto_icon(surf, "crate", 620, 612, "Find the BONE = you win!")

        # ---- Footer: hearts, settings, back ----
        for i in range(3):
            self._draw_heart(surf, 950 + i * 34, 560)
        hearts_txt = self.font_sm.render("3 hearts = your lives", True, (40, 40, 40))
        surf.blit(hearts_txt, (905, 575))

        snd = "ON" if sound_on else "OFF"
        snd_col = HEALTH_GREEN if sound_on else HEALTH_RED
        set_lbl = self.font_sm.render("Settings:  press  S  for Sound:", True, (40, 40, 40))
        surf.blit(set_lbl, (905, 605))
        snd_lbl = self.font_sm.render(snd, True, snd_col)
        surf.blit(snd_lbl, (905 + set_lbl.get_width() + 6, 605))

        back = self.font_md.render("Press  SPACE  or  ESC  to go back", True, (60, 90, 160))
        if (frame // 30) % 2 == 0:
            surf.blit(back, (SCREEN_WIDTH // 2 - back.get_width() // 2, 660))

    def _draw_key(self, surf, x, y, label, wide=False):
        """Little keycap glyph used in the controls panel."""
        w = 64 if wide else 38
        pygame.draw.rect(surf, (250, 250, 250), (x, y, w, 34), border_radius=7)
        pygame.draw.rect(surf, (90, 90, 90), (x, y, w, 34), 2, border_radius=7)
        glyph = self.font_sm.render(label, True, (50, 50, 50))
        surf.blit(glyph, (x + w // 2 - glyph.get_width() // 2,
                          y + 17 - glyph.get_height() // 2))

    # ------------------------------------------------------------------ #
    # Enter initials (new high score)
    # ------------------------------------------------------------------ #
    def draw_enter_initials(self, initials, cursor, frame, score, scores=None):
        if scores is None:
            scores = []
        surf = self.screen

        # Background
        surf.blit(art.vgradient(SCREEN_WIDTH, 610, (104, 194, 240), (205, 236, 246)), (0, 0))
        for sprite, tint, h, yb in [("hills1.png", (150, 200, 150), 150, 586),
                                    ("hills2.png", (96, 168, 96), 120, 588)]:
            strip = art.tinted("sky/" + sprite, tint, h)
            x = 0
            while x < SCREEN_WIDTH:
                surf.blit(strip, (x, yb - h))
                x += strip.get_width()
        grass = art.scaled("ground/grass_mid.png", 70, 70)
        dirt = art.scaled("ground/dirt.png", 70, 70)
        for sx in range(0, SCREEN_WIDTH + 70, 70):
            surf.blit(grass, (sx, 580))
            surf.blit(dirt, (sx, 650))

        # Banner
        banner_bg = pygame.Surface((780, 110), pygame.SRCALPHA)
        banner_bg.fill((20, 60, 20, 200))
        surf.blit(banner_bg, (250, 60))
        pygame.draw.rect(surf, GOLD, (250, 60, 780, 110), 4, border_radius=12)
        hs_txt = self.font_lg.render("NEW HIGH SCORE!", True, GOLD)
        surf.blit(hs_txt, (640 - hs_txt.get_width() // 2, 78))
        sc_txt = self.font_sm.render(f"Score: {score}", True, SUN_YELLOW)
        surf.blit(sc_txt, (640 - sc_txt.get_width() // 2, 138))

        # Instructions
        instr = self.font_xs.render(
            "Type A-Z  |  ← → Move  |  ↑ ↓ Change Letter  |  ENTER Confirm  |  ESC Skip",
            True, WHITE)
        surf.blit(instr, (640 - instr.get_width() // 2, 198))

        # Letter boxes — three large cells
        box_w, box_h = 90, 110
        gap = 20
        total = box_w * 3 + gap * 2
        bx0 = 640 - total // 2
        by  = 230

        for i in range(3):
            bx = bx0 + i * (box_w + gap)
            selected = i == cursor
            bg_col = (40, 80, 40) if selected else (20, 40, 20)
            border_col = GOLD if selected else GRAY
            border_w   = 4 if selected else 2
            pygame.draw.rect(surf, bg_col, (bx, by, box_w, box_h), border_radius=8)
            pygame.draw.rect(surf, border_col, (bx, by, box_w, box_h), border_w, border_radius=8)
            letter = self.font_xl.render(initials[i], True, GOLD if selected else WHITE)
            surf.blit(letter, (bx + box_w // 2 - letter.get_width() // 2,
                               by + box_h // 2 - letter.get_height() // 2))
            # Cursor blink on selected box
            if selected and (frame // 20) % 2 == 0:
                pygame.draw.rect(surf, GOLD, (bx + 10, by + box_h - 14, box_w - 20, 4))

        # Up/down hint arrows on active box
        arrow_x = bx0 + cursor * (box_w + gap) + box_w // 2
        up_col   = GOLD if (frame // 15) % 2 == 0 else (180, 140, 0)
        dn_col   = GOLD if (frame // 15) % 2 == 1 else (180, 140, 0)
        pygame.draw.polygon(surf, up_col,
                            [(arrow_x, by - 14), (arrow_x - 10, by - 4), (arrow_x + 10, by - 4)])
        pygame.draw.polygon(surf, dn_col,
                            [(arrow_x, by + box_h + 14), (arrow_x - 10, by + box_h + 4),
                             (arrow_x + 10, by + box_h + 4)])

        # Confirm button (blink)
        if (frame // 28) % 2 == 0:
            enter_txt = self.font_md.render("Press ENTER to Save", True, SUN_YELLOW)
            surf.blit(enter_txt, (640 - enter_txt.get_width() // 2, by + box_h + 36))

        # Leaderboard preview (right side)
        lb_x, lb_y, lb_w, lb_h = 900, 230, 330, 210
        lb_bg = pygame.Surface((lb_w, lb_h), pygame.SRCALPHA)
        lb_bg.fill((20, 40, 20, 190))
        surf.blit(lb_bg, (lb_x, lb_y))
        pygame.draw.rect(surf, GOLD, (lb_x, lb_y, lb_w, lb_h), 2, border_radius=10)
        lb_hdr = self.font_sm.render("CURRENT TOP 5", True, GOLD)
        surf.blit(lb_hdr, (lb_x + lb_w // 2 - lb_hdr.get_width() // 2, lb_y + 8))
        pygame.draw.line(surf, GOLD, (lb_x + 10, lb_y + 34), (lb_x + lb_w - 10, lb_y + 34), 1)
        medals = ["#1", "#2", "#3", "#4", "#5"]
        medal_colors = [GOLD, (192, 192, 192), (180, 120, 60), WHITE, WHITE]
        for rank, (medal, col) in enumerate(zip(medals, medal_colors)):
            ry = lb_y + 44 + rank * 32
            if rank < len(scores):
                sc2, ini2 = scores[rank]
                rl = self.font_sm.render(medal,    True, col)
                il = self.font_sm.render(ini2,     True, col)
                sl = self.font_sm.render(str(sc2), True, col)
                surf.blit(rl, (lb_x + 12, ry))
                surf.blit(il, (lb_x + 60, ry))
                surf.blit(sl, (lb_x + lb_w - 12 - sl.get_width(), ry))
            else:
                el = self.font_sm.render(f"{medal}  ---", True, DARK_GRAY)
                surf.blit(el, (lb_x + 12, ry))

        # Ollie on left side
        tail_angle = math.sin(frame * 0.1) * 25
        bob = int(math.sin(frame * 0.08) * 4)
        draw_ollie_sprite(surf, 120, 400 + bob, 1, "wag", frame, tail_angle)

    # ------------------------------------------------------------------ #
    # Game Over
    # ------------------------------------------------------------------ #
    def draw_game_over(self, score, frame):
        surf = self.screen
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surf.blit(overlay, (0, 0))

        panel = pygame.Surface((600, 260), pygame.SRCALPHA)
        panel.fill((40, 10, 10, 210))
        surf.blit(panel, (340, 230))
        pygame.draw.rect(surf, RED, (340, 230, 600, 260), 3, border_radius=14)

        title = self.font_lg.render("Oh No, Ollie!", True, RED)
        surf.blit(title, (640 - title.get_width() // 2, 252))
        cheer = self.font_md.render("You can do it — keep trying!", True, PEACH)
        surf.blit(cheer, (640 - cheer.get_width() // 2, 318))
        sc = self.font_sm.render(f"Score so far: {score}", True, GOLD)
        surf.blit(sc, (640 - sc.get_width() // 2, 360))
        if (frame // 30) % 2 == 0:
            restart = self.font_md.render("Press ENTER to try again!", True, SUN_YELLOW)
            surf.blit(restart, (640 - restart.get_width() // 2, 408))

    # ------------------------------------------------------------------ #
    # Pause overlay
    # ------------------------------------------------------------------ #
    def draw_pause(self):
        surf = self.screen
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surf.blit(overlay, (0, 0))

        panel = pygame.Surface((500, 220), pygame.SRCALPHA)
        panel.fill((15, 40, 15, 220))
        surf.blit(panel, (390, 250))
        pygame.draw.rect(surf, GOLD, (390, 250, 500, 220), 4, border_radius=14)

        title = self.font_lg.render("PAUSED", True, GOLD)
        surf.blit(title, (640 - title.get_width() // 2, 272))
        sub = self.font_sm.render("Press  P  or  ESC  to resume", True, CREAM)
        surf.blit(sub, (640 - sub.get_width() // 2, 360))
        snd_hint = self.font_xs.render("Tip: Press S to toggle sound on/off", True, GRAY)
        surf.blit(snd_hint, (640 - snd_hint.get_width() // 2, 408))

    # ------------------------------------------------------------------ #
    # Traveling transition screen
    # ------------------------------------------------------------------ #
    def draw_traveling_screen(self, timer):
        surf = self.screen
        surf.fill(BLACK)

        cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

        # Expanding star rings radiate outward from center
        for ring in range(5):
            ring_r = int((timer * 2.2 + ring * 90) % 420)
            brightness = max(0, 220 - ring_r // 2)
            for i in range(20):
                angle = math.radians(i * 18 + timer * 0.6 + ring * 7)
                sx = cx + int(math.cos(angle) * ring_r)
                sy = cy + int(math.sin(angle) * ring_r * 0.45)
                r = max(1, 3 - ring_r // 160)
                col = (min(255, brightness + 30), min(255, brightness + 60), min(255, brightness // 2 + 80))
                if 0 <= sx <= SCREEN_WIDTH and 0 <= sy <= SCREEN_HEIGHT:
                    pygame.draw.circle(surf, col, (sx, sy), r)

        # Static background stars that twinkle
        for i in range(60):
            angle = i * 137.508   # golden angle for even distribution
            r_star = (i * 19 + 60) % 340
            sx = cx + int(math.cos(math.radians(angle)) * r_star)
            sy = cy + int(math.sin(math.radians(angle)) * r_star * 0.5)
            twinkle = int(80 + 175 * abs(math.sin(timer * 0.08 + i * 0.7)))
            col = (twinkle, twinkle, min(255, twinkle + 60))
            if 0 <= sx <= SCREEN_WIDTH and 0 <= sy <= SCREEN_HEIGHT:
                pygame.draw.circle(surf, col, (sx, sy), 2)

        # "Traveling..." text fades in after a brief pause
        if timer > 15:
            txt = self.font_lg.render("Traveling...", True, (180, 180, 255))
            shadow = self.font_lg.render("Traveling...", True, (50, 50, 100))
            tx = cx - txt.get_width() // 2
            bounce = int(math.sin(timer * 0.12) * 5)
            surf.blit(shadow, (tx + 3, cy - 18 + bounce + 3))
            surf.blit(txt,    (tx,     cy - 18 + bounce))

            sub = self.font_md.render("Almost home, Ollie...", True, (130, 130, 200))
            surf.blit(sub, (cx - sub.get_width() // 2, cy + 48 + bounce // 2))

    # ------------------------------------------------------------------ #
    # Home screen helpers
    # ------------------------------------------------------------------ #
    def _draw_carpet_at(self, surf, cx, cy, frame):
        """Draw the magic carpet at screen position (cx, cy) = top-left of carpet."""
        w = CARPET_SIZE[0]   # 90
        wave = int(math.sin(frame * 0.14) * 3)

        # Main body
        pts = [(cx, cy + wave), (cx + w, cy + wave),
               (cx + w + 7, cy + 14 - wave), (cx - 7, cy + 14 - wave)]
        pygame.draw.polygon(surf, CARPET_RED, pts)

        # Gold border strips
        pygame.draw.line(surf, CARPET_GOLD, (cx + 2, cy + wave + 1),    (cx + w - 2, cy + wave + 1),    3)
        pygame.draw.line(surf, CARPET_GOLD, (cx + 2, cy + 12 - wave),   (cx + w - 2, cy + 12 - wave),   3)

        # Blue diamonds
        for i in range(3):
            dx = cx + 14 + i * 26
            dy = cy + 7 + wave // 2
            pygame.draw.polygon(surf, CARPET_BLUE, [
                (dx, dy - 4), (dx + 7, dy), (dx, dy + 4), (dx - 7, dy)
            ])

        # Top fringe
        for fx in range(cx, cx + w, 5):
            pygame.draw.line(surf, CARPET_GOLD, (fx, cy + wave), (fx + 1, cy - 5 + wave), 2)
        # Bottom fringe
        for fx in range(cx, cx + w, 5):
            pygame.draw.line(surf, CARPET_GOLD, (fx, cy + 14 - wave), (fx + 1, cy + 20 - wave), 2)

        # Center medallion with spinning spokes
        mx, my = cx + w // 2, cy + 7 + wave // 2
        pygame.draw.circle(surf, CARPET_GOLD, (mx, my), 11)
        pygame.draw.circle(surf, CARPET_BLUE, (mx, my), 7)
        pygame.draw.circle(surf, CARPET_GOLD, (mx, my), 3)
        for a in range(0, 360, 60):
            ex = mx + int(math.cos(math.radians(a + frame * 2)) * 9)
            ey = my + int(math.sin(math.radians(a + frame * 2)) * 9)
            pygame.draw.line(surf, SUN_YELLOW, (mx, my), (ex, ey), 1)

        # Corner rosettes
        for corner_x in [cx + 10, cx + w - 10]:
            pygame.draw.circle(surf, CARPET_GOLD, (corner_x, cy + 7 + wave // 2), 5)
            pygame.draw.circle(surf, CARPET_RED,  (corner_x, cy + 7 + wave // 2), 3)

    def _home_ollie_sprite(self, surf, cx, cy, frame, sitting=True):
        """Draw the full in-game Ollie centred at (cx, cy-bottom) on the home/celebration screen."""
        bob = int(math.sin(frame * 0.11) * 5)
        tail_angle = math.sin(frame * 0.45) * 25
        # Convert centre-bottom to sprite top-left for draw_ollie_sprite
        sx = cx - 24
        sy = cy - 48 + bob
        anim = "wag" if not sitting else "idle"
        draw_ollie_sprite(surf, sx, sy, 1, anim, frame, tail_angle)

    # ------------------------------------------------------------------ #
    # Home celebration screen
    # ------------------------------------------------------------------ #
    def start_confetti(self):
        self.confetti_active = True
        self.confetti = []
        for _ in range(200):
            self.confetti.append({
                "x": random.randint(0, SCREEN_WIDTH),
                "y": random.randint(-SCREEN_HEIGHT, 0),
                "vx": random.uniform(-1.5, 1.5),
                "vy": random.uniform(2, 5),
                "color": random.choice([RED, GOLD, BLUE, PINK, GRASS_GREEN, PURPLE, WHITE]),
                "size": random.randint(6, 14),
                "rot": random.uniform(0, 360),
                "rot_spd": random.uniform(-5, 5),
            })

    def update_confetti(self):
        for c in self.confetti:
            c["x"] += c["vx"]
            c["y"] += c["vy"]
            c["rot"] += c["rot_spd"]
            if c["y"] > SCREEN_HEIGHT:
                c["y"] = random.randint(-60, -10)
                c["x"] = random.randint(0, SCREEN_WIDTH)

    def draw_home_screen(self, score, home_timer, carpet_done, lives_bonus=0):
        surf = self.screen

        # Reset trail on first frame so replays start clean
        if home_timer == 0:
            self.home_carpet_trail.clear()

        # ---- Background ----
        surf.blit(art.vgradient(SCREEN_WIDTH, 510, (104, 194, 240), (205, 236, 246)), (0, 0))

        # Warm sun with soft glow
        sun_cx, sun_cy = 180, 90
        surf.blit(art.radial_glow(150, (255, 240, 160), 110), (sun_cx - 150, sun_cy - 150))
        art.aadraw.circle(surf, (255, 243, 150), (sun_cx, sun_cy), 56)
        art.aadraw.circle(surf, (255, 250, 210), (sun_cx, sun_cy), 44)

        # Layered hills behind the ground
        for sprite, tint, h, yb in [("hills1.png", (150, 200, 150), 140, 504),
                                    ("hills2.png", (96, 168, 96), 110, 506)]:
            strip = art.tinted("sky/" + sprite, tint, h)
            x = 0
            while x < SCREEN_WIDTH:
                surf.blit(strip, (x, yb - h))
                x += strip.get_width()

        # Tiled grass/dirt ground (top at y=498)
        grass = art.scaled("ground/grass_mid.png", 70, 70)
        dirt = art.scaled("ground/dirt.png", 70, 70)
        for sx in range(0, SCREEN_WIDTH + 70, 70):
            surf.blit(grass, (sx, 498))
            for yy in range(568, 720, 70):
                surf.blit(dirt, (sx, yy))

        # Foliage trees framing the homecoming
        for tx, var, h in [(78, "tree_a", 170), (158, "tree_c", 200),
                           (1138, "pine_a", 170), (1212, "tree_b", 190)]:
            img = art.scaled_h("foliage/" + var + ".png", h)
            surf.blit(img, (tx - img.get_width() // 2, 498 - img.get_height() + 8))

        # House
        self._draw_house(surf, 488, 318)

        # ---- Carpet fly-in / landing / departure sequence ----
        FLY_FRAMES    = 100   # carpet enters from left and glides to landing spot
        STAY_FRAMES   = 40    # carpet rests on the ground while Ollie steps off
        DEPART_FRAMES = 50    # carpet drifts off to the right
        LAND_X = 308          # carpet left-edge screen-x at landing
        LAND_Y = 464          # carpet top-y at landing (just above grass)

        carpet_cx, carpet_cy = LAND_X, LAND_Y
        show_carpet  = True
        ollie_sitting = True

        if home_timer < FLY_FRAMES:
            t    = home_timer / FLY_FRAMES
            ease = 1.0 - (1.0 - t) ** 3          # cubic ease-out
            carpet_cx = int(-112 + ease * (LAND_X + 112))
            carpet_cy = int(155  + ease * (LAND_Y - 155))
            carpet_cy += int(math.sin(home_timer * 0.22) * 10)  # gentle sway
            ollie_sitting = True

        elif home_timer < FLY_FRAMES + STAY_FRAMES:
            carpet_cx, carpet_cy = LAND_X, LAND_Y
            # Ollie stands after the first 20 frames on the ground
            ollie_sitting = (home_timer - FLY_FRAMES) < 20

        elif home_timer < FLY_FRAMES + STAY_FRAMES + DEPART_FRAMES:
            drift = home_timer - FLY_FRAMES - STAY_FRAMES
            carpet_cx = LAND_X + drift * 5
            carpet_cy = LAND_Y - drift * 3
            show_carpet   = carpet_cx < SCREEN_WIDTH + 120
            ollie_sitting = False
        else:
            show_carpet   = False
            ollie_sitting = False

        # Carpet sparkle trail (home screen)
        if home_timer < FLY_FRAMES + STAY_FRAMES + DEPART_FRAMES and show_carpet:
            if home_timer % 3 == 0:
                trail_colors = [GOLD, SUN_YELLOW, WHITE, CARPET_GOLD, (255, 120, 210)]
                for _ in range(2):
                    self.home_carpet_trail.append([
                        float(carpet_cx + random.randint(0, 22)),
                        float(carpet_cy + random.randint(4, 12)),
                        random.uniform(-2.2, -0.3),
                        random.uniform(-1.4, 1.4),
                        random.randint(20, 36),
                        random.choice(trail_colors),
                    ])
        self.home_carpet_trail = [
            [p[0] + p[2], p[1] + p[3], p[2], p[3], p[4] - 1, p[5]]
            for p in self.home_carpet_trail if p[4] > 1
        ]
        for p in self.home_carpet_trail:
            r = max(1, int(p[4] / 9))
            pygame.draw.circle(surf, p[5], (int(p[0]), int(p[1])), r)
            if r > 1:
                pygame.draw.circle(surf, WHITE, (int(p[0]), int(p[1])), max(1, r - 1))

        if show_carpet:
            self._draw_carpet_at(surf, carpet_cx, carpet_cy, home_timer)

        # Ollie — seated on carpet or standing in yard
        ollie_cx = carpet_cx + CARPET_SIZE[0] // 2   # centre of carpet
        if not show_carpet:
            ollie_cx = LAND_X + CARPET_SIZE[0] // 2  # stays at landing spot
        ollie_cy = carpet_cy if ollie_sitting else 498
        self._home_ollie_sprite(surf, ollie_cx, ollie_cy, home_timer, sitting=ollie_sitting)

        # ---- Family — appear once the carpet starts descending ----
        if home_timer >= FLY_FRAMES // 2:
            family_appear = home_timer - FLY_FRAMES // 2
            family = [
                (700, 476, "Mom",  PINK),
                (778, 471, "Dad",  BLUE),
                (856, 476, "Lily", (255, 230, 80)),
                (934, 476, "Leia", (160, 110, 60)),
            ]
            for i, (fx, fy, name, hair) in enumerate(family):
                # Jump with individual phase offsets — more energetic after carpet lands
                jt  = max(0, home_timer - FLY_FRAMES)
                amp = 14 if jt > 0 else 6
                jump_off = -int(abs(math.sin(jt * 0.14 + i * 0.9)) * amp)
                self._draw_family_member(surf, fx, fy + jump_off, name, hair, home_timer)

        # ---- Treasure chest ----
        chest_timer = max(0, home_timer - FLY_FRAMES)
        self._draw_treasure_chest(surf, 1058, 476, chest_timer)

        # ---- Confetti ----
        if self.confetti_active:
            self.update_confetti()
            for c in self.confetti:
                ccx, ccy = int(c["x"]), int(c["y"])
                s = c["size"]
                pygame.draw.rect(surf, c["color"], (ccx - s // 2, ccy - s // 2, s, s))

        # ---- Banner: "You made it home, Ollie!" ----
        BANNER_START = FLY_FRAMES + STAY_FRAMES + 20   # 160
        if home_timer >= BANNER_START:
            appear_t  = home_timer - BANNER_START
            slide_off = max(0, 28 - appear_t * 2)      # slides down into place

            banner = pygame.Surface((920, 122), pygame.SRCALPHA)
            banner.fill((18, 58, 18, 215))
            surf.blit(banner, (180, 62 + slide_off))
            pygame.draw.rect(surf, GOLD, (180, 62 + slide_off, 920, 122), 4, border_radius=12)

            title = self.font_lg.render("You made it home, Ollie!", True, GOLD)
            surf.blit(title, (640 - title.get_width() // 2, 80 + slide_off))

            sc = self.font_md.render(f"Score: {score}", True, SUN_YELLOW)
            surf.blit(sc, (640 - sc.get_width() // 2, 204))

            if lives_bonus > 0:
                lives_count = lives_bonus // SCORE_LIVES_BONUS
                bonus_txt = self.font_sm.render(
                    f"Lives Bonus: +{lives_bonus}  ({lives_count} × {SCORE_LIVES_BONUS} pts)",
                    True, PINK)
                surf.blit(bonus_txt, (640 - bonus_txt.get_width() // 2, 234))

            # Level 2 button
            if appear_t >= 30:
                btn_w, btn_h = 380, 56
                bx = SCREEN_WIDTH // 2 - btn_w // 2
                by = 268
                pygame.draw.rect(surf, DARK_GREEN, (bx, by, btn_w, btn_h), border_radius=12)
                pygame.draw.rect(surf, GOLD,       (bx, by, btn_w, btn_h), 3, border_radius=12)
                if (home_timer // 28) % 2 == 0:
                    btn_txt = self.font_md.render("Level 2: Find Your Crate!", True, GOLD)
                else:
                    btn_txt = self.font_md.render("Press ENTER to Continue", True, WHITE)
                surf.blit(btn_txt, (640 - btn_txt.get_width() // 2, by + 13))

        # ---- Fade in from black (first ~48 frames) ----
        if home_timer < 48:
            fade_alpha = max(0, 255 - home_timer * 6)
            if fade_alpha > 0:
                fade_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                fade_surf.fill((0, 0, 0, fade_alpha))
                surf.blit(fade_surf, (0, 0))

    # ------------------------------------------------------------------ #
    # Level 2 win screen
    # ------------------------------------------------------------------ #
    def draw_level2_win(self, score, timer):
        surf = self.screen

        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 178))
        surf.blit(overlay, (0, 0))

        if self.confetti_active:
            self.update_confetti()
            for c in self.confetti:
                ccx, ccy = int(c["x"]), int(c["y"])
                s = c["size"]
                pygame.draw.rect(surf, c["color"], (ccx - s // 2, ccy - s // 2, s, s))

        if timer < 20:
            return

        slide_off = max(0, 28 - (timer - 20) * 2)

        banner = pygame.Surface((920, 122), pygame.SRCALPHA)
        banner.fill((18, 48, 58, 218))
        surf.blit(banner, (180, 188 + slide_off))
        pygame.draw.rect(surf, GOLD, (180, 188 + slide_off, 920, 122), 4, border_radius=12)

        title = self.font_lg.render("You found your crate, Ollie!", True, GOLD)
        surf.blit(title, (640 - title.get_width() // 2, 206 + slide_off))

        sc = self.font_md.render(f"Final Score: {score}", True, SUN_YELLOW)
        surf.blit(sc, (640 - sc.get_width() // 2, 338))

        # Draw a big bone icon
        bx, by = 576, 372
        pygame.draw.rect(surf, WHITE, (bx + 8, by + 6, 12, 26))
        for kx2, ky2 in [(bx + 6, by + 6), (bx + 22, by + 6),
                         (bx + 6, by + 32), (bx + 22, by + 32)]:
            pygame.draw.circle(surf, WHITE, (kx2, ky2), 8)

        if timer >= 50:
            btn_w, btn_h = 340, 56
            btnx = SCREEN_WIDTH // 2 - btn_w // 2
            btny = 390
            pygame.draw.rect(surf, DARK_GREEN, (btnx, btny, btn_w, btn_h), border_radius=12)
            pygame.draw.rect(surf, GOLD,       (btnx, btny, btn_w, btn_h), 3, border_radius=12)
            if (timer // 28) % 2 == 0:
                btn_txt = self.font_md.render("Play Again!", True, GOLD)
            else:
                btn_txt = self.font_md.render("Press ENTER", True, WHITE)
            surf.blit(btn_txt, (640 - btn_txt.get_width() // 2, btny + 13))

    # ------------------------------------------------------------------ #
    # Bone celebration scene — Ollie zooms toward camera, jumps for joy
    # ------------------------------------------------------------------ #
    def draw_bone_celebrate(self, player, timer, cam_x):
        surf = self.screen

        # Dark vignette fades in quickly
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        alpha = min(210, timer * 7)
        overlay.fill((10, 5, 30, alpha))
        surf.blit(overlay, (0, 0))

        if timer < 5:
            return

        # Radial sparkle burst
        rng = random.Random(timer // 3)
        for i in range(18):
            angle = rng.uniform(0, 360)
            radius = rng.uniform(100, 280) * min(1.0, timer / 35)
            spx = SCREEN_WIDTH // 2 + int(math.cos(math.radians(angle)) * radius)
            spy = SCREEN_HEIGHT // 2 + int(math.sin(math.radians(angle)) * radius * 0.6)
            col = rng.choice([GOLD, SUN_YELLOW, WHITE, PINK, LIGHT_BLUE])
            sz = rng.randint(3, 9)
            if 0 < spx < SCREEN_WIDTH and 0 < spy < SCREEN_HEIGHT:
                pygame.draw.circle(surf, col, (spx, spy), sz)
                pygame.draw.circle(surf, WHITE, (spx, spy), max(1, sz - 3))

        # Spinning rings of stars
        for ring in range(3):
            ring_r = 160 + ring * 70
            num_stars = 8 + ring * 4
            for i in range(num_stars):
                ang = math.radians(i * (360 / num_stars) + timer * (3 - ring))
                rx = SCREEN_WIDTH // 2 + int(math.cos(ang) * ring_r)
                ry = SCREEN_HEIGHT // 2 + int(math.sin(ang) * ring_r * 0.5) + 30
                if 0 < rx < SCREEN_WIDTH and 0 < ry < SCREEN_HEIGHT:
                    pygame.draw.circle(surf, GOLD, (rx, ry), 4)
                    pygame.draw.circle(surf, WHITE, (rx, ry), 2)

        # Zoom: grow from 1× to 4× over the first 60 frames then hold
        scale = min(4.0, 1.0 + (min(timer, 60) / 60.0) * 3.0)

        # Joyful bouncing — multiple hops, amplitude grows then stabilises
        amp = min(70, timer * 1.5)
        bounce_y = int(abs(math.sin(timer * 0.20)) * amp)

        # Draw a scaled-up Ollie in "celebrate" anim state
        base_w, base_h = OLLIE_SIZE
        draw_w = int(base_w * scale)
        draw_h = int(base_h * scale)

        ollie_surf = pygame.Surface((base_w, base_h), pygame.SRCALPHA)
        tail_angle = math.sin(timer * 0.55) * 35
        draw_ollie_sprite(ollie_surf, 0, 0, 1, "celebrate", timer, tail_angle)

        big_ollie = pygame.transform.scale(ollie_surf, (draw_w, draw_h))
        ox = SCREEN_WIDTH // 2 - draw_w // 2
        oy = SCREEN_HEIGHT // 2 - draw_h // 2 + 50 - bounce_y
        surf.blit(big_ollie, (ox, oy))

        # "You found your bone!" banner fades in
        if timer > 12:
            fade = min(255, (timer - 12) * 10)

            title_txt = self.font_lg.render("You Found Your Bone!", True, GOLD)
            t_surf = pygame.Surface((title_txt.get_width(), title_txt.get_height()),
                                    pygame.SRCALPHA)
            t_surf.blit(title_txt, (0, 0))
            t_surf.set_alpha(fade)
            surf.blit(t_surf, (640 - title_txt.get_width() // 2, 70))

            sub_txt = self.font_md.render("What a good boy, Ollie!", True, SUN_YELLOW)
            s_surf = pygame.Surface((sub_txt.get_width(), sub_txt.get_height()),
                                    pygame.SRCALPHA)
            s_surf.blit(sub_txt, (0, 0))
            s_surf.set_alpha(fade)
            surf.blit(s_surf, (640 - sub_txt.get_width() // 2, 134))

        # Draw bone icon below Ollie
        if timer > 30:
            bx = SCREEN_WIDTH // 2 - 14
            by = oy + draw_h + 16
            pygame.draw.rect(surf, WHITE, (bx + 6, by + 6, 8, 20))
            for kx2, ky2 in [(bx + 4, by + 6), (bx + 16, by + 6),
                              (bx + 4, by + 26), (bx + 16, by + 26)]:
                pygame.draw.circle(surf, WHITE, (kx2, ky2), 7)
            pygame.draw.rect(surf, (220, 220, 220), (bx + 6, by + 6, 8, 20), 1)

        # Countdown hint near end
        if timer > 200:
            hint = self.font_sm.render("Get ready…", True, (180, 180, 255))
            surf.blit(hint, (640 - hint.get_width() // 2, SCREEN_HEIGHT - 55))

    # ------------------------------------------------------------------ #
    # Level 3 — ascent to Heaven (intro), touch-God celebration, ending
    # ------------------------------------------------------------------ #
    def _cloud_puff(self, surf, cx, cy, w, h, color=(255, 255, 255), alpha=255):
        col = color if alpha >= 255 else (*color, alpha)
        for ox, oy, ew, eh in [(-w * .34, h * .10, w * .42, h * .62),
                               (w * .34, h * .10, w * .42, h * .62),
                               (-w * .12, -h * .18, w * .50, h * .78),
                               (w * .16, -h * .12, w * .46, h * .74),
                               (0, h * .20, w * .72, h * .56)]:
            art.aadraw.ellipse(surf, col, (cx + ox - ew / 2, cy + oy - eh / 2, ew, eh))

    def draw_ascend_screen(self, timer):
        """Ollie rides the magic carpet up through the clouds into Heaven."""
        surf = self.screen
        t = min(1.0, timer / ASCEND_DURATION)
        if timer == 0:
            self.ascend_trail = []

        # Sky brightens from daytime blue to golden heaven as Ollie rises
        # (cross-fade two cached gradients — building a fresh one every frame
        # took ~100 ms each and was cached forever)
        surf.blit(art.vgradient(SCREEN_WIDTH, SCREEN_HEIGHT,
                                (104, 194, 240), (205, 236, 246)), (0, 0))
        if self._ascend_sky is None:
            self._ascend_sky = art.vgradient(SCREEN_WIDTH, SCREEN_HEIGHT,
                                             (150, 168, 232), (255, 242, 206)).copy()
        self._ascend_sky.set_alpha(int(255 * t))
        surf.blit(self._ascend_sky, (0, 0))

        # Growing radiance at the very top — the light of Heaven
        # (one cached full-size glow, scaled and faded per frame)
        glow_r = int(140 + t * 280)
        glow = pygame.transform.smoothscale(
            art.radial_glow(ASCEND_GLOW_MAX_R, (255, 248, 210), ASCEND_GLOW_MAX_ALPHA),
            (glow_r * 2, glow_r * 2))
        glow.set_alpha(int(255 * (50 + t * 130) / ASCEND_GLOW_MAX_ALPHA))
        surf.blit(glow, (SCREEN_WIDTH // 2 - glow_r, -glow_r + int(30 + t * 150)))

        # Clouds rushing DOWNWARD past the view → feels like rising
        cloud_imgs = ["cloud_a", "cloud_b", "cloud_c", "cloud_d"]
        for i in range(12):
            img = art.scaled_h("sky/" + cloud_imgs[i % 4] + ".png", 72 + (i % 3) * 30)
            cx = (i * 233 + 40) % (SCREEN_WIDTH + 200) - 100
            cy = int((i * 150 + timer * 5.2) % (SCREEN_HEIGHT + 260)) - 130
            surf.blit(img, (cx, cy))

        # Carpet + Ollie swaying and rising toward the light
        carpet_cx = SCREEN_WIDTH // 2 - CARPET_SIZE[0] // 2 + int(math.sin(timer * 0.08) * 28)
        carpet_cy = int(SCREEN_HEIGHT * 0.54 - t * 70 + math.sin(timer * 0.16) * 8)

        # Sparkle trail streaming downward from the carpet
        if timer % 3 == 0:
            for _ in range(2):
                self.ascend_trail.append([
                    float(carpet_cx + random.randint(0, CARPET_SIZE[0])),
                    float(carpet_cy + random.randint(10, 22)),
                    random.uniform(-1.0, 1.0), random.uniform(1.2, 3.0),
                    random.randint(20, 38),
                    random.choice([GOLD, SUN_YELLOW, WHITE, CARPET_GOLD, (255, 130, 210)])])
        self.ascend_trail = [[p[0] + p[2], p[1] + p[3], p[2], p[3], p[4] - 1, p[5]]
                             for p in self.ascend_trail if p[4] > 1]
        for p in self.ascend_trail:
            r = max(1, int(p[4] / 9))
            pygame.draw.circle(surf, p[5], (int(p[0]), int(p[1])), r)

        self._draw_carpet_at(surf, carpet_cx, carpet_cy, timer)
        self._home_ollie_sprite(surf, carpet_cx + CARPET_SIZE[0] // 2, carpet_cy,
                                timer, sitting=True)

        # Title text
        if timer > 16:
            bounce = int(math.sin(timer * 0.12) * 5)
            txt = self.font_lg.render("Up to Heaven...", True, (255, 250, 220))
            sh = self.font_lg.render("Up to Heaven...", True, (150, 120, 60))
            tx = SCREEN_WIDTH // 2 - txt.get_width() // 2
            surf.blit(sh, (tx + 3, 70 + bounce + 3))
            surf.blit(txt, (tx, 70 + bounce))
            sub = self.font_md.render("Hold on tight, Ollie!", True, (120, 110, 170))
            surf.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 138 + bounce // 2))

        # Brief fade-in from the Level 2 win screen
        if timer < 30:
            fade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            fade.fill((0, 0, 0, max(0, 200 - timer * 8)))
            surf.blit(fade, (0, 0))

    def _draw_food(self, surf, cx, cy, kind, s=1.0):
        """A small procedural food item for Ollie's heavenly feast."""
        def S(v):
            return int(v * s)
        if kind == "bone":
            pygame.draw.line(surf, WHITE, (cx - S(12), cy), (cx + S(12), cy), S(7))
            for bx in (cx - S(12), cx + S(12)):
                pygame.draw.circle(surf, WHITE, (bx, cy - S(5)), S(5))
                pygame.draw.circle(surf, WHITE, (bx, cy + S(5)), S(5))
        elif kind == "bowl":
            pygame.draw.ellipse(surf, (200, 60, 60), (cx - S(18), cy - S(6), S(36), S(20)))
            pygame.draw.ellipse(surf, (150, 40, 40), (cx - S(18), cy + S(4), S(36), S(10)))
            for ox in (-7, 0, 7):                       # kibble
                pygame.draw.circle(surf, (150, 100, 50), (cx + S(ox), cy - S(2)), S(4))
        elif kind == "apple":
            pygame.draw.circle(surf, (220, 50, 50), (cx, cy + S(2)), S(12))
            pygame.draw.circle(surf, (240, 90, 90), (cx - S(4), cy - S(2)), S(4))
            pygame.draw.line(surf, (120, 80, 40), (cx, cy - S(10)), (cx, cy - S(16)), S(2))
            pygame.draw.ellipse(surf, GRASS_GREEN, (cx + S(1), cy - S(18), S(10), S(6)))
        elif kind == "cake":
            pygame.draw.polygon(surf, (235, 200, 120),
                                [(cx - S(12), cy + S(12)), (cx + S(12), cy + S(12)),
                                 (cx + S(8), cy - S(2)), (cx - S(8), cy - S(2))])
            pygame.draw.ellipse(surf, PINK, (cx - S(11), cy - S(10), S(22), S(12)))
            pygame.draw.circle(surf, RED, (cx, cy - S(12)), S(4))
        elif kind == "cookie":
            pygame.draw.circle(surf, (205, 160, 95), (cx, cy), S(12))
            for ox, oy in [(-4, -3), (4, -1), (-1, 4), (5, 5), (-6, 3)]:
                pygame.draw.circle(surf, (90, 55, 30), (cx + S(ox), cy + S(oy)), S(2))
        elif kind == "drumstick":
            pygame.draw.circle(surf, (190, 130, 80), (cx - S(3), cy), S(11))
            pygame.draw.line(surf, (210, 150, 95), (cx + S(2), cy), (cx + S(16), cy + S(8)), S(7))
            pygame.draw.circle(surf, WHITE, (cx + S(16), cy + S(8)), S(5))

    def draw_heaven_celebrate(self, player, timer, cam_x):
        """Ollie touches God: no more pain, and all the food he could want."""
        surf = self.screen
        D = HEAVEN_CELEBRATE_DURATION

        # Warm golden light floods the screen
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((255, 244, 200, min(205, timer * 6)))
        surf.blit(overlay, (0, 0))
        if timer < 4:
            return

        cx0, cy0 = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

        # Radiant beams from on high
        beams = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(16):
            ang = math.radians(i * 22.5 + timer * 0.5)
            ex = cx0 + math.cos(ang) * 800
            ey = cy0 + math.sin(ang) * 800
            pygame.draw.polygon(beams, (255, 250, 215, 30),
                                [(cx0, cy0 - 120),
                                 (ex - 26, ey), (ex + 26, ey)])
        surf.blit(beams, (0, 0))

        # Big radiant halo of God up top
        surf.blit(art.radial_glow(220, (255, 248, 200), 120), (cx0 - 220, -120))
        for r, a in [(60, 70), (44, 120), (30, 170)]:
            ring = pygame.Surface((r * 2 + 6, r * 2 + 6), pygame.SRCALPHA)
            art.aadraw.circle(ring, (255, 246, 185, a), (r + 3, r + 3), r, 4)
            surf.blit(ring, (cx0 - r - 3, 70 - r))

        # Joyful Ollie, healed and bouncing
        bounce = int(abs(math.sin(timer * 0.18)) * 30)
        base_w, base_h = OLLIE_SIZE
        scale = 2.4
        ollie_surf = pygame.Surface((base_w, base_h), pygame.SRCALPHA)
        draw_ollie_sprite(ollie_surf, 0, 0, 1, "celebrate", timer,
                          math.sin(timer * 0.5) * 30)
        big = pygame.transform.scale(ollie_surf, (int(base_w * scale), int(base_h * scale)))
        ox = cx0 - big.get_width() // 2
        oy = cy0 - big.get_height() // 2 + 40 - bounce
        surf.blit(big, (ox, oy))

        # "No more pain" healing hearts swirl up around Ollie (first phase)
        if timer < 150:
            for i in range(6):
                ang = timer * 0.06 + i * (2 * math.pi / 6)
                hx = cx0 + int(math.cos(ang) * 90)
                hy = cy0 + 20 - (timer % 60) + int(math.sin(ang) * 30)
                self._draw_heart(surf, hx, hy, 9)

        # The feast appears, one dish at a time, in a ring around Ollie
        feast = ["bone", "bowl", "drumstick", "apple", "cookie", "cake",
                 "bone", "drumstick"]
        if timer > 90:
            shown = min(len(feast), (timer - 90) // 10)
            for i in range(shown):
                ang = math.radians(i * (360 / len(feast)) - 90 + timer * 0.3)
                fx = cx0 + int(math.cos(ang) * 230)
                fy = cy0 + 60 + int(math.sin(ang) * 120)
                pop = min(1.0, ((timer - 90) - i * 10) / 12.0)
                self._draw_food(surf, fx, fy, feast[i], s=1.1 * pop)

        # Banners reflecting the moment
        if 16 < timer < 170:
            self._heaven_banner(surf, "No more pain, Ollie!", "You feel all better now",
                                 min(255, (timer - 16) * 8))
        elif timer >= 170:
            self._heaven_banner(surf, "Eat all you want!", "A feast that never ends",
                                 min(255, (timer - 170) * 8))

        # Singing-note flourish near the end
        if timer > 240:
            rng = random.Random(timer // 4)
            for _ in range(8):
                nx = rng.randint(120, SCREEN_WIDTH - 120)
                ny = rng.randint(120, SCREEN_HEIGHT - 160)
                col = (255, 240, 170)
                pygame.draw.ellipse(surf, col, (nx - 4, ny, 8, 6))
                pygame.draw.line(surf, col, (nx + 3, ny), (nx + 3, ny - 12), 2)

        if timer > D - 50:
            hint = self.font_sm.render("Almost there...", True, (170, 130, 40))
            surf.blit(hint, (cx0 - hint.get_width() // 2, SCREEN_HEIGHT - 52))

    def _heaven_banner(self, surf, title, sub, alpha):
        banner = pygame.Surface((760, 110), pygame.SRCALPHA)
        banner.fill((255, 252, 235, min(220, alpha)))
        surf.blit(banner, (SCREEN_WIDTH // 2 - 380, 36))
        pygame.draw.rect(surf, GOLD, (SCREEN_WIDTH // 2 - 380, 36, 760, 110),
                         4, border_radius=14)
        t = self.font_lg.render(title, True, (210, 150, 30))
        ts = pygame.Surface(t.get_size(), pygame.SRCALPHA); ts.blit(t, (0, 0)); ts.set_alpha(alpha)
        surf.blit(ts, (SCREEN_WIDTH // 2 - t.get_width() // 2, 50))
        s2 = self.font_sm.render(sub, True, (150, 110, 60))
        ss = pygame.Surface(s2.get_size(), pygame.SRCALPHA); ss.blit(s2, (0, 0)); ss.set_alpha(alpha)
        surf.blit(ss, (SCREEN_WIDTH // 2 - s2.get_width() // 2, 112))

    def _draw_cloud_house(self, surf, x, y):
        """A cosy little home up in the clouds for Ollie."""
        # Fluffy cloud base the house sits on
        self._cloud_puff(surf, x + 100, y + 168, 280, 70)
        # Walls
        pygame.draw.rect(surf, (255, 252, 245), (x + 20, y + 60, 160, 110), border_radius=8)
        pygame.draw.rect(surf, (235, 224, 210), (x + 20, y + 60, 160, 110), 3, border_radius=8)
        # Golden roof
        pygame.draw.polygon(surf, (240, 200, 90),
                            [(x, y + 64), (x + 200, y + 64), (x + 100, y - 16)])
        pygame.draw.polygon(surf, (210, 168, 50),
                            [(x, y + 64), (x + 200, y + 64), (x + 100, y - 16)], 3)
        # Door
        pygame.draw.rect(surf, (210, 170, 110), (x + 82, y + 110, 36, 60), border_radius=6)
        pygame.draw.circle(surf, GOLD, (x + 110, y + 142), 3)
        # Windows with golden light
        for wx in (x + 40, x + 130):
            pygame.draw.rect(surf, (255, 236, 160), (wx, y + 82, 30, 30), border_radius=4)
            pygame.draw.line(surf, (210, 180, 110), (wx + 15, y + 82), (wx + 15, y + 112), 2)
            pygame.draw.line(surf, (210, 180, 110), (wx, y + 97), (wx + 30, y + 97), 2)
        # Little heart over the door + "OLLIE'S" sign
        self._draw_heart(surf, x + 100, y + 50, 9)
        sign = _font("Arial", 13, True).render("OLLIE'S", True, (180, 130, 40))
        surf.blit(sign, (x + 100 - sign.get_width() // 2, y + 172))

    def draw_heaven_win(self, score, timer):
        """Final ending — Ollie gets a home to live in up in Heaven."""
        surf = self.screen

        # Dreamy heaven sky
        surf.blit(art.vgradient(SCREEN_WIDTH, SCREEN_HEIGHT,
                                (150, 168, 232), (255, 244, 212)), (0, 0))
        # Warm sun glow
        surf.blit(art.radial_glow(170, (255, 244, 170), 110), (SCREEN_WIDTH - 320, -40))

        # Drifting background clouds
        for i in range(8):
            img = art.scaled_h("sky/" + ["cloud_a", "cloud_b", "cloud_c", "cloud_d"][i % 4] + ".png",
                               70 + (i % 3) * 24)
            cx = int((i * 190 + timer * 0.6) % (SCREEN_WIDTH + 300)) - 150
            surf.blit(img, (cx, 40 + (i % 4) * 60))

        # Fluffy cloud ground
        for sx in range(-40, SCREEN_WIDTH + 160, 150):
            self._cloud_puff(surf, sx, 590, 200, 80)

        # The Singing Angels who welcomed Ollie, flanking the scene
        for ax, phase in [(250, 0.0), (1030, 1.4)]:
            bob = int(math.sin(timer * 0.08 + phase) * 4)
            self._draw_ending_angel(surf, ax, 470 + bob, timer)

        # Ollie's cloud home
        self._draw_cloud_house(surf, 540, 360)

        # Ollie, home at last, wagging in front of his house
        bob = int(math.sin(timer * 0.11) * 5)
        draw_ollie_sprite(surf, 616, 520 + bob, 1, "wag", timer,
                          math.sin(timer * 0.4) * 25)

        # Confetti
        if self.confetti_active:
            self.update_confetti()
            for c in self.confetti:
                ccx, ccy = int(c["x"]), int(c["y"])
                s = c["size"]
                pygame.draw.rect(surf, c["color"], (ccx - s // 2, ccy - s // 2, s, s))

        # Banner
        if timer >= 30:
            slide = max(0, 28 - (timer - 30) * 2)
            banner = pygame.Surface((940, 124), pygame.SRCALPHA)
            banner.fill((255, 252, 235, 220))
            surf.blit(banner, (170, 54 + slide))
            pygame.draw.rect(surf, GOLD, (170, 54 + slide, 940, 124), 4, border_radius=14)
            title = self.font_lg.render("Ollie's Home in Heaven!", True, (210, 150, 30))
            surf.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 70 + slide))
            sub = self.font_sm.render("No more pain, all the food he wants, and a home forever.",
                                      True, (140, 110, 70))
            surf.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 134 + slide))

        # Final score + finish prompt
        sc = self.font_md.render(f"Final Score: {score}", True, (200, 140, 30))
        scbg = pygame.Surface((sc.get_width() + 24, sc.get_height() + 10), pygame.SRCALPHA)
        scbg.fill((255, 255, 255, 170))
        surf.blit(scbg, (SCREEN_WIDTH // 2 - scbg.get_width() // 2, 196))
        surf.blit(sc, (SCREEN_WIDTH // 2 - sc.get_width() // 2, 200))

        if timer >= 70 and (timer // 28) % 2 == 0:
            prompt = self.font_md.render("Press ENTER to finish", True, (90, 90, 160))
            pbg = pygame.Surface((prompt.get_width() + 28, prompt.get_height() + 12), pygame.SRCALPHA)
            pbg.fill((255, 255, 255, 150))
            surf.blit(pbg, (SCREEN_WIDTH // 2 - pbg.get_width() // 2, 250))
            surf.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 256))

        # Fade in from the celebration
        if timer < 40:
            fade = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            fade.fill((255, 248, 220, max(0, 220 - timer * 6)))
            surf.blit(fade, (0, 0))

    def _draw_ending_angel(self, surf, cx, feet_y, frame):
        """A simple happy angel for the Heaven ending screen."""
        sy = feet_y - 70
        surf.blit(art.radial_glow(40, (255, 244, 180), 70), (cx - 40, sy - 6))
        wf = int(math.sin(frame * 0.18) * 6)
        for side in (-1, 1):
            for k, (col, ww, hh) in enumerate([((212, 220, 248), 34, 36),
                                               (WHITE, 18, 20)]):
                art.aadraw.ellipse(surf, col, (cx + side * (8 + k * 5) - ww // 2,
                                               sy + 24 - wf + k * 4, ww, hh))
        art.aadraw.polygon(surf, (250, 250, 255),
                           [(cx - 17, sy + 34), (cx + 17, sy + 34),
                            (cx + 23, sy + 78), (cx - 23, sy + 78)])
        pygame.draw.line(surf, GOLD, (cx - 22, sy + 76), (cx + 22, sy + 76), 2)
        art.aadraw.circle(surf, (255, 232, 198), (cx, sy + 20), 12)
        art.aadraw.ellipse(surf, (180, 90, 90), (cx - 3, sy + 23, 6, 5))   # singing
        halo_y = sy + 4 + int(math.sin(frame * 0.1) * 2)
        art.aadraw.ellipse(surf, GOLD, (cx - 13, halo_y - 3, 26, 8), 3)

    def _draw_house(self, surf, x, y):
        # Main structure
        pygame.draw.rect(surf, (220, 190, 150), (x, y, 200, 160))
        # Roof
        pygame.draw.polygon(surf, (160, 60, 40), [
            (x - 20, y), (x + 220, y), (x + 100, y - 100)
        ])
        # Door
        pygame.draw.rect(surf, BROWN, (x + 80, y + 80, 40, 80))
        pygame.draw.circle(surf, GOLD, (x + 112, y + 120), 4)
        # Windows
        for wx in [x + 20, x + 140]:
            pygame.draw.rect(surf, LIGHT_BLUE, (wx, y + 40, 40, 40))
            pygame.draw.line(surf, WHITE, (wx + 20, y + 40), (wx + 20, y + 80), 2)
            pygame.draw.line(surf, WHITE, (wx, y + 60), (wx + 40, y + 60), 2)
        # Chimney
        pygame.draw.rect(surf, (160, 80, 40), (x + 150, y - 80, 24, 60))
        # Welcome mat
        pygame.draw.rect(surf, (150, 80, 40), (x + 70, y + 155, 60, 10))
        surf.blit(_font("Arial", 8).render("HOME", True, CREAM), (x + 82, y + 157))

    def _draw_family_member(self, surf, x, y, name, hair_color, frame):
        # Reuse the in-game stock people so the cast looks the same everywhere
        sprite = {"Dad":  "char/dad_idle.png",   # light-skinned man, orange shirt
                  "Mom":  "char/mom_wave.png",   # purple shirt
                  "Lily": "char/lily_wave.png",  # orange shirt
                  "Leia": "char/leia_wave.png"   # gold shirt
                  }.get(name, "char/girl_wave.png")
        cx, feet = x + 15, y + 50
        art.blit_sprite(surf, sprite, cx, feet, 74)
        lbl = _font("Arial", 12, True).render(name, True, WHITE)
        bg = pygame.Surface((lbl.get_width() + 8, lbl.get_height() + 2), pygame.SRCALPHA)
        bg.fill((40, 40, 40, 150))
        surf.blit(bg, (cx - bg.get_width() // 2, y - 22))
        surf.blit(lbl, (cx - lbl.get_width() // 2, y - 21))

    def _draw_treasure_chest(self, surf, x, y, frame):
        # Open chest
        pygame.draw.rect(surf, (120, 80, 30), (x, y + 20, 60, 40))
        pygame.draw.rect(surf, GOLD, (x, y + 20, 60, 8))
        # Lid (open)
        open_angle = min(120, frame * 3)
        lid_y = y + 20 - int(math.sin(math.radians(open_angle)) * 30)
        pygame.draw.rect(surf, (100, 60, 20), (x, lid_y, 60, 14))
        # Sparkles
        for i in range(6):
            angle = frame * 4 + i * 60
            sx2 = x + 30 + int(math.cos(math.radians(angle)) * 20)
            sy2 = y + int(math.sin(math.radians(angle)) * 20)
            pygame.draw.circle(surf, GOLD, (sx2, sy2), 4)
            pygame.draw.circle(surf, WHITE, (sx2, sy2), 2)
        # Coins spilling
        for i, (ox, oy) in enumerate([(5, 15), (20, 10), (35, 12), (10, 25), (30, 22)]):
            pygame.draw.circle(surf, GOLD, (x + ox, y + oy), 5)
            pygame.draw.circle(surf, SUN_YELLOW, (x + ox, y + oy), 3)
