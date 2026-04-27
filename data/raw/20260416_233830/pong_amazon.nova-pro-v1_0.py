import pygame
import random
import sys

pygame.init()
random.seed(42)

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
PADDLE_WIDTH, PADDLE_HEIGHT = 18, 100
BALL_SIZE = 18
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FONT = pygame.font.Font(None, 36)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pong Easy")
clock = pygame.time.Clock()

def draw_objects(left_paddle, right_paddle, ball, left_score, right_score):
    screen.fill(BLACK)
    pygame.draw.rect(screen, WHITE, left_paddle)
    pygame.draw.rect(screen, WHITE, right_paddle)
    pygame.draw.ellipse(screen, WHITE, ball)
    pygame.draw.aaline(screen, WHITE, (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT))
    left_score_surface = FONT.render(str(left_score), True, WHITE)
    right_score_surface = FONT.render(str(right_score), True, WHITE)
    screen.blit(left_score_surface, (SCREEN_WIDTH // 4, 20))
    screen.blit(right_score_surface, (3 * SCREEN_WIDTH // 4, 20))

def show_winner(winner):
    screen.fill(BLACK)
    winner_surface = FONT.render(f"{winner} wins!", True, WHITE)
    screen.blit(winner_surface, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 - 20))
    restart_surface = FONT.render("Press R to Restart", True, WHITE)
    screen.blit(restart_surface, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 20))
    pygame.display.flip()

def reset_ball():
    return pygame.Rect(SCREEN_WIDTH // 2 - BALL_SIZE // 2, SCREEN_HEIGHT // 2 - BALL_SIZE // 2, BALL_SIZE, BALL_SIZE)

def main():
    left_paddle = pygame.Rect(50, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
    right_paddle = pygame.Rect(SCREEN_WIDTH - 50 - PADDLE_WIDTH, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT)
    ball = reset_ball()
    ball_speed_x, ball_speed_y = 5, 5
    if random.randint(0, 1) == 0:
        ball_speed_x = -ball_speed_x
    left_score, right_score = 0, 0
    game_running = True
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_r:
                    left_paddle.y = SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2
                    right_paddle.y = SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2
                    ball = reset_ball()
                    left_score, right_score = 0, 0
                    game_running = True

        if game_running:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w] and left_paddle.top > 0:
                left_paddle.y -= 7
            if keys[pygame.K_s] and left_paddle.bottom < SCREEN_HEIGHT:
                left_paddle.y += 7
            if keys[pygame.K_UP] and right_paddle.top > 0:
                right_paddle.y -= 7
            if keys[pygame.K_DOWN] and right_paddle.bottom < SCREEN_HEIGHT:
                right_paddle.y += 7

            ball.x += ball_speed_x
            ball.y += ball_speed_y

            if ball.top <= 0 or ball.bottom >= SCREEN_HEIGHT:
                ball_speed_y = -ball_speed_y
            if ball.colliderect(left_paddle) or ball.colliderect(right_paddle):
                ball_speed_x = -ball_speed_x

            if ball.left <= 0:
                right_score += 1
                ball = reset_ball()
                ball_speed_x, ball_speed_y = 5, 5
                if random.randint(0, 1) == 0:
                    ball_speed_x = -ball_speed_x
            elif ball.right >= SCREEN_WIDTH:
                left_score += 1
                ball = reset_ball()
                ball_speed_x, ball_speed_y = 5, 5
                if random.randint(0, 1) == 0:
                    ball_speed_x = -ball_speed_x

            if left_score == 7 or right_score == 7:
                game_running = False
                if left_score == 7:
                    show_winner("Left")
                else:
                    show_winner("Right")

        draw_objects(left_paddle, right_paddle, ball, left_score, right_score)
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()