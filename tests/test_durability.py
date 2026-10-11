"""Regression tests for the durability fixes (0.8.1 and 0.8.2).

Runs the real Game headlessly (no window, no sound device) and drives it with
injected key presses.  The leaderboard is redirected to a temp folder, so the
real highscores.json is never touched.

    python -m unittest discover -s tests -v
"""
import json
import os
import shutil
import sys
import tempfile
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

import art  # noqa: E402
import leaderboard as lb  # noqa: E402
from constants import *  # noqa: E402,F401,F403
from game import Game  # noqa: E402

_TMP = None
_REAL_SCORES_FILE = lb._SCORES_FILE
_REAL_LEGACY_FILE = lb._LEGACY_FILE
_real_get_pressed = pygame.key.get_pressed


class _Keys:
    """Stand-in for pygame.key.get_pressed() so tests can hold keys down."""
    def __init__(self):
        self.down = set()

    def __getitem__(self, key):
        return key in self.down


KEYS = _Keys()


def setUpModule():
    global _TMP
    _TMP = tempfile.mkdtemp(prefix="ollie_tests_")
    lb._SCORES_FILE = os.path.join(_TMP, "highscores.json")
    lb._LEGACY_FILE = os.path.join(_TMP, "no_legacy_file.json")
    pygame.key.get_pressed = lambda: KEYS
    pygame.init()
    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


def tearDownModule():
    pygame.key.get_pressed = _real_get_pressed
    lb._SCORES_FILE = _REAL_SCORES_FILE
    lb._LEGACY_FILE = _REAL_LEGACY_FILE
    pygame.quit()
    shutil.rmtree(_TMP, ignore_errors=True)


def new_game():
    KEYS.down = set()
    return Game(pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)), pygame.display.get_surface())


def press(game, key):
    game._handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))


def step(game, frames=1, draw=False):
    for _ in range(frames):
        game.frame += 1
        game._update()
        if draw:
            game._draw()


def jump_to_level(game, n):
    """Use the title-screen shortcut (press 2 or 3 five times)."""
    for _ in range(5):
        press(game, pygame.K_2 if n == 2 else pygame.K_3)


