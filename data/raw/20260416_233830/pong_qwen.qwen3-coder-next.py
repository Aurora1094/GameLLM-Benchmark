import pygame
import random

# 固定参数
WIDTH, HEIGHT = 800, 600
FPS = 60
PADDLE_WIDTH, PADDLE_HEIGHT = 18, 100
BALL_SIZE = 18
PADDLE_SPEED = 7
BALL_SPEED_X_INIT = 5
BALL_SPEED_Y_INIT = 5
WINNING_SCORE = 7

# 颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)

# 初始化
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong Easy")
clock = pygame.time.Clock()
random.seed(42)

# 游戏状态
def reset_game():
    return {
        'left_score': 0,
        'right_score': 0,
        'game_over': False,
        'winner': None
    }

def reset_ball():
    return {
        'x': WIDTH // 2 - BALL_SIZE // 2,
        'y': HEIGHT // 2 - BALL_SIZE // 2,
        'dx': BALL_SPEED_X_INIT * random.choice([-1, 1]),
        'dy': BALL_SPEED_Y_INIT * random.choice([-1, 1])
    }

# 主程序
def main():
    state = reset_game()
    ball = reset_ball()
    left_paddle_y = HEIGHT // 2 - PADDLE_HEIGHT // 2
    right_paddle_y = HEIGHT // 2 - PADDLE_HEIGHT // 2

    # 字体设置
    pygame.font.init()
    font_score = pygame.font.Font(None, 72)
    font_status = pygame.font.Font(None, 48)
    font_large = pygame.font.Font(None, 60)

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
                    if state['game_over']:
                        state = reset_game()
                        ball = reset_ball()

        if not state['game_over']:
            # 按键处理
            keys = pygame.key.get_pressed()
            
            # 左侧球拍控制
            if keys[pygame.K_w]:
                left_paddle_y = max(0, left_paddle_y - PADDLE_SPEED)
            if keys[pygame.K_s]:
                left_paddle_y = min(HEIGHT - PADDLE_HEIGHT, left_paddle_y + PADDLE_SPEED)
            
            # 右侧球拍控制
            if keys[pygame.K_UP]:
                right_paddle_y = max(0, right_paddle_y - PADDLE_SPEED)
            if keys[pygame.K_DOWN]:
                right_paddle_y = min(HEIGHT - PADDLE_HEIGHT, right_paddle_y + PADDLE_SPEED)

            # 球移动
            ball['x'] += ball['dx']
            ball['y'] += ball['dy']

            # 上下边界碰撞
            if ball['y'] <= 0 or ball['y'] + BALL_SIZE >= HEIGHT:
                ball['dy'] = -ball['dy']

            # 球拍碰撞检测
            left_paddle_rect = pygame.Rect(20, left_paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT)
            right_paddle_rect = pygame.Rect(WIDTH - 20 - PADDLE_WIDTH, right_paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT)
            ball_rect = pygame.Rect(ball['x'], ball['y'], BALL_SIZE, BALL_SIZE)

            # 左侧球拍反弹
            if ball_rect.colliderect(left_paddle_rect) and ball['dx'] < 0:
                ball['dx'] = -ball['dx']
                ball['x'] = left_paddle_rect.right
            # 右侧球拍反弹
            if ball_rect.colliderect(right_paddle_rect) and ball['dx'] > 0:
                ball['dx'] = -ball['dx']
                ball['x'] = right_paddle_rect.left - BALL_SIZE

            # 得分检测
            if ball['x'] < 0:
                state['right_score'] += 1
                if state['right_score'] >= WINNING_SCORE:
                    state['game_over'] = True
                    state['winner'] = 'Right'
                else:
                    ball = reset_ball()
            elif ball['x'] + BALL_SIZE > WIDTH:
                state['left_score'] += 1
                if state['left_score'] >= WINNING_SCORE:
                    state['game_over'] = True
                    state['winner'] = 'Left'
                else:
                    ball = reset_ball()

        # 绘制
        screen.fill(BLACK)
        
        # 中线
        pygame.draw.line(screen, GRAY, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 2)
        
        # 游戏元素
        pygame.draw.rect(screen, WHITE, pygame.Rect(20, left_paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT))
        pygame.draw.rect(screen, WHITE, pygame.Rect(WIDTH - 20 - PADDLE_WIDTH, right_paddle_y, PADDLE_WIDTH, PADDLE_HEIGHT))
        pygame.draw.rect(screen, WHITE, ball_rect)
        
        # 分数显示
        left_text = font_score.render(str(state['left_score']), True, WHITE)
        right_text = font_score.render(str(state['right_score']), True, WHITE)
        screen.blit(left_text, (WIDTH // 4 - left_text.get_width() // 2, 20))
        screen.blit(right_text, (3 * WIDTH // 4 - right_text.get_width() // 2, 20))

        # 胜利提示
        if state['game_over']:
            winner_text = font_large.render(f"{state['winner']} Wins!" if state['winner'] == 'Left' else f"{state['winner']} Wins!", True, WHITE)
            restart_text = font_status.render("Press R to Restart", True, WHITE)
            screen.blit(winner_text, (WIDTH // 2 - winner_text.get_width() // 2, HEIGHT // 2 - 30))
            screen.blit(restart_text, (WIDTH // 2 - restart_text.get_width() // 2, HEIGHT // 2 + 30))

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()