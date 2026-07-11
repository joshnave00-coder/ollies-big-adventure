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


# ---------------------------------------------------------------------------
# Base NPC
# ---------------------------------------------------------------------------
class NPC:
    def __init__(self, x, y, w, h):
        self.x = float(x)
        self.y = float(y)
        self.w = w
        self.h = h
        self.frame = 0
        self.active = True

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def update(self, player, platforms):
        self.frame = (self.frame + 1) % 120

    def draw(self, surf, cam_x):
        pass


# ---------------------------------------------------------------------------
# Camper
# ---------------------------------------------------------------------------
class Camper(NPC):
    AWAY_DIST = 160   # px Ollie must step back before the visit resets

    def __init__(self, x, y):
        super().__init__(x, y, *CAMPER_SIZE)
        # visit_state: "ready" → "petted" → "treated" → reset on walk-away
        self.visit_state = "ready"
        self.delay_timer = 0    # frames until treat is offered after pet (120 = 2 s)
        self.show_bone = 0      # frames to display bone icon above camper
        self.show_heart = 0     # frames to animate big smile during pet
        self.anim = "sit"       # "sit" | "pet"

    def update(self, player, platforms):
        super().update(player, platforms)
        dist = abs(player.x - self.x)

        if self.delay_timer > 0:
            self.delay_timer -= 1
        if self.show_bone > 0:
            self.show_bone -= 1
        if self.show_heart > 0:
            self.show_heart -= 1

        # Reset after Ollie walks away post-treat
        if self.visit_state == "treated" and dist > self.AWAY_DIST:
            self.visit_state = "ready"
            self.anim = "sit"

        if dist < PET_RADIUS:
            self.anim = "pet"
            if self.visit_state == "ready":
                self.visit_state = "petted"
                self.delay_timer = 120   # 2-second gap before treat
                self.show_heart = 70
                return "pet"
            if self.visit_state == "petted" and self.delay_timer == 0:
                self.visit_state = "treated"
                self.show_bone = 90
                return "treat"
        else:
            if dist > 120:
                self.anim = "sit"

        return None

    def draw(self, surf, cam_x):
        sx = int(self.x - cam_x)
        sy = int(self.y)

        # ---- SAFE green glow badge (always visible) ----
        badge_r = 18 + int(math.sin(self.frame * 0.12) * 3)
        badge_surf = pygame.Surface((badge_r * 2, badge_r * 2), pygame.SRCALPHA)
        aadraw.circle(badge_surf, (80, 200, 80, 70), (badge_r, badge_r), badge_r)
        surf.blit(badge_surf, (sx + 6 - badge_r, sy - 46 - badge_r))
        lbl = _font("Arial", 10, True).render("SAFE", True, (40, 160, 40))
        surf.blit(lbl, (sx + 6 - lbl.get_width() // 2, sy - 52))

        # ---- Campfire (a proper stone-ring fire to Ollie's left) ----
        fx, fy = sx - 28, sy + 50
        surf.blit(art.radial_glow(46, (255, 150, 40), 70), (fx - 46, fy - 46))
        for ox in (-16, -6, 6, 16):                       # ring of stones
            aadraw.ellipse(surf, (152, 152, 160), (fx + ox - 5, fy - 3, 12, 9))
            aadraw.ellipse(surf, (120, 120, 128), (fx + ox - 5, fy - 3, 12, 9), 1)
        aadraw.line(surf, (120, 80, 44), (fx - 14, fy + 1), (fx + 14, fy - 7), 6)   # crossed logs
        aadraw.line(surf, (150, 104, 60), (fx - 14, fy - 7), (fx + 14, fy + 1), 6)
        fl = int(math.sin(self.frame * 0.3) * 3)           # flicker
        for col, sw, sh2 in [((230, 70, 20), 17, 30), ((255, 150, 20), 11, 22),
                             ((255, 226, 130), 6, 13)]:
            aadraw.polygon(surf, col, [(fx, fy - sh2 - fl - 4),
                                       (fx - sw // 2, fy - 3), (fx + sw // 2, fy - 3)])
        aadraw.circle(surf, (255, 242, 190), (fx, fy - 8), 2)

        # ---- Tent (A-frame with a door flap, beside the camper) ----
        tx0, tx1, base = sx + 20, sx + 84, sy + 52
        apex = (sx + 52, sy - 8)
        aadraw.polygon(surf, (212, 98, 72), [(tx0, base), (tx1, base), apex])      # lit half
        aadraw.polygon(surf, (182, 76, 54), [(tx0, base), (sx + 52, base), apex])  # shaded half
        aadraw.line(surf, (150, 60, 40), (tx0, base), apex, 3)
        aadraw.line(surf, (150, 60, 40), (tx1, base), apex, 3)
        aadraw.polygon(surf, (88, 48, 38), [(sx + 44, base), (sx + 52, base), (sx + 52, sy + 22)])
        aadraw.polygon(surf, (120, 64, 48), [(sx + 52, base), (sx + 60, base), (sx + 52, sy + 22)])

        # Friendly camper — stock person sprite who cheers when Ollie visits
        cx = sx + self.w // 2
        feet = sy + self.h
        var = "camper2" if (int(self.x) // 100) % 2 == 0 else "camper"
        pose = "cheer" if (self.anim == "pet" or self.show_heart > 0) else "idle"
        art.blit_sprite(surf, "char/%s_%s.png" % (var, pose), cx, feet, 82)

        # ---- Bone icon (appears after treat reward) ----
        if self.show_bone > 0:
            self._draw_bone(surf, sx + 14, sy - 48)

    def _draw_bone(self, surf, x, y):
        aadraw.line(surf, CREAM, (x, y), (x + 20, y), 5)
        for bx in [x, x + 20]:
            aadraw.circle(surf, CREAM, (bx, y - 4), 4)
            aadraw.circle(surf, CREAM, (bx, y + 4), 4)


# ---------------------------------------------------------------------------
# Dog Catcher
# ---------------------------------------------------------------------------
class DogCatcher(NPC):
    PATROL_SPEED = CATCHER_PATROL_SPD   # 1.0 — well below Ollie's speed of 4

    def __init__(self, x, y, patrol_left, patrol_right):
        super().__init__(x, y, *CATCHER_SIZE)
        self.spawn_x = float(x)
        self.spawn_y = float(y)
        self.patrol_left = patrol_left
        self.patrol_right = patrol_right
        self.vx = self.PATROL_SPEED
        self.facing = 1
        self.chasing = False
        self.alert_timer = 0

    def _respawn_if_far(self, player):
        if abs(player.x - self.spawn_x) > ENEMY_RESPAWN_DIST:
            self.x = self.spawn_x
            self.y = self.spawn_y
            self.chasing = False
            self.alert_timer = 0
            self.vx = self.PATROL_SPEED
            self.facing = 1

    def update(self, player, platforms):
        super().update(player, platforms)
        self._respawn_if_far(player)

        dist = abs(player.x - self.x)
        player_vert = abs(player.y - self.y)

        if dist < ENEMY_ALERT_RAD and player_vert < 80:
            self.chasing = True
            self.alert_timer = 30
        else:
            if self.alert_timer > 0:
                self.alert_timer -= 1
            else:
                self.chasing = False

        if self.chasing:
            spd = CATCHER_CHASE_SPD
            if abs(player.x - self.x) <= 12:
                self.vx = 0          # dead-zone: don't jitter right under Ollie
            elif player.x > self.x:
                self.vx = spd
                self.facing = 1
            else:
                self.vx = -spd
                self.facing = -1
        else:
            # Patrol
            if self.x >= self.patrol_right:
                self.vx = -self.PATROL_SPEED
                self.facing = -1
            elif self.x <= self.patrol_left:
                self.vx = self.PATROL_SPEED
                self.facing = 1

        self.x += self.vx

        # Gravity stub — keep on platforms
        self.y = min(self.y, GROUND_Y - self.h)

        if self.rect.colliderect(player.rect):
            return "life_damage"
        return "alert" if dist < ENEMY_ALERT_RAD and player_vert < 80 else None

    SPRITE_H = 86   # rendered pixel height (taller than the 56px collision rect)

    def draw(self, surf, cam_x):
        flip = self.facing == -1
        cx = int(self.x - cam_x) + self.w // 2
        feet = int(self.y) + self.h
        # Walk-cycle: alternate the two stock walk poses while moving, idle when still
        moving = abs(self.vx) > 0.05
        if moving:
            frame_img = "char/catcher_walk1.png" if (self.frame // 8) % 2 == 0 else "char/catcher_walk2.png"
        else:
            frame_img = "char/catcher_idle.png"
        art.blit_sprite(surf, frame_img, cx, feet, self.SPRITE_H, flip=flip)

        # Procedural catching net in the leading hand (keeps the "dog catcher" read)
        hand_x = cx + (22 if not flip else -22)
        hand_y = feet - int(self.SPRITE_H * 0.52)
        tip_x = cx + (46 if not flip else -46)
        tip_y = hand_y - 22
        aadraw.line(surf, (110, 80, 50), (hand_x, hand_y), (tip_x, tip_y), 4)
        aadraw.ellipse(surf, (210, 210, 215), (tip_x - 13, tip_y - 22, 26, 30), 0)
        aadraw.ellipse(surf, (150, 150, 160), (tip_x - 13, tip_y - 22, 26, 30), 2)
        # mesh hint
        for k in range(-1, 2):
            aadraw.line(surf, (150, 150, 160), (tip_x + k * 7, tip_y - 20),
                        (tip_x + k * 7, tip_y + 6), 1)

        # Alert !
        if self.alert_timer > 0:
            surf.blit(_font("Arial", 18, True).render("!", True, RED),
                      (cx - 4, feet - self.SPRITE_H - 18))


# ---------------------------------------------------------------------------
# Bird (small, friendly — Ollie chases)
# ---------------------------------------------------------------------------
class Bird(NPC):
    def __init__(self, x, y):
        super().__init__(x, y, *BIRD_SIZE)
        self.vx = random.choice([-1, 1]) * 0.5
        self.vy = 0.0
        self.base_y = float(y)
        self.fleeing = False
        self.caught = False
        self.flutter = 0

    def update(self, player, platforms):
        super().update(player, platforms)
        dist = math.hypot(player.x - self.x, player.y - self.y)

        if dist < BIRD_CATCH_RAD and not self.caught:
            self.caught = True
            return "caught"

        if dist < BIRD_FLEE_RAD:
            self.fleeing = True
        else:
            self.fleeing = False

        if self.fleeing:
            dx = self.x - player.x
            self.vx = (3.0 if dx > 0 else -3.0)
            self.vy = -2.0
        else:
            self.vx *= 0.95
            self.vy = math.sin(self.frame * 0.08) * 0.5

        self.x += self.vx
        self.y += self.vy
        # Gentle hover
        self.y = self.base_y + math.sin(self.frame * 0.05) * 12
        self.flutter = (self.flutter + 1) % 12
        return None

    def draw(self, surf, cam_x):
        if self.caught:
            return
        sx = int(self.x - cam_x)
        sy = int(self.y)
        wing_up = self.flutter < 6
        # Body
        aadraw.ellipse(surf, (180, 140, 100), (sx, sy + 6, 28, 14))
        # Head
        aadraw.circle(surf, (160, 120, 80), (sx + 22, sy + 8), 7)
        # Beak
        aadraw.polygon(surf, ORANGE, [(sx + 28, sy + 8), (sx + 34, sy + 10), (sx + 28, sy + 12)])
        # Wing
        if wing_up:
            aadraw.ellipse(surf, (200, 160, 110), (sx + 2, sy, 20, 10))
        else:
            aadraw.ellipse(surf, (200, 160, 110), (sx + 2, sy + 8, 20, 10))
        # Eye
        aadraw.circle(surf, BLACK, (sx + 22, sy + 7), 2)


# ---------------------------------------------------------------------------
# Hawk (enemy, flies)
# ---------------------------------------------------------------------------
class Hawk(NPC):
    def __init__(self, x, y):
        super().__init__(x, y, *HAWK_SIZE)
        self.spawn_x = float(x)
        self.spawn_y = float(y)
        self.base_x = float(x)   # patrol centre (was incorrectly using base_y)
        self.base_y = float(y)
        self.vx = HAWK_PATROL_SPD
        self.vy_local = 0.0
        self.facing = 1

    def _respawn_if_far(self, player):
        if abs(player.x - self.spawn_x) > ENEMY_RESPAWN_DIST:
            self.x = self.spawn_x
            self.y = self.spawn_y
            self.vx = HAWK_PATROL_SPD
            self.vy_local = 0.0
            self.facing = 1

    def update(self, player, platforms):
        super().update(player, platforms)
        self._respawn_if_far(player)

        dist = math.hypot(player.x - self.x, player.y - self.y)
        if dist < HAWK_CHASE_RAD:
            dx = player.x - self.x
            dy = player.y - self.y
            self.vx = (dx / dist) * HAWK_CHASE_SPD
            self.vy_local = (dy / dist) * HAWK_CHASE_SPD
            self.facing = 1 if dx > 0 else -1
        else:
            self.vy_local = math.sin(self.frame * 0.05) * 1.0
            if self.x > self.base_x + 400:
                self.vx = -HAWK_PATROL_SPD
                self.facing = -1
            elif self.x < self.base_x - 400:
                self.vx = HAWK_PATROL_SPD
                self.facing = 1

        self.x += self.vx
        self.y += self.vy_local
        self.y = max(60, min(self.y, self.base_y + 40))

        if self.rect.colliderect(player.rect):
            return "life_damage"
        return "alert" if dist < ENEMY_ALERT_RAD else None

    def draw(self, surf, cam_x):
        sx = int(self.x - cam_x)
        sy = int(self.y)
        flip = self.facing == -1
        sgn = 1 if not flip else -1

        BRN    = (122, 84, 50)
        BRN_DK = (84, 56, 30)
        CREAM  = (236, 218, 186)

        cx, cy = sx + 19, sy + 12
        flap = math.sin(self.frame * 0.3)          # wing beat

        # Fanned tail at the back
        bxk = cx - sgn * 16
        aadraw.polygon(surf, BRN_DK, [(cx - sgn * 5, cy), (bxk, cy - 7), (bxk, cy + 7)])

        # Two big swept wings (top-down), beating up and down
        for s in (-1, 1):
            spread = 18 - int(abs(flap) * 7)
            shoulder = (cx + sgn * 2, cy)
            tip = (cx - sgn * 7, cy + s * spread)
            mid = (cx + sgn * 8, cy + s * 5)
            aadraw.polygon(surf, BRN if s > 0 else BRN_DK, [shoulder, tip, mid])
            # feather notches at the wing tip
            aadraw.line(surf, BRN_DK, tip, (tip[0] + sgn * 4, tip[1] - s * 2), 2)

        # Body with pale chest
        aadraw.ellipse(surf, BRN, (cx - 12, cy - 6, 26, 13))
        aadraw.ellipse(surf, CREAM, (cx - 6, cy - 2, 15, 8))

        # Head + fierce eye + hooked beak
        hx = cx + sgn * 14
        aadraw.circle(surf, BRN, (hx, cy - 2), 6)
        aadraw.ellipse(surf, CREAM, (hx - 4, cy - 4, 8, 7))
        aadraw.circle(surf, (250, 205, 50), (hx + sgn * 1, cy - 3), 3)
        aadraw.circle(surf, BLACK, (hx + sgn * 1, cy - 3), 2)
        aadraw.line(surf, BRN_DK, (hx - sgn * 2, cy - 6), (hx + sgn * 5, cy - 5), 2)  # brow
        bkx = hx + sgn * 5
        aadraw.polygon(surf, (245, 190, 40),
                       [(bkx, cy - 3), (bkx + sgn * 8, cy), (bkx, cy + 1)])
        aadraw.polygon(surf, (205, 150, 25),
                       [(bkx + sgn * 5, cy), (bkx + sgn * 8, cy + 1), (bkx + sgn * 3, cy + 2)])


# ---------------------------------------------------------------------------
# Lion (ground enemy)
# ---------------------------------------------------------------------------
class GroundEnemy(NPC):
    def __init__(self, x, y):
        super().__init__(x, y, *LION_SIZE)
        self.spawn_x = float(x)
        self.spawn_y = float(y)
        self.patrol_left  = x - 150
        self.patrol_right = x + 150
        self._patrol_spd  = LION_PATROL_SPD
        self._chase_spd   = LION_CHASE_SPD
        self.vx = self._patrol_spd
        self.facing = 1

    def _respawn_if_far(self, player):
        if abs(player.x - self.spawn_x) > ENEMY_RESPAWN_DIST:
            self.x = self.spawn_x
            self.y = self.spawn_y
            self.vx = self._patrol_spd
            self.facing = 1

    def update(self, player, platforms):
        super().update(player, platforms)
        self._respawn_if_far(player)

        dist = math.hypot(player.x - self.x, player.y - self.y)

        if dist < BEAST_CHASE_RAD:
            dx = player.x - self.x
            if abs(dx) < 8:
                self.vx = 0  # directly below player — stand still rather than jitter
            else:
                self.vx = self._chase_spd if dx > 0 else -self._chase_spd
                self.facing = 1 if dx > 0 else -1
        else:
            if self.x > self.patrol_right:
                self.vx = -self._patrol_spd; self.facing = -1
            elif self.x < self.patrol_left:
                self.vx = self._patrol_spd; self.facing = 1

        self.x += self.vx
        self.y = min(self.y, GROUND_Y - self.h)

        if self.rect.colliderect(player.rect):
            return "life_damage"
        return "alert" if dist < ENEMY_ALERT_RAD else None

    def draw(self, surf, cam_x):
        sx = int(self.x - cam_x)
        sy = int(self.y)
        flip = self.facing == -1
        w, h = self.w, self.h

        BODY    = (232, 182, 92)
        BODY_DK = (198, 142, 58)
        BELLY   = (248, 222, 162)
        MANE    = (182, 118, 50)
        MANE_DK = (146, 88, 34)
        MANE_LT = (210, 146, 70)
        MUZZLE  = (250, 232, 198)

        # Contact shadow
        art.ground_shadow(surf, sx + w // 2, sy + h + 2, w + 8, 12, 65)

        sgn = 1 if not flip else -1
        head_cx = sx + (w - 15) if not flip else sx + 15
        head_cy = sy + 15

        # Tail with dark tuft (back side)
        tail_x = sx + (8 if not flip else w - 8)
        tx2 = tail_x - sgn * 18
        aadraw.line(surf, BODY_DK, (tail_x, sy + 22), (tx2, sy + 9), 4)
        aadraw.circle(surf, MANE_DK, (tx2, sy + 8), 5)

        # Legs (gentle walk bob)
        leg_off = int(math.sin(self.frame * 0.3) * 3)
        for i, lx in enumerate([sx + 12, sx + 22, sx + w - 24, sx + w - 14]):
            bob = leg_off if i % 2 == 0 else -leg_off
            aadraw.rect(surf, BODY_DK, (lx, sy + 26, 7, 13))
            aadraw.circle(surf, BODY, (lx + 3, sy + 39 + max(0, bob) // 2), 4)

        # Body + belly highlight
        aadraw.ellipse(surf, BODY, (sx + 5, sy + 9, w - 10, 25))
        aadraw.ellipse(surf, BELLY, (sx + 13, sy + 20, w - 26, 12))

        # Big fluffy mane — three dense rings of tufts
        for r, col, sz in [(20, MANE_DK, 7), (16, MANE, 7), (11, MANE_LT, 6)]:
            for a in range(0, 360, 18):
                mx = head_cx + int(math.cos(math.radians(a)) * r)
                my = head_cy + int(math.sin(math.radians(a)) * r)
                aadraw.circle(surf, col, (mx, my), sz)

        # Head
        aadraw.circle(surf, BODY, (head_cx, head_cy), 14)
        # Rounded ears with inner
        for ox in (-8, 8):
            aadraw.circle(surf, MANE, (head_cx + ox, head_cy - 12), 5)
            aadraw.circle(surf, MUZZLE, (head_cx + ox, head_cy - 12), 2)
        # Muzzle + nose + mouth
        mz_x = head_cx + sgn * 4
        aadraw.ellipse(surf, MUZZLE, (mz_x - 9, head_cy + 2, 20, 13))
        aadraw.polygon(surf, (78, 50, 36),
                       [(mz_x + sgn * 1, head_cy + 4), (mz_x + sgn * 7, head_cy + 4),
                        (mz_x + sgn * 4, head_cy + 7)])
        aadraw.line(surf, (78, 50, 36), (mz_x + sgn * 4, head_cy + 7),
                    (mz_x + sgn * 4, head_cy + 11), 2)
        # Two cute-but-fierce eyes
        for eoff in (-4, 6):
            ex = head_cx + eoff
            aadraw.circle(surf, WHITE, (ex, head_cy - 2), 3)
            aadraw.circle(surf, BLACK, (ex + sgn, head_cy - 2), 2)
            aadraw.line(surf, MANE_DK, (ex - 3, head_cy - 6), (ex + 3, head_cy - 5), 2)


# ---------------------------------------------------------------------------
# Lily / Leia (friendly girl)
# ---------------------------------------------------------------------------
class FriendlyGirl(NPC):
    AWAY_DIST = 160   # px Ollie must step back before the reward resets

    def __init__(self, x, y, name="Lily", hair_color=None,
                 reward_label="Good boy!", points=20):
        super().__init__(x, y, *LILY_SIZE)
        self.name = name
        self.hair_color = hair_color or (255, 230, 80)
        self.reward_label = reward_label
        self.points = points
        self.rewarded_this_visit = False   # resets when Ollie walks away
        self.greeting = False              # True when Ollie is near → waving pose

    def update(self, player, platforms):
        super().update(player, platforms)
        dist = abs(player.x - self.x)

        # Distance-based reset so every new pass can earn a reward
        if self.rewarded_this_visit and dist > self.AWAY_DIST:
            self.rewarded_this_visit = False

        # Only reward when Ollie is actively moving RIGHT (toward home)
        self.greeting = dist < 200   # wave when Ollie is in greeting range

        if dist < LILY_GIVE_RAD and player.vx > 0 and not self.rewarded_this_visit:
            self.rewarded_this_visit = True
            return "treat"

        if dist < 200:
            return "wave"
        return None

    def draw(self, surf, cam_x):
        sx = int(self.x - cam_x)
        sy = int(self.y)

        cx = sx + self.w // 2
        feet = sy + self.h
        # Stock girl sprite, recoloured per character (Lily=orange, Leia=gold).
        # Waves when greeting Ollie or just after giving a treat.
        waving = getattr(self, "greeting", False) or self.rewarded_this_visit
        pose = "wave" if waving else "idle"
        img = art.blit_sprite(surf, "char/%s_%s.png" % (self.name.lower(), pose),
                              cx, feet, 80)
        top = feet - img.get_height()

        # Treat biscuit by her hand right after she gives one
        if self.rewarded_this_visit:
            aadraw.circle(surf, BROWN, (cx + 24, top + 20), 6)
            aadraw.circle(surf, (150, 100, 50), (cx + 24, top + 20), 6, 1)

        # Name tag above her head
        label = _font("Arial", 12, True).render(self.name, True, PURPLE)
        tag_bg = pygame.Surface((label.get_width() + 10, label.get_height() + 4), pygame.SRCALPHA)
        tag_bg.fill((255, 255, 255, 180))
        surf.blit(tag_bg, (cx - tag_bg.get_width() // 2, top - 20))
        surf.blit(label, (cx - label.get_width() // 2, top - 18))


# ---------------------------------------------------------------------------
# Angel
# ---------------------------------------------------------------------------
class Angel(NPC):
    _TARGET_Y = 120   # screen-space Y to rest at during glow phase
    _DESCEND_SPD = (_TARGET_Y - (-80)) / ANGEL_DESCEND_FRAMES
    _ASCEND_SPD  = (_TARGET_Y - (-80)) / ANGEL_ASCEND_FRAMES

    def __init__(self):
        super().__init__(-200, -200, *ANGEL_SIZE)
        self.visible = False
        self.phase = "idle"   # idle | descend | glow | ascend
        self.phase_timer = 0
        self.screen_x = 640   # screen-space X, set at trigger time
        self.glow_particles = []

    def trigger(self, world_x, cam_x):
        if self.visible:      # only one Angel on screen at a time
            return
        self.screen_x = max(80, min(int(world_x - cam_x), SCREEN_WIDTH - 120))
        self.y = -80.0        # start above the visible screen (screen-space Y)
        self.visible = True
        self.phase = "descend"
        self.phase_timer = ANGEL_DESCEND_FRAMES
        self.glow_particles = []

    def update(self, player, platforms):
        super().update(player, platforms)
        if not self.visible:
            return

        self.phase_timer -= 1

        if self.phase == "descend":
            self.y += self._DESCEND_SPD
            if self.phase_timer <= 0:
                self.y = float(self._TARGET_Y)
                self.phase = "glow"
                self.phase_timer = ANGEL_GLOW_FRAMES
        elif self.phase == "glow":
            if self.phase_timer <= 0:
                self.phase = "ascend"
                self.phase_timer = ANGEL_ASCEND_FRAMES
        elif self.phase == "ascend":
            self.y -= self._ASCEND_SPD
            if self.phase_timer <= 0:
                self.visible = False
                self.phase = "idle"
                self.glow_particles = []
                return

        # Sparkle particles stored in screen-space coords
        if self.frame % 4 == 0:
            self.glow_particles.append([
                self.screen_x + random.randint(0, self.w),
                self.y + random.randint(0, self.h),
                random.uniform(-1.5, 1.5),
                random.uniform(-2, 0),
                30,
            ])
        self.glow_particles = [[px + pvx, py + pvy, pvx, pvy, life - 1]
                                for px, py, pvx, pvy, life in self.glow_particles if life > 1]

    def draw(self, surf, cam_x):
        if not self.visible:
            return
        sx = self.screen_x
        sy = int(self.y)

        # Glow aura — larger and brighter during glow phase
        pulse = 0.7 + 0.3 * math.sin(self.frame * 0.2)
        glow_r = int((60 if self.phase == "glow" else 40) * pulse)
        alpha  = 130 if self.phase == "glow" else 80
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        aadraw.circle(glow_surf, (255, 255, 150, alpha), (glow_r, glow_r), glow_r)
        surf.blit(glow_surf, (sx + self.w // 2 - glow_r, sy + self.h // 2 - glow_r))

        # Sparkle particles (screen-space — no cam_x subtraction needed)
        for px, py, pvx, pvy, life in self.glow_particles:
            r = max(1, life // 10)
            aadraw.circle(surf, GOLD, (int(px), int(py)), r)

        cx = sx + self.w // 2

        # Wings — layered feathers, gently flapping
        wf = int(math.sin(self.frame * 0.3) * 8)
        for side in (-1, 1):
            base_x = cx + side * 10
            for k, (col, ww, hh) in enumerate([((205, 212, 245), 30, 30),
                                               ((230, 234, 252), 24, 24),
                                               (WHITE, 16, 16)]):
                aadraw.ellipse(surf, col,
                               (base_x + side * (4 + k * 4) - ww // 2,
                                sy + 8 - wf + k * 3, ww, hh))

        # Flowing robe with a soft shaded fold + gold hem
        aadraw.polygon(surf, WHITE, [(cx - 14, sy + 22), (cx + 14, sy + 22),
                                     (cx + 20, sy + 56), (cx - 20, sy + 56)])
        aadraw.polygon(surf, (224, 228, 244), [(cx, sy + 22), (cx + 14, sy + 22),
                                               (cx + 20, sy + 56), (cx, sy + 56)])
        aadraw.line(surf, GOLD, (cx - 19, sy + 54), (cx + 19, sy + 54), 2)

        # Body + arms
        aadraw.rect(surf, (255, 244, 226), (cx - 9, sy + 14, 18, 12), border_radius=4)
        aadraw.line(surf, (255, 244, 226), (cx - 8, sy + 18), (cx - 16, sy + 28), 4)
        aadraw.line(surf, (255, 244, 226), (cx + 8, sy + 18), (cx + 16, sy + 28), 4)

        # Head + serene face (closed eyes, rosy cheeks, gentle smile)
        aadraw.circle(surf, (255, 232, 196), (cx, sy + 7), 10)
        aadraw.circle(surf, (255, 190, 175), (cx - 5, sy + 9), 2)
        aadraw.circle(surf, (255, 190, 175), (cx + 5, sy + 9), 2)
        aadraw.arc(surf, (90, 60, 40), (cx - 6, sy + 4, 5, 4), 0, math.pi, 2)
        aadraw.arc(surf, (90, 60, 40), (cx + 1, sy + 4, 5, 4), 0, math.pi, 2)
        aadraw.arc(surf, (200, 110, 110), (cx - 3, sy + 9, 6, 4), 0, math.pi, 1)

        # Glowing halo
        halo_y = sy - 4 + int(math.sin(self.frame * 0.1) * 2)
        surf.blit(art.radial_glow(16, (255, 240, 150), 70), (cx - 16, halo_y - 16))
        aadraw.ellipse(surf, GOLD, (cx - 12, halo_y - 3, 24, 8), 3)

        # Stars orbiting the halo
        for i in range(5):
            angle = self.frame * 0.05 + i * (2 * math.pi / 5)
            stx = cx + int(math.cos(angle) * 20)
            sty = halo_y + int(math.sin(angle) * 6)
            aadraw.circle(surf, SUN_YELLOW, (stx, sty), 2)
            aadraw.circle(surf, WHITE, (stx, sty), 1)

        # "Go Ollie!" bounces gently during glow phase
        if self.phase == "glow":
            bounce = int(math.sin(self.frame * 0.15) * 4)
            text = _font("Arial", 22, True).render("Go Ollie!", True, GOLD)
            surf.blit(text, (sx + self.w // 2 - text.get_width() // 2, sy - 32 + bounce))


# ---------------------------------------------------------------------------
# Water Bottle pickup
# ---------------------------------------------------------------------------
class WaterBottle(NPC):
    def __init__(self, x, y):
        super().__init__(x, y, 24, 32)
        self.collected = False

    def update(self, player, platforms):
        super().update(player, platforms)
        if not self.collected and self.rect.colliderect(player.rect):
            self.collected = True
            return "collected"
        return None

    def draw(self, surf, cam_x):
        if self.collected:
            return
        sx = int(self.x - cam_x)
        sy = int(self.y)
        bob = int(math.sin(self.frame * 0.1) * 4)
        # Bottle
        aadraw.rect(surf, LIGHT_BLUE, (sx + 4, sy + 8 + bob, 16, 20))
        aadraw.rect(surf, WHITE, (sx + 6, sy + 10 + bob, 12, 16))
        aadraw.rect(surf, BLUE, (sx + 8, sy + 4 + bob, 8, 6))
        # Shine
        aadraw.line(surf, WHITE, (sx + 7, sy + 11 + bob), (sx + 7, sy + 22 + bob), 2)
        # Label
        surf.blit(_font("Arial", 8).render("H2O", True, BLUE), (sx + 4, sy + 14 + bob))


# ---------------------------------------------------------------------------
# Magic Carpet
# ---------------------------------------------------------------------------
class MagicCarpet(NPC):
    def __init__(self, x, y):
        super().__init__(x, y, *CARPET_SIZE)
        self.active = False
        self.vx = 0.0
        self.flying = False
        self.trail = []   # sparkle star trail: [x, y, vx, vy, life, color]

    def start(self):
        self.active = True

    def launch(self):
        self.flying = True
        self.vx = 4.0

    def update(self, player, platforms):
        super().update(player, platforms)
        if self.flying:
            # Emit trail particles from the back (left) edge
            if self.frame % 2 == 0:
                trail_colors = [GOLD, SUN_YELLOW, WHITE, CARPET_GOLD, (255, 130, 210)]
                for _ in range(3):
                    self.trail.append([
                        self.x + random.randint(0, 18),
                        self.y + random.randint(2, 10),
                        random.uniform(-2.5, -0.4),
                        random.uniform(-1.5, 1.5),
                        random.randint(22, 40),
                        random.choice(trail_colors),
                    ])
            self.x += self.vx
            self.vx = min(self.vx + 0.05, 8.0)
            self.y -= 0.5

        # Age trail regardless of flying state so existing particles fade out
        self.trail = [
            [p[0] + p[2], p[1] + p[3], p[2], p[3], p[4] - 1, p[5]]
            for p in self.trail if p[4] > 1
        ]
        return None

    def draw(self, surf, cam_x):
        if not self.active:
            return
        sx = int(self.x - cam_x)
        sy = int(self.y)
        wave = int(math.sin(self.frame * 0.15) * 4)

        # Draw star trail first (behind carpet)
        for p in self.trail:
            tsx = int(p[0] - cam_x)
            if -20 < tsx < SCREEN_WIDTH + 20:
                r = max(1, int(p[4] / 10))
                aadraw.circle(surf, p[5], (tsx, int(p[1])), r)
                if r > 1:
                    aadraw.circle(surf, WHITE, (tsx, int(p[1])), max(1, r - 1))

        # Carpet body
        points = [
            (sx, sy + wave), (sx + self.w, sy + wave),
            (sx + self.w + 8, sy + 12 - wave), (sx - 8, sy + 12 - wave)
        ]
        aadraw.polygon(surf, CARPET_RED, points)

        # Gold border strips
        aadraw.line(surf, CARPET_GOLD, (sx + 2, sy + wave + 1), (sx + self.w - 2, sy + wave + 1), 3)
        aadraw.line(surf, CARPET_GOLD, (sx + 2, sy + 11 - wave), (sx + self.w - 2, sy + 11 - wave), 3)

        # Blue diamond pattern
        for i in range(3):
            dx = sx + 14 + i * 26
            dy = sy + 6 + wave // 2
            aadraw.polygon(surf, CARPET_BLUE, [
                (dx, dy - 4), (dx + 7, dy), (dx, dy + 4), (dx - 7, dy)
            ])

        # Fringe (bottom)
        for fx in range(sx, sx + self.w, 6):
            aadraw.line(surf, CARPET_GOLD, (fx, sy + 12 - wave), (fx + 2, sy + 18 - wave), 2)

        # Center medallion
        mx, my = sx + self.w // 2, sy + 6 + wave // 2
        aadraw.circle(surf, CARPET_GOLD, (mx, my), 9)
        aadraw.circle(surf, CARPET_BLUE, (mx, my), 6)
        aadraw.circle(surf, CARPET_GOLD, (mx, my), 3)
        # Spinning spokes on medallion when flying
        if self.flying:
            for a in range(0, 360, 60):
                ex = mx + int(math.cos(math.radians(a + self.frame * 3)) * 7)
                ey = my + int(math.sin(math.radians(a + self.frame * 3)) * 7)
                aadraw.line(surf, SUN_YELLOW, (mx, my), (ex, ey), 1)
