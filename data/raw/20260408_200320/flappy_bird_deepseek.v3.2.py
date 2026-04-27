import pygame
import random
import sys

# 初始化Pygame
pygame.init()

# 游戏常量
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.25
JUMP_STRENGTH = -6
PIPE_SPEED = -4
PIPE_WIDTH = 80
PIPE_GAP = 180
PIPE_FREQUENCY = 1800  # 毫秒
FLOOR_HEIGHT = 50
BIRD_SIZE = 30

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 180, 0)
BLUE = (0, 120, 255)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)
BROWN = (139, 69, 19)

class Bird:
    def __init__(self):
        self.x = 100
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.alive = True
        self.rect = pygame.Rect(self.x - BIRD_SIZE//2, self.y - BIRD_SIZE//2, BIRD_SIZE, BIRD_SIZE)
    
    def jump(self):
        if self.alive:
            self.velocity = JUMP_STRENGTH
    
    def update(self):
        if self.alive:
            self.velocity += GRAVITY
            self.y += self.velocity
            self.rect.center = (self.x, self.y)
            
            # 边界检测
            if self.y <= BIRD_SIZE//2 or self.y >= SCREEN_HEIGHT - FLOOR_HEIGHT - BIRD_SIZE//2:
                self.alive = False
    
    def draw(self, screen):
        color = YELLOW if self.alive else RED
        pygame.draw.circle(screen, color, (self.x, self.y), BIRD_SIZE//2)
        pygame.draw.circle(screen, BLACK, (self.x + 10, self.y - 5), 5)  # 眼睛
        # 鸟嘴
        beak_points = [(self.x + 15, self.y), (self.x + 35, self.y - 5), (self.x + 35, self.y + 5)]
        pygame.draw.polygon(screen, RED, beak_points)

class Pipe:
    def __init__(self):
        self.x = SCREEN_WIDTH
        self.height = random.randint(100, SCREEN_HEIGHT - FLOOR_HEIGHT - PIPE_GAP - 100)
        self.passed = False
        self.top_rect = pygame.Rect(self.x, 0, PIPE_WIDTH, self.height)
        self.bottom_rect = pygame.Rect(self.x, self.height + PIPE_GAP, PIPE_WIDTH, SCREEN_HEIGHT)
    
    def update(self):
        self.x += PIPE_SPEED
        self.top_rect.x = self.x
        self.bottom_rect.x = self.x
    
    def draw(self, screen):
        # 管道主体
        pygame.draw.rect(screen, GREEN, self.top_rect)
        pygame.draw.rect(screen, GREEN, self.bottom_rect)
        # 管道顶部装饰
        pygame.draw.rect(screen, (0, 150, 0), 
                        (self.x - 5, self.height - 20, PIPE_WIDTH + 10, 20))
        pygame.draw.rect(screen, (0, 150, 0), 
                        (self.x - 5, self.height + PIPE_GAP, PIPE_WIDTH + 10, 20))
    
    def off_screen(self):
        return self.x < -PIPE_WIDTH

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Flappy Bird Easy")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont(None, 48)
        self.small_font = pygame.font.SysFont(None, 36)
        self.reset_game()
        
        # 设置管道生成计时器
        self.last_pipe = pygame.time.get_ticks()
    
    def reset_game(self):
        self.bird = Bird()
        self.pipes = []
        self.score = 0
        self.game_over = False
        self.last_pipe = pygame.time.get_ticks()
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    if self.game_over:
                        self.reset_game()
                    else:
                        self.bird.jump()
    
    def generate_pipes(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_pipe > PIPE_FREQUENCY and not self.game_over:
            self.pipes.append(Pipe())
            self.last_pipe = current_time
    
    def update(self):
        if not self.game_over:
            self.bird.update()
            
            # 更新管道
            for pipe in self.pipes[:]:
                pipe.update()
                
                # 碰撞检测
                if (pipe.top_rect.colliderect(self.bird.rect) or 
                    pipe.bottom_rect.colliderect(self.bird.rect)):
                    self.bird.alive = False
                
                # 计分
                if not pipe.passed and pipe.x < self.bird.x:
                    pipe.passed = True
                    self.score += 1
                
                # 移除屏幕外的管道
                if pipe.off_screen():
                    self.pipes.remove(pipe)
            
            # 检查游戏结束
            if not self.bird.alive:
                self.game_over = True
    
    def draw(self):
        # 背景
        self.screen.fill(BLUE)
        
        # 绘制云朵
        for i in range(3):
            x = (pygame.time.get_ticks() // 50 + i*300) % (SCREEN_WIDTH + 200) - 100
            y = 80 + i*70
            pygame.draw.circle(self.screen, WHITE, (x, y), 30)
            pygame.draw.circle(self.screen, WHITE, (x+25, y-15), 25)
            pygame.draw.circle(self.screen, WHITE, (x+25, y+15), 25)
            pygame.draw.circle(self.screen, WHITE, (x+50, y), 20)
        
        # 绘制管道
        for pipe in self.pipes:
            pipe.draw(self.screen)
        
        # 绘制地板
        pygame.draw.rect(self.screen, BROWN, (0, SCREEN_HEIGHT - FLOOR_HEIGHT, SCREEN_WIDTH, FLOOR_HEIGHT))
        pygame.draw.rect(self.screen, (120, 60, 10), 
                        (0, SCREEN_HEIGHT - FLOOR_HEIGHT + 10, SCREEN_WIDTH, 10))
        
        # 绘制小鸟
        self.bird.draw(self.screen)
        
        # 绘制分数
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # 游戏结束画面
        if self.game_over:
            # 半透明覆盖层
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            self.screen.blit(overlay, (0, 0))
            
            # 游戏结束文字
            game_over_text = self.font.render("GAME OVER", True, RED)
            score_text = self.font.render(f"Final Score: {self.score}", True, YELLOW)
            restart_text = self.small_font.render("Press SPACE or UP to restart", True, WHITE)
            
            self.screen.blit(game_over_text, 
                           (SCREEN_WIDTH//2 - game_over_text.get_width()//2, 150))
            self.screen.blit(score_text, 
                           (SCREEN_WIDTH//2 - score_text.get_width()//2, 220))
            self.screen.blit(restart_text, 
                           (SCREEN_WIDTH//2 - restart_text.get_width()//2, 300))
        
        # 绘制操作提示
        if not self.game_over:
            hint_text = self.small_font.render("Press SPACE or UP to jump", True, WHITE)
            self.screen.blit(hint_text, (SCREEN_WIDTH//2 - hint_text.get_width()//2, 50))
    
    def run(self):
        while True:
            self.handle_events()
            self.generate_pipes()
            self.update()
            self.draw()
            
            pygame.display.flip()
            self.clock.tick(FPS)

if __name__ == "__main__":
    game = Game()
    game.run()