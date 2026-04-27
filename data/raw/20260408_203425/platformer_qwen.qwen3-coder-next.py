import pygame
import sys

# 初始化 Pygame
pygame.init()

# 屏幕设置
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Platformer Hard")

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
DARK_GRAY = (50, 50, 50)
LIGHT_GRAY = (200, 200, 200)

# 游戏常量
PLAYER_SPEED = 5
PLAYER_JUMP = -13
GRAVITY = 0.6
ENEMY_SPEED = 2
MAX_LIVES = 3
FLAG_REWARD = 100
COIN_REWARD = 10
TOTAL_LEVELS = 3

# 字体
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 30
        self.height = 50
        self.vel_x = 0
        self.vel_y = 0
        self.is_jumping = False
        self.color = BLUE
        self.lives = MAX_LIVES
        self.invincible = False
        self.invincible_timer = 0
        self.facing_right = True

    def update(self, platforms, enemies, coins, level, game):
        # 输入处理
        keys = pygame.key.get_pressed()
        self.vel_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -PLAYER_SPEED
            self.facing_right = False
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = PLAYER_SPEED
            self.facing_right = True
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and not self.is_jumping:
            self.vel_y = PLAYER_JUMP
            self.is_jumping = True

        # 重力应用
        self.vel_y += GRAVITY

        # 更新位置
        self.x += self.vel_x
        self.y += self.vel_y

        # 限制边界（左右）
        if self.x < 0:
            self.x = 0
        elif self.x + self.width > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.width

        # 碰撞检测：平台
        on_ground = False
        for platform in platforms:
            if (self.x < platform.x + platform.width and
                self.x + self.width > platform.x and
                self.y < platform.y + platform.height and
                self.y + self.height > platform.y):
                
                # 落地检测（只检测从上方下落）
                if self.vel_y > 0 and (self.y + self.height - self.vel_y) <= platform.y:
                    self.y = platform.y - self.height
                    self.vel_y = 0
                    self.is_jumping = False
                    on_ground = True
                # 顶头检测（只检测从下方上升）
                elif self.vel_y < 0 and (self.y - self.vel_y) >= platform.y + platform.height:
                    self.y = platform.y + platform.height
                    self.vel_y = 0
        
        # 掉出屏幕则重置
        if self.y > SCREEN_HEIGHT:
            self.reset_to_start()
            game.lose_life()

        # 收集金币
        for coin in coins[:]:
            if (self.x < coin.x + coin.width and
                self.x + self.width > coin.x and
                self.y < coin.y + coin.height and
                self.y + self.height > coin.y):
                coins.remove(coin)
                game.score += COIN_REWARD

        # 敌人碰撞检测
        for enemy in enemies:
            if (not self.invincible and
                self.x < enemy.x + enemy.width and
                self.x + self.width > enemy.x and
                self.y < enemy.y + enemy.height and
                self.y + self.height > enemy.y):
                self.reset_to_start()
                game.lose_life()
                self.invincible = True
                self.invincible_timer = 120  # 2秒 @ 60fps

        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False

        # 门/终点检测
        if (game.level < TOTAL_LEVELS and
            self.x < game.end_gate.x + game.end_gate.width and
            self.x + self.width > game.end_gate.x and
            self.y < game.end_gate.y + game.end_gate.height and
            self.y + self.height > game.end_gate.y):
            game.next_level()

    def reset_to_start(self):
        self.x = 50
        self.y = SCREEN_HEIGHT - 100
        self.vel_x = 0
        self.vel_y = 0

    def draw(self, screen):
        if self.invincible and self.invincible_timer % 4 < 2:
            return  # 闪烁效果
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        # 眼睛
        eye_offset = 5 if self.facing_right else -5
        pygame.draw.circle(screen, WHITE, (self.x + 10 + eye_offset, self.y + 10), 4)
        pygame.draw.circle(screen, BLACK, (self.x + 10 + eye_offset, self.y + 10), 2)

class Platform:
    def __init__(self, x, y, width, height, move_range=0, move_speed=0):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.start_x = x
        self.move_range = move_range
        self.move_speed = move_speed
        self.direction = 1

    def update(self):
        if self.move_range > 0:
            self.x += self.move_speed * self.direction
            if self.x <= self.start_x:
                self.x = self.start_x
                self.direction = 1
            elif self.x >= self.start_x + self.move_range:
                self.x = self.start_x + self.move_range
                self.direction = -1

    def draw(self, screen):
        # 平台主体
        pygame.draw.rect(screen, DARK_GRAY, (self.x, self.y, self.width, self.height))
        # 平台顶部细节
        pygame.draw.rect(screen, LIGHT_GRAY, (self.x, self.y, self.width, 5))

