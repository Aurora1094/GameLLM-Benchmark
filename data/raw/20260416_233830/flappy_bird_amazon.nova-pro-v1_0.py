import pygame
import random
import sys

pygame.init()
random.seed(42)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
BIRD_SIZE = (40, 30)
BIRD_START_POS = (160, 300)
GRAVITY = 0.35
FLAP_STRENGTH = -7.5
PIPE_WIDTH = 80
PIPE_GAP = 170
PIPE_VELOCITY = 3
SPAWN_PIPE_INTERVAL = 90
GROUND_HEIGHT = 20

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird Easy")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 55)

def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    surface.blit(textobj, textrect)

class Bird:
    def __init__(self):
        self.rect = pygame.Rect(BIRD_START_POS[0], BIRD_START_POS[1], *BIRD_SIZE)
        self.velocity = 0

    def flap(self):
        self.velocity = FLAP_STRENGTH

    def update(self):
        self.velocity += GRAVITY
        self.rect.y += int(self.velocity)

    def draw(self, surface):
        pygame.draw.rect(surface, (255, 255, 0), self.rect)

class Pipe:
    def __init__(self, x):
        gap_center = random.randint(PIPE_GAP // 2, SCREEN_HEIGHT - PIPE_GAP // 2)
        self.top_rect = pygame.Rect(x, 0, PIPE_WIDTH, gap_center - PIPE_GAP // 2)
        self.bottom_rect = pygame.Rect(x, gap_center + PIPE_GAP // 2, PIPE_WIDTH, SCREEN_HEIGHT - (gap_center + PIPE_GAP // 2))
        self.passed = False

    def update(self):
        self.top_rect.x -= PIPE_VELOCITY
        self.bottom_rect.x -= PIPE_VELOCITY

    def draw(self, surface):
        pygame.draw.rect(surface, (0, 255, 0), self.top_rect)
        pygame.draw.rect(surface, (0, 255, 0), self.bottom_rect)

def game():
    bird = Bird()
    pipes = []
    score = 0
    frame_count = 0
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    bird.flap()
                if event.key == pygame.K_r:
                    return

        frame_count += 1
        if frame_count % SPAWN_PIPE_INTERVAL == 0:
            pipes.append(Pipe(SCREEN_WIDTH))

        bird.update()
        for pipe in pipes:
            pipe.update()
            if not pipe.passed and bird.rect.right > pipe.top_rect.right:
                pipe.passed = True
                score += 1
            if bird.rect.colliderect(pipe.top_rect) or bird.rect.colliderect(pipe.bottom_rect):
                running = False
        if bird.rect.top <= 0 or bird.rect.bottom >= SCREEN_HEIGHT:
            running = False

        pipes = [pipe for pipe in pipes if pipe.top_rect.right > 0]

        screen.fill((135, 206, 235))
        bird.draw(screen)
        for pipe in pipes:
            pipe.draw(screen)
        pygame.draw.rect(screen, (0, 128, 0), (0, SCREEN_HEIGHT - GROUND_HEIGHT, SCREEN_WIDTH, GROUND_HEIGHT))
        draw_text(str(score), font, (255, 255, 255), screen, SCREEN_WIDTH // 2, 50)
        pygame.display.flip()
        clock.tick(FPS)

    draw_text("Game Over", font, (255, 0, 0), screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3)
    draw_text(f"Score: {score}", font, (255, 0, 0), screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    draw_text("Press R to Restart", font, (255, 0, 0), screen, SCREEN_WIDTH // 2, 2 * SCREEN_HEIGHT // 3)
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r:
                    game()
                    return

while True:
    game()