import pygame
import random
import sys

# 初始化
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders Medium")
clock = pygame.time.Clock()

# 颜色
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 120, 255)
YELLOW = (255, 255, 0)

# 玩家
class Player:
    def __init__(self):
        self.width = 60
        self.height = 40
        self.x = WIDTH // 2 - self.width // 2
        self.y = HEIGHT - self.height - 20
        self.speed = 6
        self.color = GREEN
        self.bullets = []
        self.cooldown = 0

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        # 绘制炮台
        pygame.draw.rect(screen, GREEN, (self.x + self.width//2 - 5, self.y - 10, 10, 10))

    def move(self, direction):
        if direction == "left" and self.x > 0:
            self.x -= self.speed
        if direction == "right" and self.x < WIDTH - self.width:
            self.x += self.speed

    def shoot(self):
        if self.cooldown == 0:
            self.bullets.append([self.x + self.width//2 - 2, self.y])
            self.cooldown = 15

    def update_bullets(self):
        for bullet in self.bullets[:]:
            bullet[1] -= 8
            if bullet[1] < 0:
                self.bullets.remove(bullet)
        if self.cooldown > 0:
            self.cooldown -= 1

# 外星人
class Alien:
    def __init__(self, x, y, row):
        self.width = 40
        self.height = 30
        self.x = x
        self.y = y
        self.row = row
        self.speed_x = 2
        self.color = YELLOW if row % 3 == 0 else RED if row % 3 == 1 else BLUE
        self.bullets = []

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.width, self.height))
        # 两只眼睛
        pygame.draw.circle(screen, BLACK, (self.x + 10, self.y + 10), 5)
        pygame.draw.circle(screen, BLACK, (self.x + self.width - 10, self.y + 10), 5)

    def move(self, direction):
        if direction == "right":
            self.x += self.speed_x
        else:
            self.x -= self.speed_x

    def maybe_shoot(self):
        if random.random() < 0.0005:  # 随机发射概率
            self.bullets.append([self.x + self.width//2 - 2, self.y + self.height])

    def update_bullets(self):
        for bullet in self.bullets[:]:
            bullet[1] += 5
            if bullet[1] > HEIGHT:
                self.bullets.remove(bullet)

# 游戏管理
class Game:
    def __init__(self):
        self.player = Player()
        self.aliens = []
        self.alien_direction = "right"
        self.alien_move_timer = 0
        self.score = 0
        self.game_over = False
        self.win = False
        self.font = pygame.font.SysFont(None, 36)
        self.create_aliens()

    def create_aliens(self):
        rows = 5
        cols = 10
        spacing_x = 60
        spacing_y = 50
        start_x = 50
        start_y = 50
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * spacing_x
                y = start_y + row * spacing_y
                self.aliens.append(Alien(x, y, row))

    def update_aliens(self):
        self.alien_move_timer += 1
        move_down = False
        if self.alien_move_timer > 30:
            self.alien_move_timer = 0
            edge_hit = False
            for alien in self.aliens:
                if self.alien_direction == "right" and alien.x + alien.width >= WIDTH:
                    edge_hit = True
                    break
                if self.alien_direction == "left" and alien.x <= 0:
                    edge_hit = True
                    break
            if edge_hit:
                self.alien_direction = "left" if self.alien_direction == "right" else "right"
                move_down = True

            for alien in self.aliens:
                alien.move(self.alien_direction)
                if move_down:
                    alien.y += 20
                alien.maybe_shoot()

        # 检查是否到达底部
        for alien in self.aliens:
            if alien.y + alien.height >= HEIGHT:
                self.game_over = True

    def check_collisions(self):
        # 玩家子弹与外星人
        for bullet in self.player.bullets[:]:
            bullet_rect = pygame.Rect(bullet[0], bullet[1], 4, 10)
            for alien in self.aliens[:]:
                alien_rect = pygame.Rect(alien.x, alien.y, alien.width, alien.height)
                if bullet_rect.colliderect(alien_rect):
                    self.score += 10
                    if bullet in self.player.bullets:
                        self.player.bullets.remove(bullet)
                    if alien in self.aliens:
                        self.aliens.remove(alien)
                    break

        # 外星人子弹与玩家
        player_rect = pygame.Rect(self.player.x, self.player.y, self.player.width, self.player.height)
        for alien in self.aliens:
            for bullet in alien.bullets[:]:
                bullet_rect = pygame.Rect(bullet[0], bullet[1], 4, 10)
                if bullet_rect.colliderect(player_rect):
                    self.game_over = True

        # 外星人与玩家相撞
        for alien in self.aliens:
            alien_rect = pygame.Rect(alien.x, alien.y, alien.width, alien.height)
            if alien_rect.colliderect(player_rect):
                self.game_over = True

    def update(self):
        if self.game_over or self.win:
            return
        self.player.update_bullets()
        self.update_aliens()
        for alien in self.aliens:
            alien.update_bullets()
        self.check_collisions()
        if len(self.aliens) == 0:
            self.win = True

    def draw(self):
        screen.fill(BLACK)
        self.player.draw()
        for bullet in self.player.bullets:
            pygame.draw.rect(screen, GREEN, (bullet[0], bullet[1], 4, 10))
        for alien in self.aliens:
            alien.draw()
            for bullet in alien.bullets:
                pygame.draw.rect(screen, RED, (bullet[0], bullet[1], 4, 10))
        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        if self.game_over:
            text = self.font.render("GAME OVER - Press R to restart", True, RED)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2))
        if self.win:
            text = self.font.render("YOU WIN! - Press R to restart", True, GREEN)
            screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2))

def main():
    game = Game()
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game.game_over and not game.win:
                    game.player.shoot()
                if event.key == pygame.K_r:
                    if game.game_over or game.win:
                        game = Game()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            game.player.move("left")
        if keys[pygame.K_RIGHT]:
            game.player.move("right")

        game.update()
        game.draw()
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()