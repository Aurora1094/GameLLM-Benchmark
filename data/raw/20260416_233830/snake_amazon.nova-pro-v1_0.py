import pygame
import random
import sys

pygame.init()
random.seed(42)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_WIDTH = 30
GRID_HEIGHT = 24
CELL_SIZE = 20
GRID_AREA_WIDTH = GRID_WIDTH * CELL_SIZE
GRID_AREA_HEIGHT = GRID_HEIGHT * CELL_SIZE
FPS = 60
SNAKE_SPEED = 10

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Snake Easy")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

def draw_grid():
    for x in range(0, GRID_AREA_WIDTH, CELL_SIZE):
        for y in range(0, GRID_AREA_HEIGHT, CELL_SIZE):
            rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, WHITE, rect, 1)

def draw_hud(score):
    text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(text, (10, 10))

def game_over(score):
    screen.fill(BLACK)
    text = font.render("Game Over", True, RED)
    score_text = font.render(f"Score: {score}", True, WHITE)
    restart_text = font.render("Press R to Restart", True, WHITE)
    screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - text.get_height() // 2))
    screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, SCREEN_HEIGHT // 2))
    screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))
    pygame.display.flip()

def reset_game():
    snake = [(GRID_WIDTH // 2, GRID_HEIGHT // 2 + i) for i in range(3)]
    direction = (1, 0)
    food = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
    while food in snake:
        food = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
    score = 0
    return snake, direction, food, score

snake, direction, food, score = reset_game()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_r:
                snake, direction, food, score = reset_game()
            elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                new_direction = (0, -1) if event.key == pygame.K_UP else (0, 1) if event.key == pygame.K_DOWN else (-1, 0) if event.key == pygame.K_LEFT else (1, 0)
                if (new_direction[0] * -1, new_direction[1] * -1)!= direction:
                    direction = new_direction

    new_head = (snake[0][0] + direction[0], snake[0][1] + direction[1])
    snake.insert(0, new_head)

    if (new_head[0] < 0 or new_head[0] >= GRID_WIDTH or new_head[1] < 0 or new_head[1] >= GRID_HEIGHT or new_head in snake[1:]):
        game_over(score)
        waiting_for_restart = True
        while waiting_for_restart:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    waiting_for_restart = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    snake, direction, food, score = reset_game()
                    waiting_for_restart = False

    if new_head == food:
        food = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
        while food in snake:
            food = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
        score += 10
    else:
        snake.pop()

    screen.fill(BLACK)
    draw_grid()
    draw_hud(score)
    for segment in snake:
        pygame.draw.rect(screen, GREEN, (segment[0] * CELL_SIZE + GRID_AREA_WIDTH // 2 - GRID_WIDTH * CELL_SIZE // 2, segment[1] * CELL_SIZE + 10, CELL_SIZE, CELL_SIZE))
    pygame.draw.rect(screen, RED, (food[0] * CELL_SIZE + GRID_AREA_WIDTH // 2 - GRID_WIDTH * CELL_SIZE // 2, food[1] * CELL_SIZE + 10, CELL_SIZE, CELL_SIZE))
    pygame.display.flip()
    clock.tick(FPS // SNAKE_SPEED)

pygame.quit()
sys.exit()