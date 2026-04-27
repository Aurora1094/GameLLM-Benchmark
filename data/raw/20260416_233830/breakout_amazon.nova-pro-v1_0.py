import pygame
import random
import sys

pygame.init()
random.seed(42)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
PADDLE_WIDTH = 110
PADDLE_HEIGHT = 18
BALL_SIZE = 16
BRICK_ROWS = 5
BRICK_COLS = 8
BRICK_WIDTH = 84
BRICK_HEIGHT = 24
BRICK_PADDING_X = 10
BRICK_PADDING_Y = 10
BALL_INITIAL_SPEED = [4, -5]
PADDLE_SPEED = 8
LIVES = 3
SCORE_PER_BRICK = 10

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Breakout Medium")
clock = pygame.time.Clock()

font = pygame.font.Font(None, 36)

def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

def reset_game():
    global paddle, ball, ball_speed, bricks, score, lives, game_over, game_won
    paddle = pygame.Rect(SCREEN_WIDTH // 2 - PADDLE_WIDTH // 2, SCREEN_HEIGHT - PADDLE_HEIGHT - 10, PADDLE_WIDTH, PADDLE_HEIGHT)
    ball = pygame.Rect(paddle.centerx - BALL_SIZE // 2, paddle.top - BALL_SIZE, BALL_SIZE, BALL_SIZE)
    ball_speed = list(BALL_INITIAL_SPEED)
    bricks = [pygame.Rect(BRICK_PADDING_X + (BRICK_WIDTH + BRICK_PADDING_X) * i, BRICK_PADDING_Y + (BRICK_HEIGHT + BRICK_PADDING_Y) * j, BRICK_WIDTH, BRICK_HEIGHT) for i in range(BRICK_COLS) for j in range(BRICK_ROWS)]
    score = 0
    lives = LIVES
    game_over = False
    game_won = False

reset_game()

running = True
while running:
    screen.fill(BLACK)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_r:
                reset_game()
    
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and paddle.left > 0:
        paddle.move_ip(-PADDLE_SPEED, 0)
    if keys[pygame.K_RIGHT] and paddle.right < SCREEN_WIDTH:
        paddle.move_ip(PADDLE_SPEED, 0)
    
    ball.move_ip(ball_speed)
    
    if ball.left <= 0 or ball.right >= SCREEN_WIDTH:
        ball_speed[0] = -ball_speed[0]
    if ball.top <= 0:
        ball_speed[1] = -ball_speed[1]
    if ball.colliderect(paddle):
        ball_speed[1] = -ball_speed[1]
    
    if ball.bottom >= SCREEN_HEIGHT:
        lives -= 1
        if lives == 0:
            game_over = True
        else:
            ball.center = (paddle.centerx, paddle.top - BALL_SIZE)
            ball_speed = list(BALL_INITIAL_SPEED)
    
    hit_index = ball.collidelist(bricks)
    if hit_index!= -1:
        hbrick = bricks.pop(hit_index)
        if ball.centery < hbrick.centery:
            ball_speed[1] = -abs(ball_speed[1])
        else:
            ball_speed[1] = abs(ball_speed[1])
        ball_speed[0] = -ball_speed[0]
        score += SCORE_PER_BRICK
    
    if len(bricks) == 0:
        game_won = True
    
    if not game_over and not game_won:
        pygame.draw.rect(screen, WHITE, paddle)
        pygame.draw.ellipse(screen, WHITE, ball)
        for brick in bricks:
            pygame.draw.rect(screen, GREEN, brick)
    else:
        if game_won:
            draw_text("You Win! Press R to Restart", font, WHITE, screen, 200, SCREEN_HEIGHT // 2 - 30)
        else:
            draw_text("Game Over! Press R to Restart", font, WHITE, screen, 200, SCREEN_HEIGHT // 2 - 30)
    
    draw_text(f"Score: {score}", font, WHITE, screen, 10, 10)
    draw_text(f"Lives: {lives}", font, WHITE, screen, 10, 50)
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()