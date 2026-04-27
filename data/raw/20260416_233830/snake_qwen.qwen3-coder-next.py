import pygame
import random
import sys

# 常量定义
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
GRID_COLS = 30
GRID_ROWS = 24
GRID_SIZE = 20
GAME_WIDTH = GRID_COLS * GRID_SIZE
GAME_HEIGHT = GRID_ROWS * GRID_SIZE
FPS = 60
SNAKE_SPEED = 10  # grids per second
SCORE_PER_FOOD = 10

# 颜色
BG_COLOR = (20, 20, 30)
GRID_COLOR = (40, 40, 50)
SNAKE_HEAD_COLOR = (0, 255, 0)
SNAKE_BODY_COLOR = (0, 200, 0)
FOOD_COLOR = (255, 0, 0)
TEXT_COLOR = (255, 255, 255)
HUD_BG_COLOR = (30, 30, 40)
HUD_BORDER_COLOR = (100, 100, 120)

# 屏幕居中计算
GAME_X = (WINDOW_WIDTH - GAME_WIDTH) // 2
GAME_Y = (WINDOW_HEIGHT - GAME_HEIGHT) // 2

# 初始化
random.seed(42)
pygame.init()
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Snake Easy")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)


def create_grid():
    """创建一个空的网格"""
    return [[False] * GRID_COLS for _ in range(GRID_ROWS)]


def spawn_food(snake):
    """在蛇身之外随机生成食物"""
    while True:
        x = random.randint(0, GRID_COLS - 1)
        y = random.randint(0, GRID_ROWS - 1)
        if (x, y) not in snake:
            return x, y


def draw_grid(surface):
    """绘制网格线"""
    for x in range(GRID_COLS + 1):
        pygame.draw.line(surface, GRID_COLOR,
                         (GAME_X + x * GRID_SIZE, GAME_Y),
                         (GAME_X + x * GRID_SIZE, GAME_Y + GAME_HEIGHT))
    for y in range(GRID_ROWS + 1):
        pygame.draw.line(surface, GRID_COLOR,
                         (GAME_X, GAME_Y + y * GRID_SIZE),
                         (GAME_X + GAME_WIDTH, GAME_Y + y * GRID_SIZE))


def draw_snake(surface, snake):
    """绘制蛇身"""
    for i, (x, y) in enumerate(snake):
        rect = pygame.Rect(GAME_X + x * GRID_SIZE,
                          GAME_Y + y * GRID_SIZE,
                          GRID_SIZE, GRID_SIZE)
        if i == 0:
            color = SNAKE_HEAD_COLOR
        else:
            color = SNAKE_BODY_COLOR
        pygame.draw.rect(surface, color, rect)


def draw_food(surface, food_x, food_y):
    """绘制食物"""
    rect = pygame.Rect(GAME_X + food_x * GRID_SIZE,
                      GAME_Y + food_y * GRID_SIZE,
                      GRID_SIZE, GRID_SIZE)
    pygame.draw.rect(surface, FOOD_COLOR, rect)


def draw_hud(surface, score, game_over=False):
    """绘制HUD（分数和游戏结束信息）"""
    # HUD背景
    hud_rect = pygame.Rect(GAME_X - 20, GAME_Y - 50, GAME_WIDTH + 40, 40)
    pygame.draw.rect(surface, HUD_BG_COLOR, hud_rect)
    pygame.draw.rect(surface, HUD_BORDER_COLOR, hud_rect, 2)
    
    # 分数
    score_text = font.render(f"Score: {score}", True, TEXT_COLOR)
    score_rect = score_text.get_rect(center=(GAME_X + GAME_WIDTH // 2, GAME_Y - 30))
    surface.blit(score_text, score_rect)
    
    # 游戏结束提示
    if game_over:
        game_over_text = font.render("GAME OVER", True, (255, 50, 50))
        game_over_rect = game_over_text.get_rect(center=(GAME_X + GAME_WIDTH // 2, GAME_Y + GAME_HEIGHT // 2))
        surface.blit(game_over_text, game_over_rect)
        
        restart_text = small_font.render("Press R to Restart", True, TEXT_COLOR)
        restart_rect = restart_text.get_rect(center=(GAME_X + GAME_WIDTH // 2, GAME_Y + GAME_HEIGHT // 2 + 50))
        surface.blit(restart_text, restart_rect)


def main():
    running = True
    game_over = False
    
    # 游戏状态
    score = 0
    direction = (1, 0)
    next_direction = (1, 0)
    snake = []
    food_x = 0
    food_y = 0
    last_move_time = 0
    move_interval = 1000 // SNAKE_SPEED  # 毫秒
    
    def start_game():
        nonlocal score, direction, next_direction, snake, food_x, food_y, last_move_time, game_over
        score = 0
        direction = (1, 0)
        next_direction = (1, 0)
        center_y = GRID_ROWS // 2
        start_x = GRID_COLS // 2
        snake = [(start_x - i, center_y) for i in range(3)]  # 初始长度为3
        food_x, food_y = spawn_food(snake)
        last_move_time = 0
        game_over = False
    
    start_game()
    
    while running:
        dt = clock.get_time()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r and game_over:
                    start_game()
                elif not game_over:
                    if event.key in (pygame.K_UP, pygame.K_w):
                        if direction[1] != 1:  # 不允许向下时反向向上
                            next_direction = (0, -1)
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        if direction[1] != -1:  # 不允许向上时反向向下
                            next_direction = (0, 1)
                    elif event.key in (pygame.K_LEFT, pygame.K_a):
                        if direction[0] != 1:  # 不允许向右时反向向左
                            next_direction = (-1, 0)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        if direction[0] != -1:  # 不允许向左时反向向右
                            next_direction = (1, 0)
        
        # 确定新方向
        if not game_over:
            direction = next_direction
        
        # 计时和移动
        if not game_over:
            current_time = pygame.time.get_ticks()
            if current_time - last_move_time >= move_interval:
                # 移动蛇
                head_x, head_y = snake[0]
                new_head = (head_x + direction[0], head_y + direction[1])
                
                # 检查碰撞墙壁
                if (new_head[0] < 0 or new_head[0] >= GRID_COLS or
                    new_head[1] < 0 or new_head[1] >= GRID_ROWS):
                    game_over = True
                # 检查碰撞自己
                elif new_head in snake:
                    game_over = True
                else:
                    snake.insert(0, new_head)
                    # 检查是否吃到食物
                    if new_head == (food_x, food_y):
                        score += SCORE_PER_FOOD
                        food_x, food_y = spawn_food(snake)
                    else:
                        snake.pop()
                
                last_move_time = current_time
        
        # 绘制
        screen.fill(BG_COLOR)
        
        # 绘制游戏区域
        draw_grid(screen)
        draw_food(screen, food_x, food_y)
        draw_snake(screen, snake)
        draw_hud(screen, score, game_over)
        
        # 更新标题
        pygame.display.set_caption(f"Snake Easy - Score: {score}")
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()