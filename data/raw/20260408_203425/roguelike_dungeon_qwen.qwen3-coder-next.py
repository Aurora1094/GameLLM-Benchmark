import pygame
import random
import sys

# 初始化 Pygame
pygame.init()

# 常量定义
TILE_SIZE = 24
MAP_WIDTH = 40
MAP_HEIGHT = 30
SCREEN_WIDTH = TILE_SIZE * MAP_WIDTH
SCREEN_HEIGHT = TILE_SIZE * MAP_HEIGHT + 60  # 额外显示状态栏
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 128, 0)
PLAYER_COLOR = (0, 191, 255)
ENEMY_COLOR = (220, 20, 60)
ITEM_COLOR = (127, 255, 0)
XP_COLOR = (255, 215, 0)
WALL_COLOR = (70, 70, 70)
FLOOR_COLOR = (30, 30, 30)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Roguelike Dungeon Hard")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 20)
big_font = pygame.font.SysFont(None, 24)


class Entity:
    def __init__(self, x, y, char, color, name, max_hp=None, attack=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.max_hp = max_hp
        self.hp = max_hp
        self.attack = attack

    def move(self, dx, dy, game):
        new_x = self.x + dx
        new_y = self.y + dy
        if game.map[new_y][new_x] == '.' and not game.get_entity_at(new_x, new_y):
            self.x = new_x
            self.y = new_y


class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, '@', PLAYER_COLOR, "Hero", max_hp=100, attack=5)
        self.level = 1
        self.xp = 0
        self.xp_to_next = 20
        self.weapon = None  # {'damage': int, 'name': str}
        self.potion_count = 0
        self.defense = 0

    def attack_target(self, enemy, game):
        damage = self.attack
        if self.weapon:
            damage += self.weapon.get('damage', 0)
        damage = max(1, damage - enemy.defense)
        enemy.hp -= damage
        game.effects.append(Effect(enemy.x, enemy.y, f"-{damage}", RED))
        if enemy.hp <= 0:
            game.kill_entity(enemy)
            self.gain_xp(enemy.xp_value)

    def gain_xp(self, amount):
        self.xp += amount
        if self.xp >= self.xp_to_next:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.xp -= self.xp_to_next
        self.xp_to_next = int(self.xp_to_next * 1.5)
        self.max_hp += 20
        self.hp = self.max_hp
        self.attack += 3
        game.effects.append(Effect(self.x, self.y - 1, "LEVEL UP!", ORANGE))

    def heal(self, amount):
        self.hp = min(self.max_hp, self.hp + amount)

    def move(self, dx, dy, game):
        new_x, new_y = self.x + dx, self.y + dy
        target = game.get_entity_at(new_x, new_y)
        if game.map[new_y][new_x] == '#':
            return

        if target and target != self:
            self.attack_target(target, game)
            return

        if game.map[new_y][new_x] == '.' and not game.get_entity_at(new_x, new_y):
            self.x = new_x
            self.y = new_y
            # Check items
            item = game.get_item_at(new_x, new_y)
            if item:
                if item['type'] == 'potion':
                    self.heal(20)
                    self.potion_count = 0  # Already used
                    game.items.remove(item)
                    game.effects.append(Effect(new_x, new_y, "+20 HP", GREEN))
                elif item['type'] == 'weapon':
                    self.weapon = item
                    game.items.remove(item)
                    game.effects.append(Effect(new_x, new_y, "Got Weapon!", YELLOW))
                elif item['type'] == 'exit':
                    game.next_level()

    def take_damage(self, amount):
        actual_damage = max(1, amount - self.defense)
        self.hp -= actual_damage
        game.effects.append(Effect(self.x, self.y, f"-{actual_damage}", RED))
        if self.hp <= 0:
            game.game_over()


class Enemy(Entity):
    def __init__(self, x, y, level):
        super().__init__(x, y, 'e', ENEMY_COLOR, "Enemy", max_hp=20 + level * 10, attack=3 + level)
        self.level = level
        self.defense = level // 2
        self.xp_value = 10 + level * 5
        self.attack_delay = 0

    def take_turn(self, player, game):
        dx = player.x - self.x
        dy = player.y - self.y
        dist = abs(dx) + abs(dy)
        
        if dist <= 1:
            # Attack player
            damage = max(1, self.attack - player.defense)
            player.take_damage(damage)
            game.effects.append(Effect(player.x, player.y, f"-{damage}", RED))
        elif dist <= 4:
            # Move toward player (simple)
            if abs(dx) > abs(dy):
                dx_sign = 1 if dx > 0 else -1
                dy_sign = 0
            else:
                dx_sign = 0
                dy_sign = 1 if dy > 0 else -1
            
            new_x, new_y = self.x + dx_sign, self.y + dy_sign
            target = game.get_entity_at(new_x, new_y)
            if game.map[new_y][new_x] == '.' and not target:
                self.x, self.y = new_x, new_y


