import pygame
import random
import sys

pygame.init()
random.seed(42)

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
PLAYER_SIZE = 60
PLAYER_COLOR = (0, 255, 0)
PLAYER_SPEED = 7
PLAYER_BOTTOM_OFFSET = 40
BLOCK_SIZE = 40
BLOCK_COLOR = (255, 0, 0)
BLOCK_SPAWN_RATE = 40
BLOCK_MIN_SPEED = 4
BLOCK_MAX_SPEED = 8
BACKGROUND_COLOR = (0, 0, 0)
TEXT_COLOR = (255, 255, 255)
FONT = pygame.font.SysFont(None, 36)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dodge Blocks Easy")
clock = pygame.time.Clock()

def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.topleft = (x, y)
    surface.blit(textobj, textrect)

class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE))
        self.image.fill(PLAYER_COLOR)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - PLAYER_BOTTOM_OFFSET

    def update(self, direction):
        if direction == "left":
            self.rect.x -= PLAYER_SPEED
        elif direction == "right":
            self.rect.x += PLAYER_SPEED
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

class Block(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE))
        self.image.fill(BLOCK_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - BLOCK_SIZE)
        self.rect.y = 0
        self.speed = random.randint(BLOCK_MIN_SPEED, BLOCK_MAX_SPEED)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()

def game():
    all_sprites = pygame.sprite.Group()
    blocks = pygame.sprite.Group()
    player = Player()
    all_sprites.add(player)
    spawn_block_event = pygame.USEREVENT
    pygame.time.set_timer(spawn_block_event, 1000 // BLOCK_SPAWN_RATE)
    start_ticks = pygame.time.get_ticks()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == spawn_block_event:
                block = Block()
                all_sprites.add(block)
                blocks.add(block)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            player.update("left")
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            player.update("right")

        all_sprites.update()
        if pygame.sprite.spritecollideany(player, blocks):
            seconds = (pygame.time.get_ticks() - start_ticks) / 1000
            score = int(seconds)
            game_over(score)

        screen.fill(BACKGROUND_COLOR)
        all_sprites.draw(screen)
        seconds = (pygame.time.get_ticks() - start_ticks) / 1000
        draw_text(f"Score: {int(seconds)}", FONT, TEXT_COLOR, screen, 10, 10)
        pygame.display.flip()
        clock.tick(FPS)

def game_over(score):
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game()
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        screen.fill(BACKGROUND_COLOR)
        draw_text("Game Over", FONT, TEXT_COLOR, screen, SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2 - 30)
        draw_text(f"Score: {score}", FONT, TEXT_COLOR, screen, SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 + 10)
        draw_text("Press R to Restart", FONT, TEXT_COLOR, screen, SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50)
        pygame.display.flip()
        clock.tick(FPS)

game()