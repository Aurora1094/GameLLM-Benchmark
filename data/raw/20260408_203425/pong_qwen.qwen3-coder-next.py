import pygame
import sys

# 初始化 Pygame
pygame.init()

# 常量定义
WIDTH, HEIGHT = 800, 600
PADDLE_WIDTH, PADDLE_HEIGHT = 15, 100
BALL_SIZE = 15
WINNING_SCORE = 5
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# 创建窗口
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong Easy")

# 时钟
clock = pygame.time.Clock()
FPS = 60

# 游戏物体类
class Paddle:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, PADDLE_WIDTH, PADDLE_HEIGHT)
        self.speed = 7
    
    def move_up(self):
        self.rect.y = max(0, self.rect.y - self.speed)
    
    def move_down(self):
        self.rect.y = min(HEIGHT - self.rect.height, self.rect.y + self.speed)
    
    def draw(self):
        pygame.draw.rect(screen, WHITE, self.rect)

class Ball:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH // 2, HEIGHT // 2, BALL_SIZE, BALL_SIZE)
        self.dx = 5
        self.dy = 5
        self.reset()
    
    def reset(self):
        self.rect.x = WIDTH // 2
        self.rect.y = HEIGHT // 2
        # 随机选择发球方向
        self.dx = 5 if self.dx > 0 else -5
        self.dy = 5 if self.dy > 0 else -5
    
    def move(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        
        # 上下边界反弹
        if self.rect.top <= 0 or self.rect.bottom >= HEIGHT:
            self.dy *= -1
    
    def draw(self):
        pygame.draw.ellipse(screen, WHITE, self.rect)

# 初始化游戏对象
left_paddle = Paddle(20, HEIGHT // 2 - PADDLE_HEIGHT // 2)
right_paddle = Paddle(WIDTH - 20 - PADDLE_WIDTH, HEIGHT // 2 - PADDLE_HEIGHT // 2)
ball = Ball()
left_score = 0
right_score = 0
game_over = False
winner = None

# 游戏主循环
running = True
while running:
    # 处理事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r and game_over:
                # 重置游戏
                left_score = 0
                right_score = 0
                ball.reset()
                left_paddle.rect.y = HEIGHT // 2 - PADDLE_HEIGHT // 2
                right_paddle.rect.y = HEIGHT // 2 - PADDLE_HEIGHT // 2
                game_over = False
                winner = None
    
    # 键盘控制
    keys = pygame.key.get_pressed()
    
    # 左侧玩家控制 (W/S)
    if keys[pygame.K_w]:
        left_paddle.move_up()
    if keys[pygame.K_s]:
        left_paddle.move_down()
    
    # 右侧玩家控制 (上/下方向键)
    if keys[pygame.K_UP]:
        right_paddle.move_up()
    if keys[pygame.K_DOWN]:
        right_paddle.move_down()
    
    if not game_over:
        # 更新球的位置
        ball.move()
        
        # 球与 paddle 碰撞检测
        if ball.rect.colliderect(left_paddle.rect) and ball.dx < 0:
            ball.dx *= -1.05  # 稍微加速
            # 确保球不会卡在 paddle 内部
            ball.rect.left = left_paddle.rect.right + 1
            # 根据球击中 paddle 的位置调整垂直方向速度
            paddle_center = left_paddle.rect.y + PADDLE_HEIGHT // 2
            ball.dy = (ball.rect.y - paddle_center) * 0.1
        elif ball.rect.colliderect(right_paddle.rect) and ball.dx > 0:
            ball.dx *= -1.05
            ball.rect.right = right_paddle.rect.left - 1
            paddle_center = right_paddle.rect.y + PADDLE_HEIGHT // 2
            ball.dy = (ball.rect.y - paddle_center) * 0.1
        
        # 边界检测得分
        if ball.rect.left <= 0:
            right_score += 1
            ball.reset()
        elif ball.rect.right >= WIDTH:
            left_score += 1
            ball.reset()
        
        # 胜利判定
        if left_score >= WINNING_SCORE:
            game_over = True
            winner = "Left Player"
        elif right_score >= WINNING_SCORE:
            game_over = True
            winner = "Right Player"
    
    # 绘制
    screen.fill(BLACK)
    
    # 绘制中线
    for i in range(0, HEIGHT, 40):
        pygame.draw.rect(screen, WHITE, (WIDTH // 2 - 2, i, 4, 20))
    
    # 绘制球拍和球
    left_paddle.draw()
    right_paddle.draw()
    ball.draw()
    
    # 显示分数
    font = pygame.font.Font(None, 74)
    left_text = font.render(str(left_score), True, WHITE)
    right_text = font.render(str(right_score), True, WHITE)
    screen.blit(left_text, (WIDTH // 4, 20))
    screen.blit(right_text, (3 * WIDTH // 4, 20))
    
    # 游戏结束显示
    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        win_font = pygame.font.Font(None, 80)
        win_text = win_font.render(f"{winner} Wins!", True, GREEN)
        screen.blit(win_text, (WIDTH // 2 - win_text.get_width() // 2, HEIGHT // 2 - 60))
        
        restart_font = pygame.font.Font(None, 50)
        restart_text = restart_font.render("Press 'R' to restart", True, RED)
        screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 40))
    
    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()