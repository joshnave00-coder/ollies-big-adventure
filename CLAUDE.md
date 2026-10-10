# CLAUDE.md — Ollie's Big Adventure

Reference file for Claude Code. Read this before touching any file in this project.
It answers "where does X live?", "how does Y work?", and "what must I not break?"

---

## Project at a Glance

| Item | Value |
|------|-------|
| Language | Python 3.10+ |
| Framework | Pygame 2.x |
| Window | 1280 × 720, 60 FPS |
| Entry point | `main.py` |
| Current version | 0.8.1 |
| Level 1 width | 7 000 px (outdoor scrolling level) |
| Level 2 width | 8 000 px (interior house level) |
| Level 3 width | 8 000 px (sky / Heaven scrolling level) |
| Art style | Hybrid: CC0 stock art for environment + human NPCs (`char/`); Ollie & all animals/heavenly beings stay procedural |
| Audio | Programmatic synthesis via `sounds.py`; no audio files |

---

## File Map — What Lives Where

```
main.py          Pygame init, window, icon, Game instantiation
game.py          Game class — state machine + event router
player.py        Player class (Ollie) + draw_ollie_sprite() helper
characters.py    Level 1 NPC classes: Camper, DogCatcher, Bird, Hawk,
                   GroundEnemy, FriendlyGirl, WaterBottle, MagicCarpet, Angel
level.py         Level 1 — world layout, camera, background, NPC instances
level2.py        Level 2 — interior house; HouseCat, Roomba, BoneCrate, Level2
level3.py        Level 3 — sky/Heaven; Coin, CloudSpirit, SingingAngel, GodThrone, Level3
ui.py            UI class — HUD, popups, pause overlay, all non-gameplay screens
art.py           Rendering toolkit: aadraw AA primitives, CC0 image loader/cache,
                   sprite()/blit_sprite() (stock NPC sprites), panel() (illustrated
                   furniture), gradients, soft shadows, tint/tile helpers
leaderboard.py   High-score persistence (highscores.json, top 5 entries)
sounds.py        SoundManager — all sounds synthesised at runtime, no audio files
constants.py     Every magic number and string in the project
tests/           Headless regression tests — run: python -m unittest discover -s tests
requirements.txt pygame>=2.1,<3
assets/img/      CC0 Kenney art: ground/ sky/ foliage/ pattern/ char/ (human NPC poses)
assets/sounds/   Reserved for future .wav/.ogg files
assets/CREDITS.txt  CC0 attribution for the bundled art packs
```

**One rule:** all numeric constants (colors, sizes, speeds, radii) belong in `constants.py`.
Never hard-code them inside other files.

