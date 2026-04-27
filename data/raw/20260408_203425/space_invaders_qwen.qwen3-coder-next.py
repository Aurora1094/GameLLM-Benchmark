import pygame
import random
import sys

# 初始化 Pygame
pygame.init()

# 屏幕设置
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders Medium")

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)

# 游戏常量
PLAYER_WIDTH, PLAYER_HEIGHT = 50, 30
ALIEN_WIDTH, ALIEN_HEIGHT = 40, 30
BUCKET_WIDTH, BUCKET_HEIGHT = 5, 15
ALIEN_BULLET_WIDTH, ALIEN_BULLET_HEIGHT = 5, 10
PLAYER_SPEED = 5
ALIEN_SPEED_X = 1
ALIEN_SPEED_Y = 30
ALIEN_BULLET_SPEED = 5
ALIEN_SHOOT_PROBABILITY = 0.01  # 每帧射击概率

# 字体
font = pygame.font.SysFont(None, 36)
big_font = pygame.font.SysFont(None, 72)

# 玩家类
class Player:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH // 2 - PLAYER_WIDTH // 2, HEIGHT - PLAYER_HEIGHT - 10,
                                PLAYER_WIDTH, PLAYER_HEIGHT)
        self.speed = PLAYER_SPEED
    
    def update(self, keys):
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < WIDTH:
            self.rect.x += self.speed
    
    def draw(self):
        pygame.draw.rect(screen, GREEN, self.rect)
        # 简单的飞船形状
        pygame.draw.polygon(screen, (0, 255, 0), [
            (self.rect.centerx, self.rect.top - 10),
            (self.rect.left, self.rect.bottom),
            (self.rect.right, self.rect.bottom)
        ])

# 外星人类
class Alien:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, ALIEN_WIDTH, ALIEN_HEIGHT)
    
    def draw(self):
        pygame.draw.rect(screen, RED, self.rect)
        # 简单的外星人眼睛
        pygame.draw.rect(screen, WHITE, (self.rect.x + 5, self.rect.y + 5, 8, 8))
        pygame.draw.rect(screen, WHITE, (self.rect.x + ALIEN_WIDTH - 13, self.rect.y + 5, 8, 8))

# 游戏变量
player = Player()
aliens = []
aliens_bullets = []
bullets = []
score = 0
game_over = False
game_won = False

# 创建外星人群
def create_aliens():
    global aliens
    aliens = []
    rows = 5
    cols = 10
    Alien.SPEED_X = ALIEN_SPEED_X
    Alien.direction = 1
    Alien.move_timer = 0
    
    for row in range(rows):
        for col in range(cols):
            x = 100 + col * (ALIEN_WIDTH + 20)
            y = 50 + row * (ALIEN_HEIGHT + 20)
            aliens.append(Alien(x, y))

create_aliens()

# 玩家子弹类
class PlayerBullet:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, BUCKET_WIDTH, BUCKET_HEIGHT)
    
    def update(self):
        self.rect.y -= 7
    
    def draw(self):
        pygame.draw.rect(screen, YELLOW, self.rect)

# 外星人子弹类
class AlienBullet:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, ALIEN_BULLET_WIDTH, ALIEN_BULLET_HEIGHT)
    
    def update(self):
        self.rect.y += ALIEN_BULLET_SPEED
    
    def draw(self):
        pygame.draw.rect(screen, RED, self.rect)

# 子弹碰撞检测
def check_collisions():
    global game_over, game_won, score
    player_hit = False
    
    # 玩家子弹击中外星人
    for bullet in bullets[:]:
        hit = False
        for alien in aliens[:]:
            if bullet.rect.colliderect(alien.rect):
                bullets.remove(bullet)
                aliens.remove(alien)
                score += 10
                hit = True
                break
        if not hit and bullet.rect.bottom < 0:
            bullets.remove(bullet)
    
    # 外星人子弹击中玩家
    for bullet in aliens_bullets[:]:
        bullet.update()
        if bullet.rect.colliderect(player.rect):
            player_hit = True
            aliens_bullets.remove(bullet)
            game_over = True
    
    # 移除屏幕外的外星人子弹
    for bullet in aliens_bullets[:]:
        if bullet.rect.top > HEIGHT:
            aliens_bullets.remove(bullet)
    
    # 检查胜利
    if not aliens:
        game_won = True
        game_over = True
        
    # 检查外星人是否到达底部或碰到玩家
    for alien in aliens:
        if alien.rect.bottom >= HEIGHT:
            game_over = True
        if alien.rect.colliderect(player.rect):
            game_over = True

# 外星人射击
def alien_shoot():
    if aliens:
        shooter = random.choice(aliens)
        bullet = AlienBullet(shooter.rect.centerx, shooter.rect.bottom)
        aliens_bullets.append(bullet)

# 游戏主循环
def main():
    global game_over, game_won, score, bullets, aliens_bullets, player
    
    create_aliens()
    score = 0
    bullets.clear()
    aliens_bullets.clear()
    game_over = False
    game_won = False
    clock = pygame.time.Clock()
    
    while True:
        keys = pygame.key.get_pressed()
        
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over:
                    bullet = PlayerBullet(player.rect.centerx - BUCKET_WIDTH // 2, player.rect.top)
                    bullets.append(bullet)
                if event.key == pygame.K_r and (game_over or game_won):
                    # 重置游戏
                    create_aliens()
                    score = 0
                    bullets.clear()
                    aliens_bullets.clear()
                    player.rect.x = WIDTH // 2 - PLAYER_WIDTH // 2
                    game_over = False
                    game_won = False
        
        if not game_over:
            player.update(keys)
            
            # 更新玩家子弹
            for bullet in bullets[:]:
                bullet.update()
            
            # 外星人移动
            if aliens:
                move_aliens()
            
            # 外星人随机射击
            if random.random() < ALIEN_SHOOT_PROBABILITY:
                alien_shoot()
            
            # 碰撞检测
            check_collisions()
        
        # 绘制
        screen.fill(BLACK)
        
        # 绘制所有元素
        player.draw()
        for alien in aliens:
            alien.draw()
        for bullet in bullets:
            bullet.draw()
        for bullet in aliens_bullets:
            bullet.draw()
        
        # 显示分数
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        # 游戏结束或胜利界面
        if game_over:
            if game_won:
                text = big_font.render("YOU WIN!", True, GREEN)
            else:
                text = big_font.render("GAME OVER", True, RED)
            text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(text, text_rect)
            
            restart_text = font.render("Press 'R' to Restart", True, WHITE)
            restart_rect = restart_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 60))
            screen.blit(restart_text, restart_rect)
        
        pygame.display.flip()
        clock.tick(60)

def move_aliens():
    if not aliens:
        return
    
    # 计算当前最边缘的外星人位置
    rightmost = max(alien.rect.right for alien in aliens)
    leftmost = min(alien.rect.left for alien in aliens)
    
    # 移动方向控制
    if rightmost >= WIDTH - 10:
        Alien.direction = -1
        for alien in aliens:
            alien.rect.y += ALIEN_SPEED_Y
    elif leftmost <= 10:
        Alien.direction = 1
        for alien in aliens:
            alien.rect.y += ALIEN_SPEED_Y
    
    # 水平移动
    for alien in aliens:
        alien.rect.x += Alien.direction * ALIEN_SPEED_X

if __name__ == "__main__":
    main()