import pygame


WINDOW_SIZE = (320, 240)


def main() -> None:
    pygame.init()
    pygame.display.set_mode(WINDOW_SIZE)
    for _event in pygame.event.get():
        pass
    pygame.quit()


if __name__ == "__main__":
    main()