**Rendering rule (since 0.6):** for any *character/furniture* shape, draw through
`aadraw` (imported from `art.py`) instead of `pygame.draw` — it is a drop-in with the same
signatures but anti-aliased circle/ellipse/polygon/line/lines (rects stay crisp). Load stock
environment art with `art.image / scaled / scaled_h / tinted` (all cached); never
`pygame.image.load` directly in a draw method. **Human NPCs** (Dog Catcher, Campers, Lily/Leia,
and the homecoming family) blit CC0 `char/` poses via `art.blit_sprite(surf, rel, cx, feet_y, h,
flip=...)` — it auto-adds a contact shadow. **Ollie and every animal/creature/heavenly being**
(lion, hawk, bird, house cat, Roomba, angel, carpet, Cloud Spirit, Singing Angel, God's throne)
stay 100% procedural so the heart of the game is the family's own.
Furniture uses `art.panel(rect, color, radius=...)` for a rounded, gradient-shaded, drop-shadowed
look. `art.ground_shadow(...)` adds the soft contact shadow under procedural ground sprites.

**Font rule:** never call `pygame.font.SysFont()` directly inside a `draw()` method.
Each module that needs fonts has a module-level `_font(name, size, bold)` helper decorated
with `@functools.lru_cache(maxsize=None)`.  `UI.__init__` also pre-creates the six common
sizes (`font_lg`, `font_md`, `font_sm`, `font_xs`, `font_xl`) for use in all screen methods.

---

## Architecture

```
Game
 ├─ Player          (player.py)
 ├─ Level / Level2  (level.py / level2.py) — owns all NPC instances except Angel
 │    Level 1
 │    ├─ Camper × 3
 │    ├─ DogCatcher × 4
 │    ├─ Bird × 12
 │    ├─ Hawk × 4
 │    ├─ GroundEnemy × 4  (Lion × 4)
 │    ├─ FriendlyGirl × 4 (Lily × 2 + Leia × 2)
 │    ├─ WaterBottle × 1
 │    └─ MagicCarpet × 1
 │    Level 2
 │    ├─ HouseCat × 9   (level2.py — not NPC subclass; same interface)
 │    ├─ Roomba × 3     (level2.py)
 │    └─ BoneCrate × 1  (level2.py)
 │    Level 3            (level3.py — standalone classes, same interface as NPC)
 │    ├─ Coin × 32       (money pickup; reuses the ("score", …) event)
 │    ├─ CloudSpirit × 9 (the floaty "weird people" obstacles)
 │    ├─ SingingAngel × 5 (friendly greeters — emit no events)
 │    └─ GodThrone × 1   (level goal; emits ("reached_god",))
 ├─ Angel           (characters.py) — owned by Game, not Level
 ├─ UI              (ui.py)
 ├─ SoundManager    (sounds.py)
 └─ lb (leaderboard) (leaderboard.py) — loaded at startup, saved on high score
```

### Event Bus (critical pattern)

`Level.update()` appends tuples to `self.events` each frame. `Game._update()` reads them.
**Never have Level import Game or Player directly** — communication is one-way via this list.

| Tuple | Meaning |
|-------|---------|
| `("score", pts: int, label: str)` | Award points, maybe trigger Angel, show popup |
| `("life_damage",)` | Enemy contact — call `player.lose_life()` (−1 life, respects invincibility) |
| `("damage", amount: int)` | HP-based hazard — call `player.take_damage(amount)` (slide only) |
| `("hearts",)` | Camper pet — call `player.add_hearts()` (10 pink particles above Ollie) |
| `("alert",)` | Set player animation to "alert" for 20 frames (shows "!" above Ollie) |
| `("water",)` | Set `game.has_water = True`; call `level.magic_carpet.start()` |
| `("slide",)` | Damage if no water, wag if water |
| `("found_crate",)` | Level 2 goal — award SCORE_BONE, trigger bone celebration |
| `("reached_god",)` | Level 3 goal — award SCORE_HEAVEN, full heal +1 life, trigger heaven celebration |

Coins (Level 3 "money") reuse the existing `("score", SCORE_COIN, "Coin!")` tuple — the
`"Coin!"` label routes to `play_coin()` in `Game._process_event()`.

To add a new game event: emit a new tuple from `Level.update()` and handle it in
`Game._process_event()`. Do not bypass this pattern.

---

## State Machine

States are strings defined in `constants.py`:

```
STATE_TITLE          "title"          Title screen — no update logic runs
STATE_HOWTO          "howto"          Kid-friendly How-to-Play screen — no update logic runs
STATE_PLAYING        "playing"        Level 1 normal gameplay
STATE_PAUSED         "paused"         Pause overlay — no update logic runs
STATE_CARPET         "carpet"         End-of-level carpet sequence (Ollie locked to carpet)
STATE_TRAVELING      "traveling"      Black-screen transition between Level 1 and home screen
STATE_HOME           "home"           Home celebration screen
STATE_GAME_OVER      "game_over"      Overlay — no update logic runs
STATE_ENTER_INITIALS "enter_initials" High-score initials entry — no update logic runs
STATE_LEVEL2         "level2"         Level 2 normal gameplay
STATE_BONE_CELEBRATE "bone_celebrate" Level 2 bone-found celebration cutscene
STATE_LEVEL2_WIN     "level2_win"     Level 2 win screen
STATE_SLIDE          "slide"          Defined; slide sequence handled inline in game.py
STATE_ASCEND         "ascend"         Carpet rises through clouds (Level 2 → Level 3 intro)
STATE_LEVEL3         "level3"         Level 3 (Heaven) normal gameplay
STATE_HEAVEN_CELEBRATE "heaven_celebrate" Touch-God cutscene (healing + feast)
STATE_HEAVEN_WIN     "heaven_win"     "Ollie's Home in Heaven" ending screen
```

Transitions:
```
title ──Enter/Space──► playing
title ──H/I──► howto ──Space/Enter/Esc/H──► title   (S toggles sound in either)
playing ──P/Esc──► paused ──P/Esc──► playing
playing ──lives==0──► game_over
playing ──carpet contact──► carpet
carpet ──carpet off-screen──► traveling
traveling ──timer done──► home     (awards lives bonus)
home ──Enter──► level2             (calls _init_level2())
game_over ──Enter──► enter_initials (if high score) or playing (calls _init_game())
enter_initials ──Enter──► title    (saves score, calls _init_game())
level2 ──lives==0──► game_over
level2 ──found_crate──► bone_celebrate
bone_celebrate ──timer done──► level2_win
level2_win ──Enter──► ascend                       (carpet flies up to Heaven)
ascend ──timer done──► level3                      (calls _init_level3())
level3 ──lives==0──► game_over
level3 ──reached_god──► heaven_celebrate
heaven_celebrate ──timer done──► heaven_win
heaven_win ──Enter──► enter_initials (if high score) or title (calls _init_game())
```

`Game._init_game()` fully resets Player, Level, Angel, and all flags. Call it on every restart.
`Game._init_level2()` / `_init_level3()` preserve score/lives but reset level state. Call them at
each level transition (never `_init_game()`).  Level 3 is the new finale: it now owns the
high-score/initials hand-off that Level 2 used to.

**Title test shortcuts:** press `2` ×5 (within ~1.5 s) jumps straight to Level 2; press `3` ×5
jumps to Level 3 — handy for showing off a level without replaying the earlier ones.

---

## Player (player.py)

### Key attributes
| Attribute | Type | Purpose |
|-----------|------|---------|
| `x, y` | float | World position (top-left of sprite) |
| `vx, vy` | float | Velocity |
| `on_ground` | bool | True when standing on a platform |
| `facing` | int | 1=right, −1=left |
| `health` | int | 0–100 (slide hazard only; enemies use lives) |
| `lives` | int | Starts at 3; reaches 0 = Game Over |
| `score` | int | Accumulates all game points |
| `jumped_this_frame` | bool | True for one frame when jump fires; read by game.py for sound |
| `invincible` | int | Frames remaining; >0 = immune + red flash blink |
| `anim_state` | str | idle / run / jump / wag / sad / alert / slide / celebrate |
| `anim_timer` | int | Counts down; when 0, base state takes over |
| `particles` | list | Sparkle particles from `add_sparkles()` |

Note: `has_water` is stored on `Game`, not Player.

### Damage methods
- `lose_life()` — enemy contact path; decrements `lives` by 1, sets `invincible = INVINCIBLE_FRAMES` (120), returns `False` if already invincible.
- `take_damage(amount)` — HP-path (slide hazard); decrements `health`, also loses a life when HP reaches 0.

### Collision model
`move_and_collide()` does two AABB passes — X first, then Y — against the `platforms` list
(list of `pygame.Rect`). The ground and elevated platforms are all in `level.platforms`.
Platforms are static; NPCs do not use them for their own physics.

### Drawing
`Player.draw(surf, cam_x)` — pass the surface and `level.camera_x`.
Screen x = `self.x - cam_x`. All drawing is in `_draw_ollie()` → `draw_ollie_sprite()`.

### Adding a new animation state
1. Set it with `player.set_anim("mystate", duration_frames)`.
2. Add a visual branch inside `draw_ollie_sprite()` under `# State overlays`.
3. The state auto-reverts to idle/run/jump when `anim_timer` reaches 0.

---

## NPC Base Class (characters.py — `NPC`)

All Level 1 NPCs inherit from `NPC(x, y, w, h)`:
- `self.rect` → `pygame.Rect` (computed from x/y/w/h)
- `self.frame` → increments every update (use for animation)
- `self.active` → set False to hide/disable
- `update(player, platforms)` → return a string event or None
- `draw(surf, cam_x)` → screen x = `self.x - cam_x`

Level 2 classes (`HouseCat`, `Roomba`, `BoneCrate`) implement the same interface but do
not subclass `NPC` — they are standalone classes in `level2.py`.

**Do not call `player.lose_life()` or `player.take_damage()` inside an NPC.** Return a string
event; `Level` emits the tuple; `Game` applies the damage. NPCs stay stateless w.r.t. Player.

### Enemy respawn
All enemy classes (`DogCatcher`, `Hawk`, `GroundEnemy`, `HouseCat`, `Roomba`) store `spawn_x`
and reset when `abs(player.x - self.spawn_x) > ENEMY_RESPAWN_DIST` (900 px).

### Adding a new NPC
1. Subclass `NPC` in `characters.py`.
2. Add a size constant to `constants.py`.
3. Instantiate in `Level.__init__()`.
4. Call `.update()` and `.draw()` in `Level.update()` / `Level.draw_characters()`.
5. Emit appropriate event tuples; handle in `Game._process_event()` if needed.

---

## Level (level.py)

### Platform layout
`self.platforms` is a flat list of `pygame.Rect`. The first entry is always the single
continuous ground platform — no gaps. Elevated platforms start at x=300.

Key y-values:
- `GROUND_Y = 580` — top of the ground surface
- Platforms range from y=350 to y=490
- Ollie spawns at `y = GROUND_Y - OLLIE_SIZE[1]` = 532

### Camera
```python
level.update_camera(player_x)
```
Smooth lerp: `camera_x += (target - camera_x) * 0.12`
`target = player_x - SCROLL_THRESH` (SCROLL_THRESH = 400)
Clamped to `[0, level.width - SCREEN_WIDTH]`.
All drawing uses `sx = world_x - camera_x`.

### Background drawing order (draw_background → draw_world)
1. Sky gradient fill
2. Sun + rotating rays
3. Distant hills (parallax 0.2×)
4. Mid hills (parallax 0.5×)
5. Clouds (parallax 0.1×)
6. Ground rect (DARK_GREEN fill + GRASS_GREEN top strip)
7. Trees (parallax 1:1)
8. Elevated platforms
9. Hot slide illustration
10. Walk-right beginner hint (first 5 s, `start_hint_timer`)

### Character world positions (approximate x)
| Character | World x | Notes |
|-----------|---------|-------|
| Campers | 500, 2600, 4800 | At GROUND_Y; 3 total |
| Dog Catchers | 900, 2100, 3600, 5200 | Patrol ranges span ~350 px each |
| Lily | 1600, 4200 | `self.friendly_girls[0]` and `[1]` |
| Leia | 3100, 5600 | `self.friendly_girls[2]` and `[3]` |
| Water Bottle | 5700 | At GROUND_Y − 32 |
| Slide zone | 6000–6200 | Rect y = GROUND_Y − 160, h = 160 |
| Magic Carpet | 6400 | At GROUND_Y − CARPET_SIZE[1] − 10 |
| Hawks | 1400, 2800, 4200, 5600 | y ≈ 180–220 (airborne) |

---

## Level 2 (level2.py)

Eight rooms across 8 000 px. All rooms share a continuous ground platform.
Level 2 starts from `_init_level2()` in `game.py` — Ollie keeps score and lives from Level 1.
Furniture is drawn in `Level2._draw_room_details`; behind-the-furniture dressing (wainscoting,
rugs, light pools, plants) in `_draw_room_decor`. **Platforms are the visible tops of furniture**
(11 total + ground) — `draw_world` only adds a faint highlight lip so the standable edge reads;
the furniture itself is drawn in the background pass.

| Room | x range | Enemies |
|------|---------|---------|
| Entry Hall | 0–1 000 | 1 HouseCat |
| Living Room | 1 000–2 200 | 1 HouseCat, 1 Roomba |
| Hallway | 2 200–2 800 | 1 HouseCat |
| Kitchen | 2 800–4 000 | 1 HouseCat |
| Dining Room | 4 000–5 000 | 1 HouseCat, 1 Roomba |
| Play Room | 5 000–6 400 | 1 HouseCat |
| Corridor | 6 400–7 000 | 1 HouseCat, 1 Roomba |
| Master Bedroom | 7 000–8 000 | 2 HouseCats + BoneCrate at x=7880 |

**Enemy chase logic** (HouseCat, Roomba, DogCatcher, GroundEnemy): all use a small **dead-zone**
(~12 px) so they stop rather than flip-flopping when standing directly under Ollie. Speeds live in
`constants.py` and stay well below `PLAYER_SPEED`.

---

## Level 3 — Heaven (level3.py)

8 000 px sky level. Born from a 7-year-old's wish: *Ollie rides the magic carpet up to heaven,
passes the weird people, collects as much money as he can, climbs the stairs to the singing angels,
touches God on a flying throne, has no more pain and all the food he wants, and gets a home in
heaven.* Reached via `STATE_ASCEND` after the Level 2 win; `_init_level3()` keeps score/lives.

Standalone classes (same interface as `NPC`, not subclasses):

| Class | Role | `update()` returns |
|-------|------|--------------------|
| `Coin` | Money pickup, spins + bobs | `"coin"` on overlap → Level3 emits `("score", SCORE_COIN, "Coin!")` |
| `CloudSpirit` | The floaty "weird people"; patrol + dead-zone chase + vertical drift | `"life_damage"` / `"alert"` |
| `SingingAngel` | Friendly greeter at the gates; floating notes, sings faster when Ollie is near | always `None` (no gameplay events) |
| `GodThrone` | The goal — radiant figure on a floating golden throne | `"reached_god"` on overlap |

| Section | x range | Contents |
|---------|---------|----------|
| Cloud Landing | 0–1 300 | warm-up hop-clouds, "Welcome to Heaven" sign |
| Spirit Gauntlet | 1 300–4 600 | 7 Cloud Spirits + showers of coins on hop-clouds |
| Great Staircase | 4 600–6 500 | ascending cloud steps climbing skyward + 2 spirits |
| Pearly Gates | 6 500–7 400 | 5 Singing Angels on the high landing |
| God's Throne | 7 400–8 000 | the flying throne on a high cloud (x≈7 470, y≈50) |

- **`platforms[0]` is a single continuous cloud floor** at `GROUND_Y` — same no-gaps rule as the
  other levels. The throne sits high up so Ollie must climb the staircase to reach it (he can't
  touch it from the floor). All elevated platforms are drawn as fluffy cloud ledges by `_cloud(...)`.
- CloudSpirit/throne speeds & radii live in `constants.py`; spirits stay below `PLAYER_SPEED`.
- The big radiant glow / god-rays in `draw_background` are presentation only. `GodThrone.rect`
  is just the lower half of the throne so Ollie reaches it by walking in from the landing.

---

## UI (ui.py)

### HUD elements (`draw_hud(player, has_water, level_width=LEVEL_WIDTH, goal_label="Home")`)
- Health bar: x=14, y=10, 180 px wide. Color: green >40 HP, yellow >20 HP, red ≤20 HP.
- Lives: paw icons at x=204 + i×26, y=20.
- Score: centered at top.
- Level progress bar: centered, y=46, 360 px wide, pink fill, "{goal_label} →" label. Pass
  `level_width=self.level.width` and `goal_label=self._goal_label()` from `game._draw()` so the
  bar scales to each level's width and reads "Home →" (L1), "Bone →" (L2), "Heaven →" (L3).
- Water indicator: top-right, only shown when `has_water=True`.

### Level 3 screens
- `draw_ascend_screen(timer)` — Ollie on the carpet rising as clouds rush downward; sky brightens
  to gold over `ASCEND_DURATION`; uses `self.ascend_trail`.
- `draw_heaven_celebrate(player, timer, cam_x)` — touch-God cutscene: golden light, healing hearts,
  then a ring of feast food (`_draw_food`), with "No more pain" → "Eat all you want!" banners.
- `draw_heaven_win(score, timer)` — the ending: Ollie + his `_draw_cloud_house`, flanking angels,
  confetti, "Ollie's Home in Heaven!" banner, final score, ENTER-to-finish prompt.

### How-to-Play screen (`draw_howto(frame, sound_on)`)
Kid-facing instructions, reached from the title with **H**. Reuses the real character/item
sprites as labelled icons via `_howto_icons()` (lazily built, cached) and `_howto_icon(...)`.
No gameplay runs in `STATE_HOWTO`. Keep it presentation-only.

### Score popups
`ui.add_popup(text, world_x, world_y, color)` — world coordinates.
`ui.draw_popups(cam_x)` converts to screen. Popups rise 1.2 px/frame and fade over 90 frames.

### Pause overlay
`ui.draw_pause()` — draws a semi-transparent panel with "PAUSED" and resume instructions.
Called from `game._draw()` when `state == STATE_PAUSED`.

### Confetti system
`ui.start_confetti()` spawns 200 pieces. `update_confetti()` moves them; pieces loop when
they fall off the bottom. Called from `Game._update()` at celebration milestones.

### Adding a new screen
Add a `draw_myscreen(...)` method to `UI`. Call it from `Game._draw()` under the appropriate
state branch. Never put game logic inside UI methods.

---

## Sounds (sounds.py)

`SoundManager` synthesises all sounds at startup. No external audio files needed.
Available sounds: `play_jump`, `play_score`, `play_treat`, `play_bird`, `play_enemy_hit`,
`play_angel`, `play_water`, `play_slide`, `play_carpet`, `play_fanfare`, `play_game_over`,
`play_coin` (Level 3 money), `play_heaven` (choir chord when Ollie touches God).

To add a sound:
1. Add a `_build(...)` entry in `SoundManager._build_all()` using the existing generator helpers.
2. Add a `play_mysound(self)` method that calls `self._play('key')`.
3. Call it from `game.py` at the appropriate event.

Toggle mute: `sounds.toggle()` or press S on the title screen.

---

## Leaderboard (leaderboard.py)

Persists top 5 scores to `highscores.json` next to the .py files.
- `lb.load_scores()` → `[(score, initials), ...]` sorted descending
- `lb.save_score(score, initials)` → updated list
- `lb.is_high_score(score)` → bool

Scores are saved after entering initials in `STATE_ENTER_INITIALS`.

---

## Constants Quick Reference

```python
# Physics
GRAVITY = 0.6           JUMP_POWER = -14       PLAYER_SPEED = 4
SCROLL_THRESH = 400

# World
LEVEL_WIDTH = 7000      LEVEL2_WIDTH = 8000    LEVEL3_WIDTH = 8000
GROUND_Y = 580          PLATFORM_THICK = 20

# Health / damage
MAX_HEALTH = 100        ENEMY_DAMAGE = 25      SLIDE_DAMAGE = 30
# Note: ENEMY_DAMAGE is unused by enemy contact (they use "life_damage" event).

# Scoring
SCORE_PET = 10          SCORE_TREAT = 15
SCORE_LILY_TREAT = 20   SCORE_LEIA_TREAT = 20  SCORE_BIRD = 25
SCORE_LIVES_BONUS = 100                         # pts per remaining life at Level 1 end
SCORE_BONE = 500                                # big bone in Level 2
SCORE_COIN = 25         SCORE_HEAVEN = 1000     # Level 3 money & reaching God

# Level 3 timing (frames)
ASCEND_DURATION = 200   HEAVEN_CELEBRATE_DURATION = 360

# Detection radii
PET_RADIUS = 80         ENEMY_ALERT_RAD = 150
BIRD_FLEE_RAD = 120     BIRD_CATCH_RAD = 40    LILY_GIVE_RAD = 100

# Angel timings (frames)
ANGEL_DESCEND_FRAMES = 90   ANGEL_GLOW_FRAMES = 120   ANGEL_ASCEND_FRAMES = 60
ANGEL_CHANCE = 4                                # 1-in-4 scoring events
INVINCIBLE_FRAMES = 120                         # 2 s post-hit immunity
ENEMY_RESPAWN_DIST = 900                        # px from spawn → enemy resets

# Enemy speeds (all chase speeds < PLAYER_SPEED = 4 — do not raise above player)
CATCHER_PATROL_SPD=1.0  CATCHER_CHASE_SPD=1.6
HAWK_PATROL_SPD=0.9     HAWK_CHASE_SPD=1.4     HAWK_CHASE_RAD=180
LION_PATROL_SPD=0.7     LION_CHASE_SPD=1.2     BEAST_CHASE_RAD=180
CAT_PATROL_SPD=0.8      CAT_CHASE_SPD=1.1      CAT_CHASE_RAD=160
ROOMBA_PATROL_SPD=1.0   ROOMBA_CHASE_SPD=1.3   ROOMBA_CHASE_RAD=200
SPIRIT_PATROL_SPD=0.8   SPIRIT_CHASE_SPD=1.1   SPIRIT_CHASE_RAD=170

# Sprite sizes (w, h)
OLLIE_SIZE = (48, 48)    CAMPER_SIZE = (36, 52)   CATCHER_SIZE = (36, 56)
BIRD_SIZE = (28, 20)     HAWK_SIZE = (38, 24)
LION_SIZE = (54, 40)
LILY_SIZE = (30, 52)     LEIA_SIZE = (30, 52)
ANGEL_SIZE = (44, 56)    CARPET_SIZE = (90, 30)
CAT_SIZE = (40, 30)      CRATE_SIZE = (64, 48)    ROOMBA_SIZE = (50, 18)
SPIRIT_SIZE = (44, 58)   COIN_SIZE = (26, 26)
SING_ANGEL_SIZE = (46, 70)   THRONE_SIZE = (132, 150)
```

---

## How to Add / Change Things Safely

### Add a new enemy type
1. Add size constant to `constants.py`.
2. Subclass `NPC` in `characters.py` (or add standalone class in `level2.py` for Level 2):
   - Store `self.spawn_x`, `self.spawn_y` in `__init__`.
   - Add `_respawn_if_far(player)` following the pattern in `DogCatcher`.
   - `update()` returns `"life_damage"`, `"alert"`, or `None`.
3. Instantiate in `Level.__init__()` and add to a list.
4. Call `update()` / `draw()` in `Level.update()` / `Level.draw_characters()`.
5. Emit `("life_damage",)` or `("alert",)` — `Game._process_event()` already handles both.

### Add a new pickup
1. Subclass `NPC`; `update()` returns `"collected"` when player rect overlaps.
2. Emit a new event tuple from `Level.update()`.
3. Handle the new tuple in `Game._process_event()`.

### Add a new level
- Create `Level3(Level)` or a new class with the same interface.
- Add a new state string to `constants.py`.
- Wire the transition in `Game._update()` and `Game._draw()`.

### Change scoring values
Edit only `constants.py`. The values are referenced by name everywhere else.

### Change physics feel
Edit `GRAVITY`, `JUMP_POWER`, or `PLAYER_SPEED` in `constants.py`. No other files need changes.

### Add sound
Add a `_build(...)` entry and `play_*()` method in `sounds.py`. Call it from `game.py`.

---

## Friendly Character Internals

### Camper state machine
`visit_state`: `"ready" → "petted" → "treated"`. Resets to `"ready"` when Ollie steps
>160 px away (`AWAY_DIST`). `delay_timer` counts down 120 frames (2 s) between pet and
treat. `update()` returns `"pet"` or `"treat"`; `Level` emits `("score",...) + ("hearts",)`
or just `("score",...)`. Never set `visit_state` externally.

### FriendlyGirl (Lily / Leia)
Stored in `level.friendly_girls` list — index 0–1 = Lily, 2–3 = Leia. Each instance
carries `reward_label` and `points`; do not hard-code in `level.py`. Reward fires only when
`player.vx > 0`. `rewarded_this_visit` resets on distance, not a timer. Do not re-add
a timer-based `interact_cooldown`.

---

## What Not to Break

- **Run the tests after any change**: `python -m unittest discover -s tests` (use the Python that
  has pygame — on this PC that is `py`, not `python`). They run headlessly and redirect
  `leaderboard._SCORES_FILE` to a temp folder; never let a test write the real `highscores.json`.
- **Never pass per-frame-changing arguments to `art.vgradient` / `art.radial_glow`** (or any
  `lru_cache`d art helper). Each new argument builds and caches a whole surface — this is what
  made the ascend cutscene run at 5 fps. Animate by blending/scaling a fixed cached surface instead.
- **Don't draw overlapping anti-aliased shapes straight onto one transparent surface** — gfxdraw's
  soft edges overwrite alpha and leave seams. See `_cloud_sprite` in `level3.py` for the pattern.
- **Every screen must paint the whole 1280×720 frame** — the game surface is never cleared, so
  any unpainted strip shows the previous screen and darkens under the pause overlay.
- **World right edge**: `Player.move_and_collide()` clamps x to `platforms[0].right`, so
  `platforms[0]` must span the full level width (it already must for the no-gaps rule).
- **`Game._present()`** scales the game surface to the window (letterboxed). Always draw to
  `self.screen` (fixed 1280×720), never to the window surface.
- **`leaderboard.load_scores()` / `save_score()` must never raise** — they run at startup and at
  the high-score hand-off.

- **Ground platform**: `level.platforms[0]` must be a single platform at `y == GROUND_Y`
  covering `x=0` to `x=level.width`. Do not split it — gaps cause Ollie to fall through.
  The Y-boundary safety net in `Player.move_and_collide()` is a fallback, not the primary fix.
- **Enemy speeds must stay below `PLAYER_SPEED`**: all chase speeds are in `constants.py`.
  Never hard-code speed values; always reference the named constants so difficulty can be tuned.
- **Event bus pattern**: Level must never import or call Game/Player directly.
- **`_init_game()`**: must fully reset all state — always call it on restart, never patch around it.
- **`_init_level2()` / `_init_level3()`**: must reset all level-state flags; do NOT call
  `_init_game()` — Ollie keeps score and lives from the previous level.
- **Level 3 cloud floor**: `level3.platforms[0]` is the single continuous floor at `GROUND_Y`,
  same no-gaps rule. God's throne is high up *on purpose* — never lower it to floor level or the
  staircase climb becomes pointless.
- **`cam_x` threading**: every NPC `draw()` receives `cam_x`; never draw at raw world coords.
- **`on_ground` flag**: set False before Y-collision pass, True only inside `_collide_y()`.
  Breaking this makes jumping feel sticky or floaty.
- **`invincible` counter**: checked in `take_damage()` to prevent multi-hit in one frame.
- **`level.events` list**: cleared at the start of every `Level.update()` call. Do not cache
  a reference to it across frames — always read within the same frame's update.
- **Font caching**: never call `pygame.font.SysFont()` inside a draw method. Use the module-level
  `_font()` helper. Breaking this causes a visible FPS drop on slower hardware.
- **Pause state**: `STATE_PAUSED` freezes `_update()` entirely. Any state that should be
  pauseable must be listed in the P/Esc handler in `game._handle_event()`.
- **`draw_hud` signature**: always pass `level_width=self.level.width` (so the progress bar
  scales per level) and `goal_label=self._goal_label()` (so it reads "Home →" in Level 1,
  "Bone →" in Level 2, "Heaven →" in Level 3).
- **Pauseable states**: `STATE_LEVEL3` is in the P/Esc handler alongside `STATE_PLAYING` and
  `STATE_LEVEL2`. The Heaven cutscenes (`ascend`, `heaven_celebrate`, `heaven_win`) are timer
  driven and intentionally not pauseable.
