import pygame
import random
import sys

# 初始化配置
pygame.init()
random.seed(42)

# 窗口设置
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

# 颜色定义
BACKGROUND_COLOR = (15, 15, 25)
GRID_COLOR = (40, 40, 60)
SNAKE_HEAD_COLOR = (50, 205, 50)  # 蛇头
SNAKE_BODY_COLOR = (144, 238, 144)  # 蛇身
FOOD_COLOR = (220, 60, 60)
TEXT_COLOR = (240, 240, 240)
GAME_OVER_BG = (0, 0, 0, 180)  # 半透明黑色

# 游戏网格参数
GRID_WIDTH = 600
GRID_HEIGHT = 480
GRID_LEFT = (WINDOW_WIDTH - GRID_WIDTH) // 2
GRID_TOP = (WINDOW_HEIGHT - GRID_HEIGHT) // 2
GRID_COLS = 30
GRID_ROWS = 24
CELL_SIZE = 20

# 游戏参数
SNAKE_SPEED = 10  # 每秒移动网格数
INIT_SNAKE_LENGTH = 3
FOOD_SCORE = 10

# 初始化窗口和时钟
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Snake Easy")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 28)

def draw_grid():
    """绘制网格"""
    for x in range(GRID_COLS + 1):
        pygame.draw.line(screen, GRID_COLOR,
                         (GRID_LEFT + x * CELL_SIZE, GRID_TOP),
                         (GRID_LEFT + x * CELL_SIZE, GRID_TOP + GRID_HEIGHT), 1)
    for y in range(GRID_ROWS + 1):
        pygame.draw.line(screen, GRID_COLOR,
                         (GRID_LEFT, GRID_TOP + y * CELL_SIZE),
                         (GRID_LEFT + GRID_WIDTH, GRID_TOP + y * CELL_SIZE), 1)

def game_loop():
    # 蛇初始位置在网格中心附近
    start_col = GRID_COLS // 2
    start_row = GRID_ROWS // 2
    snake = []
    for i in range(INIT_SNAKE_LENGTH):
        snake.append((start_col - i, start_row))
    
    direction = (1, 0)  # 初始向右
    next_direction = (1, 0)
    food = None
    score = 0
    game_over = False
    
    # 生成第一个食物
    def generate_food():
        while True:
            col = random.randint(0, GRID_COLS - 1)
            row = random.randint(0, GRID_ROWS - 1)
            if (col, row) not in snake:
                return (col, row)
    
    food = generate_food()
    
    # 计算移动间隔（帧数）
    move_interval = FPS // SNAKE_SPEED
    move_counter = 0
    
    running = True
    while running:
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif event.key == pygame.K_r:
                    return  # 重新开始
                elif not game_over:
                    # 方向键控制
                    if event.key == pygame.K_UP and direction != (0, 1):
                        next_direction = (0, -1)
                    elif event.key == pygame.K_DOWN and direction != (0, -1):
                        next_direction = (0, 1)
                    elif event.key == pygame.K_LEFT and direction != (1, 0):
                        next_direction = (-1, 0)
                    elif event.key == pygame.K_RIGHT and direction != (-1, 0):
                        next_direction = (1, 0)
        
        if not game_over:
            # 蛇移动逻辑
            move_counter += 1
            if move_counter >= move_interval:
                move_counter = 0
                direction = next_direction
                
                # 计算新头部位置
                head_col, head_row = snake[0]
                new_head = (head_col + direction[0], head_row + direction[1])
                
                # 检查是否撞墙
                if (new_head[0] < 0 or new_head[0] >= GRID_COLS or
                    new_head[1] < 0 or new_head[1] >= GRID_ROWS):
                    game_over = True
                # 检查是否撞到自己
                elif new_head in snake:
                    game_over = True
                else:
                    # 移动蛇
                    snake.insert(0, new_head)
                    
                    # 检查是否吃到食物
                    if new_head == food:
                        score += FOOD_SCORE
                        food = generate_food()
                    else:
                        snake.pop()
        
        # 绘制
        screen.fill(BACKGROUND_COLOR)
        
        # 绘制网格背景区域
        grid_rect = pygame.Rect(GRID_LEFT, GRID_TOP, GRID_WIDTH, GRID_HEIGHT)
        pygame.draw.rect(screen, (25, 25, 35), grid_rect)
        draw_grid()
        
        # 绘制食物
        if food:
            food_rect = pygame.Rect(
                GRID_LEFT + food[0] * CELL_SIZE,
                GRID_TOP + food[1] * CELL_SIZE,
                CELL_SIZE, CELL_SIZE
            )
            pygame.draw.rect(screen, FOOD_COLOR, food_rect)
        
        # 绘制蛇
        for i, (col, row) in enumerate(snake):
            snake_rect = pygame.Rect(
                GRID_LEFT + col * CELL_SIZE,
                GRID_TOP + row * CELL_SIZE,
                CELL_SIZE, CELL_SIZE
            )
            color = SNAKE_HEAD_COLOR if i == 0 else SNAKE_BODY_COLOR
            pygame.draw.rect(screen, color, snake_rect)
            # 蛇身边框
            if i > 0:
                pygame.draw.rect(screen, (30, 120, 30), snake_rect, 1)
        
        # 绘制分数
        score_text = font.render(f"Score: {score}", True, TEXT_COLOR)
        screen.blit(score_text, (20, 20))
        
        # 绘制标题
        title_text = font.render("Snake Easy", True, TEXT_COLOR)
        screen.blit(title_text, (WINDOW_WIDTH - title_text.get_width() - 20, 20))
        
        # 绘制操作提示
        controls_text = small_font.render("Arrow Keys: Move | R: Restart | ESC: Exit", True, (180, 180, 180))
        screen.blit(controls_text, (WINDOW_WIDTH // 2 - controls_text.get_width() // 2, GRID_TOP - 40))
        
        # 游戏结束提示
        if game_over:
            # 半透明覆盖层
            overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
            overlay.fill(GAME_OVER_BG)
            screen.blit(overlay, (0, 0))
            
            game_over_text = font.render("Game Over", True, (255, 50, 50))
            final_score_text = font.render(f"Final Score: {score}", True, TEXT_COLOR)
            restart_text = small_font.render("Press R to Restart", True, (200, 200, 100))
            
            screen.blit(game_over_text, (WINDOW_WIDTH // 2 - game_over_text.get_width() // 2, WINDOW_HEIGHT // 2 - 50))
            screen.blit(final_score_text, (WINDOW_WIDTH // 2 - final_score_text.get_width() // 2, WINDOW_HEIGHT // 2))
            screen.blit(restart_text, (WINDOW_WIDTH // 2 - restart_text.get_width() // 2, WINDOW_HEIGHT // 2 + 50))
        
        pygame.display.flip()
        clock.tick(FPS)

# 主游戏循环
while True:
    game_loop()