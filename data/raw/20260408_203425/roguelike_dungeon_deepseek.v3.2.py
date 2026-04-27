import pygame
import random
import sys
import math

# 初始化
pygame.init()

# 常量
SCREEN_WIDTH, SCREEN_HEIGHT = 1200, 800
TILE_SIZE = 32
FPS = 60

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (30, 144, 255)
BROWN = (139, 69, 19)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
DARKGREEN = (0, 100, 0)
TEXT_COLOR = (50, 50, 50)
PLAYER_COLOR = (65, 105, 225)
ENEMY_COLOR = (220, 20, 60)
WALL_COLOR = (101, 67, 33, 180)
EXIT_COLOR = (255, 223, 0)

# 初始化
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags=pygame.SCALED)
pygame.display.set_caption("Roguelike Dungeon")
clock = pygame.time.Clock()

# 创建字体
pygame.font.init()
font = pygame.font.SysFont(None, 24)
big_font = pygame.font.SysFont(None, 48)

# 游戏状态
class GameState:
    def __init__(self):
        self.level = 1
        self.floor = 1
        self.room_map = []
        self.room_centers = []
        self.corridors = []
        self.player_x, self.player_y = 0, 0
        self.player_hp = 100
        self.player_max_hp = 100
        self.player_atk = 15
        self.player_def = 0
        self.player_exp = 0
        self.player_level = 1
        self.exp_to_next = 100
        self.game_over = False
        self.message = ""

    def level_up(self):
        self.player_level += 1
        self.player_max_hp += 10
        self.player_hp += 20
        self.player_atk += 3

game_state = GameState()

# 辅助函数
def generate_dungeon(width, height):
    map_data = [['#' for x in range(width)] for y in range(height)]
    room1 = (random.randint(5, width//4), random.randint(5, height-4))
    room2 = (random.randint(width*3//4, width-5), 
              random.randint(5, height-4))
    
    for y in range(room1[1], room1[1]+4):
        for x in range(room1[0], room1[0]+6):
            if 0 <= y < height and 0 <= x < width:
                map_data[y][x] = '.'
    for y in range(room2[1], room2[1]+3):
        for x in range(room2[0], room2[0]+5):
            if 0 <= y < height and 0 <= x < width:
                map_data[y][x] = '.'
    start_y = room1[0] + 2
    for x in range(room1[0]+6, room2[0]):
        if 0 <= start_y < height and 0 <= x < width:
            map_data[start_y][x] = '.'
    return map_data

def draw_health_bar(surf, x, y, pct):
    if pct < 0:
        pct = 0
    bar_width = 200
    bar_height = 20
    fill = pct * bar_width / 100
    pygame.draw.rect(surf, (255,0,0), (x, y, bar_width, bar_height), 2)
    pygame.draw.rect(surf, (255,150,150), (x+1, y+1, int(fill)-2, bar_height-2))

def main():
    map_w, map_h = 80, 45
    screen_w, screen_h = SCREEN_WIDTH, SCREEN_HEIGHT
    camera_x, camera_y = 0, 0
    keys = set()
    tiles, player_x, player_y = generate_level(map_w, map_h)
    running = True

    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    if game_state.game_over:
                        running = False
            if e.type == pygame.KEYDOWN:
                if not game_state.game_over:
                    old_x, old_y = player_x, player_y
                    try_move = (0,0)
                    if e.key == pygame.K_UP or e.key == pygame.K_w:
                        try_move = (0, -1)
                    elif e.key == pygame.K_DOWN or e.key == pygame.K_s:
                        try_move = (0, 1)
                    if e.key == pygame.K_LEFT or e.key == pygame.K_a:
                        try_move = (-1, 0)
                    if e.key == pygame.K_RIGHT or e.key == pygame.K_d:
                        try_move = (1, 0)
                    if try_move != (0,0):
                        new_x, new_y = player_x+try_move[0], player_y+try_move[1]
                        if (0 <= new_x < map_w and 0 <= new_y < map_h
                             and tiles[new_y][new_x] == '.'):
                            sx, sy = camera_x, camera_y
                            player_x, player_y = new_x, new_y
                            camera_x = max(0, min(camera_x, player_x*TILE_SIZE))
                            camera_y = 0

        screen.fill((20,12,28))
        for y in range(map_h):
            for x in range(map_w):
                dx = (x*TILE_SIZE) - camera_x*TILE_SIZE
                dy = (y*TILE_SIZE) - camera_y*TILE_SIZE
                rect = (dx, dy, TILE_SIZE, TILE_SIZE)
                if tiles[y][x] == '#':
                    # 墙
                    dark = (180,200,220)
                    px,py = rect[0], rect[1]
                    pygame.draw.rect(screen, (30, 40, 50), 
                                   (px, py, TILE_SIZE//2, TILE_SIZE))
                    if y>0 and y+1<map_h and tiles[y+1][x]=='.' :
                        cl = (200,180,80)
                        pygame.draw.rect(screen, cl, (px, py+TILE_SIZE//2, TILE_SIZE, TILE_SIZE//2))
                elif tiles[y][x] == '.':
                    # 地板
                    col = (80,70,50)
                    circ = (dx+TILE_SIZE//2, dy+TILE_SIZE//2)
                    pygame.draw.circle(screen,(90,80,60),circ, TILE_SIZE//2 - 2)
                    pygame.draw.circle(screen,(120,110,80),circ,TILE_SIZE//2-4)
                    
        player_screen_x = (player_x * TILE_SIZE) - camera_x*TILE_SIZE
        player_screen_y = (player_y * TILE_SIZE)
        pygame.draw.rect(screen,PLAYER_COLOR,
                         (player_screen_x, player_screen_y, TILE_SIZE, TILE_SIZE))
        # UI
        hp_percent = 80
        draw_health_bar(screen, 50, SCREEN_HEIGHT-100, hp_percent)
        level_text = f"LV:1 HP:{game_state.player_hp}"
        level_surf = font.render(level_text, True, (255,255,255))
        screen.blit(level_surf, (20,20))

        # 消息
        msg_surf = font.render(game_state.message, True, (255,255,255))
        screen.blit(msg_surf, (SCREEN_WIDTH//2 - 100,20))
        
        pygame.display.flip()
        clock.tick(20)

    pygame.quit()

if __name__ == "__main__":
    main()