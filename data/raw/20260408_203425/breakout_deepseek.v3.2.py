import pygame
import sys
import random

# 初始化pygame
pygame.init()

# 游戏常量
WIDTH, HEIGHT = 800, 600
PADDLE_WIDTH, PADDLE_HEIGHT = 120, 15
BALL_SIZE = 20
BRICK_WIDTH, BRICK_HEIGHT = 80, 30
BRICK_ROWS = 5
BRICK_COLS = 9
BRICK_GAP = 5
FPS = 60

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 50, 50)
GREEN = (50, 255, 50)
BLUE = (50, 100, 255)
YELLOW = (255, 255, 50)
ORANGE = (255, 150, 50)
PURPLE = (180, 50, 255)
BRICK_COLORS = [RED, ORANGE, YELLOW, GREEN, BLUE]

# 创建游戏窗口
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Breakout Medium")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

class Paddle:
    def __init__(self):
        self.width = PADDLE_WIDTH
        self.height = PADDLE_HEIGHT
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT - 50
        self.speed = 8
        self.color = WHITE
    
    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height), 0, 10)
    
    def move(self, keys):
        if keys[pygame.K_LEFT] and self.x > 0:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] and self.x < WIDTH - self.width:
            self.x += self.speed
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

class Ball:
    def __init__(self):
        self.size = BALL_SIZE
        self.reset()
        self.color = WHITE
    
    def reset(self):
        self.x = WIDTH // 2
        self.y = HEIGHT // 2
        self.speed_x = random.choice([-5, -4, 4, 5])
        self.speed_y = -5
    
    def draw(self):
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.size // 2)
    
    def move(self):
        self.x += self.speed_x
        self.y += self.speed_y
        
        # 碰撞左右墙壁
        if self.x <= self.size // 2 or self.x >= WIDTH - self.size // 2:
            self.speed_x = -self.speed_x
            self.x = max(self.size // 2, min(WIDTH - self.size // 2, self.x))
        
        # 碰撞顶部
        if self.y <= self.size // 2:
            self.speed_y = -self.speed_y
            self.y = self.size // 2
    
    def get_rect(self):
        return pygame.Rect(self.x - self.size // 2, self.y - self.size // 2, self.size, self.size)
    
    def check_paddle_collision(self, paddle):
        ball_rect = self.get_rect()
        paddle_rect = paddle.get_rect()
        
        if ball_rect.colliderect(paddle_rect) and self.speed_y > 0:
            # 根据击中球拍的位置调整反弹角度
            relative_x = (self.x - paddle.x) / paddle.width
            self.speed_x = (relative_x - 0.5) * 10
            self.speed_y = -abs(self.speed_y)
            self.y = paddle.y - self.size // 2
            return True
        return False

class Brick:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.width = BRICK_WIDTH
        self.height = BRICK_HEIGHT
        self.color = color
        self.visible = True
    
    def draw(self):
        if self.visible:
            pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height), 0, 5)
            pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height), 2, 5)
    
    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def check_collision(self, ball):
        if not self.visible:
            return False
        
        brick_rect = self.get_rect()
        ball_rect = ball.get_rect()
        
        if ball_rect.colliderect(brick_rect):
            self.visible = False
            
            # 确定碰撞方向并反弹
            overlap_left = ball_rect.right - brick_rect.left
            overlap_right = brick_rect.right - ball_rect.left
            overlap_top = ball_rect.bottom - brick_rect.top
            overlap_bottom = brick_rect.bottom - ball_rect.top
            
            min_overlap = min(overlap_left, overlap_right, overlap_top, overlap_bottom)
            
            if min_overlap == overlap_left or min_overlap == overlap_right:
                ball.speed_x = -ball.speed_x
            else:
                ball.speed_y = -ball.speed_y
            
            return True
        return False

class Game:
    def __init__(self):
        self.paddle = Paddle()
        self.ball = Ball()
        self.bricks = []
        self.score = 0
        self.lives = 3
        self.game_state = "PLAYING"  # PLAYING, WIN, LOSE
        self.create_bricks()
    
    def create_bricks(self):
        self.bricks = []
        total_brick_width = BRICK_COLS * BRICK_WIDTH + (BRICK_COLS - 1) * BRICK_GAP
        start_x = (WIDTH - total_brick_width) // 2
        
        for row in range(BRICK_ROWS):
            for col in range(BRICK_COLS):
                x = start_x + col * (BRICK_WIDTH + BRICK_GAP)
                y = 80 + row * (BRICK_HEIGHT + BRICK_GAP)
                color = BRICK_COLORS[row % len(BRICK_COLORS)]
                self.bricks.append(Brick(x, y, color))
    
    def update(self):
        if self.game_state != "PLAYING":
            return
        
        keys = pygame.key.get_pressed()
        self.paddle.move(keys)
        self.ball.move()
        
        # 球拍碰撞检测
        self.ball.check_paddle_collision(self.paddle)
        
        # 砖块碰撞检测
        for brick in self.bricks:
            if brick.check_collision(self.ball):
                self.score += 10
                break
        
        # 检查球是否落出底部
        if self.ball.y > HEIGHT:
            self.lives -= 1
            if self.lives <= 0:
                self.game_state = "LOSE"
            else:
                self.ball.reset()
        
        # 检查是否胜利
        if all(not brick.visible for brick in self.bricks):
            self.game_state = "WIN"
    
    def draw(self):
        # 绘制背景
        screen.fill(BLACK)
        
        # 绘制砖块
        for brick in self.bricks:
            brick.draw()
        
        # 绘制球拍和球
        self.paddle.draw()
        self.ball.draw()
        
        # 绘制分数和生命值
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        lives_text = font.render(f"Lives: {self.lives}", True, WHITE)
        screen.blit(score_text, (10, 10))
        screen.blit(lives_text, (WIDTH - 120, 10))
        
        # 绘制游戏状态信息
        if self.game_state == "WIN":
            win_text = font.render("YOU WIN! Press R to restart", True, GREEN)
            screen.blit(win_text, (WIDTH // 2 - win_text.get_width() // 2, HEIGHT // 2))
        elif self.game_state == "LOSE":
            lose_text = font.render("GAME OVER! Press R to restart", True, RED)
            screen.blit(lose_text, (WIDTH // 2 - lose_text.get_width() // 2, HEIGHT // 2))
    
    def restart(self):
        self.paddle = Paddle()
        self.ball = Ball()
        self.score = 0
        self.lives = 3
        self.game_state = "PLAYING"
        self.create_bricks()

def main():
    game = Game()
    running = True
    
    while running:
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.restart()
                elif event.key == pygame.K_ESCAPE:
                    running = False
        
        # 更新游戏状态
        game.update()
        
        # 绘制游戏
        game.draw()
        
        # 更新屏幕
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()