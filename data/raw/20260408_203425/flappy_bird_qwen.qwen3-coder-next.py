import pygame
import sys
import random

# 初始化 pygame
pygame.init()

# 游戏常量
WIDTH, HEIGHT = 400, 600
FPS = 60
GRAVITY = 0.25
JUMP_STRENGTH = -5
PIPE_WIDTH = 60
PIPE_GAP = 150
PIPE_SPEED = 3
PIPE_SPAWN_RATE = 90  # 约每1.5秒生成一道管道（60 FPS）

# 颜色定义
SKY_COLOR = (135, 206, 235)
BIRD_COLOR = (255, 255, 0)
PIPE_COLOR = (34, 139, 34)
GROUND_COLOR = (139, 69, 19)
TEXT_COLOR = (255, 255, 255)

# 设置游戏窗口
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird Easy")
clock = pygame.time.Clock()

# 字体设置
font_large = pygame.font.SysFont("Arial", 64, bold=True)
font_small = pygame.font.SysFont("Arial", 32, bold=True)


class Bird:
    def __init__(self):
        self.x = 80
        self.y = HEIGHT // 2
        self.velocity = 0
        self.radius = 15

    def jump(self):
        self.velocity = JUMP_STRENGTH

    def update(self):
        self.velocity += GRAVITY
        self.y += self.velocity

        # 碰到上边界
        if self.y - self.radius < 0:
            self.y = self.radius
            self.velocity = 0

        # 碰到地面
        if self.y + self.radius > HEIGHT:
            self.y = HEIGHT - self.radius
            return True
        return False

    def draw(self):
        pygame.draw.circle(screen, BIRD_COLOR, (int(self.x), int(self.y)), self.radius)


class Pipe:
    def __init__(self, x):
        self.x = x
        self.width = PIPE_WIDTH
        self.gap = PIPE_GAP
        self.top_height = random.randint(50, HEIGHT - self.gap - 50)
        self.bottom_y = self.top_height + self.gap
        self.passed = False

    def update(self, speed):
        self.x -= speed

    def draw(self):
        # 上管道
        pygame.draw.rect(screen, PIPE_COLOR, (self.x, 0, self.width, self.top_height))
        # 管道边缘装饰
        pygame.draw.rect(screen, (20, 100, 20), (self.x, 0, self.width, self.top_height), 3)
        
        # 下管道
        pygame.draw.rect(screen, PIPE_COLOR, (self.x, self.bottom_y, self.width, HEIGHT - self.bottom_y))
        # 管道边缘装饰
        pygame.draw.rect(screen, (20, 100, 20), (self.x, self.bottom_y, self.width, HEIGHT - self.bottom_y), 3)

    def check_collision(self, bird):
        # 检查是否在管道水平范围内
        if bird.x + bird.radius > self.x and bird.x - bird.radius < self.x + self.width:
            # 检查是否碰到上下管道
            if bird.y - bird.radius < self.top_height or bird.y + bird.radius > self.bottom_y:
                return True
        return False


def draw_text(text, font, color, x, y, center=True):
    surface = font.render(text, True, color)
    rect = surface.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(surface, rect)


def main():
    bird = Bird()
    pipes = []
    score = 0
    high_score = 0
    pipe_timer = 0
    game_over = False
    game_active = True

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP):
                    if not game_active and not game_over:
                        # 刚开始游戏
                        game_active = True
                        bird = Bird()
                        pipes = []
                        score = 0
                        pipe_timer = 0
                    elif game_active and not game_over:
                        bird.jump()
                    elif game_over:
                        # 重置游戏
                        game_over = False
                        game_active = True
                        bird = Bird()
                        pipes = []
                        score = 0
                        pipe_timer = 0

        screen.fill(SKY_COLOR)

        if game_active and not game_over:
            bird.update()
            pipe_timer += 1

            # 生成新管道
            if pipe_timer % PIPE_SPAWN_RATE == 0:
                pipes.append(Pipe(WIDTH))

            # 更新和绘制管道
            for pipe in pipes:
                pipe.update(PIPE_SPEED)
                pipe.draw()
                
                # 检查通过管道
                if not pipe.passed and bird.x > pipe.x + pipe.width:
                    score += 1
                    pipe.passed = True
                    if score > high_score:
                        high_score = score
                
                # 碰撞检测
                if pipe.check_collision(bird):
                    game_over = True

            # 移除屏幕外的管道
            pipes = [pipe for pipe in pipes if pipe.x + pipe.width > 0]

            # 检查是否碰到地面
            if bird.y + bird.radius >= HEIGHT:
                game_over = True

        # 绘制小鸟
        if game_active:
            bird.draw()

        # 绘制地面
        pygame.draw.rect(screen, GROUND_COLOR, (0, HEIGHT - 10, WIDTH, 10))

        # 显示分数
        draw_text(f"Score: {score}", font_small, TEXT_COLOR, 10, 20, center=False)
        draw_text(f"High: {high_score}", font_small, TEXT_COLOR, WIDTH - 10, 20, center=False)

        # 游戏状态显示
        if not game_active and not game_over:
            draw_text("Flappy Bird Easy", font_large, TEXT_COLOR, WIDTH // 2, HEIGHT // 2 - 40)
            draw_text("Press SPACE/UP to Start", font_small, TEXT_COLOR, WIDTH // 2, HEIGHT // 2 + 30)
        elif game_over:
            draw_text("GAME OVER", font_large, TEXT_COLOR, WIDTH // 2, HEIGHT // 2 - 50)
            draw_text(f"Score: {score}", font_small, TEXT_COLOR, WIDTH // 2, HEIGHT // 2 + 10)
            draw_text("Press SPACE/UP to Restart", font_small, TEXT_COLOR, WIDTH // 2, HEIGHT // 2 + 60)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()