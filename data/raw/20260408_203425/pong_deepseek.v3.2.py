import pygame
import sys

# 初始化 Pygame
pygame.init()

# 定义颜色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 50, 50)
BLUE = (50, 150, 255)

# 初始化窗口
WIDTH, HEIGHT = 800, 600
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pong Easy")
pygame.font.init()
FONT = pygame.font.SysFont('Roboto', 30, bold=True)
WIN_SCORE = 5  # 获胜分数

class Paddle:
    def __init__(self, x, y, up_key, down_key):
        self.width, self.height = 20, 120
        self.rect = pygame.Rect(x, y, self.width, self.height)
        self.color = WHITE
        self.speed = 8
        self.score = 0
        self.up_key = up_key
        self.down_key = down_key

    def move_up(self):
        if self.rect.top > 0:
            self.rect.move_ip(0, -self.speed)

    def move_down(self):
        if self.rect.bottom < HEIGHT:
            self.rect.move_ip(0, self.speed)

    def draw(self, window):
        pygame.draw.rect(window, self.color, self.rect, 0, 8)

    def computer_ai(self, ball):
        # 简单AI：直接让球拍中心跟随球的垂直位置
        if self.rect.centery < ball.rect.centery - 35:
            self.rect.y += 5
        elif self.rect.centery > ball.rect.centery:
            self.rect.y -= 5

        if self.rect.y < 0:
            self.rect.y = 0
        elif self.rect.bottom > HEIGHT:
            self.rect.bottom = HEIGHT

