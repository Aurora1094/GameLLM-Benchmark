import pygame
import random
import time

# 初始化Pygame
pygame.init()

# 常量定义
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRID_SIZE = 30
PLAYER_SIZE = 15
WALL_THICKNESS = 2
TITLE = "Maze Runner Easy"

# 颜色常量
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# 创建窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(TITLE)
clock = pygame.time.Clock()

class Maze:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = []
        self.start_pos = (1, 1)
        self.end_pos = (rows*2 - 1, cols*2 - 1)
        
    def generate(self):
        # 初始化迷宫：1=墙, 0=路
        self.grid = [[1 for _ in range(self.cols * 2 + 1)] for _ in range(self.rows * 2 + 1)]
        
        # 使用深度优先搜索生成迷宫
        stack = [(1, 1)]
        visited = set()
        visited.add((1, 1))
        
        while stack:
            current = stack[-1]
            x, y = current
            
            # 获取未访问的邻居
            neighbors = []
            directions = [(0, -2), (0, 2), (-2, 0), (2, 0)]
            
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 1 <= nx <= self.rows * 2 - 1 and 1 <= ny <= self.cols * 2 - 1:
                    if (nx, ny) not in visited:
                        neighbors.append((nx, ny, dx//2, dy//2))
            
            if neighbors:
                # 随机选择一个邻居
                nx, ny, dx, dy = random.choice(neighbors)
                # 移除墙
                self.grid[x + dx][y + dy] = 0
                # 标记并入栈
                self.grid[nx][ny] = 0
                visited.add((nx, ny))
                stack.append((nx, ny))
            else:
                stack.pop()
        
        # 设置起点和终点
        self.grid[1][1] = 0
        self.grid[self.end_pos[0]][self.end_pos[1]] = 0
    
    def is_wall(self, x, y):
        if 0 <= x < len(self.grid) and 0 <= y < len(self.grid[0]):
            return self.grid[x][y] == 1
        return True
    
    def draw(self, surface, cell_size):
        # 绘制迷宫
        for row in range(len(self.grid)):
            for col in range(len(self.grid[0])):
                if self.grid[row][col] == 1:
                    pygame.draw.rect(surface, BLACK, (col * cell_size, row * cell_size, cell_size, cell_size))
                else:
                    pygame.draw.rect(surface, WHITE, (col * cell_size, row * cell_size, cell_size, cell_size))
        
        # 绘制起点
        pygame.draw.rect(surface, GREEN, (self.start_pos[1] * cell_size, self.start_pos[0] * cell_size, cell_size, cell_size))
        
        # 绘制终点
        pygame.draw.rect(surface, RED, (self.end_pos[1] * cell_size, self.end_pos[0] * cell_size, cell_size, cell_size))

class Player:
    def __init__(self, x, y, cell_size=GRID_SIZE):
        self.x = x
        self.y = y
        self.size = PLAYER_SIZE
        self.speed = 1
        self.cell_size = cell_size
    
    def move(self, dx, dy, maze):
        new_x = self.x + dx
        new_y = self.y + dy
        
        # 碰撞检测：检查新位置是否是墙
        grid_x = int(new_x // self.cell_size)
        grid_y = int(new_y // self.cell_size)
        
        # 检查四个角是否都是空地，避免卡在墙中
        corner_offsets = [
            (0, 0),
            (self.size, 0),
            (0, self.size),
            (self.size, self.size)
        ]
        
        can_move = True
        for dx_off, dy_off in corner_offsets:
            check_x = int((new_x + dx_off) // self.cell_size)
            check_y = int((new_y + dy_off) // self.cell_size)
            if maze.grid[check_y][check_x] == 1:
                can_move = False
                break
        
        if can_move:
            self.x = new_x
            self.y = new_y
    
    def draw(self, surface):
        pygame.draw.circle(surface, BLUE, (int(self.x + self.size // 2), int(self.y + self.size // 2)), self.size // 2)
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.size, self.size)

class Game:
    def __init__(self):
        self.maze_rows = 10
        self.maze_cols = 10
        self.maze = Maze(self.maze_rows, self.maze_cols)
        self.maze.generate()
        self.player = Player(self.maze.start_pos[1] * GRID_SIZE + (GRID_SIZE - PLAYER_SIZE) // 2, 
                            self.maze.start_pos[0] * GRID_SIZE + (GRID_SIZE - PLAYER_SIZE) // 2,
                            GRID_SIZE)
        self.start_time = 0
        self.running = True
        self.game_over = False
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
    
    def reset(self):
        self.maze = Maze(self.maze_rows, self.maze_cols)
        self.maze.generate()
        self.player = Player(self.maze.start_pos[1] * GRID_SIZE + (GRID_SIZE - PLAYER_SIZE) // 2, 
                            self.maze.start_pos[0] * GRID_SIZE + (GRID_SIZE - PLAYER_SIZE) // 2,
                            GRID_SIZE)
        self.start_time = time.time()
        self.game_over = False
    
    def run(self):
        self.start_time = time.time()
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and self.game_over:
                    if event.key == pygame.K_r:
                        self.reset()
            
            if not self.game_over:
                self.handle_input()
                self.check_win()
            
            self.draw()
            clock.tick(FPS)
        
        pygame.quit()
    
    def handle_input(self):
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        
        if keys[pygame.K_UP]:
            dy = -self.player.speed
        elif keys[pygame.K_DOWN]:
            dy = self.player.speed
        elif keys[pygame.K_LEFT]:
            dx = -self.player.speed
        elif keys[pygame.K_RIGHT]:
            dx = self.player.speed
        
        if dx != 0 or dy != 0:
            self.player.move(dx, dy, self.maze)
    
    def check_win(self):
        player_grid_x = int((self.player.x + self.player.size // 2) // self.maze.cell_size)
        player_grid_y = int((self.player.y + self.player.size // 2) // self.maze.cell_size)
        
        # 检查是否到达终点
        if player_grid_x == self.maze.end_pos[1] and player_grid_y == self.maze.end_pos[0]:
            self.game_over = True
            self.win_time = time.time() - self.start_time
    
    def draw(self):
        screen.fill(WHITE)
        
        # 绘制迷宫
        self.maze.draw(screen, GRID_SIZE)
        
        # 绘制玩家
        self.player.draw(screen)
        
        # 绘制UI
        if not self.game_over:
            elapsed_time = time.time() - self.start_time
            time_text = self.font.render(f"Time: {elapsed_time:.2f}", True, BLACK)
            screen.blit(time_text, (10, 10))
            
            controls_text = self.small_font.render("Use Arrow Keys to Move", True, BLACK)
            screen.blit(controls_text, (10, 50))
        else:
            # 游戏胜利界面
            win_text_large = self.font.render("YOU WIN!", True, GREEN)
            win_text_rect = win_text_large.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50))
            screen.blit(win_text_large, win_text_rect)
            
            time_text = self.font.render(f"Time: {self.win_time:.2f} seconds", True, BLACK)
            time_text_rect = time_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(time_text, time_text_rect)
            
            restart_text = self.font.render("Press 'R' to Restart", True, BLACK)
            restart_text_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
            screen.blit(restart_text, restart_text_rect)
        
        pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()