class LeaderboardTests(unittest.TestCase):
    def setUp(self):
        for name in os.listdir(_TMP):
            path = os.path.join(_TMP, name)
            shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)

    def _write(self, content, mode="w"):
        with open(lb._SCORES_FILE, mode) as f:
            f.write(content)

    def test_damaged_files_never_crash_startup(self):
        for content in ['{"score": 5}', "[1, 2, 3]", '[{"score": "abc", "initials": "X"}]',
                        '[{"score": null, "initials": "X"}]', "", "not json at all"]:
            with self.subTest(content=content):
                self._write(content)
                self.assertEqual(lb.load_scores(), [])
                new_game()   # Game.__init__ loads the board
        self._write(b"\xff\xfe\x00\x81\x8d", "wb")
        self.assertEqual(lb.load_scores(), [])

    def test_one_bad_entry_does_not_wipe_the_rest(self):
        self._write(json.dumps([{"score": 900, "initials": "LIL"}, {"oops": 1},
                                {"score": 1200, "initials": "lhn"}]))
        self.assertEqual(lb.load_scores(), [(1200, "LHN"), (900, "LIL")])

    def test_hand_edited_file_is_sorted_and_trimmed(self):
        self._write(json.dumps([{"score": i, "initials": "TOOLONG"} for i in range(1, 9)]))
        scores = lb.load_scores()
        self.assertEqual([s for s, _ in scores], [8, 7, 6, 5, 4])
        self.assertTrue(all(len(i) == 3 for _, i in scores))

    def test_save_round_trip_and_no_temp_file_left(self):
        for s in (50, 300, 100, 20, 700, 10):
            lb.save_score(s, "abc")
        self.assertEqual(lb.load_scores(), [(700, "ABC"), (300, "ABC"), (100, "ABC"),
                                            (50, "ABC"), (20, "ABC")])
        self.assertEqual(os.listdir(_TMP), ["highscores.json"])
        self.assertFalse(lb.is_high_score(20))
        self.assertTrue(lb.is_high_score(21))

    def test_unwritable_folder_does_not_crash_the_game(self):
        good = lb._SCORES_FILE
        # A plain file where the save folder should be: it cannot be created or written
        with open(os.path.join(_TMP, "blocker"), "w") as f:
            f.write("x")
        lb._SCORES_FILE = os.path.join(_TMP, "blocker", "highscores.json")
        try:
            g = new_game()
            press(g, pygame.K_RETURN)
            g.player.score = 99
            g.player.lives = 0
            step(g, 2)
            press(g, pygame.K_RETURN)                 # game over -> initials
            self.assertEqual(g.state, STATE_ENTER_INITIALS)
            press(g, pygame.K_RETURN)                 # save (fails quietly)
            self.assertEqual(g.state, STATE_TITLE)
            self.assertEqual(g.lb_scores, [(99, "AAA")])   # still shown this session
        finally:
            lb._SCORES_FILE = good


    def test_scores_are_saved_per_user_not_in_the_code_folder(self):
        project = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.assertNotEqual(os.path.dirname(_REAL_SCORES_FILE), project)
        self.assertEqual(os.path.dirname(_REAL_LEGACY_FILE), project)

    def test_old_scores_carry_over_and_the_old_file_is_never_written(self):
        legacy = os.path.join(_TMP, "old_highscores.json")
        old = json.dumps([{"score": 1235, "initials": "LHN"}, {"score": 945, "initials": "LIL"}])
        with open(legacy, "w") as f:
            f.write(old)
        good_legacy = lb._LEGACY_FILE
        lb._SCORES_FILE = os.path.join(_TMP, "new_place", "highscores.json")   # folder not made yet
        lb._LEGACY_FILE = legacy
        try:
            self.assertEqual(lb.load_scores(), [(1235, "LHN"), (945, "LIL")])
            lb.save_score(1000, "NEW")
            self.assertEqual(lb.load_scores(), [(1235, "LHN"), (1000, "NEW"), (945, "LIL")])
            self.assertTrue(os.path.isfile(lb._SCORES_FILE))
            with open(legacy) as f:
                self.assertEqual(f.read(), old)
        finally:
            lb._SCORES_FILE = os.path.join(_TMP, "highscores.json")
            lb._LEGACY_FILE = good_legacy


class WorldEdgeTests(unittest.TestCase):
    def _walk_right(self, g, frames=500):
        g.player.invincible = 10 ** 6
        KEYS.down = {pygame.K_RIGHT}
        lowest = 0
        for _ in range(frames):
            step(g)
            lowest = max(lowest, g.player.y)
        return lowest

    def test_ollie_cannot_walk_off_the_right_end(self):
        for n in (2, 3):
            with self.subTest(level=n):
                g = new_game()
                jump_to_level(g, n)
                if n == 2:
                    g.level.bone_crate.collected = True   # don't end the level
                g.player.x = g.level.width - 300.0
                lowest = self._walk_right(g)
                self.assertEqual(g.player.x, g.level.width - OLLIE_SIZE[0])
                self.assertLessEqual(lowest, GROUND_Y - OLLIE_SIZE[1])   # never fell

    def test_level1_without_water_is_not_a_silent_dead_end(self):
        g = new_game()
        press(g, pygame.K_RETURN)
        g.level.slide_triggered = True            # got past the slide...
        g.player.x = 6300.0
        self._walk_right(g, 400)
        self.assertEqual(g.state, STATE_PLAYING)
        self.assertFalse(g.level.magic_carpet.active)
        self.assertLessEqual(g.player.x, g.level.width - OLLIE_SIZE[0])   # still on screen
        # ...and the level tells the player why nothing is here
        without = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        with_water = without.copy()
        g.level.draw_world(without)
        g.level.water_bottle.collected = True
        g.level.draw_world(with_water)
        self.assertNotEqual(pygame.image.tobytes(without, "RGB"),
                            pygame.image.tobytes(with_water, "RGB"))


