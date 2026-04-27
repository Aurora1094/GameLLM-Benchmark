import pygame
import random
import sys

# 初始化Pygame
pygame.init()

# 游戏窗口设置
SCREEN_WIDTH = 300
SCREEN_HEIGHT = 600
BLOCK_SIZE = 30
GRID_WIDTH = SCREEN_WIDTH // BLOCK_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // BLOCK_SIZE

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
PURPLE = (128, 0, 128)
CYAN = (0, 255, 255)

# 7种方块形状及其颜色
SHAPES = [
    [[1, 1, 1, 1]],         # I形
    [[1, 1], [1, 1]],       # O形
    [[0, 1, 0], [1, 1, 1]], # T形
    [[0, 1, 1], [1, 1, 0]], # S形
    [[1, 1, 0], [0, 1, 1]], # Z形
    [[1, 0, 0], [1, 1, 1]], # J形
    [[0, 0, 1], [1, 1, 1]]  # L形
]

SHAPE_COLORS = [CYAN, YELLOW, PURPLE, GREEN, RED, BLUE, ORANGE]

# 创建游戏窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tetris Medium")

# 游戏时钟
clock = pygame.time.Clock()

class Tetromino:
    def __init__(self):
        self.index = random.randint(0, len(SHAPES) - 1)
        self.shape = SHAPES[self.index]
        self.color = SHAPE_COLORS[self.index]
        self.x = GRID_WIDTH // 2 - len(self.shape[0]) // 2
        self.y = 0
    
    def rotate(self):
        # 转置后反转行实现旋转
        self.shape = [list(row) for row in zip(*self.shape[::-1])]
    
    def move(self, dx, dy):
        self.x += dx
        self.y += dy

def create_grid(locked_positions={}):
    grid = [[0] * GRID_WIDTH for _ in range(GRID_HEIGHT)]
    for pos in locked_positions:
        x, y = pos
        color = locked_positions[pos]
        if 0 <= y < GRID_HEIGHT and 0 <= x < GRID_WIDTH:
            grid[y][x] = color
    return grid

def valid_move(piece, grid):
    for row in range(len(piece.shape)):
        for col in range(len(piece.shape[row])):
            if piece.shape[row][col]:
                x = piece.x + col
                y = piece.y + row
                if x < 0 or x >= GRID_WIDTH or y >= GRID_HEIGHT or (y >= 0 and grid[y][x] != 0):
                    return False
    return True

def clear_rows(grid, locked_positions):
    cleared = 0
    rows_to_clear = []
    for row in range(GRID_HEIGHT - 1, -1, -1):
        if all(grid[row][col] != 0 for col in range(GRID_WIDTH)):
            rows_to_clear.append(row)
    
    for row in rows_to_clear:
        for col in range(GRID_WIDTH):
            if (col, row) in locked_positions:
                del locked_positions[(col, row)]
    
    # 移除完整行后下方的方块下移
    if rows_to_clear:
        for pos in list(locked_positions.keys()):
            x, y = pos
            for cleared_row in rows_to_clear:
                if y < cleared_row:
                    locked_positions[(x, y + len(rows_to_clear))] = locked_positions[pos]
                    del locked_positions[pos]
    
    return len(rows_to_clear)

def draw_grid(grid):
    for y in range(GRID_HEIGHT):
        for x in range(GRID_WIDTH):
            color = grid[y][x]
            if color != 0:
                pygame.draw.rect(screen, color, (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE))
    
    # 绘制网格线
    for x in range(0, SCREEN_WIDTH, BLOCK_SIZE):
        pygame.draw.line(screen, (50, 50, 50), (x, 0), (x, SCREEN_HEIGHT))
    for y in range(0, SCREEN_HEIGHT, BLOCK_SIZE):
        pygame.draw.line(screen, (50, 50, 50), (0, y), (SCREEN_WIDTH, y))

def draw_text(text, font_size, x, y, color=WHITE):
    font = pygame.font.SysFont(None, font_size, bold=True)
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))

def main():
    locked_positions = {}
    grid = create_grid(locked_positions)
    current_piece = Tetromino()
    score = 0
    fall_time = 0
    fall_speed = 0.5  # 初始下落速度（秒/格）
    game_over = False
    
    # 游戏主循环
    while not game_over:
        grid = create_grid(locked_positions)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    current_piece.move(-1, 0)
                    if not valid_move(current_piece, grid):
                        current_piece.move(1, 0)
                elif event.key == pygame.K_RIGHT:
                    current_piece.move(1, 0)
                    if not valid_move(current_piece, grid):
                        current_piece.move(-1, 0)
                elif event.key == pygame.K_UP:
                    current_piece.rotate()
                    if not valid_move(current_piece, grid):
                        current_piece.rotate()
                        current_piece.rotate()
                        current_piece.rotate()
                elif event.key == pygame.K_DOWN:
                    current_piece.move(0, 1)
                    if not valid_move(current_piece, grid):
                        current_piece.move(0, -1)
        
        # 自动下落逻辑
        fall_time += clock.get_rawtime()
        if fall_time / 1000 >= fall_speed:
            fall_time = 0
            current_piece.move(0, 1)
            if not valid_move(current_piece, grid):
                current_piece.move(0, -1)
                
                # 将当前方块固定到网格
                for row in range(len(current_piece.shape)):
                    for col in range(len(current_piece.shape[row])):
                        if current_piece.shape[row][col]:
                            locked_positions[(current_piece.x + col, current_piece.y + row)] = current_piece.color
                
                # 消除完整行
                rows_cleared = clear_rows(grid, locked_positions)
                if rows_cleared > 0:
                    score += rows_cleared * 100
                
                # 生成新方块
                current_piece = Tetromino()
                
                # 检查游戏结束
                if not valid_move(current_piece, grid):
                    game_over = True
        
        # 渲染界面
        screen.fill(BLACK)
        
        # 绘制当前方块
        for row in range(len(current_piece.shape)):
            for col in range(len(current_piece.shape[row])):
                if current_piece.shape[row][col]:
                    pygame.draw.rect(screen, current_piece.color, 
                                   (current_piece.x * BLOCK_SIZE + col * BLOCK_SIZE,
                                    current_piece.y * BLOCK_SIZE + row * BLOCK_SIZE,
                                    BLOCK_SIZE, BLOCK_SIZE))
        
        draw_grid(grid)
        draw_text(f"Score: {score}", 24, 10, 10)
        
        if game_over:
            draw_text("GAME OVER", 48, SCREEN_WIDTH//2 - 90, SCREEN_HEIGHT//2 - 24, RED)
            draw_text("Press R to Restart", 24, SCREEN_WIDTH//2 - 105, SCREEN_HEIGHT//2 + 24, WHITE)
        
        pygame.display.flip()
        
        # 处理游戏结束后的重新开始
        if game_over:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_r]:
                locked_positions = {}
                score = 0
                grid = create_grid(locked_positions)
                current_piece = Tetromino()
                game_over = False
                fall_time = 0
        
        clock.tick(60)

if __name__ == "__main__":
    main()