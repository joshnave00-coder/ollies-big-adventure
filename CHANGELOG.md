# Changelog

All notable changes to Ollie's Big Adventure are recorded here.
Format: `## [version] — YYYY-MM-DD` with subsections Added / Changed / Fixed / Removed.

---

## [0.8.2] — 2026-10-10

Second durability pass — the five follow-ups from the 0.8.1 review.

### Changed
- **Game speed no longer depends on frame rate.** Logic runs in fixed 1/60 s steps
  (`Game._advance`); a slow machine draws fewer frames but Ollie, enemies and cutscenes keep
  real-time speed down to about 12 fps. A long stall (dragging the window) is dropped, not
  fast-forwarded. Confetti now advances in `_update` instead of while drawing.
- **High scores are saved per user**, outside the code folder (`%APPDATA%\OlliesBigAdventure\`
  on Windows). The old `highscores.json` beside the code is read as the starting board until the
  first new score is saved and is never written again, so playing no longer dirties the repo and
  a read-only install can still save.
- **Bigger text.** Smallest UI text 14 → 16 px (`FONT_SIZE_XS`); in-world labels (SAFE badge,
  name tags) 10–13 → 14 px (`FONT_SIZE_LABEL`).
- **Title and How-to-Play describe the whole game** (three levels, Cloud Spirits, coins, Heaven)
  instead of only Level 1, and no longer say the bone is the win.
- **One font helper with fallbacks** (`art.font`): Arial, then metric-compatible Liberation Sans /
  Arimo, then other sans-serifs, then pygame's built-in font. Text inside fixed panels uses
  `art.fit_text`, which shrinks to fit. The initials screen spells out the keys instead of using
  arrow glyphs that some fonts lack.

### Added
- **Volume control**: `-` / `+` on the title, How-to-Play and pause screens (10% steps).
- **Gamepad support**: stick or d-pad to walk, any face button to jump / confirm, Start to
  pause, d-pad to enter initials. Unplugging the pad pauses the game.

### Fixed
- Score popups now actually fade out.
- The hot slide only says "Ouch!" when it really cost a life.
- With no audio device the screens say "Sound is not available" instead of offering a toggle
  that reads ON while silent.
- Removed a half-second freeze at the start of the carpet-to-Heaven cutscene (0.8.1 built its
  glow at full size; it is now built small and scaled).

---

## [0.8.1] — 2026-10-10

Durability pass — no new gameplay; fixes found by running the game headlessly end to end.

### Fixed
- **Carpet-to-Heaven cutscene ran at ~5 fps** (the 3-second ride took 30–40 s) and leaked hundreds
  of MB: it built and permanently cached a new full-screen gradient and a giant glow every frame.
  It now cross-fades two cached gradients and scales one cached glow.
- **Damaged `highscores.json` crashed the game at startup** (wrong shape, bad values, non-text
  bytes). Loading now never raises, skips only the damaged entries, and sorts/trims the board.
- **Saving a score could crash** if the folder wasn't writable; the save is now atomic
  (temp file + replace) and a failed save is reported on stderr instead of ending the game.
- **Ollie could walk off the right end of every level** and fall forever off-screen. The world
  now has a right-hand wall.
- **Level 1 dead end without the water bottle**: the bottle is easy to hop over, and without it
  the carpet never appears. A sign at the end now tells the player to go back for it.
- **Level 3: the strip under the cloud floor was never painted** — it showed leftovers from the
  previous screen and turned permanently black after pausing.
- **Ollie was "airborne" every other frame while standing** (`on_ground` flickered because the
  collision rect dropped the sub-pixel sink from gravity), so the run animation stuttered.
- **Pause screen said "Press S to toggle sound" but S did nothing** while paused. It works now.
- **Losing the last life on the same frame as touching the carpet** skipped Game Over and flew
  home with 0 lives.
- **Hawk divide-by-zero** when exactly on top of Ollie.
- Leftover score popups and confetti no longer carry over into the next level or a restart.

### Changed
- **Level 2 and Level 3 draw 2–5× faster** (same picture): the wallpaper wall and the Heaven sky
  are composed once instead of per frame, clouds are pre-rendered sprites, and off-screen
  enemies, coins, angels and the throne are no longer drawn.
- **The window now scales the picture to fit** (letterboxed) when resized or maximised, and
  starts smaller on screens that can't fit 1280×720. Previously a small window cropped the game.
- **The game pauses itself when the window loses focus or is minimised.**
- `art.vgradient` / `art.radial_glow` caches are now bounded.

### Added
- `tests/test_durability.py` — headless regression tests for all of the above
  (`python -m unittest discover -s tests`). They redirect the leaderboard to a temp folder.
- `requirements.txt`.

---

## [0.8.0] — 2026-06-13

### Added — Level 3: Ollie Goes to Heaven
Built from a 7-year-old's design: *Ollie rides the magic carpet up to heaven, gets past the weird
people, collects as much money as he can, climbs the stairs to the singing angels, touches God on
a flying throne, has no more pain and all the food he wants, and gets a home in heaven.*

- **New level `level3.py`** (8 000 px sky level), reached from the Level 2 win screen. Ollie keeps
  his score and lives via the new `_init_level3()`. Five sections: Cloud Landing → Spirit Gauntlet
  → Great Staircase → Pearly Gates → God's Throne.
- **Coins** — a brand-new "money" pickup (`Coin`, `SCORE_COIN = 25`) scattered generously across
  the whole climb. Spinning, bobbing gold coins with a bright two-note `play_coin` chime; they
  reuse the existing `("score", …)` event via the `"Coin!"` label.
- **Cloud Spirits** (`CloudSpirit` ×9) — the floaty, googly-eyed "weird people" Ollie must get
  past. Pastel ghost-like obstacles that drift up and down and gently give chase (speeds below
  Ollie's, with the standard anti-jitter dead-zone).
- **Singing Angels** (`SingingAngel` ×5) at the pearly gates — purely joyful greeters with
  flapping wings, halos and floating musical notes that sing faster as Ollie approaches.
- **God on a flying throne** (`GodThrone`) — the goal. A radiant, gentle, tastefully-abstract
  figure on a golden throne wreathed in light, beams and orbiting sparkles, high up so Ollie has
  to climb the staircase to reach it.
- **Carpet ascent intro** (`STATE_ASCEND` + `draw_ascend_screen`) — Ollie rides the magic carpet
  up as clouds rush past and the sky brightens to gold ("Up to Heaven…").
- **Touch-God celebration** (`STATE_HEAVEN_CELEBRATE` + `draw_heaven_celebrate`) — golden light,
  healing hearts ("No more pain, Ollie!"), then a ring of feast food appears ("Eat all you
  want!"), with a `play_heaven` choir chord. Touching God also fully heals Ollie and gifts +1 life.
- **"Ollie's Home in Heaven" ending** (`STATE_HEAVEN_WIN` + `draw_heaven_win`) — Ollie wagging in
  front of his own little cloud house, flanked by singing angels, with confetti and the final
  score. This is the new finale and now owns the high-score/initials hand-off.
- **Title test shortcut**: press `3` five times on the title screen to jump straight to Level 3
  (mirrors the existing `2`-for-Level-2 shortcut).

### Changed
- **Level 2 win now flows onward**: instead of ending the game, pressing ENTER launches the
  carpet ride up to Level 3.
- **HUD progress bar** reads "Heaven →" in Level 3 (`_goal_label()`); `STATE_LEVEL3` is pauseable.

---

## [0.7.0] — 2026-05-29

### Added — Character art & a real Level 2
- **Human NPCs now use CC0 Kenney "Platformer Characters" sprites** via new
  `art.sprite()` / `art.blit_sprite()` helpers (scale-to-height, facing flip, auto
  contact shadow): Dog Catcher = Soldier (+ a hand-drawn net), Campers = Adventurer/Player,
  Lily/Leia = Female (name tags keep them distinct). The homecoming screen's
  Mom/Dad/Lily/Leia reuse the same sprites so the cast is consistent everywhere.
- **Per-character shirt colours** (baked once via an in-engine hue swap that keeps the
  shading): Lily = orange, Leia = gold, Mom = purple. **Dad** is a light-skinned man in an
  orange shirt (based on the Adventurer, not the Soldier). **Dog catchers** wear a blue
  uniform so they're clearly different characters from the family.
- **`art.panel()`** — rounded, gradient-shaded, drop-shadowed block used to make every
  piece of furniture look illustrated instead of like a flat rectangle.
- **Room decor layer** (`Level2._draw_room_decor`): wainscoting, area rugs, warm light
  pools, and potted plants behind the furniture.

### Changed — graphics redraws
- **Lion** — fuller three-ring mane, bigger head, proper muzzle and eyes.
- **Hawk** — actually reads as a bird of prey now (swept flapping wings, hooked beak,
  fierce eye, fanned tail, pale chest).
- **Angel** — feathered layered wings, flowing robe with gold hem, serene face, glowing halo.
- **Campfire & tent** — stone-ring fire with layered flames; A-frame tent with a door flap.
- **Hot slide** — removed the cheesy "heat wave" shimmer lines; now a subtle warm glow only.
- **House cat** — redrawn as a cute orange tabby (ears, stripes, tail, whiskers).
- **Roomba** — clean domed disc with a sensor turret and gentle LED (no more busy spinning brush).
- **Level 2 rooms rebuilt** — a proper kitchen (counter, sink + faucet, range/oven with hood,
  upper cabinets, island, breakfast table, real two-door fridge); dining room with a legged
  table, chairs and sideboard; the Library is now a cosy **Play Room**; framed pictures show
  real little scenes (house, sun, family, hearts) instead of solid blocks; living-room couch
  sits on the floor with a wall-mounted TV (no more "TV on the couch").

### Changed — gameplay feel
- Level 2 platform count cut from ~30 to 11 — each is the visible top of a piece of furniture.
- **Cats and Roombas slowed** (`CAT_CHASE_SPD` 1.8→1.1, `ROOMBA_CHASE_SPD` 2.0→1.3, patrols too).
- **Anti-jitter dead-zone** for House Cats, Roombas and the Dog Catcher: they stop instead of
  flip-flopping when standing directly under Ollie. (The Lion already had one.)

## [0.6.0] — 2026-05-29

### Added — How to Play & clarity
- **`STATE_HOWTO`** — a kid-friendly **How to Play** screen reached from the title with **H**
  (or **I**). It explains the goal, controls (with keycap glyphs), friends vs. baddies (using
  the *real* in-game sprites as labelled icons), the 3-hearts lives system, and the sound
  setting. Any of Space/Enter/Esc/H returns to the title; **S** toggles sound there too.
- Title screen now shows a gold **"Press H — How to Play"** chip below the start prompt.
- **`UI.draw_howto`**, `_howto_icons`, `_howto_icon`, `_howto_band`, `_draw_key`, `_draw_heart`
  helpers in `ui.py`.

### Changed — clarity
- HUD progress-bar label is now level-aware: **"Home →"** in Level 1, **"Bone →"** in Level 2
  (`draw_hud(..., goal_label=...)`, fed by `Game._goal_label()`).

### Added — Graphics overhaul (hybrid art)
- **`art.py`** — new shared rendering toolkit (pure presentation, leaf module like
  `constants.py`):
  - `aadraw` — drop-in replacement for `pygame.draw` with anti-aliased
    circle/ellipse/polygon/line/lines (via `pygame.gfxdraw`); rects stay crisp.
  - CC0 image loader/cache: `image`, `scaled`, `scaled_h`, `scaled_w`, `tinted`.
  - Effects: `vgradient`, `soft_shadow`, `ground_shadow`, `radial_glow`, `shade`.
- **`assets/img/`** — curated CC0 (Kenney) environment art: `ground/` grass+dirt tiles,
  `sky/` clouds·hills·mountains, `foliage/` trees·bushes·tufts·flowers, `pattern/`
  wallpaper motifs. See `assets/CREDITS.txt`.

### Changed
- **Level 1** (`level.py`): flat sky/hills/clouds/trees/ground replaced with a layered
  parallax scene — gradient sky, soft sun glow, tinted hill strips, distant mountains,
  cloud sprites, tiled grass/dirt ground, and a foliage tree-line with shrubs/flowers.
- **Level 2** (`level2.py`): bare cream wall replaced with a warm gradient + subtle tiled
  wallpaper; richer wood floor (gradient, plank seams, sheen, moulding). All furniture and
  the cat/roomba/crate now render through `aadraw` for smooth edges.
- **Characters** (`player.py`, `characters.py`): drawn through `aadraw`; ground-based
  sprites (Ollie + NPCs) get a soft `ground_shadow` contact shadow. Designs unchanged —
  the cast stays 100% procedural.
- **UI** (`ui.py`): title, home, and enter-initials screens reuse the new art so every
  screen matches the in-game look.

### Notes
- Gameplay, objectives, physics, collision, scoring, and the event-bus architecture are
  untouched — this release is presentation only.

## [0.5.0] — 2026-04-17

### Changed — Angel celebration (full rewrite)
- `Angel` is now fully **screen-space**: position is clamped to `[80, SCREEN_WIDTH−120]` px
  from the left edge at trigger time, so the Angel always appears on screen regardless of
  how far the camera has scrolled.
- **One-at-a-time guard**: `trigger()` returns immediately if an Angel is already visible.
- **Three-phase timer** replaces the old single countdown:
  | Phase | Duration | Behaviour |
  |-------|----------|-----------|
  | descend | 1.5 s (90 frames) | floats down from y=−80 to y=120 |
  | glow | 2.0 s (120 frames) | pauses, pulses with larger/brighter aura |
  | ascend | 1.0 s (60 frames) | floats back up and disappears |
- **"Go Ollie!" text**: rendered in gold above the Angel's head during the glow phase,
  with a gentle vertical bounce (`sin` wave).
- **Enhanced glow**: glow radius grows from 40 px to 60 px and alpha from 80 to 130
  during the glow phase so the moment of celebration is visually distinct.
- **Screen-space particles**: sparkle particles stored and drawn in screen coords —
  they no longer drift as the camera scrolls.
- `trigger()` signature changed to `trigger(world_x, cam_x)` — `game.py` now passes
  `self.level.camera_x` as the second argument.
- Phase-timing constants moved to `constants.py`:
  `ANGEL_DESCEND_FRAMES = 90`, `ANGEL_GLOW_FRAMES = 120`, `ANGEL_ASCEND_FRAMES = 60`
  (replaces the old `ANGEL_DURATION = 180`).

---

## [0.4.0] — 2026-04-17

### Fixed — Ollie disappearing off the bottom of the screen
- **Root cause**: the ground was 7 separate platform strips with 30–50 px gaps between them
  (e.g. x=1400–1450). The visual ground drew as a solid rectangle so the gaps were invisible,
  but collision was broken — Ollie would fall through and sink below the screen while the
  camera only tracked horizontal position, leaving gameplay running but Ollie invisible.
- **Fix**: replaced all 7 ground strip `_plat()` entries with a single continuous platform
  `_plat(0, GROUND_Y, LEVEL_WIDTH)` — solid ground from world x=0 to x=7000.
- **Safety net**: added a Y-boundary check in `Player.move_and_collide()` — if `self.y`
  ever exceeds `SCREEN_HEIGHT + 40` (should now be unreachable), Ollie snaps back to ground
  level with `vy=0` and `on_ground=True`.

### Changed — Enemy speeds (child-friendly difficulty)
All enemy chase speeds are now well below `PLAYER_SPEED = 4`, so a beginner can always
outrun every enemy by holding a direction key.

| Enemy | Patrol (before → after) | Chase (before → after) | Chase trigger (before → after) |
|-------|------------------------|------------------------|-------------------------------|
| Dog Catcher | 1.8 → **1.0** | 3.24 → **1.6** | 150 px (unchanged) |
| Hawk | 2.0 → **0.9** | 2.5 → **1.4** | 250 px → **180 px** |
| Tiger | 1.5 → **0.8** | 2.8 → **1.5** | 220 px → **180 px** |
| Lion | 1.5 → **0.7** | 2.8 → **1.2** | 220 px → **180 px** |

All speed values are now named constants in `constants.py`:
`CATCHER_PATROL_SPD`, `CATCHER_CHASE_SPD`, `HAWK_PATROL_SPD`, `HAWK_CHASE_SPD`,
`HAWK_CHASE_RAD`, `TIGER_PATROL_SPD`, `TIGER_CHASE_SPD`,
`LION_PATROL_SPD`, `LION_CHASE_SPD`, `BEAST_CHASE_RAD`.

`GroundEnemy` now stores `_patrol_spd` and `_chase_spd` per-instance (set at construction
from the kind-specific constants) so tigers and lions differ cleanly.

---

## [0.3.0] — 2026-04-17

### Changed — Camper interaction (state machine rewrite)
- `Camper` now uses a `visit_state` machine (`ready → petted → treated`) instead of one-time
  `petted/treated` boolean flags.
- **2-second delay** (120 frames) between pet reward and treat offer, matching the spec.
- **Walk-away reset**: when Ollie steps more than 160 px away after a treat, `visit_state`
  resets to `ready` so the next approach earns both rewards again.
- `Camper.update()` now returns `"pet"` or `"treat"` directly (was `"interact"`); state is
  fully managed inside the class — `level.py` no longer needs to track `petted`/`treated`.
- **SAFE badge**: green pulsing glow + "SAFE" label drawn above each camper at all times.
- **Bone icon**: appears above the camper for ~1.5 s after a treat reward (`show_bone` timer).
- **Heart particles**: `("hearts",)` event emitted on pet; `Game` calls `player.add_hearts()`
  which spawns 10 pink particles that float up above Ollie.
- Reduced from 4 campers to 3, repositioned to x=500 / 2600 / 4800 with clear gaps.

### Changed — Lily & Leia (FriendlyGirl rewrite)
- `FriendlyGirl` adds `reward_label` and `points` attributes set at construction time.
- **Direction gate**: treats only fire when `player.vx > 0` (Ollie moving right toward home).
- **Distance-based reset** (`AWAY_DIST = 160 px`) replaces timer-only `interact_cooldown`;
  each new pass earns a reward once Ollie steps far enough away.
- Lily popup text changed from "Lily's Treat!" to **"Good boy!"**
- Leia popup text changed from "Leia's Treat!" to **"You got this!"**
- Each girl now appears at **2 positions** across the level (was 1 each):
  - Lily at x≈1600 and x≈4200
  - Leia at x≈3100 and x≈5600
- `level.py` uses `self.friendly_girls` list (replaces `self.lily` / `self.leia`).

### Added
- `Player.add_hearts()` — spawns 10 pink heart particles above Ollie (called on camper pet).
- `("hearts",)` event tuple — emitted by `Level`, handled in `Game._process_event()`.

---

## [0.2.0] — 2026-04-16

### Changed — Enemy damage model and feedback
- **All enemy contact now costs exactly −1 life** (was −25 HP). One hit = one life lost,
  matching kid-friendly intent. Slide hazard still uses HP (`take_damage()`).
- **Red flash on hit**: Ollie alternates between a red-tinted visible frame and an invisible
  frame for the full 2-second immunity window (was pure blink-invisible only).
- **Invincibility window extended to 2 seconds** (120 frames, was 90 / 1.5 s).
- **New `Player.lose_life()` method**: direct life decrement that respects the invincibility
  window. Separate from `take_damage()` which remains for HP-based hazards.
- **HUD popup on hit**: shows "Ouch! N lives left" with remaining count (was "Ouch!").
- **Alert radius tightened to 150 px** (was 200 px) — easier to avoid the warning zone.

### Added — Enemy respawn
- All enemies (`DogCatcher`, `Hawk`, `GroundEnemy`) now store `spawn_x` / `spawn_y` and
  reset to their start position + patrol state when Ollie moves more than 900 px away from
  their spawn. Keeps areas feeling "alive" on revisit.

### Fixed
- `Hawk` patrol was using `base_y` as the horizontal patrol centre — now correctly uses
  `base_x`. Hawks no longer drift off in the wrong axis.

### Internal
- New event tuple `("life_damage",)` replaces `("damage", ENEMY_DAMAGE)` for enemy contacts.
  `("damage", amount)` is reserved for HP hazards (slide). Handled in `Game._process_event()`.
- Added `INVINCIBLE_FRAMES = 120` and `ENEMY_RESPAWN_DIST = 900` to `constants.py`.

---

## [0.1.0] — 2026-04-16

### Added
- Initial playable build of Level 1.

**Core systems**
- `main.py` — entry point; Pygame 2.x init, 1280×720 window, custom poodle icon.
- `game.py` — `Game` class with state machine: `title → playing → carpet → home` (plus
  `game_over`). Per-frame event loop at 60 FPS target. Tuple-based event bus between `Level`
  and `Game`.
- `constants.py` — single source of truth for all colors, sizes, speeds, scoring values,
  detection radii, state strings, and physics constants.

**Player (Ollie)**
- `player.py` — `Player` class: WASD / arrow-key movement, variable-height jump, gravity,
  AABB platform collision (separate X/Y passes).
- Animations: `idle`, `run`, `jump`, `wag`, `sad`, `alert` — all procedurally drawn.
- Tail-wag pendulum animation driven by `tail_angle` + `tail_dir`.
- Invincibility frames (90 frames) after taking damage; sprite blinks during immunity.
- Sparkle particle system on score events (`add_sparkles()`).
- Health (100 HP) + 3 lives. Losing all HP costs a life and resets HP to full.

**Level**
- `level.py` — `Level` class: 7 000 px scrollable world with smooth camera (`camera_x`
  lerps toward `player_x − SCROLL_THRESH`).
- 30 platforms (ground strips + elevated platforms).
- Layered parallax background: sky gradient, sun with 12 rotating rays, clouds (0.1×),
  distant hills (0.2×), mid hills (0.5×), trees (1:1).
- Slide hazard zone at x=6000 with animated heat-wave lines and HOT glow.

**Characters (`characters.py`)**
- `Camper` × 4: sit near campfires/tents, pet animation on approach, emit `score` events
  (pet +10, treat +15), 3-second interact cooldown, pulsing heart icon.
- `DogCatcher` × 4: patrol between fixed bounds, chase Ollie at 1.8× speed when within 200 px,
  emit `damage` events on contact, show `!` alert marker.
- `Bird` × 12: hover/flutter, flee when Ollie within 120 px, caught on 40 px contact (+25 pts).
- `Hawk` × 4: airborne, swoop toward Ollie within 250 px, emit `damage` on contact.
- `GroundEnemy` (Tiger × 3, Lion × 2): patrol then chase within 220 px, emit `damage`.
- `FriendlyGirl` (Lily at x≈1600, Leia at x≈3400): wave + give treat within 100 px (+20 pts
  each, 4-second cooldown). Lily has blonde hair, Leia has light-brown hair.
- `Angel`: triggered randomly (1-in-4 scoring events) by `Game`; descends from top, glows
  yellow with orbiting star particles, ascends after 3 seconds.
- `WaterBottle` at x≈5700: collect before slide to avoid damage; activates `MagicCarpet`.
- `MagicCarpet` at x≈6400: hidden until water collected; on contact launches Ollie home.

**UI (`ui.py`)**
- HUD: semi-transparent top bar, green/yellow/red health bar, paw-icon lives display,
  gold score counter, blue water indicator.
- Floating score popups: rise and fade over 90 frames.
- Title screen: animated sun rays, parallax trees, bouncing mini-Ollie, blinking start prompt.
- Game-over screen: dark overlay, red "Game Over", final score, blinking restart prompt.
- Home celebration screen: house illustration, family members (Mom/Dad/Lily/Leia) waving,
  treasure chest opening with coin sparkles, confetti particle system (200 pieces).

**Scoring**
| Event | Points |
|-------|--------|
| Camper pet | +10 |
| Camper treat | +15 |
| Lily treat | +20 |
| Leia treat | +20 |
| Bird caught | +25 |

**End-of-level sequence**
1. Slide zone — damage (−30 HP) without water; wag animation with water.
2. Water bottle collect → carpet appears.
3. Carpet contact → 2-second pause, lift-off, fly right off screen.
4. Transition to home screen with confetti + family celebration.

---

<!-- Future versions go above this line, newest first -->
