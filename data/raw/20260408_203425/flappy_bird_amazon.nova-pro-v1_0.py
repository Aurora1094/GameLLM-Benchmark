import pygame
import random

pygame.init()

# Constants
WIDTH, HEIGHT = 400, 600
BIRD_WIDTH, BIRD_HEIGHT = 40, 30
PIPE_WIDTH = 70
FPS = 60
GRAVITY = 0.5
BIRD_FLAP = -10
FONT = pygame.font.SysFont('Arial', 30)

# Colors
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)

# Setup
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird Easy")
clock = pygame.time.Clock()

# Bird
bird_x = 50
bird_y = HEIGHT // 2
bird_y_vel = 0

# Pipes
pipes = []

def create_pipe():
    gap = 200
    pipe_height = random.randint(100, HEIGHT - gap - 100)
    pipes.append([WIDTH, pipe_height - gap // 2, gap])
    pipes.append([WIDTH, pipe_height + gap // 2, HEIGHT - pipe_height - gap // 2])

def draw_bird(x, y):
    pygame.draw.rect(screen, GREEN, (x, y, BIRD_WIDTH, BIRD_HEIGHT))

def draw_pipe(x, y, height):
    pygame.draw.rect(screen, GREEN, (x, y, PIPE_WIDTH, height))

def game_over():
    screen.fill(WHITE)
    text = FONT.render("Game Over! Press R to Restart", True, GREEN)
    screen.blit(text, (WIDTH // 4, HEIGHT // 2))
    pygame.display.update()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True
        pygame.time.delay(100)
    return False

def main():
    global bird_y, bird_y_vel, pipes
    score = 0
    create_pipe()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    bird_y_vel = BIRD_FLAP

        bird_y_vel += GRAVITY
        bird_y += bird_y_vel

        screen.fill(WHITE)

        if pipes[0][0] < -PIPE_WIDTH:
            pipes.pop(0)
            pipes.pop(0)
            score += 1
            create_pipe()

        for pipe in pipes:
            pipe[0] -= 5
            if bird_x + BIRD_WIDTH > pipe[0] and bird_x < pipe[0] + PIPE_WIDTH:
                if bird_y < pipe[1] or bird_y + BIRD_HEIGHT > pipe[1] + pipe[2]:
                    running = game_over()
                    bird_y = HEIGHT // 2
                    bird_y_vel = 0
                    pipes.clear()
                    score = 0
                    create_pipe()

            draw_pipe(pipe[0], pipe[1], pipe[2])

        if bird_y > HEIGHT or bird_y < 0:
            running = game_over()
            bird_y = HEIGHT // 2
            bird_y_vel = 0
            pipes.clear()
            score = 0
            create_pipe()

        draw_bird(bird_x, bird_y)
        screen.blit(FONT.render(f'Score: {score}', True, GREEN), (10, 10))
        pygame.display.update()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()