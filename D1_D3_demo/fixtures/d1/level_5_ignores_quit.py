import pygame


WINDOW_SIZE = (320, 240)
FRAME_RATE = 30


def main() -> None:
    pygame.init()
    pygame.display.set_mode(WINDOW_SIZE)
    frame_clock = pygame.time.Clock()
    while True:
        for _event in pygame.event.get():
            pass
        frame_clock.tick(FRAME_RATE)


if __name__ == "__main__":
    main()
