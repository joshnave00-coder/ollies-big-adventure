import pygame
import random
import math
from constants import *
from player import Player
from level import Level
from level2 import Level2
from level3 import Level3
from characters import Angel
from ui import UI
import leaderboard as lb
from sounds import SoundManager


class _HeldKeys:
    """Keyboard state plus extra keys held via a gamepad (same [] lookup)."""
    def __init__(self, keys, extra):
        self._keys = keys
        self._extra = extra

    def __getitem__(self, key):
        return key in self._extra or self._keys[key]


class Game:
    def __init__(self, screen, display=None):
        self.screen = screen
        self.display = display  # real window surface; None = same as screen
        self.clock = pygame.time.Clock()
        self.ui = UI(screen)
        self.state = STATE_TITLE
        self.frame = 0
        self.lb_scores = lb.load_scores()   # cached leaderboard; refresh on save
        self.sounds = SoundManager()        # build all sounds once at startup
        self._lag = 0.0                     # real time not yet turned into logic steps (ms)
        self._pads = {}                     # connected gamepads by instance id
        self._init_game()

    def _init_game(self):
        self.player = Player(80, GROUND_Y - OLLIE_SIZE[1])
        self.level = Level()
        self.angel = Angel()
        self.ui.clear_transient()
        self.score_event_count = 0
        self.has_water = False

        # End sequence
        self.slide_done = False
        self.carpet_launched = False
        self.carpet_done = False
        self.carpet_wait = 0   # frames before carpet departs

        # Carpet ride position for Ollie
        self.carpet_ride = False

        # Traveling transition timer
        self.travel_timer = 0

        # Home screen timer
        self.home_timer = 0

        # Slide sequence
        self.sliding = False
        self.slide_timer = 0

        # High-score initials entry
        self.pending_score = 0
        self.initials = ['A', 'A', 'A']
        self.initials_cursor = 0

        # Level 2
        self.lives_bonus = 0
        self.level2_win_timer = 0
        self.bone_celebrate_timer = 0
        self.score_event_count = 0

        # Level 3 (Heaven)
        self.ascend_timer = 0
        self.heaven_celebrate_timer = 0
        self.heaven_win_timer = 0

        # Easter eggs: press 2 (Level 2) or 3 (Level 3) five times on the title
        self._title_key2_presses = []   # list of frame numbers
        self._title_key3_presses = []

        # Pause support
        self._prev_state = STATE_PLAYING

    def _init_level2(self):
        """Start Level 2 — player keeps score and lives from Level 1."""
        self.level = Level2()
        self.angel = Angel()
        self.ui.clear_transient()
        self.has_water = False
        self.slide_done = False
        self.carpet_launched = False
        self.carpet_done = False
        self.carpet_wait = 0
        self.carpet_ride = False
        self.travel_timer = 0
        self.home_timer = 0
        self.sliding = False
        self.slide_timer = 0
        self.level2_win_timer = 0
        self.bone_celebrate_timer = 0
        self.score_event_count = 0
        # Respawn Ollie at the Level 2 start position
        self.player.x = 80.0
        self.player.y = float(GROUND_Y - OLLIE_SIZE[1])
        self.player.vx = 0.0
        self.player.vy = 0.0
        self.player.on_ground = True
        self.player.health = MAX_HEALTH

    def _init_level3(self):
        """Start Level 3 (Heaven) — player keeps score and lives from Level 2."""
        self.level = Level3()
        self.angel = Angel()
        self.ui.clear_transient()
        self.has_water = False
        self.slide_done = False
        self.carpet_launched = False
        self.carpet_done = False
        self.carpet_wait = 0
        self.carpet_ride = False
        self.travel_timer = 0
        self.home_timer = 0
        self.sliding = False
        self.slide_timer = 0
        self.level2_win_timer = 0
        self.bone_celebrate_timer = 0
        self.heaven_celebrate_timer = 0
        self.heaven_win_timer = 0
        self.score_event_count = 0
        # Respawn Ollie at the Level 3 start, fresh and healthy
        self.player.x = 80.0
        self.player.y = float(GROUND_Y - OLLIE_SIZE[1])
        self.player.vx = 0.0
        self.player.vy = 0.0
        self.player.on_ground = True
        self.player.health = MAX_HEALTH

    # ------------------------------------------------------------------ #
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type in (pygame.WINDOWFOCUSLOST, pygame.WINDOWMINIMIZED):
                    # Don't let enemies catch Ollie while nobody is looking
                    self._pause()
                self._handle_event(self._pad_event(event))

            self._advance(dt)
            self._draw()
            if self.display and self.display is not self.screen:
                # After a window resize the live surface can be a new object
                self._present(pygame.display.get_surface() or self.display)
            pygame.display.flip()

    def _present(self, display):
        """Copy the fixed-size game surface to the window, scaled to fit with
        black bars, so a small or maximised window never crops or shrinks the game."""
        dw, dh = display.get_size()
        gw, gh = self.screen.get_size()
        if (dw, dh) == (gw, gh):
            display.blit(self.screen, (0, 0))
            return
        scale = min(dw / gw, dh / gh)
        w, h = int(gw * scale), int(gh * scale)
        display.fill((0, 0, 0))
        if w > 0 and h > 0:
            display.blit(pygame.transform.smoothscale(self.screen, (w, h)),
                         ((dw - w) // 2, (dh - h) // 2))

    def _advance(self, dt_ms):
        """Turn `dt_ms` of real time into fixed 1/FPS logic steps, so the game
        plays at the same speed whether the screen draws at 60 fps or 20.
        Returns the number of steps run."""
        if abs(dt_ms - STEP_MS) < STEP_SNAP_MS:
            dt_ms = STEP_MS            # normal frame: exactly one step, no judder
        self._lag += dt_ms
        steps = 0
        while self._lag >= STEP_MS - 1e-6 and steps < MAX_CATCHUP_STEPS:
            self._lag -= STEP_MS
            self.frame += 1
            self._update()
            steps += 1
        # Still behind after the most steps we allow (a long stall such as dragging
        # the window): drop the backlog rather than fast-forwarding to catch up
        if self._lag >= STEP_MS:
            self._lag = 0.0
        return steps

    # ------------------------------------------------------------------ #
    # Gamepad — mapped onto the keyboard controls so there is one input path
    # ------------------------------------------------------------------ #
    def _pad_event(self, event):
        """Track gamepads and translate their button / d-pad presses into the
        equivalent KEYDOWN.  Any other event is returned unchanged."""
        if event.type == pygame.JOYDEVICEADDED:
            try:
                pad = pygame.joystick.Joystick(event.device_index)
                self._pads[pad.get_instance_id()] = pad
            except pygame.error:
                pass
        elif event.type == pygame.JOYDEVICEREMOVED:
            self._pads.pop(event.instance_id, None)
            self._pause()              # controller unplugged mid-game
        elif event.type == pygame.JOYBUTTONDOWN:
            playing = self.state in (STATE_PLAYING, STATE_LEVEL2, STATE_LEVEL3, STATE_PAUSED)
            if event.button in PAD_PAUSE_BUTTONS and playing:
                return pygame.event.Event(pygame.KEYDOWN, key=pygame.K_p)
            if event.button in PAD_PAUSE_BUTTONS or event.button in PAD_JUMP_BUTTONS:
                return pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        elif event.type == pygame.JOYHATMOTION:
            hx, hy = event.value
            key = (pygame.K_LEFT if hx < 0 else pygame.K_RIGHT if hx > 0 else
                   pygame.K_UP if hy > 0 else pygame.K_DOWN if hy < 0 else None)
            if key is not None:
                return pygame.event.Event(pygame.KEYDOWN, key=key)
        return event

    def _read_input(self):
        """Held keys, with any gamepad's stick / d-pad / face buttons folded in."""
        keys = pygame.key.get_pressed()
        held = set()
        for pad in list(self._pads.values()):
            try:
                x = pad.get_axis(0) if pad.get_numaxes() > 0 else 0.0
                hat = pad.get_hat(0) if pad.get_numhats() > 0 else (0, 0)
                if x < -PAD_DEADZONE or hat[0] < 0:
                    held.add(pygame.K_LEFT)
                if x > PAD_DEADZONE or hat[0] > 0:
                    held.add(pygame.K_RIGHT)
                if hat[1] > 0 or any(pad.get_button(b) for b in PAD_JUMP_BUTTONS
                                     if b < pad.get_numbuttons()):
                    held.add(pygame.K_SPACE)
            except pygame.error:
                continue               # pad vanished between events
        return _HeldKeys(keys, held) if held else keys

    def _pause(self):
        """Pause if a pauseable play state is active. Returns True if it paused."""
        if self.state in (STATE_PLAYING, STATE_LEVEL2, STATE_LEVEL3):
            self._prev_state = self.state
            self.state = STATE_PAUSED
            return True
        return False

    # ------------------------------------------------------------------ #
    def _handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        key = event.key

        # Pause / resume — works in any active play state
        if key in (pygame.K_p, pygame.K_ESCAPE):
            if self._pause():
                return
            elif self.state == STATE_PAUSED:
                self.state = self._prev_state
                return

        # Volume: - / + wherever the sound setting is shown
        if self.state in (STATE_TITLE, STATE_HOWTO, STATE_PAUSED):
            if key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self.sounds.change_volume(-1)
                return
            if key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                self.sounds.change_volume(+1)
                return

        if self.state == STATE_PAUSED:
            if key == pygame.K_s:
                self.sounds.toggle()   # the pause overlay advertises this
            return

        if self.state == STATE_TITLE:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.state = STATE_PLAYING
            elif key in (pygame.K_h, pygame.K_i):
                self.state = STATE_HOWTO       # open the How to Play screen
            elif key == pygame.K_s:
                self.sounds.toggle()
            elif key == pygame.K_2:
                self._title_key2_presses.append(self.frame)
                # Keep only presses within the last 90 frames (~1.5 s)
                self._title_key2_presses = [
                    f for f in self._title_key2_presses if self.frame - f < 90]
                if len(self._title_key2_presses) >= 5:
                    self._title_key2_presses = []
                    self._init_level2()
                    self.state = STATE_LEVEL2
            elif key == pygame.K_3:
                self._title_key3_presses.append(self.frame)
                self._title_key3_presses = [
                    f for f in self._title_key3_presses if self.frame - f < 90]
                if len(self._title_key3_presses) >= 5:
                    self._title_key3_presses = []
                    self._init_level3()
                    self.state = STATE_LEVEL3

        elif self.state == STATE_HOWTO:
            # Sound can be toggled here too; any of these keys returns to title
            if key == pygame.K_s:
                self.sounds.toggle()
            elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE,
                         pygame.K_h, pygame.K_i, pygame.K_BACKSPACE):
                self.state = STATE_TITLE

        elif self.state == STATE_GAME_OVER:
            if key == pygame.K_RETURN:
                score = self.player.score
                if lb.is_high_score(score):
                    self.pending_score = score
                    self.initials = ['A', 'A', 'A']
                    self.initials_cursor = 0
                    self.state = STATE_ENTER_INITIALS
                else:
                    self._init_game()
                    self.state = STATE_PLAYING

        elif self.state == STATE_HOME:
            if key == pygame.K_RETURN:
                self._init_level2()
                self.state = STATE_LEVEL2

        elif self.state == STATE_LEVEL2_WIN:
            if key == pygame.K_RETURN:
                # Onward and upward — Ollie rides the carpet to Heaven (Level 3)
                self.state = STATE_ASCEND
                self.ascend_timer = 0
                self.sounds.play_carpet()

        elif self.state == STATE_HEAVEN_WIN:
            if key == pygame.K_RETURN:
                score = self.player.score
                if lb.is_high_score(score):
                    self.pending_score = score
                    self.initials = ['A', 'A', 'A']
                    self.initials_cursor = 0
                    self.state = STATE_ENTER_INITIALS
                else:
                    self._init_game()
                    self.state = STATE_TITLE

        elif self.state == STATE_ENTER_INITIALS:
            if key == pygame.K_ESCAPE:
                self._init_game()
                self.state = STATE_TITLE
                return
            elif key == pygame.K_LEFT:
                self.initials_cursor = max(0, self.initials_cursor - 1)
            elif key == pygame.K_RIGHT:
                self.initials_cursor = min(2, self.initials_cursor + 1)
            elif key == pygame.K_UP:
                cur = self.initials[self.initials_cursor]
                self.initials[self.initials_cursor] = chr((ord(cur) - ord('A') + 1) % 26 + ord('A'))
            elif key == pygame.K_DOWN:
                cur = self.initials[self.initials_cursor]
                self.initials[self.initials_cursor] = chr((ord(cur) - ord('A') - 1) % 26 + ord('A'))
            elif pygame.K_a <= key <= pygame.K_z:
                self.initials[self.initials_cursor] = chr(key - pygame.K_a + ord('A'))
                if self.initials_cursor < 2:
                    self.initials_cursor += 1
            elif key == pygame.K_RETURN:
                initials_str = ''.join(self.initials)
                self.lb_scores = lb.save_score(self.pending_score, initials_str)
                self._init_game()
                self.state = STATE_TITLE

    # ------------------------------------------------------------------ #
    def _update(self):
        if self.state in (STATE_TITLE, STATE_HOWTO, STATE_GAME_OVER, STATE_PAUSED):
            return

        if self.state == STATE_TRAVELING:
            self.travel_timer += 1
            if self.travel_timer >= TRAVEL_DURATION:
                # Award 100 pts per remaining life
                self.lives_bonus = self.player.lives * SCORE_LIVES_BONUS
                self.player.score += self.lives_bonus
                self.state = STATE_HOME
                self.home_timer = 0
                self.sounds.play_fanfare()
            return

        if self.state == STATE_HOME:
            self.home_timer += 1
            if self.home_timer == 120:
                self.ui.start_confetti()
            self.ui.update_confetti()
            return

        if self.state == STATE_LEVEL2_WIN:
            self.level2_win_timer += 1
            if self.level2_win_timer == 60:
                self.ui.start_confetti()
            self.ui.update_confetti()
            return

        if self.state == STATE_BONE_CELEBRATE:
            self.bone_celebrate_timer += 1
            self.ui.update_popups()
            if self.bone_celebrate_timer >= BONE_CELEBRATE_DURATION:
                self.state = STATE_LEVEL2_WIN
                self.level2_win_timer = 0
            return

        # ---- ASCEND: carpet rises through the clouds into Heaven ----
        if self.state == STATE_ASCEND:
            self.ascend_timer += 1
            if self.ascend_timer >= ASCEND_DURATION:
                self._init_level3()
                self.state = STATE_LEVEL3
            return

        # ---- HEAVEN celebration: Ollie touched God (healing + feast) ----
        if self.state == STATE_HEAVEN_CELEBRATE:
            self.heaven_celebrate_timer += 1
            self.ui.update_popups()
            if self.heaven_celebrate_timer >= HEAVEN_CELEBRATE_DURATION:
                self.state = STATE_HEAVEN_WIN
                self.heaven_win_timer = 0
            return

        # ---- HEAVEN win: Ollie's home in Heaven ----
        if self.state == STATE_HEAVEN_WIN:
            self.heaven_win_timer += 1
            if self.heaven_win_timer == 60:
                self.ui.start_confetti()
            self.ui.update_confetti()
            return

        if self.state == STATE_ENTER_INITIALS:
            return

        keys = self._read_input()

        # ---- LEVEL 3 PLAY (Heaven) ----
        if self.state == STATE_LEVEL3:
            self.player.update(keys, self.level.platforms)
            if self.player.jumped_this_frame:
                self.sounds.play_jump()
            self.level.update(self.player)
            self.angel.update(self.player, self.level.platforms)
            self.ui.update_popups()
            for ev in self.level.events:
                self._process_event(ev)
            if self.player.lives <= 0:
                self.state = STATE_GAME_OVER
                self.sounds.play_game_over()
            return

        # ---- LEVEL 2 PLAY ----
        if self.state == STATE_LEVEL2:
            self.player.update(keys, self.level.platforms)
            if self.player.jumped_this_frame:
                self.sounds.play_jump()
            self.level.update(self.player)
            self.angel.update(self.player, self.level.platforms)
            self.ui.update_popups()
            for ev in self.level.events:
                self._process_event(ev)
            if self.player.lives <= 0:
                self.state = STATE_GAME_OVER
                self.sounds.play_game_over()
            return

        # ---- CARPET RIDE ----
        if self.state == STATE_CARPET:
            self._update_carpet_sequence(keys)
            self.angel.update(self.player, self.level.platforms)
            self.ui.update_popups()
            return

        # ---- NORMAL PLAY ----
        if self.sliding:
            self._update_slide()
        else:
            self.player.update(keys, self.level.platforms)
            if self.player.jumped_this_frame:
                self.sounds.play_jump()
        self.level.update(self.player)
        self.angel.update(self.player, self.level.platforms)
        self.ui.update_popups()

        # Process level events
        for ev in self.level.events:
            self._process_event(ev)

        # Check game over
        if self.player.lives <= 0:
            self.state = STATE_GAME_OVER
            self.sounds.play_game_over()
            return   # don't let a same-frame carpet touch override Game Over

        # Trigger carpet if player reached the magic carpet area
        carpet = self.level.magic_carpet
        if (not carpet.flying and not self.carpet_launched and
                self.player.rect.colliderect(carpet.rect) and carpet.active):
            self._start_carpet_sequence()

    def _process_event(self, ev):
        kind = ev[0]

        if kind == "score":
            _, pts, label = ev
            self.player.score += pts
            self.player.add_sparkles()
            self.ui.add_popup(f"+{pts} {label}",
                              self.player.x + OLLIE_SIZE[0] // 2,
                              self.player.y - 20, GOLD)
            # Sound — differentiate by label
            if label == "Bird!":
                self.sounds.play_bird()
            elif label == "Coin!":
                self.sounds.play_coin()
            elif "Treat" in label:
                self.sounds.play_treat()
            else:
                self.sounds.play_score()
            # Maybe spawn angel
            self.score_event_count += 1
            if random.randint(1, ANGEL_CHANCE) == 1:
                self.angel.trigger(self.player.x + OLLIE_SIZE[0] // 2, self.level.camera_x)
                self.sounds.play_angel()

        elif kind == "life_damage":
            if self.player.lose_life():
                lives_left = max(self.player.lives, 0)
                self.ui.add_popup(
                    f"Ouch! {lives_left} {'life' if lives_left == 1 else 'lives'} left",
                    self.player.x, self.player.y - 20, RED)
                self.sounds.play_enemy_hit()

        elif kind == "damage":
            _, amt = ev
            if self.player.take_damage(amt):
                self.ui.add_popup("Ouch!", self.player.x, self.player.y - 20, RED)
                self.sounds.play_enemy_hit()

        elif kind == "hearts":
            self.player.add_hearts()

        elif kind == "alert":
            self.player.set_anim("alert", 20)

        elif kind == "water":
            self.has_water = True
            self.player.add_blue_sparkles()
            self.ui.add_popup("+Water", self.player.x, self.player.y - 30, LIGHT_BLUE)
            self.level.magic_carpet.start()   # reveal carpet
            self.sounds.play_water()

        elif kind == "found_crate":
            self.player.score += SCORE_BONE
            self.player.add_sparkles()
            self.ui.add_popup(f"+{SCORE_BONE} Big Bone!",
                              self.player.x + OLLIE_SIZE[0] // 2,
                              self.player.y - 30, GOLD)
            self.sounds.play_score()
            self.state = STATE_BONE_CELEBRATE
            self.bone_celebrate_timer = 0

        elif kind == "reached_god":
            # Ollie touches God: full score bonus, no more pain (full heal),
            # and the healing/feast celebration begins.
            self.player.score += SCORE_HEAVEN
            self.player.health = MAX_HEALTH
            self.player.lives += 1            # a gift of life in heaven
            self.player.add_sparkles()
            self.ui.add_popup(f"+{SCORE_HEAVEN} Heaven!",
                              self.player.x + OLLIE_SIZE[0] // 2,
                              self.player.y - 30, GOLD)
            self.sounds.play_heaven()
            self.state = STATE_HEAVEN_CELEBRATE
            self.heaven_celebrate_timer = 0

        elif kind == "slide":
            sr = self.level.slide_rect
            self.sliding = True
            self.slide_timer = 0
            # Snap Ollie to the top of the slide
            self.player.x = float(sr.x)
            self.player.y = float(sr.y - OLLIE_SIZE[1])
            self.player.vx = 0.0
            self.player.vy = 0.0
            self.player.facing = 1
            self.sounds.play_slide()
            if not self.has_water:
                # "Ouch" only when it really cost a life (not during the mercy window)
                hurt = self.player.lose_life()
                self.player.set_anim("sad", SLIDE_DURATION + 20)
                self.ui.add_popup("Ouch! Too hot!" if hurt else "Hot! Hot! Hot!",
                                  self.player.x, self.player.y - 30, HOT_RED)
            else:
                self.player.set_anim("wag", SLIDE_DURATION + 20)
                self.ui.add_popup("Wheee!", self.player.x, self.player.y - 30, SUN_YELLOW)

    def _update_slide(self):
        sr = self.level.slide_rect
        self.slide_timer += 1
        t = min(self.slide_timer / SLIDE_DURATION, 1.0)
        ease = t * t * (3.0 - 2.0 * t)   # smooth-step

        # Move Ollie along the slide diagonal (top-left → bottom-right of slide rect)
        self.player.x = sr.x + ease * (sr.width - OLLIE_SIZE[0])
        self.player.y = (sr.y - OLLIE_SIZE[1]) + ease * sr.height
        self.player.facing = 1

        # Tick counters without physics or input
        if self.player.invincible > 0:
            self.player.invincible -= 1
        if self.player.anim_timer > 0:
            self.player.anim_timer -= 1
        self.player.frame = (self.player.frame + 1) % 60
        self.player.tail_angle += 6 * self.player.tail_dir
        if abs(self.player.tail_angle) > 25:
            self.player.tail_dir *= -1
        self.player.particles = [
            (px, py, pvx, pvy, life - 1, color)
            for px, py, pvx, pvy, life, color in self.player.particles if life > 1
        ]
        self.player.particles = [
            (px + pvx, py + pvy, pvx, pvy * 0.9, life, color)
            for px, py, pvx, pvy, life, color in self.player.particles
        ]

        if self.slide_timer >= SLIDE_DURATION:
            self.sliding = False
            self.player.x = float(sr.right - OLLIE_SIZE[0])
            self.player.y = float(GROUND_Y - OLLIE_SIZE[1])
            self.player.vy = 0.0
            self.player.on_ground = True

    def _start_carpet_sequence(self):
        self.state = STATE_CARPET
        self.carpet_launched = False
        self.carpet_ride = True
        self.carpet_wait = 120
        self.level.magic_carpet.active = True

    def _update_carpet_sequence(self, keys):
        carpet = self.level.magic_carpet
        self.carpet_wait -= 1

        if self.carpet_wait == 90:
            # Lift off
            carpet.launch()
            self.player.set_anim("wag", 999)
            self.sounds.play_carpet()

        if carpet.flying:
            # Ollie rides the carpet
            self.player.x = carpet.x + CARPET_SIZE[0] // 2 - OLLIE_SIZE[0] // 2
            self.player.y = carpet.y - OLLIE_SIZE[1] + 4
            self.level.update_camera(self.player.x)

            # Carpet has flown off screen → traveling transition
            if carpet.x - self.level.camera_x > SCREEN_WIDTH + 200:
                self.state = STATE_TRAVELING
                self.travel_timer = 0
                self.carpet_done = True

        self.level.magic_carpet.update(self.player, self.level.platforms)

    # ------------------------------------------------------------------ #
    def _draw(self):
        if self.state == STATE_TITLE:
            self.ui.draw_title(self.frame, self.lb_scores, self.sounds.enabled,
                               self.sounds.status_text())
            return

        if self.state == STATE_HOWTO:
            self.ui.draw_howto(self.frame, self.sounds.enabled, self.sounds.status_text())
            return

        if self.state == STATE_ENTER_INITIALS:
            self.ui.draw_enter_initials(
                self.initials, self.initials_cursor,
                self.frame, self.pending_score, self.lb_scores)
            return

        if self.state == STATE_PAUSED:
            self._draw_game_world()
            self.ui.draw_hud(self.player, self.has_water, self.level.width,
                             self._goal_label())
            self.ui.draw_pause(self.sounds.status_text())
            return

        if self.state == STATE_GAME_OVER:
            self._draw_game_world()
            self.ui.draw_game_over(self.player.score, self.frame)
            return

        if self.state == STATE_TRAVELING:
            self.ui.draw_traveling_screen(self.travel_timer)
            return

        if self.state == STATE_HOME:
            self.ui.draw_home_screen(self.player.score, self.home_timer,
                                     self.carpet_done, self.lives_bonus)
            return

        if self.state == STATE_LEVEL2_WIN:
            self._draw_game_world()
            self.ui.draw_level2_win(self.player.score, self.level2_win_timer)
            return

        if self.state == STATE_BONE_CELEBRATE:
            self._draw_game_world()
            self.ui.draw_bone_celebrate(self.player, self.bone_celebrate_timer,
                                        self.level.camera_x)
            return

        if self.state == STATE_ASCEND:
            self.ui.draw_ascend_screen(self.ascend_timer)
            return

        if self.state == STATE_HEAVEN_CELEBRATE:
            self._draw_game_world()
            self.ui.draw_heaven_celebrate(self.player, self.heaven_celebrate_timer,
                                          self.level.camera_x)
            return

        if self.state == STATE_HEAVEN_WIN:
            self.ui.draw_heaven_win(self.player.score, self.heaven_win_timer)
            return

        self._draw_game_world()
        self.ui.draw_hud(self.player, self.has_water, self.level.width,
                         self._goal_label())
        self.ui.draw_popups(self.level.camera_x)

    def _goal_label(self):
        """HUD progress-bar target: Level 1 heads home, Level 2 hunts the bone,
        Level 3 climbs to Heaven."""
        if isinstance(self.level, Level3):
            return "Heaven"
        return "Bone" if isinstance(self.level, Level2) else "Home"

    def _draw_game_world(self):
        self.level.draw_background(self.screen)
        self.level.draw_world(self.screen)
        self.level.draw_characters(self.screen)
        self.player.draw(self.screen, self.level.camera_x)
        self.angel.draw(self.screen, self.level.camera_x)
