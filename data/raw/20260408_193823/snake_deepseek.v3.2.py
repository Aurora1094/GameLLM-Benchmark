import pygame
import random
import sys

# 初始化pygame
pygame.init()

# 游戏参数
WIDTH, HEIGHT = 800, 600
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE
GRID_HEIGHT = HEIGHT // GRID_SIZE
FPS = 60

# 颜色定义
BG_COLOR = (25, 33, 36)  # 深炭色背景
GRID_COLOR = (45, 52, 54)
SNAKE_HEAD_COLOR = (100, 182, 172)  # 蛇头颜色
SNAKE_BODY_COLOR = (242, 223, 145)  # 蛇身颜色
FOOD_COLOR = (255, 94, 98)  # 食物颜色
GRID_LINE_COLOR = (255, 255, 255)  # 网格线颜色（白色）
TEXT_COLOR = (255, 255, 255)
GRID_LINE_ALPHA = 5  # 网格线透明度因子 (0-255)
SCORE_COLOR = (255, 223, 0)  # 得分颜色：金色

# 创建时钟对象
clock = pygame.time.Clock()

class Snake:
    def __init__(self):
        self.reset()
    
    def reset(self):
        # 放置蛇身起始点约略于中央位置
        self.body = [(GRID_WIDTH // 2 + i, GRID_HEIGHT // 2) for i in range(3, 6)]
        self.direction = (0, -1)  # 开始时向上移动
        self.grow_pending = False
        self.speed_timer = 0
        
    @property
    def head(self):
        return self.body[0]
    
    def move(self, new_direction):
        head_x, head_y = self.head
        dx, dy = self.direction
        # 从头部反向计算速度
        # 当方向变化时应用新的方向
        if new_direction is not None:
            dx, dy = new_direction
            # 确保不同时转向相反方向
            if (dx, dy) != (-self.direction[0], -self.direction[1]):
                self.direction = (dx, dy)
        
        # 计算新头部位置
        new_head = (head_x + self.direction[0], head_y + self.direction[1])
        if not (0 <= new_head[0] < GRID_WIDTH and 0 <= new_head[1] < GRID_HEIGHT):
            return False
        
        self.body.insert(0, new_head)
        
        # 如果不需要增长，则移除尾部
        if self.grow_pending:
            self.grow_pending = False
        else:
            self.body.pop()
        
        return True
    
    def grow(self):
        self.grow_pending = True
    
    def check_collision(self):
        if self.head in self.body[1:]:
            return True
        x, y = self.head
        return not (0 <= x < GRID_WIDTH) or not (0 <= y < GRID_HEIGHT)

class Food:
    def __init__(self):
        self.position = None
        self.respawn_time = 20  # 生成食物的间隔
        self.timer = 0
    
    def update(self, snake):
        if self.timer >= self.respawn_time:
            while True:
                self.position = (random.randint(0, GRID_WIDTH-1), (random.randint(0, GRID_HEIGHT-1))
                if self.position not in snake.body:
                    break
            self.timer = 0
    
    def draw(self, screen):
        if self.position:
            food_rect = pygame.Rect(
                self.position[0] * GRID_SIZE, 
                self.position[1] * GRID_SIZE, 
                GRID_SIZE, GRID_SIZE
            )
            pygame.draw.rect(screen, FOOD_COLOR, food_rect)

def create_background_surface(width, height, color_list, grid_color, grid_alpha):
    grid_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    grid_surface.fill(color_list[0])
    
    # 从指定颜色的半透明版本开始
    x, y, w, h = color_list[1]

    start_x = x
    start_y = y
    for i in range(1, 31):  # 创建具有不同亮度的多个矩形以创建渐变散射光效果
        alpha = 50 - i * 1.6
        radius = max(1, 40 - i)
        offset_x = random.randint(-5, 5)  # 添加随机偏移
        offset_y = random.randint(-5, 5)
        pos_x = start_x + i * 4 - 10 + offset_x  # 随机偏移x坐标
        pos_y = start_y + 200 + offset_y  # 在这里使用随机偏移
        color_shadow = pygame.Color(*grid_color)
        color_shadow.a = alpha  # 设置透明度
        pygame.draw.ellipse(grid_surface, color_shadow, [pos_x, pos_y, radius*2, radius*2])
    
    return grid_surface

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Game")

# 创建蛇和食物
snake = Snake()
food = Food()

# 将网格画到背景上
background = None
current_grid = None
background_dirty = True

def generate_random_position(grid_size):
    x = random.randint(0, (WIDTH // grid_size) - 1)
    y = random.randint(0, (HEIGHT // grid_size) - 1)
    return (x * grid_size, y * grid_size, grid_size, grid_size)

def main():
    global screen, font, background, snake
    global current_grid_x, characters
    
    snake = Snake()
    food = Food()
    direction = (0, -1)  # 初始移动方向：向上
    new_direction = (0, -1)
    food.respawn()
    
    paused = False
    score = 0
    clock = pygame.time.Clock()
    
    background = create_background_surface(WIDTH, HEIGHT, BG_COLORS, GRID_COLOR)
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    running = True
    
    # 初始化游戏状态
    snake.reset()
    high_score = 0
    
    while running:
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                pause_mod = paused  # 初始化暂停状态
                if event.key == pygame.K_ESCAPE:
                    running = False
                    
                if event.key == pygame.K_SPACE:
                    # 空格键用于暂停/恢复游戏
                    paused = True
                    while paused:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pause = False
                                running = False
                                break
                            if event.type == pygame.KEYDOWN:
                                if event.key == pygame.K_SPACE:
                                    paused = False
                                    break
                elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    new_direction = new_key_direction
                    if event.key == pygame.K_UP:
                        new_direction = (0, -1)
                    elif event.key == pygame.K_DOWN:
                        new_direction = (0, 1)
                    elif event.key == pygame.K_LEFT:
                        new_direction = (-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        new_direction = (1, 0)

                    # 不允许直接反向移动
                    if (new_direction[0] + snake.direction[0] or 
                        new_direction[1] + new_direction[1] == 0):
                        continue
                    else:
                        direction = new_direction

        # 清除屏幕
        screen.fill((0,0,0))

        # 更新和绘制网格/背景
        grid_alpha = min(50 + int(snake_len * 0.5), 255)
        grid_surface = pygame.Surface((WIDTH, HEIGHT))
        grid_surface.set_alpha(min(grid_alpha, 255))  # Set alpha for whole background grid, now as gridalpha
        grid_surface.fill((240,240,240))
        grid_surface.set_colorkey((0,0,0))  # Black, make transparent
        screen.blit(background, (0,0))
        # Draw grid lines using a loop with a small rectangle drawing each line
        # but to limit the number of draw calls, we'll draw many lines at once with vertical lines.
        for x in range(0, WIDTH, GRID_SIZE):
            pygame.draw.rect(grid_surface, GRID_COLOR, pygame.Rect(x - grid_width // 2, 0, 1, HEIGHT))
        for y in range(0, HEIGHT, GRID_SIZE):
            pygame.draw.rect(screen, GRID_COLOR, pygame.Rect(0, y, WIDTH, 1))

        # 移动蛇
        if not paused:
            if snake.move(direction) is not True and len(snake.body) > 2:
                # Game over: Head collides with the boundary or self
                break

            head_x, head_y = snake.head
            if (head_x, head_y) == food.position:
                snake.grow()
                food.timer += 1
                if food.timer >= food.respawn_time:
                    food.respawn(snake)  # Respawn the food at a new empty cell.
                    score += 1

        # 绘制食物
        if food.position:
            screen.blit(apple_img, 
                        (food.position[0]*GRID_SIZE, 
                         food.position[1]*GRID_SIZE))
        
        # 绘制蛇
        for segment in snake.body:
            pygame.draw.rect(screen, (255, 255, 255), 
                           (segment[0]*GRID_SIZE, segment[1]*GRID_SIZE, GRID_SIZE, GRID_SIZE), 2)
        
        # 显示分数
        score_surface = font.render(f'Score: {score}', True, SCORE_COLOR)
        screen.blit(score_surface, (WIDTH - 200, 20))
        
        # 更新显示
        pygame.display.flip()
        pygame.time.Clock().tick(10)  # 控制游戏速度

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()