import pygame
import sys
import random

# Constants
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
FPS = 60
MAZE_COLS, MAZE_ROWS = 21, 15
CELL_SIZE = 32
MAZE_WIDTH, MAZE_HEIGHT = MAZE_COLS * CELL_SIZE, MAZE_ROWS * CELL_SIZE
MAZE_OFFSET_X = (SCREEN_WIDTH - MAZE_WIDTH) // 2
MAZE_OFFSET_Y = (SCREEN_HEIGHT - MAZE_HEIGHT) // 2

# Colors
BACKGROUND_COLOR = (20, 20, 30)
WALL_COLOR = (50, 50, 90)
PATH_COLOR = (240, 240, 255)
PLAYER_COLOR = (80, 200, 255)
EXIT_COLOR = (255, 100, 100)
TEXT_COLOR = (255, 255, 200)
HUD_BG_COLOR = (30, 30, 45, 200)

# Fixed random seed
random.seed(42)

def generate_maze():
    # Initialize grid: 1 for walls, 0 for paths
    grid = [[1 for _ in range(MAZE_COLS)] for __ in range(MAZE_ROWS)]
    
    # DFS to carve paths
    stack = []
    start_x, start_y = 0, 0
    # Ensure start is a path
    grid[start_y][start_x] = 0
    stack.append((start_x, start_y))
    
    # Directions: (dx, dy)
    directions = [(-2, 0), (2, 0), (0, -2), (0, 2)]
    
    while stack:
        x, y = stack[-1]
        # Find unvisited neighbors
        neighbors = []
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < MAZE_COLS and 0 <= ny < MAZE_ROWS and grid[ny][nx] == 1:
                neighbors.append((nx, ny, dx, dy))
        if neighbors:
            nx, ny, dx, dy = random.choice(neighbors)
            # Carve path between current and chosen neighbor
            grid[ny][nx] = 0
            grid[y + dy//2][x + dx//2] = 0
            stack.append((nx, ny))
        else:
            stack.pop()
    
    # Ensure bottom-right cell is clear (exit)
    grid[MAZE_ROWS-1][MAZE_COLS-1] = 0
    # Ensure left-top cell is clear (start)
    grid[0][0] = 0
    
    return grid

def draw_maze(surface, grid):
    for y in range(MAZE_ROWS):
        for x in range(MAZE_COLS):
            rect = pygame.Rect(MAZE_OFFSET_X + x * CELL_SIZE, MAZE_OFFSET_Y + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            color = WALL_COLOR if grid[y][x] == 1 else PATH_COLOR
            pygame.draw.rect(surface, color, rect)
            pygame.draw.rect(surface, BACKGROUND_COLOR, rect, 1)

def draw_player(surface, player_pos):
    x, y = player_pos
    rect = pygame.Rect(MAZE_OFFSET_X + x * CELL_SIZE, MAZE_OFFSET_Y + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(surface, PLAYER_COLOR, rect)
    pygame.draw.rect(surface, (255, 255, 255), rect, 2)

def draw_exit(surface):
    x, y = MAZE_COLS - 1, MAZE_ROWS - 1
    rect = pygame.Rect(MAZE_OFFSET_X + x * CELL_SIZE, MAZE_OFFSET_Y + y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
    pygame.draw.rect(surface, EXIT_COLOR, rect)
    pygame.draw.rect(surface, (255, 255, 255), rect, 2)

def draw_hud(surface, elapsed_time, win):
    # HUD background
    hud_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 40)
    s = pygame.Surface((SCREEN_WIDTH, 40), pygame.SRCALPHA)
    s.fill(HUD_BG_COLOR)
    surface.blit(s, hud_rect)
    
    font = pygame.font.SysFont(None, 30)
    time_text = font.render(f"Time: {elapsed_time:.2f}s", True, TEXT_COLOR)
    surface.blit(time_text, (10, 10))
    
    restart_text = font.render("Press R to Restart, ESC to Quit", True, TEXT_COLOR)
    surface.blit(restart_text, (SCREEN_WIDTH - restart_text.get_width() - 10, 10))
    
    if win:
        font_large = pygame.font.SysFont(None, 60)
        win_text = font_large.render("You Win!", True, TEXT_COLOR)
        surface.blit(win_text, (SCREEN_WIDTH//2 - win_text.get_width()//2, MAZE_OFFSET_Y + MAZE_HEIGHT//2 - 80))
        
        time_msg = font_large.render(f"Time: {elapsed_time:.2f}s", True, TEXT_COLOR)
        surface.blit(time_msg, (SCREEN_WIDTH//2 - time_msg.get_width()//2, MAZE_OFFSET_Y + MAZE_HEIGHT//2))
        
        restart_msg = font.render("Press R to Restart", True, TEXT_COLOR)
        surface.blit(restart_msg, (SCREEN_WIDTH//2 - restart_msg.get_width()//2, MAZE_OFFSET_Y + MAZE_HEIGHT//2 + 60))

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Maze Runner Easy")
    clock = pygame.time.Clock()
    
    grid = generate_maze()
    player_pos = [0, 0]  # Start at top-left
    exit_pos = [MAZE_COLS - 1, MAZE_ROWS - 1]
    
    win = False
    start_time = None
    current_time = 0.0
    
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # Delta time in seconds
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_r:
                    # Restart
                    grid = generate_maze()
                    player_pos = [0, 0]
                    win = False
                    start_time = None
                    current_time = 0.0
        
        if not win:
            if start_time is None:
                start_time = pygame.time.get_ticks() / 1000.0
            else:
                current_time = pygame.time.get_ticks() / 1000.0 - start_time
        
        # Player movement
        if not win:
            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_LEFT]:
                dx = -1
            elif keys[pygame.K_RIGHT]:
                dx = 1
            elif keys[pygame.K_UP]:
                dy = -1
            elif keys[pygame.K_DOWN]:
                dy = 1
            
            if dx != 0 or dy != 0:
                new_x = player_pos[0] + dx
                new_y = player_pos[1] + dy
                if 0 <= new_x < MAZE_COLS and 0 <= new_y < MAZE_ROWS:
                    if grid[new_y][new_x] == 0:
                        player_pos[0] = new_x
                        player_pos[1] = new_y
        
        # Check win condition
        if player_pos[0] == exit_pos[0] and player_pos[1] == exit_pos[1]:
            win = True
        
        # Drawing
        screen.fill(BACKGROUND_COLOR)
        draw_maze(screen, grid)
        draw_exit(screen)
        draw_player(screen, player_pos)
        draw_hud(screen, current_time, win)
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()