class GameFlowTests(unittest.TestCase):
    def test_game_over_wins_over_a_same_frame_carpet_touch(self):
        g = new_game()
        press(g, pygame.K_RETURN)
        lv = g.level
        lv.magic_carpet.start()
        lv.slide_triggered = True
        g.has_water = True
        g.player.lives = 1
        g.player.x = lv.magic_carpet.x
        g.player.y = float(GROUND_Y - OLLIE_SIZE[1])
        lion = lv.ground_enemies[3]
        lion.spawn_x = lion.x = g.player.x        # lion and carpet both touching Ollie
        step(g)
        self.assertEqual(g.player.lives, 0)
        self.assertEqual(g.state, STATE_GAME_OVER)

    def test_pause_screen_sound_toggle_and_stray_keys(self):
        g = new_game()
        press(g, pygame.K_RETURN)
        press(g, pygame.K_p)
        self.assertEqual(g.state, STATE_PAUSED)
        before = g.sounds.enabled
        press(g, pygame.K_s)                      # "Tip: Press S to toggle sound"
        self.assertNotEqual(g.sounds.enabled, before)
        for key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_h, pygame.K_2):
            press(g, key)
        self.assertEqual(g.state, STATE_PAUSED)
        press(g, pygame.K_ESCAPE)
        self.assertEqual(g.state, STATE_PLAYING)

    def test_losing_window_focus_pauses_only_during_play(self):
        g = new_game()
        self.assertFalse(g._pause())
        self.assertEqual(g.state, STATE_TITLE)
        for n in (2, 3):
            g = new_game()
            jump_to_level(g, n)
            playing = g.state
            self.assertTrue(g._pause())
            self.assertEqual(g.state, STATE_PAUSED)
            press(g, pygame.K_p)
            self.assertEqual(g.state, playing)

    def test_restart_clears_leftover_popups_and_confetti(self):
        g = new_game()
        press(g, pygame.K_RETURN)
        g.ui.add_popup("old", 0, 0)
        g.ui.start_confetti()
        g.player.lives = 0
        step(g, 2)
        press(g, pygame.K_RETURN)
        self.assertEqual(g.state, STATE_PLAYING)
        self.assertEqual(g.ui.score_popups, [])
        self.assertFalse(g.ui.confetti_active)

    def test_hawk_exactly_on_ollie_does_not_divide_by_zero(self):
        g = new_game()
        press(g, pygame.K_RETURN)
        hawk = g.level.hawks[0]
        g.player.x, g.player.y = hawk.x, hawk.y
        hawk.update(g.player, g.level.platforms)

    def test_every_screen_runs_and_paints_the_whole_frame(self):
        """Walk the whole state machine; each screen must draw without errors and
        leave no part of the frame showing leftovers from the previous screen."""
        magenta = (255, 0, 255)
        g = new_game()

        def check(expected_state):
            self.assertEqual(g.state, expected_state)
            step(g, 3, draw=True)
            g.screen.fill(magenta)
            g._draw()
            for x in range(4, SCREEN_WIDTH, 61):
                for y in range(4, SCREEN_HEIGHT, 23):
                    if g.screen.get_at((x, y))[:3] == magenta:
                        self.fail(f"{g.state}: pixel ({x}, {y}) was never painted")

        check(STATE_TITLE)
        press(g, pygame.K_h); check(STATE_HOWTO)
        press(g, pygame.K_h); press(g, pygame.K_RETURN); check(STATE_PLAYING)
        press(g, pygame.K_p); check(STATE_PAUSED)
        press(g, pygame.K_p)
        g.player.lives = 0; step(g); check(STATE_GAME_OVER)
        g.player.score = 10
        press(g, pygame.K_RETURN); check(STATE_ENTER_INITIALS)
        press(g, pygame.K_ESCAPE); press(g, pygame.K_RETURN)
        g.state = STATE_TRAVELING; check(STATE_TRAVELING)
        g.travel_timer = TRAVEL_DURATION; step(g); check(STATE_HOME)
        press(g, pygame.K_RETURN); check(STATE_LEVEL2)
        g.player.invincible = 10 ** 6
        g.player.x = g.level.bone_crate.x
        step(g); check(STATE_BONE_CELEBRATE)
        g.bone_celebrate_timer = BONE_CELEBRATE_DURATION; step(g); check(STATE_LEVEL2_WIN)
        press(g, pygame.K_RETURN); check(STATE_ASCEND)
        g.ascend_timer = ASCEND_DURATION; step(g); check(STATE_LEVEL3)
        press(g, pygame.K_p); check(STATE_PAUSED)
        press(g, pygame.K_p)
        lives = g.player.lives
        g.player.x, g.player.y = g.level.throne.x + 20, 150.0
        step(g); check(STATE_HEAVEN_CELEBRATE)
        self.assertEqual(g.player.lives, lives + 1)
        g.heaven_celebrate_timer = HEAVEN_CELEBRATE_DURATION; step(g); check(STATE_HEAVEN_WIN)
        press(g, pygame.K_RETURN); check(STATE_ENTER_INITIALS)
        for key in (pygame.K_o, pygame.K_l, pygame.K_y, pygame.K_RETURN):
            press(g, key)
        self.assertEqual(g.state, STATE_TITLE)
        self.assertEqual(lb.load_scores()[0][1], "OLY")


