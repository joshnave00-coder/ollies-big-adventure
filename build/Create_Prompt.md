**Ollie's Big Adventure/LEIA'S GAME**





File named ollies\_adventure\_game\_map.svg is a comprehensive Claude Code prompt that captures all of Ollie's adventure with clear structure and technical direction:





===========================================================================



Build a kid-friendly 2D platformer game called "Ollie's Big Adventure" using Python and Pygame. 

The goal of the game is that Ollie, an apricot-colored poodle puppy, is lost and trying to make 

it home safely through Level 1.



\---



PLAYER CHARACTER

\- Ollie is an apricot/peach-colored cartoon poodle puppy

\- Has basic movement: left, right, jump

\- Has a health/stamina bar and a score counter displayed on screen

\- Shows visual feedback (wag animation, sad animation) based on game events



\---



SETTING — LEVEL 1

\- Bright daytime outdoor scene with a large, cheerful sun in the upper portion of the sky

\- Grassy platforms, trees, and nature elements

\- Scene has warm colors and a playful, cartoonish art style

\- Background layers for depth (sky, distant hills, grass)



\---



ENEMIES \& HAZARDS

\- Dog Catchers: humans in uniforms who patrol the level. If they catch Ollie, he loses health/lives.

\- Wild Animals: Hawks (flying), Tigers, and Lions that chase Ollie. Contact causes health loss.

\- Ollie should have a visual "alert" reaction when enemies are nearby



\---



FRIENDLY CHARACTERS

1\. Campers: Humans sitting near campfires/tents. They are SAFE. When Ollie approaches:

&#x20;  - They pet him (play a pet animation)

&#x20;  - Give him treats

&#x20;  - Ollie gains points for each pet and treat interaction

&#x20;  - Mark them visually as friendly (e.g., warm glow or smile icon)



2\. Birds: Small birds scattered through the level. Ollie chases them automatically when nearby.

&#x20;  If Ollie catches and "eats" a bird, he earns points. Birds should flutter and flee when Ollie 

&#x20;  approaches.



3\. Lily: A little girl with blonde hair who appears at certain spots on the level. She has treats 

&#x20;  and rewards Ollie with points when he is doing the "right thing" (moving in the right direction, 

&#x20;  avoiding enemies). She encourages him forward.



4\. Leia: A little girl with light brown hair. Same behavior as Lily but placed at different 

&#x20;  positions. Together they help guide Ollie toward home.



\---



SCORING SYSTEM

\- Camper pets Ollie: +10 points

\- Camper gives treat: +15 points

\- Lily gives treat: +20 points

\- Leia gives treat: +20 points

\- Ollie catches and eats a bird: +25 points

\- Penalties for getting caught by enemies: -1 life or health reduction



\---



ANGEL EVENT (RANDOM CELEBRATION)

\- An Angel character will randomly float down from the top of the screen (not every time points 

&#x20; are earned — only at random intervals, roughly 1 in 4 point-scoring events)

\- The Angel glows yellow and pulses with light

\- Plays a celebratory sound or sparkle particle effect

\- Floats back up after \~2-3 seconds

\- This is a special reward moment, not a regular occurrence



\---



END OF LEVEL 1 SEQUENCE

Step 1 — The Hot Slide:

&#x20; - Near the end of the level, Ollie reaches a large slide

&#x20; - A heat visual effect shows it is very hot (wavy heat lines, red/orange glow)

&#x20; - Ollie must collect a water bottle/bowl pickup before going down the slide

&#x20; - If he slides without water, he takes damage

&#x20; - If he has water, he slides down safely with a happy animation



Step 2 — The Magic Carpet:

&#x20; - At the very end of Level 1, a magic carpet appears (colorful, ornate, floating)

&#x20; - Ollie steps onto it and it lifts off, flying him across the screen toward home

&#x20; - Animate the carpet flying off to the right with Ollie on it (transition to home scene)



Step 3 — Home Arrival Scene:

&#x20; - A cozy house appears with a yard and celebration decorations

&#x20; - Ollie's human family is waiting outside: Mom, Dad, Lily (blonde hair), and Leia (light brown hair)

&#x20; - All four characters have happy animations (waving, cheering)

&#x20; - A treasure chest appears and pops open, releasing sparkles/coins

&#x20; - Confetti or fireworks go off on screen — it's a PARTY!

&#x20; - Display a "You made it home!" message and the final score



\---



TECHNICAL REQUIREMENTS

\- Use Python 3 and Pygame

\- Sprite-based characters (simple shapes or pixel art style is fine — keep it readable and cute)

\- Tile-based or layered scrolling background for level progression

\- Sound effects for: points earned, angel appearance, treat collection, enemy nearby, slide, 

&#x20; carpet liftoff, and home arrival

\- Game states: title screen → gameplay → end-of-level sequence → home celebration screen

\- Score and lives displayed in a HUD (heads-up display) at the top of the screen

\- Frame rate target: 60fps

\- Window size: 1280x720



\---



FILE STRUCTURE

Organize the project with:

\- main.py (entry point)

\- game.py (main game loop and state manager)

\- player.py (Ollie's class)

\- characters.py (Lily, Leia, campers, dog catchers, birds, wild animals, angel)

\- level.py (level layout, platforms, scrolling)

\- ui.py (score, HUD, end screens)

\- assets/ folder (images, sounds — use placeholder colored rectangles if no art is available)

\- constants.py (colors, screen size, speeds, point values)



Start by building a playable skeleton with all major game systems stubbed out, then fill in 

character behaviors and the end-of-level sequence. Prioritize getting Ollie moving, enemies 

patrolling, and scoring working first.





===========================================================================



A few things this prompt does well for Claude Code:



It breaks the game into discrete, buildable systems so Claude Code can scaffold one at a time

The file structure instruction prevents it from dumping everything into one file

The "skeleton first" note at the end tells it to prioritize a working loop over perfect art

Placeholder art is explicitly allowed, so it won't get stuck waiting for assets



When you paste this in, you can also follow up with things like "now add the angel event system" or "build out the end-of-level slide sequence" to iterate section by section. Want me to refine any part of the prompt?

