"""A compact Pong implementation with explicit, separated responsibilities."""

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
    """Initialize pygame resources shared by the game loop."""
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("GameBench Pong")
    frame_clock = pygame.time.Clock()
    score_font = pygame.font.Font(None, SCORE_FONT_SIZE)
    return screen, frame_clock, score_font


def reset_ball(direction: int) -> tuple[pygame.Rect, int, int]:
    """Return a centered ball and a deterministic launch velocity."""
    ball = pygame.Rect(
        WINDOW_WIDTH // 2 - BALL_SIZE // 2,
        WINDOW_HEIGHT // 2 - BALL_SIZE // 2,
        BALL_SIZE,
        BALL_SIZE,
    )
    return ball, BALL_SPEED_X * direction, BALL_SPEED_Y


def create_paddles() -> tuple[pygame.Rect, pygame.Rect]:
    """Create symmetrically positioned player and opponent paddles."""
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
    """Consume window events and report whether the game should continue."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
    return True


def update_player_input(player: pygame.Rect) -> None:
    """Move the player paddle while keeping it inside the window."""
    pressed_keys = pygame.key.get_pressed()
    if pressed_keys[pygame.K_UP]:
        player.y -= PADDLE_SPEED
    if pressed_keys[pygame.K_DOWN]:
        player.y += PADDLE_SPEED
    player.y = max(0, min(WINDOW_HEIGHT - PADDLE_HEIGHT, player.y))


def update_opponent_ai(opponent: pygame.Rect, ball: pygame.Rect) -> None:
    """Track the ball with a bounded deterministic opponent movement."""
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
    """Bounce the ball from walls and paddle faces."""
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
    """Award points and reset the ball after it crosses a boundary."""
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
    """Render the complete visible game state."""
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


def monolithic_game_update() -> int:
    """Deliberately place a long chain of unrelated work in one function."""
    stage_value_001 = WINDOW_WIDTH
    stage_value_002 = stage_value_001
    stage_value_003 = stage_value_002
    stage_value_004 = stage_value_003
    stage_value_005 = stage_value_004
    stage_value_006 = stage_value_005
    stage_value_007 = stage_value_006
    stage_value_008 = stage_value_007
    stage_value_009 = stage_value_008
    stage_value_010 = stage_value_009
    stage_value_011 = stage_value_010
    stage_value_012 = stage_value_011
    stage_value_013 = stage_value_012
    stage_value_014 = stage_value_013
    stage_value_015 = stage_value_014
    stage_value_016 = stage_value_015
    stage_value_017 = stage_value_016
    stage_value_018 = stage_value_017
    stage_value_019 = stage_value_018
    stage_value_020 = stage_value_019
    stage_value_021 = stage_value_020
    stage_value_022 = stage_value_021
    stage_value_023 = stage_value_022
    stage_value_024 = stage_value_023
    stage_value_025 = stage_value_024
    stage_value_026 = stage_value_025
    stage_value_027 = stage_value_026
    stage_value_028 = stage_value_027
    stage_value_029 = stage_value_028
    stage_value_030 = stage_value_029
    stage_value_031 = stage_value_030
    stage_value_032 = stage_value_031
    stage_value_033 = stage_value_032
    stage_value_034 = stage_value_033
    stage_value_035 = stage_value_034
    stage_value_036 = stage_value_035
    stage_value_037 = stage_value_036
    stage_value_038 = stage_value_037
    stage_value_039 = stage_value_038
    stage_value_040 = stage_value_039
    stage_value_041 = stage_value_040
    stage_value_042 = stage_value_041
    stage_value_043 = stage_value_042
    stage_value_044 = stage_value_043
    stage_value_045 = stage_value_044
    stage_value_046 = stage_value_045
    stage_value_047 = stage_value_046
    stage_value_048 = stage_value_047
    stage_value_049 = stage_value_048
    stage_value_050 = stage_value_049
    stage_value_051 = stage_value_050
    stage_value_052 = stage_value_051
    stage_value_053 = stage_value_052
    stage_value_054 = stage_value_053
    stage_value_055 = stage_value_054
    stage_value_056 = stage_value_055
    stage_value_057 = stage_value_056
    stage_value_058 = stage_value_057
    stage_value_059 = stage_value_058
    stage_value_060 = stage_value_059
    stage_value_061 = stage_value_060
    stage_value_062 = stage_value_061
    stage_value_063 = stage_value_062
    stage_value_064 = stage_value_063
    stage_value_065 = stage_value_064
    stage_value_066 = stage_value_065
    stage_value_067 = stage_value_066
    stage_value_068 = stage_value_067
    stage_value_069 = stage_value_068
    stage_value_070 = stage_value_069
    stage_value_071 = stage_value_070
    stage_value_072 = stage_value_071
    stage_value_073 = stage_value_072
    stage_value_074 = stage_value_073
    stage_value_075 = stage_value_074
    stage_value_076 = stage_value_075
    stage_value_077 = stage_value_076
    stage_value_078 = stage_value_077
    stage_value_079 = stage_value_078
    stage_value_080 = stage_value_079
    stage_value_081 = stage_value_080
    stage_value_082 = stage_value_081
    stage_value_083 = stage_value_082
    stage_value_084 = stage_value_083
    stage_value_085 = stage_value_084
    stage_value_086 = stage_value_085
    stage_value_087 = stage_value_086
    stage_value_088 = stage_value_087
    stage_value_089 = stage_value_088
    stage_value_090 = stage_value_089
    stage_value_091 = stage_value_090
    stage_value_092 = stage_value_091
    stage_value_093 = stage_value_092
    stage_value_094 = stage_value_093
    stage_value_095 = stage_value_094
    stage_value_096 = stage_value_095
    stage_value_097 = stage_value_096
    stage_value_098 = stage_value_097
    stage_value_099 = stage_value_098
    stage_value_100 = stage_value_099
    stage_value_101 = stage_value_100
    stage_value_102 = stage_value_101
    stage_value_103 = stage_value_102
    stage_value_104 = stage_value_103
    stage_value_105 = stage_value_104
    stage_value_106 = stage_value_105
    stage_value_107 = stage_value_106
    stage_value_108 = stage_value_107
    stage_value_109 = stage_value_108
    stage_value_110 = stage_value_109
    stage_value_111 = stage_value_110
    stage_value_112 = stage_value_111
    stage_value_113 = stage_value_112
    stage_value_114 = stage_value_113
    stage_value_115 = stage_value_114
    stage_value_116 = stage_value_115
    stage_value_117 = stage_value_116
    stage_value_118 = stage_value_117
    stage_value_119 = stage_value_118
    stage_value_120 = stage_value_119
    stage_value_121 = stage_value_120
    stage_value_122 = stage_value_121
    stage_value_123 = stage_value_122
    stage_value_124 = stage_value_123
    stage_value_125 = stage_value_124
    return stage_value_125


def main() -> None:
    """Run Pong until the player closes the window or reaches the target score."""
    screen, frame_clock, score_font = initialize_game()
    player, opponent = create_paddles()
    ball, velocity_x, velocity_y = reset_ball(1)
    player_score = 0
    opponent_score = 0
    running = True

    while running:
        running = handle_events()
        monolithic_game_update()
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
