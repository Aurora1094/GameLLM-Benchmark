import pygame
import random

pygame.init()

# 屏幕设置
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Flappy Bird Easy')

# 颜色
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)

# 时钟
clock = pygame.time.Clock()
FPS = 30

# 字体
font = pygame.font.SysFont(None, 55)

def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, 1, color)
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

class Bird(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(center=(100, SCREEN_HEIGHT // 2))
        self.velocity = 0

    def update(self):
        self.velocity += 1
        self.rect.y += self.velocity

    def jump(self):
        self.velocity = -15

class Pipe(pygame.sprite.Sprite):
    def __init__(self, x, y, position):
        super().__init__()
        self.image = pygame.Surface((50, 300))
        self.image.fill(GREEN)
        if position == 1:
            self.image = pygame.transform.flip(self.image, False, True)
            self.rect = self.image.get_rect(midbottom=(x, y - 150))
        else:
            self.rect = self.image.get_rect(midtop=(x, y + 150))

    def update(self):
        self.rect.x -= 5

def game():
    bird_group = pygame.sprite.Group()
    pipe_group = pygame.sprite.Group()
    bird = Bird()
    bird_group.add(bird)

    pipe_frequency = 1500
    last_pipe = pygame.time.get_ticks() - pipe_frequency
    score = 0
    pass_pipe = False

    run = True
    while run:
        screen.fill(WHITE)
        bird_group.draw(screen)
        bird_group.update()
        pipe_group.draw(screen)
        pipe_group.update()

        time_now = pygame.time.get_ticks()
        if time_now - last_pipe > pipe_frequency:
            pipe_height = random.randint(-100, 100)
            btm_pipe = Pipe(SCREEN_WIDTH, SCREEN_HEIGHT // 2 + pipe_height, -1)
            top_pipe = Pipe(SCREEN_WIDTH, SCREEN_HEIGHT // 2 + pipe_height, 1)
            pipe_group.add(btm_pipe)
            pipe_group.add(top_pipe)
            last_pipe = time_now

        if pygame.sprite.groupcollide(bird_group, pipe_group, False, False) or bird.rect.top < 0 or bird.rect.bottom > SCREEN_HEIGHT:
            run = False

        if bird.rect.left > SCREEN_WIDTH // 2 and not pass_pipe:
            pass_pipe = True
        if pass_pipe:
            if bird.rect.left < SCREEN_WIDTH // 2 + 50:
                score += 1
                pass_pipe = False

        draw_text(str(score), font, GREEN, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_UP:
                    bird.jump()

        pygame.display.update()
        clock.tick(FPS)

    draw_text('Game Over! Press R to Restart or Q to Quit', font, GREEN, screen, 80, SCREEN_HEIGHT // 2)
    pygame.display.update()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game()
                if event.key == pygame.K_q:
                    pygame.quit()

game()