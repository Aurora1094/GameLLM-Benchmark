import pygame
import random
import time

pygame.init()

display_width = 800
display_height = 600
cell_size = 20
player_size = 18
wall_color = (0, 0, 0)
player_color = (0, 255, 0)
exit_color = (255, 0, 0)

game_display = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption('Maze Runner Easy')

clock = pygame.time.Clock()

def generate_maze(width, height):
    maze = [[0 for _ in range(height)] for _ in range(width)]
    for x in range(width):
        for y in range(height):
            if x == 0 or y == 0 or x == width-1 or y == height-1:
                maze[x][y] = 1
            else:
                maze[x][y] = random.choice([0, 0, 0, 1])
    return maze

def draw_maze(maze):
    for x in range(len(maze)):
        for y in range(len(maze[0])):
            if maze[x][y] == 1:
                pygame.draw.rect(game_display, wall_color, (x*cell_size, y*cell_size, cell_size, cell_size))

def draw_player(x, y):
    pygame.draw.rect(game_display, player_color, (x, y, player_size, player_size))

def draw_exit(x, y):
    pygame.draw.rect(game_display, exit_color, (x, y, player_size, player_size))

def game_loop():
    game_exit = False
    game_over = False

    maze_width = display_width // cell_size
    maze_height = display_height // cell_size
    maze = generate_maze(maze_width, maze_height)

    player_x = cell_size
    player_y = cell_size
    player_x_change = 0
    player_y_change = 0

    exit_x = (maze_width - 2) * cell_size
    exit_y = (maze_height - 2) * cell_size

    start_time = time.time()

    while not game_exit:
        if game_over:
            game_display.fill((0, 0, 0))
            font = pygame.font.SysFont(None, 50)
            text = font.render('Game Over! Press R to Restart or Q to Quit', True, (255, 255, 255))
            game_display.blit(text, (display_width // 6, display_height // 3))
            pygame.display.update()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_exit = True
                    if event.key == pygame.K_r:
                        game_loop()
        else:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_exit = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        player_x_change = -cell_size
                        player_y_change = 0
                    elif event.key == pygame.K_RIGHT:
                        player_x_change = cell_size
                        player_y_change = 0
                    elif event.key == pygame.K_UP:
                        player_y_change = -cell_size
                        player_x_change = 0
                    elif event.key == pygame.K_DOWN:
                        player_y_change = cell_size
                        player_x_change = 0
                if event.type == pygame.KEYUP:
                    if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                        player_x_change = 0
                    elif event.key in (pygame.K_UP, pygame.K_DOWN):
                        player_y_change = 0

            if (0 <= player_x + player_x_change < display_width and
                0 <= player_y + player_y_change < display_height and
                maze[(player_x + player_x_change) // cell_size][(player_y + player_y_change) // cell_size] == 0):
                player_x += player_x_change
                player_y += player_y_change

            game_display.fill((255, 255, 255))
            draw_maze(maze)
            draw_player(player_x, player_y)
            draw_exit(exit_x, exit_y)

            if player_x == exit_x and player_y == exit_y:
                end_time = time.time()
                font = pygame.font.SysFont(None, 50)
                text = font.render(f'You Win! Time: {end_time - start_time:.2f} seconds', True, (0, 255, 0))
                game_display.blit(text, (display_width // 6, display_height // 3))
                game_over = True

        pygame.display.update()
        clock.tick(15)

    pygame.quit()
    quit()

game_loop()