import pygame
import sys
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS
from game import Game


def main():
    pygame.init()
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    display = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
    game_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    pygame.display.set_icon(_make_icon())

    game = Game(game_surf, display)
    game.run()

    pygame.quit()
    sys.exit()


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
