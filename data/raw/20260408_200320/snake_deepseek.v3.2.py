import pygame
import sys
import random

# 初始化
pygame.init()

# 游戏常量
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
FPS = 10

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 120, 255)
GRAY = (40, 40, 40)

# 方向常量
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

class Snake:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.length = 3
        self.positions = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = RIGHT
        self.score = 0
        # 初始化蛇身
        for i in range(1, self.length):
            self.positions.append((self.positions[0][0] - i, self.positions[0][1]))
    
    def get_head_position(self):
        return self.positions[0]
    
    def turn(self, direction):
        # 防止直接反向移动
        if (direction[0] * -1, direction[1] * -1) != self.direction:
            self.direction = direction
    
    def move(self):
        head = self.get_head_position()
        x, y = self.direction
        new_x = (head[0] + x) % GRID_WIDTH
        new_y = (head[1] + y) % GRID_HEIGHT
        new_position = (new_x, new_y)
        
        # 检查是否撞到自己
        if new_position in self.positions[1:]:
            return False
        
        self.positions.insert(0, new_position)
        if len(self.positions) > self.length:
            self.positions.pop()
        return True
    
    def draw(self, screen):
        for i, p in enumerate(self.positions):
            rect = pygame.Rect(p[0] * GRID_SIZE, p[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            if i == 0:  # 蛇头
                pygame.draw.rect(screen, GREEN, rect)
                pygame.draw.rect(screen, WHITE, rect, 1)
                # 画眼睛
                eye_size = GRID_SIZE // 5
                if self.direction == RIGHT:
                    pygame.draw.circle(screen, BLACK, (p[0]*GRID_SIZE + GRID_SIZE - eye_size, p[1]*GRID_SIZE + eye_size*2), eye_size)
                    pygame.draw.circle(screen, BLACK, (p[0]*GRID_SIZE + GRID_SIZE - eye_size, p[1]*GRID_SIZE + GRID_SIZE - eye_size*2), eye_size)
                elif self.direction == LEFT:
                    pygame.draw.circle(screen, BLACK, (p[0]*GRID_SIZE + eye_size, p[1]*GRID_SIZE + eye_size*2), eye_size)
                    pygame.draw.circle(screen, BLACK, (p[0]*GRID_SIZE + eye_size, p[1]*GRID_SIZE + GRID_SIZE - eye_size*2), eye_size)
                elif self.direction == UP:
                    pygame.draw.circle(screen, BLACK, (p[0]*GRID_SIZE + eye_size*2, p[1]*GRID_SIZE + eye_size), eye_size)
                    pygame.draw.circle(screen, BLACK, (p[0]*GRID_SIZE + GRID_SIZE - eye_size*2, p[1]*GRID_SIZE + eye_size), eye_size)
                elif self.direction == DOWN:
                    pygame.draw.circle(screen, BLACK, (p[0]*GRID_SIZE + eye_size*2, p[1]*GRID_SIZE + GRID_SIZE - eye_size), eye_size)
                    pygame.draw.circle(screen, BLACK, (p[0]*GRID_SIZE + GRID_SIZE - eye_size*2, p[1]*GRID_SIZE + GRID_SIZE - eye_size), eye_size)
            else:  # 蛇身
                color = (0, 200 - i % 5 * 20, 0)
                pygame.draw.rect(screen, color, rect)
                pygame.draw.rect(screen, WHITE, rect, 1)
    
    def grow(self):
        self.length += 1
        self.score += 10

class Food:
    def __init__(self, snake):
        self.position = (0, 0)
        self.randomize_position(snake)
    
    def randomize_position(self, snake):
        while True:
            self.position = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
            if self.position not in snake.positions:
                break
    
    def draw(self, screen):
        rect = pygame.Rect(self.position[0] * GRID_SIZE, self.position[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(screen, RED, rect)
        pygame.draw.rect(screen, WHITE, rect, 1)
        # 画一个简单的苹果样式
        stem_rect = pygame.Rect(self.position[0] * GRID_SIZE + GRID_SIZE // 2 - 2, 
                               self.position[1] * GRID_SIZE - 3, 4, 5)
        pygame.draw.rect(screen, (139, 69, 19), stem_rect)
        leaf_rect = pygame.Rect(self.position[0] * GRID_SIZE + GRID_SIZE // 2 + 2, 
                               self.position[1] * GRID_SIZE - 2, 6, 3)
        pygame.draw.ellipse(screen, GREEN, leaf_rect)

def draw_grid(screen):
    for x in range(0, SCREEN_WIDTH, GRID_SIZE):
        pygame.draw.line(screen, GRAY, (x, 0), (x, SCREEN_HEIGHT), 1)
    for y in range(0, SCREEN_HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, GRAY, (0, y), (SCREEN_WIDTH, y), 1)

def draw_score(screen, score, game_over):
    font = pygame.font.SysFont(None, 36)
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))
    
    if game_over:
        game_over_font = pygame.font.SysFont(None, 72)
        game_over_text = game_over_font.render("GAME OVER", True, RED)
        game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(game_over_text, game_over_rect)
        
        restart_font = pygame.font.SysFont(None, 36)
        restart_text = restart_font.render("Press SPACE to restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
        screen.blit(restart_text, restart_rect)

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Snake Easy")
    clock = pygame.time.Clock()
    
    snake = Snake()
    food = Food(snake)
    game_over = False
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_SPACE:
                        snake.reset()
                        food.randomize_position(snake)
                        game_over = False
                else:
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        snake.turn(UP)
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        snake.turn(DOWN)
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        snake.turn(LEFT)
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        snake.turn(RIGHT)
        
        if not game_over:
            # 移动蛇
            if not snake.move():
                game_over = True
            
            # 检查是否吃到食物
            if snake.get_head_position() == food.position:
                snake.grow()
                food.randomize_position(snake)
        
        # 绘制
        screen.fill(BLACK)
        draw_grid(screen)
        snake.draw(screen)
        food.draw(screen)
        draw_score(screen, snake.score, game_over)
        
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()