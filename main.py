import pygame
import sys
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS, WINDOW_FIT_W, WINDOW_FIT_H
from game import Game


def main():
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    display = pygame.display.set_mode(_window_size(), pygame.RESIZABLE)
    game_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    pygame.display.set_icon(_make_icon())

    game = Game(game_surf, display)
    game.run()

    pygame.quit()
    sys.exit()


def _window_size():
    """Full game size if it fits on this screen, otherwise the largest 16:9
    window that does (Game scales the picture to whatever the window is)."""
    try:
        dw, dh = pygame.display.get_desktop_sizes()[0]
    except (pygame.error, IndexError):
        return SCREEN_WIDTH, SCREEN_HEIGHT
    # leave room for the title bar and taskbar
    scale = min(1.0, (dw * WINDOW_FIT_W) / SCREEN_WIDTH, (dh * WINDOW_FIT_H) / SCREEN_HEIGHT)
    return max(320, int(SCREEN_WIDTH * scale)), max(180, int(SCREEN_HEIGHT * scale))


def _make_icon():
    icon = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.circle(icon, (255, 180, 120), (16, 18), 12)
    pygame.draw.circle(icon, (255, 210, 160), (16, 10), 9)
    for ox in [-4, 0, 4]:
        pygame.draw.circle(icon, (255, 210, 160), (16 + ox, 4), 5)
    pygame.draw.circle(icon, (0, 0, 0), (20, 9), 2)
    pygame.draw.ellipse(icon, (40, 20, 10), (22, 13, 6, 4))
    return icon


if __name__ == "__main__":
    main()
