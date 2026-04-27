import pygame
import random
import sys

# 初始化Pygame
pygame.init()

# 游戏常量
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.5
JUMP_STRENGTH = -8
PIPE_SPEED = 3
PIPE_WIDTH = 60
PIPE_GAP = 170
PIPE_SPAWN_RATE = 150  # 帧数间隔

# 颜色定义
SKY_BLUE = (135, 206, 235)
BIRD_YELLOW = (255, 215, 0)
PIPE_GREEN = (34, 139, 34)
TEXT_COLOR = (255, 255, 255)

# 创建屏幕
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Flappy Bird Easy")
clock = pygame.time.Clock()

# 游戏状态
game_state = "start"  # "start", "playing", "game_over"

# 小鸟类
class Bird:
    def __init__(self):
        self.x = SCREEN_WIDTH // 3
        self.y = SCREEN_HEIGHT // 2
        self.velocity = 0
        self.radius = 20
    
    def jump(self):
        self.velocity = JUMP_STRENGTH
    
    def update(self):
        self.velocity += GRAVITY
        self.y += self.velocity
        
        # 边界检测
        if self.y + self.radius >= SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.radius
            return True
        if self.y - self.radius <= 0:
            self.y = self.radius
            self.velocity = 0
            return False
        return False
    
    def draw(self):
        pygame.draw.circle(screen, BIRD_YELLOW, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, (255, 160, 0), (int(self.x), int(self.y)), self.radius, 2)

# 管道类
class Pipe:
    def __init__(self, x):
        self.x = x
        self.top_height = random.randint(100, SCREEN_HEIGHT - PIPE_GAP - 100)
        self.bottom_height = SCREEN_HEIGHT - self.top_height - PIPE_GAP
        self.passed = False
    
    def update(self):
        self.x -= PIPE_SPEED
    
    def draw(self):
        # 上管道
        pygame.draw.rect(screen, PIPE_GREEN, (self.x, 0, PIPE_WIDTH, self.top_height))
        pygame.draw.rect(screen, (19, 93, 20), (self.x, 0, PIPE_WIDTH, self.top_height), 2)
        # 下管道
        pygame.draw.rect(screen, PIPE_GREEN, (self.x, SCREEN_HEIGHT - self.bottom_height, PIPE_WIDTH, self.bottom_height))
        pygame.draw.rect(screen, (19, 93, 20), (self.x, SCREEN_HEIGHT - self.bottom_height, PIPE_WIDTH, self.bottom_height), 2)
    
    def check_collision(self, bird):
        # 小鸟矩形近似
        bird_rect = pygame.Rect(bird.x - bird.radius, bird.y - bird.radius, 2 * bird.radius, 2 * bird.radius)
        
        # 上管道矩形
        top_pipe_rect = pygame.Rect(self.x, 0, PIPE_WIDTH, self.top_height)
        # 下管道矩形
        bottom_pipe_rect = pygame.Rect(self.x, SCREEN_HEIGHT - self.bottom_height, PIPE_WIDTH, self.bottom_height)
        
        return bird_rect.colliderect(top_pipe_rect) or bird_rect.colliderect(bottom_pipe_rect)

# 分数显示
def draw_score(score):
    font = pygame.font.Font(None, 36)
    text = font.render(f"Score: {score}", True, TEXT_COLOR)
    screen.blit(text, (10, 10))

# 消息显示
def draw_message(message, y_offset=0):
    font = pygame.font.Font(None, 48)
    text = font.render(message, True, TEXT_COLOR)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + y_offset))
    screen.blit(text, text_rect)
    
    sub_font = pygame.font.Font(None, 24)
    sub_text = sub_font.render("Press SPACE or UP to restart", True, TEXT_COLOR)
    sub_rect = sub_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + y_offset + 50))
    screen.blit(sub_text, sub_rect)

# 主游戏函数
def main():
    global game_state
    bird = Bird()
    pipes = []
    score = 0
    frame_count = 0
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    if game_state == "start":
                        game_state = "playing"
                        bird.velocity = JUMP_STRENGTH
                    elif game_state == "playing":
                        bird.jump()
                    elif game_state == "game_over":
                        # 重置游戏
                        bird = Bird()
                        pipes = []
                        score = 0
                        frame_count = 0
                        game_state = "start"
        
        screen.fill(SKY_BLUE)
        
        if game_state == "start":
            bird.draw()
            draw_message("Flappy Bird", -50)
        elif game_state == "playing":
            # 更新小鸟
            bird.update()
            
            # 生成管道
            frame_count += 1
            if frame_count % PIPE_SPAWN_RATE == 0:
                pipes.append(Pipe(SCREEN_WIDTH))
            
            # 更新和绘制管道
            for pipe in pipes[:]:
                pipe.update()
                pipe.draw()
                
                # 移除超出屏幕的管道
                if pipe.x + PIPE_WIDTH < 0:
                    pipes.remove(pipe)
                
                # 碰撞检测
                if pipe.check_collision(bird):
                    game_state = "game_over"
                
                # 计分
                if not pipe.passed and pipe.x + PIPE_WIDTH < bird.x:
                    pipe.passed = True
                    score += 1
            
            # 检测地板碰撞
            if bird.y + bird.radius >= SCREEN_HEIGHT:
                game_state = "game_over"
            
            bird.draw()
            draw_score(score)
            
        elif game_state == "game_over":
            for pipe in pipes:
                pipe.draw()
            bird.draw()
            draw_score(score)
            draw_message("Game Over", -100)
        
        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()