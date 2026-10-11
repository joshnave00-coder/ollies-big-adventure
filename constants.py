# Screen
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
# Largest share of the desktop the starting window may use (room for title bar / taskbar)
WINDOW_FIT_W = 0.94
WINDOW_FIT_H = 0.86

# Game logic always advances in fixed 1/FPS steps, however fast the screen draws
STEP_MS           = 1000.0 / FPS
STEP_SNAP_MS      = 4.0    # frame times this close to one step count as exactly one (no judder)
MAX_CATCHUP_STEPS = 5      # most logic steps per drawn frame (keeps real-time down to 12 fps)

# Text — Arial first, then fonts with the same letter widths, then anything sans-serif
FONT_FAMILIES   = "arial,liberationsans,arimo,helvetica,nimbussans,dejavusans,freesans"
FONT_SIZE_XS    = 16       # smallest UI text (HUD labels, captions, hints)
FONT_SIZE_LABEL = 14       # smallest in-world label (name tags, SAFE badge)

# Sound volume (0.0–1.0), changed with - / + on the title, How-to-Play and pause screens
VOLUME_DEFAULT = 1.0
VOLUME_STEP    = 0.1

# Gamepad — any face button jumps / confirms; Start / Options / Back pauses
PAD_DEADZONE      = 0.35
PAD_JUMP_BUTTONS  = (0, 1, 2, 3)
PAD_PAUSE_BUTTONS = (6, 7, 9)
TITLE = "Ollie's Big Adventure"

# Colors
WHITE       = (255, 255, 255)
BLACK       = (0, 0, 0)
SKY_BLUE    = (135, 206, 235)
SUN_YELLOW  = (255, 220, 50)
GRASS_GREEN = (80, 160, 60)
DARK_GREEN  = (40, 100, 30)
BROWN       = (120, 80, 40)
APRICOT     = (190, 110, 60)
PEACH       = (220, 150, 90)
RED         = (220, 50, 50)
ORANGE      = (255, 140, 0)
GOLD        = (255, 200, 0)
PURPLE      = (150, 80, 200)
BLUE        = (50, 100, 220)
PINK        = (255, 150, 180)
LIGHT_BLUE  = (170, 220, 255)
GRAY        = (160, 160, 160)
GREEN       = (50, 180, 50)
DARK_GRAY   = (80, 80, 80)
CREAM       = (255, 245, 220)
TAN         = (210, 170, 110)
YELLOW_GLOW = (255, 255, 150)
HOT_RED     = (255, 60, 0)
CARPET_RED  = (180, 30, 30)
CARPET_GOLD = (220, 180, 0)
CARPET_BLUE = (30, 60, 180)
CAMPER_BLUE = (70, 130, 180)
UNIFORM_GRAY = (100, 110, 120)
HEALTH_GREEN = (60, 200, 60)
HEALTH_RED   = (200, 60, 60)
HUD_BG       = (0, 0, 0, 160)

# Physics
GRAVITY = 0.6
JUMP_POWER = -14
PLAYER_SPEED = 4
SCROLL_THRESH = 400  # px from left edge before camera scrolls

# Level
LEVEL_WIDTH = 7000   # total scrollable width
GROUND_Y = 580       # y-coordinate of main ground surface
PLATFORM_THICK = 20

# Scoring
SCORE_PET        = 10
SCORE_TREAT      = 15
SCORE_LILY_TREAT = 20
SCORE_LEIA_TREAT = 20
SCORE_BIRD       = 25

# Health
MAX_HEALTH = 100
ENEMY_DAMAGE = 25
SLIDE_DAMAGE = 30

# Game states
STATE_TITLE      = "title"
STATE_HOWTO      = "howto"      # kid-friendly instructions, reached from the title screen
STATE_PLAYING    = "playing"
STATE_SLIDE      = "slide"
STATE_CARPET     = "carpet"
STATE_HOME       = "home"
STATE_GAME_OVER  = "game_over"

# Angel chance (1 in N scoring events)
ANGEL_CHANCE = 4

# Pause state
STATE_PAUSED = "paused"

# Character sizes (w, h)
OLLIE_SIZE      = (48, 48)
CAMPER_SIZE     = (36, 52)
CATCHER_SIZE    = (36, 56)
BIRD_SIZE       = (28, 20)
HAWK_SIZE       = (38, 24)
LION_SIZE       = (54, 40)
LILY_SIZE       = (30, 52)
LEIA_SIZE       = (30, 52)
ANGEL_SIZE      = (44, 56)
CARPET_SIZE     = (90, 30)

