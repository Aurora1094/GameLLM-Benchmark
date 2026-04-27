import pygame
import random
import sys

pygame.init()

# Constants
WIDTH, HEIGHT = 800, 600
PLAYER_WIDTH, PLAYER_HEIGHT = 50, 50
BLOCK_SIZE = 50
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
FPS = 60

# Setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dodge Blocks Easy")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)

def game():
    player = pygame.Rect(WIDTH // 2, HEIGHT - PLAYER_HEIGHT - 10, PLAYER_WIDTH, PLAYER_HEIGHT)
    blocks = []
    score = 0
    start_time = pygame.time.get_ticks()

    running = True
    while running:
        current_time = pygame.time.get_ticks()
        elapsed_time = (current_time - start_time) / 1000

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and player.left > 0:
            player.x -= 5
        if keys[pygame.K_RIGHT] and player.right < WIDTH:
            player.x += 5

        if random.randint(1, 30) == 1:
            block = pygame.Rect(random.randint(0, WIDTH - BLOCK_SIZE), 0, BLOCK_SIZE, BLOCK_SIZE)
            blocks.append(block)

        for block in blocks:
            block.y += 5
            if block.colliderect(player):
                running = False
            if block.top > HEIGHT:
                blocks.remove(block)
                score += 1

        screen.fill(BLACK)
        pygame.draw.rect(screen, WHITE, player)
        for block in blocks:
            pygame.draw.rect(screen, RED, block)

        draw_text(f'Score: {score}', font, WHITE, screen, WIDTH // 2, 30)
        draw_text(f'Time: {elapsed_time:.2f}', font, WHITE, screen, WIDTH // 2, 60)

        pygame.display.flip()
        clock.tick(FPS)

    draw_text('Game Over', font, WHITE, screen, WIDTH // 2, HEIGHT // 2 - 50)
    draw_text(f'Score: {score}', font, WHITE, screen, WIDTH // 2, HEIGHT // 2)
    draw_text('Press R to Restart or Q to Quit', font, WHITE, screen, WIDTH // 2, HEIGHT // 2 + 50)
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game()
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

game()