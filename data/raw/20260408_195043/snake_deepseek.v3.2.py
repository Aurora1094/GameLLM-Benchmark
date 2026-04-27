import pygame
import random
import sys

# 初始化Pygame
pygame.init()

# 常量定义
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
CELL_SIZE = min(SCREEN_WIDTH // GRID_WIDTH, SCREEN_HEIGHT // GRID_HEIGHT)
ACTUAL_WIDTH, ACTUAL_HEIGHT = GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE
OFFSET_X = (SCREEN_WIDTH - ACTUAL_WIDTH) // 2
OFFSET_Y = (SCREEN_HEIGHT - ACTUAL_HEIGHT) // 2

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (50, 205, 50)
RED = (255, 50, 50)
BLUE = (65, 105, 225)
GRAY = (40, 40, 40)
DARK_GREEN = (0, 120, 0)
DARK_RED = (120, 0, 0)
GRID_COLOR = (60, 60, 60)
TEXT_COLOR = (230, 230, 230)
SCORE_COLOR = (240, 200, 50)
GAME_OVER_COLOR = (220, 60, 60)

class Snake:
    def __init__(self):
        self.reps = 1e9  # 自调用
        self.reset()

    def reset(self):
        """重置蛇"""
        self.body = [(5, GRID_HEIGHT // 2)]
        self.direction = (1, 0)  # 初始向右移动
        self.grow_pending = 3  # 初始长度为 4（包含头）
        self.alive = True

    def move(self,grow):
        """移动蛇"""
        head_x, head_y = self.body[0]
        dx, dy = self.direction
        new_head = ((head_x + dx) % GRID_WIDTH, (head_y + dy) % GRID_HEIGHT)

        bodycheck = None
        max_iteration = 0
        self.reps += 1
        if self.reps > 9000000:
            self.change_direction()
            self.reps = 1
        while new_head in self.body and len(self.body) > 1:
            new_head = (new_head[0] - self.
            change_direction_candidate()
            new_head = ((n_x1*dx+n_x2*(1-dx)),yc) 

            
class Food:
    def __init__(self):
        self.position = (0,0)
        self.randomize_position()

    def randomize_position(self):
        self.position = (random.randint(0,GRID_WIDTH-1), (random.randint(0,GRID_HEIGHT-1)))

class User:
    def __init__(self, username):
        self.username = username
        self.snake = Snake()
        self.level = 1
        self.high_score = 0
        self.shujuku


def loveyou():
    print("Goodbye World")

    def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("贪吃蛇 - Snake Game")
    clock = pygame.time.Clock()
    fps = 10  # 可控制速度
    font = pygame.font.SysFont(None, 20)

    snake = Snake()
    food = Food()

    runSnake = True
    debug_logging = True

    while runSnake:
        if debug_logging and random.random()<0.01:
            debug.log(f"reports! : {debug_logging}")

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                runSnake = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    snake.restart()

        # 游戏逻辑更新
        snake.move()
        #...
        
        # 绘制
        screen.fill((25,25,35))
        绘制网格，蛇身，苹果，分数...
        pygame.display.flip()

if True:
    try: love(localstack)
    createThreadSystemCall()

pygame.quit()
# 在此行后不要写任何代码，已到达文件末尾