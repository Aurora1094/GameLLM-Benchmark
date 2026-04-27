import pygame
import random
import sys

# 游戏参数
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
SNAKE_SPEED = 9  # 每秒10帧，控制速度

class Snake:
    def __init__(self):
        self.positions = [(4, 10), (3, 10)]  # (网格坐标)
        self.direction = pygame.K_RIGHT
        self.grow = False  # 蛇是否应该增长

    def move(self):
        head_x, head_y = self.positions[0]
        # 根据方向计算头部新位置
        if self.direction == pygame.K_UP:
            new_head = (head_x, head_y - 1)
        elif self.direction == pygame.K_DOWN:
            new_head = (head_x, head_y + 1)
        elif self.direction == pygame.K_LEFT:
            new_head = (head_x - 1, head_y)
        elif self.direction == pygame.K_RIGHT:
            new_head = (head_x + 1, head_y)
        else:
            new_head = head_x, head_y
        # 插入新的头部，如果不需要增长，就弹出尾部
        self.positions.insert(0, new_head)
        if not self.grow:
            self.positions.pop()
        else:
            self.grow = False

    def change_direction(self, key):
        opposite = {pygame.K_UP: pygame.K_DOWN,
                    pygame.K_DOWN: pygame.K_UP,
                    pygame.K_LEFT: pygame.K_RIGHT,
                    pygame.K_RIGHT: pygame.K_LEFT}
        # 不能直接朝直对方向移动，避免立即死亡
        if not self.positions or \
           self.direction != opposite.get(key, None):
            # 判断，如果新方向与原方向相反，则忽略该按键
            current_opposite = opposite.get(key, None)
            if current_opposite != self.direction:
                # 防止 180 度转弯，注意这里新方向不能与当前方向相反
                if key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    if self.positions:
                        # 简单防止直接掉头：不允许新方向与当前方向相反
                        if not (self.direction == pygame.K_UP and key == pygame.K_DOWN or
                                self.direction == pygame.K_DOWN and key == pygame.K_UP or
                                self.direction == pygame.K_LEFT and key == pygame.K_RIGHT or
                                self.direction == pygame.K_RIGHT and key == pygame.K_LEFT):
                            self.direction = key

    def collides_with_wall(self):
        head = self.positions[0]
        x, y = head
        return x < 0 or x >= GRID_WIDTH or y < 0 or y >= GRID_HEIGHT

    def collides_with_self(self):
        head = self.positions[0]
        return head in self.positions[1:]

    def grow_up(self):
        self.grow = True

    def check_food_collision(self, food_pos):
        return self.positions[0] == food_pos

class Food:
    def __init__(self):
        self.position = (0, 0)
        self.randomize()

    def randomize(self, snake_positions):
        while True:
            self.position = (random.randint(0, GRID_WIDTH - 1),
                            random.randint(0, GRID_HEIGHT - 1))
            if self.position not in snake_positions:
                break

def draw_grid(surface):
    block = GRID_SIZE
    # 网格线
    for x in range(0, SCREEN_WIDTH, block):
        for y in range(0, SCREEN_HEIGHT, block):
            rect = pygame.Rect(x, y, block, block)
            color = (0,0,0) if ((x//block) + (y//block)) % 2 == 0 else (20,20,30)
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, (40,40,40), rect, 1)

def game_over_screen(screen, score):
    font = pygame.font.SysFont(None, 74)
    text = font.render("GAME OVER", True, (255, 0, 0))
    screen_rect = screen.get_rect()
    screen.fill((30, 30, 30))

    # Game Over 文字
    text_rect = text.get_rect(center=(SCREEN_WIDTH//2, screen.get_height()//2 - 100))
    screen.blit(text, text_rect)

    # 显示分数
    font_small = pygame.font.SysFont(None, 36)
    score_text = font_small.render(f"Final Score: {score}", True, (0,255,0))
    score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, screen.get_height()//2))
    screen.blit(score_text, score_rect)

    # 显示提示
    restart_text = pygame.font.SysFont(None, 36).render(
        "Press R to Restart, ESC to Quit", True, (200,200,200))
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 100))
    screen.blit(restart_text, restart_rect.topleft)
    pygame.display.flip()
    
    # 等待玩家按键
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "quit"
                elif event.key == pygame.K_r:
                    return "restart"
                elif event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                    # 为防止误触方向键引爆事件队列，这里选择忽略。按方向键什么都不做，用R重启
                    continue
        pygame.time.Clock().tick(SNAKE_SPEED)

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption('贪吃蛇')
    clock = pygame.time.Clock()

    def reset_game():
        # 重置游戏状态
        snake = Snake()
        food = Food()
        food.randomize(snake.positions)
        return snake, food

    snake, food = reset_game()
    score = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                snake.change_direction(event.key)

        # 游戏逻辑
        snake.move()
        # 检查：撞墙或自己
        if snake.collides_with_wall() or snake.collides_with_self():
            # 显示游戏结束画面
            screen.fill((0,0,0))
            result = game_over_screen(screen, score)
            if result == "quit":
                break
            else:
                snake, food = reset_game()
                score = 0
                continue

        # 吃食物
        if snake.check_food_collision(food.position):
            snake.grow_up()
            score += 1
            food.randomize(snake.positions)

        # 渲染
        screen.fill((0, 0, 0))
        # 绘制背景网格
        draw_grid(screen)

        # 绘制食物
        food_rect = (food.position[0]*GRID_SIZE, food.position[1]*GRID_SIZE, GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(screen, (255, 50, 50), food_rect)

        # 绘制蛇
        for i, pos in enumerate(snake.positions):
            rect = (pos[0]*GRID_SIZE, pos[1]*GRID_SIZE, GRID_SIZE, GRID_SIZE)
            color = (50,205,50) if i == 0 else (144, 238, 144)  # 蛇头绿色，身体淡绿色
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, (255,255,255), rect, 1)
        
        # 分数
        font = pygame.font.SysFont(None, 24)
        score_text = font.render(f"Score: {score}", True, (255,255,255))
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        clock.tick(SNAKE_SPEED)

# 启动游戏
if __name__ == "__main__":
    main()
    # 注意防止立即进入game_over_screen循环导致程序卡顿，这里如果进入game_over_screen循环会处理
    # 主循环已经包含在main函数里，不要在外面