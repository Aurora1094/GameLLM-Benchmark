import pygame
import random
import sys

pygame.init()

# 屏幕尺寸
SCREEN_WIDTH = 300
SCREEN_HEIGHT = 600
GRID_SIZE = 30
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

# 颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (150, 150, 150)
COLORS = [
    (0, 255, 255),  # Cyan
    (255, 255, 0),  # Yellow
    (0, 0, 255),    # Blue
    (255, 165, 0),  # Orange
    (0, 255, 0),    # Green
    (255, 0, 0),    # Red
    (128, 0, 128)   # Purple
]

SHAPES = [
    [[1, 1, 1, 1]],
    [[1, 1], [1, 1]],
    [[1, 1, 1], [0, 1, 0]],
    [[1, 1, 0], [0, 1, 1]],
    [[0, 1, 1], [1, 1, 0]],
    [[1, 1, 0], [1, 1, 0]],
    [[0, 1, 1], [1, 1, 0]]
]

class Tetromino:
    def __init__(self, shape):
        self.shape = shape
        self.color = COLORS[SHAPES.index(shape)]
        self.rotation = 0
        self.x = GRID_WIDTH // 2 - len(shape[0]) // 2
        self.y = 0

    def rotate(self):
        self.rotation = (self.rotation + 1) % len(self.shape)

    def image(self):
        return self.shape[self.rotation]

def check_collision(grid, shape, offset):
    off_x, off_y = offset
    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell and (off_y + y >= GRID_HEIGHT or off_x + x < 0 or off_x + x >= GRID_WIDTH or grid[off_y + y][off_x + x]):
                return True
    return False

def remove_row(grid, row):
    del grid[row]
    return [[0 for _ in range(GRID_WIDTH)]] + grid

def move_down(grid, tetromino):
    while not check_collision(grid, tetromino.image(), (tetromino.x, tetromino.y + 1)):
        tetromino.y += 1
    place_tetromino(grid, tetromino)
    return clear_rows(grid)

def place_tetromino(grid, tetromino):
    for y, row in enumerate(tetromino.image()):
        for x, cell in enumerate(row):
            if cell:
                grid[tetromino.y + y][tetromino.x + x] = tetromino.color

def clear_rows(grid):
    new_grid = grid
    full_rows = [idx for idx, row in enumerate(new_grid) if 0 not in row]
    for idx in sorted(full_rows, reverse=True):
        new_grid = remove_row(new_grid, idx)
    return len(full_rows)

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tetris")
    clock = pygame.time.Clock()
    grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
    current_tetromino = Tetromino(random.choice(SHAPES))
    next_tetromino = Tetromino(random.choice(SHAPES))
    fall_time = 0
    fall_speed = 0.3
    score = 0

    running = True
    while running:
        fall_time += clock.get_rawtime()
        clock.tick()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    if not check_collision(grid, current_tetromino.image(), (current_tetromino.x - 1, current_tetromino.y)):
                        current_tetromino.x -= 1
                if event.key == pygame.K_RIGHT:
                    if not check_collision(grid, current_tetromino.image(), (current_tetromino.x + 1, current_tetromino.y)):
                        current_tetromino.x += 1
                if event.key == pygame.K_DOWN:
                    fall_speed = 0.1
                if event.key == pygame.K_UP:
                    current_tetromino.rotate()
                    if check_collision(grid, current_tetromino.image(), (current_tetromino.x, current_tetromino.y)):
                        current_tetromino.rotate()
                        current_tetromino.rotate()
                        current_tetromino.rotate()

        if fall_time / 1000 >= fall_speed:
            fall_time = 0
            if not check_collision(grid, current_tetromino.image(), (current_tetromino.x, current_tetromino.y + 1)):
                current_tetromino.y += 1
            else:
                rows_cleared = move_down(grid, current_tetromino)
                score += rows_cleared ** 2
                current_tetromino = next_tetromino
                next_tetromino = Tetromino(random.choice(SHAPES))
                if check_collision(grid, current_tetromino.image(), (current_tetromino.x, current_tetromino.y)):
                    running = False

        screen.fill(BLACK)
        for y, row in enumerate(grid):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(screen, cell, (x * GRID_SIZE, y * GRID_SIZE, GRID_SIZE - 1, GRID_SIZE - 1))

        for y, row in enumerate(current_tetromino.image()):
            for x, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(screen, current_tetromino.color, ((current_tetromino.x + x) * GRID_SIZE, (current_tetromino.y + y) * GRID_SIZE, GRID_SIZE - 1, GRID_SIZE - 1))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()