class Ball:
    def __init__(self):
        self.radius = 15
        self.reset_ball()
        self.speed_x = 6
        self.speed_y = 6

    def reset_ball(self):
        self.rect = pygame.Rect(WIDTH // 2 - 10, HEIGHT // 2 - 10, self.radius * 2, self.radius * 2)
        self.velocity_x = self.velocity_y = 0.5

    def move(self, players):
        # 与左右挡板碰撞头部预测：为更平滑，直接反射，不重复矫正
        for player in players:
            if self.rect.colliderect(player.rect):
                self.velocity_x *= -1.05  # 增加速度并反转
                offset = self.rect.centery - player.rect.centery
                total_range = (player.height // 2) + self.radius
                self.velocity_y = 8 * offset / total_range

    def update(self):
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y
        
        if self.rect.top <= 0 or self.rect.bottom >= HEIGHT:
            self.velocity_y *= -1

    def draw(self, window):
        pygame.draw.circle(window, WHITE, self.rect.center, self.radius)
    
    def out_of_left_bounds(self):
        return self.rect.centerx < 0

    def out_of_right_bounds(self):
        return self.rect.centerx > WIDTH

class PongGame:
    def __init__(self):
        self.window = WIN
        self.clock = pygame.time.Clock()
        self.players = []
        self.ball = Ball()  # 临时创建ball，游戏开始时初始化
        self.WIN_SCORE = 5
        self.game_active = True
        self.show_winner = False
        self.reset_game_state()

    def reset_game_state(self):
        self.player1 = Paddle(50, HEIGHT//2 - 60, None, None)
        self.player2 = Paddle(WIDTH - 70, HEIGHT//2 - 60, None, None)
        self.left_panel = self.player1
        self.right_panel = self.player2

        # AI玩家是两个玩家
        self.players = [self.player1, self.player2]
        self.ball = Ball()
        self.reset_positions(who = 0)
        self.winner = ''

    def spin_ball(self):
        self.ball.rect.center = (WIDTH//2, HEIGHT//2)
        self.ball.speed = [8, 0]
        start = -10, 10
        self.ball.velocity_x, self.ball.velocity_y = start[1 if pygame.time.get_ticks() % 2 else 0], 0

    def reset_positions(self, scorer):
        self.player1.rect.y = HEIGHT//2 - 60
        self.player2.rect.y = HEIGHT//2 - 60
        self.ball.rect.center = (WIDTH//2, HEIGHT//2)
        self.ball.speed_x = 7 if scorer == 0 else -7
        self.ball.speed_y = 0 if scorer != -1 else 0
        self.ball.rect.centerx = WIDTH // 2 if scorer != 1 else 100

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
            if self.winner_text and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.__init__()  # 重新开始

        keys = pygame.key.get_pressed()
        if keys[pygame.K_w] and self.player1.rect.top > 0:
            self.player1.rect.y = max(0, self.player1.rect.y - 8)
        if keys[pygame.K_s] and self.player1.rect.bottom < HEIGHT:
            self.player1.rect.y = min(HEIGHT - self.player1.height, self.player1.rect.y + 8)
        if keys[pygame.K_UP]:
            self.player2.rect.y = max(0, self.player2.rect.y - 8)
        if keys[pygame.K_DOWN]:
            self.player2.rect.y = min(HEIGHT - self.player2.height, self.player2.rect.y + 8)

    def update_ball_position(self):
        ball = self.ball
        
        # 碰撞上下边界
        if ball.rect.top <= 0 or ball.rect.bottom >= HEIGHT:
            ball.speed_y *= -1
        
        # 与球拍1碰撞
        if ball.rect.colliderect(self.player1.rect) and ball.velocity_x < 0:
            ball.velocity_x *= -1
        if ball.rect.colliderect(self.player2.rect) and ball.velocity_x > 0:
            ball.velocity_x *= -1

        # 更新位置
        ball.rect.x += ball.velocity_x
        ball.rect.y += ball.velocity_y
        
        # AI 移动，实现简单的AI玩家
        if ball.velocity_x < 0:  # 向左移动
            ai_paddle = self.player1
        else:
            ai_paddle = self.player2
            
        if ai_paddle.rect.centery > ball.rect.centery + 10:
            ai_paddle.rect.move_ip(0, -5)  # 使用move_ip移动
        elif ai_paddle.rect.centery < ball.rect.centery - 10:
            ai_paddle.rect.move_ip(0, 5)
        ai_paddle.rect.clamp_ip(pygame.Rect(0,0,WIDTH, HEIGHT))

        # 边界检测
        if ball.rect.left < 0:
            ball.reset_ball()
            ball.velocity_x = abs(ball.velocity_x)
        elif ball.rect.right > WIDTH:
            ball.reset_ball()
            ball.velocity_x = -6  # 设定一个方向

    def show_winner_screen(self, winner_text):
        self.winner_text = winner_text

    def run(self):
        while True:
            self.handle_events()
            self.window.fill(BLACK)

            # 移动玩家球拍
            keys = pygame.key.get_pressed()
            if keys[pygame.K_w] and self.player1.rect.top > 0:
                self.player1.move_up()
            if keys[pygame.K_s] and self.player1.rect.bottom < HEIGHT:
                self.player1.move_down()
            if keys[pygame.K_UP] and self.player2.rect.top > 0:
                self.player2.move_up()
            if keys[pygame.K_DOWN] and self.player2.rect.bottom < HEIGHT:
                self.player2.move_down()

            # 获取电脑玩家
            self.player1.computer_ai(self.ball)
            self.update_ball_position()

            # 绘制
            self.window.fill(BLACK)

            # 绘制中线和点状线
            pygame.draw.line(self.window, WHITE, (WIDTH//2-1, 0), (WIDTH//2-1, HEIGHT), 2) # 中线
            for i in range(0, HEIGHT, 30): # 虚线
                pygame.draw.rect(self.window, WHITE, (WIDTH//2-1, i, 3, 15))
            
            # 绘制使用Pygame的绘制方法，球拍和球
            self.ball.draw(self.window)
            self.player1.draw(self.window)
            self.player2.draw(self.window)
            
            # 绘制分数
            left_score_text = FONT.render(str(self.player1.score), True, WHITE)
            right_score_text = FONT.render(str(self.player2.score), True, WHITE)
            self.window.blit(left_score_text, (WIDTH//4, 30))
            self.window.blit(right_score_text, (3*WIDTH//4 - right_score_text.get_width(), 30))

            # 检查胜利条件
            if self.player1.score == self.WIN_SCORE or self.player2.score == self.WIN_SCORE:
                self.show_winner()
                if self.winner:
                    winner_text = self.winner + " WON"
                    text = FONT.render(winner_text, True, (255, 0, 0))
                    self.window.blit(text, (WIDTH//2 - text.get_width()/2, 50))
                    pygame.display.update()
                    pygame.time.wait(3000)  # 显示3秒后回到菜单
                return self.main_menu()  # 回到主菜单或重新开始

            pygame.display.update()
            self.clock.tick(60)

    def main_menu(self):
        paused = True
        while paused:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False, False  # 完全退出
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        return True  # 开始游戏
                    if event.key == pygame.K_2:
                        return False
            # 显示菜单
            # ... 详情略

def main():
    game = PongGame()
    while True:
        game.run()

if __name__ == "__main__":
    main()