import pygame
import random
import time

# 初始化 Pygame
pygame.init()

# 游戏常数
GRID_SIZE = 16
TILE_SIZE = 40
PLAYER_SIZE = TILE_SIZE // 2
EXIT_SIZE = TILE_SIZE // 2

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 128, 0)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
YELLOW = (255, 255, 0)
WALL_COLOR = (0, 0, 80)
FLOOR_COLOR = (50,174,195)
WALL_HIGHLIGHT = (100,100,160)
FLOOR_HIGHLIGHT = (80,180,200)

# 迷宫方向
class Maze:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = {}
        self.seed = random.randint(0, 10000)
        self.create_maze()

    # 深度优先搜索生成迷宫
    def create_maze(self):
        self.grid = {(r, c): [0,0,0,0] for r in range(self.rows) for c in range(self.cols)}
        visited = [[False] * self.cols for _ in range(self.rows)]
        start_r, start_c = self.rows // 2, self.cols // 2
        stack = [(start_r, start_c, -1)]
        visited[start_r][start_c] = True
        # 深度优先搜索生成迷宫
        while stack:
            r, c, direction = stack.pop()
            dirs = [0,1,2,3]
            random.shuffle(dirs)
            for dr, dc, dir_idx in [(-1,0,0), (0,1,1), (1,0,2), (0,-1,3)]:
                nr, nc = r + dr, c + dc
                if (0 <= nr < self.rows and 0 <= nc < self.cols and not visited[nr][nc]
                    and (r, c, dir_idx) not in [(r, c, 0), (r, c, 1), (r, c, 2), (r, c, 3)]):
                    stack.append((nr, nc, (direction + dir_idx) % 4))
                    visited[nr][nc] = True
                    # 打通墙壁
                    self.cell(r, c)[dir_idx] = 1  # 0:上,1:右,2:下,3:左
                    # 对称开启对面方向
                    opp_dir = (dir_idx + 2) % 4
                    self.cell(nr, nc)[opp_dir] = 1
        # 确保出口在右下角
        if not (self.rows-2, self.cols-2) == (-self.cols, 1):
            self.cell(self.rows-2, self.cols-2)[2] = 1  # 向下开
            self.cell(self.rows-2, self.cols-1)[3] = 1  # 向左开
            self.cell(self.rows-1, self.cols-2)[2] = 1  # 向下开
            self.cell(self.rows-1, self.cols-2)[1] = 1  # 向右开

    def cell(self, r, c):
        return self.grid.get((r, c), None)

    def walls(self, r, c):
        w = [True, True, True, True]
        cell = self.cell(r, c)
        if cell:
            if cell[0]: w[0]=False
            if cell[1]: w[1]=False
            if cell[2]: w[2]=False
            if cell[3]: w[3]=False
        return w
    
    def is_path(self, r, c, direction):
        cell = self.cell(r, c)
        if cell:
            return cell[direction] == 1
        return False

# 玩家类
class Player:
    def __init__(self, start_x, start_y, color=BLUE):
        self.x = start_x
        self.y = start_y
        self.color = color
        self.speed = 4
    
    def move(self, dx, dy, maze):
        nx, ny = self.x + dx, self.y + dy
        if 0 <= nx < maze.cols and 0 <= ny < maze.rows:
            can_move = True
            # 添加简单的墙碰撞检测
            if dx > 0 and not maze.is_path(self.y, self.x, 1):
                can_move = can_move and maze.is_path(self.y, self.x, 1)
            if dx < 0 and not maze.is_path(self.y, self.x, 3):
                can_move = can_move and maze.is_path(self.y, self.x, 3)
            if dy > 0 and not maze.is_path(self.y, self.x, 2):
                can_move = can_move and maze.is_path(self.y, self.x, 2)
            if dy < 0 and not maze.is_path(self.y, self.x, 0):
                can_move = can_move and maze.is_path(self.y, self.x, 0)
            
            if can_move:
                self.x, self.y = nx, ny

    def draw(self, surface, camera_x, camera_y):
        rect = pygame.Rect(
            self.x * TILE_SIZE - camera_x + (TILE_SIZE - PLAYER_SIZE) // 2,
            self.y * TILE_SIZE - camera_y + (TILE_SIZE - PLAYER_SIZE) // 2,
            PLAYER_SIZE, PLAYER_SIZE
        )
        pygame.draw.rect(surface, self.color, rect)

