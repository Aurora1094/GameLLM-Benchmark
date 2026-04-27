import pygame
import sys

pygame.init()

width, height = 800, 600
win = pygame.display.set_mode((width, height))
pygame.display.set_caption("Pong Easy")

white = (255, 255, 255)
black = (0, 0, 0)

paddle_width, paddle_height = 10, 100
ball_size = 20
ball_radius = ball_size // 2
paddle_speed = 7
ball_speed_x, ball_speed_y = 7 * pygame.math.Vector2(1, 1).normalize()

left_paddle = pygame.Rect(30, height // 2 - paddle_height // 2, paddle_width, paddle_height)
right_paddle = pygame.Rect(width - 30 - paddle_width, height // 2 - paddle_height // 2, paddle_width, paddle_height)
ball = pygame.Rect(width // 2 - ball_radius, height // 2 - ball_radius, ball_size, ball_size)

left_score = 0
right_score = 0
font = pygame.font.Font(None, 74)

def draw_objects():
    win.fill(black)
    pygame.draw.rect(win, white, left_paddle)
    pygame.draw.rect(win, white, right_paddle)
    pygame.draw.ellipse(win, white, ball)
    pygame.draw.aaline(win, white, (width // 2, 0), (width // 2, height))
    left_text = font.render(str(left_score), True, white)
    right_text = font.render(str(right_score), True, white)
    win.blit(left_text, (250, 50))
    win.blit(right_text, (550, 50))
    pygame.display.update()

def move_paddles(keys):
    if keys[pygame.K_w] and left_paddle.top > 0:
        left_paddle.y -= paddle_speed
    if keys[pygame.K_s] and left_paddle.bottom < height:
        left_paddle.y += paddle_speed
    if keys[pygame.K_UP] and right_paddle.top > 0:
        right_paddle.y -= paddle_speed
    if keys[pygame.K_DOWN] and right_paddle.bottom < height:
        right_paddle.y += paddle_speed

def move_ball():
    global ball_speed_x, ball_speed_y, left_score, right_score
    ball.x += ball_speed_x * 7
    ball.y += ball_speed_y * 7
    if ball.top <= 0 or ball.bottom >= height:
        ball_speed_y *= -1
    if ball.colliderect(left_paddle) or ball.colliderect(right_paddle):
        ball_speed_x *= -1
    if ball.left <= 0:
        right_score += 1
        ball_reset()
    if ball.right >= width:
        left_score += 1
        ball_reset()

def ball_reset():
    global ball_speed_x, ball_speed_y
    ball.center = (width // 2, height // 2)
    ball_speed_x *= -1
    ball_speed_y *= -1

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    keys = pygame.key.get_pressed()
    move_paddles(keys)
    move_ball()
    draw_objects()
    if left_score >= 5 or right_score >= 5:
        win_text = font.render("Left Win" if left_score >= 5 else "Right Win", True, white)
        win.blit(win_text, (width // 2 - 100, height // 2 - 50))
        pygame.display.update()
        pygame.time.delay(3000)
        pygame.quit()
        sys.exit()
    clock.tick(60)