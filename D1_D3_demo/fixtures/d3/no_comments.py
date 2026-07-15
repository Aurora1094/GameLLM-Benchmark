import pygame


WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FRAME_RATE = 60
PADDLE_WIDTH = 14
PADDLE_HEIGHT = 100
PADDLE_MARGIN = 36
PADDLE_SPEED = 7
BALL_SIZE = 16
BALL_SPEED_X = 5
BALL_SPEED_Y = 4
WIN_SCORE = 5
BACKGROUND_COLOR = (18, 22, 30)
FOREGROUND_COLOR = (235, 238, 245)
ACCENT_COLOR = (74, 190, 156)
CENTER_LINE_WIDTH = 2
SCORE_FONT_SIZE = 42


def initialize_game() -> tuple[pygame.Surface, pygame.time.Clock, pygame.font.Font]:
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("GameBench Pong")
    frame_clock = pygame.time.Clock()
    score_font = pygame.font.Font(None, SCORE_FONT_SIZE)
    return screen, frame_clock, score_font


def reset_ball(direction: int) -> tuple[pygame.Rect, int, int]:
    ball = pygame.Rect(
        WINDOW_WIDTH // 2 - BALL_SIZE // 2,
        WINDOW_HEIGHT // 2 - BALL_SIZE // 2,
        BALL_SIZE,
        BALL_SIZE,
    )
    return ball, BALL_SPEED_X * direction, BALL_SPEED_Y


def create_paddles() -> tuple[pygame.Rect, pygame.Rect]:
    center_height = WINDOW_HEIGHT // 2 - PADDLE_HEIGHT // 2
    player = pygame.Rect(PADDLE_MARGIN, center_height, PADDLE_WIDTH, PADDLE_HEIGHT)
    opponent = pygame.Rect(
        WINDOW_WIDTH - PADDLE_MARGIN - PADDLE_WIDTH,
        center_height,
        PADDLE_WIDTH,
        PADDLE_HEIGHT,
    )
    return player, opponent


def handle_events() -> bool:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
    return True


def update_player_input(player: pygame.Rect) -> None:
    pressed_keys = pygame.key.get_pressed()
    if pressed_keys[pygame.K_UP]:
        player.y -= PADDLE_SPEED
    if pressed_keys[pygame.K_DOWN]:
        player.y += PADDLE_SPEED
    player.y = max(0, min(WINDOW_HEIGHT - PADDLE_HEIGHT, player.y))


def update_opponent_ai(opponent: pygame.Rect, ball: pygame.Rect) -> None:
    opponent_center = opponent.centery
    if ball.centery < opponent_center:
        opponent.y -= PADDLE_SPEED
    elif ball.centery > opponent_center:
        opponent.y += PADDLE_SPEED
    opponent.y = max(0, min(WINDOW_HEIGHT - PADDLE_HEIGHT, opponent.y))


def resolve_ball_collision(
    ball: pygame.Rect,
    player: pygame.Rect,
    opponent: pygame.Rect,
    velocity_x: int,
    velocity_y: int,
) -> tuple[int, int]:
    if ball.top <= 0 or ball.bottom >= WINDOW_HEIGHT:
        velocity_y = -velocity_y
    if ball.colliderect(player) and velocity_x < 0:
        ball.left = player.right
        velocity_x = -velocity_x
    if ball.colliderect(opponent) and velocity_x > 0:
        ball.right = opponent.left
        velocity_x = -velocity_x
    return velocity_x, velocity_y


def update_score(
    ball: pygame.Rect,
    player_score: int,
    opponent_score: int,
) -> tuple[pygame.Rect, int, int, int, int]:
    velocity_x = BALL_SPEED_X
    velocity_y = BALL_SPEED_Y
    if ball.right < 0:
        opponent_score += 1
        ball, velocity_x, velocity_y = reset_ball(1)
    elif ball.left > WINDOW_WIDTH:
        player_score += 1
        ball, velocity_x, velocity_y = reset_ball(-1)
    return ball, velocity_x, velocity_y, player_score, opponent_score


def draw_scene(
    screen: pygame.Surface,
    score_font: pygame.font.Font,
    player: pygame.Rect,
    opponent: pygame.Rect,
    ball: pygame.Rect,
    player_score: int,
    opponent_score: int,
) -> None:
    screen.fill(BACKGROUND_COLOR)
    pygame.draw.line(
        screen,
        ACCENT_COLOR,
        (WINDOW_WIDTH // 2, 0),
        (WINDOW_WIDTH // 2, WINDOW_HEIGHT),
        CENTER_LINE_WIDTH,
    )
    pygame.draw.rect(screen, FOREGROUND_COLOR, player)
    pygame.draw.rect(screen, FOREGROUND_COLOR, opponent)
    pygame.draw.ellipse(screen, ACCENT_COLOR, ball)
    score_text = score_font.render(
        f"{player_score}   {opponent_score}",
        True,
        FOREGROUND_COLOR,
    )
    score_position = score_text.get_rect(center=(WINDOW_WIDTH // 2, SCORE_FONT_SIZE))
    screen.blit(score_text, score_position)
    pygame.display.flip()


def main() -> None:
    screen, frame_clock, score_font = initialize_game()
    player, opponent = create_paddles()
    ball, velocity_x, velocity_y = reset_ball(1)
    player_score = 0
    opponent_score = 0
    running = True

    while running:
        running = handle_events()
        update_player_input(player)
        update_opponent_ai(opponent, ball)
        ball.x += velocity_x
        ball.y += velocity_y
        velocity_x, velocity_y = resolve_ball_collision(
            ball,
            player,
            opponent,
            velocity_x,
            velocity_y,
        )
        ball, velocity_x, velocity_y, player_score, opponent_score = update_score(
            ball,
            player_score,
            opponent_score,
        )
        draw_scene(screen, score_font, player, opponent, ball, player_score, opponent_score)
        if player_score >= WIN_SCORE or opponent_score >= WIN_SCORE:
            player_score = 0
            opponent_score = 0
        frame_clock.tick(FRAME_RATE)

    pygame.quit()


if __name__ == "__main__":
    main()