class FrameRateTests(unittest.TestCase):
    """Game speed must not depend on how fast the screen draws."""

    def _steps(self, g, frame_ms, seconds):
        total, t = 0, 0.0
        while t < seconds * 1000:
            total += g._advance(frame_ms)
            t += frame_ms
        return total

    def test_normal_frames_run_exactly_one_step(self):
        g = new_game()
        self.assertEqual([g._advance(ms) for ms in (16, 17, 17, 16, 18, 15)], [1] * 6)

    def test_slow_drawing_still_runs_sixty_steps_a_second(self):
        for frame_ms in (33.3, 50, 80):          # 30, 20 and 12.5 fps
            with self.subTest(frame_ms=frame_ms):
                self.assertAlmostEqual(self._steps(new_game(), frame_ms, 2), 120, delta=3)

    def test_a_long_stall_does_not_fast_forward_the_game(self):
        g = new_game()
        self.assertEqual(g._advance(5000), MAX_CATCHUP_STEPS)
        self.assertEqual(g._advance(16), 1)

    def test_cutscene_takes_the_same_real_time_at_20_fps(self):
        g = new_game()
        jump_to_level(g, 2)
        g.state = STATE_LEVEL2_WIN
        press(g, pygame.K_RETURN)
        elapsed = 0
        while g.state == STATE_ASCEND and elapsed < 20000:
            g._advance(50)
            elapsed += 50
        self.assertEqual(g.state, STATE_LEVEL3)
        self.assertAlmostEqual(elapsed, ASCEND_DURATION * 1000 / FPS, delta=100)

    def test_ollie_covers_the_same_ground_at_60_and_20_fps(self):
        distances = []
        for frame_ms in (1000 / 60, 50):
            g = new_game()
            press(g, pygame.K_RETURN)
            g.player.invincible = 10 ** 6
            g._advance(1000 / 60)                # settle on the ground
            start = g.player.x
            KEYS.down = {pygame.K_RIGHT}
            self._steps(g, frame_ms, 1)
            distances.append(g.player.x - start)
        self.assertAlmostEqual(distances[0], PLAYER_SPEED * FPS, delta=PLAYER_SPEED * 2)
        self.assertAlmostEqual(distances[0], distances[1], delta=PLAYER_SPEED * 3)


class _FakePad:
    """Minimal joystick: one stick, one d-pad, ten buttons."""
    def __init__(self):
        self.axis, self.hat, self.buttons = 0.0, (0, 0), set()

    def get_numaxes(self):
        return 2

    def get_numhats(self):
        return 1

    def get_numbuttons(self):
        return 10

    def get_axis(self, i):
        return self.axis if i == 0 else 0.0

    def get_hat(self, i):
        return self.hat

    def get_button(self, b):
        return b in self.buttons


