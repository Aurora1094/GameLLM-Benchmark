import pygame
import sys
import random
import time

pygame.init()
random.seed(42)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
MAZE_WIDTH = 21
MAZE_HEIGHT = 15
TILE_SIZE = 32
MAZE_X = (SCREEN_WIDTH - MAZE_WIDTH * TILE_SIZE) // 2
MAZE_Y = (SCREEN_HEIGHT - MAZE_HEIGHT * TILE_SIZE) // 2

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Maze Runner Easy")
clock = pygame.time.Clock()

def generate_maze():
    maze = [[1 for _ in range(MAZE_WIDTH)] for _ in range(MAZE_HEIGHT)]
    start = (1, 1)
    end = (MAZE_HEIGHT - 2, MAZE_WIDTH - 2)
    maze[start[0]][start[1]] = 0
    maze[end[0]][end[1]] = 0

    def is_valid(x, y):
        return 0 <= x < MAZE_HEIGHT and 0 <= y < MAZE_WIDTH and maze[x][y] == 1

    def dfs(x, y):
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = x + 2 * dx, y + 2 * dy
            if is_valid(nx, ny):
                maze[nx][ny] = 0
                maze[x + dx][y + dy] = 0
                dfs(nx, ny)

    dfs(start[0], start[1])
    return maze

maze = generate_maze()
player_pos = [1, 1]
start_time = time.time()
game_over = False

def draw_maze():
    for y in range(MAZE_HEIGHT):
        for x in range(MAZE_WIDTH):
            if maze[y][x] == 1:
                pygame.draw.rect(screen, BLACK, (MAZE_X + x * TILE_SIZE, MAZE_Y + y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
            elif maze[y][x] == 0:
                pygame.draw.rect(screen, WHITE, (MAZE_X + x * TILE_SIZE, MAZE_Y + y * TILE_SIZE, TILE_SIZE, TILE_SIZE))

def draw_player():
    pygame.draw.rect(screen, GREEN, (MAZE_X + player_pos[1] * TILE_SIZE, MAZE_Y + player_pos[0] * TILE_SIZE, TILE_SIZE, TILE_SIZE))

def draw_exit():
    pygame.draw.rect(screen, RED, (MAZE_X + (MAZE_WIDTH - 2) * TILE_SIZE, MAZE_Y + (MAZE_HEIGHT - 2) * TILE_SIZE, TILE_SIZE, TILE_SIZE))

def draw_hud():
    font = pygame.font.Font(None, 36)
    elapsed_time = int(time.time() - start_time) if not game_over else int(time.time() - start_time)
    text = font.render(f"Time: {elapsed_time}s", True, YELLOW)
    screen.blit(text, (20, 20))

    if game_over:
        win_text = font.render("You Win", True, YELLOW)
        screen.blit(win_text, (SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 - 30))
        restart_text = font.render("Press R to Restart", True, YELLOW)
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 30))

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            if event.key == pygame.K_r and game_over:
                maze = generate_maze()
                player_pos = [1, 1]
                start_time = time.time()
                game_over = False

    if not game_over:
        keys = pygame.key.get_pressed()
        new_pos = player_pos.copy()

        if keys[pygame.K_UP] and maze[player_pos[0] - 1][player_pos[1]] == 0:
            new_pos[0] -= 1
        if keys[pygame.K_DOWN] and maze[player_pos[0] + 1][player_pos[1]] == 0:
            new_pos[0] += 1
        if keys[pygame.K_LEFT] and maze[player_pos[0]][player_pos[1] - 1] == 0:
            new_pos[1] -= 1
        if keys[pygame.K_RIGHT] and maze[player_pos[0]][player_pos[1] + 1] == 0:
            new_pos[1] += 1

        if new_pos!= player_pos:
            player_pos = new_pos
            if player_pos == [MAZE_HEIGHT - 2, MAZE_WIDTH - 2]:
                game_over = True

    screen.fill(BLUE)
    draw_maze()
    draw_player()
    draw_exit()
    draw_hud()
    pygame.display.flip()
    clock.tick(FPS)