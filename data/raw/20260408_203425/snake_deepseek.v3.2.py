import pygame
import random
import sys

# 初始化pygame
pygame.init()

# 游戏常量
GRID_SIZE = 20
GRID_WIDTH = 20
GRID_HEIGHT = 15
CELL_SIZE = 30
SCREEN_WIDTH = GRID_WIDTH * CELL_SIZE
SCREEN_HEIGHT = GRID_HEIGHT * CELL_SIZE
FPS = 8  # 控制蛇速，数字越大速度越快

# 颜色定义 (使用改进的可视性)
BACKGROUND = (15, 15, 15)  # 深灰色背景
GRID_COLOR = (40, 40, 40)  # 网格线颜色
SNAKE_COLOR = (50, 255, 50)  # 亮绿色 - 蛇
FOOD_COLOR = (255, 100, 100)  # 亮红色
SCORE_COLOR = (250, 250, 200)  # 分数文本颜色
GAME_OVER_COLOR = (150, 50, 50)

class SnakeGame:
    def __init__(self):
        # Pygame 初始化
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("贪吃蛇游戏")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)
        self.large_font = pygame.font.SysFont("Arial", 48)
        self.small_font = pygame.font.SysFont(None, 36)
        
        self.reset_game()
        pygame.key.set_repeat(100, 50)  # 按键重复，方便连续移动
    
    def reset_game(self):
        """重置游戏状态"""
        # 蛇的初始状态，从屏幕中间开始
        self.snake = [(GRID_WIDTH // 3, GRID_HEIGHT // 2)]
        self.direction = (1, 0)  # 初始向右移动
        self.next_direction = (1, 0)  # 下一步方向
        self.score = 0
        self.game_over = False
        
        # 生成第一个食物（确保不在蛇身上）
        while True:
            self.food = (
                random.randint(0, GRID_WIDTH - 1),
                random.randint(0, GRID_HEIGHT - 1)
            )
            if self.food not in self.snake:
                break
                
    def draw_grid(self, surface, grid_size):
        """绘制网格线"""
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                if (x + y) % 2 == 0:
                    pygame.draw.rect(surface, (20, 20, 20), 
                                   pygame.Rect(x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE))
                else:
                    pygame.draw.rect(surface, (25, 25, 25), 
                                   pygame.Rect(x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE))
        # 绘制网格线
        for x in range(GRID_WIDTH + 1):
            pygame.draw.line(surface, GRID_COLOR, (x*CELL_SIZE, 0), 
                          (x*CELL_SIZE, SCREEN_HEIGHT), 1)
        for y in range(GRID_HEIGHT + 1):
            pygame.draw.line(surface, GRID_COLOR, (0, y*CELL_SIZE), 
                          (SCREEN_WIDTH, y*CELL_SIZE), 1)
    
    def move_snake(self):
        """移动蛇"""
        # 设置新的头方向
        self.direction = self.next_direction
        # 计算新的头部位置
        head_x, head_y = self.snake[0]
        dx, dy = self.direction
        new_head = (
            (head_x + dx) % GRID_WIDTH,
            (head_y + dy) % GRID_HEIGHT
        )
        
        # 检查是否撞到自己
        if new_head in self.snake:
            self.game_over = True
            return False
            
        # 移动蛇
        self.snake.insert(0, new_head)
        
        # 检查是否吃到食物
        if new_head == self.food:
            # 吃到食物，分数增加
            self.score += 10
            
            # 生成新食物（确保不在蛇身上）
            while True:
                self.food = (
                    random.randint(0, GRID_WIDTH - 1),
                    random.randint(0, GRID_HEIGHT - 1)
                )
                if self.food not in self.snake and self.food != new_head:
                    break
        else:
            # 没吃到食物，去掉蛇尾
            self.snake.pop()
            
        return True
    
    def handle_input(self):
        """处理键盘输入"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN and not self.game_over:
                if event.key == pygame.K_UP and self.direction != (0, 1):  # 不能直接掉头
                    self.next_direction = (0, -1)
                elif event.key == pygame.K_DOWN and self.direction != (0, -1):
                    self.next_direction = (0, 1)
                elif event.key == pygame.K_LEFT and self.direction != (1, 0):
                    self.next_direction = (-1, 0)
                elif event.key == pygame.K_RIGHT and self.direction != (-1, 0):
                    self.next_direction = (1, 0)
                elif event.key == pygame.K_r:
                    self.reset_game()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
    
    def draw_snake_and_food(self):
        # 绘制食物
        pygame.draw.rect(self.screen, FOOD_COLOR, 
                        (self.food[0]*CELL_SIZE, self.food[1]*CELL_SIZE, CELL_SIZE, CELL_SIZE))
        
        # 绘制蛇（蛇头用不同颜色）
        for i, (x, y) in enumerate(self.snake):
            color = (100, 220, 50) if i == 0 else SNAKE_COLOR  # 蛇头和蛇身不同颜色
            pygame.draw.rect(self.screen, color, 
                           (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE-1, CELL_SIZE-1))
            
            # 绘制蛇眼睛（仅蛇头）
            if i == 0:
                eye_color = (255, 255, 200)  # 白色
                eye_radius = 3
                eye_offset = 8
                eye_x1 = x*CELL_SIZE + eye_offset
                eye_x2 = (x+1)*CELL_SIZE - eye_offset - eye_radius
                eye_y = y*CELL_SIZE + 7
                pygame.draw.circle(self.screen, eye_color, (eye_x1, eye_y), eye_radius)
                pygame.draw.circle(self.screen, eye_color, (eye_x2, eye_y), eye_radius)
    
    def show_game_over(self):
        # 半透明遮挡层
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0,0))
        
        # 绘制半透明背景
        game_over_rect = pygame.Rect(SCREEN_WIDTH//2-150, SCREEN_HEIGHT//2-100, 300, 200)
        pygame.draw.rect(self.screen, (30, 30, 35), game_over_rect)
        pygame.draw.rect(self.screen, GAME_OVER_COLOR, game_over_rect, 2)
        
        # 游戏结束文字
        game_over_text = self.large_font.render("游戏结束", True, GAME_OVER_COLOR)
        score_text = self.font.render(f"最终分数: {self.score}", True, (255, 255, 255))
        score_text2 = self.font.render("按 R 重新开始", True, (200, 200, 200))
        score_text3 = self.font.render("ESC键退出", True, (200, 200, 200))
        self.screen.blit(game_over_text, 
                        (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 
                         SCREEN_HEIGHT//2 - 120))
        self.screen.blit(score_text, 
                        (SCREEN_WIDTH//2 - score_text.get_width()//2, 
                         SCREEN_HEIGHT//2 - 40))
        self.screen.blit(score_text2, 
                        (SCREEN_WIDTH//2 - score_text2.get_width()//2, 
                         SCREEN_HEIGHT//2 + 20))
        self.screen.blit(score_text3, 
                        (SCREEN_WIDTH//2 - score_text3.get_width()//2, 
                         SCREEN_HEIGHT//2 + 60))
    
    def run(self):
        # 主循环
        running = True
        move_timer = 0
        move_delay = FPS  # 移动间隔（帧数）
        
        while running:
            # 事件处理和移动
            self.handle_input()
            
            # 绘制背景和网格
            self.screen.fill((15, 15, 15))
            self.draw_grid(SCREEN_WIDTH, SCREEN_HEIGHT)
            
            # 游戏逻辑和绘制（非游戏结束状态）
            if not self.game_over:
                move_timer += 1
                # 移动定时器
                if move_timer >= move_delay:
                    if not self.move_snake():  # 如果游戏结束
                        move_timer = -float('inf')  # 移动停止，游戏结束
                    move_timer = 0
                
                # 绘制蛇和食物
                self.draw_snake_and_food()
            else:
                # 游戏结束画面
                self.show_game_over()
            
            pygame.display.flip()
            self.clock.tick(FPS)  # 控制更新速度

class Game:
    def __init__(self):
        pygame.init()
        self.initialize_game()
        
    def initialize_game(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("PySnake")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont('Arial', 24)
        self.big_font = pygame.font.SysFont("Arial", 28)
        self.reset_game()
    
    def reset_game(self):
        self.snake = [(5, 5)]
        self.direction = (1, 0)        # 初始方向：右
        self.next_direction = (1, 0)
        self.food = self.generate_food()
        self.score = 0
        self.game_over = False
        self.start_timer = 3  # 3秒倒计时
        self.timer_start = pygame.time.get_ticks()
    
    def generate_food(self):
        while True:
            food_pos = (random.randint(0, GRID_WIDTH-1), 
                       random.randint(0, GRID_HEIGHT-1))
            if not any(segment == food_pos for segment in self.snake):
                return food_pos
    
    def draw_background(self):
        # 渐变背景
        self.screen.fill((10, 10, 10))
        # 绘制网格
        for x in range(GRID_WIDTH):
            for y in range(GRID_HEIGHT):
                if (x + y) % 2 == 0:
                    color = (30, 30, dic(40 if x*y%2 else 30) 
                    pygame.draw.rect(self.screen, color, 
                        (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE))
        
        # 绘制深色网格线
        [pygame.draw.line(self.screen, (77, 77, 77), 
                (0, i), (SCREEN_WIDTH, i)) for i in range(0, SCREEN_HEIGHT, CELL_SIZE)]
        [pygame.draw.line(self.screen, (77, 77, 77), 
                (i, 0), (i, SCREEN_HEIGHT)) for i in range(0, SCREEN_WIDTH, CELL_SIZE)]
    
    def draw_start_screen(self):
        self.screen.fill((0, 0, 0))
        title_font = pygame.font.Font(None, 48)
        start_msg = self.big_font.render("按任意键开始游戏", True, (255, 255, 255))
        instr = self.font.render("方向键控制移动，R键重新开始", True, (150, 150, 150))
    
        self.screen.blit(title_font.render("贪吃蛇游戏", True, (0, 200, 100)), 
                        (SCREEN_WIDTH//2-100, SCREEN_HEIGHT//2 - 150))
        self.screen.blit(start_msg, (SCREEN_WIDTH//2 - start_msg.get_width()//2, SCREEN_HEIGHT//2))
        self.screen.blit(instr, (SCREEN_WIDTH//2 - instr.get_width()//2, SCREEN_HEIGHT//2 + 80))
    
    def draw(self):
        self.screen.fill(BACKGROUND)  # 清屏
        self.draw_grid(self.screen)
        self.screen.title(f"贪吃蛇  |  分数: {self.score}")  

        # 绘制食物
        pygame.draw.rect(self.screen, FOOD_COLOR,
                       (self.food[0]*CELL_SIZE, 
                        self.food[1]*CELL_SIZE, 
                        CELL_SIZE, CELL_SIZE))
        
        # 绘制蛇
        for i, (x, y) in enumerate(self.snake):
            color = color_snake_head if i == 0 else SNAKE_COLOR  # 头部绿色特别一点
            rect = (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE-1, CELL_SIZE-1)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (0, 100, 0), 
                (x*CELL_SIZE, y*CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)
        
        # 绘制分数
        score_text = self.font.render(f"得分: {self.score}", True, SCORE_COLOR)
        self.screen.blit(score_text, (5, 5))
        
        # 游戏开始时显示倒计时
        if hasattr(self, 'start_timer') and self.start_timer > 0 and not self.game_over:
            time_left = self.start_timer - int((current_time - self.timer_start) / 1000)
            if time_left > 0:
                countdown_text = font.render(str(time_left), True, (255, 100, 100))
                self.screen.blit(countdown_text, 
                               (SCREEN_WIDTH//2 - countdown_text.get_width()//2,
                                SCREEN_HEIGHT//2))

def main():
    pygame.init()
    game = SnakeGame()
    game.run()

if __name__ == "__main__":
    main()