class Game:
    def __init__(self):
        self.level = 1
        self.map = []
        self.entities = []
        self.player = None
        self.items = []
        self.effects = []
        self.game_over_flag = False
        self.next_floor_requested = False
        self.generate_level()
        self.entities.append(self.player)

    def generate_level(self):
        # Generate map with rooms and corridors
        self.map = [['#' for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
        self.items = []
        self.entities = [self.player]
        self.effects = []
        self.next_floor_requested = False
        
        # Room generation
        num_rooms = random.randint(8, 12)
        rooms = []
        max_room_size = 8
        min_room_size = 4
        
        for _ in range(num_rooms):
            w = random.randint(min_room_size, max_room_size)
            h = random.randint(min_room_size, max_room_size)
            x = random.randint(1, MAP_WIDTH - w - 1)
            y = random.randint(1, MAP_HEIGHT - h - 1)
            
            room = {'x': x, 'y': y, 'w': w, 'h': h}
            
            # Don't overlap too much
            overlap = False
            for r in rooms:
                if x < r['x'] + r['w'] + 1 and x + w + 1 > r['x'] and \
                   y < r['y'] + r['h'] + 1 and y + h + 1 > r['y']:
                    overlap = True
                    break
            if not overlap:
                rooms.append(room)
                # Carve room
                for i in range(y, y + h):
                    for j in range(x, x + w):
                        self.map[i][j] = '.'
        
        # Create corridors between rooms
        for i in range(len(rooms) - 1):
            r1 = rooms[i]
            r2 = rooms[i + 1]
            
            # Center of each room
            c1_x = r1['x'] + r1['w'] // 2
            c1_y = r1['y'] + r1['h'] // 2
            c2_x = r2['x'] + r2['w'] // 2
            c2_y = r2['y'] + r2['h'] // 2
            
            # Carve horizontal then vertical (L-shape)
            for x in range(min(c1_x, c2_x), max(c1_x, c2_x) + 1):
                self.map[c1_y][x] = '.'
            for y in range(min(c1_y, c2_y), max(c1_y, c2_y) + 1):
                self.map[y][c2_x] = '.'
        
        # Place player in first room center
        first_room = rooms[0]
        px = first_room['x'] + first_room['w'] // 2
        py = first_room['y'] + first_room['h'] // 2
        
        if not self.player:
            self.player = Player(px, py)
        else:
            self.player.x = px
            self.player.y = py
        
        # Place exit at last room center
        last_room = rooms[-1]
        exit_x = last_room['x'] + last_room['w'] // 2
        exit_y = last_room['y'] + last_room['h'] // 2
        self.items.append({'x': exit_x, 'y': exit_y, 'type': 'exit', 'char': '>', 'color': BLUE, 'name': 'Exit'})
        
        # Place enemies and items
        for room in rooms[1:-1]:  # Skip first and last room
            room_area = [(r['x'] + i, r['y'] + j) for r in [room] for i in range(r['w']) for j in range(r['h'])]
            # Shuffle positions
            random.shuffle(room_area)
            
            # Place enemies (2-3 per room)
            num_enemies = random.randint(2, min(3, len(room_area) // 3))
            for _ in range(num_enemies):
                if room_area:
                    ex, ey = room_area.pop()
                    if (ex != px or ey != py):
                        self.entities.append(Enemy(ex, ey, self.level))
            
            # Place items (1-2 per room)
            num_items = random.randint(1, min(2, len(room_area) // 2))
            for _ in range(num_items):
                if room_area:
                    ix, iy = room_area.pop()
                    item_type = random.choice(['potion', 'potion', 'weapon'])
                    item = {'x': ix, 'y': iy}
                    if item_type == 'potion':
                        item.update({'type': 'potion', 'char': '+', 'color': GREEN, 'name': 'Health Potion'})
                    else:
                        item.update({
                            'type': 'weapon',
                            'char': '/',
                            'color': YELLOW,
                            'name': 'Sword',
                            'damage': 2 + random.randint(0, 2) + self.level
                        })
                    self.items.append(item)
    
    def get_entity_at(self, x, y):
        for entity in self.entities:
            if entity.x == x and entity.y == y and entity != self.player:
                return entity
        return None
    
    def get_item_at(self, x, y):
        for item in self.items:
            if item['x'] == x and item['y'] == y:
                return item
        return None
    
    def kill_entity(self, entity):
        if entity in self.entities:
            self.entities.remove(entity)
    
    def next_level(self):
        self.level += 1
        self.generate_level()
        self.entities.append(self.player)
    
    def game_over(self):
        self.game_over_flag = True

    def update_enemies(self):
        for enemy in self.entities:
            if isinstance(enemy, Enemy):
                enemy.take_turn(self.player, self)


# Game state
game = Game()

def draw_text(text, x, y, color, font_instance=font, center=False):
    text_surface = font_instance.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    screen.blit(text_surface, text_rect)


def draw():
    screen.fill(BLACK)
    
    # Draw map
    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            if game.map[y][x] == '#':
                pygame.draw.rect(screen, WALL_COLOR, (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
            else:
                pygame.draw.rect(screen, FLOOR_COLOR, (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
    
    # Draw items
    for item in game.items:
        if item['type'] == 'exit':
            color = BLUE
        elif item['type'] == 'potion':
            color = GREEN
        elif item['type'] == 'weapon':
            color = YELLOW
        else:
            color = WHITE
        
        pygame.draw.circle(
            screen, color,
            (item['x'] * TILE_SIZE + TILE_SIZE // 2, item['y'] * TILE_SIZE + TILE_SIZE // 2),
            TILE_SIZE // 4
        )
        if item['type'] == 'exit':
            pygame.draw.aalines(screen, color, True, [
                (item['x'] * TILE_SIZE + TILE_SIZE//4, item['y'] * TILE_SIZE + TILE_SIZE//4),
                (item['x'] * TILE_SIZE + TILE_SIZE*3//4, item['y'] * TILE_SIZE + TILE_SIZE//4),
                (item['x'] * TILE_SIZE + TILE_SIZE*3//4, item['y'] * TILE_SIZE + TILE_SIZE*3//4),
                (item['x'] * TILE_SIZE + TILE_SIZE//4, item['y'] * TILE_SIZE + TILE_SIZE*3//4)
            ])
        elif item['type'] == 'potion':
            draw_text(item['char'], item['x'] * TILE_SIZE + TILE_SIZE//4, item['y'] * TILE_SIZE + TILE_SIZE//4, color)
    
    # Draw enemies
    for entity in game.entities:
        if entity == game.player:
            continue
        pygame.draw.circle(
            screen, entity.color,
            (entity.x * TILE_SIZE + TILE_SIZE // 2, entity.y * TILE_SIZE + TILE_SIZE // 2),
            TILE_SIZE // 3
        )
        draw_text(entity.char, entity.x * TILE_SIZE + TILE_SIZE//4, entity.y * TILE_SIZE + TILE_SIZE//4, WHITE)
    
    # Draw player
    player = game.player
    pygame.draw.circle(
        screen, player.color,
        (player.x * TILE_SIZE + TILE_SIZE // 2, player.y * TILE_SIZE + TILE_SIZE // 2),
        TILE_SIZE // 3
    )
    draw_text(player.char, player.x * TILE_SIZE + TILE_SIZE//4, player.y * TILE_SIZE + TILE_SIZE//4, WHITE)
    
    # Effects (damage numbers)
    for effect in game.effects:
        effect.y -= 0.05  # float up
        draw_text(effect.text, effect.x * TILE_SIZE + TILE_SIZE // 2, effect.y * TILE_SIZE, effect.color, center=True)
        effect.life -= 1
    
    game.effects = [e for e in game.effects if e.life > 0]
    
    # Draw UI
    ui_y = MAP_HEIGHT * TILE_SIZE
    pygame.draw.rect(screen, DARK_GRAY, (0, ui_y, SCREEN_WIDTH, 60))
    
    ui_text = []
    ui_text.append(f"Level: {game.level}")
    ui_text.append(f"HP: {player.hp}/{player.max_hp}")
    if player.weapon:
        ui_text.append(f"Weapon: {player.weapon['name']} (+{player.weapon['damage']} DMG)")
    ui_text.append(f"XP: {player.xp}/{player.xp_to_next} (Lvl {player.level})")
    
    for i, text in enumerate(ui_text):
        color = WHITE
        if "HP" in text and player.hp <= player.max_hp // 3:
            color = RED
        draw_text(text, 10, ui_y + 5 + i*25, color)
    
    # Game Over / Win screens
    if game.game_over_flag:
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        draw_text("GAME OVER", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40, RED, big_font, center=True)
        draw_text(f"Final Level: {game.level}", SCREEN_WIDTH//2, SCREEN_HEIGHT//2, WHITE, big_font, center=True)
        draw_text("Press R to Restart or Q to Quit", SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 40, YELLOW, big_font, center=True)


class Effect:
    def __init__(self, x, y, text, color):
        self.x = x
        self.y = y
        self.text = text
        self.color = color
        self.life = 40


# Main game loop
running = True
while running:
    clock.tick(FPS)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if game.game_over_flag:
                if event.key == pygame.K_r:
                    game = Game()
                    game.entities.append(game.player)
                elif event.key == pygame.K_q:
                    running = False
            else:
                dx, dy = 0, 0
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    dy = -1
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    dy = 1
                elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                    dx = -1
                elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                    dx = 1
                elif event.key == pygame.K_SPACE:
                    pass  # Do nothing
                else:
                    continue
                
                if dx or dy:
                    game.player.move(dx, dy, game)
                    # Update enemies after player moves
                    game.update_enemies()
    
    draw()
    pygame.display.flip()

pygame.quit()
sys.exit()