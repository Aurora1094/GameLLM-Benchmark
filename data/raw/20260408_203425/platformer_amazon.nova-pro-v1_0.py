import pygame
import random

pygame.init()

# 设置游戏窗口
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Platformer Hard")

# 颜色
white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
yellow = (255, 255, 0)

# 玩家类
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((50, 50))
        self.image.fill(blue)
        self.rect = self.image.get_rect()
        self.rect.x = 50
        self.rect.y = screen_height - 100
        self.change_x = 0
        self.change_y = 0
        self.level = None

    def update(self):
        self.calc_grav()
        self.rect.x += self.change_x
        block_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
        for block in block_hit_list:
            if self.change_x > 0:
                self.rect.right = block.rect.left
            elif self.change_x < 0:
                self.rect.left = block.rect.right

        self.rect.y += self.change_y
        block_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
        for block in block_hit_list:
            if self.change_y > 0:
                self.rect.bottom = block.rect.top
            elif self.change_y < 0:
                self.rect.top = block.rect.bottom
            self.change_y = 0

    def calc_grav(self):
        if self.change_y == 0:
            self.change_y = 1
        else:
            self.change_y += 0.35

        if self.rect.y >= screen_height - self.rect.height and self.change_y >= 0:
            self.change_y = 0
            self.rect.y = screen_height - self.rect.height

    def go_left(self):
        self.change_x = -6

    def go_right(self):
        self.change_x = 6

    def stop(self):
        self.change_x = 0

    def jump(self):
        self.rect.y += 2
        platform_hit_list = pygame.sprite.spritecollide(self, self.level.platform_list, False)
        self.rect.y -= 2

        if len(platform_hit_list) > 0 or self.rect.bottom >= screen_height:
            self.change_y = -10

# 平台类
class Platform(pygame.sprite.Sprite):
    def __init__(self, width, height):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(green)
        self.rect = self.image.get_rect()

# 移动平台类
class MovingPlatform(Platform):
    def __init__(self, width, height):
        super().__init__(width, height)
        self.change_x = 3
        self.change_y = 0
        self.boundary_top = 0
        self.boundary_bottom = 0
        self.level = None

    def update(self):
        self.rect.x += self.change_x

        hit = pygame.sprite.spritecollide(self, self.level.player.sprites(), False)
        for player in hit:
            if self.change_x < 0:
                player.rect.right = self.rect.left
            elif self.change_x > 0:
                player.rect.left = self.rect.right

        hit_platform = pygame.sprite.spritecollide(self, self.level.platform_list, False)
        for p in hit_platform:
            if isinstance(p, MovingPlatform):
                if self.change_x < 0:
                    if self.rect.left <= p.rect.left:
                        self.change_x *= -1
                elif self.change_x > 0:
                    if self.rect.right >= p.rect.right:
                        self.change_x *= -1
            elif isinstance(p, Platform):
                if self.change_x < 0:
                    if self.rect.left <= p.rect.left:
                        self.change_x *= -1
                elif self.change_x > 0:
                    if self.rect.right >= p.rect.right:
                        self.change_x *= -1

        if self.rect.bottom > self.boundary_bottom or self.rect.top < self.boundary_top:
            self.change_y *= -1

        self.rect.y += self.change_y

# 敌人类
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface([30, 30])
        self.image.fill(red)
        self.rect = self.image.get_rect()
        self.change_x = 3
        self.level = None
        self.boundary_top = 0
        self.boundary_bottom = 0
        self.level = None

    def update(self):
        self.rect.x += self.change_x
        pos = self.rect.x + self.level.world_shift
        if pos < self.boundary_top or pos > self.boundary_bottom:
            self.change_x *= -1

# 金币类
class Coin(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface([20, 20])
        self.image.fill(yellow)
        self.rect = self.image.get_rect()

# 旗帜类
class Flag(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface([30, 60])
        self.image.fill(green)
        self.rect = self.image.get_rect()

# 关卡类
class Level:
    def __init__(self, player):
        self.platform_list = pygame.sprite.Group()
        self.enemy_list = pygame.sprite.Group()
        self.coin_list = pygame.sprite.Group()
        self.flag_list = pygame.sprite.Group()
        self.player = pygame.sprite.GroupSingle(player)
        self.world_shift = 0
        self.level_limit = -1000

    def update(self):
        self.platform_list.update()
        self.enemy_list.update()
        self.coin_list.update()
        self.player.update()

        self.world_shift += self.player.sprite.change_x

        if self.world_shift >= 20 or self.world_shift <= -20:
            self.world_shift = 0

            for platform in self.platform_list:
                platform.rect.x -= self.player.sprite.change_x

            for enemy in self.enemy_list:
                enemy.rect.x -= self.player.sprite.change_x

            for coin in self.coin_list:
                coin.rect.x -= self.player.sprite.change_x

            for flag in self.flag_list:
                flag.rect.x -= self.player.sprite.change_x

    def draw(self, screen):
        screen.fill(white)
        self.platform_list.draw(screen)
        self.enemy_list.draw(screen)
        self.coin_list.draw(screen)
        self.flag_list.draw(screen)
        self.player.draw(screen)

# 关卡1
class Level_01(Level):
    def __init__(self, player):
        super().__init__(player)
        level = [
            "PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P              P",
            "P                                                                               P