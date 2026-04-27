import pygame
import random
import time

# 固定常量
WIDTH, HEIGHT = 800, 600
FPS = 60
MAZE_COLS, MAZE_ROWS = 21, 15
CELL_SIZE = 32
MAZE_WIDTH = MAZE_COLS * CELL_SIZE
MAZE_HEIGHT = MAZE_ROWS * CELL_SIZE
OFFSET_X = (WIDTH - MAZE_WIDTH) // 2
OFFSET_Y = (HEIGHT - MAZE_HEIGHT) // 2

# 颜色定义
COLOR_WALL = (30, 30, 30)
COLOR_PATH = (240, 240, 240)
COLOR_PLAYER = (0, 120, 255)
COLOR_EXIT = (0, 200, 0)
COLOR_HUD_BG = (50, 50, 50)
COLOR_HUD_TEXT = (255, 255, 255)

# 随机种子
random.seed(42)

class Maze:
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        self.grid = [[1] * cols for _ in range(rows)]  # 1=wall, 0=path
        self.start = (0, 0)
        self.exit = (cols - 1, rows - 1)
        self.generate()

    def generate(self):
        # 使用深度优先搜索生成迷宫
        stack = []
        x, y = self.start
        self.grid[y][x] = 0
        stack.append((x, y))
        
        while stack:
            x, y = stack[-1]
            neighbors = []
            
            for dx, dy in [(2, 0), (-2, 0), (0, 2), (0, -2)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows and self.grid[ny][nx] == 1:
                    neighbors.append((nx, ny, dx // 2, dy // 2))
            
            if neighbors:
                nx, ny, px, py = neighbors[random.randint(0, len(neighbors) - 1)]
                self.grid[y + py][x + px] = 0
                self.grid[ny][nx] = 0
                stack.append((nx, ny))
            else:
                stack.pop()

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Maze Runner Easy")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)
        self.restart()
        
    def restart(self):
        self.maze = Maze(MAZE_COLS, MAZE_ROWS)
        self.player_pos = list(self.maze.start)
        self.game_state = "playing"  # playing, won
        self.start_time = 0
        self.elapsed_time = 0
        self.is_first_move = True
        
    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r:
                        self.restart()
                    else:
                        self.handle_input(event.key)
            
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
    
    def handle_input(self, key):
        if self.game_state != "playing":
            return
            
        if self.is_first_move:
            self.start_time = time.time()
            self.is_first_move = False
        
        dx, dy = 0, 0
        if key == pygame.K_UP:
            dy = -1
        elif key == pygame.K_DOWN:
            dy = 1
        elif key == pygame.K_LEFT:
            dx = -1
        elif key == pygame.K_RIGHT:
            dx = 1
        else:
            return
        
        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy
        
        if 0 <= new_x < self.maze.cols and 0 <= new_y < self.maze.rows:
            if self.maze.grid[new_y][new_x] == 0:
                self.player_pos = [new_x, new_y]
                # Check win condition
                if self.player_pos[0] == self.maze.exit[0] and self.player_pos[1] == self.maze.exit[1]:
                    self.game_state = "won"
                    self.elapsed_time = time.time() - self.start_time
    
    def update(self):
        if self.game_state == "playing" and not self.is_first_move:
            self.elapsed_time = time.time() - self.start_time
    
    def draw(self):
        # Clear screen
        self.screen.fill(COLOR_HUD_BG)
        
        # Draw maze
        for y in range(self.maze.rows):
            for x in range(self.maze.cols):
                rect = pygame.Rect(
                    OFFSET_X + x * CELL_SIZE,
                    OFFSET_Y + y * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )
                if (x, y) == self.maze.start:
                    pygame.draw.rect(self.screen, COLOR_PLAYER, rect)
                elif (x, y) == self.maze.exit:
                    pygame.draw.rect(self.screen, COLOR_EXIT, rect)
                elif self.maze.grid[y][x] == 1:
                    pygame.draw.rect(self.screen, COLOR_WALL, rect)
                else:
                    pygame.draw.rect(self.screen, COLOR_PATH, rect)
        
        # Draw player on path
        if self.game_state == "playing" or self.game_state == "won":
            player_x, player_y = self.player_pos
            if not ((player_x == self.maze.start[0] and player_y == self.maze.start[1]) or 
                    (player_x == self.maze.exit[0] and player_y == self.maze.exit[1])):
                rect = pygame.Rect(
                    OFFSET_X + player_x * CELL_SIZE,
                    OFFSET_Y + player_y * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE
                )
                pygame.draw.rect(self.screen, COLOR_PLAYER, rect)
        
        # Draw HUD
        time_str = f"Time: {self.elapsed_time:.2f}s"
        if self.game_state == "playing":
            time_text = self.font.render(time_str, True, COLOR_HUD_TEXT)
            self.screen.blit(time_text, (20, 20))
        
        # Draw win screen
        if self.game_state == "won":
            # Semi-transparent overlay
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(128)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0, 0))
            
            # Win message
            win_font = pygame.font.SysFont("Arial", 64, bold=True)
            win_text = win_font.render("You Win!", True, (0, 255, 0))
            self.screen.blit(win_text, (WIDTH//2 - win_text.get_width()//2, HEIGHT//2 - 120))
            
            # Time text
            time_msg = f"Time: {self.elapsed_time:.2f}s"
            time_text2 = self.font.render(time_msg, True, (255, 255, 255))
            self.screen.blit(time_text2, (WIDTH//2 - time_text2.get_width()//2, HEIGHT//2 - 40))
            
            # Restart text
            restart_font = pygame.font.SysFont("Arial", 32)
            restart_text = restart_font.render("Press R to Restart", True, (255, 255, 255))
            self.screen.blit(restart_text, (WIDTH//2 - restart_text.get_width()//2, HEIGHT//2 + 40))
        
        pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()