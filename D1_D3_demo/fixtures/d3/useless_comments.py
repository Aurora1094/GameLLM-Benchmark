"""Calibration fixture whose comments repeat syntax instead of explaining intent."""

import pygame


WINDOW_SIZE = (320, 240)  # Set the window size to 320 by 240.
FRAME_RATE = 30  # Set the frame rate to 30.
BACKGROUND = (24, 28, 36)  # Set the background color.
PLAYER_COLOR = (230, 235, 245)  # Set the player color.


def move_player(player: pygame.Rect, direction: int) -> None:
    # Add direction times four to player y.
    player.y += direction * 4
    # Set player y to a value between zero and the lower boundary.
    player.y = max(0, min(WINDOW_SIZE[1] - player.height, player.y))


def draw(screen: pygame.Surface, player: pygame.Rect) -> None:
    # Fill the screen with the background color.
    screen.fill(BACKGROUND)
    # Draw a rectangle with the player color.
    pygame.draw.rect(screen, PLAYER_COLOR, player)
    # Flip the display.
    pygame.display.flip()


def main() -> None:
    # Initialize pygame.
    pygame.init()
    # Create the screen.
    screen = pygame.display.set_mode(WINDOW_SIZE)
    # Create the clock.
    clock = pygame.time.Clock()
    # Create the player.
    player = pygame.Rect(24, 90, 18, 60)
    # Set running to true.
    running = True
    # Loop while running is true.
    while running:
        # Loop over events.
        for event in pygame.event.get():
            # Check whether the event is quit.
            if event.type == pygame.QUIT:
                # Set running to false.
                running = False
        # Get the pressed keys.
        pressed = pygame.key.get_pressed()
        # Subtract whether up is pressed from whether down is pressed.
        direction = int(pressed[pygame.K_DOWN]) - int(pressed[pygame.K_UP])
        # Call move player.
        move_player(player, direction)
        # Call draw.
        draw(screen, player)
        # Tick the clock.
        clock.tick(FRAME_RATE)
    # Quit pygame.
    pygame.quit()


# Check whether name is main.
if __name__ == "__main__":
    # Call main.
    main()
