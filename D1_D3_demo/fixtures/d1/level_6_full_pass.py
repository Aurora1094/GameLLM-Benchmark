import pygame


WINDOW_SIZE = (320, 240)
FRAME_RATE = 30
BACKGROUND_COLOR = (24, 28, 36)


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    frame_clock = pygame.time.Clock()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.fill(BACKGROUND_COLOR)
        pygame.display.flip()
        frame_clock.tick(FRAME_RATE)
    pygame.quit()


if __name__ == "__main__":
    main()