class Enemy:
    def __init__(self, x, y, patrol_distance):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 30
        self.start_x = x
        self.patrol_distance = patrol_distance
        self.direction = -1
        self.speed = ENEMY_SPEED

    def update(self):
        self.x += self.speed * self.direction
        # 限制巡逻范围
        if self.x <= self.start_x or self.x >= self.start_x + self.patrol_distance:
            self.direction *= -1

    def draw(self, screen):
        # 敌人本体
        pygame.draw.rect(screen, RED, (self.x, self.y, self.width, self.height))
        # 眼睛
        eye_offset = 15 if self.direction == -1 else 5
        pygame.draw.circle(screen, WHITE, (self.x + 10 + eye_offset, self.y + 10), 5)
        pygame.draw.circle(screen, BLACK, (self.x + 10 + eye_offset, self.y + 10), 2)
        # 尖刺装饰
        pygame.draw.polygon(screen, ORANGE, [
            (self.x, self.y + self.height),
            (self.x + self.width // 3, self.y + self.height + 10),
            (self.x + 2 * self.width // 3, self.y + self.height)
        ])

class Coin:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 20
        self.rotation = 0

    def draw(self, screen):
        self.rotation += 5
        radius = 10
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2
        color = YELLOW
        pygame.draw.circle(screen, color, (cx, cy), radius)
        # 币面细节
        pygame.draw.circle(screen, ORANGE, (cx, cy), radius - 3)
        text = font.render('$', True, ORANGE)
        text_rect = text.get_rect(center=(cx, cy))
        screen.blit(text, text_rect)

class Gate:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 50
        self.height = 70
        self.particle_timer = 0

    def draw(self, screen):
        # 门框架
        pygame.draw.rect(screen, BLACK, (self.x, self.y, self.width, self.height))
        # 门柱
        pygame.draw.rect(screen, GREEN, (self.x + 5, self.y, 10, self.height))
        pygame.draw.rect(screen, GREEN, (self.x + self.width - 15, self.y, 10, self.height))
        # 门楣
        pygame.draw.rect(screen, GREEN, (self.x, self.y, self.width, 15))
        # 门内发光效果
        self.particle_timer += 1
        alpha = int((1 + (self.particle_timer % 60) / 60) * 100)
        gate_surface = pygame.Surface((self.width - 10, self.height - 10), pygame.SRCALPHA)
        gate_surface.fill((100, 255, 100, alpha))
        screen.blit(gate_surface, (self.x + 10, self.y + 10))

class Game:
    def __init__(self):
        self.score = 0
        self.level = 1
        self.player = Player(50, SCREEN_HEIGHT - 150)
        self.platforms = []
        self.enemies = []
        self.coins = []
        self.end_gate = None
        self.game_over = False
        self.level_complete = False
        self.create_level()

    def create_level(self):
        self.platforms = []
        self.enemies = []
        self.coins = []
        
        # 地面
        self.platforms.append(Platform(0, SCREEN_HEIGHT - 50, SCREEN_WIDTH, 50))
        
        if self.level == 1:
            # 平台设计
            self.platforms.extend([
                Platform(200, SCREEN_HEIGHT - 180, 150, 20),
                Platform(450, SCREEN_HEIGHT - 280, 100, 20),
                Platform(650, SCREEN_HEIGHT - 180, 150, 20),
                Platform(300, SCREEN_HEIGHT - 400, 200, 20)
            ])
            # 敌人
            self.enemies.extend([
                Enemy(250, SCREEN_HEIGHT - 180 - 30, 100),
                Enemy(470, SCREEN_HEIGHT - 280 - 30, 60)
            ])
            # 金币
            self.coins.extend([
                Coin(350, SCREEN_HEIGHT - 180 - 30),
                Coin(480, SCREEN_HEIGHT - 280 - 30),
                Coin(700, SCREEN_HEIGHT - 180 - 30),
                Coin(400, SCREEN_HEIGHT - 400 - 30)
            ])
            # 终点门
            self.end_gate = Gate(700, SCREEN_HEIGHT - 50 - 70)
            
        elif self.level == 2:
            # 平台设计
            self.platforms.extend([
                Platform(50, SCREEN_HEIGHT - 200, 100, 20),
                Platform(250, SCREEN_HEIGHT - 300, 100, 20, 150, 2),
                Platform(450, SCREEN_HEIGHT - 200, 100, 20),
                Platform(650, SCREEN_HEIGHT - 350, 150, 20),
                Platform(300, SCREEN_HEIGHT - 500, 200, 20)
            ])
            # 敌人
            self.enemies.extend([
                Enemy(30, SCREEN_HEIGHT - 200 - 30, 60),
                Enemy(500, SCREEN_HEIGHT - 350 - 30, 100),
                Enemy(400, SCREEN_HEIGHT - 500 - 30, 100)
            ])
            # 金币
            self.coins.extend([
                Coin(100, SCREEN_HEIGHT - 200 - 30),
                Coin(300, SCREEN_HEIGHT - 300 - 30),
                Coin(500, SCREEN_HEIGHT - 200 - 30),
                Coin(700, SCREEN_HEIGHT - 350 - 30),
                Coin(400, SCREEN_HEIGHT - 500 - 30)
            ])
            # 终点门
            self.end_gate = Gate(700, SCREEN_HEIGHT - 350 - 70)
            
        else:  # Level 3
            # 平台设计
            self.platforms.extend([
                Platform(100, SCREEN_HEIGHT - 150, 100, 20),
                Platform(300, SCREEN_HEIGHT - 250, 100, 20, 120, 3),
                Platform(500, SCREEN_HEIGHT - 350, 100, 20),
                Platform(650, SCREEN_HEIGHT - 250, 100, 20),
                Platform(400, SCREEN_HEIGHT - 450, 200, 20),
                Platform(200, SCREEN_HEIGHT - 550, 100, 20)
            ])
            # 敌人
            self.enemies.extend([
                Enemy(300, SCREEN_HEIGHT - 250 - 30, 100),
                Enemy(500, SCREEN_HEIGHT - 350 - 30, 60),
                Enemy(450, SCREEN_HEIGHT - 450 - 30, 100),
                Enemy(150, SCREEN_HEIGHT - 550 - 30, 60)
            ])
            # 金币
            self.coins.extend([
                Coin(150, SCREEN_HEIGHT - 150 - 30),
                Coin(350, SCREEN_HEIGHT - 250 - 30),
                Coin(550, SCREEN_HEIGHT - 350 - 30),
                Coin(700, SCREEN_HEIGHT - 250 - 30),
                Coin(500, SCREEN_HEIGHT - 450 - 30),
                Coin(250, SCREEN_HEIGHT - 550 - 30)
            ])
            # 终点门
            self.end_gate = Gate(50, SCREEN_HEIGHT - 150 - 70)
        
        # 确保玩家初始位置正确
        self.player.x = 50
        self.player.y = SCREEN_HEIGHT - 150

    def lose_life(self):
        self.player.lives -= 1
        if self.player.lives <= 0:
            self.game_over = True

    def next_level(self):
        if self.level < TOTAL_LEVELS:
            self.level += 1
            self.create_level()
            # 奖励分数
            self.score += FLAG_REWARD
        else:
            # 完成所有关卡
            self.game_over = True
            self.level_complete = True

    def draw_ui(self):
        # 生命值显示
        lives_text = small_font.render("Lives: " + "♥" * self.player.lives, True, WHITE)
        screen.blit(lives_text, (10, 10))
        
        # 得分显示
        score_text = small_font.render("Score: " + str(self.player.score + self.score), True, WHITE)
        screen.blit(score_text, (10, 50))
        
        # 关卡显示
        level_text = small_font.render("Level: " + str(self.level) + "/3", True, WHITE)
        screen.blit(level_text, (10, 90))

    def draw_game_over(self):
        if self.level_complete:
            text = "CONGRATULATIONS! YOU WIN!"
            color = GREEN
        else:
            text = "GAME OVER"
            color = RED
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        
        game_over_text = font.render(text, True, color)
        final_score_text = font.render("Final Score: " + str(self.player.score + self.score), True, WHITE)
        restart_text = small_font.render("Press R to Restart or Q to Quit", True, WHITE)
        
        screen.blit(game_over_text, (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2, SCREEN_HEIGHT // 2 - 100))
        screen.blit(final_score_text, (SCREEN_WIDTH // 2 - final_score_text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, SCREEN_HEIGHT // 2))

    def reset(self):
        self.__init__()

# 主游戏循环
def main():
    clock = pygame.time.Clock()
    game = Game()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if game.game_over:
                    if event.key == pygame.K_r:
                        game.reset()
                    elif event.key == pygame.K_q:
                        running = False
        
        if not game.game_over:
            # 更新平台
            for platform in game.platforms:
                platform.update()
            
            # 更新敌人
            for enemy in game.enemies:
                enemy.update()
            
            # 更新玩家
            game.player.update(game.platforms, game.enemies, game.coins, game.level, game)
            
            # 绘制
            screen.fill((135, 206, 235))  # 天空蓝背景
            
            # 绘制平台
            for platform in game.platforms:
                platform.draw(screen)
            
            # 绘制敌人
            for enemy in game.enemies:
                enemy.draw(screen)
            
            # 绘制金币
            for coin in game.coins:
                coin.draw(screen)
            
            # 绘制门
            game.end_gate.draw(screen)
            
            # 绘制玩家
            game.player.draw(screen)
            
            # UI
            game.draw_ui()
        
        else:
            # 游戏结束画面
            game.draw_game_over()
        
        # 刷新显示
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()