class GamepadTests(unittest.TestCase):
    def _pad_press(self, g, button):
        g._handle_event(g._pad_event(pygame.event.Event(pygame.JOYBUTTONDOWN, button=button)))

    def test_stick_walks_and_button_jumps(self):
        g = new_game()
        pad = _FakePad()
        g._pads[1] = pad
        self._pad_press(g, PAD_JUMP_BUTTONS[0])           # confirm on the title screen
        self.assertEqual(g.state, STATE_PLAYING)
        step(g, 3)
        x0 = g.player.x
        pad.axis = 0.2                                    # stick drift inside the dead zone
        step(g, 10)
        self.assertEqual(g.player.x, x0)
        pad.axis = 1.0
        step(g, 10)
        self.assertEqual(g.player.x, x0 + 10 * PLAYER_SPEED)
        pad.axis, pad.hat = 0.0, (-1, 0)                  # d-pad left
        step(g, 5)
        self.assertEqual(g.player.x, x0 + 5 * PLAYER_SPEED)
        pad.hat = (0, 0)
        pad.buttons = {PAD_JUMP_BUTTONS[0]}
        step(g, 2)
        self.assertLess(g.player.vy, 0)

    def test_start_button_pauses_and_unplugging_pauses(self):
        g = new_game()
        g._pads[7] = _FakePad()
        press(g, pygame.K_RETURN)
        self._pad_press(g, PAD_PAUSE_BUTTONS[1])
        self.assertEqual(g.state, STATE_PAUSED)
        self._pad_press(g, PAD_PAUSE_BUTTONS[1])
        self.assertEqual(g.state, STATE_PLAYING)
        g._pad_event(pygame.event.Event(pygame.JOYDEVICEREMOVED, instance_id=7))
        self.assertEqual(g.state, STATE_PAUSED)
        self.assertEqual(g._pads, {})
        step(g, 3)                                        # no pad left: must not raise

    def test_dpad_enters_initials(self):
        g = new_game()
        press(g, pygame.K_RETURN)
        g.player.score, g.player.lives = 50, 0
        step(g, 2)
        self._pad_press(g, 0)                             # game over -> initials
        self.assertEqual(g.state, STATE_ENTER_INITIALS)
        for value in ((0, 1), (0, 0), (1, 0), (0, -1)):   # up, release, right, down
            g._handle_event(g._pad_event(pygame.event.Event(pygame.JOYHATMOTION, value=value)))
        self.assertEqual("".join(g.initials), "BZA")
        self._pad_press(g, 0)
        self.assertIn((50, "BZA"), lb.load_scores())


