# Ollie's Big Adventure 🐾

A cheerful, kid-friendly 2D platformer built with Python 3 and Pygame. You play as **Ollie**, an
apricot-colored poodle puppy who got lost. Help him cross a sunny outdoor world to find his
**magic carpet** and fly home — then sniff through the whole **house** to find his **big bone!**

Made by a dad and his 7-year-old daughter. The cast (Ollie, Lily, Leia, the campers, and every
critter) is original, hand-coded art; the scenery uses free [Kenney](https://kenney.nl) CC0 art.

---

## Quick Start

```bash
cd "Ollie's Big Adventure"
pip install pygame      # Pygame 2.x — the only dependency
python main.py
```

Python 3.10+ recommended. No other downloads needed — the environment art ships in
`assets/img/`, and all sounds are generated in code.

---

## How to Play (for kids! 🧒)

You can also read this **inside the game**: on the start screen, press **H — How to Play**.

### 🎯 The goal
1. **Walk RIGHT** through the outdoor world to find Ollie's **Magic Carpet**, then fly home.
2. Inside the house, explore the rooms to find Ollie's **BIG BONE**. That's the win!

### 🎮 How to move
| Key | What it does |
|-----|--------------|
| **← →** or **A / D** | Walk left and right |
| **↑ / W / Space** | Jump |
| **P** or **Esc** | Pause / resume |
| **Enter / Space** | Start the game · confirm on menus |
| **H** | Open the How-to-Play screen (from the title) |
| **S** | Turn sound **ON / OFF** |

### 💚 Friends — go say hi!
- **Campers** sit by their **SAFE** tents. Walk up to **pet** them, then they give a **treat**.
- **Lily & Leia** wave and hand Ollie a **treat** when he passes by (heading right).
- **Birds** flutter around — **chase and catch** them for points.

### ⚠️ Watch out — don't get touched!
**Dog Catchers, Lions, and Hawks** (outdoors) and **House Cats and Roombas** (in the house)
will cost Ollie a **heart** if they touch him. After a bump he flashes and is safe for a
moment. They all move slower than Ollie, so you can always outrun them.

### ❤️ Lives & the hot slide
Ollie has **3 hearts**. Lose them all and it's **Game Over**. The HP bar mostly matters for the
**hot slide** near the end of Level 1 — grab the **water bottle** first so the slide is a fun
"Wheee!" instead of an "Ouch!".

### 😇 The Angel
Now and then after scoring, a little **Angel** floats down, sparkles, and cheers Ollie on. Pure
encouragement — no points needed.

---

## Features

- **Two full levels** — a 7 000 px outdoor adventure and an 8 000 px, 8-room furnished house
  (entry, living room, hallway, kitchen, dining room, play room, corridor, master bedroom).
- **Ollie & every animal are original procedural art** — drawn in code, anti-aliased, with soft
  contact shadows. The human NPCs (dog catcher, campers, Lily & Leia) and the homecoming family
  use matching CC0 [Kenney](https://kenney.nl) people sprites so the cast looks consistent.
- **Hybrid environment art** — layered parallax skies, hills, foliage, tiled ground, wallpapered
  and furnished rooms (real kitchen, fridge, framed pictures) from free CC0 art
  (see [assets/CREDITS.txt](assets/CREDITS.txt)).
- **Kid-friendly How-to-Play screen** reachable from the title, with real creature icons.
- **Gentle difficulty** — every enemy is slower than the player; a 2-second mercy window after hits.
- **Score popups, an encouraging Angel, confetti celebrations**, and a **top-5 leaderboard**
  saved to `highscores.json`.
- **No asset hunting** — programmatic sound effects, bundled environment art, one `pip install`.

---

## Scoring

| Event | Points |
|-------|--------|
| Pet a camper | +10 |
| Camper gives a treat | +15 |
| Lily / Leia gives a treat | +20 |
| Catch a bird | +25 |
| Each remaining life at the end of Level 1 | +100 |
| Find the big bone (Level 2 win) | +500 |

---

## Settings

- **Sound on/off** — press **S** on the title screen or the How-to-Play screen. The current
  state is shown in the corner.

---

## Project Layout

```
Ollie's Big Adventure/
├── main.py          Entry point — Pygame init, window, icon, game loop
├── game.py          Game class — state machine, event routing, draw dispatch
├── player.py        Player (Ollie) — physics, input, collision, animation
├── characters.py    Level 1 NPCs: Camper, DogCatcher, Bird, Hawk, GroundEnemy (Lion),
│                     FriendlyGirl (Lily/Leia), WaterBottle, MagicCarpet, Angel
├── level.py         Level 1 — layout, camera, parallax background, NPC instances
├── level2.py        Level 2 — interior house; HouseCat, Roomba, BoneCrate, Level2
├── ui.py            UI — HUD, popups, title, How-to-Play, home & other screens
├── art.py           Rendering toolkit — anti-aliased primitives, CC0 image loader,
│                     gradients, soft shadows (added in v0.6)
├── sounds.py        SoundManager — all sound effects synthesised at runtime
├── leaderboard.py   Top-5 high-score persistence (highscores.json)
├── constants.py     Every magic number and string (colors, sizes, speeds, scoring)
└── assets/
    ├── img/         CC0 Kenney art: ground/ sky/ foliage/ pattern/ char/ (human NPCs)
    ├── sounds/      Reserved for future audio files
    └── CREDITS.txt  Art attribution (CC0)
```

---

## For Developers

[`CLAUDE.md`](CLAUDE.md) is the authoritative deep-dive: architecture, the one-way Level→Game
**event bus**, the state machine, per-character internals, the **rendering rule** (draw character
shapes through `art.aadraw`, load scenery through `art.image`/`scaled`/`tinted`), and a
"what not to break" checklist. Read it before changing code.

Version history lives in [`CHANGELOG.md`](CHANGELOG.md).

### Design rules in one breath
- All tunable numbers live in `constants.py` — never hard-code them elsewhere.
- `Level` never imports `Game`/`Player`; it communicates only by appending event tuples.
- Characters stay 100% procedural; stock art is for environment/backgrounds only.
- Enemy chase speeds always stay below the player's speed (it's a kids' game).