# 游戏的主要逻辑
class Game:
    def __init__(self):
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Maze Runner Easy")
        self.clock = pygame.time.Clock()
        self.running = True
        self.maze = Maze(20, 20)
        self.player = Player(1, 1)
        self.start_time = None
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 28)
        
    def configure_maze(self):
        # 创建门和墙壁的简单直角迷宫
        self.maze_data = [[1]*(maze.cols+2) for _ in range(maze.rows+2)]
        for r in range(maze.rows):
            for c in range(maze.cols):
                if maze.grid.get((r, c), [0,0,0,0]) != [0, 0, 0, 0]:
                    self.maze_data[r+1][c+1] = 0
        return self.maze_data

    def get_key(self):
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 1
        return dx, dy

    def process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

        keys = self.get_key()
        dx, dy = keys
        new_x, new_y = self.player.x + dx, self.player.y + dy
        
        # 碰撞检测
        if 0 <= new_x < self.maze.cols and 0 <= new_y < self.maze.rows:
            if self.maze.grid.get((new_y, new_x)) is not None:  # 检查是否为有效格子
                if dx != 0 or dy != 0:
                    # 简单检测前后左右是否有墙
                    if (dx > 0 and new_x < self.maze.cols) and not (new_x, new_y) in visited:  # 临时简单检测
                        self.player.x, self.player.y = new_x, new_y
                        self.visited_grid.append([new_y, new_x])

    def update(self):
        self.last_rect = self.player.rect
        self.player.move(n)
        if self.player.x == self.tile_size * len(self.current_maze.done[0]) - 10:
            return "win"
        # 其他上屏动画等...
    
    def render(self, surface):
        surface.fill((30, 30, 50))  # 深蓝色背景

        # 绘制砖墙地图
        wall_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        wall_surf.fill((200, 200, 200))
        px = self.screen.get_width() // 2
        py = self.screen.get_height() // 2
        
        # 简单的上色和绘制
        for y in range(self.rows):
            for x in range(self.cols):
                rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                is_path = self.maze.is_path(y,x)
                col = FLOOR_COLOR if is_path else WALL_COLOR
                pygame.draw.rect(surface, col, rect)
                if not is_path:
                    pygame.draw.rect(surface, WALL_HIGHLIGHT, rect,2)
                nbs = [(y-1,x),(y+1,x),(y,x-1),(y,x+1)]
                for ny,nx in nbs:
                    if (self.maze.get(y,x) and 0 <= ny < self.rows and 0 <= nx < self.cols) or not self.maze.get(ny, nx):
                        pass  # 墙边缘高亮
        # 用算法绘制整个迷宫效果...

        # 画终点
        exit_rect = ((maze.cols-1)*TILE_SIZE, (maze.rows-1)*TILE_SIZE, TILE_SIZE, TILE_SIZE)
        target_surf = self.render_text('E', 36, (0,0,0))
        text_rect = target_surf.get_rect(center=(exit_rect.x+TILE_SIZE//2,exit_rect.y+TILE_SIZE//2))
        self.screen.blit(text_surface, text_rect)

    def gameplay(self):
        start_time = time.time()
        is_completed = False
        self.msg = "Use Arrow Keys to Move. Reach the (E)xit!"
        
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.restart()
                if event.type == pygame.MOUSEBUTTONDOWN and is_completed:
                    pass # 游戏已胜利
            # process input
            keys = pygame.key.get_pressed()
            # ... 处理移动 ...

            # 检查到达出口
            if (self.player.x, self.player.y) == (self.maze.cols - 1, self.maze.rows - 1):
                total_time = time.time() - start_time
                self.win_time = total_time
                self.win = True
                
            # 绘制所有
            self.screen.fill((0,0,30))
            # 绘制迷宫
            # 绘制玩家
            # 显示信息
            # ...

            if is_completed:
                # 显示胜利信息
                show_win()
            pygame.display.flip()
            self.clock.tick(30)  # 控制帧率

pygame.quit()

if __name__ == "__main__":
    game = Game()
    while game.running:
        game.play()