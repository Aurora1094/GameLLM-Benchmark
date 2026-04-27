import pygame
import sys
import random

pygame.init()

# 设置屏幕和颜色
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Breakout Medium")
white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)
blue = (0, 0, 255)
clock = pygame.time.Clock()

# 初始化变量
ball_pos = [400, 300]
ball_speed = [random.choice([-3, 3]), 3]
paddle_pos = [350, 560]
paddle_speed = 0
bricks = [[1 for _ in range(10)] for _ in range(5)]
score = 0
lives = 3
font = pygame.font.Font(None, 36)

def draw_bricks():
    for row in range(5):
        for col in range(10):
            if bricks[row][col]:
                pygame.draw.rect(screen, red, (col * 80, row * 30, 70, 20))

def move_ball():
    global ball_pos, ball_speed, score, lives

    ball_pos[0] += ball_speed[0]
    ball_pos[1] += ball_speed[1]

    if ball_pos[0] <= 0 or ball_pos[0] >= 790:
        ball_speed[0] = -ball_speed[0]
    if ball_pos[1] <= 0:
        ball_speed[1] = -ball_speed[1]

    if ball_pos[1] >= 590:
        lives -= 1
        reset_ball()

    if ball_pos[1] >= paddle_pos[1] - 10 and paddle_pos[0] <= ball_pos[0] <= paddle_pos[0] + 100:
        ball_speed[1] = -ball_speed[1]

    for row in range(5):
        for col in range(10):
            if bricks[row][col]:
                brick_rect = pygame.Rect(col * 80, row * 30, 70, 20)
                if brick_rect.colliderect(pygame.Rect(ball_pos[0], ball_pos[1], 10, 10)):
                    ball_speed[1] = -ball_speed[1]
                    bricks[row][col] = 0
                    score += 10

def reset_ball():
    global ball_pos, ball_speed
    ball_pos = [400, 300]
    ball_speed = [random.choice([-3, 3]), 3]

def game_over():
    screen.fill(black)
    text = font.render("Game Over! Press R to Restart", True, white)
    screen.blit(text, (200, 250))
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    global score, lives
                    score = 0
                    lives = 3
                    global bricks
                    bricks = [[1 for _ in range(10)] for _ in range(5)]
                    waiting = False

def victory():
    screen.fill(black)
    text = font.render("Victory! Press R to Restart", True, white)
    screen.blit(text, (200, 250))
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    global score, lives
                    score = 0
                    lives = 3
                    global bricks
                    bricks = [[1 for _ in range(10)] for _ in range(5)]
                    waiting = False

running = True
while running:
    screen.fill(black)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                paddle_speed = -5
            if event.key == pygame.K_RIGHT:
                paddle_speed = 5
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                paddle_speed = 0

    paddle_pos[0] += paddle_speed
    if paddle_pos[0] <= 0:
        paddle_pos[0] = 0
    if paddle_pos[0] >= 700:
        paddle_pos[0] = 700

    move_ball()
    pygame.draw.rect(screen, blue, (paddle_pos[0], paddle_pos[1], 100, 10))
    pygame.draw.circle(screen, white, (ball_pos[0], ball_pos[1]), 5)
    draw_bricks()

    score_text = font.render(f"Score: {score}", True, white)
    lives_text = font.render(f"Lives: {lives}", True, white)
    screen.blit(score_text, (10, 10))
    screen.blit(lives_text, (10, 40))

    if lives <= 0:
        game_over()
    if all(all(row) for row in bricks):
        victory()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()