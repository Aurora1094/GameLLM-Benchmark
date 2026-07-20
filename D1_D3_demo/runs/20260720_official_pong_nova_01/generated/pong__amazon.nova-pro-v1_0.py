import pygame
import sys
import time

pygame.init()

SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
PADDLE_WIDTH, PADDLE_HEIGHT = 10, 100
BALL_SIZE = 10
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FONT = pygame.font.Font(None, 36)
TARGET_SCORE = 5
GAME_DURATION = 120

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pong")

class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = 5

    def move(self, direction):
        if direction == "up":
            self.rect.y -= self.speed
        elif direction == "down":
            self.rect.y += self.speed
        self.rect.y = max(0, min(self.rect.y, SCREEN_HEIGHT - PADDLE_HEIGHT))

class Ball:
    def __init__(self):
        self.rect = pygame.Rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, BALL_SIZE, BALL_SIZE)
        self.speed_x = 5
        self.speed_y = 5

    def move(self):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        if self.rect.top <= 0 or self.rect.bottom >= SCREEN_HEIGHT:
            self.speed_y *= -1
        if self.rect.left <= 0:
            return 1
        if self.rect.right >= SCREEN_WIDTH:
            return -1
        return 0

    def reset(self):
        self.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.speed_x *= -1

def draw_objects(paddles, ball):
    screen.fill(BLACK)
    for paddle in paddles:
        pygame.draw.rect(screen, WHITE, paddle.rect)
    pygame.draw.ellipse(screen, WHITE, ball.rect)
    pygame.display.flip()

def main():
    clock = pygame.time.Clock()
    start_time = time.time()
    left_paddle = Paddle(30, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2)
    right_paddle = Paddle(SCREEN_WIDTH - 40, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2)
    ball = Ball()
    left_score = 0
    right_score = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            left_paddle.move("up")
        if keys[pygame.K_DOWN]:
            left_paddle.move("down")

        if ball.rect.colliderect(left_paddle.rect) or ball.rect.colliderect(right_paddle.rect):
            ball.speed_x *= -1

        score = ball.move()
        if score == 1:
            right_score += 1
            ball.reset()
        elif score == -1:
            left_score += 1
            ball.reset()

        if right_paddle.rect.centery < ball.rect.centery:
            right_paddle.move("down")
        elif right_paddle.rect.centery > ball.rect.centery:
            right_paddle.move("up")

        draw_objects([left_paddle, right_paddle], ball)
        screen.blit(FONT.render(f"{left_score} - {right_score}", True, WHITE), (SCREEN_WIDTH // 2 - 20, 10))

        if left_score >= TARGET_SCORE or right_score >= TARGET_SCORE or time.time() - start_time >= GAME_DURATION:
            winner = "Left" if left_score > right_score else "Right"
            screen.blit(FONT.render(f"{winner} Wins!", True, WHITE), (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 - 20))
            pygame.display.flip()
            pygame.time.wait(2000)
            break

        clock.tick(60)

if __name__ == "__main__":
    main()
