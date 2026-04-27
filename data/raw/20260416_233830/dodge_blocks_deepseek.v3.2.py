import pygame
import random
import sys

# 固定参数
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
PLAYER_WIDTH = 60
PLAYER_HEIGHT = 60
PLAYER_INITIAL_Y = SCREEN_HEIGHT - PLAYER_HEIGHT - 40
PLAYER_SPEED = 7
OBSTACLE_WIDTH = 40
OBSTACLE_HEIGHT = 40
OBSTACLE_SPAWN_INTERVAL = 40
MIN_OBSTACLE_SPEED = 4
MAX_OBSTACLE_SPEED = 8

# 颜色定义
BACKGROUND_COLOR = (20, 20, 40)
PLAYER_COLOR = (70, 200, 100)
OBSTACLE_COLOR = (220, 80, 60)
TEXT_COLOR = (255, 255, 255)
HUD_BG_COLOR = (30, 30, 60, 180)

# 初始化pygame
pygame.init()
random.seed(42)

class Player:
    def __init__(self):
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = PLAYER_INITIAL_Y
        self.speed = PLAYER_SPEED
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        self.x = max(0, min(self.x, SCREEN_WIDTH - self.width))
        self.rect.x = self.x
        self.rect.y = self.y

    def draw(self, screen):
        pygame.draw.rect(screen, PLAYER_COLOR, self.rect, border_radius=8)

class Obstacle:
    def __init__(self):
        self.width = OBSTACLE_WIDTH
        self.height = OBSTACLE_HEIGHT
        self.x = random.randint(0, SCREEN_WIDTH - self.width)
        self.y = -self.height
        self.speed = random.randint(MIN_OBSTACLE_SPEED, MAX_OBSTACLE_SPEED)
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)

    def update(self):
        self.y += self.speed
        self.rect.y = self.y
        return self.y > SCREEN_HEIGHT

    def draw(self, screen):
        pygame.draw.rect(screen, OBSTACLE_COLOR, self.rect, border_radius=6)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Dodge Blocks Easy")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 28)
        self.reset()

    def reset(self):
        self.player = Player()
        self.obstacles = []
        self.frame_count = 0
        self.score = 0
        self.game_over = False

    def draw_hud(self):
        score_text = self.font.render(f"Score: {self.score}", True, TEXT_COLOR)
        score_rect = score_text.get_rect(topright=(SCREEN_WIDTH - 20, 20))
        hud_bg = pygame.Surface((score_rect.width + 30, score_rect.height + 20), pygame.SRCALPHA)
        hud_bg.fill(HUD_BG_COLOR)
        self.screen.blit(hud_bg, (score_rect.left - 15, score_rect.top - 10))
        self.screen.blit(score_text, score_rect)

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        game_over_text = self.font.render("GAME OVER", True, TEXT_COLOR)
        final_score_text = self.font.render(f"Final Score: {self.score}", True, TEXT_COLOR)
        restart_text = self.small_font.render("Press R to Restart", True, TEXT_COLOR)
        self.screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 70))
        self.screen.blit(final_score_text, (SCREEN_WIDTH//2 - final_score_text.get_width()//2, SCREEN_HEIGHT//2 - 20))
        self.screen.blit(restart_text, (SCREEN_WIDTH//2 - restart_text.get_width()//2, SCREEN_HEIGHT//2 + 30))

    def run(self):
        running = True
        while running:
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    if event.key == pygame.K_r:
                        self.reset()

            # 输入处理
            keys = pygame.key.get_pressed()

            # 游戏逻辑更新
            if not self.game_over:
                self.player.update(keys)
                self.frame_count += 1
                if self.frame_count % OBSTACLE_SPAWN_INTERVAL == 0:
                    self.obstacles.append(Obstacle())
                self.score = self.frame_count // FPS

                # 障碍物更新与碰撞检测
                for obstacle in self.obstacles[:]:
                    if obstacle.update():
                        self.obstacles.remove(obstacle)
                    elif self.player.rect.colliderect(obstacle.rect):
                        self.game_over = True

            # 绘制
            self.screen.fill(BACKGROUND_COLOR)
            self.player.draw(self.screen)
            for obstacle in self.obstacles:
                obstacle.draw(self.screen)
            self.draw_hud()
            if self.game_over:
                self.draw_game_over()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()