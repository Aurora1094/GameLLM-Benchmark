import pygame
import sys
import random

# 初始化 Pygame
pygame.init()

# 游戏常量
BLOCK_SIZE = 20
GRID_WIDTH = 30
GRID_HEIGHT = 20
SCREEN_WIDTH = BLOCK_SIZE * GRID_WIDTH
SCREEN_HEIGHT = BLOCK_SIZE * GRID_HEIGHT
FPS = 10
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 100, 0)
BLUE = (0, 0, 255)

# 创建显示界面
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake Easy")

# 时钟控制帧率
clock = pygame.time.Clock()

# 字体设置
font = pygame.font.SysFont(None, 36)


def draw_text(text, color, x, y, center=False):
    """在指定位置绘制文字"""
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(text_surface, rect)


def get_food_position(snake):
    """生成不与蛇身重叠的食物位置"""
    while True:
        x = random.randint(0, GRID_WIDTH - 1)
        y = random.randint(0, GRID_HEIGHT - 1)
        if (x, y) not in snake:
            return (x, y)


def draw_snake(snake):
    """绘制蛇"""
    for i, (x, y) in enumerate(snake):
        color = DARK_GREEN if i == 0 else GREEN
        rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
        pygame.draw.rect(screen, color, rect)
        pygame.draw.rect(screen, BLACK, rect, 1)


def draw_food(food):
    """绘制食物"""
    x, y = food
    rect = pygame.Rect(x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE)
    pygame.draw.rect(screen, RED, rect)
    pygame.draw.rect(screen, BLACK, rect, 1)


def main():
    # 初始化游戏状态
    snake = [(10, 10), (9, 10), (8, 10)]  # 蛇身坐标列表
    direction = (1, 0)  # 初始方向：向右
    next_direction = (1, 0)
    food = get_food_position(snake)
    score = 0
    game_over = False

    # 游戏主循环
    while True:
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and direction != (0, 1):
                    next_direction = (0, -1)
                elif event.key == pygame.K_DOWN and direction != (0, -1):
                    next_direction = (0, 1)
                elif event.key == pygame.K_LEFT and direction != (1, 0):
                    next_direction = (-1, 0)
                elif event.key == pygame.K_RIGHT and direction != (-1, 0):
                    next_direction = (1, 0)
                elif event.key == pygame.K_r and game_over:
                    # 重新开始游戏
                    main()
                    return
                elif event.key == pygame.K_q and game_over:
                    pygame.quit()
                    sys.exit()

        if game_over:
            # 游戏结束界面
            screen.fill(BLACK)
            draw_text("GAME OVER", RED, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50, center=True)
            draw_text(f"Score: {score}", WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, center=True)
            draw_text("Press 'R' to Restart or 'Q' to Quit", WHITE, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50, center=True)
            pygame.display.flip()
            clock.tick(FPS)
            continue

        # 更新方向
        direction = next_direction

        # 计算新蛇头位置
        head_x, head_y = snake[0]
        dx, dy = direction
        new_head = ((head_x + dx) % GRID_WIDTH, (head_y + dy) % GRID_HEIGHT)

        # 检查撞到自己
        if new_head in snake:
            game_over = True
            continue

        # 将新蛇头加入蛇身
        snake.insert(0, new_head)

        # 检查是否吃到食物
        if new_head == food:
            score += 1
            food = get_food_position(snake)
        else:
            # 移除蛇尾
            snake.pop()

        # 绘制画面
        screen.fill(BLACK)
        draw_snake(snake)
        draw_food(food)
        draw_text(f"Score: {score}", WHITE, 10, 10)
        pygame.display.flip()

        # 控制帧率
        clock.tick(FPS)


if __name__ == "__main__":
    main()