import pygame
import time
import random

# 初始化 Pygame
pygame.init()

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
DARK_GREEN = (0, 150, 0)

# 显示窗口设置
WIDTH, HEIGHT = 600, 400
BLOCK_SIZE = 20
GAME_SPEED = 10  # FPS

# 创建屏幕
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Easy")

clock = pygame.time.Clock()
font_style = pygame.font.SysFont("bahnschrift", 25)
score_font = pygame.font.SysFont("comicsansms", 35)

def show_score(score):
    score_value = score_font.render("Score: " + str(score), True, BLACK)
    screen.blit(score_value, [10, 10])

def draw_snake(snake_body):
    for x, y in snake_body:
        pygame.draw.rect(screen, DARK_GREEN, [x, y, BLOCK_SIZE, BLOCK_SIZE])
        pygame.draw.rect(screen, GREEN, [x+2, y+2, BLOCK_SIZE-4, BLOCK_SIZE-4])

def draw_food(food_x, food_y):
    pygame.draw.rect(screen, RED, [food_x, food_y, BLOCK_SIZE, BLOCK_SIZE])

def message(msg, color):
    mesg = font_style.render(msg, True, color)
    screen.blit(mesg, [WIDTH / 6, HEIGHT / 3])

def generate_food():
    food_x = round(random.randrange(0, WIDTH - BLOCK_SIZE) / BLOCK_SIZE) * BLOCK_SIZE
    food_y = round(random.randrange(0, HEIGHT - BLOCK_SIZE) / BLOCK_SIZE) * BLOCK_SIZE
    return food_x, food_y

def game_loop():
    game_over = False
    game_close = False

    # 初始蛇的位置
    x, y = WIDTH // 2, HEIGHT // 2
    x_change = 0
    y_change = 0

    snake_body = []
    length_of_snake = 1

    # 食物位置
    food_x, food_y = generate_food()

    score = 0

    while not game_over:
        while game_close:
            screen.fill(WHITE)
            message("You Lost! Press Q-Quit or C-Play Again", RED)
            show_score(score)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over = True
                        game_close = False
                    if event.key == pygame.K_c:
                        game_loop()
                elif event.type == pygame.QUIT:
                    game_over = True
                    game_close = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and x_change != BLOCK_SIZE:
                    x_change = -BLOCK_SIZE
                    y_change = 0
                elif event.key == pygame.K_RIGHT and x_change != -BLOCK_SIZE:
                    x_change = BLOCK_SIZE
                    y_change = 0
                elif event.key == pygame.K_UP and y_change != BLOCK_SIZE:
                    y_change = -BLOCK_SIZE
                    x_change = 0
                elif event.key == pygame.K_DOWN and y_change != -BLOCK_SIZE:
                    y_change = BLOCK_SIZE
                    x_change = 0

        # 蛇头移动
        if x >= WIDTH or x < 0 or y >= HEIGHT or y < 0:
            game_close = True
        x += x_change
        y += y_change

        screen.fill(WHITE)
        
        # 绘制食物
        draw_food(food_x, food_y)
        
        # 更新蛇身
        snake_head = [x, y]
        snake_body.append(snake_head)
        
        if len(snake_body) > length_of_snake:
            del snake_body[0]

        # 检查自我碰撞
        for segment in snake_body[:-1]:
            if segment == snake_head:
                game_close = True

        draw_snake(snake_body)
        show_score(score)
        pygame.display.update()

        # 吃食物
        if x == food_x and y == food_y:
            food_x, food_y = generate_food()
            length_of_snake += 1
            score += 10

        clock.tick(GAME_SPEED)

    pygame.quit()
    quit()

# 启动游戏
game_loop()