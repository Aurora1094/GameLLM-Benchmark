import pygame, random, sys

pygame.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

BACKGROUND_COLOR = (100, 180, 255)
GROUND_COLOR = (222, 184, 135)
GROUND_HEIGHT = 80
PIPE_COLOR = (76, 175, 80)
PIPE_WIDTH = 80
PIPE_GAP = 170
PIPE_MIN_HEIGHT = 80
PIPE_MAX_HEIGHT = SCREEN_HEIGHT - GROUND_HEIGHT - PIPE_MIN_HEIGHT - PIPE_GAP
PIPE_SPEED = 3
PIPE_FREQUENCY = 90
BIRD_COLOR = (255, 204, 0)
BIRD_SIZE = (40, 30)
GRAVITY = 0.35
JUMP_STRENGTH = -7.5
TEXT_COLOR = (255, 255, 255)
GAME_OVER_COLOR = (200, 50, 50)

random.seed(42)

class Bird:
    def __init__(self):
        self.width, self.height = BIRD_SIZE
        self.x = 160
        self.y = SCREEN_HEIGHT // 2
        self.vel_y = 0
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def jump(self):
        self.vel_y = JUMP_STRENGTH

    def update(self):
        self.vel_y += GRAVITY
        self.y += self.vel_y
        self.rect.y = self.y

    def draw(self, screen):
        pygame.draw.rect(screen, BIRD_COLOR, self.rect, border_radius=8)

    def check_boundary(self):
        return self.y < 0 or self.y + self.height > SCREEN_HEIGHT - GROUND_HEIGHT

class PipePair:
    def __init__(self, x):
        self.x = x
        self.passed = False
        gap_y = random.randint(PIPE_MIN_HEIGHT, PIPE_MAX_HEIGHT)
        self.top_pipe = pygame.Rect(self.x, 0, PIPE_WIDTH, gap_y)
        bottom_pipe_height = SCREEN_HEIGHT - GROUND_HEIGHT - gap_y - PIPE_GAP
        self.bottom_pipe = pygame.Rect(self.x, gap_y + PIPE_GAP, PIPE_WIDTH, bottom_pipe_height)

    def update(self):
        self.x -= PIPE_SPEED
        self.top_pipe.x = self.x
        self.bottom_pipe.x = self.x

    def draw(self, screen):
        pygame.draw.rect(screen, PIPE_COLOR, self.top_pipe)
        pygame.draw.rect(screen, PIPE_COLOR, self.bottom_pipe)

    def is_off_screen(self):
        return self.x + PIPE_WIDTH < 0

    def collide_with(self, bird_rect):
        return bird_rect.colliderect(self.top_pipe) or bird_rect.colliderect(self.bottom_pipe)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Flappy Bird Easy")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.reset_game()

    def reset_game(self):
        self.bird = Bird()
        self.pipes = []
        self.score = 0
        self.game_over = False
        self.frame_count = 0

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_r:
                    self.reset_game()
                if not self.game_over and (event.key == pygame.K_SPACE or event.key == pygame.K_UP):
                    self.bird.jump()

    def update(self):
        if not self.game_over:
            self.bird.update()
            if self.bird.check_boundary():
                self.game_over = True

            self.frame_count += 1
            if self.frame_count % PIPE_FREQUENCY == 0:
                self.pipes.append(PipePair(SCREEN_WIDTH))

            for pipe in self.pipes[:]:
                pipe.update()
                if pipe.is_off_screen():
                    self.pipes.remove(pipe)
                    continue
                if not pipe.passed and pipe.x + PIPE_WIDTH < self.bird.x:
                    pipe.passed = True
                    self.score += 1
                if pipe.collide_with(self.bird.rect):
                    self.game_over = True

    def draw(self):
        self.screen.fill(BACKGROUND_COLOR)

        for pipe in self.pipes:
            pipe.draw(self.screen)

        pygame.draw.rect(self.screen, GROUND_COLOR, (0, SCREEN_HEIGHT - GROUND_HEIGHT, SCREEN_WIDTH, GROUND_HEIGHT))

        self.bird.draw(self.screen)

        score_text = self.font.render(f"Score: {self.score}", True, TEXT_COLOR)
        self.screen.blit(score_text, (10, 10))

        if self.game_over:
            game_over_text = self.font.render("Game Over", True, GAME_OVER_COLOR)
            restart_text = self.font.render("Press R to Restart", True, TEXT_COLOR)
            final_score_text = self.font.render(f"Final Score: {self.score}", True, TEXT_COLOR)

            self.screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 60))
            self.screen.blit(final_score_text, (SCREEN_WIDTH // 2 - final_score_text.get_width() // 2, SCREEN_HEIGHT // 2 - 20))
            self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()