import pygame
import random
import sys

# 初始化 Pygame
pygame.init()

# 游戏 constants
BLOCK_SIZE = 20
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
FPS = 10

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (213, 50, 80)
GREEN = (0, 255, 0)
BLUE = (50, 153, 213)

# 创建游戏窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Snake Easy')
clock = pygame.time.Clock()

# 字体
font_style = pygame.font.SysFont("bahnschrift", 25)
score_font = pygame.font.SysFont("comicsansms", 20)


def show_score(score):
    """显示当前得分"""
    value = score_font.render("Score: " + str(score), True, GREEN)
    screen.blit(value, [10, 10])


def message(msg, color, y_displace=0):
    """显示游戏信息"""
    mesg = font_style.render(msg, True, color)
    text_rect = mesg.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + y_displace))
    screen.blit(mesg, text_rect)


def generate_food(snake_list):
    """生成不在蛇身上的食物"""
    while True:
        food_x = round(random.randrange(0, SCREEN_WIDTH - BLOCK_SIZE) / BLOCK_SIZE) * BLOCK_SIZE
        food_y = round(random.randrange(0, SCREEN_HEIGHT - BLOCK_SIZE) / BLOCK_SIZE) * BLOCK_SIZE
        # 检查是否生成在蛇身上
        for segment in snake_list:
            if segment[0] == food_x and segment[1] == food_y:
                break
        else:
            return [food_x, food_y]


def game_loop():
    game_over = False
    game_close = False

    # 蛇的初始位置
    x1 = SCREEN_WIDTH // 2
    y1 = SCREEN_HEIGHT // 2
    x1_change = 0
    y1_change = 0

    snake_list = []
    snake_length = 1

    # 食物
    food_pos = generate_food(snake_list)

    score = 0

    while not game_over:
        while game_close:
            screen.fill(BLACK)
            message("Game Over!", RED, -20)
            message("Press Q-quit or C-play again", WHITE, 20)
            show_score(score)
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_over = True
                    game_close = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over = True
                        game_close = False
                    elif event.key == pygame.K_c:
                        game_loop()
                        return

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_over = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and x1_change == 0:
                    x1_change = -BLOCK_SIZE
                    y1_change = 0
                elif event.key == pygame.K_RIGHT and x1_change == 0:
                    x1_change = BLOCK_SIZE
                    y1_change = 0
                elif event.key == pygame.K_UP and y1_change == 0:
                    y1_change = -BLOCK_SIZE
                    x1_change = 0
                elif event.key == pygame.K_DOWN and y1_change == 0:
                    y1_change = BLOCK_SIZE
                    x1_change = 0

        # 检查是否撞墙
        if x1 >= SCREEN_WIDTH or x1 < 0 or y1 >= SCREEN_HEIGHT or y1 < 0:
            game_close = True
            continue

        # 更新蛇的位置
        x1 += x1_change
        y1 += y1_change

        # 清空屏幕
        screen.fill(BLACK)

        # 绘制食物
        pygame.draw.rect(screen, RED, [food_pos[0], food_pos[1], BLOCK_SIZE, BLOCK_SIZE])

        # 更新蛇的身体
        snake_head = [x1, y1]
        snake_list.append(snake_head)

        # 移除多余的身体段
        if len(snake_list) > snake_length:
            del snake_list[0]

        # 检查是否撞到自己
        for segment in snake_list[:-1]:
            if segment[0] == x1 and segment[1] == y1:
                game_close = True
                break

        # 绘制蛇
        for segment in snake_list:
            pygame.draw.rect(screen, BLUE, [segment[0], segment[1], BLOCK_SIZE, BLOCK_SIZE])

        # 检查是否吃食物
        if x1 == food_pos[0] and y1 == food_pos[1]:
            food_pos = generate_food(snake_list)
            snake_length += 1
            score += 10

        show_score(score)
        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    game_loop()