class SoundAndTextTests(unittest.TestCase):
    def test_volume_keys_step_and_clamp(self):
        g = new_game()
        self.assertEqual(g.sounds.volume, VOLUME_DEFAULT)
        press(g, pygame.K_EQUALS)                         # already at the top
        self.assertEqual(g.sounds.volume, 1.0)
        for _ in range(3):
            press(g, pygame.K_MINUS)
        self.assertAlmostEqual(g.sounds.volume, 0.7)
        self.assertTrue(all(abs(s.get_volume() - 0.7) < 0.02 for s in g.sounds._sounds.values()))
        self.assertIn("70%", g.sounds.status_text())
        for _ in range(20):
            press(g, pygame.K_KP_MINUS)
        self.assertEqual(g.sounds.volume, 0.0)
        press(g, pygame.K_RETURN)
        press(g, pygame.K_EQUALS)                         # not a volume key during play
        self.assertEqual(g.sounds.volume, 0.0)
        press(g, pygame.K_p)
        press(g, pygame.K_PLUS)
        self.assertAlmostEqual(g.sounds.volume, 0.1)

    def test_no_audio_device_is_reported_not_faked(self):
        import sounds

        def broken(self):
            raise pygame.error("no audio device")

        real = sounds.SoundManager._build_all
        sounds.SoundManager._build_all = broken
        try:
            mgr = sounds.SoundManager()
        finally:
            sounds.SoundManager._build_all = real
        self.assertFalse(mgr.enabled)
        mgr.toggle()
        self.assertFalse(mgr.enabled)                     # cannot be switched "ON" while silent
        self.assertIn("not available", mgr.status_text())
        mgr.change_volume(-1)
        mgr.play_jump()                                   # all still safe to call

    def test_score_popups_fade_out(self):
        g = new_game()

        def brightest(timer):
            g.ui.score_popups = [["+25 Bird!", 300, 300, timer, (255, 255, 255)]]
            g.screen.fill((0, 0, 0))
            g.ui.draw_popups(0)
            return max(g.screen.get_at((x, y))[0] for x in range(250, 350, 2)
                       for y in range(298, 325, 2))

        self.assertGreater(brightest(90), 200)
        self.assertLess(brightest(20), brightest(90) // 2)
        self.assertLess(brightest(2), 20)

    def test_hot_slide_popup_matches_what_happened(self):
        for invincible, lives_lost, word in ((0, 1, "Ouch"), (60, 0, "Hot")):
            with self.subTest(invincible=invincible):
                g = new_game()
                press(g, pygame.K_RETURN)
                g.player.invincible = invincible
                g.player.x = g.level.slide_rect.x - 2.0
                KEYS.down = {pygame.K_RIGHT}
                step(g, 2)
                self.assertEqual(3 - g.player.lives, lives_lost)
                self.assertTrue(any(word in p[0] for p in g.ui.score_popups))
                self.assertFalse(lives_lost == 0 and any("Ouch" in p[0] for p in g.ui.score_popups))

    def test_text_fits_and_draws_without_arial(self):
        import constants
        real = constants.FONT_FAMILIES
        constants.FONT_FAMILIES = "no-such-font-installed"
        art.font.cache_clear()
        try:
            wide = "A very long label that would never fit in a small panel"
            self.assertLessEqual(art.fit_text(wide, 28, True, (0, 0, 0), 200).get_width(), 200)
            self.assertGreater(art.font(18).render("Ollie", True, (0, 0, 0)).get_width(), 10)
            g = new_game()                                # builds every UI font from the fallback
            for key in (None, pygame.K_h, pygame.K_h, pygame.K_RETURN, pygame.K_p):
                if key is not None:
                    press(g, key)
                step(g, 2, draw=True)
            self.assertEqual(g.state, STATE_PAUSED)
        finally:
            constants.FONT_FAMILIES = real
            art.font.cache_clear()

    def test_smallest_text_sizes(self):
        self.assertGreaterEqual(FONT_SIZE_XS, 16)
        self.assertGreaterEqual(FONT_SIZE_LABEL, 14)
        g = new_game()
        self.assertGreaterEqual(g.ui.font_xs.get_height(), art.font(16).get_height())


class RenderingTests(unittest.TestCase):
    def test_level3_pause_does_not_darken_the_bottom_of_the_screen(self):
        g = new_game()
        jump_to_level(g, 3)
        step(g, 5, draw=True)
        before = g.screen.get_at((640, 700))[:3]
        press(g, pygame.K_p)
        step(g, 60, draw=True)
        press(g, pygame.K_p)
        step(g, 5, draw=True)
        self.assertEqual(g.screen.get_at((640, 700))[:3], before)

    def test_ascend_cutscene_does_not_build_a_new_sky_every_frame(self):
        """The original built and cached a full-screen gradient and a huge glow per
        frame (~5 fps and hundreds of MB).  The caches must stay flat."""
        g = new_game()
        jump_to_level(g, 2)
        g.state = STATE_LEVEL2_WIN
        press(g, pygame.K_RETURN)
        step(g, 5, draw=True)
        grads = art.vgradient.cache_info().currsize
        glows = art.radial_glow.cache_info().currsize
        step(g, ASCEND_DURATION - 10, draw=True)
        self.assertEqual(g.state, STATE_ASCEND)
        self.assertEqual(art.vgradient.cache_info().currsize, grads)
        self.assertEqual(art.radial_glow.cache_info().currsize, glows)

    def test_window_scaling_fits_the_whole_picture(self):
        g = new_game()
        g.screen.fill((10, 200, 30))
        # Same size: straight copy
        same = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        g._present(same)
        self.assertEqual(same.get_at((0, 0))[:3], (10, 200, 30))
        # Smaller 4:3 window: full width used, black bars above and below
        small = pygame.Surface((640, 480))
        g._present(small)
        self.assertEqual(small.get_at((2, 240))[:3], (10, 200, 30))
        self.assertEqual(small.get_at((637, 240))[:3], (10, 200, 30))
        self.assertEqual(small.get_at((320, 10))[:3], (0, 0, 0))
        self.assertEqual(small.get_at((320, 470))[:3], (0, 0, 0))
        # Bigger window: picture grows to fill the height
        big = pygame.Surface((2560, 1440))
        g._present(big)
        self.assertEqual(big.get_at((5, 5))[:3], (10, 200, 30))
        self.assertEqual(big.get_at((2554, 1434))[:3], (10, 200, 30))
        # Degenerate (minimised) window must not raise
        g._present(pygame.Surface((1, 1)))


if __name__ == "__main__":
    unittest.main()
