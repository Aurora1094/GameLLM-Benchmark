import pygame
import random
import sys

# 初始化
pygame.init()
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Dodge Blocks Easy")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

# 颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
BLUE = (50, 150, 255)
GREEN = (50, 255, 100)
YELLOW = (255, 255, 50)

class Player:
    def __init__(self):
        self.width = 60
        self.height = 60
        self.x = SCREEN_WIDTH // 2 - self.width // 2
        self.y = SCREEN_HEIGHT - self.height - 20
        self.speed = 8
        self.color = BLUE

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height), 0, 10)
        # 绘制玩家内部装饰
        pygame.draw.rect(screen, WHITE, (self.x + 10, self.y + 10, self.width - 20, self.height - 20), 3, 5)

    def move(self, direction):
        if direction == "left" and self.x > 0:
            self.x -= self.speed
        if direction == "right" and self.x < SCREEN_WIDTH - self.width:
            self.x += self.speed

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Block:
    def __init__(self):
        self.width = random.randint(30, 80)
        self.height = random.randint(30, 80)
        self.x = random.randint(0, SCREEN_WIDTH - self.width)
        self.y = -self.height
        self.speed = random.uniform(3, 7)
        self.color = RED

    def update(self):
        self.y += self.speed

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height), 0, 5)
        # 绘制方块内部装饰
        pygame.draw.rect(screen, YELLOW, (self.x + 5, self.y + 5, self.width - 10, self.height - 10), 2, 3)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def is_off_screen(self):
        return self.y > SCREEN_HEIGHT

def game_loop():
    player = Player()
    blocks = []
    score = 0
    game_over = False
    block_timer = 0
    block_interval = 30  # 每30帧生成一个方块

    running = True
    while running:
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game_over:
                    return True  # 重启游戏
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        if not game_over:
            # 玩家移动
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                player.move("left")
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                player.move("right")

            # 生成方块
            block_timer += 1
            if block_timer >= block_interval:
                blocks.append(Block())
                block_timer = 0
                # 随着分数增加，生成间隔略微减少
                block_interval = max(15, 30 - score // 100)

            # 更新方块
            for block in blocks[:]:
                block.update()
                if block.is_off_screen():
                    blocks.remove(block)
                    score += 1

            # 碰撞检测
            player_rect = player.get_rect()
            for block in blocks:
                if player_rect.colliderect(block.get_rect()):
                    game_over = True
                    break

        # 绘制
        screen.fill(BLACK)
        # 绘制背景网格
        for x in range(0, SCREEN_WIDTH, 50):
            pygame.draw.line(screen, (30, 30, 30), (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 50):
            pygame.draw.line(screen, (30, 30, 30), (0, y), (SCREEN_WIDTH, y), 1)

        player.draw()
        for block in blocks:
            block.draw()

        # 显示分数
        score_text = font.render(f"Score: {score}", True, GREEN)
        screen.blit(score_text, (10, 10))

        if game_over:
            # 游戏结束遮罩
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            # 游戏结束文本
            game_over_text = font.render("GAME OVER", True, YELLOW)
            screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 60))

            final_score_text = font.render(f"Final Score: {score}", True, GREEN)
            screen.blit(final_score_text, (SCREEN_WIDTH // 2 - final_score_text.get_width() // 2, SCREEN_HEIGHT // 2))

            restart_text = font.render("Press R to Restart or ESC to Quit", True, WHITE)
            screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 60))

        # 绘制操作说明
        controls_text = font.render("Use LEFT/RIGHT or A/D to move", True, WHITE)
        screen.blit(controls_text, (SCREEN_WIDTH // 2 - controls_text.get_width() // 2, SCREEN_HEIGHT - 40))

        pygame.display.flip()
        clock.tick(60)

    return False

def main():
    restart = True
    while restart:
        restart = game_loop()

if __name__ == "__main__":
    main()