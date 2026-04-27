import pygame
import random
import sys

# --- 初始化随机种子 ---
random.seed(42)

# --- 常量定义 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# 颜色定义
BACKGROUND_COLOR = (0, 0, 0)
PADDLE_COLOR = (255, 255, 255)
BALL_COLOR = (255, 255, 255)
NET_COLOR = (64, 64, 64)
TEXT_COLOR = (255, 255, 255)
WIN_COLOR = (255, 200, 50)

# 球拍参数
PADDLE_WIDTH = 18
PADDLE_HEIGHT = 100
PADDLE_SPEED = 7
LEFT_PADDLE_X = 20
RIGHT_PADDLE_X = SCREEN_WIDTH - 20 - PADDLE_WIDTH

# 球参数
BALL_SIZE = 18
BALL_SPEED_X_INIT = 5
BALL_SPEED_Y_INIT = 5

# 分数和胜利条件
WIN_SCORE = 7

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pong Easy")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 48)  # 主字体
    small_font = pygame.font.SysFont(None, 36)  # 小字体

    # --- 游戏状态初始化函数 ---
    def init_game():
        nonlocal left_score, right_score, game_over, left_paddle_y, right_paddle_y, ball_x, ball_y, ball_speed_x, ball_speed_y
        left_score = 0
        right_score = 0
        game_over = False
        left_paddle_y = (SCREEN_HEIGHT - PADDLE_HEIGHT) // 2
        right_paddle_y = (SCREEN_HEIGHT - PADDLE_HEIGHT) // 2
        ball_x = SCREEN_WIDTH // 2 - BALL_SIZE // 2
        ball_y = SCREEN_HEIGHT // 2 - BALL_SIZE // 2
        # 随机初始方向，但受种子控制
        ball_speed_x = BALL_SPEED_X_INIT * random.choice([-1, 1])
        ball_speed_y = BALL_SPEED_Y_INIT * random.choice([-1, 1])

    # 初始化游戏状态
    left_score = 0
    right_score = 0
    game_over = False
    left_paddle_y = (SCREEN_HEIGHT - PADDLE_HEIGHT) // 2
    right_paddle_y = (SCREEN_HEIGHT - PADDLE_HEIGHT) // 2
    ball_x = SCREEN_WIDTH // 2 - BALL_SIZE // 2
    ball_y = SCREEN_HEIGHT // 2 - BALL_SIZE // 2
    ball_speed_x = BALL_SPEED_X_INIT * random.choice([-1, 1])
    ball_speed_y = BALL_SPEED_Y_INIT * random.choice([-1, 1])

    # --- 主游戏循环 ---
    running = True
    while running:
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    init_game()

        if not game_over:
            # 键盘输入处理（连续移动）
            keys = pygame.key.get_pressed()
            # 左侧球拍 W/S
            if keys[pygame.K_w]:
                left_paddle_y = max(0, left_paddle_y - PADDLE_SPEED)
            if keys[pygame.K_s]:
                left_paddle_y = min(SCREEN_HEIGHT - PADDLE_HEIGHT, left_paddle_y + PADDLE_SPEED)
            # 右侧球拍 上/下方向键
            if keys[pygame.K_UP]:
                right_paddle_y = max(0, right_paddle_y - PADDLE_SPEED)
            if keys[pygame.K_DOWN]:
                right_paddle_y = min(SCREEN_HEIGHT - PADDLE_HEIGHT, right_paddle_y + PADDLE_SPEED)

            # 小球移动
            ball_x += ball_speed_x
            ball_y += ball_speed_y

            # 上下边界反弹
            if ball_y <= 0:
                ball_y = 0
                ball_speed_y = -ball_speed_y
            elif ball_y >= SCREEN_HEIGHT - BALL_SIZE:
                ball_y = SCREEN_HEIGHT - BALL_SIZE
                ball_speed_y = -ball_speed_y

            # 球拍碰撞检测和反弹
            # 左侧球拍
            if ball_speed_x < 0 and ball_x <= LEFT_PADDLE_X + PADDLE_WIDTH:
                if left_paddle_y < ball_y + BALL_SIZE and left_paddle_y + PADDLE_HEIGHT > ball_y:
                    ball_x = LEFT_PADDLE_X + PADDLE_WIDTH
                    ball_speed_x = -ball_speed_x
            # 右侧球拍
            if ball_speed_x > 0 and ball_x + BALL_SIZE >= RIGHT_PADDLE_X:
                if right_paddle_y < ball_y + BALL_SIZE and right_paddle_y + PADDLE_HEIGHT > ball_y:
                    ball_x = RIGHT_PADDLE_X - BALL_SIZE
                    ball_speed_x = -ball_speed_x

            # 得分检测
            if ball_x < 0:
                right_score += 1
                # 重置球
                ball_x = SCREEN_WIDTH // 2 - BALL_SIZE // 2
                ball_y = SCREEN_HEIGHT // 2 - BALL_SIZE // 2
                ball_speed_x = BALL_SPEED_X_INIT * random.choice([-1, 1])
                ball_speed_y = BALL_SPEED_Y_INIT * random.choice([-1, 1])
            elif ball_x > SCREEN_WIDTH:
                left_score += 1
                # 重置球
                ball_x = SCREEN_WIDTH // 2 - BALL_SIZE // 2
                ball_y = SCREEN_HEIGHT // 2 - BALL_SIZE // 2
                ball_speed_x = BALL_SPEED_X_INIT * random.choice([-1, 1])
                ball_speed_y = BALL_SPEED_Y_INIT * random.choice([-1, 1])

            # 检查胜利条件
            if left_score >= WIN_SCORE or right_score >= WIN_SCORE:
                game_over = True

        # --- 渲染 ---
        screen.fill(BACKGROUND_COLOR)

        # 绘制中线（虚线）
        dash_length = 15
        gap_length = 10
        for y in range(0, SCREEN_HEIGHT, dash_length + gap_length):
            pygame.draw.rect(screen, NET_COLOR, (SCREEN_WIDTH // 2 - 1, y, 2, dash_length))

        # 绘制球拍
        pygame.draw.rect(screen, PADDLE_COLOR, (LEFT_PADDLE_X, left_paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT))
        pygame.draw.rect(screen, PADDLE_COLOR, (RIGHT_PADDLE_X, right_paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT))

        # 绘制球
        pygame.draw.rect(screen, BALL_COLOR, (ball_x, ball_y, BALL_SIZE, BALL_SIZE))

        # 绘制分数
        left_score_text = font.render(str(left_score), True, TEXT_COLOR)
        right_score_text = font.render(str(right_score), True, TEXT_COLOR)
        screen.blit(left_score_text, (SCREEN_WIDTH // 4 - left_score_text.get_width() // 2, 20))
        screen.blit(right_score_text, (SCREEN_WIDTH * 3 // 4 - right_score_text.get_width() // 2, 20))

        # 游戏结束时的胜利信息和重启提示
        if game_over:
            if left_score >= WIN_SCORE:
                win_text = font.render("Left Player Wins!", True, WIN_COLOR)
            else:
                win_text = font.render("Right Player Wins!", True, WIN_COLOR)
            screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2, SCREEN_HEIGHT // 2 - 30))

            restart_text = small_font.render("Press R to Restart", True, TEXT_COLOR)
            screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2 + 30))

        # 底部操作提示
        controls_text = small_font.render("W/S - Left Paddle   Up/Down - Right Paddle   ESC - Quit", True, TEXT_COLOR)
        screen.blit(controls_text, (SCREEN_WIDTH // 2 - controls_text.get_width() // 2, SCREEN_HEIGHT - 40))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()