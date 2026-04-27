import pygame
import sys
import random

# 初始化 Pygame
pygame.init()

# 屏幕设置
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 400
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
GRAY = (50, 50, 50)

# 创建屏幕
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake Easy")

# FPS 控制
clock = pygame.time.Clock()
FPS = 10

# 游戏状态
game_over = False
score = 0
high_score = 0

# 蛇初始化
snake = [(10, 10), (9, 10), (8, 10)]
snake_direction = (1, 0)  # 初始方向：向右
next_direction = (1, 0)

# 食物初始化
food = (15, 15)


def generate_food():
    """生成不在蛇身上的食物"""
    while True:
        x = random.randint(0, GRID_WIDTH - 1)
        y = random.randint(0, GRID_HEIGHT - 1)
        if (x, y) not in snake:
            return (x, y)


def reset_game():
    """重置游戏"""
    global snake, snake_direction, next_direction, food, score, game_over
    snake = [(10, 10), (9, 10), (8, 10)]
    snake_direction = (1, 0)
    next_direction = (1, 0)
    food = generate_food()
    score = 0
    game_over = False


def draw_text(text, font, color, x, y):
    """渲染文字"""
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, (x, y))


# 字体设置
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)

# 主循环
while True:
    # 事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if game_over:
                if event.key == pygame.K_r:
                    reset_game()
            else:
                # 改变方向（防止直接反向）
                if event.key == pygame.K_UP and snake_direction != (0, 1):
                    next_direction = (0, -1)
                elif event.key == pygame.K_DOWN and snake_direction != (0, -1):
                    next_direction = (0, 1)
                elif event.key == pygame.K_LEFT and snake_direction != (1, 0):
                    next_direction = (-1, 0)
                elif event.key == pygame.K_RIGHT and snake_direction != (-1, 0):
                    next_direction = (1, 0)

    if not game_over:
        # 更新蛇方向
        snake_direction = next_direction
        
        # 计算新蛇头位置
        head_x, head_y = snake[0]
        dx, dy = snake_direction
        new_head = ((head_x + dx) % GRID_WIDTH, (head_y + dy) % GRID_HEIGHT)
        
        # 检查碰撞自己
        if new_head in snake:
            game_over = True
            if score > high_score:
                high_score = score
        
        # 更新蛇
        snake.insert(0, new_head)
        
        # 检查吃食物
        if new_head == food:
            score += 1
            food = generate_food()
        else:
            snake.pop()  # 移除尾部

    # 绘制背景
    screen.fill(BLACK)
    
    # 画网格（可选）
    for x in range(0, SCREEN_WIDTH, GRID_SIZE):
        pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y))
    
    # 画食物
    pygame.draw.rect(screen, RED, (food[0]*GRID_SIZE, food[1]*GRID_SIZE, GRID_SIZE, GRID_SIZE))
    
    # 画蛇
    for segment in snake:
        pygame.draw.rect(screen, GREEN, (segment[0]*GRID_SIZE, segment[1]*GRID_SIZE, GRID_SIZE, GRID_SIZE))
    
    # 显示得分
    draw_text(f"Score: {score}", small_font, WHITE, 10, 10)
    draw_text(f"High Score: {high_score}", small_font, WHITE, SCREEN_WIDTH - 180, 10)
    
    # 游戏结束画面
    if game_over:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        draw_text("GAME OVER", font, WHITE, SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 50)
        draw_text(f"Final Score: {score}", small_font, WHITE, SCREEN_WIDTH//2 - 75, SCREEN_HEIGHT//2 + 10)
        draw_text("Press 'R' to Restart", small_font, WHITE, SCREEN_WIDTH//2 - 120, SCREEN_HEIGHT//2 + 50)
    
    # 更新显示
    pygame.display.flip()
    
    # 控制帧率
    clock.tick(FPS)