# Detection radii
PET_RADIUS      = 80
ENEMY_ALERT_RAD = 150   # px — "!" warning appears above Ollie within this range
BIRD_FLEE_RAD   = 120
BIRD_CATCH_RAD  = 40
LILY_GIVE_RAD   = 100
ANGEL_DESCEND_FRAMES = 90    # 1.5 s — float down into view
ANGEL_GLOW_FRAMES    = 120   # 2.0 s — glow and pulse
ANGEL_ASCEND_FRAMES  = 60    # 1.0 s — float back up

# Enemy behaviour
INVINCIBLE_FRAMES  = 120   # 2 seconds at 60 fps — post-hit immunity window
ENEMY_RESPAWN_DIST = 900   # px from spawn before enemy resets to start position

# Enemy speeds — kept well below PLAYER_SPEED (4) so a 7-year-old can outrun everything
CATCHER_PATROL_SPD = 1.0   # dog catcher patrol (was 1.8)
CATCHER_CHASE_SPD  = 1.6   # dog catcher chase  (was 3.24)
HAWK_PATROL_SPD    = 0.9   # hawk horizontal patrol (was 2.0)
HAWK_CHASE_SPD     = 1.4   # hawk swoop speed   (was 2.5)
HAWK_CHASE_RAD     = 180   # px before hawk swoops (was 250)
LION_PATROL_SPD    = 0.7   # lion patrol        (was 1.5)
LION_CHASE_SPD     = 1.2   # lion chase         (was 2.8)
BEAST_CHASE_RAD    = 180   # px before lion chases (was 220)

# End-sequence states / timing
STATE_TRAVELING      = "traveling"
STATE_ENTER_INITIALS = "enter_initials"
TRAVEL_DURATION  = 150          # frames for the "traveling…" black-screen transition (2.5 s)
SLIDE_DURATION   = 60           # frames for the hot-slide animation

# Level 2
STATE_LEVEL2     = "level2"
STATE_LEVEL2_WIN = "level2_win"
LEVEL2_WIDTH     = 8000

# Level 2 scoring
SCORE_LIVES_BONUS = 100   # points per remaining life awarded at end of Level 1
SCORE_BONE        = 500   # big bone found in Level 2

# House Cat (Level 2 enemy)
CAT_SIZE       = (40, 30)
CAT_PATROL_SPD = 0.8
CAT_CHASE_SPD  = 1.1
CAT_CHASE_RAD  = 160

# Bone Crate (Level 2 goal)
CRATE_SIZE = (64, 48)

# Roomba (Level 2 ground obstacle)
ROOMBA_SIZE       = (50, 18)
ROOMBA_PATROL_SPD = 1.0
ROOMBA_CHASE_SPD  = 1.3
ROOMBA_CHASE_RAD  = 200

# Bone celebration
STATE_BONE_CELEBRATE     = "bone_celebrate"
BONE_CELEBRATE_DURATION  = 240   # 4 seconds at 60 fps

# ─────────────────────────────────────────────────────────────────────────────
# Level 3 — Heaven  (Ollie rides the carpet up, passes the weird cloud spirits,
# collects money, climbs the great staircase, meets the singing angels and God)
# ─────────────────────────────────────────────────────────────────────────────
STATE_ASCEND            = "ascend"            # carpet rises through the clouds (intro)
STATE_LEVEL3            = "level3"            # heaven gameplay
STATE_HEAVEN_CELEBRATE  = "heaven_celebrate"  # Ollie touches God — healing + feast cutscene
STATE_HEAVEN_WIN        = "heaven_win"        # "Ollie's Home in Heaven" ending screen

LEVEL3_WIDTH = 8000
ASCEND_DURATION          = 200   # frames for the carpet-to-heaven rise (~3.3 s)
HEAVEN_CELEBRATE_DURATION = 360  # frames for the touch-God cutscene (6 s)
ASCEND_GLOW_BASE_R    = 105      # the ascent light is built once at this radius, then scaled up
ASCEND_GLOW_MAX_ALPHA = 180      # final brightness of that light

# Level 3 scoring
SCORE_COIN   = 25     # each coin of "money" Ollie collects
SCORE_HEAVEN = 1000   # reaching God on the flying throne

# Cloud Spirit — the floaty "weird people" Ollie must pass (chase speeds < PLAYER_SPEED)
SPIRIT_SIZE       = (44, 58)
SPIRIT_PATROL_SPD = 0.8
SPIRIT_CHASE_SPD  = 1.1
SPIRIT_CHASE_RAD  = 170

# Coin (money pickup)
COIN_SIZE = (26, 26)

# Singing Angel (friendly greeter) + God's flying throne (goal)
SING_ANGEL_SIZE = (46, 70)
THRONE_SIZE     = (132, 150)
