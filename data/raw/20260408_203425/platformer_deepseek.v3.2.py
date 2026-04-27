import pygame
import random
import sys

# 初始化
pygame.init()
WIDTH, HEIGHT = 800, 600
FPS = 60
TILE_SIZE = 64
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 120, 255)
YELLOW = (255, 255, 0)
PINK = (255, 182, 193)
BLACK = (0, 0, 0)
PURPLE = (180, 0, 255)

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 30, 50)
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 5
        self.jump_power = 15
        self.gravity = 0.8
        self.on_ground = False
        self.facing_right = True
        self.lives = 3
        self.lives_cooldown = 0

    def update(self, platforms, enemies):
        if self.lives_cooldown > 0:
            self.lives_cooldown -= 1

        # 左右移动
        keys = pygame.key.get_pressed()
        self.vel_x = 0
        if (keys[pygame.K_LEFT] or keys[pygame.K_a]) and self.rect.left > 0:
            self.vel_x = -self.speed
            self.facing_right = False
        if (keys[pygame.K_RIGHT] or keys[pygame.K_d]) and self.rect.right < WIDTH:
            self.vel_x = self.speed
            self.facing_right = True

        # 应用重力
        self.rect.x += self.vel_x
        self.apply_collision(0, platforms)
        
        self.vel_y += self.gravity
        # 左右手动添加下坠速度上限，防止下落速度过快穿墙
        if self.vel_y > 15:
            self.vel_y = 15
        self.rect.y += self.vel_y
        # 下落过程中与平台顶部碰撞检测
        if self.vel_y > 0:  # 下落
            for p in platforms:
                if p.colliderect(self.rect):
                    # 调整玩家至平台顶部
                    self.rect.bottom = p.top
                    self.vel_y = 0
                    self.on_ground = True
        
        self.vel_x = self.rect.x - prev_x
        prev_x = self.rect.x

        # 跳跃
        if (keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = -self.jump_power

    def apply_collision(self, dx, platforms):
        for p in platforms:
            if self.rect.colliderect(p.rect):
                if dx > 0:
                    self.rect.right = p.rect.left
                elif dx < 0:
                    self.rect.left = p.rect.right

class Platform:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, 30)
        self.moving = False
        self.speed = 0
        self.original_x, self.original_y = x, y

    def move_horizontal(self, start, end, speed):
        self.rect.x += speed
        if self.rect.x <= start or self.rect.x >= end:
            speed = -speed
        return speed

class Enemy:
    def __init__(self, x, y, left_limit, right_limit,):
        self.rect = pygame.Rect(x, y, 30, 40)
        self.direction = 1  # 1右，-1左
        self.speed = 2
        self.left_bound = left_limit
        self.right_bound = right_limit

    def update(self, platforms):
        self.rect.x += self.speed * self.direction
        # 碰撞 detection with screen edges
        if self.rect.right >= self.right_bound or self.rect.left <= self.left_bound:
            self.direction *= -1

class Coin:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.collected = False

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True
        #font = pygame.font.SysFont(None, 36)
        self.platforms = [
            pygame.Rect(100, HEIGHT - 50, 200, 20),
            pygame.Rect(350, 400, 150, 20),
            pygame.Rect(500, HEIGHT - 150, 200, 20),
            pygame.Rect(50, 200, 150, 20),
        ]
        self.player = Player(100, HEIGHT - 100)
        self.coins = [Coin((i+1) * 80, 300) for i in range(5)]
        self.score = 0
        self.current_level = 1
        self.enemies = [
            pygame.Rect(300, 150, 20, 20)
        ]

    def draw_ground(self):
        for platform in self.platforms:
            pygame.draw.rect(self.screen, WHITE, platform)

    def run(self):
        while self.running:
            self.screen.fill((30, 30, 30))  # Dark gray background
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    return

                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.menu_screen()

            self.draw_elements()
            pygame.display.update()
        
    def menu_screen(self):
        #Pygame main loop
        root = tk.Tk()
        root.withdraw()  # Hide the Tkinter root

        lvl_won = None
        while self.run:
            dt = self.clock.tick(FPS) / 500.0
            dt *= 60
            for event in pygame.event.get():
                run_flag = self.handle_event(event, dt)

                if event.type == pygame.QUIT:
                    run_flag = False
                    break 

            if not run_flag:
                break

            # ---UPDATE YOUR GAME STATE AND LOGIC
            ...